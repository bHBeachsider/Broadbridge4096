-- Versioned expert feedback; separate from model scores and training approval.
CREATE TABLE broadbridge.questionnaire_packets (
    questionnaire_id text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    packet_sha256 text NOT NULL CHECK (packet_sha256 ~ '^[0-9a-f]{64}$'),
    record jsonb NOT NULL CHECK (octet_length(record::text) <= 1048576),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (questionnaire_id, version),
    CHECK ((record->>'schema' = 'broadbridge.training_questionnaire/1'
        AND record->>'id' = questionnaire_id AND (record->>'version')::integer = version
        AND record->'training_approved' = 'false'::jsonb
        AND jsonb_typeof(record->'questions') = 'array') IS TRUE)
);
CREATE TABLE broadbridge.questionnaire_responses (
    questionnaire_id text NOT NULL,
    version integer NOT NULL,
    reviewer text NOT NULL CHECK (reviewer = lower(btrim(reviewer)) AND reviewer ~ '^[^[:space:]@]+@[^[:space:]@]+$'),
    revision integer NOT NULL CHECK (revision > 0),
    record jsonb NOT NULL CHECK (octet_length(record::text) <= 262144),
    saved_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (questionnaire_id, version, reviewer, revision),
    FOREIGN KEY (questionnaire_id, version) REFERENCES broadbridge.questionnaire_packets(questionnaire_id, version),
    CHECK ((record->>'schema' = 'broadbridge.training_questionnaire_response/1'
        AND record->>'questionnaire_id' = questionnaire_id AND (record->>'questionnaire_version')::integer = version
        AND record->'training_approved' = 'false'::jsonb AND record->>'state' IN ('draft','submitted')
        AND jsonb_typeof(record->'answers') = 'object') IS TRUE)
);
CREATE VIEW broadbridge.current_questionnaire_responses AS
SELECT DISTINCT ON (questionnaire_id,version,reviewer) *
FROM broadbridge.questionnaire_responses
ORDER BY questionnaire_id,version,reviewer,revision DESC;

CREATE FUNCTION broadbridge.save_questionnaire_response(p_record jsonb, p_actor text, p_expected integer)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    v_actor text := lower(btrim(broadbridge.valid_ingestion_actor(p_actor)));
    v_packet broadbridge.questionnaire_packets%ROWTYPE;
    v_previous broadbridge.questionnaire_responses%ROWTYPE;
    v_saved broadbridge.questionnaire_responses%ROWTYPE;
BEGIN
    SELECT * INTO v_packet FROM broadbridge.questionnaire_packets
      WHERE questionnaire_id=p_record->>'questionnaire_id' AND version=(p_record->>'questionnaire_version')::integer;
    IF NOT FOUND OR v_packet.packet_sha256 IS DISTINCT FROM p_record->>'questionnaire_sha256' THEN
        RAISE EXCEPTION 'Questionnaire changed or unavailable' USING ERRCODE='40001';
    END IF;
    IF EXISTS (SELECT 1 FROM jsonb_object_keys(p_record->'answers') k
        WHERE NOT EXISTS (SELECT 1 FROM jsonb_array_elements(v_packet.record->'questions') q WHERE q->>'id'=k)) THEN
        RAISE EXCEPTION 'Unknown questionnaire question' USING ERRCODE='23514';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(jsonb_build_array(v_packet.questionnaire_id,v_packet.version,v_actor)::text,1947014097));
    SELECT * INTO v_previous FROM broadbridge.current_questionnaire_responses
      WHERE questionnaire_id=v_packet.questionnaire_id AND version=v_packet.version AND reviewer=v_actor;
    -- A repeated request after a lost response returns the same receipt.
    IF v_previous.record = p_record THEN RETURN to_jsonb(v_previous); END IF;
    IF v_previous.revision IS DISTINCT FROM p_expected THEN
        RAISE EXCEPTION 'Stale questionnaire revision' USING ERRCODE='40001';
    END IF;
    INSERT INTO broadbridge.questionnaire_responses(questionnaire_id,version,reviewer,revision,record)
      VALUES(v_packet.questionnaire_id,v_packet.version,v_actor,coalesce(v_previous.revision,0)+1,p_record)
      RETURNING * INTO v_saved;
    RETURN to_jsonb(v_saved);
END $$;
CREATE TRIGGER questionnaire_packets_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
ON broadbridge.questionnaire_packets FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
CREATE TRIGGER questionnaire_responses_append_only BEFORE UPDATE OR DELETE OR TRUNCATE
ON broadbridge.questionnaire_responses FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.reject_ingestion_history_change();
