# Broadbridge ingestion pipeline runbook

This runbook binds the generic Foundry ingestion engine to the
`broadbridge-oil-gas` pack. It covers offline and operator-controlled steps. It
does not establish live R2, Neon, worker, model, or production acceptance.

## Bound resources and configuration

The private originals store is the Cloudflare R2 bucket `broadbridge` at
`https://af7446fd472b9a8d087250687882a487.r2.cloudflarestorage.com`. The bucket
and endpoint were supplied separately; access and contents remain unverified.
Only `incoming/broadbridge-oil-gas/` produces intake events. The generic runner
uses `originals/broadbridge-oil-gas/`, `artifacts/broadbridge-oil-gas/`,
`registry/broadbridge-oil-gas/`, and `recipes/broadbridge-oil-gas/`. Those four
prefixes must never feed the intake trigger.

The generic worker receives the environment-variable name
`INGESTION_DB_ENV=BROADBRIDGE_DATABASE_URL` and the dedicated schema
`INGESTION_DB_SCHEMA=broadbridge`. There is no `broadbridge` alias translation.
Runtime code receives the pooled URL explicitly and never falls back to
`DATABASE_URL`, PermitHub, a root `.env`, or a generic hardcoded DSN.
Only the existing `scripts/db.py migrate` path reads
`DATABASE_URL_UNPOOLED`; it verifies that the direct migration identity matches
the dedicated Broadbridge runtime identity. Constructors do not run DDL.

Required environment names for a live operator are:

- `INGESTION_DB_ENV=BROADBRIDGE_DATABASE_URL`
- `INGESTION_DB_SCHEMA=broadbridge`
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

## Candidate registration and release bridge

The release bridge consumes no model endpoint. It accepts one pending
`foundry.training_example/1`, a JSON list of pending examples, or the capture UI
shape `{ "examples": [...] }`. Each example must already contain its messages,
task type, family, requested split, and block-level source references. The
command resolves those references through a successful durable job and its
exact `result.normalized` receipt. It verifies the stored bytes, receipt,
normalized-document hash, and immutable source revision before generic curation
derives document/block quality flags and strict family splits. Only then does it
record the exact candidate hash for technical review.

Submit every member of an affected family in the same registration batch,
including intended exclusions and holdouts. If a later candidate introduces a
stricter family split, source-quality flag, or near-duplicate flag, re-register
the complete affected family and review the returned hashes. Preparation
re-runs global curation across all current candidates and refuses any silent
post-review change. Historical assignments from every immutable candidate
version also constrain its family: replacing a test/validation example or
adding a new family member cannot move that family into training. Registration
applies this closure before hashing and review. A legacy version that bypassed
the rule must be re-registered and reviewed; changing its family ID is refused.

Use an explicit local object root for offline operation:

```powershell
$env:BROADBRIDGE_DATABASE_URL = 'postgresql://...dedicated pooled URL...'
python packs/oil-gas/scripts/ingestion_release.py `
  --foundry C:\absolute\path\to\slm-foundry `
  --pack C:\absolute\path\to\Broadbridge4096\packs\oil-gas `
  --local-object-root C:\absolute\private\objects `
  register-candidates --input C:\private\pending-candidates.json `
  --actor builder@example.com --output C:\private\registered.json
```

The JSON output contains IDs, hashes, quality flags, and artifact receipt
metadata. It does not echo messages or document content. Review the returned
`candidate_hash` through `broadbridge.review_candidate`; the pending candidate
record itself remains immutable.

Prepare the exact generic candidate after source-rights and technical reviews:

```powershell
python packs/oil-gas/scripts/ingestion_release.py `
  --foundry C:\absolute\path\to\slm-foundry `
  --pack C:\absolute\path\to\Broadbridge4096\packs\oil-gas `
  --local-object-root C:\absolute\private\objects `
  prepare-release --output C:\private\prepared-release.json
```

An optional `--exclusions` file uses the generic acknowledged-exclusion
contract. Excluded examples remain in curation so their families still affect
strictest split closure. The prepared output contains dispositions and
`candidate_content_hash`, but no training message content.

Current revoked, pending, testing-only, and reference-only source permissions
produce explicit ineligible dispositions. Acknowledging their exclusions lets
unrelated approved examples proceed; omitting an acknowledgement still blocks
release. Source/artifact integrity is verified even for excluded examples.
Rights changes invalidate the previous release approval, so prepare and approve
the new hash after recording any exclusion.

The release approver must name that exact hash in a generic approval JSON object:

```json
{
  "status": "approved",
  "reviewer": "release@example.com",
  "reviewed_at": "2026-09-25T15:00:00Z",
  "candidate_content_hash": "<exact prepared hash>"
}
```

Build and record it with the same caller actor as the named reviewer:

```powershell
python packs/oil-gas/scripts/ingestion_release.py `
  --foundry C:\absolute\path\to\slm-foundry `
  --pack C:\absolute\path\to\Broadbridge4096\packs\oil-gas `
  --local-object-root C:\absolute\private\objects `
  build-release --approval C:\private\approval.json `
  --release-root C:\private\releases --actor release@example.com `
  --output C:\private\release-manifest.json
```

For R2, omit `--local-object-root` and supply all four explicit variables:
`R2_ENDPOINT_URL`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, and
`R2_SECRET_ACCESS_KEY`. The bridge does not load `.env` files or AWS profiles.

Preparation uses a repeatable-read database snapshot. Build takes shared locks
on source/job/right/candidate identity and review tables, re-reads current
rights and technical decisions, and re-verifies every bound artifact before it
writes the immutable release. It then records the release with
`broadbridge.record_dataset_release` in the same database transaction. The
object store and PostgreSQL do not provide a distributed transaction: if the
database record fails after publication, the verified immutable release may be
an unreferenced object for operator reconciliation. Never delete or overwrite
it as an automatic retry.

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

The bridge records an approved immutable release with
`broadbridge.record_dataset_release(manifest, actor)` after its final locked
recheck. The actor must match the manifest reviewer and the approval hash must
equal the release ID. Model state
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
The historical-holdout, explicit-exclusion, and NULL-contract regressions and
their SQL column/count evidence are in
`packs/oil-gas/db/verification/ingestion-T6-fixes.json`.

Still open: scoped R2 credentials and private-access verification, dedicated
nonproduction Neon/R2/Vercel mapping, CPU worker host and parser artifacts,
retention and upload limits, approved real rights authority, reviewed training
batch, bounded GPU budget, real QLoRA/evaluation, and production promotion.
No cloud upload, remote inference, EC2 action, or production migration is part
of the local T6 acceptance.
