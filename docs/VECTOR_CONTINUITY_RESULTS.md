# Vector continuity repair and metric contract

28 September 2026. **DXF's seven false edges are removed on the frozen regression
set. Diagram training remains blocked.** PDF and DXF now both recover 23 of 24
reference edges, with no false edges and seven correct directions from seven
claims. This is small-sample development evidence, not production qualification.

## What was repaired

The old DXF hop converted closely spaced spline samples into false junctions.
Native path identity and sample order now survive extraction; approximation
vertices supply continuity, not branches. A hop plus its crossing line produces
two separate through paths. Real tees and dots remain connections.

Independent read-only review exposed two additional regressions in the first
implementation: a true tee between sample positions was missed, and an unbulged
polyline could lose straight continuation. The final extractor inserts contacts
verified on the actual circle/B-spline/PDF cubic before approximation and retains
straight polyline span types. Negative fixtures with nearby non-contact endpoints
guard against solving this by widening the connection tolerance. Additional tests
preserve source-parameter order through turning splines and
reject tee claims supported only by an approximation chord. The evidence
checker remains unchanged; the old archived results still replay exactly.

Native-path drawings currently use 1e-7 drawing-unit contacts, including ports
and unrelated straight geometry on that drawing. Coordinate rounding, complex
curves and incomplete port annotations can cause conservative misses. The test
does not establish complete CAD semantics, source-model connector extraction,
realistic symbol/OCR accuracy, or robustness to arbitrary drawing conventions.

## Same twelve drawings, unchanged references

All original input files, source graphs, ports/masks, baseline requests and results
remain unchanged under `evidence/deterministic-diagrams-2026-09-27/`. The three new CPU
detector attempts and report are separate under
[`evidence/vector-continuity-2026-09-28/`](evidence/vector-continuity-2026-09-28/results-final.json).
No model calls, dataset downloads, GPU/EC2, client drawings or production changes.

| Route | Before TP / FP / FN | After TP / FP / FN | Precision | Recall | Correct directions / claims / known reference directions |
|---|---:|---:|---:|---:|---:|
| Vector PDF | 23 / 0 / 1 | 23 / 0 / 1 | 100% | 95.83% | 7 / 7 / 7 |
| Vector DXF | 22 / 7 / 2 | **23 / 0 / 1** | **100%** | **95.83%** | 7 / 7 / 7 |
| Raster PNG | 16 / 0 / 8 | 16 / 0 / 8 | 100% | 66.67% | 0 / 0 / 7 |
| Archived vision v2 | 22 / 9 / 2 | unchanged | 70.97% | 91.67% | 1 / 6 / 7 |

Final deterministic graphs all pass evidence checks, so raw and accepted counts
coincide. Old DXF accepted counts were 21 TP / 0 FP / 3 FN because its entire hop
graph was rejected. Baseline geometry has no detection evidence: all 31 predicted
edges are ineligible, including its six direction claims. This is reported as
missing baseline detector evidence, not twelve checker executions or twelve
extraction failures.

Vector routes have zero observed false edges at crossings, reversals,
reference-unsupported directions and evidence violations on this set. Raster
also has zero direction errors but **makes no direction claims**; its direction
precision is null and recovery is 0/7. Raster cannot meet the target by abstaining.

The remaining vector miss is the interrupted horizontal edge in `break-crossing`.
Its source model knows the intended continuity; visible geometry does not prove
it. Its reference and missed-edge count are retained. There is no gap-bridging
heuristic and no post-result relabeling of that fixture.

## Why this is not yet a qualification pass

The [metric contract](DIAGRAM_METRIC_CONTRACT.md) sets distinct point targets,
confidence requirements, evidence obligations and independent-family gates.

| PDF and DXF metric | Count | Point estimate | Two-sided 95% Wilson interval |
|---|---:|---:|---:|
| Edge precision | 23 / 23 | 100% | 85.69%–100% |
| Edge recall | 23 / 24 | 95.83% | 79.76%–99.26% |
| Direction precision | 7 / 7 | 100% | 64.57%–100% |
| Direction recovery | 7 / 7 | 100% | 64.57%–100% |

Both vector routes meet the proposed **point** targets here; neither meets the
confidence requirements. Moreover, these are correlated development drawings
from one simple-line generator, with assisted label/port localization. Per drawing,
conservative source family, route, failure category, raw/accepted graph and status
counts are in `results-final.json`. There is no pooling of formats for qualification.
Wilson intervals are descriptive iid approximations; the later qualification
study needs preregistered independent families and cluster-aware analysis.

## Next gates and who contributes

### Assessment comments incorporated (28 September)

The supplied assessment describes the **pre-repair** experiment. Its priorities
are retained below, with the final replay and evaluation-integrity corrections
applied. Its embedded lane prompt is review context, not a new execution request.

