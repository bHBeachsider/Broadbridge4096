# Next AWS session: reuse the verified Qwen checkpoint

The existing A10G already passed runtime and Qwen3-8B loading. Its 15 verified files (16,397,438,697 bytes) remain on the retained disk. No new model download is necessary. See the [successful result](QWEN_MODEL_LOAD_RESULT_2026-09-30.md).

This delivery makes the next load session reproducible from Foundry source and [Broadbridge configuration](../infra/gpu/model-load-reuse.json). It is preparation, not a second AWS execution or training result. A repeat load is useful for qualifying the tracked controller or another operator; it should not become a recurring hardware test while dataset decisions are pending.

## Prepare locally

Use the two existing `codex/aws-training-readiness` checkouts. Commit reviewed changes before preparing an executable packet; a dirty packet can be inspected but execution is refused. Run in Windows PowerShell with the existing CPU Python environment:

```powershell
$domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-plan'
$session = Join-Path $foundry ('outputs\qwen-reuse-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$pins = Join-Path $foundry 'outputs\runtime-a10g-retry-20260929-1920\known_hosts'
$operatorKey = Read-Host 'Local SSH private-key FILE PATH (not its contents)'
$lockFile = Join-Path $foundry 'outputs\broadbridge-gpu-session.lock'
python "$foundry\scripts\model_load_packet.py" --config "$domain\infra\gpu\model-load-reuse.json" --inventory "$domain\docs\evidence\aws-runtime-bundle-2026-09-28\qwen-base-inventory.json" --host-keys $pins --ssh-key $operatorKey --lock-file $lockFile --domain-root $domain --out $session
if ($LASTEXITCODE -ne 0) { throw 'Packet preparation failed; do not execute.' }
$packetDigest = (Get-FileHash (Join-Path $session 'packet.json') -Algorithm SHA256).Hash.ToLowerInvariant()
python "$session\model_load_session.py" --session-dir $session --packet-sha256 $packetDigest
if ($LASTEXITCODE -ne 0) { throw 'Packet check failed; do not execute.' }
```

Expected: `prepared`, then `packet-verified`, both with `execution_authorized: false` and `model_download_bytes: 0`. These commands do not call AWS, SSH or Qwen. They do not read `.env`, databases, R2 or customer records. The source archives contain only explicit runtime-check scripts/manifests and the model inventory.

The pins are from the **actual successful A10G `known_hosts`**, SHA-256 `87ac13d4c985765a06143abde42274f5aae66eb76aee24e702c7b07bc835fb4e`. Do not substitute that old directory's `previously_verified_host_keys`. Another operator needs the trusted public-key file and their own approved local SSH key through the existing secure handoff; neither is obtained by accepting whatever a new network scan returns. Keep all packets and private logs ignored.

## Execution after a fresh decision

Review the exact packet digest, selected host, source commits and scope with Brad. The earlier successful packet's approval and deadline are not reused. Confirm the old automation remains paused, no local controller/lock exists and no other operator owns a retained GPU. A local lock cannot establish ownership on another PC.

Only for that approved packet, within 24 hours of preparation:

```powershell
python "$session\model_load_session.py" --session-dir $session --packet-sha256 $packetDigest --execute
```

This makes at most one start request for **i-079b24e2b51ef7630**. It checks all three retained Broadbridge hosts and account G/VT conflicts; it never starts a replacement. AWS quota/capacity/authorization errors are classified, and an ambiguous response is reconciled under the original deadline. It preserves source/config/host identities, busy-GPU diagnostics, 80-minute guest stop, 85-minute API stop, forced-stop fallback by minute 87 and stopped-state verification by minute 90. Keep the local PC awake and connected. No shutdown guarantee is possible during simultaneous loss of AWS/guest/local control.

The retained cache is checked against the exact inventory before any model import. Missing or changed files fail without fetching, deleting or repairing them. The existing pinned runtime must match. A load must show NF4, context 2048, all parameters on CUDA, zero inference/optimizer steps and no adapter. All work stops before minute 78, even if unfinished. Failure/completion stops early; a capacity rejection is not an automatic retry instruction.

## Evidence and remaining work

Preserve private `session.json`, phase logs, watchdog receipt and any `model-result.json`. Publish a redacted result only after stopped state is independently confirmed. The tracked controller is currently qualified offline; its first live use and a genuinely independent second-operator run remain unproved. No AWS calls or model activity were needed to prepare it.

Then return to the [dataset/readiness gates](AWS_TRAINING_READINESS.md): accepted task/rights, engineering reference corrections, signed-case coverage and scored baseline, immutable family-separated release, and separately authorized QLoRA smoke/resume. Hardware loading success does not close those gates. The [fallback image plan](AWS_GPU_REUSE_AND_FALLBACK.md) remains prepared and blocked on a verified image; no AMI or replacement is created here.

## Offline validation result

Foundry full CPU suite: **940 passed, 12 skipped, 3 existing warnings**. The 107 focused session/diagnostic/launch-policy tests passed, including mocked success, busy preflight, capacity rejection, ambiguous start cleanup, changed boot, forced-stop timing, independent watchdog, immutable packets and failed cache verification. The packet tests were also rerun after making Bash fixture cleanup entirely pytest-owned (27 passed).

The 12 skips are optional pyDEXPI (9), C01 input (1), Docling (1) and opt-in local PostgreSQL (1). Existing Requests/SWIG warnings remain. Domain JSON, relative links, whitespace and both generated Bash scripts passed checks. All 11 artifacts pinned by the successful historical session packet retain their recorded hashes. The new tools prepared and checked a real-config local packet with zero AWS/SSH/model calls; it initially recorded the in-progress source state and could not execute. A fresh clean-source packet can be generated after these commits. [Validation receipt](evidence/aws-capacity-2026-09-30/cache-reuse-preparation.json).
