# Focused vision extraction and connectivity checks

27 September 2026. Development experiment; engineering acceptance and training
permission remain pending. [Runbook](VISION_V2_RUNBOOK.md) ·
[protocol](VISION_CONNECTIVITY_PLAN.md) · [v1 results](LOCAL_VISION_RESULTS.md).

## What changed

The large combined extraction prompt is split into label reading, direct-edge
tracing and pressure transcription. Each has a small JSON schema and token
limit. Granite receives two legible formula crops with its formula-to-LaTeX
instruction. The four synthetic images are byte-identical to v1. Crop receipts
retain page-image hashes, pixel coordinates and derived image hashes.

Qwen uses the publisher's visual sampling recommendations, with explicitly
smaller local context/output budgets. The protocol changes prompts, schema,
sampling and (for Granite) image framing together. It cannot isolate which
change caused an improvement, and this development set was chosen from v1
failures. It is not a held-out test of refinery engineering competence.

## Connectivity result

The crossing figure's eight labels were all read correctly. Its topology was
still wrong: the model proposed seven direct edges, of which four were
unsupported, and omitted two of the five expected edges. The independently
frozen graph check rejected it.

Missing: A-101–B-101 and G-201–J-201. Unsupported: A-101–C-101,
B-101–C-101, E-201–G-201 and F-201–G-201. The model also marked the response
uncertain. Neither valid JSON nor correct labels establishes correct topology.

The simple P-301–V-301 line and its unknown direction match the reference;
Qwen's uncertainty flag still keeps the result in review. All three label
tasks match their expected tags/counts, including abstention on the obscured
tag. The focused pressure transcription preserves both 80 psig and 80 psia.

The two unconnected pressure records also failed connectivity validation: Qwen
invented four directed relationships between document headings, the instrument
tag and pressure text. It reported no uncertainty. The independent graph has
zero edges, and those text headings are not equipment/junction nodes. The
checker rejects the endpoints before any edge can be considered acceptable.

## Complete run

All nine requests completed within their bounds, once each, with no timeout or
truncation. This is operational completion, not nine correct answers.

| Task | Seconds | Separate check |
| --- | ---: | --- |
| Crossing labels | 71.915 | Pass: all eight tags |
| Crossing connections | 96.041 | Fail: four unsupported edges, two missing |
| Obscured-tag labels | 63.068 | Pass: two readable tags, one unreadable |
| Simple-line labels | 59.312 | Pass: both tags |
| Simple-line connection | 60.700 | Needs review: matching edge but uncertainty flagged |
| Conflicting pressure transcription | 58.204 | Pass: both pressure bases retained |
| Conflicting pressure connectivity | 73.986 | Fail: invented directed relationships with non-node text |
| DOE rho formula crop | 12.546 | Needs review: rho recovered, raw formatting remains |
| DOE exponent crop | 12.927 | Needs review: superscript recovered, raw formatting remains |

Four fixture checks pass, two fail, three require review. None is approved for
training. Request time totals 508.699 seconds (8 minutes 29 seconds); this
excludes orchestration overhead. Qwen mean is 69.032 seconds. Peak vision
container memory including filesystem cache was 8.416 GiB, under the 10 GiB
cap; this is not GPU memory or model working-set size.

Both Granite crops visibly preserve the target symbol: `\rho H` and
`10^{3}` (with spaces in the raw LaTeX). V1's whole-page conversion substituted
Latin p for rho and flattened the exponent. V2 still returns location tags and
spaced word letters in an array, so it is not a clean normalized equation or a
verified physical calculation. These are assistant observations against the
source crops; qualified engineering acceptance is still pending.

The [machine receipt](verification/local-vision-v2.json) records hashes, model
pins, settings and all nine outcomes. Raw outputs and crop provenance remain
in the ignored `packs/oil-gas/outputs/vision-v2-2026-09-27/` directory. V1 is
preserved. The vision container exited normally; the existing voice interviewer
remained healthy. No model weights, source images or raw datasets are committed.

## Admission boundary

The checker compares direct edges with a separate reference; it does not trace
pixels. For real PFD/P&ID work, use a source-bound CAD topology export or an
independent qualified trace. A missing reference, missing reviewer for a real
reference, uncertainty, changed source hash or incomplete response cannot pass.
Synthetic reference metadata is not a credential that a model may issue.

All proposals and check receipts remain `training_approved:false`. The existing
training-example contract rejects them, and there is no automatic visual
normalization/export route in this pilot. An accepted future route must bind
the checked/corrected topology to the exact candidate, preserve image ancestry,
and still pass source rights, technical review and family/release gates.

Keep the crossing failure as a development regression example, not a gold
training answer. Next diagram work should test reviewed CAD topology or a
specialist symbol/line tracer against new fixtures before increasing scale.

## Software verification

Foundry: 215 offline tests passed across local vision, connectivity, assist,
synthetic review/batches, curation and datasets; 38 new profile/checker tests.
One pre-existing requests dependency warning remains. Broadbridge: 375 passed,
113 skipped in the combined packs and research suite; 11 new v2 protocol tests.
The skips are not passes or evidence of live integration coverage.

Foundry implementation: draft [PR #13](https://github.com/bHBeachsider/slm-foundry/pull/13),
commit `41c17801618d22b736eec8d1a7bf3dd427756189`, stacked on #12. No EC2,
training, paid inference or production deployment is part of this experiment.
All three Foundry CI jobs (Python, container, Cloudflare) also passed on that
commit.
