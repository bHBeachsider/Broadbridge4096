# Local diagram review preparation

Use the isolated `codex/diagram-target-recovery` branch. This is a local
preparation tool; it does not change Case Capture, the database or production.
It exports a pending correction proposal, not an authenticated signed reference.

## 1. Trace before seeing the detector

Open the source-only example at
`docs/evidence/diagram-target-recovery-2026-09-28/review-source-only/review.html`
in a local browser. That file contains the original image and an empty trace
array. Neither detector proposals nor reference answers are embedded.

Record the drawing revision, line endpoints, visible arrows, unknowns and the
legend supporting any connection. Coordinates are original PNG pixels with the
origin at the top left. The current editor uses an edge-array text box; this is
an operator-assisted review prototype, not a finished tracing application.

## 2. Inspect detector evidence separately

After the source-only trace has been recorded, open
`docs/evidence/diagram-target-recovery-2026-09-28/review-overlay/review.html`.
Toggle proposed paths, arrow keypoints and excluded contacts. Hover to inspect
recorded evidence. Amber means unknown direction; it is not a failed rendering.

Change the proposed edge array and explain corrections in notes. Enter reviewer
attribution and review time, then choose **Export pending proposal**. The download
includes original/revision/detector/reference hashes and a before hash with the
proposed after state. It never writes over the scored reference or source file.

Only original PNG pixel coordinates are currently accepted. A vector PDF/DXF
overlay requires a separately verified page-to-pixel transform; do not substitute
a convenient screenshot or infer a transform. This remains an open integration.

## 3. Validate and accept through a trusted review boundary

Use `validate_proposal(proposal, bundle)` in
`scripts/research/diagram_review_overlay.py` to reject stale bindings or an
attempt to turn a local export into `signed`. A valid proposal is still pending.
An authenticated workflow must independently establish identity, competence,
rights, source revision, source-only tracing and technical acceptance. This
branch does not create that integration or impersonate Bill's acceptance.

If a correction is used for development, create a new reference version and keep
the old scored version. A viewed/scored holdout cannot be recycled as untouched.

## Rebuild examples (PowerShell)

Run from the isolated Broadbridge worktree. Use new output directory names; the
script intentionally refuses to overwrite an existing bundle.

```powershell
$foundry = 'C:/Users/bradu/Documents/Broadbridge4096/tmp/slm-foundry-worktrees/codex-foundry-ingestion-live-http'
$python = "$foundry/outputs/geometry-venv/Scripts/python.exe"
$evidence = 'docs/evidence/diagram-target-recovery-2026-09-28'
$inputs = 'docs/evidence/deterministic-diagrams-2026-09-27/inputs'
& $python scripts/research/diagram_review_overlay.py `
  --source "$inputs/forward.png" `
  --detection "$evidence/regression-attempt-3/forward.png.json" `
  --revision frozen-2026-09-27 --out tmp/new-source-only-review
& $python scripts/research/diagram_review_overlay.py `
  --source "$inputs/forward.png" `
  --detection "$evidence/regression-attempt-3/forward.png.json" `
  --reference "$inputs/references.json" `
  --revision frozen-2026-09-27 --out tmp/new-detector-review
```

## Review-time study

Use matched different drawings, not the same drawing twice. Counterbalance which
condition comes first. Keep a separate source-only gold reference reviewer.
Record drawing/family, reviewer, condition, order, minutes, corrections and errors
remaining after review. The target is at least 50% lower median time without more
errors. No timing result or benefit is claimed yet.

| Pair | Reviewer | First condition | Second condition | Minutes / remaining errors |
|---|---|---|---|---|
| Independent matched drawings A/B | Pending | A source-only | B overlay | Not measured |
| Independent matched drawings C/D | Pending | C overlay | D source-only | Not measured |

The built-in browser refused the local `file:` URL under its URL security policy.
Structural/escaping/isolation tests ran, but interactive visual acceptance remains
for a local operator. No browser-policy workaround was attempted.
