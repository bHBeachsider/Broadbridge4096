-- Additive Broadbridge binding for the generic Foundry ingestion contracts.
-- The generic job store expects these exact sixteen columns and performs its
-- own explicit initialization in other schemas.  This migration owns only the
-- dedicated broadbridge schema; constructors never run DDL.
CREATE TABLE broadbridge.ingestion_jobs (
    job_id text PRIMARY KEY,
    source_json text NOT NULL,
    recipe_version text NOT NULL,
    state text NOT NULL CHECK (state IN ('queued','running','succeeded','retry','failed')),
    attempts integer NOT NULL DEFAULT 0,
    max_attempts integer NOT NULL,
    backoff_seconds double precision NOT NULL,
    max_backoff_seconds double precision NOT NULL,
    available_at double precision NOT NULL,
    lease_token text,
    lease_expires_at double precision,
    worker_id text,
    result_json text,
    error_code text,
    created_at double precision NOT NULL,
    updated_at double precision NOT NULL,
    CONSTRAINT ingestion_jobs_project CHECK (
        jsonb_typeof(source_json::jsonb) = 'object'
        AND source_json::jsonb->>'project_id' = 'broadbridge-oil-gas'
    )
);

CREATE TABLE broadbridge.source_revisions (
    source_id text NOT NULL REFERENCES broadbridge.sources(source_id),
    revision_id text NOT NULL,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    registry_ref text NOT NULL UNIQUE,
    source_record jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    created_by text NOT NULL,
    PRIMARY KEY (source_id, revision_id, content_sha256),
    UNIQUE (source_id, revision_id),
    CONSTRAINT source_revision_contract CHECK (
        jsonb_typeof(source_record) = 'object'
        AND source_record->>'schema' = 'foundry.source_revision/1'
        AND source_record->>'project_id' = 'broadbridge-oil-gas'
        AND source_record->>'source_id' = source_id
        AND source_record->>'revision_id' = revision_id
        AND source_record->>'content_sha256' = content_sha256
        AND source_record#>>'{permission,status}' = 'pending'
        AND source_record#>>'{permission,reviewed_by}' IS NULL
        AND source_record#>>'{permission,reviewed_at}' IS NULL
    )
);

CREATE TABLE broadbridge.source_rights_reviews (
    review_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id text NOT NULL,
    revision_id text NOT NULL,
    content_sha256 text NOT NULL,
    status text NOT NULL CHECK (status IN ('approved','revoked')),
    permitted_use text NOT NULL CHECK (permitted_use IN ('training','testing_only','reference_only')),
    rights_basis text NOT NULL CHECK (broadbridge.valid_id(rights_basis)),
    reviewed_by text NOT NULL,
    reviewed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (source_id, revision_id, content_sha256)
        REFERENCES broadbridge.source_revisions(source_id, revision_id, content_sha256)
);
CREATE INDEX source_rights_identity ON broadbridge.source_rights_reviews
    (source_id, revision_id, content_sha256, review_id DESC);

CREATE TABLE broadbridge.candidate_records (
    example_id text NOT NULL,
    candidate_hash text NOT NULL CHECK (candidate_hash ~ '^[0-9a-f]{64}$'),
    family_id text NOT NULL,
    requested_split text NOT NULL CHECK (requested_split IN ('train','dev','val','locked_test','test')),
    candidate_record jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    created_by text NOT NULL,
    PRIMARY KEY (example_id, candidate_hash),
    CONSTRAINT candidate_record_contract CHECK (
        jsonb_typeof(candidate_record) = 'object'
        AND candidate_record->>'schema' = 'foundry.training_example/1'
        AND candidate_record->>'example_id' = example_id
        AND candidate_record->>'family_id' = family_id
        AND candidate_record->>'split' = requested_split
        AND candidate_record#>>'{review,status}' = 'pending'
        AND candidate_record#>>'{review,reviewer}' IS NULL
        AND candidate_record#>>'{review,reviewed_at}' IS NULL
        AND jsonb_typeof(candidate_record->'source_refs') = 'array'
        AND jsonb_array_length(candidate_record->'source_refs') > 0
    )
);

CREATE TABLE broadbridge.candidate_reviews (
    review_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    example_id text NOT NULL,
    candidate_hash text NOT NULL,
    status text NOT NULL CHECK (status IN ('approved','rejected')),
    reason text NOT NULL CHECK (broadbridge.valid_id(reason)),
    reviewed_by text NOT NULL,
    reviewed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (example_id, candidate_hash)
        REFERENCES broadbridge.candidate_records(example_id, candidate_hash)
);
CREATE INDEX candidate_reviews_identity ON broadbridge.candidate_reviews
    (example_id, candidate_hash, review_id DESC);

