# Broadbridge ingestion pipeline runbook

This runbook binds the generic Foundry ingestion engine to the
`broadbridge-oil-gas` pack. It covers offline and operator-controlled steps. It
does not establish live R2, Neon, worker, model, or production acceptance.

## Bound resources and configuration

The private originals store is the Cloudflare R2 bucket `broadbridge` at
`https://af7446fd472b9a8d087250687882a487.r2.cloudflarestorage.com`. The bucket
and endpoint were supplied separately; access and contents remain unverified.
Only `incoming/broadbridge-oil-gas/` produces intake events. Derived prefixes in
`ingestion.yaml` must never feed the intake trigger.

The worker selects the `broadbridge` database binding through
`INGESTION_DB_ENV`. That binding names `BROADBRIDGE_DATABASE_URL` and schema
`broadbridge`. Runtime code receives the pooled URL explicitly and never falls
back to `DATABASE_URL`, PermitHub, a root `.env`, or a generic hardcoded DSN.
Only the existing `scripts/db.py migrate` path reads
`DATABASE_URL_UNPOOLED`; it verifies that the direct migration identity matches
the dedicated Broadbridge runtime identity. Constructors do not run DDL.

Required environment names for a live operator are:

- `INGESTION_DB_ENV=broadbridge`
- `BROADBRIDGE_DATABASE_URL` for runtime database access
- `DATABASE_URL_UNPOOLED` only while applying migrations
- the generic worker's R2 endpoint, bucket, access-key and secret-key variables
- the generic worker bearer secret and pack path

Do not put values, signed URLs, source manifests, or customer records in Git.

## Source intake and durable jobs

The capture server authorizes a unique incoming object key and registers the
intended full `foundry.source_revision/1` before upload by calling:

```sql
SELECT broadbridge.register_source_revision($source_json, $registry_ref, $actor);
```

The function atomically creates the independent `broadbridge.sources` parent
when needed and records the immutable revision. Initial permission is always
`pending`. The returned `source_ref` is the immutable registry object key passed
to the generic runner. After upload, the server verifies actual size and SHA-256
against the registered values before it writes the trusted manifest and
enqueues. An upload mismatch remains un-enqueued and visible for reconciliation.

The generic HTTP service owns the runner routes. Its job submission body is
`{ "source_ref": "<immutable registry object key>" }`; the server selects the
recipe. Status comes from the job resource, retry uses the generic retry route,
and attachment admission uses the generic attachment route with an empty body.
Attachment references appear in the job result. This domain pack defines no
competing HTTP routes.

`broadbridge.ingestion_jobs` has the generic 16-column PostgreSQL layout. Query
source identity through `source_json::jsonb` and show sanitized job errors. A
job's original source JSON remains unchanged when later rights decisions occur.

## Rights and technical review

Classification labels describe technical content only. They never grant
rights. Rights review is append-only and bound to source ID, revision ID, and
content SHA-256:

```sql
SELECT broadbridge.review_source_rights(
  $source_id, $revision_id, $content_sha256,
  $decision, $permitted_use, $rights_basis,
  $expected_review_id, $actor
);
```

`decision` is `approved` or `revoked`. The basis and caller actor must be
nonblank. A null expected review ID is accepted only before the first decision;
a stale value raises SQLSTATE `40001`. Read the overlay through
`broadbridge.ingestion_source_status`. Revocation changes current eligibility
without rewriting the intake manifest or prior job.

Candidate technical review is separate:

```sql
SELECT broadbridge.register_candidate($candidate, $candidate_hash, $actor);
SELECT broadbridge.review_candidate(
  $example_id, $candidate_hash, $decision, $reason,
  $expected_review_id, $actor
);
```

Technical review binds the exact candidate hash and uses the same stale-review
rule. It cannot grant source rights. Dataset release additionally requires the
explicit named approval in the generic manifest to bind
`candidate_content_hash` to `release_id`.

## Canonical case and source adaptation

Run the adapter only with explicit absolute paths. It imports the generic engine
from that checkout and does not copy engine code:

```powershell
python packs/oil-gas/scripts/ingestion_adapter.py `
  --foundry C:\absolute\path\to\slm-foundry `
  --pack C:\absolute\path\to\Broadbridge4096\packs\oil-gas `
  cases --input C:\private\capture-export.json --output C:\private\adapted.json
```

The case path validates the unchanged `broadbridge.case_record/1` contract.
Only `status=signed` and `identity.permitted_use=training` cases become
examples. Family split closure is computed across every question in every case,
including excluded cases: `dev` maps to `val`, `locked_test` maps to `test`, and
the strictest family assignment wins. User messages contain decision-time data
only; the reviewed `reference_answer` is the assistant target.

The `source` adapter mode consumes an existing source record, evidence records,
and an explicit generic source revision. A source may exist without a case. It
produces a normalized document with provenance and pending classification; it
never manufactures a case, reviewer, rights decision, or signed answer from a
report.

## Releases, model runs, and recovery

Record an approved immutable release with
`broadbridge.record_dataset_release(manifest, actor)`. The actor must match the
manifest reviewer and the approval hash must equal the release ID. Model state
uses append-only revisions through
`broadbridge.record_model_run(record, expected_revision, actor)`; read the latest
state through `broadbridge.current_model_runs`. A retry may add a new state only
for the same run, release, and dataset hash.

For an interrupted worker, read the durable job first. Retry only a retryable or
failed job through the generic service. Expired leases are fenced by the engine.
If object output exists without a successful fenced completion, use the generic
reconciliation operation; do not hand-edit job rows or overwrite immutable
objects. Rights revocation blocks future admission and should trigger the
generic release-impact lookup before another model is approved.

## Local verification and live gates

Database tests accept only an explicitly supplied loopback database named
`broadbridge_test_ingestion_*` through
`BROADBRIDGE_INGESTION_TEST_DATABASE_URL`. Use a fresh owned PostgreSQL 17 image
with pgvector, apply migrations 0001 through 0005, run the focused test, then
stop and remove only that ownership-labeled container. The committed synthetic
evidence is in `packs/oil-gas/db/verification/ingestion-T6.json`.

Still open: scoped R2 credentials and private-access verification, dedicated
nonproduction Neon/R2/Vercel mapping, CPU worker host and parser artifacts,
retention and upload limits, approved real rights authority, reviewed training
batch, bounded GPU budget, real QLoRA/evaluation, and production promotion.
No cloud upload, remote inference, EC2 action, or production migration is part
of the local T6 acceptance.
