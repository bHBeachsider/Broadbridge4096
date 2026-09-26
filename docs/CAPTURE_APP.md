# Broadbridge capture app

The capture app lives in [`apps/capture`](../apps/capture). It uses Next.js, Auth.js email magic links, Resend, and the dedicated Broadbridge Neon database. The repository's case and export JSON schemas remain authoritative; Python and the app share SQL migrations and case/workflow write functions.

The original [`case-capture.html`](../output/expert-capture/case-capture.html) is preserved. Its field labels, instructions, IBM Plex typography, and steel-blue light/dark design are ported verbatim. The introductory copy still describes document search and later training/retests. Those are roadmap statements retained from the supplied page: this implementation is **v0 S0-cases, with decision-time input only**. It adds no retrieval, embeddings, model calls, or EC2 operations.

## Deployment and database inventory

| Item | Configured target |
| --- | --- |
| Repository | `bHBeachsider/Broadbridge4096` |
| Vercel project / plan | `broadbridge-capture` / Hobby |
| Vercel workspace | `bhbeachsiders-projects` |
| Project dashboard | [Broadbridge capture](https://vercel.com/bhbeachsiders-projects/broadbridge-capture) |
| Vercel root directory | `apps/capture` |
| Neon project | `crimson-block-71962201` — PostgreSQL 18, AWS `us-east-1` |
| Production branch | `production` — `br-old-leaf-au0q8w6y` |
| Requested development branch | `dev` — `br-billowing-morning-audiqy3e` |
| Development endpoint | `ep-restless-bread-au1nwu5h` |
| Preserved earlier rehearsal | `capture-dev` — `br-royal-moon-auq044a1` |
| Production URL | [Broadbridge Case Capture](https://broadbridge-capture.vercel.app) — READY, 24 September 2026 |
| Preview URL | [Verified preview](https://broadbridge-capture-7m79rrfj3-bhbeachsiders-projects.vercel.app) — READY, 24 September 2026 |

The earlier `capture-dev` branch is preserved for its audit rehearsal. It is not the currently selected `dev` target. Production is named `production`, not `main`.

## Select and verify the database

Run the current Neon checkout command from the repository root:

```powershell
npx --yes neon@6.1.0 checkout dev --create --project-id crimson-block-71962201 --agent
```

The older global `neon` alias does not implement this checkout command. Checkout selects the local `.neon` development context and manages standard Neon connection variables, including `DATABASE_URL`; it does **not** keep the application's custom `BROADBRIDGE_DATABASE_URL` synchronized. The coordinating setup explicitly rebound that custom variable to the verified `dev` endpoint.

Before any migration, import, browser test, or deployment, verify the project, branch ID, and endpoint ID in Neon. Load the corresponding values into the current process through the approved secret mechanism. Python does not automatically load root `.env`. Do not print, paste into logs, or commit connection strings.

On this Windows checkout, install the pinned Python dependencies and load only the required dotenv entries into the current shell. The JSON output is captured into a variable, never displayed:

```powershell
python -m pip install -r packs/oil-gas/requirements-db.txt
$captureEnv = (& python -c "import json; from dotenv import dotenv_values; v=dotenv_values('.env'); print(json.dumps({k:v.get(k) for k in ['BROADBRIDGE_DATABASE_URL','DATABASE_URL','DATABASE_URL_UNPOOLED']}))") | ConvertFrom-Json
foreach ($captureKey in @('BROADBRIDGE_DATABASE_URL','DATABASE_URL','DATABASE_URL_UNPOOLED')) {
    $captureValue = $captureEnv.$captureKey
    if (-not $captureValue) { throw "Missing required local variable: $captureKey" }
    [Environment]::SetEnvironmentVariable($captureKey, $captureValue, 'Process')
}
Remove-Variable captureEnv, captureValue
```

For an explicit local rebind after checkout, inspect only parsed metadata and require the expected endpoint before assigning the custom variable:

```powershell
$capturePooled = [uri]$env:DATABASE_URL
$captureDirect = [uri]$env:DATABASE_URL_UNPOOLED
$captureEndpoint = 'ep-restless-bread-au1nwu5h'
if ($capturePooled.Scheme -notin @('postgres', 'postgresql') -or
    $captureDirect.Scheme -notin @('postgres', 'postgresql') -or
    -not $capturePooled.UserInfo -or
    $capturePooled.Host.Split('.')[0] -ne "${captureEndpoint}-pooler" -or
    $captureDirect.Host.Split('.')[0] -ne $captureEndpoint -or
    ($capturePooled.Host -replace '-pooler\.', '.') -ne $captureDirect.Host -or
    $capturePooled.AbsolutePath -ne $captureDirect.AbsolutePath -or
    $capturePooled.UserInfo -ne $captureDirect.UserInfo) {
    throw 'Refusing connection rebind: the expected dev endpoint and matching database/role were not verified.'
}
$env:BROADBRIDGE_DATABASE_URL = $env:DATABASE_URL
```

This is an intentional, endpoint-checked operator assignment. It is not a runtime fallback. The app and normal Python operations read only the pooled `BROADBRIDGE_DATABASE_URL`; they never fall back to `DATABASE_URL`, PermitHub, or another project.

Use `db.py migrate` for the reviewed migration sequence. Migration-only connection selection uses matching `DATABASE_URL_UNPOOLED` for direct DDL; it must match the dedicated pooled target's endpoint, database, role, and port. Do not select an unrelated unpooled URL or use the direct variable for normal app operations. The selection guards passed 45 offline configuration tests, and the command successfully applied the sequence to dev and production using their matching direct connections.

From the repository root, with the verified values exported:

```powershell
python packs/oil-gas/scripts/db.py migrate
python packs/oil-gas/scripts/db.py status
```

Migrations are in [`packs/oil-gas/db/migrations`](../packs/oil-gas/db/migrations): `0001_init.sql`, `0002_constraints.sql`, `0003_capture_auth.sql`, and `0004_capture_actions.sql`. They include the capture tables, canonical checks, audit/family projections, authentication token storage, and revision-checked app actions. Add a new migration when changing an applied contract; do not edit an already applied migration or bypass its checksum.

## Environment and email activation

Existing local dotenv files already contain configuration variables; maintain their values through secret tooling. Configure Vercel variables for the intended **Preview** or **Production** environment, never by embedding them in source or command arguments.

| Variable | Purpose and scope |
| --- | --- |
| `BROADBRIDGE_DATABASE_URL` | Dedicated pooled URL. Preview uses verified `dev`; Production uses the separately verified production branch. Server-side only. |
| `DATABASE_URL_UNPOOLED` | Matching direct connection for the migration command only; not an app fallback. |
| `AUTH_SECRET` | Private Auth.js signing secret, provided through the environment. |
| `RESEND_API_KEY` | Private Resend key for the account allowed to send from the configured domain. |
| `CAPTURE_ALLOWED_EMAILS` | Exact reviewer addresses, separated by commas or newlines. Addresses are trimmed and lowercased; malformed configuration fails closed. |
| `CAPTURE_EMAIL_FROM` | A mailbox on a verified Resend sender/domain, optionally `Broadbridge <mailbox@verified-domain>`. |
| `AUTH_URL` | Production is pinned to `https://broadbridge-capture.vercel.app` so emailed callbacks and the origin guard agree across deployments. Local example: `http://127.0.0.1:3100`. |
| `VERCEL_URL` | Vercel supplies the deployment hostname. With `VERCEL=1`, the app derives its trusted HTTPS origin automatically; avoid pinning all previews to a different deployment's URL. |

**Production email configuration is present:** `bupham@ilyrium.io` and `whurt@antiochrenewables.com` are allowlisted. Production has the Resend key and sender configuration, its separate database URL/Auth.js secret, and `AUTH_URL=https://broadbridge-capture.vercel.app`. The public sign-in page and stable callback URL are verified. Actual mail delivery and reviewer login still need a human check. The ingestion-test Preview now has email configuration and its separate dev database. Pin `AUTH_URL` on that branch to its stable Preview alias, as recorded in [the live setup log](INGESTION_LIVE_SETUP.md). Without this override, Auth.js can use the alias while the origin guard uses the immutable deployment hostname, rejecting the sign-in request before sending mail. Never point a dev Preview at the Production auth origin.

To activate email, configure those values in the intended environment, redeploy so that the running application sees the changes, and complete a real sign-in with an approved reviewer address. Confirm arrival from the verified sender, successful same-origin login, and rejection of a replayed link. Record the result rather than assuming provider configuration implies delivery.

Magic links expire after at most 15 minutes and are single-use. Token creation caps expiry using the database clock, so a small app/DB clock difference does not break issuance or extend the limit. Stored verification values are hashes, and consuming a link deletes the token atomically. Session admission and protected actions recheck the allowlist. To revoke a reviewer, remove their address and apply the updated environment to the running deployment; their **next authenticated request** is rejected, including an existing session. An already open tab may still display previously loaded text until its next request. Rotate `AUTH_SECRET` separately if a wider session invalidation is required.

## Local checks and browser rehearsal

Use Node.js 24 and the committed lockfile. From `apps/capture`:

```powershell
npm ci
npm run typecheck
npm test
npm run build
```

For the local Playwright rehearsal, first bind the database to the verified `dev` endpoint as above and apply its migrations. Configure a temporary test process with:

- `AUTH_URL=http://127.0.0.1:3100` and a development server (`npm run dev`, started by Playwright).
- `AUTH_SECRET` supplied privately.
- `CAPTURE_TEST_EMAIL` set to an explicitly allowlisted synthetic test address, included in `CAPTURE_ALLOWED_EMAILS`.
- `CAPTURE_TEST_OUTBOX` set to a new absolute temporary file path outside tracked artifacts.
- `CAPTURE_DB_TEST_HOST` equal to the exact hostname of the verified `BROADBRIDGE_DATABASE_URL`.

The host guard is an additional check, not a substitute for verifying the Neon project and branch. Do not bind it to an arbitrary currently configured URL. After checking the expected dev endpoint, create the temporary path and run from `apps/capture`:

```powershell
$captureTestHost = ([uri]$env:BROADBRIDGE_DATABASE_URL).Host
if ($captureTestHost.Split('.')[0] -ne 'ep-restless-bread-au1nwu5h-pooler') {
    throw 'Browser tests require the verified dev endpoint.'
}
$env:CAPTURE_DB_TEST_HOST = $captureTestHost
$env:CAPTURE_TEST_OUTBOX = Join-Path ([System.IO.Path]::GetTempPath()) ('broadbridge-capture-' + [guid]::NewGuid().ToString('N') + '.jsonl')
$env:AUTH_URL = 'http://127.0.0.1:3100'
npm run test:e2e
```

Playwright starts a fresh loopback development server. It exercises the real Auth.js issuance and one-use consumption path, intercepting the actual verification link into the temporary outbox instead of sending mail. It then creates/edits/signs a synthetic testing-only case, verifies case/question/audit rows and the training exclusion, checks the canonical export, rejects link replay, and signs out. Database writes go to verified `dev`; this is not a production test.

`CAPTURE_TEST_OUTBOX` is allowed only for local development with a loopback auth origin. It is rejected when Vercel is present or the app is not running in development. **Never configure the test outbox or test interception on Vercel.** Keep raw links, tokens, credentials, and outbox contents out of test reports; remove the temporary outbox after the run. Traces are disabled. Only sanitized summaries and synthetic light/dark screenshots belong in `test-results`.

## Deploy a preview

Use the existing project and repository association. Confirm root directory `apps/capture` in the [Vercel project dashboard](https://vercel.com/bhbeachsiders-projects/broadbridge-capture); the build must retain access to the repository's canonical schema files outside the app directory. Configure Preview secrets there against `dev`. Do not set `CAPTURE_TEST_OUTBOX`.

For CLI deployment from the repository root, explicitly select the project before uploading the repository:

```powershell
vercel link --repo --yes --scope bhbeachsiders-projects
vercel deploy --yes --target preview --scope bhbeachsiders-projects
```

If a dashboard redeploy reports that `apps/capture` is missing, it is reusing an incomplete earlier source snapshot. Deploy the verified checkout from the repository root instead of repeating that failed snapshot. Record the URL actually returned by the deployment and its build result. Inspect the deployed sign-in route, then perform the real approved-email smoke once activation inputs exist. A preview that intentionally reports authentication unavailable is not a successful live-login smoke. The final URL and measured results are recorded below; live email delivery remains unverified.

Run deployment uploads from the repository root with the existing `.vercel/repo.json` link; the project's build root remains `apps/capture`. The root `.vercelignore` admits the app, shared schemas and synthetic test fixtures. It excludes dotenv files, documents, intake data, local dependencies and test output. Its directory rules are tested against the CLI file walker; trailing-slash parent exceptions can otherwise produce an empty upload.

## Reviewer workflow

1. Open the verified app URL, enter an allowlisted email address, and follow the new link from the verified sender. Do not share the link.
2. Read the introductory page. Complete Part A once; workflow answers are stored per authenticated author. Allowlisted reviewers can see the shared case list.
3. Create a case and record Identity, decision-time observations, hindsight, evidence descriptions, and test questions. Preserve unknowns; do not infer missing facts. Files are collected separately from their descriptions.
4. Set the case's permitted use beside sign-off. Enter reviewer name/date and tick the review checkbox only after checking the record. Signed status requires complete signoff. Editing a signed record clears its checkbox and returns it to draft for renewed review.
5. Wait for the saved status. Changes debounce for 1.2 seconds; saves for each record are serialized. Failures retain the draft in the tab and expose an explicit retry. A revision conflict requires comparison/reload and manual resolution; the app does not blindly overwrite a newer record.
6. Export all records or copy a case's JSON only after saves succeed. Export and sign-out flush pending changes and stop on errors/conflicts. Sign-out disables editing while it finishes. Closing a tab with dirty changes warns; there is no asynchronous save-on-unload guarantee.

For a conflict, keep the unsaved tab open while comparing its text with the saved version in another tab. Copy individual text as needed, reload deliberately, and reapply the resolved changes. Do not force a retry using a guessed revision. Server actions derive the actor from the authenticated session; reviewer-entered signoff names do not override audit identity.

## One-time Claude export migration and retirement

Use a complete saved export from the original page, preserving `exported_at`, workflow, and every case. Keep an untouched archive. With the dedicated database endpoint verified and an explicit responsible operator identity, run from the repository root:

```powershell
python packs/oil-gas/scripts/import_cases.py path/to/claude-export.json path/to/new-capture-snapshot --db --actor reviewer@example.test
python packs/oil-gas/scripts/db.py status
```

Replace the example paths and actor with the actual approved operator; the output directory must be fresh or empty. The importer validates the full export, rejects partial database imports, writes canonical case/question/workflow files, and upserts the database in one coordinated operation. It considers existing database family holdouts when producing training candidates.

Compare the import report, database row IDs/counts, canonical records, workflow, signoff/permissions, and family-derived candidate counts. Log in to the new app and compare its canonical JSON export against the migrated content, allowing documented export/audit timestamps to differ. Repeating an identical import should be idempotent; old run/scorecard snapshots do not overwrite newer case records.

Retire the Claude intake only after the live-login and migration checks succeed. Freeze the old intake as read-only/archive, retain the original HTML and source export, and direct reviewers to the verified app URL. Do not keep both as writable systems of record or retire Claude merely because a build or synthetic smoke passes.

The exact five registered sources remain unresolved. `db_sources.json` contains **five synthetic `DB-TEST-*` fixtures**; the broader existing register contains 32 rows. Neither identifies the requested five real sources. Do not choose arbitrary rows or report the synthetic fixture import as completion of real source intake.

## Production promotion and failure recovery

Dev-to-production promotion means applying **reviewed SQL migration files**, not copying/promoting the dev branch or its synthetic data. Verify `crimson-block-71962201` and production branch `br-old-leaf-au0q8w6y`, bind its matching pooled/direct URLs through secret tooling, apply the reviewed sequence with `db.py migrate`, and inspect `db.py status`. Never reset a remote production database. The reset command refuses all remote targets.

Configure Production secrets independently, pointing to that production branch. After its schema and real email activation checks are ready, publish the production app through the same project, for example:

```powershell
# From the linked repository root; Vercel builds apps/capture.
vercel deploy --prod --scope bhbeachsiders-projects
```

Run the verified-email smoke against that returned production URL. Do not promote a preview configuration that still points to synthetic dev storage. Keep the previous deployment available for application rollback; database migration rollback is a separate reviewed operation.

Python file publication and PostgreSQL do **not** form a distributed atomic transaction. The helper stages outputs, writes inside the database transaction, publishes before commit, and compensates ordinary failures. A process crash, power loss, uncertain remote commit, or failed compensation requires reconciliation: preserve the source/input and remaining artifacts, inspect database IDs/records and the output/report, establish which side committed, and retry only with a fresh destination after resolving the discrepancy. Do not interpret a missing output file as proof that the database did not commit. See the [database contract and reset guidance](../packs/oil-gas/db/README.md) and [`db_publication.py`](../packs/oil-gas/scripts/db_publication.py).

## Final verification record

Measured results from 24 September 2026 are retained in [capture-final.json](verification/capture-final.json). The browser screenshots were visually checked in [light](verification/capture-light.png) and [dark](verification/capture-dark.png) themes: labels, fields, tabs, permissions, and sign-off are legible with no horizontal clipping. Production has the four migrations and zero capture rows; no synthetic dev data was promoted.

| Evidence | Final result |
| --- | --- |
| Final Python/database suite and row counts | **329 passed**, 74.42 seconds, fresh offline PostgreSQL 17 container. [Dev fixture import](verification/capture-dev-fixture-import.json): sources 5, cases 3, questions 3, workflow 1, training candidates 2; sources are synthetic. |
| Matching migration-only unpooled selection | Passed; applied `0001`–`0004` to dev and [empty production](verification/capture-production-schema.json). |
| Final app tests and typecheck | **75 passed**, including six SQL tests on Neon dev; TypeScript passed. |
| Production build | [Production](https://broadbridge-capture.vercel.app) **READY**; final remote build completed in 6 seconds. [Runtime checks](verification/capture-production-live.json) confirm anonymous access to the sign-in form and the stable callback URL. |
| Local real-token Playwright rehearsal against verified `dev` | **1 passed**, 23.1 seconds; [sanitized result](verification/capture-browser-smoke.json). Real Auth.js test link, signed testing-only case, SQL rows, export, replay rejection, sign-out. No email sent. |
| Vercel preview URL / build result | [Preview](https://broadbridge-capture-7m79rrfj3-bhbeachsiders-projects.vercel.app), **READY**. Sign-in route verified; missing mail configuration fails closed. |
| Live approved-email login | Production configuration and form enabled; actual delivery/login check awaits an approved reviewer. No email was sent by the automated production check. Preview mail configuration remains absent. |
| Real five-source import | Pending identification of the exact registered sources. |
| Claude intake retirement | Pending verified live login and canonical migration comparison. |
