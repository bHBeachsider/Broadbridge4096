# SLM Foundry infrastructure implementation brief

Broadbridge Oil and Gas | Broadbridge4096 | 24 September 2026 revised for core SLM v0

## 1 Verified starting point and delivery status

Use the existing Foundry Qwen3-8B platform for Broadbridge Oil & Gas, a subsidiary of Broadbridge4096. This revision corrects the earlier Broadbridge update and replaces the six-week infrastructure-first sequence with Gates 0 through 3. Scope decisions and a retrieval baseline precede domain training. This task performs offline Foundry fixes and document revision only; EC2 remains unstarted by this work.

The role titles in the approved Oil-and-Gas-Expert-Knowledge-Business-Assessment.md remain the target organisation. Until positions are filled, Brad holds all roles; Technical Director acceptance is exercised by a Broadbridge-appointed reviewer named at Gate 0.

The initial scope is refining and process operations: evidence review, missing-information questions, checked calculations and engineer-reviewed diagnostic briefs. Norm Lieberman remains an illustrative expert candidate, with no appointment or source permissions assumed.

| Item and task mapping | Verified status and evidence |
| --- | --- |
| Current EC2 instance | i-0e5e1cbc7b1367566 in us-east-1, as recorded in infra/status.ps1 and docs/SLM_SERVING_BRIEF.md at commit f8f5827. The old June-plan ID i-02d15a1d9645210ad is stale. |
| B01 / B02 / B04 | COMPLETE for the serving host/model setup: qwen3:8b, Q4_K_M, GPU-served on the L4. Completion is documented in docs/SLM_SERVING_BRIEF.md; no repeat setup is planned. |
| B05 | COMPLETE for end-to-end inference through localhost:11435 and closed external port 11434, per the same serving brief. Do not reopen this as a new work package. |
| Shared inference client | src/llm_client.py, mocked tests and .env.example are committed in 3fe688f after tests passed. It now supports schema= and JSON mode with think:false by default; callers still validate the returned answer. |
| Gate 1a and 1b | Implemented and CPU-tested on codex/broadbridge-gate1-data-training. Family splits, explicit fixture counts, assistant-only labels and local-tokenizer dry-run are covered in tests/. GPU integration remains Gate 3. |
| Gate 0 and remaining validation | Gate 0 remains OPEN. Gates 1c to 1e have offline implementations and tests; live runtime, conversion and model performance are unverified. See the Foundry engineering log for exact test counts. |
| Training host blockers | No ~/slm training venv and no slm-foundry-ec2 instance profile are reported in the serving brief. Both must be resolved before B03/B07. Serving completion does not resolve them. |

Evidence was verified from local files and commit history, not by starting or connecting to AWS. The old instance ARN also remains in infra/iam-ec2-selfmanage-policy.json; replace that obsolete policy during the later infrastructure work. The slm SSH alias used by status diagnostics can become stale after a restart. Preserve unrelated Nast, Broderick and stripe work.



Core SLM v0 is a broadbridge-oil-gas adapter that beats the S0 retrieval baseline on the Gate 0 question set without new critical errors, served on the existing box and reproducible by a second operator from the two repositories. This is the delivery target, not a performance claim.

<!-- page -->

## 2 Gate 0 scope and Gate 1 offline Foundry fixes

Critical path: Gate 0 Broadbridge scope → Gate 1 Foundry readiness → Gate 2 retrieval and baseline → Gate 3 training prerequisites and experiments. No prior calendar estimate overrides a failed gate.

Gate 0 is OPEN and owned by Brad/Broadbridge. It requires no GPU and no code. Record the approved rights and exact storage location, a named technical reviewer, approximately 30 target engineering questions with reference answers, and the output schema. Each question needs source_ids, applicable numeric tolerances/units, missing-evidence expectations and critical-error criteria. The reviewer name and these assets are decisions to be supplied, not invented here.

