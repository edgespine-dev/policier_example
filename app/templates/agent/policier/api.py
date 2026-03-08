from __future__ import annotations

import os
import threading
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ollama_client import Ollama
from policy_collector import (
    build_payload,
    build_policy_excluded_file_list,
    build_policy_file_list,
)
from policy_pipeline import (
    DEFAULT_MAX_FILE_CHARS,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    DEFAULT_PIPELINE_BUDGET_SECONDS,
    build_rules_per_file,
    curate_topic_per_file,
    get_cache_stats,
    list_included_policy_files,
    run_policy_compact_pipeline,
    warm_cache_topics,
)
from policy_runner import (
    DEFAULT_TIME_BUDGET_SECONDS,
    build_topic_context,
    policy_extract_step,
    policy_revise_step,
    policy_verify_step,
    run_policy_loop,
)
from topic_catalog import list_topics

app = FastAPI(title="Human Policy Collector", version="1.0.0")


def _terminate_process() -> None:
    os._exit(0)


def _schema_type(schema: dict[str, Any] | None) -> str:
    if not isinstance(schema, dict):
        return "unknown"
    if isinstance(schema.get("type"), str):
        return str(schema["type"])
    if isinstance(schema.get("$ref"), str):
        return str(schema["$ref"]).split("/")[-1]
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and any_of:
        return " | ".join(_schema_type(item) for item in any_of if isinstance(item, dict))
    return "unknown"


def _curl_example(
    *,
    method: str,
    path: str,
    operation: dict[str, Any],
    base_url: str,
) -> str:
    query_params: list[dict[str, Any]] = [
        p
        for p in operation.get("parameters", [])
        if isinstance(p, dict) and p.get("in") == "query"
    ]
    required_query = [p for p in query_params if bool(p.get("required"))]
    query_string = ""
    if required_query:
        query_parts = [f"{p['name']}=<{p['name']}>" for p in required_query if "name" in p]
        if query_parts:
            query_string = "?" + "&".join(query_parts)

    url = f"{base_url}{path}{query_string}"
    if method == "GET":
        return f'curl -s "{url}"'

    has_body = isinstance(operation.get("requestBody"), dict)
    if has_body:
        return (
            f'curl -s -X {method} "{url}" '
            '-H "Content-Type: application/json" -d \'<json_body>\''
        )
    return f'curl -s -X {method} "{url}"'


class PolicyStepRequest(BaseModel):
    topic: str
    model: str
    source_text: str
    ollama_base_url: str | None = None
    timeout_seconds: int = 120


class PolicyExtractRequest(PolicyStepRequest):
    output_schema: str


class PolicyVerifyRequest(PolicyStepRequest):
    candidate: dict[str, Any]


class PolicyReviseRequest(PolicyStepRequest):
    output_schema: str
    candidate: dict[str, Any]
    feedback: dict[str, Any]


