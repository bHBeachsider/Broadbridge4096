# Diagram target recovery implementation plan

28 September 2026. Execution authorized by Brad. Use the executing-plans workflow
in one implementation lane. The [specification](../specs/2026-09-28-diagram-target-recovery.md)
and existing metric contract define acceptance; tests cannot confer human approval.

## Branches and reproducibility

Both branches: `codex/diagram-target-recovery`.

Published as draft [Foundry #19](https://github.com/bHBeachsider/slm-foundry/pull/19)
and [Broadbridge #23](https://github.com/bHBeachsider/Broadbridge4096/pull/23).

- Foundry worktree: `C:/Users/bradu/Documents/Broadbridge4096/tmp/slm-foundry-worktrees/codex-foundry-ingestion-live-http`, base `19f55e300936587244613a16b82412ddc073809b` (draft #18).
- Domain worktree: `C:/Users/bradu/Documents/Broadbridge4096/tmp/codex-broadbridge-ingestion-live-test`, base `d4bb302` (draft #22).
- CPU Python: Foundry `outputs/geometry-venv/Scripts/python.exe`; installed geometry
  dependencies already suffice. No installation or dataset download planned.
- Keep `docs/evidence/deterministic-diagrams-2026-09-27` and
  `docs/evidence/vector-continuity-2026-09-28` immutable. `results-final.json`
  is the accepted regression report, not the intermediate `results.json`.

## Sequence and estimates

### Execution record: first cycle

The [results and residual work](../../DIAGRAM_TARGET_RECOVERY_RESULTS.md) are the
current execution record. This plan is not marked wholly complete: independent
qualification and remaining detector/reviewer capabilities still need work.

| Package | State after this cycle |
|---|---|
| DG-01 | Implemented/tested offline; authenticated acceptances remain unverified |
| DG-02 | 14 new development drawings frozen; no fabricated holdouts; 24 slots reserved for later independent sources |
| DG-03 | Three configurations and post-review verification executed; raster targets still not all met |
| DG-04 | Existing vector rules revalidated and convention scope documented; off-page/symbol semantics unsupported pending reviewed evidence |
| DG-05 | Local PNG prototype and pending exports tested; vector transforms, finished tracing controls, visual check and real timing study remain open |
| DG-06 | Stratified raw/accepted reports, explicit unknown/empty/unmeasured metrics and CI tests implemented |
| DG-07 | Fresh review fixed; full suites 842/450 passed; draft publication only |
| DG-08 | Open: independent sources, signed references/visibility/conventions, uncertainty analysis, rights and release |

Decisions: generated seeds from one family remain development data; the planned
synthetic reserve split was replaced with empty reserves. The unexplained gap was
not filled to inflate recall. One post-review verification followed three
experiments to confirm a reproduced false-direction fix. No GPU or model use.

### Work-package effort estimates

Effort estimates are engineering estimates, not scheduled promises. Human
qualification depends on available rights-cleared drawings and independent review.

| ID | Deliverable | Depends on | Estimated effort | Done when |
|---|---|---|---|---|
| DG-01 | Qualification preflight and lineage rules | Existing contract | 0.5-1 day | Negative cases fail closed with explicit blockers |
| DG-02 | Frozen development/reserve fixture design | DG-01 | 1 day | <=38 new drawings; lineage and checksums committed before tuning |
| DG-03 | Independent raster arrow/line paths | DG-02 development set | 1-3 days | Bounded experiments reported, including remaining misses |
| DG-04 | Vector convention/ambiguity diagnostics | DG-01/02 | 1-2 days | No guessed break/off-page merges; named regressions pass |
| DG-05 | Local reviewer overlay and correction packet | DG-01 | 1 day | Source-only and detector views; immutable pending exports |
| DG-06 | Stratified report and CI integration | DG-03/04/05 | 0.5-1 day | Raw/accepted counts, intervals, missing buckets and blockers explicit |
| DG-07 | Freeze, software review, draft delivery | DG-06 | 0.5-1 day | Full offline suites and fresh read-only review complete |
| DG-08 | Independent engineering qualification | DG-07 + human inputs | External dependency | Targets/uncertainty/review gates actually satisfied |

## DG-01 — fail-closed qualification profile

The detailed checklists below preserve the original package specifications;
unchecked boxes are not a current completion tally. The execution table above
and the results document distinguish implemented subsets from open requirements.

- [ ] Add Foundry `schemas/diagram_qualification.schema.json`,
  `src/ingestion/diagram_qualification.py`, `tests/test_diagram_qualification.py`.
- [ ] Public API: `qualification_blockers(profile: dict) -> list[str]`. Return
  stable blocker codes; malformed profiles return `schema_invalid`. Passing
  structural preflight is not performance acceptance or training approval.
- [ ] Test missing fields, changed source/reference/crop hashes, siblings across
  splits, retrospective provenance, self-review, local typed sign-offs, missing
  coordinate transforms, insufficient independent evidence and release holds.
- [ ] Add domain `packs/oil-gas/manifests/diagram_qualification_profile.json`
  describing current pending decisions honestly. No manufactured reviewer IDs.
- [ ] Reuse existing evidence/metric functions; do not replace the immutable
  regression reporter or weaken `check_edges`.

## DG-02 — fixture design before detector tuning

- [ ] Add `scripts/research/diagram_fixture_suite.py`, its test module, and
  `packs/oil-gas/manifests/diagram_fixture_design.json` in Broadbridge.
- [ ] API: `validate_split(records) -> list[str]`; exclusive-output
  `prepare_suite(out, foundry, design) -> dict`. Preparation invokes no detector.
- [ ] Generate at most 14 new development drawings. Keep space for up to 12
  reserve-A + 12 reserve-B drawings, but do not generate purported holdouts from
  the same construction family. Reserve cohorts remain unpopulated until distinct
  source-family ancestry is established; a new seed alone is not independence.
- [ ] Cover crossings, hops, tees +/- dots, unexplained breaks, no/conflicting
  arrows, rotated/small arrows, port ambiguity and unresolved off-page symbols.
  Include positive and negative critical-class cases. Gold comes from source
  construction, never predicted geometry.
- [ ] Pin seeds, design, renderer, original model/reference files, input hashes,
  coordinate frames, derivation transforms and split hash. Refuse overwrites,
  path traversal, changed assets, unknown source classes and >50 program drawings.
- [ ] Commit hashes before development runs. Do not view or score reserve
  predictions during development; qualification requires additional human gates.

## DG-03 — raster recovery

- [ ] First add failing tests in `tests/test_raster_connectivity.py`: original
  pixels unchanged; forward/reverse/rotated/small arrows; dots/tees; triangles
  off a pipe; crossing/hop; ambiguous nearest lines and contradictory arrows.
- [ ] Add `src/ingestion/raster_connectivity.py` with `detect_arrows(image)`,
  `detect_lines(image)` and `reconcile(arrows, lines, tolerance)`; wire only the
  raster adapter in `geometry_extractors.py`.
- [ ] Detect bounded multiscale contour/rotation candidates on original pixels;
  skeletonize a separate unchanged copy. Preserve arrow bbox, tip/base and source
  image hash. Require unique compatible local line attachment; otherwise unknown.
- [ ] Evaluate skeleton spurs explicitly. Do not simply remove arrow blobs and
  reconstruct a guessed line. Existing evidence checker remains the final filter.
- [ ] Run <=3 documented configuration experiments on development + old
  regression only. Save all attempts under new directories. Stop tuning after
  this bound and report residual failure classes; no quiet holdout tuning.

## DG-04 — vector scope and conventions

- [ ] Add `tests/test_diagram_conventions.py` for the four critical classes.
  Modify builder/extractor only for reproduced defects, preserving native curves.
- [ ] Add domain convention manifest: supported no-dot crossing/tee/hop behavior,
  unresolved break, off-page, port, reducer and instrument-symbol semantics.
- [ ] Test no off-page merge without matching source/revision evidence; no gap
  bridging from proximity alone; no reducer/symbol outline promoted to pipe.
- [ ] Any semantic extension requires versioned evidence and tests. Without
  source-model or signed convention evidence, abstain and retain the recall miss.
- [ ] Record remaining false/missed edges by class. Two misses in a class create
  a development regression group without changing family ancestry.

## DG-05 — reviewer-ready local bundle

- [ ] Add `scripts/research/diagram_review_overlay.py`, tests, and
  `docs/DIAGRAM_REVIEW_RUNBOOK.md`; no hosted app/database changes.
- [ ] Generate local HTML/SVG/JSON with source-only tracing view and separate
  detector overlay (paths, arrows, evidence, unknowns, rejections). Source-only
  mode must hide detector proposals and reference answers.
- [ ] Export reviewer/date/revision/hash-bound before/after correction proposals
  as `pending_authenticated_review`. Typed names are not authenticated sign-off.
  Never overwrite reference files; edits become a new review/development version.
- [ ] Test HTML escaping, coordinates, stale revision/hash rejection, exclusive
  writes, no network calls, and absence of predictions in source-only mode.
- [ ] Visually inspect the local bundle. Add matched-drawing, counterbalanced
  review-time assignments; blank measurements remain blank until humans review.

## DG-06 — reporting and CI

- [ ] Add separate qualification reporting rather than rewriting old regression
  semantics. Show raw/accepted TP/FP/FN, all claims/correct/eligible directions,
  unknown/missed directions, evidence failures, not-run/extraction-failed/checker-
  rejected statuses and overlapping critical flags by route/family/drawing.
- [ ] Stratify arrow size, rotation, DPI/noise and intersection; empty buckets
  show null estimates and zero denominators. Visibility eligibility remains
  pending until independently reviewed before the freeze.
- [ ] Report port/tag F1 and attachment metrics as unmeasured where unavailable;
  supplied ports cannot earn end-to-end credit. Report all-edge recall as well as
  any preregistered eligible subset.
- [ ] CI checks checksums, ancestry, evidence, unknown preservation and metric
  output. CI does not automatically run untouched reserves or approve training.
- [ ] Test tampering, zero denominators, wrong scopes, correlated-family claims,
  duplicated sources and absent authenticated acceptances.

## DG-07 — freeze and publish drafts

- [ ] Run focused changed tests, then Foundry full `python -m pytest tests -q`
  (starting baseline 819 passed/3 skipped) and Broadbridge
  `python -m pytest -q` (437 passed/103 skipped).
  Set `SLM_FOUNDRY_PATH`, `FOUNDRY_REPO`, `FOUNDRY_INGESTION_PATH` to the isolated
  Foundry path. Record exact commands/counts and explain skipped integrations.
- [ ] Fresh read-only review of geometry, leakage, stale signoff and statistical
  claims; correct material defects and rerun affected checks.
- [ ] Commit only scoped files; push branch and open draft successor PR in each
  repository. Check CI without `--watch`; do not merge or deploy production.
- [ ] Publish result table and remaining gates. A failed target remains failed,
  not replaced by a selective subset or manually repaired evaluated reference.

## DG-08 — explicit human/external completion gates

- [ ] Bill/appointed reviewer ratifies supported tasks, conventions and source-only
  arrow visibility/reference traces. Brad accepts rights and processing scope.
- [ ] Acquire adequate independent families only within approved data/download
  boundaries; preregister cluster-aware analysis and freeze the engine first.
- [ ] Evaluate each unseen cohort once. If results guide a fix, that cohort is
  development thereafter; do not count its replay as another validation.
- [ ] Conduct reviewer-time study and report uncertainty/errors as well as time.
- [ ] Record route-specific qualification; raster can remain blocked after vector
  progress. Training additionally needs crop history, rights and explicit release.

## Separation from main SLM work

FQ-05 owns these diagram branches. FQ-07 (offline helper-comparison protocol) is
the next main SLM item; text/calculation preparation and Bill's case/review intake
continue independently. A separate sidebar chat will be created only if Brad
requests it. No automatic future scheduler or hidden background service is implied.
