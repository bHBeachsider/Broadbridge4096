# Diagram repair: tested, not resolved

27 September 2026 (local date; raw UTC receipts cross into 28 September). **Neither tested change repaired the diagram connectivity errors.** Preserve the v2 extractor as the existing baseline, keep v3 experimental, and continue blocking these diagram proposals from training. No weights were changed.

## What ran

One local CPU Docker session per batch, using the already installed `qwen3-vl:4b-instruct-q4_K_M`, digest `sha256:ee4b975b58c17ce268cd19d40db35d5edc64603035d2ffc1fee1968eb0947f7b`. Same temperature 0.7, seed 42, top-p 0.8, top-k 20, presence penalty 1.5, 384 output-token cap and 180-second timeout. Six known synthetic development drawings; no client documents, cloud inference, downloads, EC2, training, database or production writes. The dedicated vision stack stopped after each batch; it has no published host port.

1. **Separate route/arrow prompts:** twelve requests, once each, two per original drawing. Route stage proposes endpoint pairs; arrow stage proposes literal `from_tag` / `to_tag`. The composer preserves unknown directions/uncertainty and rejects inconsistent stages. All six route stages returned empty connections; all six arrow stages returned empty arrows. All six composed graphs failed the independent checker.
2. **Enlarged crops:** after observing v3 failures, four more requests using the original v2 prompt/settings. Three failing drawings plus the passing forward-chain control; operator-selected crops removed captions/footer and enlarged the remaining pixels 2x with nearest-neighbor resampling. All tags and routes were visually checked as retained before inference. No redrawing, graph answers or old predictions entered prompts. All four failed the checker.

This consumed **16 requests**, with no retries or further prompt search: 689.948 seconds summed inference for v3 and 270.367 seconds for crops (about 16 minutes total, excluding preparation and Docker startup). There was no paid API usage; local CPU time is not free infrastructure. These fixtures are development data, not a held-out benchmark or engineering sign-off.

## Comparable results

| Variant | Drawings | Edges correct / extra / missing | Edge precision / recall | Known directions correct / reference | Unsupported direction claims |
|---|---:|---:|---:|---:|---:|
| Original v2, all qualified drawings | 6 | 14 / 2 / 0 | 87.5% / 100% | 6 / 8 | 2 |
| Separate-task v3, same six | 6 | 0 / 0 / 14 | undefined / 0% | 0 / 8 | 0 |
| Original v2, the four crop parents only | 4 | 9 / 2 / 0 | 81.8% / 100% | 3 / 5 | 2 |
| Enlarged v2 crops, same four | 4 | 9 / 2 / 0 | 81.8% / 100% | 1 / 5 | 2 |

Abstaining from every edge is not an improvement. Unknown reference directions are excluded from direction accuracy and tracked separately as unsupported claims. Enlarged-crop known-direction precision was 1/3; recall was 1/5. Do not compare the four-crop totals to the six-image baseline as if their populations matched.

| Cropped drawing | Remaining problem |
|---|---|
| Forward chain, previously passing control | Both explicit arrow directions became `unknown`; uncertainty set true. This regressed the control. |
| Reverse chain | Both edges correct, both explicit arrow directions still reversed. |
| Bridge crossing | Two real edges plus the same two false cross-connections. |
| Mixed junction | Three edges correct, the explicit direction correct, but two unarrowed segments still assigned unsupported directions. |

## Evidence and reporting fixes

All jobs, images, individual responses, settings, elapsed times and scores are in [the evidence directory](evidence/diagram-repair-2026-09-27). Job hashes: v3 `30ee71a5dc24fe4a020565b43bb8efa568be0488fc4314820121902ee0d2a922`; crops `c77ab77ca2d58abca7c122af576aec9b6c591a9129f3b40b00934bd9043b569c`. The original pilot evidence is unchanged. Reference graphs come from the construction model, never vision output.

Independent code review found two important reporting issues. Both now have reproducing tests that failed before the fixes:

- Future jobs pin the complete evaluation payload (including baseline) before inference. Editing a reference and its adjacent checksum can no longer change the score unnoticed. The first v3 job predates this protection: its original bytes and original report remain preserved. `report-verified.json` uses the explicitly recorded **retrospective** evaluation pin `85ec4facc03d2c6128f8ef1df6e45c49da5c6c81ad21ab659f318dd772c944c8`, also checks against canonical historical references/baseline artifacts, and discloses the weaker original binding. This does not retroactively prove a pre-run evaluation freeze.
- Crop reporting now checks the exact installed model digest before invoking the existing checker. A response from another model revision cannot silently score under this pin.

Deferred minor: the standalone crop-lineage sidecar is supplementary metadata, not an independently pinned authority. The job pins transformed images and references; reference `evidence_id` carries parent-image hash, rectangle and scale. Use those for integrity, not the sidecar alone. Pin the complete lineage sidecar in a future experiment format.

Software tests and their environments are recorded in [tests.json](evidence/diagram-repair-2026-09-27/tests.json). They prove validation/reporting behavior, not model reading accuracy. Experiments started from Broadbridge `00cfa12` and Foundry `6800c55` plus the experimental changes now presented in the successor drafts. No claim that the base commits alone reproduce the new profiles is intended.

## What can actually fix this

For native CAD/DEXPI input, take connectivity from the model. For raster-only input, next test a dedicated route tracer plus arrowhead detection against independent graphs; use the vision model for proposals and tag interpretation. Require new development families, then a separate held-out set before claiming improved accuracy. Human-signed tracing is the fallback for unresolved diagrams. This is the next experiment, not an already implemented solution.

Do not infer missing source facts: C01's four absent endpoints stay null, and flow stays unknown where the native source supplies no evidence. A qualified independent reviewer must resolve those from additional documents or tracing. Text/calculation preparation can continue meanwhile.

## Replay without a model call

From the Broadbridge checkout, set `$foundry` to the absolute successor Foundry checkout. These commands only rescore saved evidence and refuse overwrites:

```powershell
$root = 'docs/evidence/diagram-repair-2026-09-27'
python scripts/research/diagram_tracing_repair.py report --foundry $foundry --work "$root/v3" --results "$root/v3/results-qwen" --legacy-evaluation-sha256 85ec4facc03d2c6128f8ef1df6e45c49da5c6c81ad21ab659f318dd772c944c8 --report-name replay-local.json
python scripts/research/diagram_tracing_repair.py report-crops --foundry $foundry --work "$root/crops" --results "$root/crops/results-qwen" --report-name replay-local.json
```

No new inference is authorized or necessary to reproduce these scores. Keep ad-hoc replay outputs out of the committed evidence.

## Provenance disposition (28 September 2026)

This original experiment is explicitly `provenance: retrospective-checksum` and `gate_eligible: false`; it is excluded from all diagram-training gate decisions. See the [machine disposition](evidence/diagram-repair-2026-09-27/disposition.json). Original receipts remain unchanged. The [subsequent deterministic experiment](DETERMINISTIC_DIAGRAM_RESULTS.md) has a new pre-run input freeze and still grants no training approval. Crop-history metadata pinning remains required and deferred.
