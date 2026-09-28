# Foundry hosting options — review, 27 September 2026

Keep local Docker for the current pilot. Cloud Run Jobs is a credible later host for intermittent document processing, but the supplied comparison does not establish that Google is cheaper. Compare finite jobs on both clouds, including startup, memory, retries, networking and operating effort. This is an architecture review, not authorization to deploy, start EC2, train or change production.

## Recommended placement

| Workload | Now | Later, when measured demand warrants it |
|---|---|---|
| Extraction, normalization, source checking | Existing local Docker worker | Benchmark Cloud Run Jobs against short-lived ECS Fargate tasks; consider interruptible capacity only after checkpoint/retry validation |
| Capture and review UI | Existing Vercel app | Keep it; trigger authenticated batch execution from the server when needed |
| Original documents and derived evidence | Private R2; Neon stores metadata and workflow state | Keep the separation; record object hashes and dataset lineage |
| Qwen fine-tuning | Remains gated; no training now | Existing AWS L4 box when separately authorized; checkpoint and stop after a bounded run |
| Occasional vision/inference | Existing bounded local experiment path | Benchmark a Cloud Run GPU service if CPU latency becomes unacceptable and cloud inference is authorized |
| Kubernetes or TPU | Defer | Adopt only for demonstrated scheduling, throughput or cost requirements |

The current Foundry base is `unsloth/Qwen3-8B` (`packs/nast/pack.yaml`); remote serving uses `qwen3:8b`. The local diagram experiment uses `qwen3-vl:4b-instruct-q4_K_M`. The pasted `Qwen3.5-4B` and an eight-day AWS mandate are not the current project's recorded baseline. Hosting does not remedy the observed diagram-connectivity errors or replace expert acceptance.

## Corrections to the supplied comparison

