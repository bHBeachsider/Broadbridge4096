# FQ-07: bounded helper comparison, version 2

28 September 2026. **Offline preparation complete; live comparison not authorized
or executed.** No winner, model quality result, training approval or expert score
is produced by this work. The main text/calculation work has its own branch,
`codex/helper-comparison-v2`, based on `codex/slm-preparation`; it does not depend
on the unfinished diagram-recovery branches.

## Purpose and correction to v1

Choose a dependable, economical helper for drafting evidence-grounded answers
that a qualified engineer reviews. Qwen3-8B on EC2 remains the adapter target;
the larger hosted helpers below are separate models, called through OpenRouter
only in a later authorized run. Mistral is not documented as installed on EC2.

[Public-v1](PUBLIC_DOCUMENT_EVALUATION.md) returned 30 Qwen answers but Mistral
exhausted its first response budget. It therefore cannot establish a balanced
cost/quality ranking. This revision uses one question per request and shorter
bounded output. It changes the protocol for **both** helpers. All v1 publications,
questions, references, source offsets, outputs and existing review scores remain
unchanged. Quotation-space failures remain failures; the new instruction asks
models to copy the existing excerpt exactly instead of weakening the checker.

## Paired stages and unchanged development status

The committed [protocol](../packs/oil-gas-public-intake/eval/public-v2/protocol.json)
pins the original sample file's SHA-256. Selection uses coverage, not model grades.

| Stage | Questions | Calls at most | Coverage | Proposed spend ceiling |
|---|---:|---:|---|---:|
| A: operational/quality screen | 10 | 20 | 2 per type; all 10 publications, 9 families | $0.10 |
| B: remaining calibration | 20 | 40 | Remaining 4 per type; only after A review and separate approval | $0.15 additional |

Stage A IDs: PUB-001, 004, 007, 011, 013, 018, 021, 024, 025, 030.
All 30 original questions appear exactly once across stages. Stage B is **not an
untouched holdout**: its families and original answers are already exposed.
Neither stage is Gate 0, S0-cases, S0-retrieval or a model-release benchmark.
All source families and derivatives stay `testing_only / dev`, excluded from
training. Use fresh independently sourced families for later confirmation.

Each pair gets identical system text, all frozen excerpts from its source, one
question and the same response schema. No reference-conditioned excerpt selection.
References, tolerances, hard-fail criteria and reviewer notes are stored separately
and excluded by an allowlist and runtime check. Request order and A/B assignment
alternate by question: five first requests per model in stage A. There are no
retries, best-of sampling, provider fallback, tools, browsing or adaptive prompts.

## Models and exact execution identity

| Arm | Historical candidate ID | Historical provider |
|---|---|---|
| Mistral | `mistralai/mistral-small-24b-instruct-2501` | DeepInfra |
| Qwen helper | `qwen/qwen3-30b-a3b-instruct-2507` | Nebius |

These are candidates recorded by the earlier trial, **not newly verified current
availability or price claims**. FQ-07 makes no catalogue calls. Jev is a separate
classification candidate; it cannot substitute for these answer-generation arms.

Before a live run, snapshot the current model card, licensing/terms and provider
endpoint/capability/pricing records, with retrieval time and hashes. Require the
same named endpoints for every slot, structured-output support, no collection,
zero retention and distillable-text routing. Resolve reasoning controls for both
arms before freezing requests; do not equate Ollama `think:false` with an
OpenRouter parameter. If equivalent non-reasoning behavior cannot be verified,
block this protocol and propose a separately named comparison.

Each live receipt must retain:

- Run, stage, source, family and question IDs; both repository commits; sample,
  protocol, prompt, schema, source/block and cloud-approval hashes.
- Requested and returned model IDs; requested and actual provider; endpoint
  snapshot hash; UTC start/end; finish reason; attempt number; HTTP/error class.
- Model weights/revision, provider revision, tokenizer/template/quantization
  identity **when disclosed**, otherwise null plus `provider_not_disclosed`.
  A dated model name is not an immutable weights hash. Record opaque-provider
  reproducibility as a limitation, never invent a revision.
