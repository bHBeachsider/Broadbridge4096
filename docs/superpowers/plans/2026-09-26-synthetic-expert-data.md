# Expert-guided Synthetic Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Use one implementation lane. Steps use checkbox (`- [ ]`) syntax for tracking. This plan does not authorize subagent dispatch.

**Goal:** Add expert-guided synthetic examples to the reviewed-data workflow, with independently checked evidence and measurable benefit to Qwen3-8B.

**Architecture:** Reuse Foundry extraction, public helper transport, curation and immutable releases. Generic orchestration belongs in slm-foundry; engineering recipes, prompts, rubrics and private records belong in Broadbridge4096. Human case contracts and release authorities stay unchanged.

**Tech Stack:** Existing Python, JSON Schema, pytest, ingestion contracts and OpenRouter transport for explicitly approved public inputs. Existing case/candidate review and QLoRA paths apply after their gates pass. No new hosted service is needed.

**Spec:** [Expert-guided synthetic training data](../../SYNTHETIC_EXPERT_WORKFLOW.md).

## Global constraints

- Every PR stays draft. Brad controls readiness and squash merging; no direct main/master changes.
- No EC2, training, production write or automatic live model call is authorized by this plan.
- Bill Hurt is the appointed technical reviewer. Norman Lieberman remains a potential specialist contributor, not an agreed participant.
- Independent reviewers do not certify their own authored material.
- Preserve `broadbridge.case_record/1` and `foundry.training_example/1`; provenance uses a separate envelope.
- Whole-family split closure applies before generation, including historical and excluded members. Public-v1 remains testing_only/dev.
- Confidential inputs require existing local-only policy; no external fallback or pack relabeling.
- Preserve the existing numerical-claim guard. New computed values need a separately reviewed calculation artifact.
- Completed expert records, private manifests and credentials stay out of public Git.
- Upload, generation, review, dataset release, compute authorization and model promotion remain separate actions.

## Review focus

| Condition | Required behavior | Task |
| --- | --- | --- |
| Rights change or a family acquires a stricter historical split after drafting | Recheck current state at registration/release; receipts cannot grant admission | SD-02, SD-06 |
| An author signs their own correction, or an answer changes after review | Pending/new hash; independent review required | SD-02, SD-05 |
| A quoted number changes units/basis or physical meaning in the answer | Exact quotation success is insufficient; identify the mismatch | SD-03, SD-04 |
| Provider failure, missing cost receipt or incomplete JSON | Stop affected run, retain failed attempt, no silent retry | SD-03 |
| Hindsight/reference leakage or paraphrased holdout evidence | Reject before a call; preserve family identity | SD-02, SD-03 |

## Dependency schedule

Effort ranges are planning assumptions, not dates or approvals. Human availability
and source admission determine elapsed time. No stage bypasses original Gate 0.

| ID | Deliverable | Depends on | Owner | Planning effort | State |
| --- | --- | --- | --- | --- | --- |
| SD-00 | Workflow, expert worksheet and project links | Brad's direction | Implementation controller | This update | Prepared |
| SD-01 | Confirmed development failures and initial recipes | Human public review | Bill; Brad for rights/scope | 1-2 review sessions | Awaiting review |
| SD-02 | Offline review-packet and holdout rehearsal | SD-00; fabricated fixtures permit preparation alongside SD-01 | Foundry implementation | 1-2 engineering days | Planned |
| SD-03 | Bounded author/challenger orchestration | SD-02; SD-01 before real generation | Foundry implementation, domain binding | 1-2 engineering days | Planned |
| SD-04 | Independently checked calculation templates | SD-01, SD-02 | Qualified reviewer, implementation | 1-2 engineering days plus expert review | Planned |
| SD-05 | Up to 100 candidates with complete dispositions | SD-01 to SD-04; admitted sources and run budget | Bill; Brad for external processing | 2-4 review sessions; measure actual time | Not run |
| SD-06 | Reviewed immutable batch and CPU audit | SD-05 | Brad; Bill for technical acceptance | 0.5-1 engineering day | Not run |
| SD-07 | Baseline/adapter and synthetic-data comparison | SD-06 plus original case/baseline/compute gates | Brad; independent reviewer | Sized after token audit | Deferred |

SD-04 gates calculation candidates only. Other types can be rehearsed first;
report missing calculation coverage rather than fabricating unverified results.
The proposed mix is twenty candidates per type, at most ten per family. Fewer
eligible families produce a smaller pilot, not forced repetition or acceptance.

## File ownership

Planned paths below do not exist because of this documentation change.

