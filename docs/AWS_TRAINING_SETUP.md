# AWS training setup and private staging

**Current next step, 29 September:** the retained A10G runtime passed installation,
imports, five GPU probes and 149 selected CPU tests. All GPU hosts are stopped.
The [checkpoint/model-load packet](QWEN_MODEL_LOAD_SESSION.md) now provides the
exact 16.40 GB inventory, tested CLI, selected A10G/venv and bounded guest commands.
Preparation is complete; model download/loading needs the separately scoped live
decision described there. The dated L4 attempts below are historical.

**29 September 16:47 UTC retry:** Brad authorized a new bounded attempt using whichever existing host was available. The replacement in `us-east-1c` and then the original in `us-east-1d` each returned `InsufficientInstanceCapacity`; neither started. Both were independently confirmed stopped with unchanged launch times. The verified wheelhouse, replacement Python prerequisites and partial upload are preserved. All 18 offline selection/resume tests passed. No guest command, new transfer, installation or GPU test ran. Retry automation remains paused. [Receipt](evidence/aws-runtime-bundle-2026-09-28/retry-pair-2026-09-29-1647.json).

Prepared 28 September 2026; updated 29 September. Runtime preparation does not authorize the separate base download, model inference, accepted-data release or training. Historical attempts remain in [the original session record](AWS_RUNTIME_SESSION_2026-09-28.md); the current host result is [A10G validation](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).

## Prepared inputs and remaining gates

| Input | Prepared evidence | Still required |
| --- | --- | --- |
| Linux runtime | Installed/verified on A10G: 113 matched packages, five GPU probes and 149 CPU tests passed | Recheck exact installed versions/profile on the next boot; model load and QLoRA remain separate |
| Qwen base | [Pinned public inventory](evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json): `unsloth/Qwen3-8B` at `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb`; 15 selected files; **16,397,438,697 bytes (15.271 GiB)** | Separate >1 GB download approval; downloaded-byte verification; no weights were acquired |
| Dataset | Tested four-file private transfer with fabricated records; accepted release format already exists | Real independent acceptance, current rights/history, held-out families and exact manifest hash |
| Host | Retained stopped A10G `i-079b24e2b51ef7630`, g5.2xlarge, us-east-1b; both L4 hosts preserved stopped | New bounded model-download/load decision; no restart performed by preparation |
| Model experiment | Existing 20-step/1,800-second controller proposal, every-5-step checkpoints and private logs | Gate 0, scored baselines, real release and bounded run authorization remain open |

Combined runtime and base artifact size is **20,190,189,703 bytes (18.804 GiB)** before dataset, source archives, temporary files or checkpoints. The runtime portion has been acquired on the PC; the base has not. Four weight shards individually exceed 1 GB and remain subject to separate approval. Keep >=64 GiB free as the provisional host gate; actual checkpoint/optimizer usage remains unmeasured. Replacement preflight measured 149,799,608,320 bytes free before transfer. Recheck after installation and before any weight/checkpoint staging.

