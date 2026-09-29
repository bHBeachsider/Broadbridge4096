# SLM preparation and fine-tuning work queue

Updated 29 September 2026. Owner: Brad / Broadbridge Oil & Gas.

This is the ordered work backlog requested while the discovery questionnaire is being developed. It does not submit training jobs or start a background scheduler. Execute one implementation lane; keep GPU, live generation and production gates explicit. The editable [queue CSV](SLM_WORK_QUEUE.csv) is the task register; update both views together.

## What can proceed without waiting for Bill

FQ-01 through FQ-06 prepare software, extraction evidence and reviewable inputs offline. FQ-07 is deferred; offline FQ-12/FQ-13 readiness is the current focus. They do not require Bill to enter a case. Another appropriately qualified reviewer may later accept engineering content within their competence. Bill's technical decisions are not supplied by an assistant or by passing software tests.

**FQ-01 and FQ-02 are now prepared for review:** the calculation-verifier rehearsal and a three-page DOE pressure packet. See the [commands, results and remaining decisions](SLM_PREPARATION_REHEARSAL.md). DOE section choice is a provisional engineering-preparation choice, not a decision about the final commercial curriculum.

**FQ-03, FQ-04 and FQ-06 are also prepared:** [source shortlist, math quality findings and mock release/CPU audit](SLM_DATA_PREPARATION_RESULTS.md). They confer no training acceptance. In particular, the math sample remains on quality hold and live synthetic-review/release integration remains open.

## Ordered register

