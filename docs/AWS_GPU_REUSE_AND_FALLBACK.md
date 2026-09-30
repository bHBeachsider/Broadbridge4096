# AWS GPU reuse and fallback: prepared policy

30 September 2026. Brad approved proceeding with the capacity-review recommendations. This delivery prepares the generic safeguards and a concrete domain policy. It does not launch a host, create an AMI, request quota or authorize model work. The commercial explanation for Bill remains on its separate local branch.

## Current choice

Reuse **i-079b24e2b51ef7630**, g5.2xlarge/A10G, us-east-1b / use1-az2. Its existing pinned runtime and verified Qwen3-8B cache passed the [load check](QWEN_MODEL_LOAD_RESULT_2026-09-30.md). All four G-family instances visible in the fresh account inventory are stopped; three are retained Broadbridge hosts. The fourth belongs outside this session and is observed only for ownership conflicts.

The quota remains eight G/VT vCPUs. No quota-exceeded event established the prior capacity failures. AWS excludes pending and stopping from the documented On-Demand quota. We nevertheless require other GPU workloads fully stopped before our next session, as an ownership and cost rule. A future concurrency requirement could justify requesting 16; neither 16 nor 32 reserves hardware. No quota request was made.

## Concrete fallback policy

[Policy](../infra/gpu/fallback-policy.json), [redacted inventory](evidence/aws-capacity-2026-09-30/inventory.json), [generated offline report](evidence/aws-capacity-2026-09-30/plan.json), and [preparation receipt](evidence/aws-capacity-2026-09-30/preparation.json).

The primary identity and the existing VPC are pinned. Four alternate default subnets in that VPC offer g5.2xlarge in distinct zone IDs: use1-az1, use1-az4, use1-az5 and use1-az6. Offerings and available subnet metadata do not demonstrate free GPU hardware. They form a bounded placement shortlist, not permission to attempt all four automatically.

Only the already qualified g5.2xlarge type is currently included. L4 and L40S are not silently substituted because their model/runtime checks differ. The original L4s are preserved. Their earlier serving history is not a passed training qualification.

Fallback status is **blocked_image**. The primary's current AMI ID identifies its original source image, not its newly installed runtime/checkpoint. A reusable fallback image must be derived from the validated A10G state. The policy deliberately leaves that new image ID null and image verification false. It does not substitute the partly prepared L4 replacement or the unrelated Flux/ai-toolkit environment.

## Image preparation before a live fallback

For a separately scoped image/provisioning operation:

1. Reconfirm the source is stopped and unowned. Bind the source volume, runtime manifest, GPU profile, Qwen revision/inventory, source commits and storage cost/lifecycle to the preparation record.
2. Review the image contents for credentials, copied configuration, customer data and host identity. Preserve the original validated source. If sanitization is needed, perform it in a separately owned image-build copy; do not destructively clean the source or bake customer records into the image.
3. Create a private encrypted image with an explicit retention decision. Establish a fresh trusted SSH identity for a new host through the approved channel; do not blindly trust cloned host keys. Include verified model weights or specify a separately approved exact acquisition/restore path. Our current plan prefers keeping the verified cache.
4. Verify the AMI's availability, architecture, ownership, block mappings and artifact manifest. Record its exact ID and evidence before changing the policy's image verification flag. No floating 'latest' image or bootstrap.
5. Prepare a fresh bounded session packet. Keep the existing security group, IMDSv2, one-host lock, exact identity/GPU checks, busy-process diagnostics, 80/85/90-minute controls and final stopped confirmation. Resolve addresses from AWS, never stored public IPs. Add only permissions needed by the selected artifact path; the older Ilyrium S3 profile is not automatically applicable to private Broadbridge R2.
6. For each approved launch, bind a unique client token and session tags. Only an explicit capacity rejection is eligible for another planned placement. Reconcile any timeout or unexpected response first. Every later attempt retains the original session deadline; alternate placement does not renew the budget.

Spot requires demonstrated checkpoint/resume and interruption handling. Capacity reservations carry ongoing charges and are deferred. Neither is a prerequisite for using the prepared A10G.

## Reproduce the offline plan

From the domain checkout, with the existing sibling Foundry checkout:

```powershell
$foundry = '..\slm-foundry-worktrees\codex-foundry-ingestion-plan'
python "$foundry\scripts\gpu_capacity_plan.py" --policy infra/gpu/fallback-policy.json --inventory docs/evidence/aws-capacity-2026-09-30/inventory.json
```

Expected: primary `prepared_reuse`, fallback `blocked_image`, `execution_authorized: false`. This command reads files only. Before live execution, collect fresh inventory and recheck it while holding the session lock; this recorded snapshot is not current authorization or a capacity guarantee.

The generic request boundary distinguishes capacity, fatal prerequisite and ambiguous errors without disclosing raw stderr. An offline-only copy of the private controller now consumes that boundary and considers stopping hosts a conflict. Its 35 diagnostic/controller/integration tests pass. Earlier receipts and the successful model-load controller are unchanged. The candidate CLI is deliberately disabled; there is no executable fresh session packet yet. Its test of the historical payload reads the original file, rather than copying a fetch payload that would conflict with the retained model cache.

## Validation

Foundry `ac00b3d`: **873 passed, 12 skipped, no failures** in the full offline CPU suite. Skips: nine pyDEXPI dependency cases, the optional DEXPI C01 file, one Docling dependency case and the opt-in local PostgreSQL integration. Three existing Requests/SWIG warnings remain. The focused policy/shell suite passed 40 tests; the separate private controller/diagnostic rehearsal passed 35. Bash syntax, domain JSON parsing, relative links and whitespace checks passed. No new dependencies were installed.

## Return to the model/data work

The next model session should verify/reuse the retained checkpoint, not download it again. Hardware/model loading is established; training memory, checkpoint/resume, engineering usefulness and a serving endpoint on A10G are not established by that result.

The existing [readiness runbook](AWS_TRAINING_READINESS.md) and [queue](SLM_WORK_QUEUE.md) remain authoritative:

| Gate | Actual next work | Owner |
| --- | --- | --- |
| First useful task and source rights | Select the narrow pressure/calculation or case task; record item-level rights and accepted scope | Brad, with Bill or appointed reviewer |
| Engineering reference quality | Resolve the prepared DOE packet's nine exceptions; accept/correct method, units, tolerance and question/reference pairs | Appointed engineering reviewer |
| Case and baseline evidence | Obtain a canonical signed-case export; count case-derived question coverage; run/score S0-cases under a separate bounded decision. Retrieval follows scored failures and admitted documents | Operator and reviewer |
| Dataset release | Bind independent decisions, full source history, family-held-out splits and immutable messages JSONL; repeat the CPU audit on the actual release | Reviewer and operator |
| Training smoke | Authorize the existing 20-step QLoRA configuration with five-step checkpoints after its prerequisites; verify real interruption/resume and costs | Brad and operator |

The latest database evidence here is the earlier dev-only aggregate. It does not establish current production submissions or Bill's responses. No production connection, private case contents or database credentials were accessed in this preparation. The held math sample and diagram outputs remain excluded. No automatic training from raw uploads or synthetic agreement is introduced.

AWS references: [capacity errors](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/troubleshooting-launch.html), [quota rules](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html), [default-subnet behavior](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RunInstances.html).
