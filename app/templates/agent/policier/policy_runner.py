from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ollama_client import Ollama
from policy_collector import (
    collect_markdown_files,
    detect_base_dir,
    load_policy,
)
from topic_catalog import get_topic

DEFAULT_TIME_BUDGET_SECONDS = 900
MAX_ITERATIONS = 6
MAX_SOURCE_CHARS = 35000
MAX_FILE_CHARS = 12000
MAX_FILES = 12


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _collect_topic_source(
    *,
    base_dir: Path,
    keywords: list[str],
) -> tuple[str, list[str]]:
    policy = load_policy(base_dir)
    files = collect_markdown_files(base_dir, policy)
    lowered_keywords = [k.lower() for k in keywords if k]

    scored: list[tuple[int, Path]] = []
    for path in files:
        rel = path.relative_to(base_dir).as_posix().lower()
        text = _read_text(path).lower()
        score = 0
        for key in lowered_keywords:
            if key in rel:
                score += 3
            if key in text:
                score += min(10, text.count(key))
        if score > 0:
            scored.append((score, path))

    selected: list[Path]
    if scored:
        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [item[1] for item in scored[:MAX_FILES]]
    else:
        selected = files[:MAX_FILES]

    chunks: list[str] = []
    used_paths: list[str] = []
    used_chars = 0
    for path in selected:
        rel = path.relative_to(base_dir).as_posix()
        content = _read_text(path)
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + "\n\n[TRUNCATED]"
        chunk = f"# FILE: /{rel}\n\n{content}\n"
        if used_chars + len(chunk) > MAX_SOURCE_CHARS:
            break
        chunks.append(chunk)
        used_paths.append(f"/{rel}")
        used_chars += len(chunk)

    return "\n\n".join(chunks), used_paths


def _fill_template(raw: str, values: dict[str, str]) -> str:
    out = raw
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out


def _extract_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return {"raw": raw}


def _remaining_call_timeout(deadline: float) -> int:
    remaining = int(deadline - time.time())
    return max(5, min(120, remaining))


def _ask_with_deadline(client: Ollama, prompt: str, deadline: float) -> str:
    if time.time() >= deadline:
        raise TimeoutError("time_budget_exceeded")
    return client.ask(prompt, timeout=_remaining_call_timeout(deadline))


def build_topic_context(
    *,
    topic_name: str,
    base_dir_value: str | None = None,
) -> dict[str, Any]:
    topic = get_topic(topic_name, include_prompts=True)
    if not topic:
        raise ValueError(f"Unknown topic: {topic_name}")

    keywords = [str(k) for k in topic.get("keywords", [])]
    base_dir = detect_base_dir(base_dir_value)
    source_text, source_files = _collect_topic_source(base_dir=base_dir, keywords=keywords)
    output_schema = json.dumps(
        {
            "topic": topic_name,
            "summary": "string",
            "coverage": [
                {
                    "requirement": "string",
                    "details": "string",
                    "evidence": ["short quote or line-level excerpt"],
                    "files": ["/path/from/repo/root.md"]
                }
            ],
            "commands": ["command or script invocation"],
            "artifacts_to_store_outside_cluster": ["artifact"],
            "dr_flow": ["ordered recovery steps"],
            "uncertainties": ["unknowns or ambiguities"]
        },
        ensure_ascii=False,
        indent=2,
    )
    return {
        "topic": topic,
        "source_text": source_text,
        "source_files": source_files,
        "output_schema": output_schema,
    }