C01 may register source leads and unresolved permissions. Nothing after C01, including proprietary extraction, dataset production or baseline processing, proceeds until Gate 0 is accepted. The generic offline Gate 1a–1e work explicitly requested in this review proceeds independently using synthetic fixtures; it does not close Gate 0 or authorize any source use.

Gate 1 runs without a GPU. The oil-gas scaffold was copied from slm-foundry/packs/_template into Broadbridge4096/packs/oil-gas. Its draft schema, prompt, rubric and configuration need Gate 0 acceptance. Remove template personas and unrelated hand/image-generation fields. Do not build a parallel pack format from scratch. Domain values are populated only after Gate 0.

| Work package | Required behavior and tests |
| --- | --- |
| 1a Complete on branch | prepare.py --group-key keeps whole families together; --fixture-splits TRAIN VAL TEST bypasses the old 50/50 minimum. tests/test_prepare.py covers disjoint groups, deterministic splits, duplicates, invalid groups/counts and small fixtures. |
| 1b Complete on branch | train.py --dry-run uses local fast-tokenizer files, prints a rendered batch, input IDs, labels, assistant mask and length statistics. Prompt/padding labels are -100. Overlength data is reported and rejected, with no silent truncation. tests/test_train.py covers these behaviors and CPU loss gradients. |
| 1c Offline implementation | evaluate.py supports --split, a pluggable judge and engineering metrics: numeric tolerance, unit equivalence, missing evidence and grounding against source_ids. Covered in tests/test_evaluate.py for valid/invalid units, absent evidence, unresolved citations and split selection. |
| 1d Offline implementation | Generic deploy_pack.sh accepts pack/model names and builds into an adapter-hash release directory using a unique build ID. Never reuse a merge/GGUF simply because a file exists. Covered in tests/test_deploy_pack.py for hash/path isolation, wrong manifests and parameter propagation. |
| 1e Offline implementation | ground.py and judge.py refuse confidential packs unless an explicitly configured local OLLAMA_URL judge is approved. Both route locally with no external fallback. Covered in tests/test_confidential_llm.py for unset/nonlocal URLs, rejected external calls and permitted loopback tunnel use. |

Gate 1 exit requires all five work packages and the regression suite. A confidentiality flag or default localhost URL alone is not permission to send data. Keep independent technical review even when a local model assists evaluation.

<!-- page -->

## 3 Gate 2 retrieval baseline and fair comparisons

After Gates 0 and 1, process the first approximately 20 approved documents and the approximately 30 reviewer-approved questions. Build permission-filtered retrieval and run the existing stock qwen3:8b before training. A later authorized inference session may start the box; this document revision does not. The existing serving setup is reused, not reprovisioned.

Freeze document versions, source_ids, question IDs, reference answers, schema, retrieval/index versions and inference settings. Treat this small set as development evidence; exclude its case families from training and retain a separate acceptance set for eventual release claims. Thirty questions do not establish broad engineering reliability.

Stock qwen3:8b uses Ollama's Qwen3 template and normally enables thinking. The Foundry's fine-tuned route uses pinned ChatML. Comparing those defaults would confound template, thinking, quantization and training effects. Use the following explicitly labeled tracks.

| Track | Required method |
| --- | --- |
| S0 Product baseline before training | Stock qwen3:8b with its native Ollama template, think:false, stream:false, frozen schema/system prompt and retrieval. Record its digest/template and settings. This is the practical benchmark the proposed tuned system must improve. |
| S1 Template control before training | Create a separately named base serving artifact from the same stock GGUF with the proposed pinned ChatML template and stop tokens. Use think:false and identical evidence, context/output limits and sampling settings. Compare S1 against S0 to expose template effects. |
| B versus A Training effect at Gate 3 | Use the exact pinned Hugging Face base without an adapter (B) and with the candidate adapter (A). Render identical prompts with the same tokenizer/template and thinking policy. For serving comparisons, export both through the same pinned merge/conversion/quantization process. Do not assume the stock GGUF is identical to this base. |