| ID | Work package | State | Deliverable / completion evidence |
| --- | --- | --- | --- |
| FQ-01 | Calculation verifier rehearsal (SD-04) | PREPARED_WAIT_REVIEW | Decimal checker, five-vector admission rehearsal and release rejection verified; engineering method/tolerance acceptance remains pending |
| FQ-02 | Extract the acquired DOE handbook pilot section | PREPARED_WAIT_REVIEW | PDF 35-37 with images, two text views, glyphs, equation/conversion proposals, nine exceptions and blank review packet; no QA release |
| FQ-03 | Prepare new engineering source families | PREPARED_WAIT_REVIEW | Five exact DOE documents/four provisional families; rights/technical holds; frozen public-v1 families excluded |
| FQ-04 | Audit the existing Hugging Face math sample | PREPARED_WAIT_REVIEW | 1,200 rows audited; three exact groups/four template groups; ten spot-checks expose three quality problems; quality hold |
| FQ-05 | Test extraction and normalization coverage | IN_PROGRESS | [Reference pilot](REFERENCE_GRAPH_RESULTS.md): 14 correct edges plus two false connections, two reversed arrows and two unsupported directions. [Remediation](DIAGRAM_CONNECTIVITY_REMEDIATION.md); visual training admission remains blocked. |
| FQ-06 | Rehearse release rejection and CPU training audit (SD-06 preparation) | PREPARED_WAIT_REVIEW | Eight mock acceptance/release refusals, hash-keyed fixture verified and pinned CPU mask/length audit; live review wiring remains open |
| FQ-07 | Optional helper comparison | DEFERRED_OPTIONAL | Prepared in [Broadbridge draft #24](https://github.com/bHBeachsider/Broadbridge4096/pull/24) and [Foundry draft #20](https://github.com/bHBeachsider/slm-foundry/pull/20); provider/terms questions are not AWS-training prerequisites |
| FQ-08 | Confirm priority tasks, references and recipes (SD-01) | WAIT_REVIEW | Named decisions on first tasks, exclusions, recipe versions, hard-fail criteria and reviewer competence |
| FQ-09 | Run and score S0-cases | WAIT_CASES_AND_RUN | Stock qwen3:8b briefs plus human scorecards/aggregate; Gate 0 coverage recorded separately |
| FQ-10 | Build and compare S0-retrieval | WAIT_SCORED_BASELINE | On-box index and comparable scored briefs; beat S0-cases before training is considered |
| FQ-11 | Run the bounded synthetic candidate pilot (SD-05) | WAIT_REVIEW_AND_RUN | Up to 100 pending candidates, proposed 20/type and <=10/family; independent dispositions for every attempt |
| FQ-12 | Freeze the reviewed dataset (SD-06) | WAIT_ACCEPTED_DATA | Immutable messages JSONL release/hash; lineage, family splits, assistant-target token audit and exclusions |
| FQ-13 | Host readiness and bounded QLoRA smoke test | RUNTIME_BLOCKED_CAPACITY | At 16:47 UTC both approved existing hosts rejected one CLI start call each for capacity (six service requests from implicit retries); both stopped, unchanged boots. Replacement prerequisites and partial upload retained. All 18 offline selection/resume checks passed. [Session evidence](AWS_RUNTIME_RELOCATION_2026-09-29.md); [fallback assessment and Basic Support limitation](AWS_GPU_CAPACITY_OPTIONS_2026-09-29.md); resume/install/GPU checks, weights, release and smoke remain open |
| FQ-14 | Train and compare the first domain adapter (SD-07) | WAIT_SMOKE_RESULT | Base/retrieval/adapter comparison: per-type scores, critical errors, grounding, abstention, latency and regressions |
| FQ-15 | Reproduce and release the accepted adapter | WAIT_ACCEPTANCE | Second-operator reproduction; hash-keyed deploy_pack.sh GGUF release and rollback record |
| FQ-16 | Specialist expansion and advanced training | POST_V0 | Separate proposals for specialist families, simulator examples, preference data/RL and native vision/audio |

State meanings: **RUNTIME_BLOCKED_TRANSFER** = host prerequisites passed, runtime upload incomplete and candidate not installed/tested; no automatic retry; **DEFERRED_OPTIONAL** = parked and not a prerequisite for the main SLM; **RUNTIME_BLOCKED_PREFLIGHT** = runtime bundle verified, host started but preflight failed before installation/GPU checks, retries paused; **RUNTIME_BLOCKED_CAPACITY** = runtime setup approved and download verified, existing-host capacity prevents completing installation/GPU checks; **PREPARED_WAIT_GPU_GATE** = offline preparation delivered, live prerequisites unresolved; **READY_OFFLINE** = queued preparation can proceed without a live model; **PREPARED_WAIT_REVIEW** = software/extraction deliverable exists but the applicable human decisions remain open; **WAIT_…** = the named input/decision is outstanding; **POST_V0** = outside the initial adapter release. Ready is not running or complete. Conditional work may be prepared out of row order when its recorded dependencies are satisfied; numbering is dispatch priority, not a mandatory finish-to-start schedule.

The intended first real synthetic pilot includes all five question types; calculation examples also depend on independent acceptance of FQ-01's method. A non-calculation pilot may proceed with recorded missing coverage rather than invented numerical verification. FQ-12 describes the synthetic-inclusive release; an independently approved expert-only release may be prepared for the later matched comparison without pretending the synthetic pilot ran.

## Existing work to reuse

- **SD-02 and SD-03 already exist for offline rehearsal:** pending review packets, bounded author/challenger orchestration and fabricated examples. Reuse the [batch runbook](SYNTHETIC_BATCH_RUNBOOK.md); do not rebuild them. Local code was inspected at Broadbridge `fed3482` and Foundry `f1790df`; both remain in draft delivery branches.
- **Public-v1 has already run as helper evaluation:** ten agency publications, thirty questions, thirty returned Qwen answers and thirty Mistral unavailable/not-run slots. This is not the Qwen3-8B S0 baseline. The [evaluation record](PUBLIC_DOCUMENT_EVALUATION.md) describes its limitations; technical score status must be read from the review workflow before any new decision.
- **Case batching and score aggregation already exist:** use the [first-case runbook](FIRST_CASE_RUNBOOK.md). The queue does not schedule another implementation of those tools.
- **Source leads already exist:** the existing local research inventory (`docs/expert-outreach/DATASET_REVIEW_INVENTORY.md` on `codex/commercial-partner-strategy` at `cd421de`) distinguishes acquired originals, unreviewed samples and licensing leads. Recheck terms/credits at admission; a listed source is not cleared by this queue. The research branch is local; no published link is implied.
- **Questionnaire and brainstorm design:** [draft PR #14](https://github.com/bHBeachsider/Broadbridge4096/pull/14) is a separate development track. Its `/discovery` route is not live at this queue revision. Case Capture A8 and the existing review page remain the available input paths.

The DOE original was checked locally on this date: `packs/oil-gas/data/public-start-2026-09-24/raw/doe/DOE-HDBK-1012-92_VOL1.pdf`, 1,910,060 bytes, SHA-256 `3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9`. It remains in the primary checkout's ignored data directory; it is not added to Git here. The prior public-start intake receipt also exists. The inventory's OpenMath counts are prior receipt findings, not a new answer-quality or license audit.

## Source allocation

| Input family | Queue treatment | Intended use |
| --- | --- | --- |
| Acquired DOE fundamentals; selected steam/process-heating/pumping documents | Exact page/credit/rights review, extraction and source-family assignment | Candidate engineering explanations, evidence requests and reviewed calculation examples |
| Existing EIA/CSB public-v1 families, related versions and derivatives | Preserve testing-only/dev status | Helper calibration and failure categories; never training examples |
| New incident/report families | Assign family and intended split before question generation | Historical evidence exercises; distinguish after-event findings from information known at decision time |
| Existing OpenMathInstruct-2 sample | Audit separately with provenance and attribution | General-math pipeline/control experiment; not evidence of refining expertise |
| Bill/Norm cases, archives and recordings | Wait for actual contribution, rights and appropriate review | Candidate specialist knowledge; possession/public availability does not establish training permission |
| Questionnaire answers and brainstorming | Interpret, confirm and triage first | Task priorities, new issues and source nominations; no automatic training admission |
| Drawings, images, audio and CAD | Preserve originals; evaluate extraction separately | Human-checked text/evidence for current Qwen; native multimodal training remains a later model project |

## Before a queued item becomes a model run

Record the exact two repository commits, admitted source revisions/hashes and family history, recipe/prompt/rubric versions, permitted processing route, model/tokenizer revision, inference or training configuration, run/cost/time caps, output location and accepting reviewer. A run receipt records failures and actual costs as well as successes.

For private material use the tested approved local route. If unavailable, retain the item; do not silently send it to OpenRouter. For a separately authorized public helper comparison, use the established OpenRouter selection process and refresh model/provider availability before spending. This queue makes no new claim about present pricing, model availability or current source licenses.

S0-cases can run per signed case while Gate 0 coverage accumulates. Gate 0 itself still requires recorded rights/storage, a named reviewer and at least thirty case-derived questions covering brief, missing_data, calculation, grounded_explanation and abstention. S0-retrieval follows the first scored briefs and roughly twenty admitted documents, and must improve on S0-cases before training is considered.

For later adapter comparison, do not compare stock Ollama's default template with a different fine-tuned template and call that an adapter effect. Re-run the base under the same pinned template/think/quantization/context settings used for the adapter; preserve the original S0 results separately. This is a new comparison configuration, not permission to rewrite the historical baseline.

## Next dispatch and human inputs

1. Review the FQ-01 method/tolerance and FQ-02 evidence packet. No training approval is implied by their software checks.
2. Review FQ-03's rights/credits and technical task selection; adjudicate FQ-04's family/answer quality findings. Original samples and splits remain unchanged.
3. Next dispatch: [FQ-12/FQ-13 AWS and dataset readiness](AWS_TRAINING_READINESS.md). Both existing hosts were capacity-blocked on the 16:47 UTC retry and remain stopped. Preserve the replacement prerequisites and partial upload; reuse prefix-verified resume in a later approved bounded session. Complete runtime installation/checks separately from data acceptance. Accept the narrow DOE/calculation packet and freeze a real release. The prior database count check reached dev only; production case status remains unverified. FQ-07 stays deferred; diagram recovery remains separate.
4. Bill or another appointed reviewer chooses useful tasks and verifies the real source/method/candidate packets. Brad records rights, live processing budgets and release decisions independently.

Original work packages and acceptance criteria remain in the [synthetic-data plan](superpowers/plans/2026-09-26-synthetic-expert-data.md), [expert workflow](SYNTHETIC_EXPERT_WORKFLOW.md) and [ingestion release runbook](INGESTION_PIPELINE_RUNBOOK.md). This queue organizes them; it does not mark unperformed work accepted.
