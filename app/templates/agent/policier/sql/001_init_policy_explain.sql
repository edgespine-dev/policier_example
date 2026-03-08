-- Policier explainability schema (PostgreSQL)
-- Initializes run tracking, source lineage, claims, evidence, and step traces.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- A) runs: one row per /policy execution
CREATE TABLE IF NOT EXISTS policy_runs (
  run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,

  topic TEXT NOT NULL,
  role TEXT,
  model TEXT NOT NULL,
  verifier_model TEXT,

  budget_seconds INTEGER,
  elapsed_seconds NUMERIC(12,3),
  timed_out BOOLEAN NOT NULL DEFAULT FALSE,
  stopped_reason TEXT,
  run_status TEXT NOT NULL DEFAULT 'running'
    CHECK (run_status IN ('running', 'completed', 'timed_out', 'failed')),

  topic_config_hash TEXT,
  extractor_version TEXT,
  repo_commit TEXT,

  files_count INTEGER,
  tokens_in_est BIGINT,
  tokens_out_est BIGINT,

  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_policy_runs_topic_created
  ON policy_runs (topic, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_policy_runs_status_created
  ON policy_runs (run_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_policy_runs_repo_commit
  ON policy_runs (repo_commit);

-- B) run_sources: which files were used in a run
CREATE TABLE IF NOT EXISTS policy_run_sources (
  id BIGSERIAL PRIMARY KEY,
  run_id UUID NOT NULL REFERENCES policy_runs(run_id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  bytes INTEGER,

  include_reason TEXT,
  slice_rank INTEGER,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (run_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_policy_run_sources_run_id
  ON policy_run_sources (run_id);
CREATE INDEX IF NOT EXISTS idx_policy_run_sources_file_hash
  ON policy_run_sources (file_hash);
CREATE INDEX IF NOT EXISTS idx_policy_run_sources_file_path
  ON policy_run_sources (file_path);

-- C) claims: normalized rules/claims
CREATE TABLE IF NOT EXISTS policy_claims (
  claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'SHOULD'
    CHECK (severity IN ('MUST', 'SHOULD', 'MAY')),
  claim_text TEXT NOT NULL,
  claim_key TEXT,
  status TEXT NOT NULL DEFAULT 'DRAFT'
    CHECK (status IN ('DRAFT', 'VERIFIED', 'CONFLICT', 'REJECTED')),
  confidence NUMERIC(5,4) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  created_by_run_id UUID REFERENCES policy_runs(run_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_policy_claims_topic_status
  ON policy_claims (topic, status);
CREATE INDEX IF NOT EXISTS idx_policy_claims_created_by_run
  ON policy_claims (created_by_run_id);
CREATE INDEX IF NOT EXISTS idx_policy_claims_claim_key
  ON policy_claims (claim_key);

-- D) evidence: explainability core (why a claim exists)
CREATE TABLE IF NOT EXISTS policy_evidence (
  id BIGSERIAL PRIMARY KEY,
  claim_id UUID NOT NULL REFERENCES policy_claims(claim_id) ON DELETE CASCADE,
  run_id UUID REFERENCES policy_runs(run_id) ON DELETE SET NULL,
  file_path TEXT NOT NULL,
  line_start INTEGER,
  line_end INTEGER,
  quote_snippet TEXT NOT NULL CHECK (char_length(quote_snippet) <= 1000),
  snippet_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_policy_evidence_claim_id
  ON policy_evidence (claim_id);
CREATE INDEX IF NOT EXISTS idx_policy_evidence_run_id
  ON policy_evidence (run_id);
CREATE INDEX IF NOT EXISTS idx_policy_evidence_file_path
  ON policy_evidence (file_path);
CREATE INDEX IF NOT EXISTS idx_policy_evidence_snippet_hash
  ON policy_evidence (snippet_hash);

-- Optional but useful for /explain UI: per-step prompts/outputs
CREATE TABLE IF NOT EXISTS policy_step_traces (
  id BIGSERIAL PRIMARY KEY,
  run_id UUID NOT NULL REFERENCES policy_runs(run_id) ON DELETE CASCADE,
  step_name TEXT NOT NULL
    CHECK (step_name IN (
      'files',
      'curate_extract',
      'curate_verify',
      'curate_revise',
      'rules_build',
      'rules_merge',
      'final'
    )),
  file_path TEXT,
  model TEXT,
  verifier_model TEXT,
  status TEXT NOT NULL DEFAULT 'ok'
    CHECK (status IN ('ok', 'timeout', 'error')),
  latency_ms INTEGER,
  timeout_seconds INTEGER,
  prompt_text TEXT,
  prompt_hash TEXT,
  output_text TEXT,
  output_hash TEXT,
  error_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_policy_step_traces_run_id
  ON policy_step_traces (run_id, id);
CREATE INDEX IF NOT EXISTS idx_policy_step_traces_step_name
  ON policy_step_traces (step_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_policy_step_traces_file_path
  ON policy_step_traces (file_path);

-- Cache registry (maps deterministic cache keys to payloads)
CREATE TABLE IF NOT EXISTS policy_cache_entries (
  cache_key TEXT PRIMARY KEY,
  stage TEXT NOT NULL CHECK (stage IN ('curate', 'rules', 'merged')),
  topic TEXT NOT NULL,
  model TEXT NOT NULL,
  file_path TEXT,
  file_hash TEXT,
  payload_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_hit_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  hit_count BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_policy_cache_stage_topic_model
  ON policy_cache_entries (stage, topic, model);
CREATE INDEX IF NOT EXISTS idx_policy_cache_file_hash
  ON policy_cache_entries (file_hash);

-- Updated-at maintenance
CREATE OR REPLACE FUNCTION set_updated_at_policy_claims()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_policy_claims_set_updated_at ON policy_claims;
CREATE TRIGGER trg_policy_claims_set_updated_at
BEFORE UPDATE ON policy_claims
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_policy_claims();

-- Explain-friendly views
CREATE OR REPLACE VIEW v_policy_run_overview AS
SELECT
  r.run_id,
  r.created_at,
  r.topic,
  r.model,
  r.verifier_model,
  r.run_status,
  r.timed_out,
  r.stopped_reason,
  r.elapsed_seconds,
  r.files_count,
  COUNT(DISTINCT s.file_path) AS source_files_logged,
  COUNT(t.id) AS trace_steps
FROM policy_runs r
LEFT JOIN policy_run_sources s ON s.run_id = r.run_id
LEFT JOIN policy_step_traces t ON t.run_id = r.run_id
GROUP BY
  r.run_id,
  r.created_at,
  r.topic,
  r.model,
  r.verifier_model,
  r.run_status,
  r.timed_out,
  r.stopped_reason,
  r.elapsed_seconds,
  r.files_count;

CREATE OR REPLACE VIEW v_policy_claim_explain AS
SELECT
  c.claim_id,
  c.topic,
  c.severity,
  c.status,
  c.confidence,
  c.claim_text,
  c.created_by_run_id,
  e.file_path,
  e.line_start,
  e.line_end,
  e.quote_snippet,
  e.snippet_hash,
  e.created_at AS evidence_created_at
FROM policy_claims c
LEFT JOIN policy_evidence e ON e.claim_id = c.claim_id;

COMMIT;
