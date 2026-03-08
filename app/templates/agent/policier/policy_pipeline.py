from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from ollama_client import Ollama
from policy_collector import collect_markdown_files, detect_base_dir, load_policy
from topic_catalog import get_topic, list_topics

PIPELINE_VERSION = "v1"
DEFAULT_PIPELINE_BUDGET_SECONDS = 14400
DEFAULT_PER_CALL_TIMEOUT_SECONDS = 900
DEFAULT_MAX_FILE_CHARS = 5000
DEFAULT_MAX_ITERATIONS = 2


def _cache_root() -> Path:
    root = Path(os.getenv("POLICY_CACHE_DIR", "/tmp/policier-cache")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_read_text(path: Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[TRUNCATED]"
    return text


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cache_path(stage: str, key: str) -> Path:
    return _cache_root() / stage / f"{key}.json"


def _cache_get(stage: str, key: str) -> dict[str, Any] | None:
    path = _cache_path(stage, key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_delete(stage: str, key: str) -> None:
    path = _cache_path(stage, key)
    if path.exists():
        path.unlink()


def _cache_put(stage: str, key: str, payload: dict[str, Any]) -> None:
    path = _cache_path(stage, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(body + "\n", encoding="utf-8")


def list_included_policy_files(base_dir_value: str | None = None) -> dict[str, Any]:
    base_dir = detect_base_dir(base_dir_value)
    policy = load_policy(base_dir)
    files = collect_markdown_files(base_dir, policy)
    rel = [f"/{p.relative_to(base_dir).as_posix()}" for p in files]
    return {
        "base_dir": str(base_dir),
        "count": len(rel),
        "files": rel,
    }


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


def _curate_once(
    *,
    client: Ollama,
    topic_name: str,
    title: str,
    scope: str,
    keywords: list[str],
    rel_path: str,
    file_text: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    prompt = (
        "Task: decide if this file is relevant for topic extraction.\n"
        f"Topic: {topic_name}\n"
        f"Title: {title}\n"
        f"Scope: {scope}\n"
        f"Keywords: {', '.join(keywords)}\n"
        f"File: {rel_path}\n\n"
        "File content:\n"
        f"{file_text}\n\n"
        "Return ONLY JSON:\n"
        "{\n"
        '  "relevant": true,\n'
        '  "confidence": 0.0,\n'
        '  "summary": "short factual summary",\n'
        '  "evidence": ["short exact snippets"],\n'
        '  "missing_or_unclear": ["missing details or ambiguities"]\n'
        "}\n"
    )
    raw = client.ask(prompt, timeout=timeout_seconds)
    return _extract_json(raw)


def _curate_verify_once(
    *,
    client: Ollama,
    topic_name: str,
    scope: str,
    keywords: list[str],
    rel_path: str,
    file_text: str,
    candidate: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    prompt = (
        "Verify whether the candidate is complete and accurate for this file and topic.\n"
        f"Topic: {topic_name}\n"
        f"Scope: {scope}\n"
        f"Keywords: {', '.join(keywords)}\n"
        f"File: {rel_path}\n\n"
        "File content:\n"
        f"{file_text}\n\n"
        "Candidate JSON:\n"
        f"{json.dumps(candidate, ensure_ascii=False, indent=2)}\n\n"
        "Return ONLY JSON:\n"
        "{\n"
        '  "status": "COMPLETE|INCOMPLETE",\n'
        '  "relevant": true,\n'
        '  "missing_items": ["..."],\n'
        '  "incorrect_items": ["..."],\n'
        '  "notes": "short"\n'
        "}\n"
    )
    raw = client.ask(prompt, timeout=timeout_seconds)
    return _extract_json(raw)


def _curate_revise_once(
    *,
    client: Ollama,
    topic_name: str,
    scope: str,
    keywords: list[str],
    rel_path: str,
    file_text: str,
    candidate: dict[str, Any],
    feedback: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    prompt = (
        "Revise the candidate to maximize recall and correctness.\n"
        f"Topic: {topic_name}\n"
        f"Scope: {scope}\n"
        f"Keywords: {', '.join(keywords)}\n"
        f"File: {rel_path}\n\n"
        "File content:\n"
        f"{file_text}\n\n"
        "Previous candidate JSON:\n"
        f"{json.dumps(candidate, ensure_ascii=False, indent=2)}\n\n"
        "Verifier feedback JSON:\n"
        f"{json.dumps(feedback, ensure_ascii=False, indent=2)}\n\n"
        "Return ONLY JSON with the same schema as candidate.\n"
    )
    raw = client.ask(prompt, timeout=timeout_seconds)
    return _extract_json(raw)


def curate_topic_per_file(
    *,
    topic_name: str,
    model: str,
    base_dir_value: str | None = None,
    ollama_base_url: str | None = None,
    budget_seconds: int = DEFAULT_PIPELINE_BUDGET_SECONDS,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    started = time.time()
    deadline = started + max(30, budget_seconds)
    topic = get_topic(topic_name, include_prompts=False)
    if not topic:
        raise ValueError(f"Unknown topic: {topic_name}")

    base_dir = detect_base_dir(base_dir_value)
    policy = load_policy(base_dir)
    files = collect_markdown_files(base_dir, policy)

    client = Ollama(model=model, base_url=ollama_base_url, timeout=per_call_timeout_seconds)
    keywords = [str(k) for k in topic.get("keywords", [])]
    title = str(topic.get("title", topic_name))
    scope = str(topic.get("scope", ""))

    curated: list[dict[str, Any]] = []
    cache_hits = 0
    processed = 0
    timed_out = False

    errors: list[dict[str, str]] = []

    for path in files:
        if time.time() >= deadline:
            timed_out = True
            break

        rel = f"/{path.relative_to(base_dir).as_posix()}"
        text = _safe_read_text(path, max_file_chars)
        file_hash = _hash_text(text)
        key = _hash_text(
            "|".join([PIPELINE_VERSION, "curate", topic_name, model, rel, file_hash])
        )
        cached = None if force_refresh else _cache_get("curate", key)
        if cached is not None:
            cache_hits += 1
            curated.append(cached)
            continue
        if force_refresh:
            _cache_delete("curate", key)

        try:
            candidate = _curate_once(
                client=client,
                topic_name=topic_name,
                title=title,
                scope=scope,
                keywords=keywords,
                rel_path=rel,
                file_text=text,
                timeout_seconds=min(per_call_timeout_seconds, max(5, int(deadline - time.time()))),
            )
            verify = _curate_verify_once(
                client=client,
                topic_name=topic_name,
                scope=scope,
                keywords=keywords,
                rel_path=rel,
                file_text=text,
                candidate=candidate,
                timeout_seconds=min(per_call_timeout_seconds, max(5, int(deadline - time.time()))),
            )
        except Exception as exc:
            timed_out = True
            errors.append({"file": rel, "error": str(exc)})
            break

        i = 1
        while i < max_iterations and str(verify.get("status", "")).upper() != "COMPLETE":
            if time.time() >= deadline:
                timed_out = True
                break
            try:
                candidate = _curate_revise_once(
                    client=client,
                    topic_name=topic_name,
                    scope=scope,
                    keywords=keywords,
                    rel_path=rel,
                    file_text=text,
                    candidate=candidate,
                    feedback=verify,
                    timeout_seconds=min(per_call_timeout_seconds, max(5, int(deadline - time.time()))),
                )
                verify = _curate_verify_once(
                    client=client,
                    topic_name=topic_name,
                    scope=scope,
                    keywords=keywords,
                    rel_path=rel,
                    file_text=text,
                    candidate=candidate,
                    timeout_seconds=min(per_call_timeout_seconds, max(5, int(deadline - time.time()))),
                )
            except Exception as exc:
                timed_out = True
                errors.append({"file": rel, "error": str(exc)})
                break
            i += 1

        payload = {
            "file": rel,
            "topic": topic_name,
            "model": model,
            "file_hash": file_hash,
            "candidate": candidate,
            "verification": verify,
        }
        _cache_put("curate", key, payload)
        curated.append(payload)
        processed += 1

    relevant = [
        item
        for item in curated
        if bool(item.get("candidate", {}).get("relevant"))
        or bool(item.get("verification", {}).get("relevant"))
    ]

    return {
        "topic": topic_name,
        "model": model,
        "elapsed_seconds": round(time.time() - started, 3),
        "budget_seconds": budget_seconds,
        "timed_out": timed_out,
        "processed_new": processed,
        "cache_hits": cache_hits,
        "total_files_seen": len(curated),
        "relevant_files_count": len(relevant),
        "curated": curated,
        "errors": errors,
    }


def build_rules_per_file(
    *,
    topic_name: str,
    model: str,
    curated: list[dict[str, Any]],
    ollama_base_url: str | None = None,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    client = Ollama(model=model, base_url=ollama_base_url, timeout=per_call_timeout_seconds)
    rules_per_file: list[dict[str, Any]] = []
    cache_hits = 0
    processed = 0

    errors: list[dict[str, str]] = []

    for item in curated:
        candidate = item.get("candidate", {})
        if not isinstance(candidate, dict):
            continue
        if not bool(candidate.get("relevant")):
            continue
        rel = str(item.get("file", ""))
        source = {
            "summary": candidate.get("summary"),
            "evidence": candidate.get("evidence", []),
            "missing_or_unclear": candidate.get("missing_or_unclear", []),
        }
        key = _hash_text(
            "|".join(
                [
                    PIPELINE_VERSION,
                    "rules",
                    topic_name,
                    model,
                    rel,
                    _hash_text(json.dumps(source, ensure_ascii=False, sort_keys=True)),
                ]
            )
        )
        cached = None if force_refresh else _cache_get("rules", key)
        if cached is not None:
            cache_hits += 1
            rules_per_file.append(cached)
            continue
        if force_refresh:
            _cache_delete("rules", key)

        prompt = (
            "Convert extracted policy notes into short machine-checkable rules.\n"
            f"Topic: {topic_name}\n"
            f"File: {rel}\n\n"
            "Extracted info:\n"
            f"{json.dumps(source, ensure_ascii=False, indent=2)}\n\n"
            "Return ONLY JSON:\n"
            "{\n"
            '  "rules": ["imperative short rules"],\n'
            '  "checks": ["how to verify each rule quickly"],\n'
            '  "assumptions": ["explicit assumptions"]\n'
            "}\n"
        )
        try:
            raw = client.ask(prompt, timeout=per_call_timeout_seconds)
            parsed = _extract_json(raw)
        except Exception as exc:
            errors.append({"file": rel, "error": str(exc)})
            continue
        payload = {
            "file": rel,
            "topic": topic_name,
            "model": model,
            "rules": parsed.get("rules", []),
            "checks": parsed.get("checks", []),
            "assumptions": parsed.get("assumptions", []),
        }
        _cache_put("rules", key, payload)
        rules_per_file.append(payload)
        processed += 1

    return {
        "topic": topic_name,
        "model": model,
        "rules_per_file": rules_per_file,
        "processed_new": processed,
        "cache_hits": cache_hits,
        "errors": errors,
    }


def merge_rules(rules_per_file: list[dict[str, Any]]) -> dict[str, Any]:
    merged_rules: list[str] = []
    merged_checks: list[str] = []
    merged_assumptions: list[str] = []

    def add_unique(target: list[str], value: str) -> None:
        v = value.strip()
        if not v:
            return
        norm = v.lower()
        if norm not in {x.lower() for x in target}:
            target.append(v)

    for item in rules_per_file:
        for rule in item.get("rules", []) if isinstance(item.get("rules", []), list) else []:
            add_unique(merged_rules, str(rule))
        for check in item.get("checks", []) if isinstance(item.get("checks", []), list) else []:
            add_unique(merged_checks, str(check))
        for a in item.get("assumptions", []) if isinstance(item.get("assumptions", []), list) else []:
            add_unique(merged_assumptions, str(a))

    return {
        "rules": merged_rules,
        "checks": merged_checks,
        "assumptions": merged_assumptions,
    }


def run_policy_compact_pipeline(
    *,
    topic_name: str,
    model: str,
    base_dir_value: str | None = None,
    ollama_base_url: str | None = None,
    budget_seconds: int = DEFAULT_PIPELINE_BUDGET_SECONDS,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    started = time.time()
    curate = curate_topic_per_file(
        topic_name=topic_name,
        model=model,
        base_dir_value=base_dir_value,
        ollama_base_url=ollama_base_url,
        budget_seconds=budget_seconds,
        per_call_timeout_seconds=per_call_timeout_seconds,
        max_file_chars=max_file_chars,
        max_iterations=max_iterations,
        force_refresh=force_refresh,
    )
    rules = build_rules_per_file(
        topic_name=topic_name,
        model=model,
        curated=curate.get("curated", []),
        ollama_base_url=ollama_base_url,
        per_call_timeout_seconds=per_call_timeout_seconds,
        force_refresh=force_refresh,
    )
    merged = merge_rules(rules.get("rules_per_file", []))

    return {
        "topic": topic_name,
        "model": model,
        "elapsed_seconds": round(time.time() - started, 3),
        "timed_out": bool(curate.get("timed_out", False)),
        "stages": {
            "curate": {
                "processed_new": curate.get("processed_new"),
                "cache_hits": curate.get("cache_hits"),
                "relevant_files_count": curate.get("relevant_files_count"),
                "total_files_seen": curate.get("total_files_seen"),
            },
            "rules": {
                "processed_new": rules.get("processed_new"),
                "cache_hits": rules.get("cache_hits"),
                "files_with_rules": len(rules.get("rules_per_file", [])),
            },
        },
        "curated_files": [
            item.get("file")
            for item in curate.get("curated", [])
            if bool(item.get("candidate", {}).get("relevant"))
        ],
        "merged_rules": merged,
        "rules_per_file": rules.get("rules_per_file", []),
    }


def warm_cache_topics(
    *,
    model: str,
    topic_names: list[str] | None = None,
    base_dir_value: str | None = None,
    ollama_base_url: str | None = None,
    topic_budget_seconds: int = DEFAULT_PIPELINE_BUDGET_SECONDS,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    started = time.time()
    chosen_topics = (
        topic_names
        if topic_names
        else [str(t.get("topic")) for t in list_topics(include_prompts=False)]
    )
    results: list[dict[str, Any]] = []
    for topic in chosen_topics:
        if not topic:
            continue
        try:
            out = run_policy_compact_pipeline(
                topic_name=topic,
                model=model,
                base_dir_value=base_dir_value,
                ollama_base_url=ollama_base_url,
                budget_seconds=topic_budget_seconds,
                per_call_timeout_seconds=per_call_timeout_seconds,
                max_file_chars=max_file_chars,
                max_iterations=max_iterations,
                force_refresh=force_refresh,
            )
            results.append(
                {
                    "topic": topic,
                    "ok": True,
                    "timed_out": out.get("timed_out", False),
                    "curated_files": len(out.get("curated_files", [])),
                    "rules": len(out.get("merged_rules", {}).get("rules", [])),
                    "elapsed_seconds": out.get("elapsed_seconds"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "topic": topic,
                    "ok": False,
                    "error": str(exc),
                }
            )

    return {
        "model": model,
        "topic_count": len(chosen_topics),
        "elapsed_seconds": round(time.time() - started, 3),
        "results": results,
    }


def get_cache_stats() -> dict[str, Any]:
    root = _cache_root()
    stages: dict[str, dict[str, Any]] = {}
    total_entries = 0
    total_bytes = 0
    for stage_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        entries = list(stage_dir.glob("*.json"))
        count = len(entries)
        bytes_sum = sum(p.stat().st_size for p in entries)
        total_entries += count
        total_bytes += bytes_sum
        latest_mtime = max((p.stat().st_mtime for p in entries), default=None)
        stages[stage_dir.name] = {
            "entries": count,
            "size_bytes": bytes_sum,
            "latest_mtime_epoch": latest_mtime,
        }
    return {
        "cache_root": str(root),
        "total_entries": total_entries,
        "total_size_bytes": total_bytes,
        "stages": stages,
    }
