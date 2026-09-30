# A10G runtime qualification session

29 September 2026. This is the concrete one-host fallback to the repeated L4
capacity failures. It qualifies the existing runtime candidate on another GPU;
it does not download Qwen weights, load a model, run a dataset or train an adapter.
The existing L4 machines and the prepared replacement disk stay intact.

## Latest execution result: A10G runtime checks passed

Brad's subsequent **"keep trying"** authorized sequential alternate-zone attempts
within the original window. The first follow-up request, `g5.2xlarge` in
`us-east-1b` / `use1-az2`, succeeded at **19:20:33 UTC**. No further zone was
requested. Host **`i-079b24e2b51ef7630`** used the prepared private image
`ami-0a425c55dcc606687`, existing SSH-only security group, IMDSv2 and one
encrypted 200 GiB gp3 root (`vol-09fff6b5c32ddfc09`). The two L4 hosts stayed stopped.

The original **20:43:39 UTC / 4:43 p.m. Eastern** deadline was retained, measured
from the first 19:13:39 request, not reset by the successful launch. Guest shutdown
was armed for 20:33:38 UTC; the independent API watchdog retained its 20:38:39
deadline. The reviewed seven Python packages were installed from locked Amazon
Linux release `2023.12.20260918`; GCC was already present and no driver/OS upgrade
was performed. The runtime used a fresh isolated venv:
`~/slm-training/venv-a10g-a23670f4d161`.

The complete cached archive transfer finished at **19:57:02 UTC**; all installation
and checks finished at **19:59:12 UTC**. A graceful API stop was accepted at
19:59:15. After three minutes, the approved forced-stop fallback was requested
at **20:02:18**. **Stopped was confirmed at 20:03:41 UTC / 4:03 p.m. Eastern**,
50 minutes 2 seconds from the original request and about 40 minutes before the
hard deadline. Independent inventory confirms all three hosts stopped. The disks
and source image are retained; EBS storage costs continue while instances are stopped.

| Check | Actual result |
| --- | --- |
| Host | A10G, capability 8.6, 23,028 MiB VRAM; driver 595.91.07; Python 3.11.16; glibc 2.34 |
| Install and integrity | 113 wheels / 3,792,751,006 bytes verified; all 113 installed versions matched; pip consistency passed |
| FP16 matrix multiplication | Passed; relative L2 error 0.0002065 (<0.002) |
| BF16 matrix multiplication | Passed; relative L2 error 0.0016482 (<0.015) |
| Triton JIT | Vector add passed against PyTorch |
| bitsandbytes NF4 | Round-trip relative L2 error 0.0944532 (<0.2) |
| xformers attention | Passed against CPU reference; maximum absolute error 0.0004722 |
| Foundry CPU tests on this venv | **149 passed, 0 failed, 0 skipped**, 5.89 seconds |

The five probes used fabricated tensors, with peak allocated GPU memory of
8,656,384 bytes. This is a small-kernel compatibility test, not an estimate of
Qwen memory use or engineering accuracy. PyTorch/Unsloth emitted deprecation
warnings about Enum registration and `inline_inbuilt_nn_modules`; no failing
checks occurred. Do not upgrade dependencies to suppress those warnings here.

Status: **RUNTIME_CHECKS_PASSED_WAIT_MODEL_AND_DATA**. This closes the runtime-only
installation/kernel task on this exact A10G environment. It does not qualify
the L4 environment or prove Qwen model load, QLoRA, checkpoint/resume, a domain
adapter, or second-operator reproduction. The static host-profile contract still
says `qualified: false`; a host preflight alone never certifies a runtime. The
separate execution receipt records the passed checks.

The run used Foundry source `395ab994220ab7398b63ca383b8dc465c61aae13` and the
domain plan at `47879aa5a763693433bab56f31d4c3a39cb7e5a5`. Later documentation
commits do not rewrite those bindings. [Redacted validation receipt](evidence/aws-runtime-bundle-2026-09-28/a10g-validation-2026-09-29.json)
records actual metrics, private log/script hashes, original deadline and stopped
inventory. Raw logs remain ignored in the Foundry
`outputs/runtime-a10g-retry-20260929-1920/` directory. No model weights were
downloaded, no model was loaded or called, and no training, database/R2 operation,
production change or merge occurred. The capacity retry automation stays paused.

## Initial attempt: capacity rejected

Brad explicitly requested execution. At **19:13:39 UTC / 3:13 p.m. Eastern** on
29 September, the prepared launcher made one RunInstances CLI invocation for
`g5.2xlarge` in `us-east-1a`, with `AWS_MAX_ATTEMPTS=1` and standard retry mode.
AWS returned **InsufficientInstanceCapacity** at **19:13:44 UTC**. No second
request, alternate zone or different type was attempted.

Independent DescribeInstances checks at **19:14:34 UTC** found zero instances
under the request's client token or validation-host tag. Both existing L4 hosts
remained stopped with their earlier boot times unchanged. No new resource or
compute session was observed; no transfer, prerequisite installation, runtime
installation, GPU checks, host CPU tests, model call or training occurred.

At that initial checkpoint, runtime status was **RUNTIME_BLOCKED_CAPACITY**. The launch retry policy was
configured explicitly; the CloudTrail service-request count has not yet been
independently audited. The original 90-minute deadline was 20:43:39 UTC, but no
host started. This failed one-request session is closed, not a running task or
an automatic retry. Preserve its files and use a new explicit session decision
before any further launch. [Attempt receipt](evidence/aws-runtime-bundle-2026-09-28/a10g-attempt-2026-09-29.json).

