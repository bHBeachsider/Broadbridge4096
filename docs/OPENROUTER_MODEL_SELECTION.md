# OpenRouter model selection and Jev exploration

25 September 2026. Research results, not a production model approval.

Brad's decision: use OpenRouter to compare cost and capability for supporting
ingestion tasks; do not select OpenAI merely because an API key is configured.
The Qwen3-8B fine-tuning target and existing confidentiality restrictions remain.

Implementation follow-up: [public/synthetic helper runbook](OPENROUTER_INTAKE_RUNBOOK.md).
The later drafting smoke found a critical pressure-basis error in Mistral despite
valid JSON and source quotations. Qwen3-30B-A3B-Instruct-2507 preserved the stated
values/basis on that same synthetic source and is the provisional drafting
candidate. This does not revise the earlier classification scores or establish
a production optimum. All examples remain pending review.

## Jev is available and was called successfully

The live catalogue lists `typesafe/jev-1.13`, resolving in our response to
`typesafe/jev-1.13-20260917`, and the moving alias `~typesafe/jev-latest`.
Use the pinned model for comparisons. The default text-output catalogue query
omitted the decision model; querying with `output_modalities=all` returned it.

Jev accepts text state and typed questions. It returns a choice among supplied
options, an ordered score, or a yes/no probability. It cannot generate a report,
extract arbitrary prose fields, perform OCR, or directly read audio/images. Its
32,000-token advertised context and current $0.042/million input-token price
($0 output) were verified against the public catalogue and
[OpenRouter model page](https://openrouter.ai/typesafe/jev-1.13). The API is
`POST https://openrouter.ai/api/alpha/decisions`, rather than chat completions.
See [TypeSafe's model description](https://docs.typesafe.ai/concepts/system-one).

One synthetic refinery classification succeeded: 425 input tokens, reported cost
$0.00001785, 0.707 seconds wall time, correct downstream label. This demonstrates
access through Brad's OpenRouter key, not engineering competence.

The catalogue also lists **`typesafe/jev-router`**, a distinct router described
as selecting a model and reasoning effort according to quality, speed and cost.
It advertises multimodal routing, while the Jev decision model itself is text-only.
Its price fields were `-1`, its endpoint list was empty, and a detailed router
documentation page could not be verified. These are incomplete catalogue
signals, not a negative/free price or proof of failure. We did not invoke that
router or approve it for production. Verify supported controls, selected-model
receipts, privacy behavior, and enforceable price limits before evaluating it.
Saved [catalogue snapshot](../output/openrouter-research/openrouter-jev-catalog-all.json)
and [router endpoint response](../output/openrouter-research/openrouter-jev_router_endpoints.json).

## Measured comparison

Eight embedded synthetic texts covered email, a measurement table, a report with
missing pressure units, extracted drawing labels, a transcript, an instruction
attack, unrelated content, and an unspecified pump application. Each had three
predeclared labels: document type, industry practice, and review flag. Reference
labels were set before calls and were not changed after seeing results.

| OpenRouter model | Valid responses | Correct fields | Entire records correct | Median wall time | Observed cost per 1,000 similar calls |
|---|---:|---:|---:|---:|---:|
| Jev 1.13 | 8/8 | 21/24 | 5/8 | 0.206 s | $0.0328 |
| Qwen3.5 Flash 02-23 | 8/8 | 23/24 | 7/8 | 0.762 s | $0.0301 |
| Mistral Small 24B Instruct 2501 | 8/8 | 22/24 | 6/8 | 0.733 s | $0.0184 |

Cost is the sum of returned usage receipts, divided by eight and scaled to
1,000; it is not a document-processing quote. Long inputs, retry traffic, OCR,
multiple passes and human review change economics. These successful comparison
calls reported $0.000651158 combined, plus the separate Jev access smoke above.
No proprietary material, Gate 0 cases, cloud files or training candidates were
sent. No model weights or EC2 instance were used.

Jev classified document type and practice correctly in all eight examples, but
falsely flagged three harmless inputs as instruction attempts. Both generative
models returned `unknown` for the practice in the adversarial refinery email
instead of the expected downstream label; they did identify the instruction
attempt. Mistral additionally flagged a normal request for review as an attack.
Jev's probabilities do not establish calibration on petrochemical documents.

Qwen initially returned HTTP 400: its Alibaba endpoint required the word JSON in
the messages even though JSON Schema output was requested. Added an explicit
JSON instruction and reran only Qwen's eight records. The failed attempt remains
in the evidence and is not scored as eight wrong model answers. This makes the
comparison exploratory rather than a tightly controlled benchmark. The same
source texts, expected labels and label definitions were retained. A fresh
comparison can use the corrected script for all models.
The [sanitized diagnostic](../output/openrouter-research/openrouter-qwen-format-diagnostic.json)
retains the observed provider error; request identifiers and credentials are omitted.

All successful outputs passed local key/enum validation. That does not prove
provider-side strict-schema enforcement: the Qwen error referenced JSON-object
mode. Keep local schema validation even when a provider advertises structured
outputs. [OpenRouter structured-output guidance](https://openrouter.ai/docs/guides/features/structured-outputs)
recommends explicit schemas and `require_parameters`; the test used both.

Evidence: [initial comparison](../output/openrouter-research/openrouter-intake-benchmark.json),
[corrected Qwen run](../output/openrouter-research/openrouter-intake-qwen-corrected.json),
[Jev access smoke](../output/openrouter-research/openrouter-jev-smoke.json).

## Recommendation by task

| Task | Trial candidate | Acceptance needed |
|---|---|---|
| Classify extracted text and suggest an industry practice | Jev, compared with Mistral/Qwen | Larger unseen labeled sample, unknown handling, error rates by class and measured review burden |
| Extract arbitrary fields, summarize, draft questions | Qwen Flash provisional candidate | Evidence spans, exact values/units/basis, schema validity and no unsupported claims; not measured by this classification test |
| Low-cost text classification baseline | Mistral Small | Confirm robustness and the cost of wrong labels/review referrals |
| Scan, diagram or audio interpretation | Separate local OCR/ASR or admitted multimodal model | Format-specific transcription/diagram benchmarks; Jev consumes the resulting text |
| Rights, family splits, sign-off and training admission | Existing deterministic code and named humans | Never inferred from source text or a model confidence score |
| Engineering acceptance | Bill Hurt / appointed technical reviewer and engineering metrics | Jev can suggest review priority, not certify calculations or safe operation |

No global optimum is established. Jev was fastest, Mistral cheapest, and Qwen
most accurate on this tiny combined-label test. The inference-price differences
are fractions of a cent at this scale; review errors can cost far more. Jev is
worth an optional classification experiment, not an automatic acceptance gate.

## Selection process before integration

1. Build an unseen, reviewer-labeled sample spanning intended file types and
   practices. Separate calibration examples from a locked evaluation set.
2. Enforce cloud eligibility in code before any call. Confidential packs retain
   the current local-only handling. Jev/OpenRouter routing must not bypass it.
   Classification outputs from this study are research records, not training data.
3. Run the same tasks and schemas against pinned model IDs. Record returned model,
   provider, prompt version, token counts, latency, retries and cost. For generation,
   retain source IDs and evidence spans and score numeric/unit preservation.
4. Reject candidates with critical errors or ungrounded extraction. Among those
   meeting quality thresholds, choose the lowest measured total cost per accepted
   item, including review and retries. Evaluate latency separately for interactive
   work and batch work. Do not adopt a confidence cutoff from vendor examples.
5. If automatic routing is later used, restrict eligible models/providers,
   require needed parameters, enforce price limits and retain selected-model
   receipts. Missing configuration or unmet requirements must fail clearly;
   there is no implicit fallback to the direct OpenAI endpoint.
6. Implement any generic provider support in slm-foundry with offline HTTP tests;
   keep Broadbridge taxonomy, prompts, eligibility and evaluation data in this repo.
   Deploy through a draft PR after review. No runtime provider was switched here.

## Reproduction

The script can transmit only its embedded synthetic examples. It requires
`--live`, an explicitly available OpenRouter key, and a new output path; it does
not accept arbitrary documents. Dependencies are requests and python-dotenv.

```powershell
python scripts/research/benchmark_openrouter_intake.py --live `
  --env-file "C:\Users\bradu\Documents\Broadbridge4096\.env" `
  --output output/openrouter-research/benchmark-new-run.json
```

The script has no retries, bounds request time/output length and stops further
requests after reported cost exceeds $0.02. Generative provider prices are capped
at $0.30/M input and $0.60/M output. This is a local stop control, not a
server-enforced cumulative account budget; missing/failed-call costs cannot be
assumed zero. Configure account-level limits before larger experiments.
