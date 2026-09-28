# Deterministic diagram connectivity â€” results

Experiment frozen 27 September 2026; review/validation completed 28 September. **Diagram training remains blocked.** The vector PDF path is promising on simplified construction drawings; DXF spline hops and raster arrow recovery are not solved. Text and calculation preparation continues independently. No EC2, GPU, training, production changes or client drawings were used.

## What changed

Foundry now has an optional CPU-only geometry path: PDF `get_drawings`, DXF `ezdxf`, or raster segmentation/skeletonization. Every emitted edge carries path segments, connection evidence and the applied `no_dot_crossing_nonconnecting/1` convention. A known direction must reference a detected arrow and agree with its base-to-tip orientation; absent, distant, ambiguous or conflicting arrows leave direction unknown. The checker rejects unsupported directions and a turn through an unmarked crossing. This is a declared project convention; actual plant drawing legends and the applicable ISA revision still require review.

Visibility guards reject hidden/nonplanar DXF, patterned hatches as dots, and unsupported PDF colors/layers/visibility. Raster PDFs are bounded before rendering. These limits avoid silently treating invisible geometry as connections; they do not make this a general CAD interpreter.

## Frozen experiment and fairness limits

Twelve original pyDEXPI construction models, seeds 2100â€“2111, contain 24 reference edges, seven directed. Each has PDF/DXF/PNG siblings: 36 deterministic route records and 12 unchanged image-only model requests. No source/client drawings were used to seed them. References come from construction models, never model output. These are simplified labeled port-and-line diagrams, not realistic refinery P&IDs with full equipment symbol libraries.

The exact inputs, reference graphs, seed specifications, label-only port annotations, raster text masks, detector parameters, model/prompt settings and hashes were committed at `cb35724` before any inference. `7ef89e7` marks DXF binary so Git preserves the already-frozen bytes; all 61 assets matched Git bytes. Manifest SHA-256 `962e2c8156cc2085d95c2be40994bde23486ce2b29e79ffafcf6bf42a6eb7c19`; job SHA-256 `d15c1dbcd10e0a0b56c255d3e818f3931d3bfacade14cdbff28d60c51e57accf`.

Detectors receive supplied labels/port positions and the raster route receives text masks. The image-only baseline must read labels itself. Thus this measures conditional connectivity with assisted localization, not a fair end-to-end OCR benchmark or production accuracy claim. It is a development set without independent expert sign-off, not a release gate set.

The installed local CPU `qwen3-vl:4b-instruct-q4_K_M` baseline reused the unchanged v2 prompt/settings, one request per PNG, no retries, no prompt optimization. Digest `sha256:ee4b975b58c17ce268cd19d40db35d5edc64603035d2ffc1fee1968eb0947f7b`. All 12 requests completed. The wrapper stopped the dedicated container; a subsequent Docker query confirmed no running `foundry-vision` container.

First detector run `detected-v1` used Foundry `c92fddb`. Review identified visibility/planarity/pattern-fill and pre-render memory guards; these were tested and fixed at `9b53527`. `detected-v2` is a separately retained replay after those guards; all performance counts are unchanged. No stress images, references, tolerances, prompts or model settings were tuned after the freeze. Both attempts are archived; final reporting adds explicit raw-versus-rejected counts and known-direction coverage.

## Results before evidence rejection

Raw counts deliberately retain erroneous geometry even when the evidence checker rejects it. Malformed/missing proposals receive no credit and count against recall. No failed cases are dropped. Zero denominators are `null`/n/a, not zero errors.

| Route | TP / FP / FN | Edge precision | Edge recall | False edges at crossings/hops/breaks |
|---|---:|---:|---:|---:|
| Unchanged vision v2 | 22 / 9 / 2 | 71.0% | 91.7% | 9 |
| Vector DXF | 22 / 7 / 2 | 75.9% | 91.7% | 7 |
| Vector PDF | 23 / 0 / 1 | 100.0% | 95.8% | 0 |
| Raster PNG | 16 / 0 / 8 | 100.0% | 66.7% | 0 |

| Route | Correct known directions | Reversed / 7 | Unknown / missing known directions | Unsupported vs reference / all claims | Claims lacking validated arrow evidence |
|---|---:|---:|---:|---:|---:|
| Unchanged vision v2 | 1 / 7 | 1 / 7 (14.3%) | 5 / 0 | 4 / 6 (66.7%) | 6 / 6 |
| Vector DXF | 7 / 7 | 0 / 7 (0.0%) | 0 / 0 | 0 / 7 (0.0%) | 0 / 7 |
| Vector PDF | 7 / 7 | 0 / 7 (0.0%) | 0 / 0 | 0 / 7 (0.0%) | 0 / 7 |
| Raster PNG | 0 / 7 | 0 / 7 (0.0%) | 1 / 6 | 0 / 0 (n/a) | 0 / 0 |

