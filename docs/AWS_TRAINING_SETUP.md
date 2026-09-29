# AWS training setup and private staging

**29 September runtime update:** the approved replacement `i-0439f5841d631d9f8` in `us-east-1c` passed host preflight after the reviewed Python 3.11 prerequisite installation. The runtime upload hit a 30-minute SCP command timeout near completion; candidate installation and GPU/CPU checks did not run. Both instances are stopped, independently verified; the original 15:06 UTC deadline was met. A prefix-verified SFTP resume passed nine offline tests but needs a new bounded-start decision. The heartbeat stays paused. See [relocation and transfer receipt](AWS_RUNTIME_RELOCATION_2026-09-29.md).

Prepared 28 September 2026; updated 29 September. Runtime preparation does not authorize the separate base download, model inference, accepted-data release or training. Historical attempts remain in [the original session record](AWS_RUNTIME_SESSION_2026-09-28.md); the active host record is the relocation report above.

## Prepared inputs and remaining gates

| Input | Prepared evidence | Still required |
| --- | --- | --- |
| Linux runtime | Foundry `infra/training/`: 113 wheels, exact hashes and 227 metadata dependency checks; PC bundle verified | Complete prefix-verified transfer, isolated Linux install, actual imports/kernels and selected CPU checks |
| Qwen base | [Pinned public inventory](evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json): `unsloth/Qwen3-8B` at `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb`; 15 selected files; **16,397,438,697 bytes (15.271 GiB)** | Separate >1 GB download approval; downloaded-byte verification; no weights were acquired |
| Dataset | Tested four-file private transfer with fabricated records; accepted release format already exists | Real independent acceptance, current rights/history, held-out families and exact manifest hash |
| Host | Replacement `i-0439f5841d631d9f8`, g6.2xlarge, us-east-1c; Python 3.11 prerequisites installed and preflight passed; source retained stopped | Both hosts stopped. No runtime venv installation or GPU check yet; another bounded start needs explicit approval |
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

## 3. Later approved host session and source transfer

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
$gpuAddress = aws ec2 describe-instances --region us-east-1 --instance-ids i-0439f5841d631d9f8 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
$sshKey = 'C:\Users\bradu\Documents\ilyrium-autostudio\slm-foundry-key-v2.pem'
ssh -i $sshKey "ec2-user@$gpuAddress" 'umask 077; mkdir -p ~/slm-training/inbox'
scp -i $sshKey "$stage/foundry.tar" "$stage/domain.tar" "ec2-user@${gpuAddress}:slm-training/inbox/"
# $wheelhouse is the later approved, already verified wheel directory from Foundry's README.
scp -i $sshKey -r $wheelhouse "ec2-user@${gpuAddress}:slm-training/"
```

Review the archive listings and sizes before transfer; stop on unexpected tracked data or credentials. On Linux, compare `sha256sum ~/slm-training/inbox/{foundry,domain}.tar` with the recorded PC hashes, then extract into **new empty** `~/slm-training/foundry` and `~/slm-training/domain` directories. Retain the two Git commit IDs in the packet because `git archive` does not create checkouts. Do not overwrite another operator's workspace. Follow Foundry `infra/training/README.md` for host facts, fresh venv, offline hash-enforced install, version/import checks and CPU tests. If Python 3.11/ensurepip, disk or driver is missing, stop and review that host change rather than running a floating bootstrap.

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
"$HOME/slm-training/venv-a23670f4d161/bin/python" scripts/training_transfer.py pull --release-id "$RELEASE_ID" --prefix training/broadbridge-oil-gas/releases --manifest-sha256 "$MANIFEST_SHA256" --destination "$DESTINATION" --execute
unset R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY
```

The tool validates remote bytes into a private temporary directory before publishing the release. A corrupted download or an existing destination is rejected. It verifies release rows, provenance structure, split hashes and manifest identity; it cannot supply missing engineering acceptance or detect external revocations. Compare the resulting receipt with the PC plan. Recreate the controller request on this host because absolute config paths change its binding.

