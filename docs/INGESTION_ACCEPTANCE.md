# Ingestion acceptance and deployment handoff

The new intake page and generic Foundry engine have an offline integration path.
This document records code acceptance; it is not a live deployment or model-quality claim.

## Repeat the local browser rehearsal

Prerequisites: Docker Desktop with a cached `pgvector/pgvector:pg17` image, Python
with the pack database dependencies and Foundry CPU dependencies, Node 24, and
the capture app's installed dependencies/Playwright Chromium. No `.env` is read
by the helper. The app is run against fresh, explicitly generated loopback services.

```powershell
python scripts/ingestion_local_smoke.py `
  --foundry C:\absolute\path\to\slm-foundry `
  --repo C:\absolute\path\to\Broadbridge4096 `
  --output tmp\ingestion-acceptance-new-run
```

Use a new output directory each time. The helper starts its own labeled PostgreSQL
container, applies migrations there, and stops/removes only that container after
the run. It uses the real Auth.js magic-link verification flow and an explicitly
local email outbox; no email is sent. Original bytes and parser output live under
the private ignored run directory. Do not commit that outbox or raw logs.

The Neon HTTP and S3 HTTP endpoints are local transport fixtures. They exercise
the application's SDK requests against real PostgreSQL and filesystem objects;
they do not validate Cloudflare signatures, live CORS, Neon networking, or Vercel
configuration. The actual Foundry API, lease-backed queue and parser subprocess
run against the owned PostgreSQL schema. No model endpoint is called.

Recorded final run: repository tests **2 passed**; Playwright smoke **1 passed**
(42.2 seconds including its setup). Both synthetic uploads reached durable
`succeeded` jobs. The browser then registered an authored synthetic candidate
through the actual domain CLI, verified that an unreviewed batch is blocked,
accepted its exact hash through the authenticated UI, prepared the reviewed
batch and built/recorded the immutable dataset twice to prove idempotence.
Independent review re-read the output files with Foundry's `verify_release`.
The dataset contains one training row; no model generated that synthetic target.

Final database totals were 204 source revisions (2 browser, 1 repository, 201
pagination fixtures), 2 rights decisions, 2 succeeded jobs, 102 candidates (1
artifact-bound browser candidate plus 101 pagination fixtures), 1 artifact
binding, 2 technical decisions, and 1 dataset release. Browser execution precedes
the pagination fixtures so unrelated synthetic rows cannot enter its dataset.
Stale-review rejection and authenticated actor stamping passed. Light, dark and
390-pixel mobile screenshots were visually inspected for clipping and legibility.
See [machine-readable evidence](verification/ingestion-local-browser.json).

The run deliberately inherited an invalid `PGHOSTADDR` and still used only its
owned local PostgreSQL. The helper isolates all libpq environment settings until
bounded HTTP handlers have exited; three regression tests cover restoration on
success/failure and an in-flight request at shutdown. Separate quality reviews
approved the harness and the complete browser-to-release path.

Earlier attempts exposed an exact-label selector mismatch, a harness recipe
that differed from the pack, and an outdated pagination candidate fixture. The
final helper reads the actual pack recipe, and the fixture uses the canonical
candidate fields. No acceptance assertion was removed.

## Live acceptance result

The deployed Preview path has now passed with actual R2, Neon dev and local
Docker: Brad signed in, uploaded two synthetic files, and inspected their CPU
evidence. Separate review gates, immutable one-row dataset construction, an
identical second build, revocation and stale-review rejection were verified.
This is distinct from the loopback rehearsal above. See the
[live setup record](INGESTION_LIVE_SETUP.md#deployed-browser-to-dataset-acceptance-completed)
and [sanitized evidence](verification/ingestion-live-browser-dataset.json).
It proves pipeline mechanics for the text/CSV fixtures, not engineering quality,
native multimodal extraction, or a trained model. The test runtime is stopped.

## Before a new live acceptance session

1. Review the completed independent package reports and keep PRs draft until Brad marks them ready.
2. Confirm a dedicated nonproduction database/bucket mapping and CPU service host.
   Apply migration 0005 only to that approved database; production remains a separate go.
3. Configure the app's `R2_ENDPOINT` and worker's `R2_ENDPOINT_URL` to the same
   approved account endpoint, plus the same bucket. Use separate scoped service
   credentials, the existing dedicated Broadbridge database, and a private
   authenticated CPU service. Do not use PermitHub resources.
4. Configure bucket CORS for the exact preview origin, PUT, and the headers emitted
   by `signUpload`. Verify a synthetic browser upload end to end before real files.
   Live acceptance must test the signed Content-Length and immutable PUT behavior.
5. Verify extraction/review/revocation and orphan recovery against real services.
   Prepare local Docling OCR/ASR weights separately before claiming those formats
   work. Missing weights must remain visible as unsupported.
6. Admit a reviewed batch, record comparable baseline/adapter evaluation receipts,
   and approve an explicit GPU budget before training. Production serving requires
   accepted release identity, exact artifacts and a rollback target.

Install the Vercel CLI for the later deployment handoff:

```powershell
npm i -g vercel
```

Then use `vercel env pull`, `vercel deploy` and `vercel logs` in the linked project
as appropriate. Environment files remain ignored; never copy their contents into
PRs or reports. Installing the CLI does not authorize production deployment.