A reference-unsupported claim asserts direction on an unknown/nonexistent reference edge. Arrow-evidence failure is a different test: the old vision output has no detector-backed `arrow_id`, so **all six of its direction claims lack the new evidence**, including its one correct guess. For raster, zero reversal/unsupported counts accompany **zero direction coverage**, not success. Known-direction coverage: PDF/DXF 100%, raster 0%, baseline 28.6%. Accuracy among claimed known directions: PDF/DXF 100%, raster n/a, baseline 50%.

After evidence rejection, DXF keeps 21 TP, 0 FP, 3 FN (precision 100%, recall 87.5%); its entire hop result is rejected. PDF/raster counts are unchanged. Passing a geometry check never approves training; the baseline cannot enter this new evidence contract.

## Per-failure metrics

Each cell set aggregates only the listed category; rotated covers two drawings, tee covers dotted and undotted variants, all other categories one each. FP at crossing categories counts erroneous edges in those drawings; it does not localize a pixel intersection. Unsupported = reference-unsupported claims; the separate arrow-evidence table above applies to every category.

| Failure category | Route | TP / FP / FN | Precision / recall | False crossing edges | Reversal rate | Unsupported-direction rate |
|---|---|---:|---:|---:|---:|---:|
| break | Vector PDF | 1 / 0 / 1 | 100.0% / 50.0% | 0 | n/a | n/a |
| break | Vector DXF | 1 / 0 / 1 | 100.0% / 50.0% | 0 | n/a | n/a |
| break | Raster PNG | 1 / 0 / 1 | 100.0% / 50.0% | 0 | n/a | n/a |
| break | Unchanged vision v2 | 1 / 2 / 1 | 33.3% / 50.0% | 2 | n/a | n/a |
| crossing | Vector PDF | 4 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| crossing | Vector DXF | 4 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| crossing | Raster PNG | 4 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| crossing | Unchanged vision v2 | 3 / 5 / 1 | 37.5% / 75.0% | 5 | n/a | n/a |
| forward | Vector PDF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| forward | Vector DXF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| forward | Raster PNG | 0 / 0 / 1 | n/a / 0.0% | 0 | 0.0% | n/a |
| forward | Unchanged vision v2 | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | n/a |
| hop | Vector PDF | 2 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| hop | Vector DXF | 1 / 7 / 1 | 12.5% / 50.0% | 7 | n/a | n/a |
| hop | Raster PNG | 1 / 0 / 1 | 100.0% / 50.0% | 0 | n/a | n/a |
| hop | Unchanged vision v2 | 2 / 2 / 0 | 50.0% / 100.0% | 2 | n/a | n/a |
| junction | Vector PDF | 4 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| junction | Vector DXF | 4 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| junction | Raster PNG | 4 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| junction | Unchanged vision v2 | 4 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| no_arrow | Vector PDF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| no_arrow | Vector DXF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| no_arrow | Raster PNG | 1 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| no_arrow | Unchanged vision v2 | 1 / 0 / 0 | 100.0% / 100.0% | 0 | n/a | n/a |
| reverse | Vector PDF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| reverse | Vector DXF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| reverse | Raster PNG | 0 / 0 / 1 | n/a / 0.0% | 0 | 0.0% | n/a |
| reverse | Unchanged vision v2 | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | n/a |
| rotated | Vector PDF | 2 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| rotated | Vector DXF | 2 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| rotated | Raster PNG | 0 / 0 / 2 | n/a / 0.0% | 0 | 0.0% | n/a |
| rotated | Unchanged vision v2 | 2 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | n/a |
| small_arrow | Vector PDF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| small_arrow | Vector DXF | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| small_arrow | Raster PNG | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | n/a |
| small_arrow | Unchanged vision v2 | 1 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | n/a |
| tee | Vector PDF | 6 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| tee | Vector DXF | 6 / 0 / 0 | 100.0% / 100.0% | 0 | 0.0% | 0.0% |
| tee | Raster PNG | 4 / 0 / 2 | 100.0% / 66.7% | 0 | 0.0% | n/a |
| tee | Unchanged vision v2 | 6 / 0 / 0 | 100.0% / 100.0% | 0 | 50.0% | 66.7% |

## Remaining failures and gates