- Temperature, output/context limits, reasoning behavior, input token preflight,
  reported input/output/reasoning/cached tokens, latency, raw response hash,
  known cost and whether billing remains unresolved. Never retain a key or DSN.

The offline packet has null returned identities/costs and `prepared_not_run` slots.
Those nulls must never be reported as successful calls or free model responses.

## Output, runtime and spending limits

Serial execution; one attempt per slot; temperature 0; 60-second request timeout;
1,000 completion tokens; answer <=100 words and <=1,000 characters; 1–2 exact
quotes <=240 characters; <=3 uncertainties <=160 characters each. The same limits
apply to both arms. Character/word checks supplement provider token limits; an
instruction is not enforcement. The local checker verifies shape, question ID,
length and exact source quotes. It does not establish engineering correctness.

Preparation rejects a serialized request description over 12,000 UTF-8 bytes;
it never truncates. **Bytes are not tokens.** The live preflight must count the
actual wire input including schema/template overhead for each endpoint and enforce
the assumed 8,192 input-token allowance. If exact tokenization/overhead cannot be
bounded, the following price calculation is not usable as a reservation: hold and
revise the budget proposal. FQ-07 does not download tokenizers or model weights.

The proposed price caps reuse the trial's $0.30/M input and $0.60/M output;
these are maximum acceptable rates, not a fresh price quote. At those caps:

`(8192 * 0.30 + 1000 * 0.60) / 1,000,000 = $0.0030576 per call`.

That is $0.061152 for A and $0.122304 for B, conditional on the token/rate
assumptions. Proposed ceilings are $0.10 and $0.15 ($0.25 combined), with room for
account/provider fees only after verifying them. Human review is separate. These
calculations are **not a server-enforced account budget** or an authorized spend.

A later runner must reserve the conservative cost of **both** calls before
starting a pair, reconcile actual receipts after each call, and refuse a pair
that could exceed its stage or combined remaining budget. Retain reservations
for unresolved billing; never assume a timeout/failed call cost zero. Configure
an appropriately scoped provider/key spend limit where supported before execution.
Any additional fee or reasoning charge must fit the approved reservation.

Stop both arms on a transport/output-limit/schema/citation/identity/unknown-cost
failure or budget exhaustion. Keep the failed slot and all not-run slots visible.
Do not finish only the working arm as v1 did. Do not retry or silently increase
limits. A revised prompt/settings/endpoint needs a new protocol and paired run;
preserve failed attempts and charge them to the experiment's total cost.

Worst-case API wait: 20 minutes for A, 40 more for B, before provider/account
preflight and bookkeeping. No latency prediction is implied. Initial technical
review estimate: 30–60 minutes for A; 60–120 additional for B, to be replaced with
recorded reviewer time. A run failure stops earlier.

## Review and decision

Use the existing per-type 0/1/2 rubric in `reviewer-only.json`. A matched hard-fail
criterion means **0 / critical YES**; other materially unsafe or fabricated claims
also require a critical flag. Record reviewer, date, evidence notes, reference
disputes and review seconds. Blank rows stay unreviewed. Missing answers do not
receive invented engineering grades: report operational availability separately.

Mask model identities from the review view until initial scoring is saved.
`requests.jsonl` discloses the mapping and is operator-only for this purpose.
This is practical masking, not cryptographic blinding; earlier public-v1 exposure
limits independence. Disputed references stay in a separate adjudication record.
If a material reference changes, version it and rescore both arms consistently;
do not repair a reference to favor one answer.

Proposed screen (requires Brad/technical-reviewer acceptance): complete paired
coverage and review, zero critical errors, mean >=1.8/2 overall and >=1.5/2 per
question type, no unresolved material reference dispute. Ten questions only test
workflow readiness; thirty remain small development evidence. They cannot certify
engineering competence or establish a universal optimum.

