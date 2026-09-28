# Qwen3-8B: AWS and dataset readiness

28 September 2026. Owner: Brad / Broadbridge. **Offline preparation only; no Broadbridge fine-tuning job has run in this work.** This is the active FQ-12/FQ-13 readiness runbook. The optional OpenRouter helper comparison is deferred. Its provider availability and terms do not block this path.

## The model and the path

The target is **`unsloth/Qwen3-8B` on the existing AWS EC2 L4 instance**, not ECS and not the larger Qwen helper accessed through OpenRouter. Ollama's installed `qwen3:8b` GGUF serves responses; it is not the trainable checkpoint. The later training session needs the pinned Hugging Face weights plus the CUDA/Unsloth/TRL stack. A LoRA adapter is then evaluated, merged and converted to GGUF for serving.

The local tokenizer snapshot is pinned to `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb`. The smoke configuration proposes that same base revision; this task verifies tokenizer files only, not availability or completeness of the corresponding weight snapshot on AWS.

The shortest approved path remains:

1. Accept a narrow task, rights and reference answers; preserve held-out families.
2. Score S0-cases on stock Qwen3-8B. Build S0-retrieval only after scored failures identify the need and about 20 documents are admitted. It must improve on S0-cases under the existing plan.
3. Freeze an independently accepted dataset; audit its exact tokenizer rendering and assistant-only labels.
4. Authorize one bounded AWS host session, establish the runtime and stage the pinned weights/data.
5. Run a 20-step QLoRA smoke test. Only after its operational checks pass, authorize the domain experiment and matched base/retrieval/adapter comparison.

Steps 1–3 are not replaced by a helper-model contest. Offline host/configuration preparation can proceed now. Diagram training remains blocked on its separate branch.

## Readiness verified locally

| Item | Finding / remaining work |
| --- | --- |
| Generic Foundry controller | Already implements immutable release/config bindings, 40-character base revision, optimizer-step limit, cumulative wall-time limit, process cleanup and matched checkpoint resume. Earlier infrastructure-brief wording that these controls still need implementation is stale. |
| Checkpoint cadence | Fixed a missing configuration pass-through: the installed CPU Transformers default is 500 steps, too sparse for an interrupted 20-step run. The proposed smoke uses every 5 steps, retaining 2 full checkpoints, evaluation batch 1 and logging every step. Real CUDA checkpoint creation/resume remains to be demonstrated. |
| External domain pack | Existing absolute `--pack` loading is covered by offline tests. For a released dataset, use the bounded controller with the smoke config; it binds the immutable release paths instead of the pack's mutable `data/train.jsonl` paths. |
| Local math snapshot | 1,200 raw records verified against the original receipt; 946 train / 128 val / 120 test candidates and 6 exclusions. All raw records: 3 over 2,048 tokens; original candidate splits: 0 overlength, 0 truncation. This is encoding evidence, not approval. |
| Math quality / family status | 3 exact duplicate groups, 4 numeric-template groups, 1,196 proposed families, no detected cross-split family under these heuristics. Ten convenience checks: 7 consistent, 1 wrong, 1 ambiguous/inconsistent, 1 contradictory. Whole sample stays on quality/family hold. These checks are not an accuracy estimate. |
| Release boundary | Fresh fabricated rehearsal again refused all 8 invalid acceptance/release scenarios. Fixture identities and approvals confer no real training authority. Authenticated synthetic acceptance still needs complete current rights/history and live integration. |
| Real accepted release / Gate 0 | Not established by the inspected local evidence. No database was queried in this task; this is not a claim that Bill has entered no cases. Obtain current signed-case export/reviews before counting coverage or declaring a release ready. |
| AWS host | Last documented, 24 September: `i-0e5e1cbc7b1367566`, `g6.2xlarge`, L4, us-east-1; serving works, training venv absent, S3 instance profile absent. None was rechecked live. |
| GPU runtime | `infra/bootstrap.sh` currently installs unpinned Unsloth. Before launch, choose/test a compatible CUDA/Torch/Unsloth/TRL/PEFT/bitsandbytes set and preserve its resolved package lock and driver versions. The CPU dev requirements are not a GPU lock. |
| Artifact storage | Broadbridge intake already uses private R2. Do not automatically attach the older Ilyrium S3 profile or create another bucket. Confirm the approved R2-to-EBS staging/backup path and least-privilege access. An S3 instance profile is a requirement only if a separately approved S3 artifact path is selected. |
| Training diagnostics | The controller presently suppresses subprocess stdout/stderr. Retain training/evaluation metrics from Trainer checkpoint state and add bounded private run-log capture before a real launch; failures before the first checkpoint otherwise have poor diagnostics. No real runtime/logging evidence is claimed. |

