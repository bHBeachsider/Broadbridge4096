# FQ-07 execution and scoring runbook

The same tools also support [v3 context reservations](HELPER_COMPARISON_V3.md).
Use its explicit `--protocol-version v3` preparation command and endpoint evidence
rules. Commands without that option continue to prepare v2, whose exact-token
preflight requirements below remain in force.

This implements the paired v2 comparison described in
[HELPER_COMPARISON_V2.md](HELPER_COMPARISON_V2.md). The default run uses fabricated
HTTP responses and has no network access. It tests the real Foundry client, paired
stop logic, billing ledger and reviewer workflow. It does not test model quality.
Qwen3-8B remains the domain-training target; these two hosted helpers are separate
candidates for later public-material work.

No live comparison has been authorized or performed by this implementation.
Public-v1, its production review page, score rows and saved answers remain unchanged.
No training, EC2, dataset download, database or production changes are involved.

## Delivery and dependency

Domain implementation: `scripts/research/run_helper_comparison.py` and its tests.
Generic dependency: Foundry `src/openrouter_client.py` on
`codex/helper-comparison-receipts`, based on `codex/foundry-synthetic-batch`.
The supplied Foundry path must contain the new `request_payload` method. Neither
the main checkout nor the isolated diagram-recovery branch is changed by this work.