- **DXF hop:** spline fragmentation creates seven false graph edges/junctions; the evidence checker rejects the result (`No shared endpoint at claimed location`). Preserve the failure. A future curve-topology repair needs new development examples and then independently frozen holdouts.
- **Raster arrows and hops:** six arrow-bearing reference edges are missed; the small-arrow edge is recovered with unknown direction. The curved overpass is also incomplete. Arrow blob isolation/line continuity remains experimental; zero invented arrows is not useful direction recovery.
- **Break convention:** every deterministic route misses the interrupted horizontal edge in the break fixture. The construction model knows it is continuous, but the detector does not guess across a visible gap. Crossing nonconnection is correct; recovering pipe continuity requires explicit break-symbol/legend evidence.
- **Crop-history metadata pinned â€” REQUIRED and still deferred.** Full-frame hashes for this new set do not close the system-wide crop lineage gate.
- **Independent reference and technical acceptance:** Bill or another appointed reviewer must accept the topology/legend and realistic OCR/port mapping, failure tolerances and task scope. This simplified unreviewed stress set is not sufficient.
- **New pre-run held-out evaluation:** independent families/revisions/crops, complete misses, arrows, ports and symbol handling; define thresholds before running. Do not promote this development result into a release gate.
- **Rights/software review:** source ownership and permitted use, and appropriate PyMuPDF/pyDEXPI deployment terms, must be cleared before deployment or training. Current artifacts are evaluation-only.
- **Explicit training/release approval:** no graph record is emitted with `training_approved: true`. No training batch or adapter was produced.

The [original experiment disposition](evidence/diagram-repair-2026-09-27/disposition.json) explicitly labels `provenance: retrospective-checksum`, `gate_eligible: false`. Its raw receipts remain unchanged and cannot be used for gate decisions. New pre-run input provenance is recorded here, but every current result also remains `gate_eligible: false`.

## Sources and license status

The [source register](REFERENCE_GRAPH_SOURCES.md) and [machine manifest](../packs/oil-gas/manifests/reference_graph_sources.json) remain authoritative. This experiment uses 12 original construction fixtures only. [PID2Graph v1](https://zenodo.org/records/14803338), DOI `10.5281/zenodo.14803338`, was rechecked: its record declares CC BY-SA 4.0 for DatasetPID and synthetic symbols. That does not independently resolve upstream OPEN100 drawing rights or make annotation adjacency signed engineering topology. Existing sample remains eval-only; the 9.3 GB archive was **not downloaded**, and no new PID2Graph material was used here. Candidate training use remains blocked pending rights/topology review. No download exceeded 1 GB.

## Reproduction and audit

Artifacts: [frozen inputs](evidence/deterministic-diagrams-2026-09-27/inputs/manifest.json), [machine results](evidence/deterministic-diagrams-2026-09-27/results-final.json), [route log](evidence/deterministic-diagrams-2026-09-27/detected-v2/routes.json), run/code/version receipts under `detected-v1` and `detected-v2`, and raw baseline records under `inputs/baseline-v2`. Host-specific Docker inspection metadata stays ignored. Output hashes seal archived evidence after execution; only the input freeze is claimed pre-run. The scripts check input/model/prompt/receipt bindings and reject tampering; checksums are integrity evidence, not signatures by an engineer.

Use Foundry's isolated CPU `requirements-geometry.txt` environment for extraction. Installed versions: PyMuPDF 1.28.2, ezdxf 1.4.4, scikit-image 0.26.0, numpy 2.3.3; local OpenCV package `opencv-python` 4.13.0.92, optional clean-env requirements use its headless build at the same version. pyDEXPI 1.2.0 is needed only for new generation. The existing frozen inputs require no model or dataset download.

From Broadbridge (absolute `$foundryRepo`, matching draft branch; set `$geometryPython` to its isolated interpreter):

```powershell
$e = 'docs/evidence/deterministic-diagrams-2026-09-27'
# Replay archived scoring only: no model, network, GPU or dataset generation.
& $geometryPython scripts/research/deterministic_diagrams.py report --foundry $foundryRepo --work "$e/inputs" --detected "$e/detected-v2" --baseline "$e/inputs/baseline-v2" --out packs/oil-gas/outputs/geometry-replay.json
# Optional CPU detector replay to a NEW directory; the original inputs stay fixed.
& $geometryPython scripts/research/deterministic_diagrams.py run --foundry $foundryRepo --work "$e/inputs" --out packs/oil-gas/outputs/geometry-new-run
```

The script refuses to overwrite existing run/report files. Generation is a separate `prepare` action into a new directory; generated DXF headers may vary, so replay the committed bytes for exact comparison rather than calling fresh generation the same frozen experiment. Original request runtime totals are in baseline `summary.json`; the dedicated local CPU baseline took 837.271 seconds (14.0 minutes) of inference, plus startup/shutdown. No baseline retries were made.

Validation: Foundry full offline suite **775 passed, 3 skipped**; focused geometry **42 passed**. Broadbridge full offline suite **431 passed, 103 skipped**. Exact commands, skip reasons and review record are in [validation.json](evidence/deterministic-diagrams-2026-09-27/validation.json). Eleven new research tests include exact archived replay, changed-baseline/detector receipt rejection, freeze tampering, raw error retention, unknown/missing direction coverage and absent-arrow evidence. Optional live database/model dependencies remain unexercised. Independent read-only review reproduced and then confirmed the visibility/planarity/hatch/render-bound fixes. Existing environment Requests/Swig warnings remain; no dependency cleanup was folded into this task.
