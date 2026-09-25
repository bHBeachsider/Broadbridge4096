# Broadbridge ingestion live setup — 25 September 2026

Status: private dev bucket and exact-origin CORS configured; local Docker approved
and R2/CPU smoke exercised. Neon dev currently rejects its configured password,
and branch-specific Preview email settings remain pending. Browser-to-worker live
acceptance is not complete. This record continues the draft PR stack and does not
authorize a merge or production release.

## Verified destinations

| Resource | Explicit target | Result |
|---|---|---|
| Neon project | `crimson-block-71962201` / `broadbridge-oil-gas` | Existing user-approved project; PostgreSQL 18 |
| Neon branch | `dev`, endpoint `ep-restless-bread-au1nwu5h` | Root `.neon` and pooled URL agree; direct URL matches the same database identity |
| Neon production | `br-old-leaf-au0q8w6y` | Not used by this work |
| Vercel owner/project | `bhbeachsiders-projects/broadbridge-capture` | CLI authenticated; project root `apps/capture`, Next.js, Node 24 |
| Preview branch | `codex/broadbridge-ingestion-live-test` | Pushed; branch-specific pooled dev database Secret created and metadata verified |
| Existing R2 bucket | `broadbridge`, account `af7446fd472b9a8d087250687882a487` | Authenticated HEAD returned 200; CORS read returned AccessDenied |
| Test bucket | `broadbridge-dev`, same account | Created after confirming it was absent; public access disabled; authenticated HEAD 200 |
| CPU runtime | Existing local Docker image `foundry-ingestion:acceptance` | Brad approved local Docker; Docker 29.8.0 and the pinned non-root image verified |

Always specify these targets. The shell's ambient bucket, Neon project, and
Vercel team point to other projects. No unrelated bucket or database was accessed.
The existing `broadbridge` bucket is unchanged. Both environments use project prefix
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

1. **Cloudflare access and test bucket — verified.** Brad's signed-in Edge session
   is accessible. The account initially contained `broadbridge`, but not
   `broadbridge-dev`; the separate test bucket was created with private defaults.
   Current operator S3 credentials can access it but cannot inspect CORS through
   S3. Dashboard configuration was used instead. Service credentials restricted
   to the test bucket are still required before deploying a persistent worker or
   copying storage credentials into Vercel. Existing broad operator credentials
   were used only for the bounded local test, never copied to Vercel.
2. **Preview database — configured.** Added branch-specific
   `BROADBRIDGE_DATABASE_URL` from the verified pooled dev URL using stdin.
   Vercel metadata confirms a hidden Secret limited to
   `codex/broadbridge-ingestion-live-test` in Preview. Earlier attempts before the
   branch was pushed did not create a setting; the post-push attempt succeeded.
   Production was not read or changed. Deploy after all required settings are
   complete so the deployment receives the new configuration. On the subsequent
   access check, the root pooled URL still identified the approved dev endpoint
   but failed password authentication. Brad was asked to refresh both dev URLs
   locally. Do not treat the older Preview secret as current after that refresh;
   update the branch-specific Preview database secret from the verified new URL.
3. **Preview email.** `RESEND_API_KEY` and `CAPTURE_EMAIL_FROM` currently exist
   for Production only. Add the approved values for the live-test Preview branch.
   `AUTH_SECRET` and `CAPTURE_ALLOWED_EMAILS` already have Preview entries. Do
   not enable the local email outbox or local integration test bypass on Vercel.
   Automatic approval review rejected an attempted expansion of the two Production
   email variables to all Preview deployments. The rejected command did not run;
   the existing entries are unchanged. Brad was asked to create Preview entries
   scoped specifically to `codex/broadbridge-ingestion-live-test`.
4. **CPU host — local Docker approved; HTTPS still pending.** First test uses the
   existing local CPU container.
   A remote Vercel Preview needs a reachable HTTPS service, its server-side bearer
   token, and a trusted proxy; localhost on this PC is not reachable from Vercel.
   Final cloud CPU hosting, exposure and budget remain a separate concrete decision.