Set think:false on every Ollama comparison; use temperature 0 and identical context/output limits for the controlled benchmark. On Hugging Face use the same saved ChatML template and generation settings for B and A. A custom template may ignore thinking controls: inspect rendered prompts and score unexpected reasoning/schema leakage consistently. If an explicit nonthinking prefix is needed, apply and validate it identically in training and both matched evaluation paths. Never silently change only the baseline template.

For each track record engineering accuracy, grounding/citation validity, critical errors and per-question latency; distinguish cold-start from warm latency. Preserve predictions, source IDs, retrieval results, settings and reviewer dispositions. Predeclare scoring tolerances and required improvement at Gate 0.

Gate 2 exit is a reviewed baseline report and a specific failure analysis. Authorize only bounded training experiments aimed at those gaps. Retain a tuned release only if it improves the agreed S0 benchmark and the matched B comparison without new critical errors or worse grounding. If retrieval already meets the objective or tuning fails to improve it, do not scale training.

<!-- page -->

## 4 Gate 3 training prerequisites and pinned base

Gate 3 begins only after the baseline and experiment decision at Gate 2. First fix both known box blockers: run infra/bootstrap.sh to establish ~/slm, and attach the slm-foundry-ec2 instance profile with least-privilege access to the one approved v0 bucket. Verify the assumed role and an allowed S3 read/write plus denied out-of-scope access. Both blockers must be closed before B03 and B07.

B03 establishes the pinned trainable checkpoint and runtime. The current bootstrap is an unpinned discovery recipe; requirements-dev.txt is a CPU test environment, not its CUDA training lock; lock the working Python 3.11, driver/CUDA, PyTorch, Unsloth, Transformers, TRL, PEFT, Datasets, Accelerate, bitsandbytes and Hub client combination after validation. Record the code commit and model/template hashes. The existing Ollama artifact is a serving baseline, not the training input.

After the environment and encrypted /data/models mount exist, resolve a revision once and download that exact snapshot. Run this only in the later authorized Gate 3 session. [R2]

```python
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

root = Path('/data/models/qwen3-8b')
root.mkdir(parents=True, exist_ok=True)
lock = root / 'base-lock.json'
if not lock.exists():
    repo = 'unsloth/Qwen3-8B'
    sha = HfApi().model_info(repo).sha
    assert sha, 'No model revision returned'
    lock.write_text(json.dumps({'repo': repo, 'revision': sha}))
spec = json.loads(lock.read_text())
target = root / spec['revision']
snapshot_download(repo_id=spec['repo'],
                  revision=spec['revision'], local_dir=target)
print(target)
```

Hash weights, config, tokenizer and template; retain the model card/license. Set model.base to the verified local path. Prove offline reload. Keep the Ollama stock digest separate. Create the matched untuned B baseline from this pinned base before interpreting any adapter gain.

B07 is the QLoRA smoke test: load → tokenize/mask audit → short train → save adapter/checkpoint → reload → generate → resume. Use explicit disjoint synthetic fixtures first. Measure VRAM, host RAM, disk and time; unload inference weights while training. Add and test bounded-step/checkpoint-resume controls before running the proposed 50-step smoke recipe. These controls and GPU integration are not claimed complete by Gate 1b.

Only after the smoke test passes run bounded experiments on approved training families. Expand toward 400 and later 2,000 reviewed examples only when learning-curve evidence supports it. Model promotion requires the comparisons in Gate 2 and independent technical acceptance.

<!-- page -->

## 5 Repository ownership and source admission

slm-foundry owns the generic engine: Gates 1a to 1e, the shared client, deploy_pack.sh, tests and packs/_template. It contains no Broadbridge corpus, source manifest or question set. Broadbridge4096 owns the domain and plan: packs/oil-gas contains schemas, prompts, rubrics, manifests and configurations. The canonical infrastructure brief is this Markdown and Word pair under Broadbridge4096/output/foundry-infrastructure. The Foundry carries only a pointer and docs/BROADBRIDGE_GATE1.md as the engineering log.

