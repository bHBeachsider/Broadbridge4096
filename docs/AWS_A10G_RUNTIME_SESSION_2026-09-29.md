# A10G runtime qualification session

29 September 2026. This is the concrete one-host fallback to the repeated L4
capacity failures. It qualifies the existing runtime candidate on another GPU;
it does not download Qwen weights, load a model, run a dataset or train an adapter.
The existing L4 machines and the prepared replacement disk stay intact.

## Execution result: capacity rejected

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

Runtime status remains **RUNTIME_BLOCKED_CAPACITY**. The launch retry policy was
configured explicitly; the CloudTrail service-request count has not yet been
independently audited. The original 90-minute deadline was 20:43:39 UTC, but no
host started. This failed one-request session is closed, not a running task or
an automatic retry. Preserve its files and use a new explicit session decision
before any further launch. [Attempt receipt](evidence/aws-runtime-bundle-2026-09-28/a10g-attempt-2026-09-29.json).

## Prepared configuration

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
