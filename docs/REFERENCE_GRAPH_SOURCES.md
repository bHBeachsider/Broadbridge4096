# Reference-graph sources

Verified 27 September 2026. Machine-readable authority: [source manifest](../packs/oil-gas/manifests/reference_graph_sources.json). Local results and exact counts: [results](REFERENCE_GRAPH_RESULTS.md). Every acquired/generated item in this pilot is **eval-only**; no training approval is created. UNKNOWN licenses block training. Tool licenses and data licenses are separate.

The proposals are useful, with one important qualification: a downloadable graph is not necessarily trusted engineering topology. Gold comes from a native model, an original construction specification, or an independently signed human trace. Vision output never supplies the reference. Whole drawings, revisions, crops and generated derivatives share a family split.

| Source | Pinned version | Verified license | Topology and decision |
|---|---|---|---|
| [DEXPI Public Example PIDs](https://gitlab.com/dexpi/TrainingTestCases) | `a23d61e2e089eb2ca464cd552f9ae580a2785963` | Repository [LICENSE](https://gitlab.com/dexpi/TrainingTestCases/-/blob/a23d61e2e089eb2ca464cd552f9ae580a2785963/LICENSE): CC BY 4.0 | Native model. C01 XML/SVG acquired. Gold **evaluation family**; four unspecified endpoints remain gaps and all flow directions remain unknown. No blanket claim about every vendor example. |
| [pyDEXPI](https://github.com/process-intelligence-research/pyDEXPI) | 1.2.0; `83e5a11c4af3635ad12290a4dbe310480eb6d7a3` | Actual LICENSE: AGPL-3.0 | Native-model adapter and construction tool, not a dataset. Optional isolated local environment only. Its generic graph includes composition/reference relations; those must not become pipe edges. |
| [dexpi-render](https://github.com/uchokoro/dexpi-render) | `5a64cdf0bbdbb95799e73b276e4915b624305260` | Actual LICENSE: MIT | Renderer candidate; not installed. Rendering does not establish topology or license input drawings. |
| [DEXPI2graphML](https://github.com/TUDoAD/DEXPI2graphML) | `cf2820fd185a17ab15097f5c17807db5ea566d3f` | Actual LICENSE.txt: LGPL-3.0 | Native-model adapter candidate; not installed. Source shapes must already have connections; it cannot repair missing engineering relationships. |
| [PID2Graph](https://zenodo.org/records/14803338), DatasetPID member 0 | DOI `10.5281/zenodo.14803338`, v1 | Record: CC BY-SA 4.0; record also declares this for DatasetPID origin | One image/GraphML pair acquired individually. The original paper says these graph edges are formed by joining annotated line segments. **Mapped annotation adjacency, not native or human-signed gold**. |
| PID2Graph OPEN100 | Same DOI/version; underlying drawing revisions not verified | Record-wide CC BY-SA 4.0; original drawing grant **UNKNOWN** | Twelve manually annotated nuclear-design drawings are described in the primary paper. No OPEN100 files acquired. Dataset annotation is not Bill's signed trace; no claims about operating refinery as-builts. |
| [Dataset-P&ID / Digitize-PID](https://arxiv.org/abs/2109.03794) | Paper v1, 2021-09-08; original release revision unverified | Original dataset license **UNKNOWN**; paper license is not a dataset grant | Original release is symbols/labels/line segments, **not topology**. No original archive acquired. PID2Graph's additional conversion does not change this source's scope. |
| [SynthPID](https://arxiv.org/abs/2604.16513) | Paper v1, 2026-04-15 | Paper CC BY 4.0; code/data **UNKNOWN** | Availability check only. Claimed GitHub release returned 404 publicly and via API. Do not integrate. |
| Broadbridge original construction fixtures | Generator v1, seeds 901–906; one disclosed rendering correction | Original in-house parameters/shapes, internal evaluation | Six pyDEXPI models and seven renderings total. Graphs frozen from construction, not vision. No C01/OPEN100 seed derivation; all remain development/eval-only. |

## What was verified and what is blocked

The actual repository license texts were acquired for DEXPI, pyDEXPI, dexpi-render and DEXPI2graphML; hashes are in the manifest/acquisition receipt. The pilot downloaded **7,511,497 bytes total** of samples, licenses, metadata and the small pyDEXPI wheel. Nothing over 1 GB was downloaded. PID2Graph's **9,303,633,645-byte** archive remains blocked by the explicit download boundary. Zenodo's container API exposes individual members, so only the named image and GraphML were fetched.

PID2Graph contains a real-engineering subset: OPEN100. Its [primary paper, §III-D](https://arxiv.org/html/2411.13929v3#S3.SS4) identifies 12 public reactor drawings, manually annotated. The same paper explains that DatasetPID graphs are converted from overlapping annotated line segments. Keep these provenance paths distinct. Unverified underlying OPEN100 permissions prevent training; this is not resolved merely by an archive-level license label.

The [SynthPID paper](https://arxiv.org/html/2604.16513v1) claims code, data and weights at `LatentSpaceIITB/SynthPID`. That public endpoint and GitHub API returned 404 during this check. This means public availability is **unverified**, not proof that the work does not exist. No integration/download was attempted. It also derives synthetic examples from OPEN100 evaluation drawings: under our family rule, derivatives cannot cross into training while the originals are held out.

Proprietary pyDEXPI deployment needs license review or an appropriate commercial arrangement. This does not imply that all generated output automatically inherits AGPL. Original dataset rights, redistribution, attribution/share-alike obligations and commercial software integration are separate checks. UNKNOWN rights are held, not interpreted as permission.

## Adapter acceptance

The Foundry adapter retains source item IDs, port IDs, line/segment IDs and original tags. It fails on unmapped classes and non-info loader diagnostics. All 31 C01 segment connections survive the pyDEXPI/JSON round-trip, including four unresolved endpoints. Instrumentation signals, vessel internals and source containment are outside this piping-connection adapter's scope.

pyDEXPI JSON drops original Proteus IDs; the adapter stores an explicit ID sidecar and validates it on restore. The native inventory is separate from the existing small frozen checker schema. A bounded checker view records exactly which native edges were selected, along with the topology hash. Parallel pipes, unresolved selected endpoints, ambiguous tags and oversized views fail rather than being silently flattened. The mapping is not a simulation-ready plant model.

## Human tracing — design only

Before any client drawing is accepted, record owner, written permitted use, confidentiality, storage location, original file hash, drawing number/revision/sheet and as-built status. Brad obtains permission; a qualified tracer records nodes, physical ports, line IDs and connections directly from the drawing. An optional vision proposal may highlight differences, but must never initialize an automatically trusted reference.

Use an authenticated review event with these fields:

| Field | Requirement |
|---|---|
| Tracer | Identified person who traced the original drawing; date and tracing method |
| Reviewer | Bill Hurt, or an explicitly appointed independent reviewer; must differ from tracer |
| Source | Original file hash, rendered sheet/image hash, evidence ID, drawing number, revision, sheet, as-built status |
| Reference | Frozen reference graph hash; parent native topology hash and selected edge IDs for a bounded view |
| Review | ISO date, authenticated account/event ID, reviewed scope, unresolved connections/directions, explicit signed flag |
| Proposal diff | Proposal hash plus added/removed edges and direction changes, or explicit `no_proposal` |
| Rights | Owner, permission evidence, permitted use, expiry/revocation terms and approved storage |

The Foundry `foundry.trace_signoff/1` checker binds the reference/image/evidence ID, named independent people, revision, date and proposal-diff record. Unsigned, stale or incomplete records are **UNREVIEWED**. A name typed into a JSON file is not authenticated sign-off; the eventual capture application must supply the record from an authorized stored review event. This pilot does not implement that UI or signing service and does not collect client drawings.

A new drawing revision, changed source image or changed graph invalidates the old sign-off. Any unresolved edge stays unresolved. Technical acceptance and source rights approval are both required before a future training-admission decision; neither a matching vision output nor a checker pass grants it.

## Reproduction

Use the optional isolated environment described in Foundry `docs/REFERENCE_GRAPHS.md`, with the exact two successor branches. Keep originals and results in ignored `packs/oil-gas/outputs/`. Fetch only the small files listed in the committed acquisition receipt, verifying byte counts and hashes. Do not download the archive URL.

From the Broadbridge worktree (set `$foundryRepo` to the matching Foundry checkout):

```powershell
$foundryRepo = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http'
$researchRoot = 'packs/oil-gas/outputs/reference-graphs-2026-09-27'
$researchPython = "$researchRoot/venv/Scripts/python.exe"
& $researchPython scripts/research/reference_graph_pilot.py prepare --foundry $foundryRepo --raw "$researchRoot/raw" --out "$researchRoot/pilot-new"
& "$foundryRepo/infra/vision/vision.ps1" Batch -WorkDir "$((Resolve-Path "$researchRoot/pilot-new").Path)" -ResultName results-qwen
& $researchPython scripts/research/reference_graph_pilot.py report --foundry $foundryRepo --out "$researchRoot/pilot-new" --results "$researchRoot/pilot-new/results-qwen"
```

Use `correct-crossing --raw <original pilot> --out <new correction directory>` for the disclosed bridge-rendering correction; run/report that one-item job separately. Original receipts are retained. Generation takes seconds; seven CPU vision calls took the time recorded in the results, with a 180-second cap per call. The wrapper stops only the vision stack in `finally`; it does not start EC2 or alter the speech service.