CREATE TABLE broadbridge.dataset_releases (
    release_id text PRIMARY KEY CHECK (release_id ~ '^[0-9a-f]{64}$'),
    candidate_content_hash text NOT NULL CHECK (candidate_content_hash ~ '^[0-9a-f]{64}$'),
    recipe_version text NOT NULL,
    manifest jsonb NOT NULL,
    approved_by text NOT NULL,
    approved_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    recorded_by text NOT NULL,
    CONSTRAINT dataset_release_contract CHECK (
        jsonb_typeof(manifest) = 'object'
        AND manifest->>'schema' = 'foundry.dataset_release/1'
        AND manifest->>'release_id' = release_id
        AND manifest->>'pack_name' = 'broadbridge-oil-gas'
        AND manifest->>'recipe_version' = recipe_version
        AND manifest#>>'{review,status}' = 'approved'
        AND manifest#>>'{review,candidate_content_hash}' = candidate_content_hash
        AND release_id = candidate_content_hash
        AND manifest#>>'{review,reviewer}' = approved_by
    )
);

CREATE TABLE broadbridge.model_runs (
    run_id text NOT NULL,
    revision bigint NOT NULL CHECK (revision > 0),
    release_id text NOT NULL REFERENCES broadbridge.dataset_releases(release_id),
    dataset_release_hash text NOT NULL,
    state text NOT NULL CHECK (state IN ('queued','running','succeeded','failed','cancelled')),
    record jsonb NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    recorded_by text NOT NULL,
    PRIMARY KEY (run_id, revision),
    CONSTRAINT model_run_contract CHECK (
        jsonb_typeof(record) = 'object'
        AND record->>'schema' = 'foundry.model_run/1'
        AND record->>'run_id' = run_id
        AND record->>'release_id' = release_id
        AND record->>'dataset_release_hash' = dataset_release_hash
        AND record->>'status' = state
        AND dataset_release_hash = release_id
    )
);

CREATE VIEW broadbridge.current_model_runs AS
SELECT DISTINCT ON (run_id)
    run_id, revision, release_id, dataset_release_hash, state, record, recorded_at, recorded_by
FROM broadbridge.model_runs
ORDER BY run_id, revision DESC;