5. **Storage and worker variables.** Configure the approved test bucket and scoped
   credentials for both services. The capture app uses `R2_ENDPOINT`; the engine
   uses `R2_ENDPOINT_URL`. Both use `R2_BUCKET`. Non-secret `R2_ENDPOINT` and
   `R2_BUCKET=broadbridge-dev` are now set and metadata-verified for the isolated
   Preview branch. Storage secrets and the live API connection remain pending.
   The worker uses
   `INGESTION_DB_ENV=BROADBRIDGE_DATABASE_URL`, `INGESTION_DB_SCHEMA=broadbridge`,
   `INGESTION_PROJECT_ID=broadbridge-oil-gas`, `INGESTION_RECIPE_VERSION=oil-gas-v1`,
   and the absolute external `INGESTION_PACK_PATH`. Set `INGESTION_API_URL` and
   secret `INGESTION_API_TOKEN` in Preview only. Separate API and worker processes.
6. **CORS configured; events pending.** The test bucket allows PUT from exactly
   `https://broadbridge-capture-git-codex-bro-d2e7c0-bhbeachsiders-projects.vercel.app`
   with `content-type`, `if-none-match`, `x-amz-meta-sha256`,
   `x-amz-meta-source-id`, `x-amz-meta-revision-id`; exposes `ETag`; and uses a
   300-second preflight cache. There is no wildcard origin. Real HTTP preflight
   accepts that origin and denies an unrelated origin. The dashboard reports
   that R2 event notifications require Workers Paid; no upgrade was purchased.
   The initial intake can enqueue explicitly through the implemented API while
   event transport remains a separate live gate. Before enabling automatic events,
   provision a test queue, dead-letter queue and Workflow with the same fixed
   project/recipe/bucket and object-create events only for
   `incoming/broadbridge-oil-gas/`. Use the Foundry transport
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

## Live R2 and local CPU evidence

The final run `r2-cpu-3ea716fb4034` passed **27 checks** for two synthetic inputs:
a text process report and a CSV observation table. See
[machine-readable evidence](verification/ingestion-live-r2-cpu.json). It used the
actual private R2 service and the existing Docker image
`sha256:8e170e65112a90c57dc91b90f6c2f7daa14b16636c901d84aa50b3ab16fc3991`.

- Exact Preview-origin CORS preflight accepted; unrelated origin denied.
- Presigned requests bind Content-Length; altered-size uploads returned 403.
- Initial PUT succeeded; duplicate immutable PUT returned 412.
- Original downloaded bytes and SHA-256 matched both fixtures.
- Anonymous reads were denied. R2 returns HTTP 400 `InvalidArgument` with an
  authorization-related message when the Authorization header is absent. The
  probe initially expected only 403/404; after inspecting that response, it was
  corrected to accept this specific missing-authorization error as well. It
  continues to reject a returned source body or an unrelated HTTP 400 error.
- Duplicate enqueue preserved job identity; both CPU extractions completed.
- Each command used a fresh container; durable job state survived those restarts.
- Normalized artifact hashes, source identity and nonempty extraction blocks
  matched. Sources remained pending and `reference_only`, with no training grant.

The containers ran as the image's non-root user, with a read-only root filesystem,
all capabilities dropped, no-new-privileges, bounded temporary storage, 8 GiB
memory, 4 CPUs and 256 PIDs. The external oil-gas pack was mounted read-only.
Only generated fixtures were supplied; no original expert files or local model
weights were mounted. Docker outbound networking was enabled for R2, so this
test does not establish a production egress allowlist. Test containers stopped
automatically. Synthetic objects and local receipts remain available for audit.

Because Neon rejected its configured dev password, this run used a disposable
**local SQLite queue**. It does not establish Neon job persistence, deployed
Next.js signing, browser login/uploads, Cloudflare event delivery, human review,
dataset release, OCR/ASR, model inference or fine-tuning. The initial 21-check run
passed before the size and anonymous-read checks were added; the final expanded
run above is the acceptance record for this limited storage/CPU scope.

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
Brad subsequently confirmed the key was rotated; the old API key was not reused.
The value is omitted from these artifacts and must not be repeated. It was not
used for subsequent Neon API requests. The verified database credentials used
for migration are distinct from that API key. Avoid invoking that CLI's help
with secret variables inherited by the process.