The first-run candidate keeps Transformers **5.5.0** with Unsloth 2026.9.12. It does not change the CPU environment's 5.9.0. Full details and tested commands are in Foundry's [runtime README](https://github.com/bHBeachsider/slm-foundry/blob/codex/aws-training-readiness/infra/training/README.md). Passing dependency constraints does not establish CUDA compatibility or improved engineering answers.

## 1. Record the approved packet

Before a live session, Brad records the exact Foundry/Broadbridge commits, wheel-manifest SHA, base revision/inventory, real dataset release ID and **raw manifest SHA-256**, current rights check, operator, storage path, maximum host duration/cost and the purpose of each operation. Setup/download approval and training approval are separate. Do not fill missing reviewer identities or authority with fixture values.

Proposed storage is the existing private R2 bucket `broadbridge`, endpoint `https://af7446fd472b9a8d087250687882a487.r2.cloudflarestorage.com`, under `training/broadbridge-oil-gas/releases/<release_id>/`. This new prefix has not been created or tested live. It is deliberately outside `incoming/broadbridge-oil-gas/`, which triggers ingestion. Keep the bucket private; never create public/signed download links for staging. Do not attach the older Ilyrium S3 profile for this R2 path.

Use a short-lived bucket-scoped R2 token: uploader needs object read/write to verify immutable writes; the host needs object read only. If the current Cloudflare token cannot enforce the requested finer prefix boundary, record its actual bucket-wide scope and obtain that scope approval; do not claim prefix isolation. An operator injects credentials into the process environment only. No script reads `.env`, copies a credential file to the host or falls back to AWS metadata credentials.

## 2. CPU release check and later approved R2 upload

PowerShell 7, from the selected Foundry checkout, with its existing CPU environment. Set `$release` to the **real approved** absolute release directory; its final path component must be its release ID. These are operator variables, not shell placeholders to copy unchanged.

```powershell
$plan = python scripts/training_transfer.py plan --release-dir $release | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Release verification failed' }
$plan | ConvertTo-Json -Depth 5
```

Record that plan in the private approval packet. It lists only hashes/sizes/IDs, not question text. Recheck current source permissions before transfer; a valid historical manifest alone cannot detect a later revocation. Technical and rights approval still happen through the existing release workflow.

Only after the packet authorizes the exact upload:

```powershell
$env:R2_ENDPOINT_URL = 'https://af7446fd472b9a8d087250687882a487.r2.cloudflarestorage.com'
$env:R2_BUCKET = 'broadbridge'
$env:R2_ACCESS_KEY_ID = Read-Host 'R2 object token access key ID' -MaskInput
$env:R2_SECRET_ACCESS_KEY = Read-Host 'R2 object token secret' -MaskInput
try {
  python scripts/training_transfer.py push --release-dir $release --prefix training/broadbridge-oil-gas/releases --manifest-sha256 $plan.manifest_sha256 --execute
  if ($LASTEXITCODE -ne 0) { throw 'R2 staging failed; retain local release and stop' }
} finally {
  Remove-Item Env:R2_ACCESS_KEY_ID,Env:R2_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
}
```

This moves only `train.jsonl`, `val.jsonl`, `test.jsonl`, `manifest.json`, at most 64 MiB each. A conflict never overwrites an existing object. The manifest is published last. No live upload was rehearsed here; offline tests used a temporary local store and fabricated reviewer records.

## 3. Source staging and full runtime reproduction

For the current checkpoint-only session, use the selective source archives
below with the lifecycle controller in the model-load packet. **Skip the
wheelhouse transfer and fresh installation:** the validated A10G environment
already exists. The full-runtime instructions remain for a separately approved
reproduction on a fresh environment; they are not steps to repeat now.

Use [AWS_TRAINING_READINESS.md](AWS_TRAINING_READINESS.md) and Foundry `docs/SLM_SERVING_BRIEF.md` for approved bring-up and **tear-down even on failure**. Host is EC2, not ECS. Obtain its current IP with `describe-instances`; never hardcode it. Keep port 11434 closed. Do not start the box just to read these instructions.

Stage a reviewed snapshot of code, not a working directory or credentials. From PowerShell, set `$foundry`, `$domain`, `$foundryCommit`, `$domainCommit` and a fresh private `$stage` directory to the two reviewed checkouts/commits and output location. Create that directory first. These selective archives contain tracked engine/config/test files; domain data is transferred separately through its approved release.

```powershell
git -C $foundry archive --format=tar --output="$stage/foundry.tar" $foundryCommit src scripts schemas infra/training configs tests conftest.py pytest.ini
if ($LASTEXITCODE -ne 0) { throw 'Foundry archive failed' }
git -C $domain archive --format=tar --output="$stage/domain.tar" $domainCommit packs/oil-gas/pack.yaml packs/oil-gas/configs packs/oil-gas/schemas packs/oil-gas/prompts packs/oil-gas/rubrics docs/evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json
if ($LASTEXITCODE -ne 0) { throw 'Domain archive failed' }
tar -tf "$stage/foundry.tar"
tar -tf "$stage/domain.tar"
Get-FileHash "$stage/foundry.tar","$stage/domain.tar" -Algorithm SHA256
$gpuAddress = aws ec2 describe-instances --region us-east-1 --instance-ids i-079b24e2b51ef7630 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
$sshKey = 'C:\Users\bradu\Documents\ilyrium-autostudio\slm-foundry-key-v2.pem'
ssh -i $sshKey "ec2-user@$gpuAddress" 'umask 077; mkdir -p ~/slm-training/inbox'
scp -i $sshKey "$stage/foundry.tar" "$stage/domain.tar" "ec2-user@${gpuAddress}:slm-training/inbox/"
```

Review the archive listings and sizes before transfer; stop on unexpected tracked data or credentials. On Linux, compare the two archive SHA-256 values with the recorded PC hashes, then extract into **new empty session-specific** Foundry and domain directories. Retain the two Git commit IDs in the packet because `git archive` does not create checkouts. Do not overwrite the prior validated snapshot or another operator's workspace. For a separately approved full runtime reproduction only, transfer the verified wheelhouse and follow Foundry `infra/training/README.md` for a fresh venv, offline hash-enforced install, version/import checks and CPU tests. For the checkpoint-only session, recheck and reuse `~/slm-training/venv-a10g-a23670f4d161`. If any prerequisite, disk or driver differs, stop and review that host change rather than running a floating bootstrap.

## 4. Later approved R2-to-EC2 release download

After runtime checks pass, in Bash, from `~/slm-training/foundry`. Supply `RELEASE_ID` and `MANIFEST_SHA256` from the independently recorded packet, not a newly fetched remote object. Supply an absolute new `DESTINATION="$HOME/slm-training/releases/$RELEASE_ID"`.

```bash
set -euo pipefail
umask 077
export R2_ENDPOINT_URL='https://af7446fd472b9a8d087250687882a487.r2.cloudflarestorage.com'
export R2_BUCKET='broadbridge'
read -rsp 'R2 read-only access key ID: ' R2_ACCESS_KEY_ID; printf '\n'
read -rsp 'R2 read-only secret: ' R2_SECRET_ACCESS_KEY; printf '\n'
export R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY
trap 'unset R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY' EXIT
"$HOME/slm-training/venv-a10g-a23670f4d161/bin/python" scripts/training_transfer.py pull --release-id "$RELEASE_ID" --prefix training/broadbridge-oil-gas/releases --manifest-sha256 "$MANIFEST_SHA256" --destination "$DESTINATION" --execute
unset R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY
```

The tool validates remote bytes into a private temporary directory before publishing the release. A corrupted download or an existing destination is rejected. It verifies release rows, provenance structure, split hashes and manifest identity; it cannot supply missing engineering acceptance or detect external revocations. Compare the resulting receipt with the PC plan. Recreate the controller request on this host because absolute config paths change its binding.

## 5. Base checkpoint and model-load check

The inline Hub-download prototype is superseded by the tested Foundry
`scripts/model_checkpoint.py`. Use [QWEN_MODEL_LOAD_SESSION.md](QWEN_MODEL_LOAD_SESSION.md)
for exact commands, inventory hash, byte total, A10G/venv selection, deadlines,
pass criteria and remaining authority. `plan`/`verify` are offline; `fetch` and
`load-check` require explicit execution flags plus the separate recorded decision.
Never use the older L4 paths or silently substitute a prequantized mirror.

## 6. Private run backup and stopping

After a separately authorized smoke, retain the immutable release, exact config/request/authorization, adapter, tokenizer, full optimizer/scheduler/RNG/trainer checkpoints, private capped logs and runtime/test receipts. Never use the four-file dataset tool for model or checkpoint backups. Do not prune resumable checkpoints merely to fit a transfer budget.

For the first session use an approved encrypted local backup destination via SSH. On the host, with `RUN_DIR` set to the exact completed private run directory and `BACKUP` to a fresh archive path outside it:

```bash
du -sb "$RUN_DIR"
test ! -e "$BACKUP"
tar -cf "$BACKUP" -C "$(dirname "$RUN_DIR")" "$(basename "$RUN_DIR")"
sha256sum "$BACKUP"
stat -c '%s bytes' "$BACKUP"
```

Review the actual archive size; stop before transferring >1 GB unless that exact backup is covered by the approved budget. Copy that one archive with `scp`, compare its SHA-256 on the PC with `Get-FileHash`, and retain the receipt before treating backup as complete. Avoid shell history with secrets, `scp` of `.env`, broad bucket/repo sync, public links or publishing logs. An R2 checkpoint-backup policy can follow separately; it is not implemented by this task.

Stop the instance using the readiness runbook even if installation, transfer or training fails. A persistent failure is recorded with its private logs; do not retry under a fresh unbounded timer. Second-operator reproducibility requires repeating the reviewed setup and bounded smoke on the actual host, not merely reading this document.

## Offline validation

The checkpoint preparation adds **36 offline tests**; the current full Foundry
suite passed **850 tests, with 3 skipped**. Command syntax, inventory bindings
and preparation-only scope are recorded in the
[checkpoint preparation receipt](evidence/aws-runtime-bundle-2026-09-28/qwen-load-preparation-2026-09-29.json).
The older preparation counts below remain historical.

[Validation receipt](evidence/aws-runtime-bundle-2026-09-28/tests.json): Foundry full suite **781 passed, 3 skipped**; one further CLI round-trip test is included in the final **30-pass** focused bundle/transfer run. Broadbridge **410 passed, 104 skipped**, including 103 database tests without credentials and one optional reference adapter. Five PowerShell blocks and two embedded Python blocks parsed successfully without executing future operations. Independent review found no remaining actionable defects after an encoding correction. CPU tests use the existing environment, not the uninstalled candidate GPU stack. Remote CI is reported on the draft PRs.
