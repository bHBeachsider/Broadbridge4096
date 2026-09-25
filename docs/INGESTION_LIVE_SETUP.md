# Broadbridge ingestion live setup — 25 September 2026

Status: dev database ready; browser-to-worker live acceptance pending. This record
continues the draft PR stack and does not authorize a merge or production release.

## Verified destinations

| Resource | Explicit target | Result |
|---|---|---|
| Neon project | `crimson-block-71962201` / `broadbridge-oil-gas` | Existing user-approved project; PostgreSQL 18 |
| Neon branch | `dev`, endpoint `ep-restless-bread-au1nwu5h` | Root `.neon` and pooled URL agree; direct URL matches the same database identity |
| Neon production | `br-old-leaf-au0q8w6y` | Not used by this work |
| Vercel owner/project | `bhbeachsiders-projects/broadbridge-capture` | CLI authenticated; project root `apps/capture`, Next.js, Node 24 |
| Preview branch | `codex/broadbridge-ingestion-live-test` | Isolated worktree based on Broadbridge acceptance commit `75355aeac7528e6fd9592b10951bd68fa8dd363a` |
| Existing R2 bucket | `broadbridge`, account `af7446fd472b9a8d087250687882a487` | Authenticated HEAD returned 200; CORS read returned AccessDenied |
| Proposed test bucket | `broadbridge-dev`, same account | Pending Brad's confirmation and Cloudflare access; not created |
| CPU runtime | Existing local Docker image `foundry-ingestion:acceptance` | Proposed first test host; no hosted service or paid instance provisioned |

Always specify these targets. The shell's ambient bucket, Neon project, and
Vercel team point to other projects. No unrelated bucket or database was accessed.
Keep the existing `broadbridge` bucket unchanged while test storage isolation is
being settled. Both environments currently use project prefix
`incoming/broadbridge-oil-gas/`; a separate test bucket prevents their events,
manifests and artifacts from mixing without changing domain IDs or schemas.
If one bucket is required, implement and test environment namespaces before live
writes; unique upload filenames alone are not environment isolation.

## Migration completed

Applied `packs/oil-gas/db/migrations/0005_ingestion.sql` using the existing
`db.py` migration implementation with an explicitly verified **unpooled dev**
connection. Normal scripts and the application continue to use the pooled
`BROADBRIDGE_DATABASE_URL`. No `neon deploy` migration path was introduced.

The operator wrapper required the root `.neon` project and branch to match the
table above and the pooled host to match the fixed dev endpoint. It removed
inherited libpq `PG*` routing settings before connecting, verified all previous
migration checksums, used a 5-second lock timeout and 30-second statement timeout,
and checked capture counts before committing. A fresh read-only connection then
confirmed 0005 and **zero migration checksum mismatches**.

| Table | Before | After |
|---|---:|---:|
| sources | 5 | 5 |
| evidence | 0 | 0 |
| cases | 4 | 4 |
| questions | 4 | 4 |
| workflow | 1 | 1 |
| runs | 0 | 0 |
| scorecards | 0 | 0 |
| review_log | 20 | 20 |

Verified 51 column definitions across the five new ingestion tables. This is
migration and connectivity evidence, not a live upload or parser test. See
[sanitized migration evidence](verification/ingestion-neon-dev.json).

## Remaining configuration

1. **Cloudflare access and test bucket.** Sign in to the dashboard or configure a
   suitably scoped operator credential through the approved secret store. Current
   S3 credentials can access the existing bucket but cannot inspect CORS. They
   have not been assumed suitable for a new service. Verify public access is off;
   configure scoped upload/service access for the approved test bucket. Do not put
   credentials in PRs, documents or command arguments.
2. **Preview database.** Configure a branch-specific `BROADBRIDGE_DATABASE_URL`
   using the verified pooled dev URL. Check the resulting environment metadata
   before deployment. Do not copy or decrypt the Production database setting.
3. **Preview email.** `RESEND_API_KEY` and `CAPTURE_EMAIL_FROM` currently exist
   for Production only. Add the approved values for the live-test Preview branch.
   `AUTH_SECRET` and `CAPTURE_ALLOWED_EMAILS` already have Preview entries. Do
   not enable the local email outbox or local integration test bypass on Vercel.
