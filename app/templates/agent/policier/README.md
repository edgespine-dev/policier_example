# Policier (Agents Project)

Internal API for collecting and merging human policy markdown files.

## Current status

This service is deployed in Kubernetes under the `agents` project:
- namespace: `agents-policier`
- deployment: `policier`
- service: `policier` (`ClusterIP`, port `8080`)

## How it works in cluster

The app code is mounted from the repo path:
- host: `/home/esadmin/bakerlabs-k8s/agent/policier`
- container: `/app` (read-only)

The repository root is mounted read-only for scanning:
- host: `/home/esadmin/bakerlabs-k8s`
- container: `/workspace`
- `POLICY_BASE_DIR=/workspace`

Because code is mounted from host, you only need a rollout restart after code updates.

## Update flow (no Makefile needed)

After editing and pushing `agent/policier/*`:

```bash
kubectl -n argocd annotate application agents-policier argocd.argoproj.io/refresh=hard --overwrite
kubectl -n agents-policier rollout restart deploy/policier
kubectl -n agents-policier rollout status deploy/policier --timeout=300s
```

## Endpoints

- `GET /healthz`
- `GET /human_policies`
- `GET /human_policies?base_dir=/workspace`
- `GET /policy_files`
- `GET /policy_files?base_dir=/workspace`
- `GET /policy_files/exclusions`
- `GET /policy_files/exclusions?base_dir=/workspace`
- `GET /topics`
- `GET /topics?prompts=true`
- `GET /models`
- `GET /ls`
- `GET /policy_source?topic=secrets_bootstrap_dr`
- `POST /policy_extract`
- `POST /policy_verify`
- `POST /policy_revise`
- `GET /policy?topic=secrets_bootstrap_dr&model=qwen2.5:7b`
- `GET /policy_pipeline/files`
- `GET /policy_pipeline/curate?topic=secrets_bootstrap_dr&model=qwen2.5:7b`
- `GET /policy_pipeline/rules?topic=secrets_bootstrap_dr&model=qwen2.5:7b`
- `GET /policy_pipeline?topic=secrets_bootstrap_dr&model=qwen2.5:7b`
- `GET /policy_pipeline/warm_cache?model=qwen2.5:7b`
- `GET /policy_pipeline/cache_stats`
- `POST /restart`

## Tunnel and test locally

Port-forward Policier service to localhost:

```bash
kubectl -n agents-policier port-forward svc/policier 45678:8080
```

Then test from another terminal:

```bash
curl -s http://127.0.0.1:45678/healthz | jq
curl -s http://127.0.0.1:45678/ls | jq '.endpoints[] | {method, path, summary}'
curl -s "http://127.0.0.1:45678/policy?topic=secrets_bootstrap_dr&model=qwen2.5:7b" | jq
```

Web UI:

- `http://127.0.0.1:45678/explain`

`POST /restart` returns immediately and then exits the process so Kubernetes restarts the container.
Optional protection:
- set env `POLICIER_RESTART_TOKEN`
- send header `x-restart-token: <token>`

`GET /policy` runs an extract/verify loop for the selected topic and model.
- default time budget: `900` seconds (15 min)
- query `budget_seconds` is clamped to `30..900`
- response includes:
  - `timed_out` (`true/false`)
  - `stopped_reason` (`complete`, `time_budget_exceeded`, etc.)

Stepwise endpoints for evaluation/debugging:
- `GET /policy_source` gives `source_text`, `source_files`, and `output_schema`
- `POST /policy_extract` runs only extraction with a chosen model
- `POST /policy_verify` runs only verification with a chosen model
- `POST /policy_revise` applies verifier feedback with a chosen model

Compact low-context pipeline (cache-first, file-by-file):
- Stage 1: list included files via `GET /policy_pipeline/files`
- Stage 2-3: per-file topic curation via `GET /policy_pipeline/curate`
- Stage 4-5: per-file machine rules + merged rules via `GET /policy_pipeline/rules` or full `GET /policy_pipeline`
- Cache location: `POLICY_CACHE_DIR` (default `/tmp/policier-cache`)
- Default per-call model timeout: `900s` (15 min)
- `warm_cache` can run topic-by-topic (all topics by default, or pass `topics=a,b,c`)
- `force_refresh=true` is supported on `curate`, `rules`, `policy_pipeline`, and `warm_cache`

`GET /ls` is service discovery generated from FastAPI OpenAPI metadata and includes:
- method/path
- params and request body hints
- ready-to-run curl templates

## SQL migrations

SQL scripts are stored in:
- `agent/policier/sql/001_init_policy_explain.sql`
- `agent/policier/sql/002_add_source_blob_and_rules.sql`

## Ollama client from Policier

Use the local helper class in `agent/policier/ollama_client.py`:

```python
from ollama_client import Ollama

aimoj = Ollama(model="qwen2.5:7b")
answer = aimoj.ask("Skriv en kort hälsning på svenska.")
print(answer)
```

Default base URL is:
- `http://ollama.infra-agent-hub.svc.cluster.local:11434`

Override with:
- `OLLAMA_BASE_URL`
- or `Ollama(..., base_url="http://...:11434")`

## Quick verification

```bash
kubectl -n agents-policier exec deploy/policier -- \
  python - <<'PY'
import json, urllib.request
with urllib.request.urlopen("http://127.0.0.1:8080/human_policies", timeout=180) as r:
    d = json.loads(r.read().decode("utf-8"))
print("file_count:", len(d.get("filelist", [])))
print("merge_len:", len(d.get("policy_merge", "")))
PY
```

## Optional local run

If you still want to run it locally outside cluster, use `uv`:

```bash
cd agent/policier
uv run --no-project --with fastapi --with uvicorn uvicorn api:app --host 0.0.0.0 --port 8000
```