## Original prepared configuration (before the authorized alternate-zone retry)

| Item | Bound configuration |
| --- | --- |
| Instance | One new On-Demand `g5.2xlarge`, NVIDIA A10G, 8 vCPU / 32 GiB RAM |
| Placement | `us-east-1a`, subnet `subnet-033fb0054024b8868`; one RunInstances request, no zone sweep |
| Image | Existing private `ami-0a425c55dcc606687`, copied from the stopped original |
| Storage | One new encrypted 200 GiB gp3 root, 3,000 IOPS / 125 MiB/s; retain after stop for inspection |
| Network | Existing `sg-00c7894c78785b6c3`, SSH only; IMDSv2 required; no instance profile or model API exposure |
| Host profile | Foundry `infra/training/profiles/g5-a10g.json`; exact A10G / capability 8.6 / one GPU |
| Runtime | Unchanged 113-wheel CPython 3.11 / CUDA 12.6 bundle; 3,792,751,006 bytes |
| Wheel inventory hash | `a23670f4d161c03466798f1a4bd548b5bf37c0d3740726aa6ac338533e8abdea` |
| Compute ceiling | 90 minutes from the first launch request; at the recorded $1.212/hour, at most $1.818 of instance compute |
| Additional costs | EBS, public IPv4 and any transfer/tax charges are separate; retained EBS continues billing after stop |

The source image predates the replacement's Python installation and incomplete
upload. This host needs the reviewed Python prerequisites and a full upload of
the locally cached wheels. No fresh wheel download is necessary. Capacity is
unknown until AWS accepts the actual launch; instance offerings are not a
capacity reservation.

## Execution order and acceptance

1. Confirm the original `i-0e5e1cbc7b1367566` and replacement
   `i-0439f5841d631d9f8` are stopped and no G/VT host is running or pending. Keep
   the capacity retry automation paused. Verify the image is private and the
   existing group exposes only SSH.
2. Verify the exact wheel/profile/archive hashes and save repository commits.
   The private prepared package is Foundry
   `outputs/runtime-a10g-prep-20260929/`. Preserve earlier session directories.
3. Make exactly one RunInstances request with a unique client token and
   `AWS_MAX_ATTEMPTS=1`, standard retry mode. A timeout triggers token/state
   reconciliation; it never grants permission for another launch. A rejected
   request or changed ownership ends the attempt.
4. Bind the returned instance ID, boot time, image, type and zone to the receipt.
   Start the independent 85-minute API stop watchdog. Resolve the IP from AWS,
   validate SSH identity against previously trusted image keys or the AWS
   console fingerprint, and cross-check guest identity through IMDSv2.
5. Verify instance-initiated shutdown is `stop`. Arm and verify the guest timer
   for minute 80 before any installation. The absolute 90-minute budget never
   resets; forced-stop fallback begins by minute 87, or after three minutes of
   unsuccessful graceful stopping, leaving time to verify stopped state.
6. If Python 3.11 is absent, inspect the transaction on locked Amazon Linux
   release `2023.12.20260918`. Only the previously reviewed seven packages are
   candidates: Python/interpreter-libs/headers `3.11.16-1.amzn2023.0.1`, pip and
   pip-wheel `22.3.1-2.amzn2023.0.14`, setuptools and setuptools-wheel
   `65.5.1-2.amzn2023.0.7`. Require the existing GCC, GPG checks and no weak
   dependencies. A different transaction, missing compiler or driver problem
   requires a report; do not improvise upgrades or extend the deadline.
7. Require exact GPU/driver/Python/glibc facts, no active GPU workload and at
   least 64 GiB free. Upload the hashed archives by SFTP with any retained prefix
   validated first. Transfer cutoff is minute 65. Keep Windows stdin binary and
   Bash files LF. Refuse a transfer estimate that consumes the installation margin.
8. Install from verified wheels into a fresh isolated
   `~/slm-training/venv-a10g-a23670f4d161`, with no package index or source builds.
   Check installed versions and pip consistency. Run the A10G host gate, imports,
   FP16/BF16 matrix comparisons, Triton JIT, NF4 round-trip, xformers attention,
   and selected CPU tests. Stop work by minute 78 even if incomplete.
9. Stop immediately on completion or failure, preserve private logs and a
   redacted receipt, and verify the exact owned instance is stopped. Do not
   delete retained disks/images or stop a later operator's boot.

A passing host gate is not a passing CUDA runtime. A passing runtime is not a
successful model load, QLoRA smoke test, domain evaluation or approved training
release. Report each of those states separately.

## Preparation evidence

The Foundry profile and subprocess-policy tests run offline. Private launch and
transfer tests use mocked AWS and a local SFTP server. Both existing L4 machines
were reconfirmed stopped during preparation, with unchanged boot times. All 113
cached wheels passed size/SHA-256 checks again. See the accompanying evidence
receipt for exact test counts, hashes and the final execution disposition.

The prior Technical route was blocked by Basic Support. A later account case,
`179070520900642`, is now confirmed Unassigned under Service Quotas, General;
no AWS reply is visible. No support-plan purchase is required for this
single-host fallback. See [capacity assessment](AWS_GPU_CAPACITY_OPTIONS_2026-09-29.md).
