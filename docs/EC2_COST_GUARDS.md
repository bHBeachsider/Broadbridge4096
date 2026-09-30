# EC2 cost guards: review of the shutdown proposal

**29 September A10G validation:** all five GPU probes and 149 CPU tests passed.
The 19:13:39 UTC start-request deadline remained fixed after an alternate-zone
launch at 19:20:33. Graceful stop was accepted at 19:59:15; the approved three-minute
forced-stop fallback was requested at 20:02:18; stopped was confirmed at 20:03:41,
before the 20:43:39 hard deadline. All three GPU hosts are stopped and the retry
automation is paused. Retained disks continue to incur storage charges.
[Exact session and evidence](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).

Reviewed 28 September 2026 (America/New_York). Scope: the existing Broadbridge Qwen3-8B EC2 workstation. This is a review and staged recommendation, not authorization to create ECS, an Auto Scaling group, an IAM role, a new bucket or a persistent alarm.

**29 September relocation:** Brad separately approved one replacement L4 in another availability zone, then explicitly approved its missing Python prerequisites and a further start within the original deadline. The same 80/85/90-minute safeguards apply to that recorded replacement boot. The source stays stopped. See [the relocation record](AWS_RUNTIME_RELOCATION_2026-09-29.md) for the exact identities, retained storage and execution outcome; this does not create a standing permission for replacement instances or repeated paid retries.

## Decision

Use a fixed session deadline now, explicit stop on completion/failure, and verified stopped state. Add workload-aware idle detection only after testing it against this actual host. Do not install the proposed CPU alarm and shell watchdog unchanged.

Brad approved the **3,792,751,006-byte runtime download, EC2 installation and GPU checks with shutdown within 90 minutes**. The runtime is separate from the 16.4 GB Qwen checkpoint, datasets and fine-tuning, which are outside this session. Runtime session results are recorded separately in `AWS_RUNTIME_SESSION_2026-09-28.md`.

## What needs correction

| Proposal | Assessment | Required change |
| --- | --- | --- |
| Stop when CPU stays below 3% for 30 minutes | Low CPU can occur during legitimate GPU work, I/O waits and some downloads. This independent alarm would stop the host even when the separate GPU watchdog considers it busy. | Do not give a CPU-only alarm a stop action. CPU is supporting telemetry, not the decision authority. |
| Poll vLLM on port 8000 for Qwen3.5-4B | Current serving is Qwen3-8B through Ollama on loopback 11434; the host is Amazon Linux 2023. The proposed assumptions do not match it. | Inspect the actual services and GPU processes. Keep 11434 private. Do not introduce vLLM or change the base model as part of cost control. |
| Treat failed/missing request metrics as zero | A broken collector becomes an apparently idle host. | Missing telemetry means UNKNOWN; alert and retain the independent absolute deadline. Apply bounded command/network timeouts. |
| Find training with broad `pgrep` patterns | Names can miss or falsely match jobs. Installation, transfer, checkpointing and backup also need protection. | Track explicit job IDs, owned processes/services, phase and expiring busy leases. No process-name guess should be the sole authority. |
| Count minutes in a shared `/tmp` file | Concurrent invocations, stale state after reboot and delayed polls can corrupt the result. | Use a single locked service, restricted state, boot ID and elapsed monotonic time; reset on activity or unknown telemetry. |
| ECS starts exactly one instance and terminates exactly 15 minutes after work | The ASG maximum caps capacity; AWS otherwise documents a two-instance initial scale-out from zero. Neither establishes the claimed timing. Scale-in includes metric datapoints and other delays, and a long-running inference task can keep capacity occupied. | Treat ECS as a separate future design and measure its behavior under the chosen limits. Set task demand to zero explicitly where appropriate; do not assume zero requests ends a task. |
| ECS scales this workstation down like stopping it | Auto Scaling terminates surplus instances. That changes persistence and recovery assumptions. | Externalize immutable artifacts and checkpoint backups first; review volume deletion policy. Keep standalone EC2 for this pilot. |
| g6.2xlarge has 25 Gbps and pulls 8 GB in four seconds | AWS lists **up to 10 Gbps** for g6.2xlarge. End-to-end download/start times need measurement. | Budget startup, registry/model download, verification, installation and cleanup separately. No guaranteed cold-start number. |
| Stopping eliminates all cost | For an ordinary stop, instance compute billing ends on entry to `stopping`; EBS and other retained resources can still cost money. Instance-store contents do not survive stop. | Track retained storage separately. Keep needed artifacts on durable storage and verify backups before stopping where required. |

