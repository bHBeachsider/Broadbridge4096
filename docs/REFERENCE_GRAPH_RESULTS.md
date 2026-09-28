# Reference-graph pilot results — 27 September 2026

The source-led approach works as a validation mechanism. It does **not** yet justify admitting visual extractions to training: the local model still reverses explicit arrows, invents flow direction and joins disconnected crossing pipes. Native reference data makes these mistakes measurable.

No training, EC2, client drawings, production changes or downloads over 1 GB. The original Foundry #13 and Broadbridge #17 remain open drafts. This work is in successor draft branches; domain data remains in Broadbridge, reusable adapter code in Foundry.

## Per-source inventory

| Source | Acquired/created | Mapped result | License / disposition |
|---|---:|---|---|
| DEXPI C01 | 1 XML + matching SVG | 37 endpoint/component nodes, 31 segment connections; 27 have both endpoints, 4 retain null endpoints; 0 known flow directions | Verified CC BY 4.0; eval-only family |
| pyDEXPI 1.2.0 | 201,065-byte wheel | Isolated research adapter; JSON + source-ID-sidecar round-trip preserves C01 nodes/edges exactly | Verified AGPL-3.0; proprietary deployment unresolved |
| dexpi-render | License/metadata only | Not installed | Verified MIT code; no data admission |
| DEXPI2graphML | License/metadata only | Not installed | Verified LGPL-3.0 code; bundled drawing rights separate |
| PID2Graph DatasetPID member 0 | 1 PNG + GraphML, ~6.72 MB | 452 nodes, 496 undirected annotation edges; 474 solid / 22 non-solid | Record CC BY-SA 4.0; eval-only mapping, **not trusted physical topology** |
| PID2Graph OPEN100 | 0 drawings | Primary paper describes 12 manually annotated public nuclear-design drawings | Original underlying drawing grant UNKNOWN; no training |
| Dataset-P&ID original | 0 files | Symbols/labels/line segments only | Original dataset license UNKNOWN; no training |
| SynthPID | 0 code/data/weights | Public GitHub release unverified (404); no integration | Code/data license UNKNOWN |
| Original local synthetic | 6 pyDEXPI models, 7 image/graph/seed pairs including a disclosed corrected rendering | 6 qualified comparisons; original defective rendering retained separately | Internal eval-only; no training admission |

Acquired total: **7,511,497 bytes**, recorded in [acquisition.json](evidence/reference-graphs-2026-09-27/acquisition.json). The full PID2Graph archive is 9,303,633,645 bytes and was not fetched. No client-owned material was inspected. Counts describe the selected files, not full collection sizes.

C01 missing endpoint IDs: `PipingNetworkSegment-20/connection/0`, `-21/connection/0`, `-22/connection/0`, `-23/connection/1`. They are preserved, not guessed or silently removed. Five informational pyDEXPI messages describe native connector-line reconstruction; one describes reversing an equipment association. These are retained in the [source receipt](evidence/reference-graphs-2026-09-27/source-results.json). The adapter is a piping-connection inventory; it does not assert vessel internals or instrumentation connectivity.