| Supplied observation or proposal | Assessment and disposition |
|---|---|
| Vector PDF is the only route near a usable bar; identify its single miss. | Correct for the original run. DXF now matches PDF on the same regression set. The remaining miss is the horizontal interrupted line in `break-crossing`, not a port-supply artifact. Neither route is qualified by this sample. |
| DXF's seven false edges have one root cause; checker rejection is working. | Agreed: concentrated spline-fragmentation errors made a targeted repair worthwhile. The measured 75.9% raw precision was still a real failure, not an overstated metric. Checker rejection protected downstream use and reduced accepted recall; it did not erase those errors. The repair now gives 23 TP / 0 FP / 1 FN. |
| Raster loses line pixels during arrow removal; detect arrows and lines separately. | A useful hypothesis and next experiment, not a demonstrated sole cause. Six directed edges are missed; the small-arrow edge is recovered with unknown direction, and hop recovery also fails. Test independent arrow/line paths and classify their failures before choosing a remedy. |
| Keep the vision baseline only as a reference row. | Accepted. Archived outputs remain diagnostic comparison data; they cannot satisfy the detector-evidence contract or supply trusted topology. No further prompting is planned. |
| Twelve drawings, seven arrows and supplied ports cannot establish deployment accuracy. | Accepted. One missed edge changes recall by 1/24, about 4.17 percentage points. Report raw counts, point estimates and intervals; do not pool sibling formats or call the regression set held out. |
| About 750 error-free edges establishes a 99.5% precision lower bound. | Corrected: the two-sided 95% Wilson lower bound is 99.4904% at 750/750, below the target. It first exceeds 99.5% at 765/765 under independent-trial assumptions. Correlated edges and a separate arrow denominator require additional study design, not just more edges. |
| Preserve native curves; flatten for rendering only; one spline hop gives one edge. | Preserve native topology/identity and verified source contacts. Controlled approximation may support geometry calculations, but its samples must not become junctions. Actual endpoint-on-curve tees and filled dots must remain supported. An isolated hop path has one connection; the complete hop fixture includes a second crossing line, so its expected result is **two independent through edges**. |
| Raster must pass held-out twice; reviewer timing uses the same drawings. | Require two separately reserved, untouched family cohorts for two independent validation rounds. Repeating the same set only checks reproducibility. For timing, use matched different drawings in counterbalanced conditions to avoid familiarity effects; post-review errors must not increase. |
| Signed overlay corrections feed ground truth. | They feed a new version of development/reference data with provenance and independent review. Never overwrite frozen gold after seeing predictions. Source-only reference tracing and signing must precede held-out scoring. |

The requested workstreams therefore remain: **(1) native continuity repair,
completed for this bounded regression; (2) vector qualification and reviewer
overlay, next; (3) raster recovery, separate and deferred.** The raster research
can later run alongside qualification when separately scheduled, but this update
does not start another implementation lane.

The [metric contract and evaluation template](DIAGRAM_METRIC_CONTRACT.md) now also
record the requested critical-error classes, miss categories, arrow/scan buckets,
end-to-end port/tag measurements and CI/reporting requirements. These are future
qualification obligations where the current harness does not yet implement them.

1. **Bill/appointed reviewer:** accept drawing conventions, first useful task and
   critical-error/abstention policy using the checklist in the metric contract.
   No need to wait for Bill to prepare the overlay and fixture inventory.
2. **Foundry/Broadbridge:** reviewer overlay, independently traced/source-model
   references and a new pre-run frozen vector holdout with pinned visible-arrow
   eligibility and source-family splits. The current set remains regression-only.
3. **Separate raster work:** preserve line continuity during arrow isolation,
   recover rotated/small arrow keypoints, and test scan degradation on new
   development cases. Existing raster misses stay visible.
4. **Before diagram training:** pin crop-history metadata; resolve source/software
   rights; obtain technical/reference acceptance, independent held-out qualification
   and explicit training/release approval. None is closed by this repair.

The two interim detector attempts and their reports are retained for audit.
`detected-final` and `results-final.json` are authoritative for this repair; the final
source hashes are recorded in the run receipt. `metrics-before-review.json` has
the superseded status accounting and is not a qualification report. No historical
result is replaced. Validation commands/counts and review findings are recorded
in `evidence/vector-continuity-2026-09-28/validation.json`.

## Replay (offline)

Set `$foundryRepo` to the absolute matching Foundry checkout and `$geometryPython`
to its existing CPU geometry interpreter. From Broadbridge:

```powershell
$old = 'docs/evidence/deterministic-diagrams-2026-09-27/inputs'
$new = 'docs/evidence/vector-continuity-2026-09-28'
& $geometryPython scripts/research/vector_qualification.py --foundry $foundryRepo --work $old --detected "$new/detected-final" --baseline "$old/baseline-v2" --out packs/oil-gas/outputs/vector-metrics-replay.json
# Optional fresh detector replay; choose a new output directory.
& $geometryPython scripts/research/deterministic_diagrams.py run --foundry $foundryRepo --work $old --out packs/oil-gas/outputs/vector-new-cpu-run
```

Output paths must not already exist. The reporter verifies original asset and
receipt bindings before computing metrics. A deterministic rerun measures
reproducibility; it does not add independent observations to the confidence bounds.