def policy_extract_step(
    *,
    topic_name: str,
    model: str,
    source_text: str,
    output_schema: str,
    ollama_base_url: str | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    topic = get_topic(topic_name, include_prompts=True)
    if not topic:
        raise ValueError(f"Unknown topic: {topic_name}")
    prompt = _fill_template(
        topic["prompts"]["start"],
        {
            "source_text": source_text,
            "output_schema": output_schema,
        },
    )
    client = Ollama(model=model, base_url=ollama_base_url, timeout=timeout_seconds)
    raw = client.ask(prompt, timeout=timeout_seconds)
    return {
        "topic": topic_name,
        "model": model,
        "candidate": _extract_json(raw),
    }


def policy_verify_step(
    *,
    topic_name: str,
    model: str,
    source_text: str,
    candidate: dict[str, Any],
    ollama_base_url: str | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    topic = get_topic(topic_name, include_prompts=True)
    if not topic:
        raise ValueError(f"Unknown topic: {topic_name}")
    prompt = _fill_template(
        topic["prompts"]["verify"],
        {
            "source_text": source_text,
            "candidate_answer": json.dumps(candidate, ensure_ascii=False, indent=2),
        },
    )
    client = Ollama(model=model, base_url=ollama_base_url, timeout=timeout_seconds)
    raw = client.ask(prompt, timeout=timeout_seconds)
    verification = _extract_json(raw)
    return {
        "topic": topic_name,
        "model": model,
        "verification": verification,
        "status": str(verification.get("status", "")).upper() or "UNKNOWN",
    }


def policy_revise_step(
    *,
    topic_name: str,
    model: str,
    source_text: str,
    output_schema: str,
    candidate: dict[str, Any],
    feedback: dict[str, Any],
    ollama_base_url: str | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    revise_prompt = (
        "Revise the extraction to maximize recall.\n"
        f"Topic: {topic_name}\n\n"
        "SOURCE TEXT:\n"
        f"{source_text}\n\n"
        "PREVIOUS CANDIDATE JSON:\n"
        f"{json.dumps(candidate, ensure_ascii=False, indent=2)}\n\n"
        "VERIFIER FEEDBACK JSON:\n"
        f"{json.dumps(feedback, ensure_ascii=False, indent=2)}\n\n"
        "Return ONLY valid JSON in this schema:\n"
        f"{output_schema}\n"
    )
    client = Ollama(model=model, base_url=ollama_base_url, timeout=timeout_seconds)
    raw = client.ask(revise_prompt, timeout=timeout_seconds)
    return {
        "topic": topic_name,
        "model": model,
        "candidate": _extract_json(raw),
    }


def run_policy_loop(
    *,
    topic_name: str,
    model: str,
    base_dir_value: str | None = None,
    verifier_model: str | None = None,
    budget_seconds: int = DEFAULT_TIME_BUDGET_SECONDS,
    max_iterations: int = MAX_ITERATIONS,
    ollama_base_url: str | None = None,
) -> dict[str, Any]:
    started = time.time()
    deadline = started + max(1, budget_seconds)

    context = build_topic_context(topic_name=topic_name, base_dir_value=base_dir_value)
    topic = context["topic"]
    source_text = context["source_text"]
    source_files = context["source_files"]
    output_schema = context["output_schema"]

    extractor = Ollama(model=model, base_url=ollama_base_url, timeout=120)
    verifier = Ollama(
        model=verifier_model or model,
        base_url=ollama_base_url,
        timeout=120,
    )

    start_prompt = _fill_template(
        topic["prompts"]["start"],
        {
            "source_text": source_text,
            "output_schema": output_schema,
        },
    )
    if time.time() >= deadline:
        raise RuntimeError("Time budget exhausted before extraction started")
    try:
        current_candidate_raw = _ask_with_deadline(extractor, start_prompt, deadline)
    except Exception as exc:
        return {
            "topic": topic_name,
            "model": model,
            "verifier_model": verifier_model or model,
            "time_budget_seconds": budget_seconds,
            "elapsed_seconds": round(time.time() - started, 3),
            "timed_out": True,
            "stopped_reason": "time_budget_exceeded",
            "iterations": 0,
            "source_files": source_files,
            "result": {},
            "verification": {
                "status": "INCOMPLETE",
                "notes": f"Initial extraction failed before completion: {exc}",
            },
            "history": [],
        }
    current_candidate = _extract_json(current_candidate_raw)

    history: list[dict[str, Any]] = []
    timed_out = False
    stopped_reason = "max_iterations_reached"

    for i in range(1, max_iterations + 1):
        now = time.time()
        if now >= deadline:
            timed_out = True
            stopped_reason = "time_budget_exceeded"
            break

        verify_prompt = _fill_template(
            topic["prompts"]["verify"],
            {
                "source_text": source_text,
                "candidate_answer": json.dumps(current_candidate, ensure_ascii=False, indent=2),
            },
        )
        try:
            verify_raw = _ask_with_deadline(verifier, verify_prompt, deadline)
        except Exception as exc:
            timed_out = True
            stopped_reason = "time_budget_exceeded"
            history.append(
                {
                    "iteration": i,
                    "verify_status": "UNKNOWN",
                    "notes": f"Verifier call aborted: {exc}",
                }
            )
            break
        verify_parsed = _extract_json(verify_raw)
        status = str(verify_parsed.get("status", "")).upper()

        history.append(
            {
                "iteration": i,
                "verify_status": status or "UNKNOWN",
                "missing_count": len(verify_parsed.get("missing_items", []))
                if isinstance(verify_parsed.get("missing_items"), list)
                else None,
                "incorrect_count": len(verify_parsed.get("incorrect_items", []))
                if isinstance(verify_parsed.get("incorrect_items"), list)
                else None,
            }
        )

        if status == "COMPLETE":
            stopped_reason = "complete"
            return {
                "topic": topic_name,
                "model": model,
                "verifier_model": verifier_model or model,
                "time_budget_seconds": budget_seconds,
                "elapsed_seconds": round(time.time() - started, 3),
                "timed_out": False,
                "stopped_reason": stopped_reason,
                "iterations": i,
                "source_files": source_files,
                "result": current_candidate,
                "verification": verify_parsed,
                "history": history,
            }

        if time.time() >= deadline:
            timed_out = True
            stopped_reason = "time_budget_exceeded"
            break

        revise_prompt = (
            "Revise the extraction to maximize recall.\n"
            f"Topic: {topic_name}\n\n"
            "SOURCE TEXT:\n"
            f"{source_text}\n\n"
            "PREVIOUS CANDIDATE JSON:\n"
            f"{json.dumps(current_candidate, ensure_ascii=False, indent=2)}\n\n"
            "VERIFIER FEEDBACK JSON:\n"
            f"{json.dumps(verify_parsed, ensure_ascii=False, indent=2)}\n\n"
            "Return ONLY valid JSON in this schema:\n"
            f"{output_schema}\n"
        )

        try:
            current_candidate_raw = _ask_with_deadline(extractor, revise_prompt, deadline)
        except Exception as exc:
            timed_out = True
            stopped_reason = "time_budget_exceeded"
            history.append(
                {
                    "iteration": i,
                    "verify_status": status or "UNKNOWN",
                    "notes": f"Revision call aborted: {exc}",
                }
            )
            break
        current_candidate = _extract_json(current_candidate_raw)

    return {
        "topic": topic_name,
        "model": model,
        "verifier_model": verifier_model or model,
        "time_budget_seconds": budget_seconds,
        "elapsed_seconds": round(time.time() - started, 3),
        "timed_out": timed_out,
        "stopped_reason": stopped_reason,
        "iterations": len(history),
        "source_files": source_files,
        "result": current_candidate,
        "verification": {
            "status": "INCOMPLETE" if timed_out else "UNKNOWN",
            "notes": (
                "Stopped because time budget was reached."
                if timed_out
                else "Stopped before verifier returned COMPLETE."
            ),
        },
        "history": history,
    }
