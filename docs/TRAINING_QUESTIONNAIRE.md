# Engineering training review

Release route: `/questionnaires/pressure-training-v1` on the existing `broadbridge-capture` project. The capture home page links to **Engineering training review**. Sign-in uses the existing allowlist and retains the exact questionnaire URL through the emailed link. The existing 24-hour sign-in-link policy is unchanged.

The questionnaire contains the revised 16 questions in five categories, eight authored reference examples and pressure-reference graphics. It identifies priority tasks, corrects teaching references, defines evaluation requirements and collects unusual cases, source nominations and suggestions for Norm. It contains no model-generated responses and does not approve training or source rights.

## Reviewer instructions

Open the questionnaire link and sign in with an approved email. Work through the categories. Read the source notes and record the required answer before opening the draft reference. Record corrections, missing evidence and serious errors. Use **Submit feedback** when ready. Further edits reopen the response as a draft.

Responses autosave after 1.2 seconds and are stored under the signed-in email. **Save now / retry** handles an interrupted save. The status displays the saved revision. A stale tab cannot overwrite a newer response; download its unsaved text before reloading. **Download this draft** preserves current tab contents, including unsaved edits. **Download saved responses** retrieves only the signed-in reviewer's database record. No other reviewer's identity can be supplied by the browser.

## Storage and versioning

- `0008_training_questionnaire.sql` adds immutable `broadbridge.questionnaire_packets`, append-only `questionnaire_responses`, the current-response view and a revision-checked save function.
- The packet in `apps/capture/lib/pressure-questionnaire.json` is versioned and checksum-bound. Register it with `scripts/questionnaire_packet.py`; reusing an ID/version with changed content fails. Future content edits require a new version and corresponding app validation update.
- Every save is validated server-side against the question IDs, permitted fields, option values and 256 KB UTF-8 cap. Actor identity comes only from the authenticated session. Reference-reveal timestamps are client-reported interaction metadata, not proof of review.
- Draft and submitted feedback remains separate from case sign-off, model scores, source-use approval and dataset admission. `training_approved` is fixed to false.
- No changes are made to existing capture records, public-review scores, AWS hosts or model training.

## Verification

Offline app tests: 115 passed, 10 database-dependent tests skipped. Type checking passed. An additional real PostgreSQL repository test passed, covering independent reviewer records, idempotent retries, revision history, stale-write rejection, immutable packets and invalid questions.

The local Playwright test passed with real Auth.js magic-link issuance/consumption into a local test outbox, autosave/reload, stale-tab rejection, submission, reviewer-specific export, anonymous export denial, mobile category navigation and the home-page link. The first browser attempt exposed a missing explicit accessible name on the mobile selector; it was corrected before the passing run. Desktop/light and mobile/dark screenshots were visually inspected.

Reproduce the local acceptance test with the existing `pgvector/pgvector:pg17` Docker image and Python database dependencies:

```powershell
python scripts/questionnaire_acceptance.py --output <new-local-output-directory>
```

The harness creates and removes only its owned loopback PostgreSQL container, substitutes the Neon HTTP transport locally, sends no mail, loads no `.env`, removes its test outbox and preserves sanitized receipts. It never uses an existing cloud database.

## Release procedure

Use the existing Vercel project `broadbridge-capture` in `project-next1`, app root `apps/capture/`. Keep production authentication and database configuration. Do not promote a preview connected to dev as a replacement for the production environment.

1. Run the app tests, type check, build and disposable-database acceptance test.
2. Use `scripts/questionnaire_release.py inspect` to verify the dedicated Neon project and selected branch. The helper reads `NEON_API_KEY` privately from the explicitly supplied environment file, resolves the selected branch's matching pooled/direct URLs and emits only identity, schema and aggregate counts.
3. Apply to dev before production. `db.py migrate` verifies every previously applied checksum; the direct connection is used for DDL only. Questionnaire registration uses the pooled connection. The production helper refuses unexpected schema versions and never inserts reviewer responses.

```powershell
python scripts/questionnaire_release.py inspect --target dev --env-file <private-env-file> --receipt <local-receipt.json>
python scripts/questionnaire_release.py apply --target dev --env-file <private-env-file> --receipt <local-receipt.json>
python scripts/questionnaire_release.py inspect --target production --env-file <private-env-file> --receipt <local-receipt.json>
python scripts/questionnaire_release.py apply --target production --env-file <private-env-file> --receipt <local-receipt.json>
```

4. Release only the questionnaire branch based on production `main`; the AWS/readiness branch contains unrelated changes and must not be promoted.
5. Verify the production deployment commit, anonymous sign-in redirect with return destination, and anonymous export rejection. Do not fabricate a Bill response or send an unsolicited login email to test production.

Application rollback returns to the previous Vercel production deployment. The additive questionnaire tables can remain; never delete submitted responses as part of rollback. No new infrastructure or credentials are required.
