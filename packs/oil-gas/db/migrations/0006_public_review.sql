-- Separate from case scoring and training admission. Apply to verified dev first.
CREATE TABLE broadbridge.public_review_packets (
    packet_id text PRIMARY KEY CHECK (packet_id ~ '^[a-z0-9][a-z0-9-]{0,63}$'),
    packet_sha256 text NOT NULL CHECK (packet_sha256 ~ '^[0-9a-f]{64}$'),
    record jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK ((record->>'schema' = 'broadbridge.public_review/1'
        AND record->>'packet_id' = packet_id
        AND record->'training_approved' = 'false'::jsonb
        AND jsonb_typeof(record->'items') = 'array') IS TRUE),
    CHECK (octet_length(record::text) <= 1048576)
);

CREATE TABLE broadbridge.public_review_scores (
    packet_id text NOT NULL REFERENCES broadbridge.public_review_packets(packet_id),
    question_id text NOT NULL CHECK (question_id ~ '^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$'),
    response_label text NOT NULL CHECK (response_label IN ('A','B')),
    reviewer text NOT NULL CHECK (reviewer = lower(btrim(reviewer)) AND reviewer ~ '^[^[:space:]@]+@[^[:space:]@]+$'),
    revision integer NOT NULL CHECK (revision > 0),
    score integer NOT NULL CHECK (score BETWEEN 0 AND 2),
    critical_error boolean NOT NULL,
    hard_fail boolean NOT NULL,
    notes text NOT NULL CHECK (length(btrim(notes)) BETWEEN 1 AND 8000),
    reviewed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (packet_id, question_id, response_label, reviewer, revision),
    CHECK (NOT critical_error OR score = 0),
    CHECK (NOT hard_fail OR (critical_error AND score = 0))
);

CREATE VIEW broadbridge.current_public_review_scores AS
SELECT DISTINCT ON (packet_id,question_id,response_label,reviewer)
    packet_id,question_id,response_label,reviewer,revision,score,critical_error,hard_fail,notes,
    reviewed_at, to_char(reviewed_at AT TIME ZONE 'UTC','YYYY-MM-DD') AS review_date
FROM broadbridge.public_review_scores
ORDER BY packet_id,question_id,response_label,reviewer,revision DESC;

CREATE FUNCTION broadbridge.save_public_review_score(
    p_packet text, p_hash text, p_question text, p_label text, p_actor text,
    p_score integer, p_critical boolean, p_hard_fail boolean, p_notes text, p_expected integer
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    v_actor text := lower(btrim(broadbridge.valid_ingestion_actor(p_actor)));
    v_packet broadbridge.public_review_packets%ROWTYPE;
    v_item jsonb;
    v_revision integer;
    v_saved broadbridge.public_review_scores%ROWTYPE;
BEGIN
    SELECT * INTO v_packet FROM broadbridge.public_review_packets WHERE packet_id=p_packet;
    IF NOT FOUND OR v_packet.packet_sha256 IS DISTINCT FROM p_hash THEN
        RAISE EXCEPTION 'Review packet changed or unavailable' USING ERRCODE='40001';
    END IF;
    SELECT item INTO v_item FROM jsonb_array_elements(v_packet.record->'items') item
      WHERE item->>'question_id'=p_question AND item->>'response_label'=p_label;
    IF v_item IS NULL THEN
        RAISE EXCEPTION 'Unknown review item' USING ERRCODE='23514';
    END IF;
    IF (v_item->'answer' IS NULL OR v_item->'answer'='null'::jsonb)
       AND (p_score IS DISTINCT FROM 0 OR p_critical IS DISTINCT FROM false OR p_hard_fail IS DISTINCT FROM false) THEN
        RAISE EXCEPTION 'Unavailable answers cannot receive quality credit or engineering-error attribution' USING ERRCODE='23514';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(jsonb_build_array(p_packet,p_question,p_label,v_actor)::text,1947014096));
    SELECT max(revision) INTO v_revision FROM broadbridge.public_review_scores
      WHERE packet_id=p_packet AND question_id=p_question AND response_label=p_label AND reviewer=v_actor;
    IF v_revision IS DISTINCT FROM p_expected THEN
        RAISE EXCEPTION 'Stale review revision' USING ERRCODE='40001';
    END IF;
    INSERT INTO broadbridge.public_review_scores
        (packet_id,question_id,response_label,reviewer,revision,score,critical_error,hard_fail,notes)
    VALUES (p_packet,p_question,p_label,v_actor,coalesce(v_revision,0)+1,p_score,p_critical,p_hard_fail,btrim(p_notes))
    RETURNING * INTO v_saved;
    RETURN to_jsonb(v_saved) || jsonb_build_object('review_date',to_char(v_saved.reviewed_at AT TIME ZONE 'UTC','YYYY-MM-DD'));
END $$;

CREATE TRIGGER public_review_packets_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
ON broadbridge.public_review_packets FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
CREATE TRIGGER public_review_scores_append_only BEFORE UPDATE OR DELETE OR TRUNCATE
ON broadbridge.public_review_scores FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
