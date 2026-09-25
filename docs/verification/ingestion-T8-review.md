# T8 local browser-to-dataset acceptance

Specification review: **PASS**. The rehearsal starts only its own labeled
loopback PostgreSQL 17 container, uses synthetic source bytes and a local
Auth.js outbox, and invokes the actual CPU service, parser, domain registration
CLI, UI review actions and generic dataset builder. The authored synthetic
answer is explicitly not an LLM result. Pending candidates block publication;
source rights, technical review and exact-batch approval remain separate.

Independent quality reviews: **APPROVE**, covering environment isolation,
bounded request teardown and the expanded browser/release flow. The reviewer
independently ran `verify_release` on the final files and matched the manifest,
hashes, one training row and one admitted source.

Final run `ingestion-local-final-03`: Playwright **1 passed** (42.2 seconds total),
repository **2 passed** (1.58 seconds). Both processes exited zero. Two CPU jobs
succeeded with no worker exceptions. The test deliberately inherited an invalid
PGHOSTADDR; the helper removed host routing settings for the full owned-service
lifetime. Isolation regressions: **3 passed**; no background request survives
environment restoration.

Totals in `ingestion-local-browser.json` include separate pagination fixtures,
not additional files admitted to the browser's dataset. The local private run
contains the full immutable release; only this sanitized report and screenshots
are committed. Light, dark and mobile views were visually inspected.

No existing database, real email, R2/Neon endpoint, model, GPU or production
service was accessed. S3 and Neon HTTP transports are local fixtures, so live
signing/CORS, deployment configuration and model quality remain separate gates.
