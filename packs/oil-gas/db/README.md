# Broadbridge database contract

The `broadbridge` schema holds capture records, source/evidence registers, historical brief runs, scorecards and append-only case review history. The canonical JSON schemas remain unchanged. PostgreSQL 17 and the `vector` extension are supported; there are no vector columns, embeddings or retrieval operations.

## Configuration and migrations

Install `packs/oil-gas/requirements-db.txt`. It pins `psycopg[binary]==3.3.2` and includes the existing offline harness requirements.

Normal scripts, `connection()`, `status` and `reset-dev` use only the explicitly exported `BROADBRIDGE_DATABASE_URL` (normally the pooled application URL). The `db.py migrate` command uses `DATABASE_URL_UNPOOLED` through `connection(migration=True)`. Both variables are required for migrations: the direct URL must name the same endpoint, effective port, database and user as the Broadbridge URL. For Neon, comparison removes only the first hostname label's `-pooler` suffix; the migration hostname itself must be unpooled. Matching explicit local PostgreSQL URLs are also supported. Local hostname aliases are not guessed equivalent: use the same host spelling in both URLs.

Migration checks decode URI identifiers and refuse missing/mismatched targets, keyword connection strings, query routing overrides and inherited `PGHOSTADDR`, `PGSERVICE`, `PGPORT` or `PGOPTIONS` overrides. They never print credentials. Passwords may differ; endpoint, database and user binding is checked independently of credentials. This module never reads `DATABASE_URL`, another project's configuration or root `.env` automatically. Export the dedicated URLs through your approved local secret mechanism before invoking a command; do not put them in a command log or commit them.

```powershell
python packs/oil-gas/scripts/db.py migrate
python packs/oil-gas/scripts/db.py status
```

`migrate` takes a transaction advisory lock, validates SHA-256 checksums for every applied migration and runs missing SQL in filename order. The caller's transaction owns all changes. Editing an applied migration or removing its file is refused; add a new migration for subsequent changes. `status` returns the last version, applied filenames and exact table counts without displaying credentials.

`0001_init.sql` creates tables, foreign keys, indexes and the vector extension. `0002_constraints.sql` adds full canonical shape validation, enum and indexed JSON consistency checks, signoff gates, revision/actor stamping, question projection and audit triggers, shared save functions and the training view. Its immutable JSON Schema validator supports the vocabulary used by the embedded canonical case schema and fails closed on unsupported validation keywords. A parity test compares the embedded schema with `case_record.schema.json`; contract changes require a new migration. The migration runner creates `broadbridge.schema_migrations` as its checksum ledger. Both SQL files use LF line endings, so Git normalization preserves their checksums.

## Shared writes and revisions

Both Python and the capture application call parameterized SQL:

```sql
SELECT broadbridge.save_case($1::jsonb, $2::text, $3::timestamptz);
SELECT broadbridge.save_workflow($1::jsonb, $2::text);
```

`save_case(record, actor, expected_updated_at DEFAULT NULL)` returns `{"record": <canonical JSON>, "revision": <database timestamp>}`. Pass the prior returned revision for optimistic concurrency. A mismatch or missing record with an expected revision raises SQLSTATE `40001`. The application must reload/resolve the conflict before retrying; it must not silently overwrite.

The case JSON's `created_at` and `updated_at` remain verbatim. The `cases.updated_at` database column is a separate monotonic revision and audit timestamp. An exact same-record, same-actor save leaves the revision and audit history unchanged. A changed actor updates audit metadata/revision without inventing a status/signoff event. The trusted server must supply the authenticated actor; browser-submitted actor identity is not authorization.

Case writes take a shared transaction advisory lock for this pilot. The AFTER trigger projects `record.questions` to `questions`, removes deleted questions and recomputes the strictest requested split for both the old and new families: `train < dev < locked_test`. A moved or deleted holdout can therefore demote its former family. Direct question mutations and truncation are refused; change case JSON through `save_case`. Family IDs are case-sensitive, matching the existing importer.

Case, question, source and evidence IDs have `lower(id)` unique indexes. The importer additionally applies Python `casefold()` collision checks. PostgreSQL 17 `lower()` is not full Unicode casefold: unusual pairs such as `ß`/`ss` can collide in the importer without colliding in SQL. Normal generated ASCII IDs agree. The canonical schema has not been narrowed to hide this limitation.