PID2Graph sample node classes: connector 235, crossing 92, valve 58, general 34, instrumentation 25, arrow 4, background 4. Crossings, connectors and patch borders need dataset-specific semantics; class labels/bounding boxes do not supply ports, actual equipment tags, line identifiers or physical flow direction. The mapper refuses to project these annotations as physical piping gold. The [primary paper §III-D](https://arxiv.org/html/2411.13929v3#S3.SS4) explains the segment-overlap conversion and distinguishes OPEN100's manual annotations.

## Local vision/checker results

Qwen3-VL `qwen3-vl:4b-instruct-q4_K_M`, pinned digest `ee4b975b58c17ce268cd19d40db35d5edc64603035d2ffc1fee1968eb0947f7b`; CPU Docker, 8 CPUs / 10 GiB limit, no host port or external inference. Existing `connectivity_v2` profile: `think:false`, 384 output tokens, 180-second per-call cap. No prompt tuning against these results.

| Drawing | Edge P / R | Known-direction P / R | Unsupported direction claims | Checker | Seconds |
|---|---|---|---:|---|---:|
| Forward chain | 100% / 100% | 100% / 100% | 0 | Pass | 69.913 |
| Reverse chain | 100% / 100% | 0% / 0% | 0 | Fail: both arrows reversed | 81.690 |
| Junction | 100% / 100% | 100% / 100% | 0 | Pass | 68.586 |
| Crossing — corrected rendering | 50% / 100% | N/A / N/A | 0 | Fail: two extra cross-connections | 69.819 |
| No-arrow chain | 100% / 100% | N/A / N/A | 0 | Needs review: model uncertainty | 62.487 |
| Mixed junction | 100% / 100% | 100% / 100% | 2 | Fail: asserts directions without arrows | 67.410 |
| **Qualified micro-average** | **87.5% / 100%** | **75% / 75%** | **2** | **2 pass / 3 fail / 1 needs review** | **419.905** |

Qualified edge counts: TP 14, FP 2, FN 0. Direction: 6 correct of 8 asserted/known directions. Unknown reference directions are excluded from direction P/R, not treated as correct; assertions on unknown directions are separately flagged. Directed false-positive edges would count against direction precision. These are exact tagged-edge metrics on tiny development fixtures, **not** published benchmark mAP or proof of real-world accuracy.

Visual inspection found that my first crossing renderer let the bridge touch the other line. Its result (50% edge precision, 100% recall, 69.017 seconds) is preserved but excluded from the qualified figures. One corrected image kept the same underlying graph/family, separated the bridge and moved labels clear of the vertical line. That correction still failed on the same two false connections. This is a disclosed fixture repair, not a best-of-many selection. Seven calls completed; summed request time **488.922 seconds (8 minutes 9 seconds)**, plus Docker startup/teardown. Both runs stopped the vision stack afterward; the speech service was not altered.

Frozen receipts and inspectable generated images:

- [Original six-item job](evidence/reference-graphs-2026-09-27/pilot/job.json), [references](evidence/reference-graphs-2026-09-27/pilot/references.json), [all first-batch metrics](evidence/reference-graphs-2026-09-27/pilot/metrics.json).
- [One-item correction job](evidence/reference-graphs-2026-09-27/crossing-correction/job.json), [correction metrics](evidence/reference-graphs-2026-09-27/crossing-correction/metrics.json), [corrected drawing](evidence/reference-graphs-2026-09-27/crossing-correction/crossing-clear.png).
- Each job preserves image, prompt, reference, result and model hashes. Full runtime metadata, native snapshots and downloaded source files remain in ignored `packs/oil-gas/outputs/reference-graphs-2026-09-27/`.

## Validation and remaining decisions

Foundry: **234 passed** (existing 215-test regression group plus 19 new tests), including the pinned C01 integration fixture. One pre-existing Requests dependency warning. Broadbridge: **389 passed, 113 skipped** (existing 375 passing tests plus 14 new tests). DB-dependent tests skip offline; no database connection was enabled.

Final independent code review found three issues, all fixed with regression tests: invalid completed vision proposals could receive accuracy credit; HTTP redirects could escape the bounded download policy; and distinct native objects with the same Proteus ID could be merged. Invalid proposals now receive no prediction credit, redirects are refused before following or reading their bodies, and duplicate source identities fail loudly.

The frozen PNGs are the replay inputs. This run used Python 3.13.5, Pillow 12.1.1 and Windows `arial.ttf`, SHA-256 `b3658eadae55e682b5f69eb64c439c1ecc8f196c0bb8d4756d145d13bc86476a`. The renderer's Linux fallback uses DejaVu Sans: regenerating on another font/platform creates a new image hash and requires new bound references/results. Cross-platform pixel-identical regeneration is not claimed; OS fonts are not redistributed.

Tests cover missing and reversed edges, port/line/tag lineage, missing endpoints, unknown/unmapped XML and graph classes, ID-sidecar loss, serialization, strict bounded projection, parallel-pipe rejection, annotation/physical-graph separation, unknown directions, metric denominators, unsigned trace refusal, hash-bound independent sign-off, UNKNOWN-license refusal and bounded download hash/size checks.

Licensing holds: original Dataset-P&ID grant; underlying OPEN100 drawings; SynthPID code/data availability and rights; any proprietary pyDEXPI deployment. Eval-only family restrictions separately block C01, inspected PID2Graph and all synthetic evaluation derivatives regardless of a permissive license. No generated proposals entered the existing training-candidate pipeline.

Next useful action is a **small independently reviewed native-model crop set** with explicit flow annotations and tested crossing conventions, plus a reviewer-approved mapping for any additional DEXPI class. Human-traced client drawings remain design-only until the user separately authorizes their use and rights are recorded. See [source registry and sign-off design](REFERENCE_GRAPH_SOURCES.md).
