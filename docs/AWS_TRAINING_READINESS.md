# Qwen3-8B: AWS and dataset readiness

**29 September 22:17 UTC:** the approved checkpoint session ended before any
model download. Controller key-selection and startup-clock defects were fixed
and 19 offline lifecycle tests passed; the corrected start was rejected for
capacity. All three GPU hosts are stopped. The runtime qualification remains
valid, but model load and training remain pending. See [the session record](QWEN_MODEL_LOAD_SESSION.md)
and [the overall process diagram](SLM_PROCESS_FLOW.md).

**Next packet prepared:** [pinned Qwen checkpoint and model-load check](QWEN_MODEL_LOAD_SESSION.md). The 15-file public inventory was refreshed without downloading weights. Offline tooling is tested; no new EC2 session, inference or training occurred. Live execution remains separately scoped.

**Latest result, 29 September 20:03 UTC:** the approved A10G retry in
`us-east-1b` succeeded. All 113 pinned wheels installed and matched; `pip check`,
five synthetic GPU probes and **149 selected CPU tests** passed. The A10G and
both retained L4 hosts are independently confirmed stopped. Runtime installation
and small-kernel checks are complete; Qwen weight staging/model load, accepted
data/baselines, QLoRA smoke/resume and second-operator reproduction remain open.
No model inference or training ran. [Session result](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).
Earlier dated entries below preserve the capacity/transfer history.

**29 September 16:47 UTC retry:** Brad authorized a new bounded attempt using whichever existing host was available. The replacement in `us-east-1c` and then the original in `us-east-1d` each returned `InsufficientInstanceCapacity`; neither started. Both were independently confirmed stopped with unchanged launch times. The verified wheelhouse, replacement Python prerequisites and partial upload are preserved. All 18 offline selection/resume tests passed. No guest command, new transfer, installation or GPU test ran. Retry automation remains paused. [Receipt](evidence/aws-runtime-bundle-2026-09-28/retry-pair-2026-09-29-1647.json).

28 September 2026. Owner: Brad / Broadbridge. **CPU preparation plus an explicitly approved read-only development-database check; no Broadbridge fine-tuning job has run in this work.** This is the active FQ-12/FQ-13 readiness runbook. The optional OpenRouter helper comparison is deferred. Its provider availability and terms do not block this path.

## The model and the path

The target is **`unsloth/Qwen3-8B` on an approved AWS EC2 GPU host** (A10G runtime checks now passed; both L4 hosts preserved), not ECS and not the larger Qwen helper accessed through OpenRouter. Ollama's installed `qwen3:8b` GGUF serves responses; it is not the trainable checkpoint. The later training session needs the pinned Hugging Face weights plus the CUDA/Unsloth/TRL stack. A LoRA adapter is then evaluated, merged and converted to GGUF for serving.

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
| Real accepted release / Gate 0 | The approved read-only check reached dev, not production. Dev has 4 cases, 4 questions, 0 brief runs and 0 scorecards. Its two signed/training cases are SYN-prefixed hypothetical fixtures; one other signed case is testing-only. Production Bill submissions and Gate 0 coverage remain unknown. See the follow-up below. |
| AWS host | A10G `i-079b24e2b51ef7630`, g5.2xlarge, us-east-1b, is stopped with the installed venv retained. Original and replacement L4 hosts also confirmed stopped. [Bounded validation result](AWS_A10G_RUNTIME_SESSION_2026-09-29.md). |
| GPU runtime | Exact 113-wheel CUDA 12.6 bundle installed offline and version/hash verified on A10G. pip consistency, five synthetic GPU checks and 149 selected CPU tests passed. Unsloth 2026.9.12 / Transformers 5.5.0; no driver change. Qwen load, QLoRA/resume and reproduction remain untested; no floating bootstrap. |
| Artifact storage | Broadbridge intake already uses private R2. Do not automatically attach the older Ilyrium S3 profile or create another bucket. The [R2-to-EBS setup runbook](AWS_TRAINING_SETUP.md) and immutable transfer tool are prepared and rehearsed locally. Live prefix/token scope and exact transfer still need approval. An S3 instance profile is a requirement only if a separately approved S3 artifact path is selected. |
| Training diagnostics | Implemented and tested with local CPU child processes: merged stdout/stderr, private per-attempt files, 4 MiB cap with continuous draining, byte/hash/truncation receipts, and rejection of changed/incomplete captures. Actual CUDA logs and metrics remain unverified. |

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

