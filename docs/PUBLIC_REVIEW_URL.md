# Public-document scoring in the capture workflow

The capture app now has an authenticated route `/review/public-v1`. Both the
Case Capture navigation and Source Intake header link to **Public-document
scoring**. A specific response can be linked directly, for example:

```text
/review/public-v1?question=PUB-022&response=A
```

Sign-in preserves that destination. Use the existing approved email address.
No email is sent merely by opening a review link. No model is called by this
page and no review score grants training rights or technical release approval.

## Reviewer steps

1. Read the original question, source excerpts and frozen A/B response. The
   original agency URL is available beside the excerpts. A/B identities remain
   masked and switch between documents as in the original scorecards.
2. Expand the draft reference and tolerance when needed. References are aids
   for review, not certified answers; flag a defective reference/question in
   notes and hold it for a new benchmark version.
3. Choose 0/1/2, critical error Yes/No, and whether any exact hard-fail criterion
   matched. A hard fail requires 0/Yes. Add evidence and corrections, then
   **Save score**. Navigation is disabled while changes are unsaved.
4. Continue using Next or the question selector. The URL follows the selected
   item; **Link to this response** is suitable for a workflow or review note.
5. The progress panel shows your counts, per-type means and critical-error
   counts. **Download my scores (CSV)** exports all 60 identities, leaving
   unreviewed scores blank. Brad's screening and Bill's review are separate
   records; this UI does not resolve disagreements or certify consensus.

There are 30 returned answers and 30 unavailable slots in this frozen run.
Unavailable answers may remain unreviewed or receive 0/No with an explanation;
they cannot receive positive credit or an invented engineering-error flag.
An empty score is unreviewed, never implicitly zero. Counts and means are
partial until review is complete. Mechanical flags are not engineering grades.

## Storage and reproducibility

Migration `0006_public_review.sql` adds immutable `public_review_packets` and
append-only `public_review_scores`, plus the current-score view and revision
checked save function. Every revision records the authenticated reviewer and
database timestamp. A stale tab is rejected. Case records, candidate rights,
training reviews and the original benchmark files stay separate.

The operator adapter verifies the four frozen source file SHA-256 values and
preserves original questions, answers, citations and A/B mapping. It strips
model names/provider receipts from the review DTO. Publishing a packet writes
no scores. Registering identical content is idempotent; a changed packet needs
a new version/identity. The adapter accepts this frozen public-v1 run only.

After independently verifying that pooled and direct URLs select the dedicated
Broadbridge **dev** branch, apply migrations using the established command and
register the frozen packet:

```powershell
python packs/oil-gas/scripts/db.py migrate
python scripts/research/public_review_packet.py --db
```

Runtime/registration use only `BROADBRIDGE_DATABASE_URL`. Only migrations use
the matching `DATABASE_URL_UNPOOLED`. Environment values are supplied privately,
never command arguments or committed files. The capture project is unchanged;
the new draft branch gets a dev-only Preview database override and its own
stable `AUTH_URL`. Production migration/deployment are not part of this work.

To feed downloaded scores into the existing report without editing the frozen
run, copy it into a **new** ignored directory, then replace only that copy's
`scores.csv` with the download and run the existing aggregator:

```powershell
$reviewRun = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\public-v1-review-NEW'
if (Test-Path -LiteralPath $reviewRun) { throw 'Choose a new review run directory' }
Copy-Item -LiteralPath 'output/openrouter-public-evaluation/public-v1-live' -Destination $reviewRun -Recurse
Copy-Item -LiteralPath "$env:USERPROFILE\Downloads\scores_public-v1.csv" -Destination (Join-Path $reviewRun 'scores.csv')
python scripts/research/public_document_evaluation.py summarize --run $reviewRun
```

The summary reveals model identities; complete blinded scoring first. Export
escapes CSV quotes/newlines and prefixes formula-like cells for spreadsheet
safety; verbatim notes and their revision history remain in PostgreSQL.

## Acceptance and limits

The local harness uses real PostgreSQL, Auth.js and the browser; Neon HTTP and
mail delivery use loopback transport/outbox fixtures. Synthetic scores are
written only to the disposable local database, never the real reviewer packet.

```powershell
python scripts/ingestion_local_smoke.py --foundry 'C:\Users\bradu\Documents\slm-foundry' `
  --output 'C:\Users\bradu\Documents\Broadbridge4096\tmp\review-acceptance-NEW' --review-only
```

The Foundry checkout must contain the matching ingestion branch; Node app
dependencies, Docker's existing `pgvector/pgvector:pg17` image and Playwright
Chromium must already be installed. The harness creates and removes only its
owned container. Browser acceptance includes destination-preserving sign-in,
revision conflicts, persisted reload, export, signed-out rejection and mobile
width. Deployed email delivery still uses the configured Resend integration.

Human steps remain: engineering scoring, resolving questionable references,
agreeing selection thresholds and approving subsequent data recipes. No source
in this evaluation or its derivatives becomes a training family.