The subsequent report must show counts, per-type means, paired differences,
critical errors, not-run/failure coverage, mechanical flags, family-level results,
latency and complete/unknown billing. Compare quality on completed matched pairs
and explicitly report that denominator; never hide incomplete slots. Rank costs
only after quality eligibility, using total billed experiment cost per accepted
answer plus reviewer minutes. If billing is unknown or no answers are accepted,
cost-per-accepted is unavailable, not zero. Family-cluster uncertainty analysis and
a fresh independent sample precede model selection; stage A alone selects no winner.

## Reproduce the offline packet

Use this branch's checkout; the compiler uses the existing lightweight
`scripts/research/requirements-public-evaluation.txt` dependencies. It has no
`--live` option and never reads `.env`, imports a Foundry client or contacts a
provider. No model-generated answers are fabricated.

```powershell
$Domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$Python = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http\outputs\geometry-venv\Scripts\python.exe'
$Run = Join-Path $Domain ('tmp\helper-v2-' + (Get-Date -Format yyyyMMdd-HHmmss))
& $Python "$Domain\scripts\research\prepare_helper_comparison.py" --stage stage_a --out $Run
```

For a separate offline stage-B packet, use `--stage stage_b` and a fresh directory.
Existing output directories are refused. Outputs are `preparation.json`, frozen
`sample.json`, `protocol.json`, `prompt.md`, paired `requests.jsonl`,
`reviewer-only.json`, blank `scores.csv`, `README.md` and `checksums.json`.
Request descriptions are not direct API payloads. Do not feed this version into
the v1 live runner, its aggregator or the production public-v1 review URL.

## Execution adapter and remaining human steps

FQ-07 now includes the [bounded executor and paired score aggregator](HELPER_COMPARISON_EXECUTION.md),
with HTTP-mocked tests and offline rehearsals. The live code path is implemented
but has not been authorized or run. Capture UI integration remains separate.
Before live execution:

1. Brad and the appointed technical reviewer accept this protocol, reference
   applicability, quality thresholds and exact stage budget. Review source rights
   and route eligibility at that time; the historical manifest is not a live registry.
2. Refresh candidate/provider identity and capability records; obtain a bounded
   token/billing calculation. Proposed names do not confer current availability.
3. Use the executor's `plan` command to prepare exact wire requests and complete
   its approval worksheet with real provider/token/rights evidence and the exact
   two committed repository revisions. The incomplete template cannot authorize calls.
4. Allocate independent reviewer time for the hash-bound score CSV. The aggregator
   preserves missing responses, critical errors, disputes and partial-review holds;
   it neither changes public-v1 nor substitutes for engineering acceptance.
5. Only then authorize/run stage A. Review it before approving B. Fresh-family
   confirmation and training release are separate later decisions.

This preparation can proceed without Bill entering a case. Real scores and
engineering acceptance still require Bill or another appointed qualified reviewer.

## Offline verification, 28 September

The [verification receipt](verification/helper-comparison-v2-preparation.json)
records actual preparation hashes and counts. Both stages were rehearsed without
HTTP or credentials: 20/40 request descriptions, 20/40 blank review slots, 10/20
questions, ten sources and nine families per stage. Largest prepared request
descriptions were 5,982 and 5,962 bytes; tokens were not measured. Sixteen output
file hashes were verified across the two packets. No answers or grades were invented.

Existing evaluation/review-packet baseline: 26 passed. New FQ-07 tests: 13 passed.
Full branch suite (`python -m pytest -q -rs --tb=short` with the existing Foundry
path variables set): **375 passed, 103 skipped**. Database integration tests were
skipped because disposable database URLs were not configured; one existing
requests dependency-version warning remains. This branch begins before diagram
work, so its suite count is not the diagram branch's count. The v1 sample and
evaluator have no diff against base `96b6c22`.

Fresh read-only review identified one provenance defect: the copied protocol was
reserialized while its recorded hash described source bytes. A regression test
reproduced the mismatch; copying those bytes verbatim fixed it. Both packet
rehearsals and the full suite were rerun afterward. Review found no other
demonstrated P1/P2 issue; provider availability, live execution and engineering
acceptance were explicitly outside this offline software review.
