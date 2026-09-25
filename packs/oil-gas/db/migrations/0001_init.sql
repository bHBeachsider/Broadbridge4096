-- Dedicated Broadbridge storage. No embeddings or external schemas are used.
CREATE SCHEMA IF NOT EXISTS broadbridge;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE broadbridge.sources (
    source_id text PRIMARY KEY,
    record jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_by text NOT NULL
);
CREATE TABLE broadbridge.cases (
    case_id text PRIMARY KEY,
    family_id text NOT NULL,
    status text NOT NULL,
    permitted_use text NOT NULL,
    signed boolean NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_by text NOT NULL,
    record jsonb NOT NULL
);
CREATE TABLE broadbridge.evidence (
    evidence_id text PRIMARY KEY,
    source_id text NOT NULL REFERENCES broadbridge.sources(source_id),
    case_id text REFERENCES broadbridge.cases(case_id),
    record jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_by text NOT NULL
);
CREATE TABLE broadbridge.questions (
    question_id text PRIMARY KEY,
    case_id text NOT NULL REFERENCES broadbridge.cases(case_id) ON DELETE CASCADE,
    type text NOT NULL,
    requested_split text NOT NULL,
    effective_split text NOT NULL,
    record jsonb NOT NULL
);
CREATE TABLE broadbridge.workflow (
    author_email text PRIMARY KEY,
    record jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_by text NOT NULL
);
CREATE TABLE broadbridge.runs (
    run_id text PRIMARY KEY,
    case_id text NOT NULL REFERENCES broadbridge.cases(case_id),
    mode text NOT NULL,
    case_sha256 text NOT NULL,
    prompt_sha256 text NOT NULL,
    record jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_by text NOT NULL,
    UNIQUE (run_id, case_id)
);
CREATE TABLE broadbridge.scorecards (
    run_id text PRIMARY KEY,
    case_id text NOT NULL REFERENCES broadbridge.cases(case_id),
    markdown text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_by text NOT NULL,
    FOREIGN KEY (run_id, case_id) REFERENCES broadbridge.runs(run_id, case_id)
);
CREATE TABLE broadbridge.review_log (
    review_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    case_id text NOT NULL,
    operation text NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    actor text NOT NULL,
    old_record jsonb,
    new_record jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE UNIQUE INDEX cases_id_ci ON broadbridge.cases (lower(case_id));
CREATE UNIQUE INDEX questions_id_ci ON broadbridge.questions (lower(question_id));
CREATE UNIQUE INDEX sources_id_ci ON broadbridge.sources (lower(source_id));
CREATE UNIQUE INDEX evidence_id_ci ON broadbridge.evidence (lower(evidence_id));
CREATE INDEX cases_family ON broadbridge.cases (family_id);
CREATE INDEX questions_case ON broadbridge.questions (case_id);
CREATE INDEX evidence_source ON broadbridge.evidence (source_id);
CREATE INDEX evidence_case ON broadbridge.evidence (case_id);
CREATE INDEX runs_case ON broadbridge.runs (case_id);
CREATE INDEX review_log_case ON broadbridge.review_log (case_id, created_at);