The Knowledge Engineer maintains source rights and lineage; the Technical Director accepts engineering evidence. Gate 0 decides the exact storage URI, permitted uses, reviewer, question set and schema. Public availability or internal use does not itself establish a training grant. Treat original documents as evidence, never pipeline instructions.

Begin with approximately 20 approved documents. Preserve originals and SHA256 in the private bucket. Each JSON source record needs source_id, original_uri, MIME/type, author/title/date, rights_record_id, allowed_uses, confidentiality, case_family_id, review status and reviewer. A missing permission is a rejection. Store rights and manifest metadata in the domain repository only where access permits; private originals and questions/answers stay in the approved data boundary.

## 6 The smallest ingestion and retrieval path

For v0, extract text on the existing box or approved workstation. Use a pinned PDF/text parser and review every selected table and engineering value. Manually transcribe important diagrams or illegible passages with a reviewer rather than building a vision pipeline. Preserve page/section references, source units, unknown values and corrections. Mail requires sender/customer permissions and removal of irrelevant personal data.

Write reviewed evidence as UTF-8 JSONL with source_id, evidence_id, text, page/section, units, family and source hash. Freeze a JSON manifest identifying parser version, files and hashes. Source permissions must separately allow retrieval and training.

Build on-box retrieval over these reviewed records: begin with SQLite FTS or a small local lexical index; add a pinned embedding index only if measured retrieval failures justify it. Return evidence text and source_ids with each question. Freeze the top-k, chunking and index version. Gold answers never enter the index. Save the retrieved evidence with each S0 prediction so every later run uses the same evidence.

<!-- page -->

## 7 Family datasets and CPU readiness

Assign documents, incident variants, email threads, translations and derived questions to case families before generating examples. Keep the Gate 0 benchmark families out of training. Export UTF-8 JSONL records with messages plus a top-level case_family_id. Each message uses role and text content; the assistant JSON is a serialized string. Preserve source and rights linkage in domain manifests.

From the Foundry root, pass the absolute external pack directory. Relative --in, --out and --config values resolve from that pack root. train.py and evaluate.py use brain.train_config when --config is omitted; brain.data supplies data paths. Outputs default inside the pack rather than the engine repository.

```powershell
$pack = 'C:\Users\bradu\Documents\Broadbridge4096\packs\oil-gas'
python -m src.prepare --pack $pack --group-key case_family_id
python -m src.train --pack $pack --dry-run --tokenizer-dir C:\local\qwen-tokenizer
```

These are post-Gate-0 commands; the scaffold contains no data. For synthetic plumbing only, --fixture-splits 16 8 8 allocates exact family counts and bypasses the legacy 50/50 minimum. Review the dry-run's rendered batch, labels, assistant mask, min/p50/p95/max lengths and overlength count. Prompt/padding labels are -100; overlength input is rejected without truncation. A CPU audit does not prove GPU fit.

## 8 Training and engineering evaluation

First complete S0 retrieval evaluation and the failure analysis in section 3. Only then authorize a bounded QLoRA experiment on approved training families. Start with rank 16, alpha 16, dropout 0, sequence length 2048, microbatch 1 and accumulation 8 as compatibility settings. Measure memory and time before scaling. The first GPU smoke must prove train, save, reload, generate and resume; max_steps and checkpoint-resume support remain additional Gate 3 work.

The generic evaluator accepts --split train, val or test and an optional trusted judge plugin. Deterministic metrics cover declared numeric fields/tolerances, compatible units, missing-information handling and source_ids membership. Declared critical-error rules are reported per question. Citation membership alone is not semantic grounding: the appointed reviewer must check whether the cited passage supports the claim and assess errors not captured by rules.

