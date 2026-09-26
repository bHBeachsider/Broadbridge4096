# Public-document reviewer evaluation

This is the next helper-model screening step after the synthetic ingestion test.
It compares two open-weight text models on **10 public agency web publications,
30 fixed questions and 60 planned answer slots**. It does not approve a training batch.
Bill Hurt is the target technical reviewer; Brad can perform an initial screening.
No completed human scores are implied by generating this packet.

An offline [assistant pre-review](../output/openrouter-public-evaluation/public-v1-live/PRE_REVIEW_TRIAGE.md)
now covers all 30 returned answers and identifies review priorities. It is not
human scoring or technical acceptance, and it reveals model identities. Complete
an independent initial review before consulting it if maintaining the masked
comparison is important. All original answers and score rows remain unchanged.

## What to open

The observed run is in
[output/openrouter-public-evaluation/public-v1-live](../output/openrouter-public-evaluation/public-v1-live/REVIEW_INSTRUCTIONS.md).
Start with the reviewer instructions, then the ten `scorecard_*.md` files. Record
scores in `scores.csv`. `scores_summary.md` reports coverage and measured cost and
latency; it cannot report engineering accuracy until scores are supplied.

Observed run, 26 September: **11 calls, $0.0034673 total reported cost**. Qwen
returned 30 answers across all 10 documents; five documents passed every exact
citation check and five have quotation flags. Some flags arise from spaces
inserted around inline HTML markup; flags remain visible and have not been
relaxed into passes. Mistral exhausted 3,200 output tokens on its first document;
no complete answer was accepted and the remaining nine documents were explicitly
not run. No retry was made. Therefore the packet contains 30 Qwen answers and
30 Mistral failure/not-run slots, not 60 completed answers. Its measured latency
cannot support a balanced cost/quality ranking. All reviewer grades remain blank.

The diagnostic `citation_audit.json` records 11 non-exact quotations: seven match
after removing spaces before punctuation, four do not under that limited rule.
The latter include a dropped parenthetical, an added ellipsis and spacing within
octane abbreviations. These categories explain the strict check; they do not
prove or disprove engineering correctness. Original answers remain unchanged.

Review Qwen's actual answers first. The Mistral failure is an operational finding,
not proof that every unattempted engineering question would be answered wrongly.
Any subsequent shorter/bounded-output protocol must be a new version and run both
models again; retain this run as evidence rather than replacing it.

| Source group | Documents | Topics |
| --- | ---: | --- |
| EIA | 6 | Refining sequence, volume gain, LNG, gas transmission, HGL fractionation, octane |
| CSB | 4 | Chevron sulfidation, Tesoro HTHA, Williams blocked-in reboiler, Enterprise BAHX thermal fatigue |

There are six questions each for brief, missing_data, calculation,
grounded_explanation and abstention. The six calculations are explicitly
illustrative arithmetic/basis checks, not a validation of process simulation,
thermodynamic property models or plant design. Synthetic givens appear in the
question and are distinguished from the publication's factual claims.

## Source rights and boundaries

