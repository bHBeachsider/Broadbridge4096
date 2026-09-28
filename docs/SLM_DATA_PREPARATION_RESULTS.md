# Offline data preparation results — 27 September 2026

FQ-03, FQ-04 and FQ-06 preparation is complete; source/technical acceptance and real training admission remain open. No EC2, model weights, inference, training, production/database writes or client material. The [execution plan](SLM_DATA_PREPARATION_PLAN.md) and [queue](SLM_WORK_QUEUE.md) separate preparation from release.

## New engineering source families

[Five DOE documents](ENGINEERING_SOURCE_SHORTLIST.md) were inspected for exact editions and credits, representing four provisional families: steam tips, burner air/fuel, pumping systems and the Dow St. Charles assessment. All remain held for item-level rights and technical scope review. None was downloaded into the pipeline or converted to QA here. The nine frozen public-v1 families, including their derivatives, remain excluded from training.

## Existing math sample

The original 1,200-row NVIDIA OpenMathInstruct-2 snapshot and eight original file hashes were verified. All six excluded rows participate in similarity analysis. They had no assigned split in the original acquisition, which rejected them before splitting; their history stays unassigned. Originals and their 946 train / 128 val / 120 test allocation were not changed.

The [aggregate evidence](evidence/data-preparation-2026-09-27/math-summary.json) records:

- Three normalized exact-duplicate groups, four numeric-template groups (including the exact groups), zero additional pairs at token-trigram Jaccard >=0.85, and 1,196 proposed families.
- Zero detected cross-split families and zero conflicting expected answers within exact-duplicate groups. These are bounded text heuristics, not a semantic-leakage guarantee. Family proposals require adjudication; missing benchmark ancestry and possible base-model contamination remain limitations.
- Ten disclosed convenience spot-checks at zero-based rows 0, 1, 99, 199, 399, 599, 799, 999, 1099 and 1199. Seven final answers were consistent with the checked interpretation; one was wrong, one question ambiguous/inconsistent and one internally inconsistent. This is not an accuracy estimate or a verification of every step of the supplied solutions.

Three findings explain why matching a publisher-supplied answer is insufficient:

| Row (zero-based) | Independent result | Disposition |
|---|---|---|
| 1 | Enumerating three-digit integers whose cubes end in 125 gives 22 values, sum **11,990**, not the supplied 2,000. Independently, n=5 mod40 gives 125..965. | Wrong final answer despite generated solution/expected-answer agreement |
| 599 | If the average after **each** shelf must be integer, the first seven shelves total 68, which is not divisible by seven. If only the overall average is intended, two valid allocations have different fifth-shelf counts. Generation-instruction residue also appears. | Ambiguous/inconsistent; the supplied answer is not justified under either interpretation |
| 1199 | Cylinder volume implies h squared =400; the supplied diagonal relation implies h squared =125. | Contradictory premises; must not teach the asserted answer as verified |

The seven consistent checks include a standard quadratic-form convention for row 99; the question's representation is not independently unique without that convention. No synthetic replacement answers or filtered training release were created. The whole sample remains **quality/family review hold**, useful for machinery tests only until independently accepted.