AWS references: [alarm stop actions and missing-data guidance](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/UsingAlarmActions.html), [ECS managed scaling behavior](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/managed-scaling-behavior.html), [EC2 stop/start and Auto Scaling termination](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html), [G6 specifications](https://aws.amazon.com/ec2/instance-types/g6/), [instance lifecycle billing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html).

## Current session control

1. Download and SHA-256-verify the wheel bundle on the PC before starting paid GPU time.
2. Record instance ID, original stopped state, start time and a single absolute 90-minute deadline. Read and require instance-initiated shutdown behavior `stop`.
3. Once SSH host identity is verified, arm a transient systemd shutdown timer for **80 minutes from session start**, before package installation. Verify the timer is active. Failed SSH/preflight/guard setup invokes immediate API stop.
4. A separate local watchdog requests an API stop at **85 minutes**, tied to the same instance boot. It must not extend the deadline. The main driver also stops the instance in its failure/completion path and verifies `stopped`. Cleanup API calls have bounded timeouts recalculated against the remaining budget. If graceful stopping has not succeeded, request forced stop with guest shutdown bypass at minute 87, leaving three minutes for verification. Forced stop can lose unsaved state; this fallback is for this isolated runtime-only session and must be reviewed alongside checkpoint safeguards before training. If AWS still fails to confirm a stop, report the failure immediately rather than claiming a guaranteed cloud completion time.
5. Run the isolated install and small synthetic kernel checks with individual timeouts. Never consume the final shutdown margin on retries, new experiments or model downloads.
6. Preserve private logs and a redacted receipt. Confirm stopped state before claiming completion. A failed runtime check is evidence to fix the candidate; it is not permission to upgrade a driver or widen dependencies.

These are session safeguards, not a guarantee against simultaneous loss of host control and the local PC/network. A cloud-side deadline would remove that local dependency and is recommended before unattended sessions. No permanent CPU-idle alarm or ECS infrastructure is installed by this review.

## Next unattended-session design

Use a one-time cloud-side deadline associated with an approved session ID and the exact instance boot. A narrowly scoped role can describe and stop only the intended instance, never terminate it. Create/verify the schedule before work; keep it effective through cleanup and reconcile/delete it after a confirmed stop. Alert on failure to stop and on missing heartbeats. Do not let an expired schedule stop a later operator's session.

One workload coordinator should own idle decisions. A job records its phase (`download`, `install`, `inference`, `training`, `checkpoint`, `backup`), owner/process identity, heartbeat and maximum lease end. An interactive operator can request a bounded lease. Leases never move the absolute approved deadline. Declare idle only after the queue is empty, no valid jobs/leases remain, expected metrics are healthy and both request/GPU activity remain below measured thresholds for a continuous grace interval. A 20-minute grace interval is a candidate, not a validated policy.

At the deadline, request graceful cancellation/checkpointing early enough to finish by the limit; stop even if workload remains. In the current runtime-only session there is no model checkpoint to save. Training sessions will need a separately tested checkpoint/backup grace window.

Before enabling automatic idle stops, test: active GPU with low CPU; large transfer; package installation; checkpoint/backup; active SSH lease; missing exporter; failed `nvidia-smi`; stale heartbeat; duplicate timer; reboot; changed instance boot; unreachable AWS API; successful early completion; and absolute deadline expiry. A lease expiry plus absent process can expose a stale job; failed telemetry alone cannot prove idle.

## What stays deferred

ECS capacity providers, an Auto Scaling group, serverless GPU migration and a new S3 design remain post-pilot options. The current artifact plan already uses private R2; cost control does not require changing it. Use measured run duration, peak disk/VRAM and queue demand to decide whether orchestration is worth its operational cost.