The source manifest contains original URLs, publication context, retrieval time,
raw/normalized hashes, exact excerpt hashes and character locations, source/family
IDs and source-specific reuse records. Its selected prose is authorized for this
public evaluation under the user's instruction and the agencies' published reuse
policies. EIA allows reuse of its information products with acknowledgment;
third-party photographs/material and its logos are excluded. CSB allows copying
its public information unless otherwise specified. See
[EIA reuse policy](https://www.eia.gov/about/copyrights_reuse.php) and
[CSB policy](https://www.csb.gov/privacy-policy/).

The Chevron input uses the CSB's own news summary; it does not reproduce the
linked Anamet report or its quoted conclusions. No source images, private
attachments, expert cases, emails or proprietary standards enter the requests.
CSB incident summaries describe knowledge after incidents; they must never be
substituted for Bill's decision-time case inputs. The dated HTHA alert is not
represented as a complete current code or a universal safe operating boundary.

Every source and question is **testing_only / dev**. The two EIA refining pages
share a family ID. Entire families remain excluded from training. These are
local evaluation records, not live source-registry updates. Any future training
release must separately enforce these holdouts, current source rights and exact
technical approval. No candidates or training JSONL are produced here.

This is an exploratory calibration set, not a locked final benchmark. Draft
references and hard-fail criteria were frozen before model calls but still need
technical review. Public material may already have appeared in model pretraining.
Do not tune prompts on these answers and then call the same sample unseen.
Reserve new source families for a subsequent locked comparison. This sample
does not count toward Gate 0's signed expert-case requirement.

## Fixed comparison protocol

| Role | Model ID | Allowed provider |
| --- | --- | --- |
| Lower-cost comparison | `mistralai/mistral-small-24b-instruct-2501` | DeepInfra |
| Provisional draft helper | `qwen/qwen3-30b-a3b-instruct-2507` | Nebius |

Both model cards declare Apache-2.0:
[Mistral](https://huggingface.co/mistralai/Mistral-Small-24B-Instruct-2501),
[Qwen](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507).
The comparison uses the existing Foundry OpenRouter transport and its
distillable-text/provider controls. Outputs here remain evaluation material,
not authorized training examples. The transport's `task="draft"` means generating
the answers for review; this script does not call the training-candidate builder
or bypass its `permitted_use=training` gate. Jev is a classification candidate,
not a generator of these engineering answers, so is outside this comparison.
Qwen3-8B remains the eventual training target, not the cloud model tested here.

Both models receive identical instructions, excerpts, fixed questions and JSON
Schema. Three questions from one document are batched into each call. References,
criteria, tolerances and reviewer scores are withheld by an explicit allowlist
and runtime leak assertion. Both use temperature 0, 3,200 output tokens,
24,000 input bytes and a 120-second timeout. Inputs are never silently truncated.
The instruction requests no more than 150 words per answer. Provider templates
and quantization remain provider-controlled; this does not prove equal local
Qwen3 serving templates or reproducibility of provider internals.

The runner alternates request order and A/B presentation by document. Model
identities/receipts are in `run.json` and `results.json`; reviewers should leave
those closed until scoring. This is a practical masked review, not cryptographic
blinding. It is one observation per model/document, without seed guarantees,
retries, fallback routing or cherry-picking the best attempt.

At most 20 calls are made. Routing requires the named provider, supported
parameters, no provider data collection, zero retention and rates no higher than
$0.30/M prompt and $0.60/M completion tokens. The run stops on a missing cost
receipt or after reported aggregate cost reaches $0.10. The cost stop occurs
after a response; it is not a prepaid server budget. A transport failure stops
that client; omitted jobs remain explicit. Costs exclude human review and any
unreported failed-call charge.

## Exact commands

Use the clean branch `codex/broadbridge-public-evaluation` and Foundry's helper
branch `codex/foundry-ingestion-openrouter` (PR #9, engine head `24de6af`). Install
the lightweight requirements only if missing. No database connection is needed.

```powershell
$Broadbridge = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-live-test'
$Foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http'
Set-Location $Broadbridge
python -m pip install -r scripts/research/requirements-public-evaluation.txt
python -m pytest scripts/research/test_public_document_evaluation.py -q

# Offline: ten packets, sixty blank score rows, no network or secrets.
python scripts/research/public_document_evaluation.py run --mode mock `
  --out "$Broadbridge\tmp\public-review-mock-NEW"

# Only after reviewing this exact public sample; the hash binds the transmitted set.
$SampleHash = python scripts/research/public_document_evaluation.py hash
python scripts/research/public_document_evaluation.py run --mode live `
  --foundry $Foundry --approve-sample-sha256 $SampleHash `
  --env-file 'C:\Users\bradu\Documents\Broadbridge4096\.env' `
  --out "$Broadbridge\output\openrouter-public-evaluation\public-review-NEW"

# After the reviewer completes scores.csv. No model or database call occurs.
python scripts/research/public_document_evaluation.py summarize `
  --run "$Broadbridge\output\openrouter-public-evaluation\public-review-NEW"
```

`--env-file` reads only `OPENROUTER_API_KEY` for explicit live mode. It never writes
`.env`, prints credentials, loads a Neon connection or falls back to direct
OpenAI. The source path/model set are fixed; the runner does not accept arbitrary
uploads. A Foundry public-pack/ancestor-policy check remains mandatory for live
calls. Exact call settings and sample snapshots are saved with each run.

To verify the original acquisition, use the ignored local cache:

```powershell
python scripts/research/verify_public_sources.py `
  --cache 'C:\Users\bradu\Documents\Broadbridge4096\tmp\public-evaluation-acquisition' `
  --report "$Broadbridge\tmp\source-check-NEW.json"
```

A second operator can use `--fetch` with a new cache to download the ten URLs.
Agency navigation/date content can change raw hashes; the tool reports drift
instead of overwriting this frozen sample. Exact excerpts and original offsets
can be checked separately. Do not silently substitute new source content.

## Review and next decision

Validation at this revision: 24 new public-evaluation tests plus the existing
helper rehearsal test = **25 passed**, including actual Foundry transport with
mocked HTTP. The tests cover identical paired inputs, reference leakage,
rights/identity/hash rejection, exact quotes, output-limit retention, unknown-cost
stop, missing-answer grades and unreviewed score aggregation. All ten original
HTML snapshots matched their raw/normalized hashes, excerpts and source offsets.
An existing requests dependency warning remains; no network was used by tests.

Allow roughly 1–3 minutes per model answer plus source/reference review: about
2–3 hours of technical review, split into sessions if useful. Automated runtime
depends on provider latency; use the measured run receipts rather than a GPU
estimate. Start with calculations, pressure-basis traps and the incident cases,
then finish all rows. Reviewer quality is not inferred from structural tests.

In scores.csv, each completed row needs a 0/1/2 score, YES/NO critical flag,
reviewer, date and evidence notes. A matched hard-fail criterion requires 0/YES.
Blank scores remain unreviewed. The aggregator reports per-type means, observed
critical errors, response coverage and documents fully reviewed; partial scores
cannot pass. Review disputed references before interpreting comparative means.

Proposed next acceptance rule for Brad/Bill to confirm: complete coverage,
zero critical errors, at least 1.8/2 overall and at least 1.5/2 in every question
type, followed by a fresh locked sample. Until agreed and met, selection stays
provisional. Then compare measured inference cost per technically acceptable
answer plus review time. Do not select a cheaper model that fails the quality
bar. A subsequent training-batch proposal still requires source rights, family
holdouts and human approval; this tool always emits `training_approved: false`.

No EC2, model weights, training, S0-retrieval construction, R2/Neon write,
Vercel deploy, production change or email is part of this step. HTML text is
tested here; PDF layout, OCR, tables, images and audio need their own later
format-specific evaluation and are not validated by these results.

## Follow-on synthetic-data work

The [synthetic expert workflow](SYNTHETIC_EXPERT_WORKFLOW.md) is now a named
subproject. Bill first confirms the failure categories through the original
review; an assistant concern is not a confirmed error. Those categories can
guide new recipes and independently sourced training families. This entire
public-v1 sample, its answers and derivatives remain testing_only/dev, excluded
from training. The sample is development calibration, not an unseen release test.

The [expert worksheet](templates/SYNTHETIC_EXPERT_REVIEW.md) records recipe
assumptions, variation limits and candidate acceptance. It does not replace
scores.csv or add human scores to this run. The proposed 100-candidate pilot and
its offline implementation are tracked in the [subproject plan](superpowers/plans/2026-09-26-synthetic-expert-data.md).
Current human-review status, source/model results and training gates are unchanged.