Fresh aggregate receipts: [data/release/config verification](evidence/aws-readiness-2026-09-28/readiness.json) and [test results](evidence/aws-readiness-2026-09-28/tests.json). Foundry: **742 passed, 3 skipped**. Broadbridge pack/DB/research suite: **410 passed, 104 skipped** (103 DB integration tests without credentials and 1 optional reference-graph configuration). Existing Requests/SWIG warnings remain. Detailed data findings and limitations remain in [SLM_DATA_PREPARATION_RESULTS.md](SLM_DATA_PREPARATION_RESULTS.md).

## Offline reproduction — no weights or model calls

Run from PowerShell 7 with the existing CPU environment (Windows PowerShell 5.1 quoting was not validated). Substitute the two checkout paths on another machine; the local data/tokenizer paths are not committed. Choose a fresh `$out` each time. These commands intentionally use the held sample for software checks only.

```powershell
$domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-plan'
$intake = 'C:\Users\bradu\Documents\Broadbridge4096\packs\oil-gas\data\public-start-2026-09-24'
$tokenizer = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\foundry-gate1\qwen-tokenizer'
$out = Join-Path $domain 'packs\oil-gas\outputs\aws-readiness-repeat'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
python "$domain\scripts\research\audit_openmath.py" --intake $intake --foundry $foundry --tokenizer $tokenizer --out "$out\math"
python "$domain\scripts\research\rehearse_release_audit.py" --mock --foundry $foundry --out "$out\release"
```

To audit the smoke settings against the existing held sample, copy the config to the ignored output folder and bind only the original candidate paths. This does not create a release or authorization:

```powershell
python -c 'import pathlib,sys,yaml; d,i,o=map(pathlib.Path,sys.argv[1:]); c=yaml.safe_load((d/"packs/oil-gas/configs/train-smoke.yaml").read_text()); c["data"]={s:str(i/"candidates/math"/(s+".jsonl")) for s in ("train","val","test")}; o.mkdir(parents=True,exist_ok=True); (o/"HELD-SAMPLE-dry-run.yaml").write_text(yaml.safe_dump(c),encoding="utf-8")' $domain $intake $out
python "$foundry\src\train.py" --config "$out\HELD-SAMPLE-dry-run.yaml" --dry-run --tokenizer-dir $tokenizer > "$out\HELD-SAMPLE-mask.json"
if ($LASTEXITCODE -ne 0) { throw 'CPU audit failed; inspect the report' }
```

The report includes a rendered batch, input token IDs, labels, mask and length distribution. `ready` means mechanically encodable only. Keep full rendered content private/ignored. No `run` command belongs in this rehearsal.

## What is needed to release a dataset

| Input | Current disposition | Next action and owner |
| --- | --- | --- |
| DOE pressure packet, pages 35–37 | Prepared, not accepted | Brad records item-level rights/credits; appointed engineering reviewer resolves the 9 extraction exceptions and accepts equation/unit/method scope. Start with this narrow packet rather than another bulk acquisition. |
| Five DOE leads / four new families | Held | Brad rights review; Bill or qualified reviewer selects useful tasks and references. Frozen public-v1 families and derivatives remain excluded from training. |
| OpenMath sample | Quality/family hold | Independently adjudicate proposed families and solution correctness for any deliberately selected subset; never train the full sample merely because format checks pass. |
| Signed expert cases | Current count unknown here | Export canonical `case_record/1`, validate/import, count Section-C coverage and inspect permissions/sign-off. `training` + `signed` is necessary but does not replace release review. Testing/reference-only cases never enter train. |
| Synthetic candidates | Pending real acceptance | Use accepted recipes/source families and independent review; numerical checks need accepted methods/tolerances. The helper contest is optional. No author self-acceptance or fabricated reviewer approval. |

Gate 0 still needs recorded rights/storage, the named reviewer (Bill Hurt), and at least 30 signed case-derived questions across all five types with reference answers. Capture preferences/brainstorms are requirements evidence, not automatic training targets. Bill may nominate another competent reviewer for narrowly scoped engineering checks.

A release must bind source revisions/rights, complete family history, train/val/locked-test allocation, independent technical decisions and a release approver. Freeze messages JSONL and manifests with the existing [release bridge](INGESTION_PIPELINE_RUNBOOK.md); do not hand-edit an approved JSONL file. Do not present mock releases as real releases.

