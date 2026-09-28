# Diagram target recovery: first implementation cycle

28 September 2026. Work is isolated on `codex/diagram-target-recovery` in both
repositories. Text/calculation SLM preparation can continue independently.

Draft review branches:

- [Foundry #19](https://github.com/bHBeachsider/slm-foundry/pull/19), engine
  implementation `82b7329`, based on draft #18.
- [Broadbridge #23](https://github.com/bHBeachsider/Broadbridge4096/pull/23),
  implementation/evidence `1069391`, based on draft #22. Later documentation-only
  commits may update these links without changing the measured artifacts.

**The implementation improves extraction, but does not yet achieve every target
or qualify diagram training.** No model calls, training, EC2/GPU, new downloads,
client drawings or production changes occurred.

## Results on fixed inputs

The old twelve drawings and their references were not changed. Fourteen new
development drawings were frozen before detector tuning: 26 total in this stress
program, below the 50-drawing limit. All share construction ancestry; none is
called an independent holdout. Each drawing's PDF/DXF/PNG siblings count once.

| Set / route | Correct / predicted edges | Correct / reference edges | Correct / claimed directions | Correct / source-known directions | False edges / evidence violations |
|---|---:|---:|---:|---:|---:|
| Original regression PDF, reviewed | 23/23 (100%) | 23/24 (95.8%) | 7/7 (100%) | 7/7 (100%) | 0 / 0 |
| Original regression DXF, reviewed | 23/23 (100%) | 23/24 (95.8%) | 7/7 (100%) | 7/7 (100%) | 0 / 0 |
| Original regression raster, previous baseline | 16/16 (100%) | 16/24 (66.7%) | 0/0 (unknown) | 0/7 (0%) | 0 / 0 |
| Original regression raster, reviewed | 21/21 (100%) | 21/24 (87.5%) | 5/5 (100%) | 5/7 (71.4%) | 0 / 0 |
| New development PDF, reviewed | 22/22 (100%) | 22/23 (95.7%) | 6/6 (100%) | 6/6 (100%) | 0 / 0 |
| New development DXF, reviewed | 22/22 (100%) | 22/23 (95.7%) | 6/6 (100%) | 6/6 (100%) | 0 / 0 |
| New development raster, reviewed | 21/21 (100%) | 21/23 (91.3%) | 4/4 (100%) | 4/6 (66.7%) | 0 / 0 |

All reviewed outputs passed structural evidence checks, with zero observed
reversals or unsupported direction claims. This is not a zero-risk estimate.
The JSON reports include counts, two-sided Wilson 95% intervals, raw and accepted
graphs, per drawing/family/route/bucket rows, empty bucket denominators and
explicit unmeasured port/tag F1. Visibility eligibility has not been independently
signed, so direction recovery above uses **all source-known directions**.
Confidence/independence and human gates remain open even where point targets pass.

Authoritative new artifacts:

- `docs/evidence/diagram-target-recovery-2026-09-28/regression-reviewed/report.json`
- `docs/evidence/diagram-target-recovery-2026-09-28/development-reviewed/report.json`
- Their `run.json`, `source-snapshot/` and `checksums.json` bind inputs, engine and
  harness sources, dependency versions and outputs. These are development reports.

## What changed and why

1. Qualification preparation now rejects malformed profiles, cross-split family
   derivatives, unsafe/mismatched artifacts and broken crop lineage. Local
   record IDs and typed signatures remain unverified; the module cannot approve
   training. The pending domain profile correctly reports open acceptances.
2. Raster arrow matching and line skeletonization now use original pixels in
   separate paths. Arrow matching uses bounded contour/rotated-template proposals
   and unique compatible base/tip attachment. Ambiguous attachments stay unknown.
3. Tiny thick spots at 2px crossings no longer count as junction dots. Supplied
   text boxes no longer erase pipe pixels from the line branch.
4. A fresh reviewer reproduced a mask-created false arrow on a symmetric diamond.
   The fix excludes entire overlapping arrow candidates instead of whitening
   pixels. A regression test watched that failure and then passed after the fix.
5. Local source-only and detector-overlay review bundles export immutable,
   hash-bound **pending** correction proposals. They do not overwrite gold or
   authenticate a reviewer. The current edit control is a technical JSON array;
   vector-to-image transforms and a finished tracing interface remain open.

Native PDF/DXF geometry was deliberately left stable after its prior curve repair.
The convention manifest maps existing tests to crossings, hops, tees and direction
rules. It explicitly labels off-page resolution and symbol semantics unsupported;
an invented legend or guessed connector is not a remedy for missing evidence.

## Experiment record

| Run | Development raster TP / FP / FN | Regression raster TP / FP / FN | Disposition |
|---|---|---|---|
| Attempt 1 | 16 / 14 / 7 | 16 / 12 / 8 | Rejected: 2px crossing artifacts became dots; one development graph failed evidence checks |
| Attempt 2 | 20 / 2 / 3 | 20 / 0 / 4 | Better dot rule; a supplied text box still cut a rotated pipe |
| Attempt 3 | 21 / 0 / 2 | 21 / 0 / 3 | Both line paths retained source pixels; directional gaps remained |
| Post-review verification | 21 / 0 / 2 | 21 / 0 / 3 | Mask-created arrow defect fixed; same frozen inputs, no additional parameter search |

Three parameter configurations were evaluated. The subsequent replay verifies the
review correction; it is not a second independent validation. No attempts were
deleted or hidden. `development-attempt-2/` failed during receipt setup because
OpenCV was installed under another distribution name; no extraction ran there.
`development-attempt-2-complete/` is its successful retry. Module-version logging
was corrected and covered by an end-to-end test.

Attempt 1 pins source hashes but lacks a complete source snapshot and environment
receipt; it is diagnostic history only. Completed attempts 2/3 and reviewed runs
include source snapshots. Early summaries omitted crossing-category false edges
from the combined critical-flag sum, although their separate counts and raw edges
were present. The final reporter fixes that sum with a regression test. Old reports
remain unchanged; use the reviewed reports for current conclusions.

## Deficiencies remaining and the next corrective work

| Deficiency | Current evidence | Next work / required input | Acceptance |
|---|---|---|---|
| Curved raster hop missed | One missed hop path in each raster set | Trace skeleton chains with native pixel adjacency; preserve curved chain identity and test nonconnecting crossings; freeze a new development recipe before another experiment | No phantom junctions; correct through-path recovered with pixel evidence |
| Rotated raster pipe missed | `rotated-reverse` regression loses its directed edge | Trace/fit across antialiased line fragments without deleting original pixels; retain endpoint/port uncertainty and reject unsupported joins | Correct endpoints, path and direction; no false branch nodes |
| Small arrows unresolved | Five-pixel arrow remains unknown; new small/rotated marks also unresolved | Preregister scan-resolution/arrow-size limits and compare source-derived DPI variants within their original family; review visibility before any eligibility freeze | Direction recovery >=90% on reviewed eligible arrows, with >=99.5% precision and no reversals |
| Visible break does not establish continuity | One unchanged miss in both vector sets and raster | Obtain legend/native connector evidence or keep abstention; never bridge the gap solely to improve recall | Evidence-backed interpretation accepted for the declared convention |
| Off-page/symbol semantics | No qualified cross-sheet or symbol resolver | Source-model IDs, drawing revision/legend and independently signed examples; named positive/negative resolver tests before claiming support | No incorrect off-page merge or invented symbol port |
| Independent accuracy evidence | One construction family, supplied ports, small counts | Separate rights-cleared source families, pre-frozen splits and cluster-aware analysis accepted by technical reviewer | Every route's qualified lower bounds meet its targets; two unseen raster cohorts |
| Review experience and acceptance | Local prototype exports pending JSON; browser visual check blocked | Local operator visual check; verified vector-to-pixel transforms, usable tracing controls, authenticated independent acceptance, timed matched-drawing study | >=50% lower median review time without more errors; signed versioned decisions |

These are remaining work, not completed capabilities. The bounded raster cycle
has ended; its results and next hypotheses are preserved for the next
diagram iteration. No model prompting is proposed. The main SLM queue can advance
FQ-07 while technical review and diagram qualification remain separate.

## Validation and release state

New tests cover preserved pixels, false directions from masks, crossing-dot
confusion, line endpoints, unknown directions, profile leakage, artifact hashes,
source-only isolation, stale correction bindings, rejected-output recall and
critical-error accounting. Final full offline suites:

- Foundry: **842 passed, 3 skipped** (`python -m pytest tests -o addopts= -q -rs --tb=short`).
  Skips: optional Docling core, owned disposable PostgreSQL not enabled, optional
  pinned C01 public fixture not configured. Warnings: existing requests dependency
  mismatch and SWIG deprecations. No dependency installation was attempted.
- Broadbridge: **450 passed, 103 skipped** (`python -m pytest -q -rs --tb=short`),
  with the three Foundry path variables pointing at the isolated branch. Skips
  require explicit disposable database URLs; one existing requests warning.
- Fresh read-only code review: one important mask-created direction defect,
  reproduced and fixed with a regression test. Source-only isolation and pending
  acceptance boundaries had no demonstrated further P1/P2 findings. Engineering
  qualification, browser interaction and full historical reproducibility were
  explicitly outside that code review's acceptance.

The first GitHub Python job exposed a test-collection issue in its lightweight
environment: Pillow was imported before the optional geometry dependency checks.
Foundry `d80cd22` fixes that test-only import. A no-Pillow collection rehearsal
skipped cleanly, and all 23 focused raster/qualification tests passed with geometry
dependencies installed. The detector and the archived measurements are unchanged;
the separate geometry CI job continues to execute these tests with its full stack.

The next Python job collected successfully and exposed an existing one-millisecond
retry-test race: parsing could finish before the timeout poll on Linux. Foundry
`4a860d8` makes retry-state tests inject a parser timeout and retains a real
stalled-child timeout/termination test. All 52 ingestion-CLI, raster and
qualification tests passed locally afterward. This changes test setup only.

The browser tool refused local `file:` URLs under its security policy. No alternate
browser/proxy workaround was used. Interactive visual verification remains open.
Neither a passing CPU suite nor a valid correction proposal closes the engineering,
rights, crop-history, independence, training or production-release gates.