| Repository | Existing integration | Planned files |
| --- | --- | --- |
| slm-foundry | `src/ingestion/contracts.py`, `curate.py`, existing normalized evidence | `src/ingestion/synthetic_review.py`, `schemas/synthetic_review.schema.json`, `tests/test_synthetic_review.py`: offline packet/provenance validation |
| slm-foundry | `src/ingestion/assist.py` and bounded OpenRouter client | `src/ingestion/synthetic_batch.py`, `tests/test_synthetic_batch.py`: explicit author/challenger jobs and attempt ledger |
| Broadbridge4096 | Domain ingestion policy, canonical case adapter, existing release bridge | `packs/oil-gas/synthetic/recipes.yaml`, `rubric.md`, `prompts/author.md`, `prompts/challenger.md`: domain policy only |
| Broadbridge4096 | Existing pack tests | `packs/oil-gas/scripts/synthetic_checks.py`, `packs/oil-gas/tests/test_synthetic_checks.py`: domain calculation checks |
| Broadbridge4096 | Existing helper rehearsal | `scripts/research/rehearse_synthetic_experts.py`, `scripts/research/test_rehearse_synthetic_experts.py`: fabricated end-to-end rehearsal |

Private runs belong under ignored `packs/oil-gas/outputs/` or approved private
artifact storage. Public inputs use the public companion pack with explicit
processing approval; that does not make the confidential pack cloud-eligible.

## SD-00: Workflow integration

- [x] Write the spec, this plan and the blank expert worksheet.
- [x] Link from README, delivery index, public evaluation and ingestion runbook.
- [x] Verify relative links, frozen benchmark hashes, diff cleanliness and existing offline helper/evaluation tests.

Publication is recorded by the draft PR head, not a preassigned completion box.
Stage only the seven workflow Markdown files; leave runtime/model state unchanged.

Verification on 26 September: 20 local links resolved, five original benchmark
hashes unchanged, all 60 human score rows still blank, and 25 existing offline
helper/evaluation tests passed. The first attempts could not create temporary
fixtures (missing local parent, then sandbox permission); an authorized run with
a fresh temporary directory passed. One existing requests dependency warning
remains. These are regression/document checks, not tests of the future runtime.

## SD-01: Main review and recipe approval

**Files:** original `output/openrouter-public-evaluation/public-v1-live/REVIEW_INSTRUCTIONS.md`, `scorecard_*.md`, `scores.csv`; blank `docs/templates/SYNTHETIC_EXPERT_REVIEW.md`.

- [ ] Bill reads original packets and records independent 0/1/2 scores, critical flags, evidence, name and date. Brad may screen first. Assistant triage is not human acceptance.
- [ ] Resolve disputed references through a new protocol version if material; do not silently change a benchmark after seeing answers.
- [ ] Run the existing offline aggregator from the Broadbridge checkout:

```powershell
python scripts/research/public_document_evaluation.py summarize `
  --run output/openrouter-public-evaluation/public-v1-live