Once a **real accepted** release is available, the following is still CPU-only. `$release` must be its verified local directory, and `$run` a fresh sibling run directory outside it:

```powershell
$config = Join-Path $domain 'packs\oil-gas\configs\train-smoke.yaml'
$revision = '946bc9ac74a6c1f8cf012497c503a119b2fcf2eb'
# Set $release and $run to approved absolute paths before proceeding.
Push-Location $foundry
python -m src.ingestion.training prepare --release-dir $release --config $config --base-revision $revision --max-steps 20 --wall-time-seconds 1800 --run-dir $run
python -m src.ingestion.training audit --release-dir $release --config $config --base-revision $revision --max-steps 20 --wall-time-seconds 1800 --run-dir $run --tokenizer-dir $tokenizer
Pop-Location
```

`prepare` prints request bindings, not approval. Do not manufacture `approved_by`. Recreate the request after staging on AWS because absolute paths change the config hash. The 1,800-second training-process cap excludes separately budgeted host setup/download time. It is a proposal, not a spend authorization or a claim that the L4 can finish in that time.

## Later AWS session — gated, not executed

Record the exact two repository commits, dataset hash, base revision, config hash, runtime lock, output/backup location, duration/cost caps, operator and release authority before the session. Resolve the runtime, storage and log-capture gaps above first. No source data should be sent to an external helper as a fallback.

Use the Foundry [serving brief](https://github.com/bHBeachsider/slm-foundry/blob/codex/aws-training-readiness/docs/SLM_SERVING_BRIEF.md) at `docs/SLM_SERVING_BRIEF.md` in the selected Foundry checkout. Approved-session bring-up/tear-down from that brief:

```powershell
# Future authorized session only; these commands were NOT run for readiness.
aws ec2 start-instances --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
aws ec2 wait instance-running --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
aws ec2 wait instance-status-ok --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
$gpuAddress = aws ec2 describe-instances --region us-east-1 --instance-ids i-0e5e1cbc7b1367566 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
ssh -i 'C:\Users\bradu\Documents\ilyrium-autostudio\slm-foundry-key-v2.pem' "ec2-user@$gpuAddress"
# At the end of the authorized session, including failures:
aws ec2 stop-instances --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
aws ec2 wait instance-stopped --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
```

Training uses SSH; the serving tunnel is needed only for model calls. Keep port 11434 private, use local port 11435 for later Ollama testing, and never pin a public IP. Recheck identity, GPU/disk capacity, runtime and actual hourly cost at session preflight. Stop if the host differs from the approved plan.

On the host, first inspect `nvidia-smi`, `df -h`, and the presence of `~/slm`; provision only the separately approved runtime. Unload Ollama's model before training to free VRAM. Stage the selected Hugging Face weight revision and the accepted release with file hashes; downloads over 1 GB need the previously required explicit go. Run local/offline token checks again against that snapshot. Do not treat the installed Ollama GGUF as the base download.

The bounded controller's **`run`** subcommand is the sole intended launch path, with the exact approved `foundry.training_authorization/1` bindings. Resume only a checkpoint inventoried by its failed-state receipt and under the same cumulative time budget. It must retain adapter weights, optimizer/scheduler state, RNG state and trainer state; adapter-only files are not resumable training checkpoints. Interrupted host locks require operator reconciliation, not blind deletion/retry.

Smoke success means 20 completed optimizer steps, finite recorded losses, no truncation/OOM, validated adapter files, a full intermediate checkpoint and demonstrated matched resume within the authorized budget. Record peak VRAM, elapsed training time, total host time/cost, package versions, failures and artifact hashes. A falling loss alone is not engineering improvement. After success, the domain experiment must beat the matched S0-retrieval baseline without new critical errors and be reproducible by a second operator before deployment.

## Review delivery

Generic engine changes: [draft Foundry #21](https://github.com/bHBeachsider/slm-foundry/pull/21), commit `9e28862`, stacked on data-audit draft #15. This domain branch is stacked on data-preparation draft #19; the helper-comparison drafts remain separate. Independent read-only review found no actionable defects in the code, commands or evidence; real GPU execution remains unverified.

## Next dispatch

1. Resolve current signed-case/reviewer status and accept the narrow DOE/calculation scope; no optional helper comparison is required.
2. Complete authenticated candidate acceptance/history binding where needed and freeze the first accepted release.
3. Finish the runtime lock, approved storage transfer and private run logging; review the concrete bounded AWS request.
4. Only then authorize the GPU session and perform the smoke run. No EC2, training or production changes occurred in this readiness work.
