# Broadbridge database and direct capture implementation plan

Goal: make the dedicated Broadbridge Neon project the system of record and replace Claude-artifact intake with the same capture experience behind email authentication. This implements Brad's twelve-point request and the subsequent dev-branch and migration-connection decisions. The existing case_record.schema.json and export.schema.json remain authoritative.

## Completed implementation

1. [x] SQL migrations 0001–0004 own the broadbridge schema, vector extension, canonical constraints, family-wide question projection, audit, training view, auth token storage and revision-checked browser writes. No embeddings or ORM migration system.
2. [x] Pinned psycopg 3 helpers use BROADBRIDGE_DATABASE_URL for normal operations. db.py migrate uses only matching DATABASE_URL_UNPOOLED; host/database/role/port mismatches and routing overrides fail closed. Reset refuses every remote target, Git main/master, and unverified local databases.
3. [x] Importer, evidence extraction, brief runner and scorecard CLI support --db with explicit actors, idempotent natural keys and staged file publication. Ordinary failures compensate files and roll back SQL; crash/uncertain-commit reconciliation is documented. Historical runs never overwrite current cases, and blank scorecards cannot overwrite completed reviews.
4. [x] Local offline PostgreSQL 17/pgvector and Python suite: 329 passed in 74.42 seconds. The regression proved the browser/CLI workflow race before the shared lock fix. Part 1 checkpoint was reported before app completion.
5. [x] Requested dev branch created/selected with neon@6.1.0 checkout dev. Imported SYN-001 plus both SYN-TRAIN fixtures: 3 cases, 3 questions, 1 workflow, 2 training candidates. Five explicitly synthetic source fixtures imported. The requested five real sources remain unconfirmed.
6. [x] Next.js App Router capture app ports the supplied HTML fields, copy, IBM Plex fonts and light/dark steel-blue design. Canonical Zod validation runs on each server action, records have a 256 KB cap, and only the session supplies the audit actor.
7. [x] Auth.js/Resend magic links, allowlist, hashed one-use tokens, 15-minute maximum expiry and local-only test outbox implemented. Browser autosaves debounce 1.2 seconds; revision conflicts retain drafts. Export/sign-out flush pending saves and block on failure.
8. [x] Final app checks: 75 tests passed, including six SQL tests on Neon dev; TypeScript passed. A real Auth.js local test-link browser smoke passed in 23.1 seconds: create/edit/sign-off, SQL verification, export, replay denial and sign-out. Light/dark screenshots visually inspected.
9. [x] Vercel Hobby project created and linked to bHBeachsider/Broadbridge4096, root apps/capture. Preview is READY and its sign-in route is verified. Separate dev/production database URLs and Auth.js secrets configured. Brad/Bill allowlist configured for both environments.
10. [x] Tested additive migrations applied to production with its matching unpooled URL; all capture tables remain empty. Local .neon/.env remain on dev. No remote reset, production data promotion, EC2, retrieval or model execution.

## Remaining activation and data steps

- [ ] Production Resend configuration is set and the public sign-in form/callback URL pass checks. Verify actual approved-email delivery/login next. Preview has no live email configuration. No real email was sent by the automated checks.
- [ ] Identify the exact five registered source IDs/file. The 32-entry research register is not assumed to be that selection; DB-TEST fixtures are synthetic.
- [ ] Archive and import actual Claude exports, compare canonical records and workflow, verify reviewer access, then freeze/retire the old writable page. Do not retire it before cutover verification.
- [x] Production application published at https://broadbridge-capture.vercel.app. AUTH_URL is pinned to that stable origin; build and anonymous sign-in page checks pass. Actual reviewer login remains the final activation check.

## Resource and evidence record

- Neon project: crimson-block-71962201, PostgreSQL 18, AWS us-east-1. PostgreSQL 17 compatibility is independently tested locally.
- Production: br-old-leaf-au0q8w6y. Requested dev: br-billowing-morning-audiqy3e, endpoint ep-restless-bread-au1nwu5h. Earlier capture-dev br-royal-moon-auq044a1 is preserved as an audit rehearsal.
- Checkout manages DATABASE_URL, not the custom application variable. BROADBRIDGE_DATABASE_URL was explicitly rebound after checking the dev endpoint. No fallback to PermitHub or a general DATABASE_URL exists in application code.
- Vercel: broadbridge-capture, project prj_qjV1c3eNiaV3R8pICrfXmvkJA4U9, workspace bhbeachsiders-projects. [Preview](https://broadbridge-capture-7m79rrfj3-bhbeachsiders-projects.vercel.app).
- [Deployment/runbook](../CAPTURE_APP.md), [measured verification](../verification/capture-final.json), [dev fixture counts](../verification/capture-dev-fixture-import.json), [empty production schema](../verification/capture-production-schema.json).

The original case-capture.html remains unchanged. Its introductory retrieval/training copy is retained verbatim; this implementation is S0-cases only. Broadbridge records remain in the dedicated Broadbridge system.
