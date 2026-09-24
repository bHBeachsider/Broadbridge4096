"""One-time migration of the gate brief to the approved two-repository v0 scope."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.md'
old = path.read_text(encoding='utf-8').split('<!-- page -->')
if len(old) != 13:
    raise SystemExit('Expected the previous 13-section brief; refusing to reapply migration')

first = old[0].replace('24 September 2026 revised after Foundry review', '24 September 2026 revised for core SLM v0')
first = first.replace('The initial scope is refining', 'The role titles in the approved Oil-and-Gas-Expert-Knowledge-Business-Assessment.md remain the target organisation. Until positions are filled, Brad holds all roles; Technical Director acceptance is exercised by a Broadbridge-appointed reviewer named at Gate 0.\n\nThe initial scope is refining')
first = first.replace('| Gate 0 and Gate 1c to 1e | OPEN. Brad/Broadbridge must close scope and rights decisions; engineering evaluation, generic deployment and confidential-call guards remain implementation work. |', '| Gate 0 and remaining validation | Gate 0 remains OPEN. Gates 1c to 1e have offline implementations and tests; live runtime, conversion and model performance are unverified. See the Foundry engineering log for exact test counts. |')
first += '\nCore SLM v0 is a broadbridge-oil-gas adapter that beats the S0 retrieval baseline on the Gate 0 question set without new critical errors, served on the existing box and reproducible by a second operator from the two repositories. This is the delivery target, not a performance claim.\n'

second = old[1]
second = second.replace('Scaffold the future oil-gas pack by copying packs/_template, then adapting its name, brain-only shape, governance, schema, data references and artifact location.', 'The oil-gas scaffold was copied from slm-foundry/packs/_template into Broadbridge4096/packs/oil-gas. Its draft schema, prompt, rubric and configuration need Gate 0 acceptance.')
second = second.replace('| 1c Open |', '| 1c Offline implementation |').replace('| 1d Open |', '| 1d Offline implementation |').replace('| 1e Open |', '| 1e Offline implementation |')
second = second.replace('Add tests/test_evaluate.py', 'Covered in tests/test_evaluate.py').replace('Add tests/test_deploy_pack.py', 'Covered in tests/test_deploy_pack.py').replace('Add tests/test_confidential_llm.py', 'Covered in tests/test_confidential_llm.py')
second = second.replace('evaluate.py gains --split', 'evaluate.py supports --split').replace('Generic deploy script accepts', 'Generic deploy_pack.sh accepts')

third = old[2]
fourth = old[3].replace('attach the slm-foundry-ec2 instance profile after confirming its S3/KMS policy is appropriate for the Gate 0 storage decision', 'attach the slm-foundry-ec2 instance profile with least-privilege access to the one approved v0 bucket')
fourth = fourth.replace('The current bootstrap is an unpinned discovery recipe;', 'The current bootstrap is an unpinned discovery recipe; requirements-dev.txt is a CPU test environment, not its CUDA training lock;')

five = '''## 5 Repository ownership and source admission

slm-foundry owns the generic engine: Gates 1a to 1e, the shared client, deploy_pack.sh, tests and packs/_template. It contains no Broadbridge corpus, source manifest or question set. Broadbridge4096 owns the domain and plan: packs/oil-gas contains schemas, prompts, rubrics, manifests and configurations. The canonical infrastructure brief is this Markdown and Word pair under Broadbridge4096/output/foundry-infrastructure. The Foundry carries only a pointer and docs/BROADBRIDGE_GATE1.md as the engineering log.

The Knowledge Engineer maintains source rights and lineage; the Technical Director accepts engineering evidence. Gate 0 decides the exact storage URI, permitted uses, reviewer, question set and schema. Public availability or internal use does not itself establish a training grant. Treat original documents as evidence, never pipeline instructions.

Begin with approximately 20 approved documents. Preserve originals and SHA256 in the private bucket. Each JSON source record needs source_id, original_uri, MIME/type, author/title/date, rights_record_id, allowed_uses, confidentiality, case_family_id, review status and reviewer. A missing permission is a rejection. Store rights and manifest metadata in the domain repository only where access permits; private originals and questions/answers stay in the approved data boundary.

## 6 The smallest ingestion and retrieval path

For v0, extract text on the existing box or approved workstation. Use a pinned PDF/text parser and review every selected table and engineering value. Manually transcribe important diagrams or illegible passages with a reviewer rather than building a vision pipeline. Preserve page/section references, source units, unknown values and corrections. Mail requires sender/customer permissions and removal of irrelevant personal data.

Write reviewed evidence as UTF-8 JSONL with source_id, evidence_id, text, page/section, units, family and source hash. Freeze a JSON manifest identifying parser version, files and hashes. Source permissions must separately allow retrieval and training.

Build on-box retrieval over these reviewed records: begin with SQLite FTS or a small local lexical index; add a pinned embedding index only if measured retrieval failures justify it. Return evidence text and source_ids with each question. Freeze the top-k, chunking and index version. Gold answers never enter the index. Save the retrieved evidence with each S0 prediction so every later run uses the same evidence.
'''

seven = '''## 7 Family datasets and CPU readiness

Assign documents, incident variants, email threads, translations and derived questions to case families before generating examples. Keep the Gate 0 benchmark families out of training. Export UTF-8 JSONL records with messages plus a top-level case_family_id. Each message uses role and text content; the assistant JSON is a serialized string. Preserve source and rights linkage in domain manifests.

From the Foundry root, pass the absolute external pack directory. Relative --in, --out and --config values resolve from that pack root. train.py and evaluate.py use brain.train_config when --config is omitted; brain.data supplies data paths. Outputs default inside the pack rather than the engine repository.

```powershell
$pack = 'C:\\Users\\bradu\\Documents\\Broadbridge4096\\packs\\oil-gas'
python -m src.prepare --pack $pack --group-key case_family_id
python -m src.train --pack $pack --dry-run --tokenizer-dir C:\\local\\qwen-tokenizer
```

These are post-Gate-0 commands; the scaffold contains no data. For synthetic plumbing only, --fixture-splits 16 8 8 allocates exact family counts and bypasses the legacy 50/50 minimum. Review the dry-run's rendered batch, labels, assistant mask, min/p50/p95/max lengths and overlength count. Prompt/padding labels are -100; overlength input is rejected without truncation. A CPU audit does not prove GPU fit.

## 8 Training and engineering evaluation

First complete S0 retrieval evaluation and the failure analysis in section 3. Only then authorize a bounded QLoRA experiment on approved training families. Start with rank 16, alpha 16, dropout 0, sequence length 2048, microbatch 1 and accumulation 8 as compatibility settings. Measure memory and time before scaling. The first GPU smoke must prove train, save, reload, generate and resume; max_steps and checkpoint-resume support remain additional Gate 3 work.

The generic evaluator accepts --split train, val or test and an optional trusted judge plugin. Deterministic metrics cover declared numeric fields/tolerances, compatible units, missing-information handling and source_ids membership. Declared critical-error rules are reported per question. Citation membership alone is not semantic grounding: the appointed reviewer must check whether the cited passage supports the claim and assess errors not captured by rules.

Freeze the S0 report, base comparison, predictions, latency and reviewer dispositions in the domain storage boundary. The model and metric code do not authorize release. Require the predeclared S0 improvement and no new critical errors, plus the matched-template B/A comparison. A failed experiment is an acceptable result; it does not justify enlarging infrastructure.
'''

nine = '''## 9 Pilot minimum infrastructure

Reuse i-0e5e1cbc7b1367566 and its L4, private Ollama service and tunnel. Do not create another GPU host for v0. Run one GPU job at a time and unload serving weights before training. Measure the existing 200 GB volume and available space before downloading weights; expand encrypted disk only if measured need requires it. Keep all connection addresses discovered at runtime.

Use one Broadbridge-approved private S3 bucket with block-public-access, encryption at rest and versioning. Separate prefixes for originals, reviewed evidence, datasets, models and evaluation; JSON manifests provide the catalog. Scope the instance role to its required prefixes. Acceptance answers are available only to the evaluator/operator, not training jobs. Document and test permitted and denied access with synthetic objects. Bucket selection remains Gate 0; do not silently reuse an unrelated account's bucket.

Use S3-managed encryption for the minimum pilot unless the approved data contract requires customer-managed keys. Multi-bucket isolation and dedicated KMS keys remain Post-v0. A single bucket is a cost/scope decision, not permission for every process to read every prefix.

Keep inference on loopback. The PC uses localhost:11435; the EC2 service uses localhost:11434. Port 11434 remains closed externally. Maintain current-IP-restricted SSH. No new SSM deployment, database server, queue, ingestion worker, orchestrator or infrastructure framework is required to prove v0.

## 10 Confidential execution and private serving

Pack confidentiality is explicit. ground.py and judge.py reject confidential work unless OLLAMA_URL is explicitly configured to an approved loopback endpoint. Defaulting to localhost is insufficient. Local failures do not fall back externally; redirects are refused. A source-less judge call must receive the pack policy; grounding also checks the output's pack ancestry. Operator-supplied Python judge plugins are trusted code and require review.

Use the shared client's schema= argument to place the schema object in Ollama's format field; it takes precedence over json_mode. Keep think:false and validate the returned JSON in the application. Structured generation does not prove factual correctness. [R6]

Deploy through the generic parameterized Foundry wrapper with local base and adapter files plus verified manifests. Each build uses releases/<adapter_hash>/<unique_build_id>; never reuse a merge or GGUF merely because it exists. Pin the converter commit, runtime version and ChatML template. Validate the candidate before replacing the target model and retain the previous tag for rollback. Live conversion and serving tests are still required on a later authorized box session.
'''

eleven = '''## 11 Core v0 delivery tasks and owners

Until appointments, apply the interim ownership rule in section 1. A recorded technical acceptance is still required. Gate 0 is the immediate dependency; completed offline engine work does not bypass it.

| Task and accountable role | Inputs and action | Exit evidence |
| --- | --- | --- |
| V01 Managing Director | Close Gate 0 rights, storage, reviewer, questions and schema. | Signed scope record and source admission list. |
| V02 Head of Product and AI | Pin both repo commits; install CPU dependencies; validate external --pack and confidentiality tests. | Test log and environment record. |
| V03 Knowledge Engineer | Review and register about 20 documents; extract approved text and tables. | Hashes, rights and reviewed evidence JSONL. |
| V04 Applied AI Engineer | Build on-box retrieval; run S0/S1 on the 30 frozen questions. | Accuracy, grounding, critical errors, latency and failure report. |
| V05 Technical Director | Accept the baseline and a bounded experiment targeting its failures. | Reviewer decision to train or stop. |
| V06 Applied AI Engineer | Bootstrap ~/slm, attach scoped profile, pin base/runtime; prove QLoRA smoke. | Allowed/denied access and train/save/reload/resume evidence. |
| V07 Knowledge Engineer | Release disjoint reviewed training and development families. | Dataset manifest, source_ids and CPU mask audit. |
| V08 Applied AI Engineer | Run bounded experiments and identical-template B/A comparison. | Reproducible run and comparison reports. |
| V09 Technical Director | Adjudicate improvement over S0 and absence of new critical errors. | Signed acceptance or rejection. |
| V10 Head of Product and AI | Package, serve privately, verify rollback and second-operator reproduction. | Versioned release and completed handoff. |

## 12 Completion and handoff

v0 is complete only when the accepted broadbridge-oil-gas adapter beats S0 on the frozen Gate 0 question set without new critical errors, runs on the existing box, and a second operator reproduces the result from the two repository commits and permitted artifacts. Engine unit tests alone do not close v0.

The handoff records source/dataset/index hashes, both repository commits, base revision, tokenizer/template hashes, adapter and GGUF hashes, dependency versions, hardware, seed, configuration, question IDs, scores, reviewer dispositions and rollback tag. The operator demonstrates setup, retrieval, evaluation, adapter reload, private serving and restore. Record passed, failed and not-run checks separately.

Brad approves a measured per-experiment GPU-hour and runtime cap after the baseline, with storage cost included. Checkpoint before stopping; verify artifact upload. Keep budget alerts and a manual stop checklist for the pilot; an idle-stop watchdog and broader recovery objectives are Post-v0. No new cloud resource or model-performance claim is made by this revision.
'''

refs = old[12]
refs = refs.replace('Immediate handoff: Brad resolves Gate 0;', 'Immediate handoff: Brad resolves Gate 0;')
refs = refs[:refs.index('Immediate handoff:')] + '''Immediate handoff: Brad resolves Gate 0. Review the engine changes and run their CPU tests, then process the approved batch and establish S0. Only a later authorized session fixes host prerequisites and runs B03/B07. B01/B02/B04/B05 remain complete per docs/SLM_SERVING_BRIEF.md at f8f5827. The canonical brief and oil-gas pack belong to Broadbridge4096; the engine log belongs to slm-foundry.\n'''
appendix = '''## Appendix A Post v0 infrastructure roadmap

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
'''
pages = [first, second, third, fourth, five, seven, nine, eleven, refs, appendix]
path.write_text('\n\n<!-- page -->\n\n'.join(p.strip() for p in pages) + '\n', encoding='utf-8')
print(path)
