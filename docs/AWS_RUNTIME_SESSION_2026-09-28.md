# Approved runtime session: 28 September 2026

Session began on 28 September in New York / 29 September UTC. **The runtime bundle is downloaded and verified, but the candidate has not been installed or GPU-qualified.** AWS returned `InsufficientInstanceCapacity` when restarting the existing host after connection/preflight corrections, including the delayed retry. Final stopped state was confirmed at **04:14:42 UTC**, **25 minutes 41 seconds** after the original start request, inside the approved 90-minute window. See the [machine-readable receipt](evidence/aws-runtime-bundle-2026-09-28/session.json).

## Scope and prepared artifacts

Brad explicitly approved the **3.79 GB runtime download, EC2 installation and GPU checks, with shutdown within 90 minutes**. The approved host is `i-0e5e1cbc7b1367566`, `g6.2xlarge`, `us-east-1`; its recorded AMI is `ami-0d17cf0308b8d1589`. No substitute instance, availability zone, instance type or fleet was created.

The candidate remains Unsloth 2026.9.12 / Zoo 2026.9.8, Transformers 5.5.0, TRL 0.24.0, torch 2.12.1+cu126 and Python 3.11. Transformers 5.9.0 in the local CPU environment was not changed. The exact source snapshots were Foundry `4a9ccfc443efbd4e9b81bfc3536e08241e93b1d5` and Broadbridge `7bec91db925e395c5d149c1e29df27eda40cc1ff`.

| Evidence | Result |
| --- | --- |
| Manifest SHA-256 | `a23670f4d161c03466798f1a4bd548b5bf37c0d3740726aa6ac338533e8abdea` |
| Actual wheel download | **113 files; 3,792,751,006 bytes** |
| Verification | Each wheel's recorded length and SHA-256 matched during fetch and an independent subsequent `verify` run |
| Source transfer archive | Selective tracked runtime code/config/tests; 104 entries, no credentials, model weights, domain datasets or output directories |
| EC2 shutdown behavior | Read and confirmed `stop`, not terminate; API stop protection false |
| SSH / guest identity | Existing PC-trusted public keys matched the AWS-resolved address; read-only IMDSv2 returned the expected instance ID before a guest mutation |
| On-host timer | Active; scheduled for **05:09:02 UTC**, approximately 80 minutes from the original session start |
| Candidate installation | **Not performed** |
| Actual driver, Python, CUDA kernels | **Not qualified**; do not infer a pass from EC2 instance type or the working Ollama installation |
| Model weights / inference / optimizer steps | None / none / zero |
| Database, R2, production | No operations |

The wheelhouse is private and ignored at `outputs/training-wheelhouse-cu126` in the selected Foundry checkout. Private operational scripts, archive hashes, logs and per-attempt receipts are retained at `outputs/runtime-session-20260929`. They are not uploaded to Git. Reuse the verified wheelhouse on the next authorized host session; do not fetch it again.

## What happened and what was corrected

The first attempt could not obtain host-key fingerprints from EC2 console output and stopped before SSH installation. The fallback was narrowed to two exact keys already trusted on the PC, with a guest IMDSv2 identity check. This is recorded as local trust continuity and guest identity, not as an AWS-signed binding of the SSH key. The instance's public IP is resolved on every start and is not pinned in code or documentation.

The second attempt authenticated, confirmed the instance ID and armed the on-host timer. Its Bash preflight failed immediately because Windows text-mode subprocess stdin converted LF to CRLF (`set: pipefail: invalid option name`). No package or runtime archive reached the host. The transport now sends UTF-8 bytes, and the scripts have canonical LF endings. A local regression test verified the exact stdin bytes; both shell scripts passed `bash -n`.

Normal stopping remained in `stopping` for several minutes. Force-stop fallbacks were used before retrying, including guest shutdown bypass on the second attempt. No model, training or dataset work was active. The first two attempts were confirmed stopped at **04:00:30 UTC** and **04:07:02 UTC** respectively. This observed delay supports the need for an off-host stop fallback; a guest-only idle timer is insufficient for unattended use.

Subsequent start requests were rejected by AWS capacity availability. Retries retained the **original 03:49:01 UTC start budget and 05:19:01 UTC maximum deadline**. They did not reset the approved 90-minute window. Installation and GPU validation therefore remain incomplete; this is not a qualified runtime release.

## Verification and limits

- Wheel fetch and separate full size/hash verification: **113/113 passed**, exact approved byte count.
- Existing bundle/transfer tests: **30 passed**, one existing Requests dependency warning, using the unchanged local CPU environment. The initial sandboxed attempt had 19 fixture-setup permission errors in pytest's shared temp directory; the rerun used a fresh writable temp directory. No tests were altered.
- Five mocked cleanup scenarios covered graceful stop, changed-boot refusal, forced fallback, expired deadline and a slow-describe deadline regression. The binary-stdin regression also passed. These are local operational checks, not proof of every AWS failure mode.
- Both Bash scripts passed syntax checks and both Python operational files parsed. Small FP16/BF16, Triton, NF4 and xformers probes are prepared but **have not run on the GPU**.
- Independent review identified shutdown deadline accounting, ownership and SSH-trust concerns. Cleanup calls were bounded against the remaining budget, boot ownership checked, host trust narrowed and retry phase budgets corrected. Cloud capacity and actual native runtime compatibility remain unresolved.

## Next action

**29 September follow-up:** Brad approved retrying the existing L4 when capacity returns. The 113 cached wheels were re-verified without another download. A fresh bounded start attempt at **04:29:31 UTC** again returned `InsufficientInstanceCapacity`; stopped state was confirmed at **04:29:38 UTC**. No installation or GPU checks ran. See the [retry receipt](evidence/aws-runtime-bundle-2026-09-28/retry-2026-09-29.json).

The thread heartbeat **Retry Broadbridge L4 runtime** is now active hourly. It makes one existing-host start attempt per run, keeps unchanged capacity failures quiet, and pauses after the first successful start or a new blocker. A successful start may execute only the approved runtime installation/checks with a fresh maximum 90-minute shutdown bound. It must preserve earlier evidence, reuse the verified bundle, refuse to take over another operator's running host and report actual qualification results. No replacement capacity, weights or training are authorized.

For the now-approved retry, verify the local wheelhouse, arm the shutdown guards, inspect Linux/Python 3.11/ensurepip/Python.h/gcc/driver/disk, install into a fresh isolated venv from the hash-enforced offline lock, then run the small synthetic GPU checks and selected Foundry CPU tests. Do not reuse an incomplete environment as qualified. Record and address any actual host prerequisite gap before broadening the installation.

The separate **16,397,438,697-byte Qwen checkpoint download**, accepted dataset, S0 results, QLoRA smoke/resume and domain fine-tuning remain gated. This session does not approve them. See [setup procedure](AWS_TRAINING_SETUP.md), [readiness and data gates](AWS_TRAINING_READINESS.md) and [cost-control review](EC2_COST_GUARDS.md).