Freeze the S0 report, base comparison, predictions, latency and reviewer dispositions in the domain storage boundary. The model and metric code do not authorize release. Require the predeclared S0 improvement and no new critical errors, plus the matched-template B/A comparison. A failed experiment is an acceptable result; it does not justify enlarging infrastructure.

<!-- page -->

## 9 Pilot minimum infrastructure

Reuse i-0e5e1cbc7b1367566 and its L4, private Ollama service and tunnel. Do not create another GPU host for v0. Run one GPU job at a time and unload serving weights before training. Measure the existing 200 GB volume and available space before downloading weights; expand encrypted disk only if measured need requires it. Keep all connection addresses discovered at runtime.

Use one Broadbridge-approved private S3 bucket with block-public-access, encryption at rest and versioning. Separate prefixes for originals, reviewed evidence, datasets, models and evaluation; JSON manifests provide the catalog. Scope the instance role to its required prefixes. Acceptance answers are available only to the evaluator/operator, not training jobs. Document and test permitted and denied access with synthetic objects. Bucket selection remains Gate 0; do not silently reuse an unrelated account's bucket.

Use S3-managed encryption for the minimum pilot unless the approved data contract requires customer-managed keys. Multi-bucket isolation and dedicated KMS keys remain Post-v0. A single bucket is a cost/scope decision, not permission for every process to read every prefix.

Keep inference on loopback. The PC uses localhost:11435; the EC2 service uses localhost:11434. Port 11434 remains closed externally. Maintain current-IP-restricted SSH. No new SSM deployment, database server, queue, ingestion worker, orchestrator or infrastructure framework is required to prove v0.

## 10 Confidential execution and private serving

Pack confidentiality is explicit. ground.py and judge.py reject confidential work unless OLLAMA_URL is explicitly configured to an approved loopback endpoint. Defaulting to localhost is insufficient. Local failures do not fall back externally; redirects are refused. A source-less judge call must receive the pack policy; grounding also checks the output's pack ancestry. Operator-supplied Python judge plugins are trusted code and require review.

Use the shared client's schema= argument to place the schema object in Ollama's format field; it takes precedence over json_mode. Keep think:false and validate the returned JSON in the application. Structured generation does not prove factual correctness. [R6]

Deploy through the generic parameterized Foundry wrapper with local base and adapter files plus verified manifests. Each build uses releases/<model>/<adapter_hash>-<unique_build_id>; never reuse a merge or GGUF merely because it exists. Pin the converter commit, runtime version and ChatML template. Validate the candidate before replacing the target model and retain the previous tag for rollback. Live conversion and serving tests are still required on a later authorized box session.

<!-- page -->

## 11 Core v0 delivery tasks and owners

Until appointments, apply the interim ownership rule in section 1. A recorded technical acceptance is still required. Gate 0 is the immediate dependency; completed offline engine work does not bypass it.

| Task and accountable role | Inputs and action | Exit evidence |
| --- | --- | --- |
| V01 Managing Director | Close Gate 0 rights, storage, reviewer, questions and schema. | Signed scope record and source admission list. |
| V02 Head of Product & AI | Pin both repo commits; install CPU dependencies; validate external --pack and confidentiality tests. | Test log and environment record. |
| V03 Knowledge Engineer | Review and register about 20 documents; extract approved text and tables. | Hashes, rights and reviewed evidence JSONL. |
| V04 Applied AI Engineer | Build on-box retrieval; run S0/S1 on the 30 frozen questions. | Accuracy, grounding, critical errors, latency and failure report. |
| V05 Technical Director | Accept the baseline and a bounded experiment targeting its failures. | Reviewer decision to train or stop. |
| V06 Applied AI Engineer | Bootstrap ~/slm, attach scoped profile, pin base/runtime; prove QLoRA smoke. | Allowed/denied access and train/save/reload/resume evidence. |
| V07 Knowledge Engineer | Release disjoint reviewed training and development families. | Dataset manifest, source_ids and CPU mask audit. |
| V08 Applied AI Engineer | Run bounded experiments and identical-template B/A comparison. | Reproducible run and comparison reports. |
| V09 Technical Director | Adjudicate improvement over S0 and absence of new critical errors. | Signed acceptance or rejection. |
| V10 Head of Product & AI | Package, serve privately, verify rollback and second-operator reproduction. | Versioned release and completed handoff. |

