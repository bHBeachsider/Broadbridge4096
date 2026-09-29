# Qwen checkpoint download and model-load session

**Execution update, 29 September 22:17 UTC: blocked before model acquisition.**
Brad approved the checkpoint download and load check. The first start stopped
after the controller selected older source-image SSH pins instead of the actual
keys recorded during successful A10G validation. Both current keys matched that
successful session's `known_hosts`. A correction then exposed a startup-clock
bug: startup readiness used the original session epoch rather than the restart
epoch. Both accepted starts were stopped before any guest transfer or download.
After fixing both paths, **19 offline tests** passed, including full mocked
first/restart lifecycles and failure cleanup. The third start request returned
`InsufficientInstanceCapacity`. The original **23:31:49 UTC** deadline was never
extended. All three GPU hosts are stopped; no weights, inference or training ran.

The original single-start procedure below received two controller corrections
within the same approved time window; three requests are recorded rather than
presented as one. No further start is scheduled. Actual acquisition and model
fit remain unverified. [Execution receipt](evidence/aws-runtime-bundle-2026-09-28/qwen-load-attempt-2026-09-29.json).

Before any later attempt: use the **actual successful A10G `known_hosts`** as
the trust source; calculate startup/SSH readiness from that attempt's timestamp,
capped by the original operation cutoff; retain one absolute acquisition/load/
shutdown deadline. The corrected private controller and its tests are preserved
under Foundry `outputs/qwen-load-session-20260929-2218/` with hashes in the receipt.
The recorded deadline must not be reset to continue this ended packet.

The following is the original prepared scope, retained for audit.

Prepared 29 September 2026. **Preparation only: no model weights downloaded,
EC2 start, inference or training in this task.** This is the next reviewable
execution packet after the [successful A10G runtime checks](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).
The previous approval explicitly excluded model weights and model loading; a new
bounded execution decision is needed before the live steps below.

## Exact scope

| Item | Binding |
| --- | --- |
| Host | Existing stopped `i-079b24e2b51ef7630`, g5.2xlarge / A10G, us-east-1b / use1-az2; us-east-1 |
| Retained environment | `~/slm-training/venv-a10g-a23670f4d161`; no installation, dependency refresh or driver change |
| Base | `unsloth/Qwen3-8B`, revision `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb` |
| Inventory | `docs/evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json` |
| Raw inventory SHA-256 | `ae69d76c4b5b18ac823687ee0df2bbc45ba12c030f9147970e51f799a0107ee5` |
| Selected files | 15, including four safetensors weight shards; **16,397,438,697 bytes / 15.271 GiB** |
| Download route | Public Hugging Face directly to the existing A10G EBS disk; no PC weight relay, R2, S3 or credentials |
| Disk admission | At least **85,116,915,433 bytes** free before acquisition, retaining 64 GiB after the selected payload |
| Fresh private cache | `~/slm-training/hf-cache-qwen-946bc9ac74a6c1f8cf012497c503a119b2fcf2eb` |
| Load | Original checkpoint quantized at load into NF4; 2,048 context, one A10G, no CPU offload, no remote code |
| Session ceiling | One start attempt; **90 minutes from the first start request**, with no deadline extension |
| Compute estimate | At the previously verified $1.212/hour, at most **$1.818** instance compute for 90 minutes; retained EBS, public IPv4 and other charges separate |
| Excluded | Inference/generation, datasets, QLoRA/adapter creation, optimizer steps, production changes, replacement hosts, instance resizing and merges |

[Metadata refresh](evidence/aws-runtime-bundle-2026-09-28/qwen-base-refresh-2026-09-29.json)
matched all 15 hashes/sizes against the pinned public record, reading only 2,823
metadata bytes. That confirms the inventory, not downloaded weights or model
compatibility. The existing Ollama GGUF is a serving artifact and cannot replace
this trainable checkpoint.

## Local preparation (available now)

From the reviewed Foundry checkout in PowerShell:

```powershell
$inventory = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan\docs\evidence\aws-runtime-bundle-2026-09-28\qwen-base-inventory.json'
python scripts/model_checkpoint.py plan --manifest $inventory
```

Expected: 15 files, 16,397,438,697 bytes, the inventory hash above and
`model_loaded: false`. The generic tool and offline tests are in Foundry;
resource identity, selection and execution authority stay in Broadbridge.

Before a live start, freeze both final Git commits and create selective tracked
source archives using [the staging runbook](AWS_TRAINING_SETUP.md). Include the
new Foundry script, `training_bundle.py`, the runtime manifest/profiles, and the
domain inventory. Review archive names/sizes and SHA-256 them on the PC; transfer
only those small archives and verify hashes on the guest. Never copy `.env`,
credentials, working directories, domain records or the already installed wheel
bundle. Extract into a fresh session directory. Do not repoint or overwrite the
prior validated source snapshot.

## Bounded live sequence (only after the new execution decision)

Use the same reviewed ownership and cost controls as the completed runtime
session, with a **new** ignored session directory and request receipt. Record
the approved scope, commits, inventory/script/archive hashes, selected paths and
first-start timestamp before mutation. The model CLI below is the guest payload;
it is not an EC2 lifecycle controller. Do not execute it through a bare SSH
session without the independent stop guards.

1. Require all three retained GPU hosts stopped and no conflicting running/
   pending G/VT workload or local session owner. Use only the named A10G. Keep
   the capacity heartbeat paused. Resolve the public IP from AWS after startup.
2. Use one `StartInstances` call with `AWS_MAX_ATTEMPTS=1`, standard retry mode.
   A capacity rejection ends the attempt. Reconcile an ambiguous timeout against
   instance/boot identity before any further action; never launch another host.