CREATE VIEW broadbridge.current_source_permissions AS
SELECT DISTINCT ON (revision.source_id, revision.revision_id, revision.content_sha256)
    revision.registry_ref AS source_ref,
    revision.source_id,
    revision.revision_id,
    revision.content_sha256,
    COALESCE(review.status, revision.source_record#>>'{permission,status}') AS status,
    COALESCE(review.permitted_use, revision.source_record#>>'{permission,permitted_use}') AS permitted_use,
    review.review_id,
    review.rights_basis,
    review.reviewed_by,
    review.reviewed_at
FROM broadbridge.source_revisions revision
LEFT JOIN broadbridge.source_rights_reviews review
  ON review.source_id = revision.source_id
 AND review.revision_id = revision.revision_id
 AND review.content_sha256 = revision.content_sha256
ORDER BY revision.source_id, revision.revision_id, revision.content_sha256, review.review_id DESC NULLS LAST;

CREATE VIEW broadbridge.ingestion_source_status AS
SELECT
    permission.source_ref,
    revision.source_id,
    revision.revision_id,
    revision.content_sha256,
    revision.source_record->>'original_filename' AS original_filename,
    revision.source_record->>'media_type' AS media_type,
    (revision.source_record->>'size_bytes')::bigint AS size_bytes,
    revision.source_record->>'confidentiality' AS confidentiality,
    revision.source_record#>>'{permission,status}' AS initial_permission_status,
    permission.status AS current_permission_status,
    permission.permitted_use AS current_permitted_use,
    permission.review_id AS current_rights_review_id,
    permission.reviewed_by AS rights_reviewed_by,
    permission.reviewed_at AS rights_reviewed_at,
    revision.created_at,
    revision.created_by
FROM broadbridge.source_revisions revision
JOIN broadbridge.current_source_permissions permission
  USING (source_id, revision_id, content_sha256);

CREATE VIEW broadbridge.current_candidate_reviews AS
SELECT DISTINCT ON (candidate.example_id, candidate.candidate_hash)
    candidate.example_id,
    candidate.candidate_hash,
    candidate.family_id,
    candidate.requested_split,
    COALESCE(review.status, candidate.candidate_record#>>'{review,status}') AS status,
    review.review_id,
    review.reason,
    review.reviewed_by,
    review.reviewed_at
FROM broadbridge.candidate_records candidate
LEFT JOIN broadbridge.candidate_reviews review USING (example_id, candidate_hash)
ORDER BY candidate.example_id, candidate.candidate_hash, review.review_id DESC NULLS LAST;

CREATE FUNCTION broadbridge.valid_ingestion_actor(value text) RETURNS text
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF NOT broadbridge.valid_id(value) THEN
        RAISE EXCEPTION 'An explicit nonblank actor is required' USING ERRCODE = '22023';
    END IF;
    RETURN broadbridge.trim_text(value);
END $$;

CREATE FUNCTION broadbridge.valid_registry_ref(value text) RETURNS boolean
LANGUAGE sql IMMUTABLE AS $$
    SELECT value IS NOT NULL AND value = broadbridge.trim_text(value) AND value <> ''
       AND value !~ '(^|/)\.\.?(/|$)' AND value !~ '//' AND value !~ '[\\[:cntrl:]]'
$$;

CREATE FUNCTION broadbridge.register_source_revision(
    p_source jsonb, p_registry_ref text, p_actor text
) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
    v_source_id text := p_source->>'source_id';
    v_revision_id text := p_source->>'revision_id';
    v_content_sha256 text := p_source->>'content_sha256';
    v_existing broadbridge.source_revisions%ROWTYPE;
    v_current_review_id bigint;
    v_actor text := broadbridge.valid_ingestion_actor(p_actor);
BEGIN
    IF jsonb_typeof(p_source) <> 'object'
       OR p_source->>'schema' <> 'foundry.source_revision/1'
       OR p_source->>'project_id' <> 'broadbridge-oil-gas'
       OR NOT broadbridge.valid_id(v_source_id)
       OR NOT broadbridge.valid_id(v_revision_id)
       OR v_content_sha256 !~ '^[0-9a-f]{64}$'
       OR p_source#>>'{permission,status}' <> 'pending'
       OR NOT broadbridge.valid_registry_ref(p_registry_ref) THEN
        RAISE EXCEPTION 'Invalid pending Broadbridge source revision' USING ERRCODE = '23514';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(v_source_id || ':' || v_revision_id, 1947014096));
    SELECT * INTO v_existing FROM broadbridge.source_revisions
      WHERE source_id=v_source_id AND revision_id=v_revision_id;
    IF FOUND THEN
        IF v_existing.content_sha256 IS DISTINCT FROM v_content_sha256
           OR v_existing.registry_ref IS DISTINCT FROM p_registry_ref
           OR v_existing.source_record IS DISTINCT FROM p_source THEN
            RAISE EXCEPTION 'Source revision identity is immutable' USING ERRCODE = '23505';
        END IF;
    ELSE
        INSERT INTO broadbridge.sources(source_id, record, updated_by)
        VALUES (v_source_id, jsonb_build_object('source_id',v_source_id,'registry_ref',p_registry_ref), v_actor)
        ON CONFLICT (source_id) DO NOTHING;
        INSERT INTO broadbridge.source_revisions
            (source_id,revision_id,content_sha256,registry_ref,source_record,created_by)
        VALUES (v_source_id,v_revision_id,v_content_sha256,p_registry_ref,p_source,v_actor)
        RETURNING * INTO v_existing;
    END IF;
    SELECT max(review_id) INTO v_current_review_id
      FROM broadbridge.source_rights_reviews
      WHERE source_id=v_source_id AND revision_id=v_revision_id
        AND content_sha256=v_content_sha256;
    RETURN jsonb_build_object(
        'source_ref',v_existing.registry_ref,'source_id',v_existing.source_id,
        'revision_id',v_existing.revision_id,'content_sha256',v_existing.content_sha256,
        'permission_status','pending','current_rights_review_id',v_current_review_id
    );
END $$;

CREATE FUNCTION broadbridge.review_source_rights(
    p_source_id text, p_revision_id text, p_content_sha256 text,
    p_decision text, p_permitted_use text, p_rights_basis text,
    p_expected_review_id bigint, p_actor text
) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
    v_current_id bigint;
    v_review broadbridge.source_rights_reviews%ROWTYPE;
    v_actor text := broadbridge.valid_ingestion_actor(p_actor);
BEGIN
    PERFORM 1 FROM broadbridge.source_revisions
      WHERE source_id=p_source_id AND revision_id=p_revision_id AND content_sha256=p_content_sha256
      FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Unknown source revision' USING ERRCODE = '23503'; END IF;
    SELECT max(review_id) INTO v_current_id FROM broadbridge.source_rights_reviews
      WHERE source_id=p_source_id AND revision_id=p_revision_id AND content_sha256=p_content_sha256;
    IF v_current_id IS DISTINCT FROM p_expected_review_id THEN
        RAISE EXCEPTION 'stale source rights review' USING ERRCODE = '40001';
    END IF;
    INSERT INTO broadbridge.source_rights_reviews
        (source_id,revision_id,content_sha256,status,permitted_use,rights_basis,reviewed_by)
    VALUES (p_source_id,p_revision_id,p_content_sha256,p_decision,p_permitted_use,
            broadbridge.trim_text(p_rights_basis),v_actor)
    RETURNING * INTO v_review;
    RETURN jsonb_build_object(
        'review_id',v_review.review_id,'status',v_review.status,
        'permitted_use',v_review.permitted_use,'reviewed_by',v_review.reviewed_by,
        'reviewed_at',v_review.reviewed_at
    );
END $$;

CREATE FUNCTION broadbridge.register_candidate(
    p_candidate jsonb, p_candidate_hash text, p_actor text
) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
    v_example_id text := p_candidate->>'example_id';
    v_existing broadbridge.candidate_records%ROWTYPE;
    v_actor text := broadbridge.valid_ingestion_actor(p_actor);
BEGIN
    IF p_candidate_hash !~ '^[0-9a-f]{64}$' OR NOT broadbridge.valid_id(v_example_id) THEN
        RAISE EXCEPTION 'Invalid candidate identity' USING ERRCODE = '23514';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(v_example_id || ':' || p_candidate_hash, 1947014096));
    SELECT * INTO v_existing FROM broadbridge.candidate_records
      WHERE example_id=v_example_id AND candidate_hash=p_candidate_hash;
    IF FOUND THEN
        IF v_existing.candidate_record IS DISTINCT FROM p_candidate THEN
            RAISE EXCEPTION 'Candidate hash identity is immutable' USING ERRCODE = '23505';
        END IF;
    ELSE
        INSERT INTO broadbridge.candidate_records
            (example_id,candidate_hash,family_id,requested_split,candidate_record,created_by)
        VALUES (v_example_id,p_candidate_hash,p_candidate->>'family_id',p_candidate->>'split',p_candidate,v_actor)
        RETURNING * INTO v_existing;
    END IF;
    RETURN jsonb_build_object('example_id',v_existing.example_id,'candidate_hash',v_existing.candidate_hash);
END $$;

CREATE FUNCTION broadbridge.review_candidate(
    p_example_id text, p_candidate_hash text, p_decision text, p_reason text,
    p_expected_review_id bigint, p_actor text
) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
    v_current_id bigint;
    v_review broadbridge.candidate_reviews%ROWTYPE;
    v_actor text := broadbridge.valid_ingestion_actor(p_actor);
BEGIN
    PERFORM 1 FROM broadbridge.candidate_records
      WHERE example_id=p_example_id AND candidate_hash=p_candidate_hash FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Unknown candidate' USING ERRCODE = '23503'; END IF;
    SELECT max(review_id) INTO v_current_id FROM broadbridge.candidate_reviews
      WHERE example_id=p_example_id AND candidate_hash=p_candidate_hash;
    IF v_current_id IS DISTINCT FROM p_expected_review_id THEN
        RAISE EXCEPTION 'stale candidate review' USING ERRCODE = '40001';
    END IF;
    INSERT INTO broadbridge.candidate_reviews
        (example_id,candidate_hash,status,reason,reviewed_by)
    VALUES (p_example_id,p_candidate_hash,p_decision,broadbridge.trim_text(p_reason),v_actor)
    RETURNING * INTO v_review;
    RETURN jsonb_build_object(
        'review_id',v_review.review_id,'status',v_review.status,
        'reviewed_by',v_review.reviewed_by,'reviewed_at',v_review.reviewed_at
    );
END $$;

CREATE FUNCTION broadbridge.record_dataset_release(p_manifest jsonb, p_actor text) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
    v_actor text := broadbridge.valid_ingestion_actor(p_actor);
    v_release_id text := p_manifest->>'release_id';
    v_existing broadbridge.dataset_releases%ROWTYPE;
BEGIN
    IF p_manifest#>>'{review,candidate_content_hash}' IS DISTINCT FROM v_release_id
       OR p_manifest#>>'{review,reviewer}' IS DISTINCT FROM v_actor THEN
        RAISE EXCEPTION 'Dataset approval hash or actor does not match release' USING ERRCODE = '23514';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(v_release_id, 1947014096));
    SELECT * INTO v_existing FROM broadbridge.dataset_releases WHERE release_id=v_release_id;
    IF FOUND THEN
        IF v_existing.manifest IS DISTINCT FROM p_manifest THEN
            RAISE EXCEPTION 'Dataset release identity is immutable' USING ERRCODE = '23505';
        END IF;
    ELSE
        INSERT INTO broadbridge.dataset_releases
            (release_id,candidate_content_hash,recipe_version,manifest,approved_by,approved_at,recorded_by)
        VALUES (v_release_id,p_manifest#>>'{review,candidate_content_hash}',p_manifest->>'recipe_version',
                p_manifest,v_actor,(p_manifest#>>'{review,reviewed_at}')::timestamptz,v_actor)
        RETURNING * INTO v_existing;
    END IF;
    RETURN jsonb_build_object('release_id',v_existing.release_id,'recorded_at',v_existing.recorded_at);
END $$;

CREATE FUNCTION broadbridge.record_model_run(
    p_record jsonb, p_expected_revision bigint, p_actor text
) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
    v_actor text := broadbridge.valid_ingestion_actor(p_actor);
    v_run_id text := p_record->>'run_id';
    v_existing broadbridge.model_runs%ROWTYPE;
    v_revision bigint;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(v_run_id, 1947014096));
    SELECT * INTO v_existing FROM broadbridge.model_runs
      WHERE run_id=v_run_id ORDER BY revision DESC LIMIT 1;
    IF FOUND THEN
        IF v_existing.record IS NOT DISTINCT FROM p_record THEN
            RETURN jsonb_build_object('run_id',v_existing.run_id,'revision',v_existing.revision,
                                      'recorded_at',v_existing.recorded_at);
        END IF;
        IF v_existing.revision IS DISTINCT FROM p_expected_revision THEN
            RAISE EXCEPTION 'stale model run revision' USING ERRCODE = '40001';
        END IF;
        IF v_existing.release_id IS DISTINCT FROM p_record->>'release_id'
           OR v_existing.dataset_release_hash IS DISTINCT FROM p_record->>'dataset_release_hash' THEN
            RAISE EXCEPTION 'Model run identity is immutable' USING ERRCODE = '23505';
        END IF;
        v_revision := v_existing.revision + 1;
    ELSE
        IF p_expected_revision IS NOT NULL THEN
            RAISE EXCEPTION 'stale model run revision' USING ERRCODE = '40001';
        END IF;
        v_revision := 1;
    END IF;
    INSERT INTO broadbridge.model_runs
        (run_id,revision,release_id,dataset_release_hash,state,record,recorded_by)
    VALUES (v_run_id,v_revision,p_record->>'release_id',p_record->>'dataset_release_hash',
            p_record->>'status',p_record,v_actor)
    RETURNING * INTO v_existing;
    RETURN jsonb_build_object('run_id',v_existing.run_id,'revision',v_existing.revision,
                              'recorded_at',v_existing.recorded_at);
END $$;

CREATE FUNCTION broadbridge.reject_ingestion_history_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Ingestion identity and review history are immutable' USING ERRCODE = '23514';
END $$;

CREATE TRIGGER source_revisions_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
    ON broadbridge.source_revisions FOR EACH STATEMENT
    EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
CREATE TRIGGER source_rights_reviews_append_only BEFORE UPDATE OR DELETE OR TRUNCATE
    ON broadbridge.source_rights_reviews FOR EACH STATEMENT
    EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
CREATE TRIGGER candidate_records_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
    ON broadbridge.candidate_records FOR EACH STATEMENT
    EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
CREATE TRIGGER candidate_reviews_append_only BEFORE UPDATE OR DELETE OR TRUNCATE
    ON broadbridge.candidate_reviews FOR EACH STATEMENT
    EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
CREATE TRIGGER dataset_releases_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
    ON broadbridge.dataset_releases FOR EACH STATEMENT
    EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
CREATE TRIGGER model_runs_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
    ON broadbridge.model_runs FOR EACH STATEMENT
    EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