4. **CPU host and HTTPS.** First test can use the existing local CPU container.
   A remote Vercel Preview needs a reachable HTTPS service, its server-side bearer
   token, and a trusted proxy; localhost on this PC is not reachable from Vercel.
   Final cloud CPU hosting, exposure and budget remain a separate concrete decision.
5. **Storage and worker variables.** Configure the approved test bucket and scoped
   credentials for both services. The capture app uses `R2_ENDPOINT`; the engine
   uses `R2_ENDPOINT_URL`. Both use `R2_BUCKET`. The worker uses
   `INGESTION_DB_ENV=BROADBRIDGE_DATABASE_URL`, `INGESTION_DB_SCHEMA=broadbridge`,
   `INGESTION_PROJECT_ID=broadbridge-oil-gas`, `INGESTION_RECIPE_VERSION=oil-gas-v1`,
   and the absolute external `INGESTION_PACK_PATH`. Set `INGESTION_API_URL` and
   secret `INGESTION_API_TOKEN` in Preview only. Separate API and worker processes.
6. **CORS and events.** After the preview origin is known, allow that exact origin
   with PUT and `content-type`, `if-none-match`, `x-amz-meta-sha256`,
   `x-amz-meta-source-id`, `x-amz-meta-revision-id`. Preserve other reviewed CORS
   entries; do not use a wildcard origin. Provision a test queue, dead-letter
   queue and Workflow with the same fixed project/recipe/bucket and object-create
   events only for `incoming/broadbridge-oil-gas/`. Use the Foundry transport
   template at `deploy/ingestion/cloudflare/wrangler.jsonc`; keep account-specific
   configuration outside the generic Foundry repository.

Branch-scoped environment command shape (secret values go through stdin or the
dashboard, never `--value`/literal arguments):

```powershell
vercel env add BROADBRIDGE_DATABASE_URL preview `
  --git-branch codex/broadbridge-ingestion-live-test `
  --project broadbridge-capture --scope bhbeachsiders-projects --sensitive
vercel env ls preview codex/broadbridge-ingestion-live-test `
  --project broadbridge-capture --scope bhbeachsiders-projects
```

Use the same branch scope for the other live-test settings. Do not run uploads
until the intended database, storage, email and authenticated CPU endpoint are
verified together. Vercel CLI 60.0.1 is installed globally; installing it in a
second repository does not create a second project-specific installation.

## Live acceptance order

1. Commit and open this handoff as a draft following Broadbridge PR #5. Continue
   to use the cumulative Foundry acceptance branch for generic engine code.
2. Complete the configuration above and deploy a Preview. Read back its branch
   identity and environment configuration; keep production deployment separate.
3. Brad signs in through the normal magic-link flow. Use synthetic text and CSV
   documents only. Register source hashes, upload through presigned PUT, verify
   CORS, exact Content-Length, immutable PUT and bytes-to-hash matching. No test
   magic-link interception on the deployed service.
4. Observe extraction in Neon, test duplicate notification/restart recovery and
   bounded retries, and read normalized evidence through the authenticated UI.
5. Confirm unreviewed data is blocked, approve only labeled synthetic candidates,
   build a batch twice, and verify hashes/idempotence and revocation behavior.
   Test decisions must never serve as real expert or training authorization.
6. Record results and remaining unsupported formats. Separately prepare licensed
   OCR/transcription model artifacts; installing parser packages is insufficient.
7. Admit rights-cleared real material, obtain reviewer acceptance and comparable
   engineering baselines, then present a bounded GPU training request. No EC2,
   base download, QLoRA, or model deployment occurs in this live setup step.

## Credential incident

The installed Neon CLI unexpectedly echoed an inherited `NEON_API_KEY` when
displaying help. Brad was informed and asked to rotate that API key locally.
The value is omitted from these artifacts and must not be repeated. It was not
used for subsequent Neon API requests. The verified database credentials used
for migration are distinct from that API key. Avoid invoking that CLI's help
with secret variables inherited by the process.
