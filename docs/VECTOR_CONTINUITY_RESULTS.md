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
| Edge precision | 23 / 23 | 100% | 85.69%â€“100% |
| Edge recall | 23 / 24 | 95.83% | 79.76%â€“99.26% |
| Direction precision | 7 / 7 | 100% | 64.57%â€“100% |
| Direction recovery | 7 / 7 | 100% | 64.57%â€“100% |

Both vector routes meet the proposed **point** targets here; neither meets the
confidence requirements. Moreover, these are correlated development drawings
from one simple-line generator, with assisted label/port localization. Per drawing,
conservative source family, route, failure category, raw/accepted graph and status
counts are in `results-final.json`. There is no pooling of formats for qualification.
Wilson intervals are descriptive iid approximations; the later qualification
study needs preregistered independent families and cluster-aware analysis.

## Next gates and who contributes

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
