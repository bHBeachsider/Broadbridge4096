# DOE pressure training package

**30 September continuation:** [retained-cache training preparation](AWS_CACHED_TRAINING_PREPARATION.md) adds a generic hash-bound offline loading path in Foundry. It is locally tested, not GPU-qualified; the accepted release, training-capable host packet and execution decision remain outstanding. Bill can now use the [live questionnaire](https://broadbridge-capture.vercel.app/questionnaires/pressure-training-v1).

30 September 2026 UTC. Purpose: show Bill a concrete teaching loop to obtain feedback and buy-in. This proposed engineering demonstration does not close Gate 0, replace S0-cases/S0-retrieval, accept diagram training or authorize a customer-facing model.

## Prepared files

The builder produces an ignored local package at `packs/oil-gas/outputs/pressure-demo-v1/`. Regenerate into a fresh directory elsewhere; generated config paths are local to that directory.

| File | Use |
| --- | --- |
| `train_candidates.jsonl` | 36 messages records: 24 Decimal-generated calculations and 12 authored examples across brief, missing-data, grounded-explanation and abstention tasks |
| `demo_prompts.jsonl` | Eight fixed system/user conversations; no reference answer, hard-fail criteria or assistant message |
| `demo_answer_key.jsonl` | Reviewer-only expectations, rounding tolerances and critical-error rules |
| `response.schema.json` | JSON answer format: answer, calculation, missing information, limitations and source IDs |
| `proposed_config.json` | Pinned Qwen/LoRA settings for CPU audit; **not execution authorization** |
| `manifest.json` | Artifact hashes, source evidence, rights hold, proposed family transition and run limits |
| `token_audit.json` | Actual local counts and Foundry renderer hash |
| `rendered_batch.json` | One rendered example with token IDs, labels and assistant-only mask |
| `scorecard.md` | Blank base/adapter review sheet; no invented scores |

This preparation envelope is not the Foundry immutable release contract, a canonical signed case or a replacement source register. Rows retain `split: null`, `proposed_split: train`, rights TBD and training false. No authorization, accepted release or adapter has been created.

## Data decisions

- Source: DOE-HDBK-1012/1-92 Volume 1, PDF pages 35–37 / printed HT-01 pages 9–11. Original SHA-256 `3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9`; extraction packet SHA-256 `0ae8da768e4fbc5427d5c4acbd4b2193dcf93308fffac6e8cb61fce26f0b8150`.
- Formulas: absolute = local atmosphere + signed gauge; absolute = local atmosphere − positive vacuum depression. Compatible supplied psi inputs only. `Decimal` arithmetic; ±0.05 psi is proposed rounding tolerance only.
- Brad approved the earlier diagnostic scoring/test set assuming Bill's agreement. New variants and JSON targets are prepared for review; there is no actual Bill signature or score. **Source rights remain TBD.** Preparation neither determines nor grants rights.
- Proposed transition: move the **whole DOE-HDBK-1012 family** to training for this demo. Preserve the historical `pressure-diagnostic-v1` and source register unchanged. Record the transition before release, including loss of independent-test eligibility for related volumes, derivatives and old answers. No silent split-policy bypass or per-page repartition.
- Eight new probe wordings/values remain the same family and method as training. They are demonstration probes, not independent val/test rows. There is no training-loop validation set, early stopping or adapter selection on these eight scores.
- Hydrostatics with implicit mass/force conventions, column-pressure recipes, images, diagram connectivity, private cases, OpenMath and the five unacquired DOE leads are excluded.

## Offline reproduction

No `.env`, database, R2, cloud API, model weights, inference or GPU is needed. Use the existing local PDF, extraction and four-file tokenizer snapshot; there is no download fallback. Changed pinned inputs and an existing output directory are rejected.

```powershell
$domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-plan'
$python = 'C:\Python 313\python.exe'
$package = Join-Path $domain 'packs\oil-gas\outputs\pressure-demo-repeat'
& $python "$domain\scripts\research\prepare_pressure_demo.py" `
  --out $package `
  --pdf 'C:\Users\bradu\Documents\Broadbridge4096\packs\oil-gas\data\public-start-2026-09-24\raw\doe\DOE-HDBK-1012-92_VOL1.pdf' `
  --evidence-dir "$domain\packs\oil-gas\outputs\fq02-doe-review-20260930" `
  --foundry $foundry `
  --tokenizer-dir 'C:\Users\bradu\Documents\Broadbridge4096\tmp\foundry-gate1\qwen-tokenizer'
if ($LASTEXITCODE -ne 0) { throw 'Preparation/audit failed; preserve output for diagnosis' }

# Optional exact trainer dry-run: --dry-run is essential; it never loads a model.
Push-Location $foundry
try {
  & $python -m src.train --config "$package\proposed_config.json" --dry-run `
    --tokenizer-dir 'C:\Users\bradu\Documents\Broadbridge4096\tmp\foundry-gate1\qwen-tokenizer'
  if ($LASTEXITCODE -ne 0) { throw 'Foundry CPU audit failed' }
} finally { Pop-Location }
```

To rebuild extraction, use `FIRST_DATASET_REVIEW.md` with the pinned PDF runtime. Training/probe rows are deterministic; config output paths and their hashes vary by workstation. The builder verifies the original proposal hash before deriving examples.

The PC audit uses existing Python 3.13.5 / Transformers 5.9.0 / tokenizers 0.22.2. **AWS stays on the validated Transformers 5.5.0 stack**. Re-run rendering on that runtime before optimizer steps and bind the actual rendering/config hashes. No upgrade was made.

## Proposed AWS session, pending approval

Use retained `i-079b24e2b51ef7630` (A10G, us-east-1), existing `~/slm-training/venv-a10g-a23670f4d161` and verified Qwen cache. Base `unsloth/Qwen3-8B`, revision `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb`. No reinstall, model download, provider switch or replacement host.

| Phase | Proposed limits and evidence |
| --- | --- |
| Before paid start | Record source-use and family transition; accept exact candidates through the existing review/release workflow; create immutable release and hash-bound authorization; prepare/test a **training-capable** host packet |
| Preflight | All retained hosts stopped; no conflicting workload/controller/lock; pinned SSH and IMDS identity; shutdown behavior stop; no busy GPU; arm guards before staging |
| Staging | Verify release/code hashes; bind loading to the existing cache with offline mode enforced; audit exact tokenizer/labels |
| Base comparison | At most eight generations; retain every answer, latency and failure |
| Training | **20 optimizer steps / 1,800 seconds** maximum; batch 1 × accumulation 8; context 2,048; NF4; LoRA r16/alpha16/dropout0; seed 3407; LR 0.0002; save every 5 steps, retain 2; `train.evaluate: false` |
| Adapter comparison | Same eight prompts, evidence, pinned ChatML and NF4 base; deterministic decoding (`do_sample=false`), no thinking trace, ≤384 new tokens each. Maximum 16 total generations; both comparison phases together ≤900 seconds |
| Evidence/stop | Hash adapter/checkpoints/receipts; preserve results; stop immediately on completion/failure. Guest stop at 80 min, API stop at 85, force fallback at 87, stopped verification by 90, all from first start request |

One host window is at most 90 minutes; work stops before the existing 78-minute cutoff. No deadline extension or automatic repetition to get a nicer result. Expected active work is an **unmeasured estimate of 20–45 minutes**, not a promise. If comparisons cannot fit, preserve the smoke result and request a separate session.

The tracked `model_load_session.py` packet is **load only** and cannot be reused as training authorization. Training-payload integration/testing, offline-cache binding and release-specific authorization remain execution preparation to complete after the source-use decision. This package does not claim that bridge has run. Foundry's bounded `src.ingestion.training` controller remains the intended optimizer launch path; do not train by directly launching the candidate config.

## Success and reporting

Mechanical success: 20 optimizer steps, finite losses, no truncation/OOM, valid adapter tied to the base, full intermediate checkpoint state, exact hashes and final stopped evidence. A checkpoint does not prove resume; a matched resume rehearsal remains required before relying on recovery.

Demonstration success: Bill can follow source → example → adapter → actual behavior and identify a useful next task. Show all eight pairs; score 0/1/2 and critical errors, structured-output validity, numerical/unit errors, grounding and abstention. Missing/malformed responses count as failures. No improvement is a valid result. Repeated tuning on these probes cannot establish independent accuracy.

Production/domain gates remain signed cases and rights, S0-cases then justified retrieval comparison, independent family-separated performance without new critical errors, and reproduction by a second operator.

## Remaining decisions

1. Brad: record the source-use basis for these exact DOE pages and internal training, and approve the whole-family transition from diagnostic dev to demonstration training.
2. Brad: approve the bounded run once the accepted release, code and tested host packet are bound to it. Preparation today is not execution approval.

The [Bill walkthrough](BILL_QWEN_TRAINING_DEMO.md) is ready now. No email was sent.

## Preparation results

All 36 training conversations fit: 473–581 tokens, median 540, p95 562;
19,231 total tokens and 5,415 supervised assistant tokens. No example was
truncated. The eight prompt lengths are 371–384 tokens, plus a 384-token output
reserve. The actual Foundry CLI `--dry-run` also returned ready for CPU rendering.
This is a preparation result, not permission to launch training.

Full Python checks: **Foundry 946 passed / 12 skipped** (three existing
Requests/SWIG warnings); **Broadbridge 453 passed / 115 skipped**. Optional
integration checks were not enabled. [Saved package manifest](evidence/pressure-demo-preparation-2026-09-30/manifest.json),
[token audit](evidence/pressure-demo-preparation-2026-09-30/token_audit.json) and
[validation receipt](evidence/pressure-demo-preparation-2026-09-30/validation.json)
record the exact scope and artifact hashes. Raw candidate files remain in the
ignored local package and can be regenerated using the commands above.
