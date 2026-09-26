-- Match Python str.strip() whitespace, including tabs, line breaks and Unicode spaces.
CREATE FUNCTION broadbridge.trim_text(value text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT btrim(value, U&'\0009\000A\000B\000C\000D\001C\001D\001E\001F\0020\0085\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000')
$$;

-- Only the JSON Schema vocabulary used by the canonical capture schema is supported.
-- Unknown validation keywords fail closed instead of being silently ignored.
CREATE FUNCTION broadbridge.matches_schema(value jsonb, contract jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE kind text := jsonb_typeof(value); item jsonb; property record; required_key text;
BEGIN
    IF contract IS NULL OR jsonb_typeof(contract) <> 'object' OR value IS NULL THEN RETURN false; END IF;
    IF EXISTS (SELECT 1 FROM jsonb_object_keys(contract) k WHERE k NOT IN
        ('$schema','$id','title','description','default','type','const','enum','required',
         'properties','additionalProperties','items','minLength')) THEN RETURN false; END IF;
    IF contract ? 'type' THEN
        IF jsonb_typeof(contract->'type') = 'array' THEN
            IF NOT (contract->'type' ? kind) THEN RETURN false; END IF;
        ELSIF contract->>'type' <> kind THEN RETURN false;
        END IF;
    END IF;
    IF contract ? 'const' AND value IS DISTINCT FROM contract->'const' THEN RETURN false; END IF;
    IF contract ? 'enum' AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(contract->'enum') AS e(entry) WHERE e.entry = matches_schema.value) THEN RETURN false; END IF;
    IF kind = 'string' AND contract ? 'minLength'
       AND length(value #>> '{}') < (contract->>'minLength')::integer THEN RETURN false; END IF;
    IF kind = 'object' THEN
        FOR required_key IN SELECT jsonb_array_elements_text(COALESCE(contract->'required', '[]'::jsonb)) LOOP
            IF NOT value ? required_key THEN RETURN false; END IF;
        END LOOP;
        FOR property IN SELECT * FROM jsonb_each(value) LOOP
            IF COALESCE(contract->'properties', '{}'::jsonb) ? property.key THEN
                IF NOT broadbridge.matches_schema(property.value, contract->'properties'->property.key) THEN RETURN false; END IF;
            ELSIF contract->'additionalProperties' = 'false'::jsonb THEN RETURN false;
            ELSIF contract ? 'additionalProperties' AND contract->'additionalProperties' <> 'true'::jsonb THEN RETURN false;
            END IF;
        END LOOP;
    ELSIF kind = 'array' AND contract ? 'items' THEN
        FOR item IN SELECT jsonb_array_elements(value) LOOP
            IF NOT broadbridge.matches_schema(item, contract->'items') THEN RETURN false; END IF;
        END LOOP;
    END IF;
    RETURN true;
EXCEPTION WHEN data_exception THEN
    RETURN false;
END $$;

CREATE FUNCTION broadbridge.valid_id(value text) RETURNS boolean
LANGUAGE sql IMMUTABLE AS $$
    SELECT value IS NOT NULL AND value = broadbridge.trim_text(value) AND broadbridge.trim_text(value) <> ''
$$;

CREATE FUNCTION broadbridge.complete_signoff(value jsonb) RETURNS boolean
LANGUAGE sql IMMUTABLE AS $$
    SELECT (jsonb_typeof(value) = 'object'
        AND value->'signed' = 'true'::jsonb
        AND jsonb_typeof(value->'name') = 'string'
        AND jsonb_typeof(value->'date') = 'string'
        AND lower(broadbridge.trim_text(value->>'name')) NOT IN ('', 'unknown', 'undecided')
        AND lower(broadbridge.trim_text(value->>'date')) NOT IN ('', 'unknown', 'undecided')) IS TRUE
$$;

ALTER TABLE broadbridge.cases ADD CONSTRAINT cases_contract CHECK (
    (jsonb_typeof(record) = 'object'
    AND record->>'schema' = 'broadbridge.case_record/1'
    AND broadbridge.valid_id(case_id) AND broadbridge.valid_id(family_id)
    AND status IN ('draft', 'complete', 'signed')
    AND permitted_use IN ('training', 'testing_only', 'reference_only')
    AND record#>>'{identity,record_type}' IN ('real_event', 'reconstructed', 'hypothetical')
    AND jsonb_typeof(record->'questions') = 'array'
    AND jsonb_typeof(record#>'{reviewer_signoff,signed}') = 'boolean'
    AND jsonb_typeof(record#>'{reviewer_signoff,name}') = 'string'
    AND jsonb_typeof(record#>'{reviewer_signoff,date}') = 'string'
    AND case_id = record->>'case_id'
    AND family_id = record->>'family_id'
    AND status = record->>'status'
    AND permitted_use = record#>>'{identity,permitted_use}'
    AND to_jsonb(signed) = record#>'{reviewer_signoff,signed}'
    AND (status <> 'signed' OR broadbridge.complete_signoff(record->'reviewer_signoff'))) IS TRUE
);
ALTER TABLE broadbridge.questions ADD CONSTRAINT questions_contract CHECK (
    (broadbridge.valid_id(question_id) AND jsonb_typeof(record) = 'object'
    AND type IN ('brief', 'missing_data', 'calculation', 'grounded_explanation', 'abstention')
    AND requested_split IN ('train', 'dev', 'locked_test')
    AND effective_split IN ('train', 'dev', 'locked_test')
    AND question_id = record->>'question_id'
    AND type = record->>'type' AND requested_split = record->>'split') IS TRUE
);
ALTER TABLE broadbridge.sources ADD CONSTRAINT sources_contract CHECK (
    (broadbridge.valid_id(source_id) AND jsonb_typeof(record) = 'object'
    AND source_id = record->>'source_id') IS TRUE
);
ALTER TABLE broadbridge.evidence ADD CONSTRAINT evidence_contract CHECK (
    (broadbridge.valid_id(evidence_id) AND jsonb_typeof(record) = 'object'
    AND evidence_id = record->>'evidence_id' AND source_id = record->>'source_id'
    AND case_id IS NOT DISTINCT FROM record->>'case_id') IS TRUE
);
ALTER TABLE broadbridge.runs ADD CONSTRAINT runs_contract CHECK (
    (run_id ~ '^[0-9a-f]{64}$' AND case_sha256 ~ '^[0-9a-f]{64}$'
    AND prompt_sha256 ~ '^[0-9a-f]{64}$' AND jsonb_typeof(record) = 'object'
    AND record->>'schema' = 'broadbridge.brief_run/1'
    AND case_id = record->>'case_id' AND mode = record->>'mode'
    AND mode IN ('mock', 'live') AND case_sha256 = record->>'case_sha256'
    AND prompt_sha256 = record->>'prompt_sha256') IS TRUE
);
ALTER TABLE broadbridge.workflow ADD CONSTRAINT workflow_contract CHECK (
    (broadbridge.valid_id(author_email) AND author_email = lower(author_email)
    AND jsonb_typeof(record) = 'object' AND record->>'schema' = 'broadbridge.workflow/1'
    AND jsonb_typeof(record->'answers') = 'object'
    AND jsonb_typeof(record->'updated_at') = 'string') IS TRUE
);

CREATE FUNCTION broadbridge.actor() RETURNS text
LANGUAGE plpgsql STABLE AS $$
DECLARE value text := current_setting('broadbridge.actor', true);
BEGIN
    IF value IS NULL OR broadbridge.trim_text(value) = '' THEN
        RAISE EXCEPTION 'An explicit actor is required' USING ERRCODE = '22023';
    END IF;
    RETURN broadbridge.trim_text(value);
END $$;

-- Every pilot case write shares one transaction lock, including direct SQL.
CREATE FUNCTION broadbridge.lock_case_writes() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(1947014096, 1);
    RETURN NULL;
END $$;
CREATE TRIGGER cases_write_lock BEFORE INSERT OR UPDATE OR DELETE ON broadbridge.cases
    FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.lock_case_writes();

CREATE FUNCTION broadbridge.stamp_case() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE who text := broadbridge.actor();
BEGIN
    PERFORM pg_advisory_xact_lock(1947014096, 1);
    IF TG_OP = 'UPDATE' THEN
        IF NEW.case_id <> OLD.case_id THEN
            RAISE EXCEPTION 'case_id is immutable' USING ERRCODE = '23514';
        END IF;
        -- Permission revocation is immediate. Other accepted-content edits require review again.
        IF OLD.status = 'signed' AND NEW.status = 'signed'
           AND (NEW.record - ARRAY['status','reviewer_signoff','updated_at'] #- '{identity,permitted_use}')
               IS DISTINCT FROM (OLD.record - ARRAY['status','reviewer_signoff','updated_at'] #- '{identity,permitted_use}')
           AND NEW.record->'reviewer_signoff' IS NOT DISTINCT FROM OLD.record->'reviewer_signoff' THEN
            RAISE EXCEPTION 'Editing signed content requires renewed reviewer signoff' USING ERRCODE = '23514';
        END IF;
        -- Do not skip validation of direct indexed-column edits, even with unchanged JSON.
        IF NEW.record = OLD.record AND NEW.family_id = OLD.family_id AND NEW.status = OLD.status
            AND NEW.permitted_use = OLD.permitted_use AND NEW.signed = OLD.signed
            AND who = OLD.updated_by THEN
            RETURN NULL;
        END IF;
        NEW.updated_at := greatest(clock_timestamp(), OLD.updated_at + interval '1 microsecond');
    ELSE
        NEW.updated_at := clock_timestamp();
    END IF;
    NEW.updated_by := who;
    RETURN NEW;
END $$;
CREATE TRIGGER cases_stamp BEFORE INSERT OR UPDATE ON broadbridge.cases
    FOR EACH ROW EXECUTE FUNCTION broadbridge.stamp_case();

CREATE FUNCTION broadbridge.protect_questions() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF pg_trigger_depth() < 2 THEN
        RAISE EXCEPTION 'Questions are projections; save the case record instead' USING ERRCODE = '23514';
    END IF;
    RETURN COALESCE(NEW, OLD);
END $$;
CREATE TRIGGER questions_projection BEFORE INSERT OR UPDATE OR DELETE ON broadbridge.questions
    FOR EACH ROW EXECUTE FUNCTION broadbridge.protect_questions();

CREATE FUNCTION broadbridge.reject_destructive_audit() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'This operation is not allowed on protected capture history' USING ERRCODE = '23514';
END $$;
CREATE TRIGGER review_log_append_only BEFORE UPDATE OR DELETE OR TRUNCATE ON broadbridge.review_log
    FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.reject_destructive_audit();
CREATE TRIGGER cases_no_truncate BEFORE TRUNCATE ON broadbridge.cases
    FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.reject_destructive_audit();
CREATE TRIGGER questions_no_truncate BEFORE TRUNCATE ON broadbridge.questions
    FOR EACH STATEMENT EXECUTE FUNCTION broadbridge.reject_destructive_audit();

CREATE FUNCTION broadbridge.after_case() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE old_family text; new_family text;
BEGIN
    IF TG_OP <> 'INSERT' THEN old_family := OLD.family_id; END IF;
    IF TG_OP <> 'DELETE' THEN new_family := NEW.family_id; END IF;
    IF TG_OP = 'INSERT' OR TG_OP = 'DELETE'
       OR OLD.status IS DISTINCT FROM NEW.status
       OR OLD.permitted_use IS DISTINCT FROM NEW.permitted_use
       OR OLD.record->'reviewer_signoff' IS DISTINCT FROM NEW.record->'reviewer_signoff' THEN
        INSERT INTO broadbridge.review_log(case_id, operation, actor, old_record, new_record)
        VALUES (COALESCE(NEW.case_id, OLD.case_id), TG_OP, broadbridge.actor(),
                CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE OLD.record END,
                CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE NEW.record END);
    END IF;
    IF TG_OP <> 'DELETE' THEN
        IF TG_OP = 'INSERT' OR NEW.record->'questions' IS DISTINCT FROM OLD.record->'questions' THEN
            DELETE FROM broadbridge.questions WHERE case_id = NEW.case_id;
            INSERT INTO broadbridge.questions(question_id, case_id, type, requested_split, effective_split, record)
            SELECT q->>'question_id', NEW.case_id, q->>'type', q->>'split', q->>'split', q
            FROM jsonb_array_elements(NEW.record->'questions') q;
        END IF;
    END IF;
    -- Recompute both families, allowing demotion when their stricter member moves or disappears.
    WITH family_splits AS (
        SELECT c.family_id, CASE max(CASE q.requested_split WHEN 'locked_test' THEN 2 WHEN 'dev' THEN 1 ELSE 0 END)
            WHEN 2 THEN 'locked_test' WHEN 1 THEN 'dev' ELSE 'train' END AS split
        FROM broadbridge.cases c JOIN broadbridge.questions q USING (case_id)
        WHERE c.family_id IN (old_family, new_family) GROUP BY c.family_id
    )
    UPDATE broadbridge.questions q SET effective_split = f.split
    FROM broadbridge.cases c JOIN family_splits f USING (family_id)
    WHERE q.case_id = c.case_id AND q.effective_split IS DISTINCT FROM f.split;
    RETURN COALESCE(NEW, OLD);
END $$;
CREATE TRIGGER cases_audit_and_questions AFTER INSERT OR UPDATE OR DELETE ON broadbridge.cases
    FOR EACH ROW EXECUTE FUNCTION broadbridge.after_case();

CREATE FUNCTION broadbridge.save_case(p_record jsonb, p_actor text,
    p_expected_updated_at timestamptz DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE current_row broadbridge.cases; result broadbridge.cases;
BEGIN
    PERFORM set_config('broadbridge.actor', p_actor, true);
    PERFORM broadbridge.actor();
    PERFORM pg_advisory_xact_lock(1947014096, 1);
    SELECT * INTO current_row FROM broadbridge.cases WHERE case_id = p_record->>'case_id';
    IF p_expected_updated_at IS NOT NULL AND
       (current_row.case_id IS NULL OR current_row.updated_at <> p_expected_updated_at) THEN
        RAISE EXCEPTION 'Case revision conflict; reload before saving' USING ERRCODE = '40001';
    END IF;
    INSERT INTO broadbridge.cases(case_id, family_id, status, permitted_use, signed, updated_by, record)
    VALUES (p_record->>'case_id', p_record->>'family_id', p_record->>'status',
        p_record#>>'{identity,permitted_use}', (p_record#>>'{reviewer_signoff,signed}')::boolean,
        p_actor, p_record)
    ON CONFLICT (case_id) DO UPDATE SET family_id = EXCLUDED.family_id,
        status = EXCLUDED.status, permitted_use = EXCLUDED.permitted_use,
        signed = EXCLUDED.signed, record = EXCLUDED.record
    RETURNING * INTO result;
    IF result.case_id IS NULL THEN
        SELECT * INTO result FROM broadbridge.cases WHERE case_id = p_record->>'case_id';
    END IF;
    RETURN jsonb_build_object('record', result.record, 'revision', result.updated_at);
END $$;

CREATE FUNCTION broadbridge.save_workflow(p_record jsonb, p_actor text) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE who text; result broadbridge.workflow;
BEGIN
    PERFORM set_config('broadbridge.actor', p_actor, true);
    who := broadbridge.actor();
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

CREATE VIEW broadbridge.train_candidates AS
SELECT c.case_id, c.family_id, q.question_id, q.type, q.effective_split AS split,
       c.permitted_use, q.record AS question, c.record AS case_record
FROM broadbridge.cases c JOIN broadbridge.questions q USING (case_id)
WHERE c.status = 'signed' AND c.signed AND c.permitted_use = 'training'
  AND lower(broadbridge.trim_text(c.case_id)) NOT IN ('', 'unknown', 'undecided')
  AND lower(broadbridge.trim_text(c.family_id)) NOT IN ('', 'unknown', 'undecided')
  AND broadbridge.complete_signoff(c.record->'reviewer_signoff') AND q.effective_split = 'train';

-- Frozen copy of the public contract; parity is tested against the canonical JSON file.
CREATE FUNCTION broadbridge.case_contract() RETURNS jsonb
LANGUAGE sql IMMUTABLE AS $contract$
    SELECT '{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://broadbridge.invalid/schemas/case_record.schema.json","title":"Broadbridge Case Capture record v1","type":"object","additionalProperties":false,"required":["schema","case_id","family_id","status","identity","decision_time","hindsight","evidence","questions","reviewer_signoff","created_at","updated_at"],"properties":{"schema":{"const":"broadbridge.case_record/1"},"case_id":{"type":"string","minLength":1},"family_id":{"type":"string","minLength":1},"status":{"enum":["draft","complete","signed"]},"identity":{"type":"object","additionalProperties":false,"required":["title","unit_service","period","confidentiality","record_type","permitted_use"],"properties":{"title":{"type":"string"},"unit_service":{"type":"string"},"period":{"type":"string"},"confidentiality":{"type":"string"},"record_type":{"enum":["real_event","reconstructed","hypothetical"]},"permitted_use":{"enum":["training","testing_only","reference_only"],"default":"training","description":"The capture page defaults new cases to training. Imports still require an explicit value; this annotation does not fill missing permissions or grant signed status."}}},"decision_time":{"type":"object","additionalProperties":false,"required":["b1_trigger","b2_operating_context","b3_initial_info_and_requests","b5_initial_hypotheses","b6_distrusted_or_missing","observations"],"properties":{"b1_trigger":{"type":"string"},"b2_operating_context":{"type":"string"},"b3_initial_info_and_requests":{"type":"string"},"b5_initial_hypotheses":{"type":"string"},"b6_distrusted_or_missing":{"type":"string"},"observations":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["time","variable_location","value_units_basis","source","quality"],"properties":{"time":{"type":"string"},"variable_location":{"type":"string"},"value_units_basis":{"type":"string"},"source":{"type":"string"},"quality":{"type":"string"}}}}}},"hindsight":{"type":"object","additionalProperties":false,"required":["b8_turning_point","b9_calculations","b10_actions_taken","b11_confidence","b12_dangerous_wrong_answer","b13_lesson_and_limits","hypotheses"],"properties":{"b8_turning_point":{"type":"string"},"b9_calculations":{"type":"string"},"b10_actions_taken":{"type":"string"},"b11_confidence":{"type":"string"},"b12_dangerous_wrong_answer":{"type":"string"},"b13_lesson_and_limits":{"type":"string"},"hypotheses":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["hypothesis","evidence_for","evidence_against","discriminator"],"properties":{"hypothesis":{"type":"string"},"evidence_for":{"type":"string"},"evidence_against":{"type":"string"},"discriminator":{"type":"string"}}}}}},"evidence":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["item","format","restriction","available_at_decision_time"],"properties":{"item":{"type":"string"},"format":{"type":"string"},"restriction":{"type":"string"},"available_at_decision_time":{"type":["string","boolean"],"description":"The seeded live record has an empty evidence array. Accept text or checkbox values until a populated live export confirms the widget type."}}}},"questions":{"type":"array","items":{"type":"object","additionalProperties":false,"required":["question_id","question","evidence_ids","reference_answer","tolerance","hard_fail_criteria","type","split"],"properties":{"question_id":{"type":"string"},"question":{"type":"string"},"evidence_ids":{"type":"string"},"reference_answer":{"type":"string"},"tolerance":{"type":"string"},"hard_fail_criteria":{"type":"string"},"type":{"enum":["brief","missing_data","calculation","grounded_explanation","abstention"]},"split":{"enum":["train","dev","locked_test"]}}}},"reviewer_signoff":{"type":"object","additionalProperties":false,"required":["signed","name","date"],"properties":{"signed":{"type":"boolean"},"name":{"type":"string"},"date":{"type":"string"}}},"created_at":{"type":"string"},"updated_at":{"type":"string"}}}'::jsonb
$contract$;
ALTER TABLE broadbridge.cases ADD CONSTRAINT cases_full_contract
    CHECK (broadbridge.matches_schema(record, broadbridge.case_contract()));