**Fargate can run finite tasks.** ECS is not necessarily an always-on deployment. A queue-driven task can exit after its batch. Fargate charges from image download until task termination, with a one-minute minimum for Linux. At the published US East Linux/x86 rates, CPU is about $0.04048/vCPU-hour and RAM $0.004446/GiB-hour. Fargate does not support GPUs. [AWS pricing](https://aws.amazon.com/fargate/pricing/), [Fargate task constraints](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-tasks-services.html).

**ALB and NAT are architecture choices.** A batch worker pulling a queue needs no public inbound endpoint or ALB. A public-subnet task with outbound internet access and inbound-denying security rules can avoid NAT, with public IPv4 charges still applicable. Private-subnet NAT, private endpoints and load balancing have different costs and security tradeoffs. The supplied $50/month overhead is not an unavoidable ECS fee. [AWS outbound networking](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/networking-outbound.html), [inbound networking](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/networking-inbound.html).

**Jobs and services differ.** A Cloud Run service supplies an HTTPS endpoint. A Cloud Run Job runs tasks to completion and has no serving endpoint; an authenticated control-plane call starts it. Do not move an infinite polling worker into a Job unchanged. [Container contract](https://docs.cloud.google.com/run/docs/container-contract), [creating jobs](https://docs.cloud.google.com/run/docs/create-jobs).

**Scale to zero is not instantaneous completion or free startup.** Cloud Run Jobs and instance-based services have a one-minute billing minimum. Jobs bill task lifetime, including startup. Standard Tier 1 Jobs CPU/RAM rates are $0.0648/vCPU-hour and $0.0072/GiB-hour; free allowances are shared across the billing account. Cloud Run worker pools and request-based services have separate pricing; do not substitute those rates. An L4 with minimum 4 vCPU/16 GiB costs approximately $1.05/hour without zonal redundancy, or $1.42/hour with it, before discounts and other charges. [Cloud Run pricing](https://cloud.google.com/run/pricing).

**GPU startup is not model readiness.** Google's approximately five-second figure concerns GPU instance startup, after which the container can use the accelerator. Weight loading, model initialization and warmup are additional. L4 requires at least 4 vCPU/16 GiB; Google recommends 8 vCPU/32 GiB. Check region, quota and redundancy configuration; new GPU services default to zonal redundancy. [Cloud Run GPU support](https://docs.cloud.google.com/run/docs/configuring/services/gpu).

**GPU jobs have a material duration limit.** Cloud Run GPU tasks currently permit up to one hour, versus seven days for CPU tasks. This makes GPU jobs a poor default for longer QLoRA runs without a tested resume strategy. GPU services are useful inference candidates; neither a GPU price nor inference compatibility proves a training recipe will work. [Task timeouts](https://docs.cloud.google.com/run/docs/configuring/task-timeout).

**R2 removes its own egress fee, not every network charge.** R2-to-browser delivery can avoid proxying files through a compute host. Uploading normalized images or checkpoints from AWS/GCP to R2 still creates outbound traffic at the compute provider. R2 storage and operations remain chargeable. [R2 pricing](https://developers.cloudflare.com/r2/pricing/).

**TPU is a separate engineering choice.** vLLM's TPU path uses its TPU integration and supported model/runtime combinations. That is not evidence that our CUDA-oriented QLoRA pipeline works unchanged or that TPU has the best throughput per dollar. Benchmark the actual model and training stack before considering a port. [vLLM TPU installation](https://docs.vllm.ai/projects/tpu/en/latest/getting_started/installation/).

**GKE adds a cluster layer.** Its cluster management fee is $0.10/hour with an eligible billing-account credit; compute and networking remain separate. That does not justify Kubernetes for the present single-reviewer pilot. The pasted EC2/GCE and TPU spot ranges were not independently validated in this review and should not be used as quotations. [GKE pricing](https://cloud.google.com/kubernetes-engine/pricing).

## Illustrative CPU comparison

One Linux/x86 task allocation: 4 vCPU and 8 GiB RAM. Both platforms terminate the task between batches. This is arithmetic from list rates, not a performance benchmark or a cost-per-document promise. Hours include billable task lifetime; multiple concurrent tasks add their hours. No Spot, commitments, registry, logs, networking, public IPv4 or orchestrator-trigger costs included.

| Allocated task-hours/month | Fargate compute | Cloud Run Jobs gross | Cloud Run Jobs with full unused monthly CPU/RAM allowance |
|---:|---:|---:|---:|
| 60 (2 hours/day × 30) | $11.85 | $19.01 | $13.79 |
| 240 (8 hours/day × 30) | $47.40 | $76.03 | $70.81 |
| 730 | $144.16 | $231.26 | $226.04 |

Calculation: Fargate = hours × (4 × 0.0404784 + 8 × 0.004446); Cloud Run = hours × (4 × 0.0648 + 8 × 0.0072). For these usages, subtract $5.22 if the entire relevant Cloud Run allowance is available. Very small workloads may fit inside Google's allowance; other services may have consumed it. Sources: [Fargate rates](https://aws.amazon.com/fargate/pricing/) and [Cloud Run rates](https://cloud.google.com/run/pricing).

There is no basis yet for claiming “250 PDFs for pennies.” Page counts, scans versus digital text, OCR, diagram rendering, model inference, retries and output size dominate the result. Equal vCPU counts also need not deliver equal throughput.

## Portable workflow and decision gate

1. Keep one versioned Docker image with a finite batch entry point. Claim a bounded set of jobs using durable Neon leases; record attempts and heartbeat. Make object writes and state transitions idempotent because retries and duplicate delivery are expected.
2. Read authorized originals from R2; classify, extract and normalize into versioned evidence with source hashes. Write progress and failures before exit. Resume from durable checkpoints rather than local container files.
3. Keep permission checks, technical review, independent reference graphs, train/dev/test family boundaries and dataset release approval intact. Uploading a document must not automatically start fine-tuning.
4. Benchmark a representative public/synthetic batch locally: pages and formats, wall time, CPU time, peak RAM, startup, bytes transferred, retries, quality and reviewer correction time. Separate OCR/extraction from vision/model calls.
5. Once always-available operation or backlog justifies cloud hosting, replay the same approved batch/image on each candidate with limits on concurrency, attempts, runtime and spend. Measure dollars per accepted document or evidence block, plus operations effort. No provider resources are provisioned by this review.
6. Start cloud jobs through server-side authentication with least-privilege identities. Keep credentials out of browser code, logs and committed files. Avoid holding the user's web request open for the batch.
7. Keep GPU inference and training as separate release gates. An eventual auto-stop guard should require no active run/lease, saved checkpoints and explicit maximum runtime; a transient utilization dip is not enough. Design and test that guard before authorizing GPU sessions.

For this stage, the next investment is better source coverage, reference quality and reviewer feedback. Moving identical unverified visual outputs to a faster host will not make them suitable for training.
