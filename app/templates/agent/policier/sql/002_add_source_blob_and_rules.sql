-- Adds source-blob and per-rule tables for stepwise explainable pipeline output.
-- Idempotent create script (safe to rerun).

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Canonical text snapshot per file version.
CREATE TABLE IF NOT EXISTS policy_source_blobs (
  source_blob_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_path TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  content_text TEXT NOT NULL,
  bytes INTEGER,
  read_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  repo_commit TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (file_path, file_hash)
);

CREATE INDEX IF NOT EXISTS idx_policy_source_blobs_file_path
  ON policy_source_blobs (file_path);
CREATE INDEX IF NOT EXISTS idx_policy_source_blobs_file_hash
  ON policy_source_blobs (file_hash);
CREATE INDEX IF NOT EXISTS idx_policy_source_blobs_repo_commit
  ON policy_source_blobs (repo_commit);

-- One row per machine rule produced from a specific source blob.
CREATE TABLE IF NOT EXISTS policy_rules (
  rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_blob_id UUID NOT NULL REFERENCES policy_source_blobs(source_blob_id) ON DELETE CASCADE,
  topic TEXT NOT NULL,
  model TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'SHOULD'
    CHECK (severity IN ('MUST', 'SHOULD', 'MAY')),
  rule_text TEXT NOT NULL,
  check_text TEXT,
  confidence NUMERIC(5,4) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  status TEXT NOT NULL DEFAULT 'DRAFT'
    CHECK (status IN ('DRAFT', 'VERIFIED', 'CONFLICT', 'REJECTED')),
  rule_hash TEXT NOT NULL,
  created_by_run_id UUID REFERENCES policy_runs(run_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_policy_rules_source_blob
  ON policy_rules (source_blob_id);
CREATE INDEX IF NOT EXISTS idx_policy_rules_topic_model
  ON policy_rules (topic, model);
CREATE INDEX IF NOT EXISTS idx_policy_rules_status
  ON policy_rules (status);
CREATE INDEX IF NOT EXISTS idx_policy_rules_rule_hash
  ON policy_rules (rule_hash);

-- Deduplicate same exact rule text for same source blob + model + topic.
CREATE UNIQUE INDEX IF NOT EXISTS uq_policy_rules_blob_topic_model_hash
  ON policy_rules (source_blob_id, topic, model, rule_hash);

-- Multiple evidence snippets can support one rule.
CREATE TABLE IF NOT EXISTS policy_rule_evidence (
  id BIGSERIAL PRIMARY KEY,
  rule_id UUID NOT NULL REFERENCES policy_rules(rule_id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  line_start INTEGER,
  line_end INTEGER,
  quote_snippet TEXT NOT NULL CHECK (char_length(quote_snippet) <= 1000),
  snippet_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_policy_rule_evidence_rule_id
  ON policy_rule_evidence (rule_id);
CREATE INDEX IF NOT EXISTS idx_policy_rule_evidence_file_path
  ON policy_rule_evidence (file_path);
CREATE INDEX IF NOT EXISTS idx_policy_rule_evidence_snippet_hash
  ON policy_rule_evidence (snippet_hash);

-- Keep updated_at current on updates.
CREATE OR REPLACE FUNCTION set_updated_at_policy_rules()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_policy_rules_set_updated_at ON policy_rules;
CREATE TRIGGER trg_policy_rules_set_updated_at
BEFORE UPDATE ON policy_rules
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_policy_rules();

-- Explain view: rule with blob lineage and run linkage.
CREATE OR REPLACE VIEW v_policy_rules_explain AS
SELECT
  r.rule_id,
  r.topic,
  r.model,
  r.severity,
  r.status,
  r.confidence,
  r.rule_text,
  r.check_text,
  r.rule_hash,
  r.created_by_run_id,
  r.created_at,
  b.source_blob_id,
  b.file_path,
  b.file_hash,
  b.repo_commit
FROM policy_rules r
JOIN policy_source_blobs b ON b.source_blob_id = r.source_blob_id;

COMMIT;
