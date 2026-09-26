# Broadbridge ingestion live setup — 25 September 2026

Status: the updated R2 credentials passed live writes. The actual R2/Docker/Neon
dev smoke passed 19 checks for two synthetic documents, followed by all six HTTPS
checks. Preview storage/API settings were refreshed and the test Preview reached
READY. Deployed human sign-in and browser uploads remain pending. Temporary Docker
services were stopped after verification. All work remains on draft PRs; no
production release is authorized.

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
   Dashboard configuration was used for CORS. After Brad updated the service
   credentials, both synthetic PUTs and normalized-artifact reads succeeded.
   Refreshed the isolated Preview branch with the tested local key pair. Do not
   fall back to earlier broad operator credentials; those
   were used only for the historical bounded test below, never copied to Vercel.
2. **Preview database — configured.** Added branch-specific
   `BROADBRIDGE_DATABASE_URL` from the verified pooled dev URL using stdin.
   Vercel metadata confirms a hidden Secret limited to
   `codex/broadbridge-ingestion-live-test` in Preview. Earlier attempts before the
   branch was pushed did not create a setting; the post-push attempt succeeded.
   Production was not read or changed. Deploy after all required settings are
   complete so the deployment receives the new configuration. After Brad repaired
   both dev URLs, the pooled connection passed locally and from Docker. Updated
   only this branch's Preview database secret from the verified local URL.
   Readback confirms PostgreSQL 18.6, five matching migration checksums and the
   unchanged capture counts listed above. The database password blocker is closed.
3. **Preview email — present.** Brad added Preview to `RESEND_API_KEY` and
   `CAPTURE_EMAIL_FROM`; metadata confirms Production and Preview scopes.
   `AUTH_SECRET` and `CAPTURE_ALLOWED_EMAILS` already have Preview entries.
   An earlier attempted scope expansion by the agent was rejected and did not
   run; Brad subsequently made the configuration change himself. Normal deployed
   magic-link login still requires a human test. Do not enable a local test bypass.
4. **CPU host — temporary Docker/HTTPS test performed, now stopped.** A private
   Docker network joined the non-root API, an unprivileged Nginx proxy and a
   temporary Cloudflare tunnel. No host port was published. The API required a
   bearer token on all routes. This was a bounded pilot runtime, not persistent
   hosting. A later session must start a fresh runtime, replace the branch API
   URL/token, redeploy Preview and verify the connection. Final cloud hosting
   and budget remain a separate decision.
5. **Storage and worker variables.** Configure the approved test bucket and scoped
   credentials for both services. The capture app uses `R2_ENDPOINT`; the engine
   uses `R2_ENDPOINT_URL`. Both use `R2_BUCKET`. Non-secret `R2_ENDPOINT` and
   `R2_BUCKET=broadbridge-dev` are now set and metadata-verified for the isolated
   Preview branch. The R2 key pair and `INGESTION_API_URL`/`INGESTION_API_TOKEN`
   were refreshed in that branch and tested. The temporary API is now offline;
   a fresh session must replace its URL/token before browser-to-worker testing.
   Presence alone is not verification.
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

## Repaired configuration and follow-up tests

The historical 27-check test above predates the repaired Neon credentials and
current service key. The new Neon/R2 smoke stopped on its first registry object
write: R2 returned 403 AccessDenied. It did not reach case/source database upserts
or extraction. Current capture counts remain 5 sources, 0 evidence, 4 cases,
4 questions, 1 workflow, 0 runs, 0 scorecards and 20 review-log entries.

Real CLI serving exposed a Foundry exception-class identity bug. A dedicated
fix delegates the module entry point to canonical `main`, preserving 404/409
domain errors instead of returning generic 400. See
[Foundry draft #8](https://github.com/bHBeachsider/slm-foundry/pull/8), head
`877d43c`, after draft #7. The new subprocess regression
and 47 focused tests passed; the full local suite recorded 473 passed and
2 skips. The test API image was
`sha256:712863f27cdd2e69398e00572b049464c0ca653de347cff7d6043d68a53fd197`,
built from the earlier acceptance image with only the corrected CLI file.

An earlier HTTPS probe passed six checks (missing/wrong token, missing job,
oversized body, unregistered source and mismatched recipe). The final shutdown
recheck confirmed the two expected 401 responses, then failed at the authenticated
missing-job assertion. Its actual response was not retained, so the cause is
unresolved; do not count current authenticated connectivity as accepted.
All three task containers were stopped and a fresh Docker listing confirmed
none remained. The local watchdog also bounded runtime lifetime to two hours.

See [historical follow-up evidence](verification/ingestion-live-followup.json).
The later accepted recheck below supersedes its connectivity status, without
claiming to establish the cause of the earlier failure.

## Updated credentials: live dev acceptance passed

Run `neon-r2-cpu-d25c0dcc4c24` passed **19 checks**, including immutable synthetic
uploads, idempotent Neon registration/enqueue, two completed CPU extractions,
fresh-container job recovery, independent database reads, artifact/source hash
matching and retained pending/reference-only permissions. Existing capture case,
question, workflow, run and scorecard counts were unchanged. Sources increased
from five to seven, solely for the two labeled synthetic inputs; review_log
remained 20. This used Neon dev, not the older SQLite substitute.

A fresh temporary runtime `bb-ingest-23181554fa` passed all six HTTPS checks:
missing/wrong tokens returned 401, authenticated missing job returned 404,
oversized request returned 413, and unregistered source/mismatched recipe
returned 409. Its first connection attempt preceded hostname resolution; after
DNS resolved, the complete probe succeeded without loosening assertions.

Refreshed only this branch's R2 key pair and API URL/token. Vercel redeployment
`dpl_B9muHKNk3qFqg2FTTp3b1t3ubK3n` reached READY as a Preview. The branch alias
opened the real sign-in page in Edge. Brad must complete normal sign-in before
the browser upload path can be exercised; no auth bypass or email interception
was used. The runtime was stopped after these checks. Restart the API and a
bounded worker, refresh the branch URL/token and redeploy for that next session.

See [live Neon/R2/CPU evidence](verification/ingestion-live-neon-r2-cpu.json).
Foundry draft #8's Cloudflare, Python and container CI jobs all passed. No EC2
or model call was used for these ingestion checks. A separate, synthetic-only
[OpenRouter/Jev study](OPENROUTER_MODEL_SELECTION.md) records model research;
none of its outputs entered the ingestion dataset.

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