## 5. Base checkpoint — inventory now, download later

The metadata-only [inventory](evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json) distinguishes LFS SHA-256 from Git blob SHA-1 for small tracked files. Do not treat a Git object ID as a file SHA-256. The revision and four weight hashes are available, but downloaded weights have not been tested. Ollama's GGUF is not this trainable checkpoint.

Only after approval of the **16,397,438,697-byte** base download, use the newly installed environment from the domain snapshot directory. Set `HF_HUB_CACHE` to a new private absolute directory and preserve that same environment variable for subsequent audits and controller runs. Run the download in a separate process with `HF_HUB_OFFLINE=0`; the runtime qualification commands use offline mode. Do not remove the revision or widen the allowlist on failure.

```bash
export HF_HUB_CACHE="$HOME/slm-training/hf-cache-qwen-946bc9ac74a6c1f8cf012497c503a119b2fcf2eb"
HF_HUB_OFFLINE=0 "$HOME/slm-training/venv-a23670f4d161/bin/python" - <<'PY'
import hashlib, json, os
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download
m = json.loads(Path('docs/evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json').read_text())
cache = Path(os.environ['HF_HUB_CACHE'])
assert cache.is_absolute() and not cache.exists(), 'Choose a fresh private cache directory'
assert sum(x['size_bytes'] for x in m['files']) == 16397438697
assert m['repo_id'] == 'unsloth/Qwen3-8B' and m['revision'] == '946bc9ac74a6c1f8cf012497c503a119b2fcf2eb'
root = Path(snapshot_download(repo_id=m['repo_id'], revision=m['revision'], cache_dir=cache,
                  allow_patterns=[x['path'] for x in m['files']], max_workers=2, token=False))
assert root.resolve().is_relative_to(cache.resolve())
for item in m['files']:
    path = root / item['path']
    # Hub snapshots use links into the cache's blobs directory; reject links outside this private cache.
    assert path.is_file() and path.resolve().is_relative_to(cache.resolve()) and path.stat().st_size == item['size_bytes'], item['path']
    if item['hash_algorithm'] == 'sha256':
        h = hashlib.sha256()
    else:
        assert item['hash_algorithm'] == 'git-blob-sha1'
        h = hashlib.sha1(b'blob ' + str(item['size_bytes']).encode() + b'\0')
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    assert h.hexdigest() == item['hash'], item['path']
    cached = Path(hf_hub_download(m['repo_id'], item['path'], revision=m['revision'], cache_dir=cache, local_files_only=True, token=False))
    assert cached.resolve() == path.resolve(), item['path']
print(json.dumps({'files_verified': len(m['files']), 'bytes': m['total_bytes'], 'model_loaded': False}))
PY
```

This future download command is not a hard network spend limiter: Hub retries/cache metadata can add overhead. Account for that in the approved cap, observe transfer size and stop on unexpected revision/size behavior. It verifies the final selected bytes and local-only cache resolution, and never loads the model. Incomplete files remain private and unqualified. Keep `model.base=unsloth/Qwen3-8B`, the same pinned revision and `HF_HUB_CACHE` for the controller; set `HF_HUB_OFFLINE=1` again after acquisition. The training worker inherits the selected cache. Use the returned snapshot's tokenizer for its CPU audit. Do not silently substitute a local path for the model ID or permit another download during training. No training command is introduced by this setup document.

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

[Validation receipt](evidence/aws-runtime-bundle-2026-09-28/tests.json): Foundry full suite **781 passed, 3 skipped**; one further CLI round-trip test is included in the final **30-pass** focused bundle/transfer run. Broadbridge **410 passed, 104 skipped**, including 103 database tests without credentials and one optional reference adapter. Five PowerShell blocks and two embedded Python blocks parsed successfully without executing future operations. Independent review found no remaining actionable defects after an encoding correction. CPU tests use the existing environment, not the uninstalled candidate GPU stack. Remote CI is reported on the draft PRs.
