-- Browser writes require an explicit revision; NULL means create, never overwrite.
-- Importer upsert semantics remain in save_case/save_workflow.
-- Share the browser lock with importer writes before checking any revision.
CREATE OR REPLACE FUNCTION broadbridge.save_workflow(p_record jsonb, p_actor text) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE who text; result broadbridge.workflow;
BEGIN
    PERFORM set_config('broadbridge.actor', p_actor, true);
    who := broadbridge.actor();
    PERFORM pg_advisory_xact_lock(1947014096, 3);
    IF (p_record - ARRAY['schema','answers','updated_at']) <> '{}'::jsonb
       OR EXISTS (SELECT 1 FROM jsonb_each(p_record->'answers') a
           WHERE a.key NOT IN ('A1','A2','A3','A4','A5','A6','A7','A8','A9','A10')
               OR jsonb_typeof(a.value) <> 'string') THEN
        RAISE EXCEPTION 'Workflow contract is invalid' USING ERRCODE = '23514';
    END IF;
    INSERT INTO broadbridge.workflow(author_email, record, updated_by)
    VALUES (lower(who), p_record, who)
    ON CONFLICT (author_email) DO UPDATE SET record = EXCLUDED.record, updated_by = who,
        updated_at = greatest(clock_timestamp(), broadbridge.workflow.updated_at + interval '1 microsecond')
    WHERE broadbridge.workflow.record IS DISTINCT FROM EXCLUDED.record OR broadbridge.workflow.updated_by <> who
    RETURNING * INTO result;
    IF result.author_email IS NULL THEN
        SELECT * INTO result FROM broadbridge.workflow WHERE author_email = lower(who);
    END IF;
    RETURN jsonb_build_object('record', result.record, 'revision', result.updated_at);
END $$;

CREATE FUNCTION broadbridge.capture_save_case(p_record jsonb, p_actor text, p_revision timestamptz)
RETURNS jsonb LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(1947014096, 1);
    IF p_revision IS NULL AND EXISTS (SELECT 1 FROM broadbridge.cases WHERE case_id=p_record->>'case_id') THEN
        RAISE EXCEPTION 'Case already exists; reload' USING ERRCODE='40001';
    END IF;
    RETURN broadbridge.save_case(p_record, p_actor, p_revision);
END $$;

CREATE FUNCTION broadbridge.capture_save_workflow(p_record jsonb, p_actor text, p_revision timestamptz)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE current_revision timestamptz;
BEGIN
    PERFORM pg_advisory_xact_lock(1947014096, 3);
    SELECT updated_at INTO current_revision FROM broadbridge.workflow WHERE author_email=lower(btrim(p_actor));
    IF current_revision IS DISTINCT FROM p_revision THEN
        RAISE EXCEPTION 'Workflow revision conflict; reload' USING ERRCODE='40001';
    END IF;
    RETURN broadbridge.save_workflow(p_record, p_actor);
END $$;

CREATE FUNCTION broadbridge.capture_delete_case(p_case_id text, p_actor text, p_revision timestamptz)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE current_revision timestamptz;
BEGIN
    PERFORM set_config('broadbridge.actor', p_actor, true);
    PERFORM broadbridge.actor();
    PERFORM pg_advisory_xact_lock(1947014096, 1);
    SELECT updated_at INTO current_revision FROM broadbridge.cases WHERE case_id=p_case_id;
    IF p_revision IS NULL OR current_revision IS NULL OR current_revision <> p_revision THEN
        RAISE EXCEPTION 'Case revision conflict; reload' USING ERRCODE='40001';
    END IF;
    DELETE FROM broadbridge.cases WHERE case_id=p_case_id;
END $$;