`status='signed'` requires Boolean `reviewer_signoff.signed=true`, a nonblank reviewer name/date and no `unknown`/`undecided` marker. Editing accepted case content while retaining signed status and unchanged signoff is refused. Save as draft/complete with cleared signoff, or provide renewed complete signoff. Permission changes are audited and do not require a new signature merely to revoke access. Signoff name/date edits are audit events even if the Boolean signed flag stays true.

Review history contains full old/new JSON snapshots, the explicit actor, operation and timestamp for insertion, deletion, and status/signoff/permission changes. UPDATE/DELETE/TRUNCATE of the history are refused. Database owners still retain PostgreSQL owner powers; application credentials should not be granted migration/owner privileges in production.

`train_candidates` exposes `case_id`, `family_id`, `question_id`, `type`, effective `split`, `permitted_use`, question JSON and full case JSON. It requires signed status, training permission, complete signoff and effective `train`; unknown/undecided identity markers are excluded, matching the importer's admission policy. This restricted view contains reference answers: it is a dataset preparation input, not a model prompt projection. Revoking permission/signoff immediately removes candidates.

## Python API

`scripts/db.py` exports:

- `connection()`: context manager yielding a psycopg connection with `autocommit=False` and `prepare_threshold=None`; commits on successful exit and rolls back on failure. Connection errors are sanitized.
- `migrate(conn)` and `status(conn)`: structured migration/count results.
- `upsert_case(conn, case, actor, expected_revision=None)`: canonical validation and the shared case function; returns record/revision.
- `upsert_workflow(conn, workflow, actor)`: export-contract validation and the shared workflow function; uses lowercase actor as `author_email` and returns record/revision.
- `upsert_source(conn, record, actor)` and `upsert_evidence(conn, record, actor)`: preserve register JSON and return the natural ID. Evidence requires an explicit existing `source_id`, with optional existing `case_id`; no source permission or relationship is inferred.
- `upsert_run(conn, brief_run, actor)`: validates the envelope/brief, requires an existing case, and returns SHA-256 of canonical entire run JSON. That ID makes replay idempotent.
- `upsert_scorecard(conn, case, brief_run, markdown, actor)`: validates the historical case/run pairing, upserts the run and scorecard, and returns its run ID.
- `effective_splits(conn, family_ids)`: returns `{family_id: effective_split}` for database families with questions, so importing a partial export cannot overlook an existing holdout.

Helpers do not commit internally. Run and scorecard writes retain their historical snapshot hashes and never replace the current case with an older file. Use one caller transaction for associated operations. PostgreSQL and local files do not share a distributed transaction; the publication layer must stage/publish/compensate ordinary failures and document crash recovery separately.

### File publication and recovery

`import_cases.py`, `extract_evidence.py`, `run_brief.py` and `score_brief.py` accept `--db --actor EMAIL`. Their publication helper writes to a staging location, performs SQL changes in one transaction, publishes files, and then commits. An ordinary exception rolls SQL back and restores/removes the files created by that operation. A process crash or a lost connection during COMMIT can leave an uncertain outcome; filesystem publication and a remote PostgreSQL commit cannot be made one atomic transaction.

If an operation exits unexpectedly, stop other writers to that run directory. Preserve the input, files and any staging/backup directories; do not delete them or assume a retry is harmless. Run `db.py status`, then compare the affected natural keys and canonical JSON with the input: `cases.case_id`, `evidence.evidence_id`, `runs.run_id` (SHA-256 of the complete brief-run envelope), and `scorecards.run_id`. The database case's separate revision can be newer than the imported file: retain that newer record and resolve the difference before retrying an import. For immutable runs, reuse the saved envelope rather than invoking the model again. Once the database outcome is established, publish matching snapshots to a new output directory or retry the original idempotent upsert from the preserved input. Keep reviewer-edited scorecards; never replace them with blank templates. If the original transaction is still in progress, wait for its outcome before reconciling.

After a reviewer fills a generated Markdown scorecard, synchronize it with:

```powershell
python packs/oil-gas/scripts/score_brief.py <case.json> <brief_run.json> <eval-directory> --db --actor <reviewer-email> --sync-existing
```

This validates completed review fields and the protected question/reference/brief content, preserves the file, and upserts the completed sheet. Generating an unreviewed template over an existing database review is refused. Neither command signs off on behalf of a reviewer.

### Capture app migrations