Record the exact two repository commits, dataset hash, base revision, config hash, runtime lock, output/backup location, duration/cost caps, operator and release authority before the session. Resolve the runtime and storage gaps above and retain private logs during qualification. No source data should be sent to an external helper as a fallback.

Use the Foundry [serving brief](https://github.com/bHBeachsider/slm-foundry/blob/codex/aws-training-readiness/docs/SLM_SERVING_BRIEF.md) at `docs/SLM_SERVING_BRIEF.md` in the selected Foundry checkout. Approved-session bring-up/tear-down from that brief:

```powershell
# Future authorized session only; these commands were NOT run for readiness.
aws ec2 start-instances --region us-east-1 --instance-ids i-0439f5841d631d9f8
aws ec2 wait instance-running --region us-east-1 --instance-ids i-0439f5841d631d9f8
aws ec2 wait instance-status-ok --region us-east-1 --instance-ids i-0439f5841d631d9f8
$gpuAddress = aws ec2 describe-instances --region us-east-1 --instance-ids i-0439f5841d631d9f8 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
ssh -i 'C:\Users\bradu\Documents\ilyrium-autostudio\slm-foundry-key-v2.pem' "ec2-user@$gpuAddress"
# At the end of the authorized session, including failures:
aws ec2 stop-instances --region us-east-1 --instance-ids i-0439f5841d631d9f8
aws ec2 wait instance-stopped --region us-east-1 --instance-ids i-0439f5841d631d9f8
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
3. Task 3 preparation delivered: [resolved candidate runtime and private staging](AWS_TRAINING_SETUP.md). Host capacity and Python prerequisites resolved on the replacement; [runtime transfer remains incomplete](AWS_RUNTIME_RELOCATION_2026-09-29.md). A tested resumable transfer is prepared. Installation/import/kernel checks remain open; another start needs an explicit bounded decision.
4. Only after runtime, dataset and baseline gates are satisfied, authorize and perform the smoke run. No model inference, training or production changes occurred during runtime setup; the earlier approved database check was read-only against dev.

## Follow-up: diagnostics, runtime candidates and current dev counts

The generic implementation and candidate runtime metadata are in the continuing [Foundry draft #21](https://github.com/bHBeachsider/slm-foundry/pull/21), follow-up commit `b10d8542407dba375b5c154b5a65bd11530a5fc0`. [GPU_RUNTIME_PLAN.md](https://github.com/bHBeachsider/slm-foundry/blob/codex/aws-training-readiness/docs/GPU_RUNTIME_PLAN.md) records the dependency mismatch, candidate roots and qualification steps. No wheels, weights or runtime packages were downloaded or installed. That earlier checkpoint had only root candidates. The task 3 update below supersedes it with a resolved candidate; GPU qualification remains pending.

Follow-up [test receipt](evidence/aws-readiness-followup-2026-09-28/tests.json): Foundry **752 passed, 3 skipped**; Broadbridge **410 passed, 104 skipped**; focused log/controller/rehearsal tests **34 passed**. Tests were offline and did not load database credentials. Independent review identified and verified the fix for log-finalization errors skipping final accounting; no remaining actionable findings. The earlier test receipt above remains the historical checkpoint-control result.

The [read-only dev receipt](evidence/aws-readiness-followup-2026-09-28/dev-status.json) records 4 cases, 4 questions, 1 workflow, 9 sources, 4 source revisions, 1 candidate version, 1 recorded release, and zero brief runs/scorecards/model runs. Current source permissions are **3 pending and 1 revoked, none approved**. A historical approved candidate/release row does not establish current source eligibility. The case labeled `real_event` is signed but `testing_only`; an ID/type label alone does not independently verify its real-world origin. No case text, email addresses or credentials were included in the receipt.

The root `.neon` configuration and supplied pooled URL select **dev**, not the production capture branch. This check therefore cannot answer whether Bill submitted a production case. It used a repeatable-read, READ ONLY transaction and rollback; no data was changed. The initial approval-review block on credential access was resolved by Brad's explicit permission. A connection attempt using startup options was rejected by the pooler; configuring read-only mode in the transaction succeeded. Production status still requires a production-scoped read-only connection or an exported canonical case file; do not silently substitute another project or URL.

### First acceptance work package

Use the already prepared narrow pressure packet before collecting a larger corpus:

1. **Brad: rights decision.** Record the exact DOE-HDBK-1012/1-92 source hash and permission basis for selected pages 35–37, including contractor/figure credits. Current status stays pending until that decision exists.
2. **Appointed engineering reviewer: evidence and method.** Review the existing packet's nine exceptions against the PDFium page renders; accept/correct the two equations and four conversion proposals. Separately accept/correct `absolute_pressure_ratio_v1`, its absolute-pressure/matching-unit scope and provisional tolerance. Reject unsupported power/gauge conversions; the code does not supply missing physics.
3. **Reviewer: questions and references.** Prepare or accept the intended questions/answers with units, assumptions, missing-evidence behavior and hard-fail criteria. Use signed cases for the case-derived evaluation set. Record reviewer identity and the exact packet hash; blank forms and fabricated fixtures are not approvals.
4. **Operator: family allocation and release.** Keep handbook pages/derivatives in one family. Do not split pages or synthetic variants across training and held-out sets. Bind accepted examples and independent validation/test families with complete source history in the existing release flow, then run the exact-release CPU audit. The math sample stays on hold and diagram outputs remain excluded.

Existing packet instructions and local artifact locations are in [SLM_PREPARATION_REHEARSAL.md](SLM_PREPARATION_REHEARSAL.md); reuse `REVIEW.md` and `review.csv` in `fq02-doe-pressure-2026-09-27`. This work package creates no new approvals, sends no reviewer invitation and does not change the capture application. Current production case/review status and scored baselines remain prerequisites, not assumed facts.

## Task 3: runtime bundle and staging delivered

[Setup runbook](AWS_TRAINING_SETUP.md): the Linux candidate has 113 hashed wheels (3,792,751,006 bytes), independently checked metadata closure, explicit download authorization, offline installation commands and host gates. A fabricated four-file release passed a local private-store round trip; corruption, unsafe/intake prefixes, unexpected destinations and missing execution authority are rejected. No R2 credentials or cloud objects were accessed.

Public metadata at the pinned Qwen revision identifies 15 required files totaling 16,397,438,697 bytes, including four weight shards. No weights or wheel set were downloaded. Total planned package/base bytes are 20,190,189,703 before data and checkpoints. The >1 GB download gate remains open. Installation, actual driver/kernel compatibility and second-operator reproduction are not proven by metadata resolution.

## 29 September: A10G preparation and support case update

The [A10G session plan](AWS_A10G_RUNTIME_SESSION_2026-09-29.md) is prepared with an explicit host profile and one-request launch policy. Offline verification: Foundry 813 passed / 3 skipped; final focused tests 62 passed; private launch/transfer checks 18 passed. All 113 cached wheels reverified. No A10G host has been created and no GPU checks or training ran. Both L4 hosts were reconfirmed stopped. [Preparation receipt](evidence/aws-runtime-bundle-2026-09-28/a10g-preparation-2026-09-29.json).

AWS account case **179070520900642** is now confirmed **Unassigned**, category **Service Quotas, General**, with the approved report in correspondence. No AWS reply or engineer assignment is visible. This supersedes earlier wording that only an intake interaction existed, while preserving the earlier Technical-route rejection. [Case record](AWS_SUPPORT_CAPACITY_CASE_2026-09-29.md).

## 29 September 19:13 UTC: A10G validation attempt

The approved one-request A10G validation attempt was rejected with
`InsufficientInstanceCapacity` for `g5.2xlarge` in `us-east-1a`. Independent
inventory confirmed no created A10G instance and both L4 hosts still stopped.
No GPU validation or installation ran. The session is closed; no automatic
retry is active. [Result and receipt](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).