Attribution: NVIDIA / Shubham Toshniwal, Wei Du, Ivan Moshkov, Branislav Kisacanin, Alexan Ayrapetyan and Igor Gitman, *OpenMathInstruct-2: Accelerating AI for Math with Massive Open-Source Instruction Data* (2024). The [pinned dataset card](https://huggingface.co/datasets/nvidia/OpenMathInstruct-2/blob/469216e3f46f4dacf476b382e192485ea51a143e/README.md) declares [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and Llama3.1-405B-Instruct-generated solutions with GSM8K/MATH source or augmented problems. The preserved card's hash is in the evidence. This audit adds analysis and counterexamples; it does not change or republish the original dataset. Preserve attribution and upstream provenance in any later admitted derivative; base-model license review is a separate record.

## CPU token audit and mock release checks

Pinned local tokenizer: `unsloth/Qwen3-8B` revision `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb`; five tokenizer file hashes verified, `local_files_only=True`. Current `qwen-2.5` rendering/assistant masking reused. All 1,200 raw rows: 119–2,407 tokens, median 359, p95 838, three over 2,048, zero truncation. The original candidate splits have no overlength rows. The [CPU dry-run summary](evidence/data-preparation-2026-09-27/cpu-dry-run-summary.json) binds the full ignored rendered batch/mask; ready means mechanically encodable, **not** ready for training. Future base/adapter comparisons still require the same pinned template and think settings.

The [mock release rehearsal](evidence/data-preparation-2026-09-27/release-rehearsal.json) verified eight refusals: author accepting their own packet, revoked rights, historical held-out family, changed candidate, stale packet decision, mock packet entering live acceptance, release of pending content and stale release approval. A separate explicitly fabricated approved fixture produced a hash-keyed release and passed readback verification.

The new generic `synthetic_admission.check_acceptance` is a **pure boundary for a trusted caller**, not authentication and not automatic release. It binds a decision to the exact pending packet, current documents/history and independent actor. Mock mode is opt-in, receipts retain `training_approved:false`, and hashes cannot detect omitted history. Wiring this into the authenticated live review/DB/release flow with authoritative history remains open for FQ-12/SD-06. No human engineering acceptance was simulated as real.

## Reproduce

Use the two draft checkouts containing this change. All paths below are absolute; choose a **new** output directory each time. `python` is the Foundry CPU development environment with the pinned local tokenizer available. The intake and tokenizer live in the original Broadbridge checkout's ignored directories, not in Git.

```powershell
$domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-live-test'
$foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http'
$intake = 'C:\Users\bradu\Documents\Broadbridge4096\packs\oil-gas\data\public-start-2026-09-24'
$tokenizer = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\foundry-gate1\qwen-tokenizer'
$out = Join-Path $domain 'packs\oil-gas\outputs\data-preparation-repeat'
python "$domain\scripts\research\audit_openmath.py" --intake $intake --foundry $foundry --tokenizer $tokenizer --out "$out\math"
python "$domain\scripts\research\rehearse_release_audit.py" --mock --foundry $foundry --out "$out\release"
python "$foundry\src\train.py" --config "$intake\offline-audit.yaml" --dry-run --tokenizer-dir $tokenizer
```

The existing intake config contains original absolute train/val paths; inspect/adjust a copied config when using another machine. No model weights are needed. Full local artifacts from this run are under `packs/oil-gas/outputs/data-preparation-2026-09-27/`; the final math report is in `math-v2` after clarification of row 599's cumulative-average wording. The earlier report remains local for audit. Only source metadata and aggregate evidence are committed.

## Software validation

[Test receipt](evidence/data-preparation-2026-09-27/tests.json): Foundry full suite **708 passed, 12 skipped**; Broadbridge pack/DB/research suite **408 passed, 106 skipped**. Optional DB/reference integrations were not enabled. After the row-599 clarification, its ten-test audit module passed again and the full 1,200-row/tokenizer audit was replayed into a fresh directory. Existing Requests dependency and SWIG deprecation warnings remain. No test result confers source rights or engineering acceptance.

## Diagram work remains separate

See [connectivity errors and required corrections](DIAGRAM_CONNECTIVITY_REMEDIATION.md): disconnected crossings joined, explicit arrows reversed, unsupported directions asserted, plus incomplete source endpoints. The saved pilot is not rerun or retuned by this task. Next useful visual work is a reviewed native-model crop set with explicit arrows and crossing conventions; source gaps must not be filled by model guesses.

Next offline queue item is FQ-07, the bounded helper-comparison protocol revision. Human decisions remain rights/credits, engineering scope and methods, case questions, and independent answer review. Those decisions precede a real training release.