`0003_capture_auth.sql` adds email users, hashed one-use verification tokens and issuance cooldowns. `0004_capture_actions.sql` adds browser save/delete functions that require the loaded revision: a null revision permits creation only. Browser workflows and CLI workflow imports share a lock. The app uses these functions; the importer retains its explicit upsert behavior. See `docs/CAPTURE_APP.md` at the repository root for deployment and the intake transition.

## Reset safety

```powershell
python packs/oil-gas/scripts/db.py reset-dev --branch test
```

Reset requires explicit `--branch dev|test`, a verified non-main/non-master/non-detached Git branch, a loopback URL without query overrides and a database named `broadbridge_test`, `broadbridge_dev` or either prefix followed by an underscore suffix. The connected libpq peer address and database name are checked again before dropping only `broadbridge`. `vector` remains installed.

All remote reset targets, including Neon, are refused. A future remote reset implementation requires an allowlisted project/endpoint-to-nonprimary-branch binding; a user-provided branch label alone is insufficient. Migrations and non-destructive writes can use the explicitly configured dedicated Neon URL.

## Test runner

```powershell
& packs/oil-gas/db/test.ps1 -Python C:/Python313/python.exe
```

With a URL already exported, the runner tests that database. With no URL, it uses Docker and a locally cached `pgvector/pgvector:pg17` image, starts one uniquely named disposable container on an ephemeral loopback port, runs the suite and removes only the container whose ID and ownership label it created. It never pulls an image or automatically loads `.env`. Docker Desktop pipe access may require the environment's normal approval mechanism.

Tests require empty capture tables and use transactions that roll back all test writes. They refuse a nonempty database. Local URLs must name a `broadbridge_test` database. To test a freshly created disposable remote development branch, first verify that branch's project/endpoint in the provider, then export `BROADBRIDGE_TEST_DATABASE_HOST` equal to its exact URL hostname. Remote query options are restricted to TLS/channel-binding/connect-timeout settings. Remote schema-reset verification is skipped; the suite never truncates or resets remote storage. Never point these tests at a production branch.

## Recorded local verification — 24 September 2026

The initial missing-helper test failed before implementation. Nine review regression cases also failed before their fixes. PostgreSQL **17.11**, pgvector **0.8.6**: the final suite passed **48 tests in 13.25 seconds** on the explicitly configured isolated `broadbridge_test_core` database. The concurrent-writer test verifies that a second writer waits for the first transaction and rechecks the revision after it rolls back. The final fresh-container offline fallback independently passed **48 tests in 13.43 seconds**, returned exit code 0 and removed its owned container.

Checks cover migration idempotence/checksums, vector, canonical schema parity and malformed nested records, enum rejection, indexed JSON consistency, natural-ID collisions, explicit actor/revision handling, whitespace/unknown signoff rejection, training identity markers, signoff/permission audit and revocation, append-only history, old/new family split closure and demotion, direct question protection, source/evidence FKs, run idempotence, scorecard snapshot binding, historical/current capture separation, concurrent writers, transactional rollback, connection sanitization and reset guards.

After tests, all eight capture table counts were zero; the checksum ledger contained `0001_init.sql` and `0002_constraints.sql`. This local verification does not claim Neon execution or seeded production data.

The following inventory was read from `information_schema.columns` using:

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'broadbridge'
ORDER BY table_name, ordinal_position;
```

| Relation | Columns and SQL types |
| --- | --- |
| cases | case_id text; family_id text; status text; permitted_use text; signed boolean; updated_at timestamp with time zone; updated_by text; record jsonb |
| evidence | evidence_id text; source_id text; case_id text; record jsonb; updated_at timestamp with time zone; updated_by text |
| questions | question_id text; case_id text; type text; requested_split text; effective_split text; record jsonb |
| review_log | review_id bigint; case_id text; operation text; actor text; old_record jsonb; new_record jsonb; created_at timestamp with time zone |
| runs | run_id text; case_id text; mode text; case_sha256 text; prompt_sha256 text; record jsonb; created_at timestamp with time zone; updated_by text |
| schema_migrations | version text; checksum text; applied_at timestamp with time zone |
| scorecards | run_id text; case_id text; markdown text; updated_at timestamp with time zone; updated_by text |
| sources | source_id text; record jsonb; updated_at timestamp with time zone; updated_by text |
| train_candidates (view) | case_id text; family_id text; question_id text; type text; split text; permitted_use text; question jsonb; case_record jsonb |
| workflow | author_email text; record jsonb; updated_at timestamp with time zone; updated_by text |