3. Bind the returned boot, type, zone, image and instance ID. Verify the retained
   pinned SSH host keys and guest IMDSv2 identity. Require shutdown behavior
   `stop`, no existing GPU process and the same A10G/runtime profile. Stop on an
   unexpected host fact; no new prerequisites or upgrades are part of this go.
4. Before any payload, arm and verify the guest stop at minute **80**, independent
   API stop at **85**, forced stop after three unsuccessful graceful-stop minutes
   or by minute **87**, and stopped verification by **90**. These deadlines are
   measured from the first start request, including capacity/startup delays.
5. Transfer/verify the small source packet. Run `host-check --profile g5-a10g`
   with the retained venv. The checkpoint tool checks selected bytes plus the
   disk reserve again. No package or model operation should overlap Ollama work.
6. Fetch the pinned checkpoint; cut off acquisition by minute **65**. Run
   `verify` and the model-load check only after every file passes. Allow at most
   ten minutes for load and stop all work by minute **78**, whichever is earlier.
7. Save private stdout/stderr, parsed results, script/hash bindings, elapsed
   time and failures. Stop immediately on completion or any failure and verify
   stopped state independently. Do not restart the host to finish this packet.

### Guest commands

Set `FOUNDRY` and `DOMAIN` to the **new verified archive directories**. Set
`SESSION_START_EPOCH` from the controller's first-start receipt, never to the
time the shell starts. Fractional seconds are rounded down in the shell, which
can shorten the window by less than one second and never extends it.
These variables are required inputs, not guessed defaults.
The external controller must enforce the minute-78 process deadline and retain
the independent 80/85/90-minute guards even if this shell exits or disconnects.

```bash
set -euo pipefail
umask 077
: "${FOUNDRY:?verified source directory required}"
: "${DOMAIN:?verified domain directory required}"
: "${SESSION_START_EPOCH:?original start epoch required}"
SESSION_START_EPOCH=${SESSION_START_EPOCH%%.*}
[[ "$SESSION_START_EPOCH" =~ ^[0-9]+$ ]]
PY="$HOME/slm-training/venv-a10g-a23670f4d161/bin/python"
INVENTORY="$DOMAIN/docs/evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json"
INVENTORY_SHA256=ae69d76c4b5b18ac823687ee0df2bbc45ba12c030f9147970e51f799a0107ee5
export HF_HUB_CACHE="$HOME/slm-training/hf-cache-qwen-946bc9ac74a6c1f8cf012497c503a119b2fcf2eb"
cd "$FOUNDRY"
"$PY" scripts/training_bundle.py host-check --profile g5-a10g --disk "$HOME/slm-training"
download_seconds=$((SESSION_START_EPOCH + 65*60 - $(date +%s)))
test "$download_seconds" -gt 0
timeout --signal=TERM --kill-after=15s "$download_seconds" \
  "$PY" scripts/model_checkpoint.py fetch --manifest "$INVENTORY" \
  --cache-dir "$HF_HUB_CACHE" --expected-sha256 "$INVENTORY_SHA256" \
  --approved-bytes 16397438697 --execute
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
"$PY" scripts/model_checkpoint.py verify --manifest "$INVENTORY" \
  --cache-dir "$HF_HUB_CACHE" --expected-sha256 "$INVENTORY_SHA256"
load_seconds=$((SESSION_START_EPOCH + 78*60 - $(date +%s) - 15))
test "$load_seconds" -gt 0
if [ "$load_seconds" -gt 600 ]; then load_seconds=600; fi
timeout --signal=TERM --kill-after=15s "$load_seconds" \
  "$PY" scripts/model_checkpoint.py load-check --manifest "$INVENTORY" \
  --cache-dir "$HF_HUB_CACHE" --expected-sha256 "$INVENTORY_SHA256" \
  --profile g5-a10g --expected-model-type qwen3 --execute
```

The full selected payload is approved separately from network overhead; Hugging
Face retries/metadata can add bytes. This tool does not impose a hard wire-byte
cap. The process and host deadlines bound elapsed compute. No automatic cache
resume/re-download is implemented: preserve an incomplete cache and report it.
An already complete cache may be independently verified under a later recorded
reuse decision, rather than deleting it to make `fetch` accept an existing path.

## Pass criteria and what follows

- All 15 files match their recorded size and correct hash algorithm; no extra
  snapshot file or cache-escaping link is accepted.
- The exact validated package versions and A10G host profile still match.
- The loaded model reports `qwen3`, actual NF4 modules, and all parameters on
  CUDA; peak allocated/reserved VRAM and load time are recorded.
- Receipt records zero inference calls, optimizer steps and adapter creation.
- Logs are preserved and the owned host is confirmed stopped within the cap.

A pass advances model-loading readiness only. An OOM, missing dependency, hash
failure, unexpected quantization or offline-cache miss ends the session for
review. It does not authorize changing the model, checkpoint, context, runtime
or hardware to obtain a pass. S0-cases/S0-retrieval, accepted data, the bounded
QLoRA/checkpoint/resume test, and second-operator reproduction remain distinct
gates. Diagram training remains blocked and the optional helper contest deferred.

Upstream behavior was checked against the pinned library wheel sources and
[Hugging Face's download guide](https://huggingface.co/docs/huggingface_hub/guides/download).
Offline rehearsal results are recorded with this packet; none is a claim that
the 8B model has already loaded on the A10G.

[Preparation validation receipt](evidence/aws-runtime-bundle-2026-09-28/qwen-load-preparation-2026-09-29.json):
36 checkpoint tests passed within the full Foundry result of **850 passed,
3 skipped**. The guest shell and local PowerShell blocks were syntax checked
without executing their commands. GPU/library boundaries use test doubles;
actual checkpoint loading remains the purpose of the separately scoped session.