@app.get("/healthz", summary="Health Check")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/human_policies", summary="Merged Human Policies")
def human_policies(base_dir: str | None = None) -> dict[str, Any]:
    effective_base_dir = base_dir or os.getenv("POLICY_BASE_DIR")
    try:
        return build_payload(effective_base_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_files", summary="Policy Markdown File List")
def policy_files(base_dir: str | None = None) -> list[str]:
    effective_base_dir = base_dir or os.getenv("POLICY_BASE_DIR")
    try:
        return build_policy_file_list(effective_base_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_files/excluded", summary="Excluded Policy Markdown Files")
def policy_file_exclusions(base_dir: str | None = None) -> list[str]:
    effective_base_dir = base_dir or os.getenv("POLICY_BASE_DIR")
    try:
        return build_policy_excluded_file_list(effective_base_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/topics", summary="Topic Catalog")
def topics(prompts: bool = False) -> list[dict[str, Any]]:
    try:
        return list_topics(include_prompts=prompts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/models", summary="Loaded Ollama Models")
def models(base_url: str | None = None) -> dict[str, Any]:
    try:
        loaded = Ollama.list_loaded_models(base_url=base_url)
        return {"models": loaded}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_source", summary="Topic Source Bundle")
def policy_source(topic: str, base_dir: str | None = None) -> dict[str, Any]:
    try:
        context = build_topic_context(
            topic_name=topic,
            base_dir_value=base_dir or os.getenv("POLICY_BASE_DIR"),
        )
        return {
            "topic": topic,
            "source_text": context["source_text"],
            "source_files": context["source_files"],
            "output_schema": context["output_schema"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/policy_extract", summary="Extract Step")
def policy_extract(req: PolicyExtractRequest) -> dict[str, Any]:
    try:
        return policy_extract_step(
            topic_name=req.topic,
            model=req.model,
            source_text=req.source_text,
            output_schema=req.output_schema,
            ollama_base_url=req.ollama_base_url,
            timeout_seconds=max(5, min(300, req.timeout_seconds)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/policy_verify", summary="Verify Step")
def policy_verify(req: PolicyVerifyRequest) -> dict[str, Any]:
    try:
        return policy_verify_step(
            topic_name=req.topic,
            model=req.model,
            source_text=req.source_text,
            candidate=req.candidate,
            ollama_base_url=req.ollama_base_url,
            timeout_seconds=max(5, min(300, req.timeout_seconds)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/policy_revise", summary="Revise Step")
def policy_revise(req: PolicyReviseRequest) -> dict[str, Any]:
    try:
        return policy_revise_step(
            topic_name=req.topic,
            model=req.model,
            source_text=req.source_text,
            output_schema=req.output_schema,
            candidate=req.candidate,
            feedback=req.feedback,
            ollama_base_url=req.ollama_base_url,
            timeout_seconds=max(5, min(300, req.timeout_seconds)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy", summary="Extract-Verify Loop")
def policy(
    topic: str,
    model: str,
    verifier_model: str | None = None,
    budget_seconds: int = DEFAULT_TIME_BUDGET_SECONDS,
    base_dir: str | None = None,
    ollama_base_url: str | None = None,
) -> dict[str, Any]:
    bounded_budget = max(30, min(900, budget_seconds))
    try:
        return run_policy_loop(
            topic_name=topic,
            model=model,
            verifier_model=verifier_model,
            budget_seconds=bounded_budget,
            base_dir_value=base_dir or os.getenv("POLICY_BASE_DIR"),
            ollama_base_url=ollama_base_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_pipeline/files", summary="Compact Pipeline Stage 1: Files")
def policy_pipeline_files(base_dir: str | None = None) -> dict[str, Any]:
    try:
        return list_included_policy_files(base_dir_value=base_dir or os.getenv("POLICY_BASE_DIR"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_pipeline/curate", summary="Compact Pipeline Stage 2-3: Curate Per File")
def policy_pipeline_curate(
    topic: str,
    model: str,
    base_dir: str | None = None,
    ollama_base_url: str | None = None,
    budget_seconds: int = DEFAULT_PIPELINE_BUDGET_SECONDS,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    try:
        return curate_topic_per_file(
            topic_name=topic,
            model=model,
            base_dir_value=base_dir or os.getenv("POLICY_BASE_DIR"),
            ollama_base_url=ollama_base_url,
            budget_seconds=max(30, min(86400, budget_seconds)),
            per_call_timeout_seconds=max(5, min(900, per_call_timeout_seconds)),
            max_file_chars=max(500, min(12000, max_file_chars)),
            max_iterations=max(1, min(4, max_iterations)),
            force_refresh=force_refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_pipeline/rules", summary="Compact Pipeline Stage 4-5: Rules")
def policy_pipeline_rules(
    topic: str,
    model: str,
    base_dir: str | None = None,
    ollama_base_url: str | None = None,
    budget_seconds: int = DEFAULT_PIPELINE_BUDGET_SECONDS,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    try:
        curated = curate_topic_per_file(
            topic_name=topic,
            model=model,
            base_dir_value=base_dir or os.getenv("POLICY_BASE_DIR"),
            ollama_base_url=ollama_base_url,
            budget_seconds=max(30, min(86400, budget_seconds)),
            per_call_timeout_seconds=max(5, min(900, per_call_timeout_seconds)),
            max_file_chars=max(500, min(12000, max_file_chars)),
            max_iterations=max(1, min(4, max_iterations)),
            force_refresh=force_refresh,
        )
        rules = build_rules_per_file(
            topic_name=topic,
            model=model,
            curated=curated.get("curated", []),
            ollama_base_url=ollama_base_url,
            per_call_timeout_seconds=max(5, min(900, per_call_timeout_seconds)),
            force_refresh=force_refresh,
        )
        return {
            "topic": topic,
            "model": model,
            "timed_out": curated.get("timed_out"),
            "curate_stats": {
                "processed_new": curated.get("processed_new"),
                "cache_hits": curated.get("cache_hits"),
                "relevant_files_count": curated.get("relevant_files_count"),
            },
            "rules_stats": {
                "processed_new": rules.get("processed_new"),
                "cache_hits": rules.get("cache_hits"),
                "files_with_rules": len(rules.get("rules_per_file", [])),
            },
            "rules_per_file": rules.get("rules_per_file", []),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_pipeline", summary="Compact Pipeline Stage 1-6")
def policy_pipeline(
    topic: str,
    model: str,
    base_dir: str | None = None,
    ollama_base_url: str | None = None,
    budget_seconds: int = DEFAULT_PIPELINE_BUDGET_SECONDS,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    try:
        return run_policy_compact_pipeline(
            topic_name=topic,
            model=model,
            base_dir_value=base_dir or os.getenv("POLICY_BASE_DIR"),
            ollama_base_url=ollama_base_url,
            budget_seconds=max(30, min(86400, budget_seconds)),
            per_call_timeout_seconds=max(5, min(900, per_call_timeout_seconds)),
            max_file_chars=max(500, min(12000, max_file_chars)),
            max_iterations=max(1, min(4, max_iterations)),
            force_refresh=force_refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_pipeline/warm_cache", summary="Compact Pipeline Warm Cache")
def policy_pipeline_warm_cache(
    model: str,
    topics: str | None = None,
    base_dir: str | None = None,
    ollama_base_url: str | None = None,
    topic_budget_seconds: int = DEFAULT_PIPELINE_BUDGET_SECONDS,
    per_call_timeout_seconds: int = DEFAULT_PER_CALL_TIMEOUT_SECONDS,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    parsed_topics = [t.strip() for t in topics.split(",")] if topics else None
    try:
        return warm_cache_topics(
            model=model,
            topic_names=parsed_topics,
            base_dir_value=base_dir or os.getenv("POLICY_BASE_DIR"),
            ollama_base_url=ollama_base_url,
            topic_budget_seconds=max(30, min(86400, topic_budget_seconds)),
            per_call_timeout_seconds=max(5, min(900, per_call_timeout_seconds)),
            max_file_chars=max(500, min(12000, max_file_chars)),
            max_iterations=max(1, min(4, max_iterations)),
            force_refresh=force_refresh,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/policy_pipeline/cache_stats", summary="Compact Pipeline Cache Stats")
def policy_pipeline_cache_stats() -> dict[str, Any]:
    try:
        return get_cache_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/ls",
    summary="Service Discovery",
    description="Lists API endpoints with method, parameters, and curl examples generated from OpenAPI.",
)
def ls(base_url: str = "http://127.0.0.1:45678") -> dict[str, Any]:
    schema = app.openapi()
    paths = schema.get("paths", {})
    endpoints: list[dict[str, Any]] = []
    for path in sorted(paths.keys()):
        methods = paths[path]
        if not isinstance(methods, dict):
            continue
        for method in sorted(methods.keys()):
            operation = methods[method]
            if not isinstance(operation, dict):
                continue
            method_upper = method.upper()
            if method_upper not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
                continue

            params: list[dict[str, Any]] = []
            for p in operation.get("parameters", []):
                if not isinstance(p, dict):
                    continue
                params.append(
                    {
                        "name": p.get("name"),
                        "in": p.get("in"),
                        "required": bool(p.get("required")),
                        "type": _schema_type(p.get("schema")),
                        "description": p.get("description"),
                    }
                )

            request_body = operation.get("requestBody")
            body_required = False
            body_content_types: list[str] = []
            if isinstance(request_body, dict):
                body_required = bool(request_body.get("required"))
                content = request_body.get("content")
                if isinstance(content, dict):
                    body_content_types = sorted(content.keys())

            endpoints.append(
                {
                    "method": method_upper,
                    "path": path,
                    "summary": operation.get("summary") or operation.get("operationId"),
                    "description": operation.get("description"),
                    "query_or_header_params": params,
                    "request_body": {
                        "required": body_required,
                        "content_types": body_content_types,
                    },
                    "curl": _curl_example(
                        method=method_upper,
                        path=path,
                        operation=operation,
                        base_url=base_url.rstrip("/"),
                    ),
                }
            )

    return {
        "service": app.title,
        "version": app.version,
        "base_url": base_url,
        "openapi": "/openapi.json",
        "docs": "/docs",
        "endpoints": endpoints,
    }


@app.get("/explain", summary="Explain UI", response_class=HTMLResponse)
def explain_ui() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Policier Explain</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --card: #ffffff;
      --text: #121418;
      --muted: #576072;
      --border: #d8dee8;
      --accent: #0b5fff;
      --ok: #157f3b;
      --warn: #9a6700;
      --bad: #b42318;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      background: linear-gradient(140deg, #f4f7fb 0%, #eef2f9 60%, #f6f7f9 100%);
      color: var(--text);
    }
    .wrap {
      max-width: 1200px;
      margin: 24px auto;
      padding: 0 16px 40px;
    }
    h1 { margin: 0 0 8px; font-size: 26px; }
    .muted { color: var(--muted); }
    .grid {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 16px;
      margin-top: 16px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      box-shadow: 0 1px 3px rgba(20, 31, 53, 0.05);
    }
    .row { margin: 10px 0; }
    .row label {
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }
    input, select {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 14px;
      background: #fff;
    }
    .buttons {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 12px;
    }
    button {
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text);
      border-radius: 8px;
      padding: 9px 10px;
      font-weight: 600;
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .status {
      margin-top: 10px;
      font-size: 13px;
      color: var(--muted);
      min-height: 18px;
    }
    .status.ok { color: var(--ok); }
    .status.warn { color: var(--warn); }
    .status.bad { color: var(--bad); }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      border: 1px solid var(--border);
      background: #0e1420;
      color: #d8e1f0;
      border-radius: 10px;
      padding: 12px;
      min-height: 420px;
      overflow: auto;
      font-size: 12px;
      line-height: 1.4;
    }
    .steps {
      margin-top: 8px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--muted);
    }
    .pill {
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 4px 8px;
      background: #fff;
    }
    @media (max-width: 980px) {
      .grid { grid-template-columns: 1fr; }
      pre { min-height: 320px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>/explain</h1>
    <div class="muted">Pedagogical view for Policier pipeline: run one step at a time and inspect JSON in/out.</div>
    <div class="steps">
      <span class="pill">1) files</span>
      <span class="pill">2) curate</span>
      <span class="pill">3) rules</span>
      <span class="pill">4) full pipeline</span>
      <span class="pill">cache stats / warm cache</span>
    </div>

    <div class="grid">
      <div class="card">
        <div class="row">
          <label>Topic</label>
          <select id="topic"></select>
        </div>
        <div class="row">
          <label>Model</label>
          <select id="model"></select>
        </div>
        <div class="row">
          <label>Budget Seconds (topic/full)</label>
          <input id="budget" type="number" min="30" step="30" value="3600" />
        </div>
        <div class="row">
          <label>Per-call Timeout Seconds</label>
          <input id="perCall" type="number" min="5" step="5" value="180" />
        </div>
        <div class="row">
          <label>Max File Chars</label>
          <input id="maxChars" type="number" min="500" step="100" value="4000" />
        </div>
        <div class="row">
          <label>Max Iterations</label>
          <input id="iters" type="number" min="1" max="4" step="1" value="1" />
        </div>
        <div class="row">
          <label><input id="force" type="checkbox" /> Force refresh (ignore cache)</label>
        </div>

        <div class="buttons">
          <button id="btnFiles">Files</button>
          <button id="btnStats">Cache Stats</button>
          <button id="btnCurate">Curate</button>
          <button id="btnRules">Rules</button>
          <button id="btnWarm">Warm Topic</button>
          <button id="btnAll" class="primary">Run Full</button>
        </div>
        <div id="status" class="status"></div>
      </div>

      <div class="card">
        <pre id="out">{ "ready": true }</pre>
      </div>
    </div>
  </div>

  <script>
    const $ = (id) => document.getElementById(id);
    const out = $("out");
    const statusEl = $("status");
    const btns = ["btnFiles","btnStats","btnCurate","btnRules","btnWarm","btnAll"].map($);

    function setStatus(text, level = "") {
      statusEl.textContent = text;
      statusEl.className = "status " + level;
    }
    function setBusy(busy) {
      btns.forEach(b => b.disabled = busy);
    }
    function showJson(obj) {
      out.textContent = JSON.stringify(obj, null, 2);
    }
    function q(params) {
      return new URLSearchParams(params).toString();
    }
    function cfg() {
      return {
        topic: $("topic").value,
        model: $("model").value,
        budget_seconds: $("budget").value || "3600",
        per_call_timeout_seconds: $("perCall").value || "180",
        max_file_chars: $("maxChars").value || "4000",
        max_iterations: $("iters").value || "1",
        force_refresh: $("force").checked ? "true" : "false",
      };
    }

    async function call(path, params = {}) {
      setBusy(true);
      setStatus("Calling " + path + "...", "");
      try {
        const url = path + (Object.keys(params).length ? "?" + q(params) : "");
        const r = await fetch(url, { method: "GET" });
        const text = await r.text();
        let data;
        try { data = JSON.parse(text); } catch { data = { raw: text }; }
        showJson(data);
        if (!r.ok) {
          setStatus("HTTP " + r.status + " " + (data.detail || "error"), "bad");
        } else if (data.timed_out) {
          setStatus("Completed with timeout flag: " + (data.stopped_reason || "timed_out"), "warn");
        } else {
          setStatus("OK", "ok");
        }
      } catch (e) {
        showJson({ error: String(e) });
        setStatus(String(e), "bad");
      } finally {
        setBusy(false);
      }
    }

    async function init() {
      try {
        const [topicsRes, modelsRes] = await Promise.all([
          fetch("/topics"),
          fetch("/models")
        ]);
        const topics = await topicsRes.json();
        const models = await modelsRes.json();

        $("topic").innerHTML = "";
        (topics || []).forEach(t => {
          const o = document.createElement("option");
          o.value = t.topic;
          o.textContent = t.topic + " - " + t.title;
          $("topic").appendChild(o);
        });
        if ($("topic").options.length) $("topic").value = "secrets_bootstrap_dr";

        $("model").innerHTML = "";
        const list = (models && models.models) || [];
        list.forEach(m => {
          const o = document.createElement("option");
          o.value = m;
          o.textContent = m;
          $("model").appendChild(o);
        });
        if (list.includes("qwen2.5:7b")) $("model").value = "qwen2.5:7b";
        showJson({ topics: topics.length, models: list });
        setStatus("Ready", "ok");
      } catch (e) {
        showJson({ error: String(e) });
        setStatus("Init failed: " + String(e), "bad");
      }
    }

    $("btnFiles").onclick = () => call("/policy_pipeline/files");
    $("btnStats").onclick = () => call("/policy_pipeline/cache_stats");
    $("btnCurate").onclick = () => call("/policy_pipeline/curate", cfg());
    $("btnRules").onclick = () => call("/policy_pipeline/rules", cfg());
    $("btnAll").onclick = () => call("/policy_pipeline", cfg());
    $("btnWarm").onclick = () => {
      const c = cfg();
      call("/policy_pipeline/warm_cache", {
        model: c.model,
        topics: c.topic,
        topic_budget_seconds: c.budget_seconds,
        per_call_timeout_seconds: c.per_call_timeout_seconds,
        max_file_chars: c.max_file_chars,
        max_iterations: c.max_iterations,
        force_refresh: c.force_refresh,
      });
    };
    init();
  </script>
</body>
</html>
"""


@app.post("/restart", summary="Restart Service Process")
def restart(x_restart_token: str | None = Header(default=None)) -> dict[str, str]:
    required = os.getenv("POLICIER_RESTART_TOKEN")
    if required and x_restart_token != required:
        raise HTTPException(status_code=403, detail="forbidden")

    # Exit shortly after response; Kubernetes restarts the container.
    threading.Timer(0.2, _terminate_process).start()
    return {"status": "restarting"}