The generic transport adds full-request validation, optional reasoning controls,
request and response hashes, UTC times, finish reason and cost/identity receipts
even when later validation fails. Existing callers retain their default settings.
OpenRouter's `reasoning.enabled: false` is a request control, not proof that a
particular endpoint supports disabling reasoning. Hiding reasoning text is not
equivalent to disabling it. Verify support for each candidate before accepting
the run. See the [official reasoning documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
and [provider routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection).
No current model availability or provider prices are asserted here.

The [28 September provider preflight](HELPER_COMPARISON_PREFLIGHT.md) records
current catalogue observations, a prepared native-nonreasoning Stage-A packet,
and the unresolved hosted-token bound. Its proposed context-based reservation
alternative is not implemented in v2 and does not authorize execution.

## Offline rehearsal

Use an existing Python environment with the repository's lightweight evaluation
dependencies. Set these paths to the corresponding checkouts on another machine.
All output directories must be new. A run never overwrites or resumes an old run.

```powershell
$Domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$Foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-plan'
$Python = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http\outputs\geometry-venv\Scripts\python.exe'
$Root = Join-Path $Domain ('tmp\helper-execution-' + (Get-Date -Format yyyyMMdd-HHmmss))
& $Python "$Domain\scripts\research\prepare_helper_comparison.py" --stage stage_a --out "$Root\packet"
& $Python "$Domain\scripts\research\run_helper_comparison.py" plan --packet "$Root\packet" --foundry $Foundry --out "$Root\preflight"
& $Python "$Domain\scripts\research\run_helper_comparison.py" run --mode mock --packet "$Root\packet" --foundry $Foundry --out "$Root\run"
& $Python "$Domain\scripts\research\run_helper_comparison.py" score --run "$Root\run" --scores "$Root\run\scores.csv" --out "$Root\unreviewed-report"
```

Expected: 20 fabricated responses, zero live calls, 20 blank score rows and an
unreviewed report. A stage-B rehearsal uses `--stage stage_b`: 40 mock responses.
Mock stage B tests software independently; it does not satisfy the live dependency
on reviewed stage A. No credentials are needed for either mock rehearsal.

Outputs:

| File | Purpose |
| --- | --- |
| `preflight/wire_requests.jsonl` | Complete request payloads for token/capability preflight; no headers or credentials |
| `preflight/approval.template.json` | Incomplete worksheet, with approvals false and counts/reviewer/dates unset |
| `run/run.json` | All planned slots, attempts, valid/failed/not-run states, hashes, receipts and reservations |
| `run/sample.json`, `protocol.json`, `prompt.md`, `requests.jsonl` | Frozen evidence and request snapshots |
| `run/review.md` | Questions, evidence, references, hard-fail criteria, tolerances and responses A/B |
| `run/scores.csv` | Blank manual review rows bound to the run and exact answer hashes |
| `run/checksums.json` | Immutable artifact checksums; scores are versioned separately |
| `report/scores_summary.json` and `.md` | Coverage, paired quality metrics, critical errors, disputes, billing and review time |

The review view omits helper identity. Operator files disclose it and should be
withheld until initial scoring is saved. This is practical masking, not a security
boundary or a claim of independent blind assessment.

## Reviewer instructions

Copy `scores.csv` to a new file for each review/adjudication version. Keep every
planned row, identity column and hash unchanged. For each valid answer fill:

| Field | Required value |
| --- | --- |
| `score` | 0 incorrect; 1 needs correction; 2 correct and supported, using the per-type rubric |
| `critical_error` | YES or NO; YES requires score 0 |
| `hard_fail_matched` | YES or NO; YES requires score 0 and critical_error YES |
| `reference_dispute` | YES or NO; a dispute blocks the proposed screen |
| `review_seconds` | Finite nonnegative time spent; record measured time where practical |
| `reviewer`, `review_date` | Named reviewer and ISO date, e.g. `2026-09-28` |
| `notes` | Supporting evidence, correction, hard-fail match or dispute explanation |

Leave unreviewed rows entirely blank in the review fields. Failed/not-run responses
stay ungraded: an HTTP error is not an engineering score of zero. Run `score` again
using the reviewed CSV and a new report directory. Changed answer hashes, missing
rows, duplicate rows, grades for failed responses and incomplete reviews are rejected.
The tool validates recorded fields; it cannot independently determine whether a
hard-fail criterion actually applies. That is the technical reviewer's responsibility.

JSON reports expose each arm's planned/valid/failed/not-run/reviewed counts, matched
pair count, per-type and per-family means and denominators, critical errors, failure
flags, mean attempted-call latency, known billing and accepted-answer cost where
eligible. The paired difference is Qwen minus Mistral. A zero score is retained;
an absent score is not zero. Billing from failed calls is included when known.
Unknown billing is a hold, not free usage. Reviewer minutes are separate from API cost.
The live stage-B report recomputes and includes the pinned stage-A reviews: all
30 pairs, both stages' charges and reviewer time. Standalone mock B is explicitly
labelled stage-only. Missing or altered A artifacts block the combined report.

The quality screen remains a proposed development screen. Mock results never
produce eligible cost rankings or selection/training approval. Even fully reviewed
live stage B requires fresh-family confirmation before model selection. A CSV name
is a manual record, not authenticated engineering sign-off. Capture UI integration
and formal release approval remain separate work.

## Before any live run

The `plan` command creates a concrete worksheet and wire payloads, not consent.
Brad and the technical reviewer must finish it with real evidence. Store an approved
copy as `approval.json`, with supporting evidence files beside it. Never place keys,
tokens, signed URLs or connection strings in any of these files.

1. Commit the exact two code revisions and keep both worktrees clean. Bind the
   packet checksum-manifest hash, stage and repository commits. Record a run ID,
   approving operator, technical reviewer and timezone-aware approval/expiry times;
   the approval lasts at most 24 hours.
2. Recheck public-source rights, cloud route, references and the proposed quality
   screen. Record explicit acceptance. Add a hash-bound rights/cloud decision file.
3. Refresh both model/provider endpoint snapshots. Confirm strict JSON schema,
   price controls, no fallback, privacy/retention/distillable-text controls and
   equivalent non-reasoning behavior. `disabled` sends `reasoning.enabled:false`;
   `native_nonreasoning` sends no reasoning field and requires evidence that the
   endpoint is inherently non-reasoning. The default worksheet is only a proposal.
   Use `plan --mistral-reasoning native_nonreasoning` (or the Qwen equivalent) if
   the verified endpoint calls for it, then redo hashes and token preflight.
4. Record disclosed weights/provider/tokenizer/template/quantization revisions.
   Keep undisclosed ones null, with `unknown_revision_reason: provider_not_disclosed`;
   do not invent pins. Such nulls remain a limitation of reproducibility.
5. For **every** wire request, record its canonical JSON SHA-256 and a verified
   input-token upper bound <=8,192, including template and schema overhead.
   Supported attestations are `provider_count` or `pinned_tokenizer_with_template`,
   each backed by a local evidence file and its SHA-256. Byte counts or guessed
   token ratios do not qualify. If the provider's hidden overhead cannot be bounded,
   the live run remains blocked. No tokenizer/model is downloaded by this tool.
6. Accept a stage ceiling no greater than $0.10 for A / $0.15 for B and combined
   ceiling no greater than $0.25. Confirm account/key spending controls and that any
   fees fit the reservation. Local receipts cannot enforce the provider's bill.
   Unknown charges retain their reservation and stop both arms. A charge above the
   reservation is reported as an overrun, not hidden or refunded by the runner.
7. Stage B additionally pins A's `run.json` and reviewed CSV by path and hash in
   `prior_stage_a`. The runner recomputes A's report, requires a complete reviewed
   live A passing the proposed screen, and deducts A's known cost from the combined
   allowance. Mock A, missing reviews, disputes or unknown billing cannot qualify.
8. Brad authorizes that exact completed approval-file hash. Only then use `run
   --mode live --approval <file> --approve-sha256 <hash> ...` with the separately
   configured `OPENROUTER_API_KEY`. The tool does not read `.env` or use OpenAI keys.

The approval's `evidence_files` is a mapping of simple local filenames to SHA-256
values. `cloud_approval_sha256`, each provider's `endpoint_snapshot_sha256`, and
each request's `evidence_sha256` must reference those verified bytes. Human
attestations are auditable inputs, not independent API capability tests.

An approval gets a one-use `.used` sidecar. Both call reservations are checkpointed
before the first call. Each slot is checkpointed as attempting before transport,
then finalized with its result. An interrupted run keeps an incomplete checkpoint
and cannot be scored/resumed automatically; reconcile billing before creating a
new protocol/run. Preserve all failed-run costs in the experiment record. Filesystem
interlocks prevent accidental reuse at the same location, not deliberate copying
or execution by a different machine. Account spend controls remain necessary.

## Acceptance tests

All transport tests use mocked HTTP; the integration rehearsal also blocks socket
connections. Tests cover payload parity, receipt fields on errors, first/second-arm
failures, no retries, preserved reservations, exact packet/approval/token binding,
stage-B dependency, stale/incomplete/critical/disputed reviews, and mock isolation.
See `docs/verification/helper-comparison-v2-execution.json` for actual suite counts
and the separately recorded mock rehearsal. No engineering scores are fabricated
in the saved example; positive grading is confined to software test fixtures.