```

Before human input, expect HOLD with no measured engineering mean. Missing model
outputs are availability findings, not observed technical errors.

- [ ] Brad/Bill confirm helper-selection thresholds. Bill records confirmed failure categories and recipe assumptions/variation rules using worksheet A; completed source/family/rights records stay private.
- [ ] Name an independent qualified reviewer when the accepting reviewer authored the answer or substantive correction. An unfilled assignment remains pending.
- [ ] Independently review each calculation template's assumptions, units/basis, valid ranges, fixed reference results and tolerance.

**Acceptance:** reviewed failure categories and recipe versions, with rights and
external-processing authorization recorded separately. No selected teacher is
inferred from the present incomplete paired comparison.

## SD-02: Offline verification packet

**Planned interface:** `build_review_packet(candidate, *, normalized_documents, family_history, recipe, generation_receipt, checks) -> dict` in `src/ingestion/synthetic_review.py`. Inputs are explicit JSON-compatible values. No network, database or environment fallback.

The envelope contains `schema=foundry.synthetic_review/1`, the unchanged pending
candidate/hash, source/recipe/prompt/rubric/receipt hashes, family closure, author
identity and named checks (`status`, `evidence`, `limitation`). Use Foundry's
canonical serialization/hash helpers. Model content cannot supply approval.

- [ ] Write failing tests with fabricated normalized documents/candidates: changed source hash, testing-only family, excluded historical holdout, invented evidence block, preapproved generated candidate, missing applicable check, and changed answer after hashing.
- [ ] Run `python -m pytest tests/test_synthetic_review.py -q`; confirm failures exercise absent behavior, not missing dependencies.
- [ ] Implement schema checks, evidence resolution, existing family closure and deterministic envelope hashing. Results remain pending even when mechanical checks pass.
- [ ] Test an otherwise valid positive fixture and a source instruction that tries to grant rights or set a reviewer; source instructions must not change trusted metadata.
- [ ] Rerun focused and existing contract/curation tests, then commit only named files in a draft Foundry PR.

**Acceptance:** deterministic CPU-only packet construction, unable to grant rights,
independent acceptance or training release.

## SD-03: Bounded generation and challenge

**Planned interface:** `run_batch(plan, *, author, challenger, verifier, output_root) -> dict` in `src/ingestion/synthetic_batch.py`. Roles are injected callables. The plan binds sources, eligibility, recipes, models/settings, candidate/call caps and budget. Live execution requires an explicit mode and approved plan hash.

- [ ] Write mocked tests for success, challenge objections, malformed output, timeout, unknown cost, call cap, restart and duplicate immutable attempt writes. Require retained failures and no automatic retry or cloud fallback.
- [ ] Test confidential ancestor policy and historical holdout rejection before either model callable. Add canary hindsight/reference strings to fabricated cases and assert absence from student/generation inputs.
- [ ] Implement the sequential runner using existing transport/policy controls. Preserve every attempt and receipt. It must not turn uploads into model calls or `assist.py` into a training trigger.
- [ ] Add domain recipes/prompts/rubric and a fabricated rehearsal. The challenger cites objections; it cannot approve. Only SD-01-approved recipes enter real runs.
- [ ] Run focused tests and `python -m pytest scripts/research/test_rehearse_synthetic_experts.py -q`. Require pending packets and zero releases without human decisions.
- [ ] Open separate draft engine/domain PRs with dependency hashes and named files; keep one implementation lane.

**Acceptance:** a second operator reproduces mock dispositions; CI makes no live
call. A documented manual run can bind sources/settings/budget without executing.

## SD-04: Calculation path

**Planned interface:** `check_calculation(template_id, givens, proposed_result) -> dict` in domain `synthetic_checks.py`, returning the SD-02 status/evidence/limitation shape. First template: `absolute_pressure_ratio_v1`; it does not size a compressor or predict power.

Independent reference vectors:

| Givens | Proposed answer | Expected disposition |
| --- | --- | --- |
| 30 bara suction, 60 bara discharge | ratio 2, dimensionless | pass arithmetic/basis within approved tolerance |
| 30 barg suction, 60 bara discharge | ratio 2 | needs_review; no implicit basis conversion |
| 0 bara suction, 60 bara discharge | any ratio | fail invalid input |
| 30 bara suction, 60 bara discharge | ratio 0.5 | fail |
| Same pressures, absent flow/composition/efficiency | numerical power | needs_review; ratio does not establish power |

- [ ] Write fixed-vector tests before the checker. Expected answers come from independent arithmetic, not calls to the implementation under test.
- [ ] Implement decimal arithmetic, explicit units/basis and accepted applicability limits. Persist template/version, synthetic givens, method and computed results as a calculation artifact, not a fabricated source quotation.
- [ ] Rehearse artifact admission through existing source/evidence controls. Its candidate still requires separate source rights and technical acceptance.
- [ ] Run `python -m pytest packs/oil-gas/tests/test_synthetic_checks.py -q` and the Foundry helper tests proving its original new-numerical-claim rejection still operates.

**Acceptance:** independently reviewed reference vectors and failure cases;
calculation success does not certify the entire engineering answer.

## SD-05: Candidate pilot

- [ ] Freeze eligible families, approved recipes, five-type mix and explicit call/cost bounds. Reserve independent evaluation families.
- [ ] Generate at most 100 candidates, at most 10 per family, proposed 20 per type. Record coverage gaps, every attempt and failure.
- [ ] Review every candidate using worksheet B. Admission requires 2/2, no critical error, no unresolved applicable check and independent acceptance. This candidate rule does not silently adopt the proposed helper-selection thresholds.
- [ ] Revisions get new hashes/reviews and retain family identity. Do not silently replace rejected examples to reach a quota.
- [ ] Complete worksheet C: dispositions, family coverage, known/missing costs, reviewer time and cost/minutes per accepted example; use N/A when zero accepted.

**Acceptance:** complete accounting and a technical decision to continue, revise
or stop. A target count never requires accepting a defective example.

## SD-06: Admission, release and CPU audit

- [ ] Use existing `ingestion_release.py register-candidates`, separate rights/technical reviews and `prepare-release` from the operator runbook.
- [ ] Rehearse revoked rights, new historical holdout, self-acceptance and changed candidate after review. Each must block release until resolved; add enforcement tests where current controls are insufficient.
- [ ] Bind verification evidence to the candidate/release artifact set. Changed envelope/recipe invalidates acceptance. Detached worksheets/receipts cannot satisfy this requirement.
- [ ] Obtain the separate release decision, build the immutable dataset and run the CPU audit. Record assistant-target token counts, truncation, family coverage and exact release hash.

**Acceptance:** reviewed rows admitted with preserved exclusions and provenance.
CPU audit success does not authorize GPU startup or host work.

## SD-07: Comparison after original gates

- [ ] Close Gate 0, score S0-cases and the required S0-retrieval comparison, and obtain bounded host/compute authorization.
- [ ] Freeze configs, model revisions, tokenizer/template/think settings, data hashes and evaluation families. Where data permits, compare expert-only and expert-plus-synthetic adapters with matched settings and stated token budgets.
- [ ] Run authorized QLoRA and report per-type quality, critical errors, grounding, abstention, latency and unrelated-task regressions.
- [ ] Brad controls promotion. Feed development failure categories into new recipes; keep locked test items outside generation. Stop iterations with unresolved regressions or inadequate measured benefit.

**Acceptance:** existing v0 baseline improvement and no new critical errors on the
evaluated set, reproducible by a second operator. Without an attribution
comparison, do not claim the improvement was caused by synthetic data alone.

## Later packages

Simulator sweeps need reviewed property methods, valid ranges and balance checks.
Preference/DPO needs reviewed preferred/rejected answers. Reinforcement learning
needs executable rewards and reward-exploitation tests. Native image/audio work
needs its own model and evaluation. None enters the current critical path.