## 12 Completion and handoff

v0 is complete only when the accepted broadbridge-oil-gas adapter beats S0 on the frozen Gate 0 question set without new critical errors, runs on the existing box, and a second operator reproduces the result from the two repository commits and permitted artifacts. Engine unit tests alone do not close v0.

The handoff records source/dataset/index hashes, both repository commits, base revision, tokenizer/template hashes, adapter and GGUF hashes, dependency versions, hardware, seed, configuration, question IDs, scores, reviewer dispositions and rollback tag. The operator demonstrates setup, retrieval, evaluation, adapter reload, private serving and restore. Record passed, failed and not-run checks separately.

Brad approves a measured per-experiment GPU-hour and runtime cap after the baseline, with storage cost included. Checkpoint before stopping; verify artifact upload. Keep budget alerts and a manual stop checklist for the pilot; an idle-stop watchdog and broader recovery objectives are Post-v0. No new cloud resource or model-performance claim is made by this revision.

<!-- page -->

## 13 Technical references and document precedence

The implementation choices and targets in this brief are project recommendations. Vendor documentation supports the specific API and platform behavior cited, not the proposed gate sequence, hardware capacity or engineering acceptance. Documentation was checked on 24 September 2026; pin the versions actually validated during Gate 3.

- R1 Qwen3-8B model cards: [Qwen publisher](https://huggingface.co/Qwen/Qwen3-8B) and [Foundry Unsloth checkpoint](https://huggingface.co/unsloth/Qwen3-8B). Text-generation architecture and model license; archive the exact revision used.

- R2 [Hugging Face Hub download guide](https://huggingface.co/docs/huggingface_hub/guides/download). Snapshot downloads, revision pinning and local directories.

- R3 [AWS EC2 IAM roles](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html). Instance profiles and workload credentials.

- R4 [AWS S3 KMS encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html). Encryption behavior and KMS permissions.

- R5 [TRL SFT Trainer](https://huggingface.co/docs/trl/sft_trainer). Conversational datasets, assistant-only loss and chat-template compatibility. Validate behavior in the pinned environment.

- R6 [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs). JSON/schema generation controls and response validation.

- R7 [AWS budget actions](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-action-configure.html). Configure budget actions explicitly; notifications alone do not implement a job runtime limit.

- R8 [AWS Session Manager sessions](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html). Agent/plugin prerequisites and SSH/port-forwarding logging limitations.

- R9 [Docling project](https://github.com/docling-project/docling). Local document conversion, layout and OCR interfaces.

- R10 [faster-whisper project](https://github.com/SYSTRAN/faster-whisper). Local transcription runtime; pin its speech-model dependency separately.

- R11 [BGE small English model card](https://huggingface.co/BAAI/bge-small-en-v1.5). Initial embedding candidate; benchmark on engineering retrieval before acceptance.

Local implementation evidence inspected: AGENTS.md; docs/SLM_SERVING_BRIEF.md; infra/bootstrap.sh; infra/launch-slm.ps1; infra/status.ps1; infra/iam-s3-policy.json; infra/iam-ec2-selfmanage-policy.json; configs/qwen3-8b-example.yaml; src/train.py; src/prepare.py; src/evaluate.py; src/pack.py; src/llm_client.py; packs/_template/pack.yaml; and packs/nast/brain/deploy_box.sh in the slm-foundry repository.

Broadbridge background: Broadbridge-Foundry-Implementation-Update.md; Broadbridge-Multimodal-SLM-CTO-Plan.md; Broadbridge-Oil-and-Gas-SLM-Development-Plan.md; and the multimodal/AWS implementation runbooks in output/multimodal-implementation. Preserve the original reports and Energy Trading folder link; commodity-trading documents remain organizational references, not a trading-desk requirement.

Precedence for this infrastructure work: current user constraints and Foundry serving brief establish the operational baseline; this brief supplies the new infrastructure scope and acceptance evidence. Earlier new-instance/Qwen3.5 proposals and old instance IDs are not the starting procedure. Existing corporate governance remains in force. Gates 0–3 replace the prior six-week infrastructure-first estimate. Rebaseline dates after Gate 0 and the retrieval benchmark; previous 24- or 31-week whole-program estimates are not renewed commitments.

Immediate handoff: Brad resolves Gate 0. Review the engine changes and run their CPU tests, then process the approved batch and establish S0. Only a later authorized session fixes host prerequisites and runs B03/B07. B01/B02/B04/B05 remain complete per docs/SLM_SERVING_BRIEF.md at f8f5827. The canonical brief and oil-gas pack belong to Broadbridge4096; the engine log belongs to slm-foundry.

<!-- page -->

## Appendix A Post v0 infrastructure roadmap

The following capabilities are retained as the long-term plan. They are outside the core v0 critical path, not abandoned. Activate them when customer isolation, availability, data volume or measured retrieval/vision failures justify the cost and a funded owner is assigned.

| Capability | Retained long term design and adoption trigger |
| --- | --- |
| Infrastructure as code | CloudFormation foundation.yaml and workers.yaml, parameterized accounts, VPC/subnets, AMI, worker types, disks, CIDR and budget. Review change sets and prove rebuild when repeated environments are needed. |
| Stronger storage isolation | Separate private data, model-artifact and evaluation buckets; customer-managed KMS keys and scoped key policies. Separate ingestion/training/serving/evaluator identities; test allowed and denied S3/KMS access. Adopt for customer or contractual isolation requirements. |
| Dedicated ingestion worker | Initially 4 vCPU/16 GB with sandboxed parsing, OCR, table extraction and job queue. Pin Docling/OCR, spreadsheet/email parsers and private transcription components. Keep GPU extraction separate from training; add capacity from measured throughput. |
| Private access management | Systems Manager, required agent/permissions/endpoints and controlled egress; human SSO/MFA and temporary worker credentials. Retain application audit metadata because SSH/port-forward contents are not Session Manager logs. |
| Retrieval and catalog scale | PostgreSQL, full-text search and pgvector with pinned embeddings; backup and later managed database. Adopt only after the on-box pilot demonstrates its scale/availability limit. |
| Operator CLI framework | Domain-owned packs/oil_gas_cli.py with inventory, download-base, ingest, validate, build-dataset, train, evaluate, package and verify-release. Explicit run/environment IDs and dry-run for mutations. Until then use the tested Foundry entry points. |
| Vision and audio | Reviewed P&ID/diagram interpretation through a separately benchmarked vision extractor, OCR and private speech transcription. Preserve uncertainty and evidence locators. Native multimodal fine-tuning remains a separate model and validation project; Qwen3-8B stays text-only. |
| Availability and recovery | Dedicated serving host, GPU job leases, CloudWatch/CloudTrail monitoring, checkpoint-age alarms, cost alerts and idle-stop watchdog. Proposed recovery targets: 30-minute checkpoint loss, 24-hour metadata RPO, one-day restore and 30-minute serving rollback, demonstrated before becoming commitments. |

Long-term disk planning retains an encrypted 500 GB gp3 working-volume estimate, recalculated from actual model and data files. Keep latest two plus best development checkpoints as an initial retention proposal, subject to the approved records policy and legal holds. Do not auto-terminate the existing box.

Shared parent services and the approved subsidiary organisation remain the governance model at every stage. Infrastructure growth creates no automatic hiring commitment or expert appointment. Keep expert content rights, software/adapter ownership, base-model licensing and customer-data permissions as distinct records.
