# GPU capacity alternatives and AWS escalation

**Latest result, 29 September 20:03 UTC:** the approved A10G retry in
`us-east-1b` succeeded. All 113 pinned wheels installed and matched; `pip check`,
five synthetic GPU probes and **149 selected CPU tests** passed. The A10G and
both retained L4 hosts are independently confirmed stopped. Runtime installation
and small-kernel checks are complete; Qwen weight staging/model load, accepted
data/baselines, QLoRA smoke/resume and second-operator reproduction remain open.
No model inference or training ran. [Session result](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).
Earlier dated entries below preserve the capacity/transfer history.

**Later update:** account case [179070520900642](https://console.aws.amazon.com/support/home#/case/?displayId=179070520900642&language=en)
is now confirmed **Unassigned**, under Service Quotas, General. No AWS reply is
visible. The earlier technical-route rejection below remains the history of that
attempt. The separate A10G profile and local tests are prepared; see the
[concrete bounded-session plan](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).

29 September 2026. Brad authorized qualification of alternative GPU types/regions and escalation of the repeated capacity errors to AWS Support. This assessment made read-only AWS calls. It did not start, resize or replace an instance, purchase support, reserve capacity, request a quota increase, or run a model. Both existing hosts and the prepared replacement disk are preserved.

## Recommendation

The first alternative to qualify on hardware is **g5.2xlarge in us-east-1**. It changes the GPU allocation pool from L4 to A10G while retaining x86-64, 8 vCPUs, 32 GiB RAM and a GPU in the marketed 24 GB class. The regional quota already permits one. This is a hardware/specification assessment, not a passed CUDA or training qualification, and an instance offering is not evidence of presently free capacity.

Keep the prepared L4 replacement intact. Do not resize it just to probe availability. A later approved fallback can use a separate host, with one running GPU host at a time and the same bounded shutdown controls. A private image from the original stopped host already exists, but **does not include the replacement's later Python installation or partial runtime upload**. Reusing that image would require repeating the reviewed prerequisites and transferring the locally verified bundle; do not assume the replacement preparation is in that image.

## Account and hardware checks

AWS API results were collected on 29 September; the [evidence receipt](evidence/aws-runtime-bundle-2026-09-28/capacity-options-2026-09-29.json) contains timestamps, specifications, offerings, prices and selected CloudTrail request IDs.

| Option | GPU | vCPU / RAM | Linux On-Demand USD/hour | 90-minute compute estimate | Disposition |
| --- | --- | --- | ---: | ---: | --- |
| Existing g6.2xlarge, Virginia | L4, marketed 24 GB | 8 / 32 GiB | 0.9776 | 1.4664 | Resume prepared replacement if capacity returns |
| g5.2xlarge, Virginia | A10G, marketed 24 GB | 8 / 32 GiB | 1.2120 | 1.8180 | Preferred different-GPU fallback; quota permits one; runtime profile/checks pending |
| g6e.xlarge, Virginia | L40S, marketed 48 GB | 4 / 32 GiB | 1.8610 | 2.7915 | Secondary fallback; fewer CPU cores, more VRAM, higher cost; runtime profile/checks pending |
| g6.2xlarge, Ohio | L4 | 8 / 32 GiB | 0.9776 | 1.4664 | GPU quota is zero; requires quota approval and region setup |
| g6.2xlarge, Oregon | L4 | 8 / 32 GiB | 0.9776 | 1.4664 | GPU quota is zero; requires quota approval and region setup |

Prices came directly from AWS Price List `GetProducts`, Linux/shared tenancy/no preinstalled software, effective 1 September 2026. Estimates cover compute only; retained EBS/snapshots, public IPv4, transfer and taxes are additional. The g5 premium over g6 for 90 minutes is **$0.3516**. No live throughput comparison has been performed.

The `Running On-Demand G and VT instances` quota (`L-DB2E81BA`) is **8 vCPUs in us-east-1**, **0 in us-east-2**, and **0 in us-west-2**. Read-only inventory found no running/pending G/VT instances in those regions. A regional quota increase would permit requests; it would not reserve hardware.

In this account, g5.2xlarge and g6.2xlarge are offered in Virginia zones a/b/c/d/f. G6e.xlarge is offered in a/b/c/d. The Ohio and Oregon offerings are recorded in the receipt. `DescribeInstanceTypeOfferings` lists supported locations, not available GPU inventory. No start, RunInstances dry run, or Spot placement score was used to claim capacity availability.

AWS describes the L4 and A10G configurations as 24 GB; its instance-type API reports 22,888 MiB for each, and 45,776 MiB for L40S. Actual usable memory must be measured on the selected host. The existing L4 previously reported 23,034 MiB via nvidia-smi. These different reporting surfaces must not be substituted for measured training memory headroom.

The private source AMI is available, private, x86-64/HVM, EBS-backed, ENA-enabled and UEFI-preferred. G5/G6/G6e support the required architecture and boot modes. This establishes metadata compatibility only; guest boot and the installed driver remain untested on A10G/L40S.

## Runtime qualification required before a paid fallback

The unchanged pinned bundle targets Linux x86-64, CPython 3.11, glibc >=2.34 and CUDA 12.6. The 113 cached wheels total 3,792,751,006 bytes; retain manifest SHA-256 `a23670f4d161c03466798f1a4bd548b5bf37c0d3740726aa6ac338533e8abdea`.

Foundry `scripts/training_bundle.py::assess_host` and `infra/training/wheels.json` explicitly require **NVIDIA L4**. Three offline probes using invented host facts confirmed: L4 passes the current host gate; A10G and L40S are rejected with `gpu`. No checks were loosened. NVIDIA lists L4/L40S at compute capability 8.9 and A10 at 8.6; changing GPU family requires fresh kernel validation, even if the wheels can be reused.

Before starting a different GPU:

1. Create a separately reviewed host profile for the exact GPU/type and test acceptance/rejection, preserving the L4 profile and historical manifest. Record a distinct profile digest bound to the unchanged wheel inventory. Do not bypass the existing GPU check or mark the runtime qualified from specifications.
2. Amend the private session controller's exact host/type/zone identity guard and guest GPU expectation. Set `AWS_MAX_ATTEMPTS=1` for **StartInstances/RunInstances** calls so one requested attempt is one service request. Do not suppress the bounded describe/stop recovery needed for cleanup. Test request counting and ambiguous outcomes offline.
3. Approve the specific one-host fallback, provisioning/storage approach and 90-minute compute ceiling. Keep the prepared replacement and original stopped. No fleet, driver upgrades, floating bootstrap, model weights, inference, fine-tuning or dataset work belongs to the runtime session.
4. Resolve the AWS address, establish trusted SSH identity and IMDSv2 guest identity, verify the exact GPU/driver/OS/prerequisites/disk, and arm the 80-minute guest guard plus independent 85-minute API fallback before installation. Preserve the 90-minute absolute deadline and final stopped-state verification.
5. Verify the cached wheel and transfer archive hashes, install into a fresh isolated venv, and run the prepared import, FP16/BF16, Triton, bitsandbytes NF4, xformers and selected CPU tests. Record GPU name/compute capability/driver and actual results. Stop on failure; do not improvise a driver or dependency upgrade.
6. Preserve receipts and stop. Model-weight staging, dataset acceptance, QLoRA smoke and domain training remain separate gates.

For an eventual cross-region alternative, first obtain a quota of at least 8 G/VT vCPUs, review private AMI copying and storage charges, and recreate the minimum SSH/IMDS/network configuration in the target region. Resources and quotas are regional; an Ohio/Oregon catalog listing is not a ready deployment.

## Support escalation and corrected request count

AWS Support `DescribeServices` and `DescribeSeverityLevels` both returned `SubscriptionRequiredException`. The API requires an eligible support subscription. After sign-in and explicit approval of the exact payload, AWS received the report in its automated Support intake (interaction `0ca2dd14-33a4-4dec-8ecc-c90d368c465b`). The console confirmed Basic Support and rejected the Technical case type: **"Technical case type is not available for your support plan."** A draft was saved, but no human support case number or engineer response exists. No paid plan/trial was purchased. See the [submission and limitation](AWS_SUPPORT_CAPACITY_CASE_2026-09-29.md).

CloudTrail confirms the failures as **Server.InsufficientInstanceCapacity**. It also corrects the earlier wording: the 16:47 attempt made **two CLI invocations, which produced six service requests** (three per host), consistent with automatic CLI retries. The controller has no explicit retry loop for selection, but its subprocess inherited AWS retry behavior. All six requests failed; no host started. Earlier receipts remain unchanged; this is the additive audit correction. Future start calls must explicitly disable implicit retries as described above.

Latest selected service request IDs:

| UTC on 29 September | Instance / AZ ID | Request ID | Result |
| --- | --- | --- | --- |
| 16:47:23 | Replacement / use1-az4 | 056839a0-e6d4-418d-943d-403ee0dd2cf1 | InsufficientInstanceCapacity |
| 16:47:24 | Replacement / use1-az4 | adc5e7ff-192c-4ea9-b7a4-ed07b489b9e6 | InsufficientInstanceCapacity |
| 16:47:26 | Replacement / use1-az4 | 51f4a74f-7972-42f4-a474-47db70b8c3dc | InsufficientInstanceCapacity |
| 16:47:33 | Original / use1-az6 | acbee627-0f71-4e1b-a0e5-3a95d95c601e | InsufficientInstanceCapacity |
| 16:47:35 | Original / use1-az6 | 1b9c9fe6-20a7-4df4-b499-1d4e10cbf172 | InsufficientInstanceCapacity |
| 16:47:37 | Original / use1-az6 | fe276ed1-778e-4501-9abf-af8ba9e5fa5a | InsufficientInstanceCapacity |

Runtime status stays **RUNTIME_BLOCKED_CAPACITY**. The later account case is open and Unassigned; the Technical route remains unavailable under Basic Support. A10G now has an offline-tested candidate profile and prepared session package, but no hardware validation. The original and replacement remain stopped with unchanged launch times, and automatic retries remain paused.

## References

- [AWS capacity-error meaning and alternatives](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/troubleshooting-launch.html)
- [AWS instance offerings API](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instance-type-offerings.html)
- [AWS G5](https://aws.amazon.com/ec2/instance-types/g5/) and [G6e](https://aws.amazon.com/ec2/instance-types/g6e/)
- [NVIDIA compute capabilities](https://developer.nvidia.com/cuda/gpus)
- [AWS Support API eligibility](https://docs.aws.amazon.com/awssupport/latest/APIReference/API_CreateCase.html)
- [AWS CLI retry configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-retries.html)

## 29 September 19:13 UTC: A10G validation attempt

The approved one-request A10G validation attempt was rejected with
`InsufficientInstanceCapacity` for `g5.2xlarge` in `us-east-1a`. Independent
inventory confirmed no created A10G instance and both L4 hosts still stopped.
No GPU validation or installation ran. The session is closed; no automatic
retry is active. [Result and receipt](AWS_A10G_RUNTIME_SESSION_2026-09-29.md).
