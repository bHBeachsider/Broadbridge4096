# Broadbridge Oil and Gas foundry implementation update

24 September 2026 revised for core SLM v0

The [canonical infrastructure brief](output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.md) and [editable Word version](output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.docx) are the source of truth. Core v0 is a broadbridge-oil-gas adapter that beats the S0 retrieval baseline on the Gate 0 question set without new critical errors, served on the existing box and reproducible by a second operator from the two repositories.

## Organisation and ownership

The role titles are the approved target organisation in [the business assessment](Oil-and-Gas-Expert-Knowledge-Business-Assessment.md). Until positions are filled, Brad holds all roles; Technical Director acceptance is exercised by a Broadbridge-appointed reviewer named at Gate 0.

slm-foundry owns the generic engine, Gates 1a–1e, client, deployment script, tests and packs/_template. Broadbridge4096 owns the domain and plan. [packs/oil-gas](packs/oil-gas) was copied from the generic template and contains draft schemas, prompts, rubrics, manifests guidance and configuration. It contains no approved source corpus or question set. Domain assets are consumed through --pack <absolute-path>, not copied into the engine repository. Foundry's infrastructure brief is now only a pointer; its engineering log records tests.

## Verified baseline and open scope

infra/status.ps1 and docs/SLM_SERVING_BRIEF.md at Foundry commit f8f5827 identify i-0e5e1cbc7b1367566 in us-east-1. The June-plan i-02d15a1d9645210ad is stale. B01/B02/B04/B05 are complete for qwen3:8b Q4_K_M on the L4, localhost:11435 SSH-tunnel access and external port 11434 closed. These facts were verified from repository records, without starting EC2.

The serving box still needs ~/slm through infra/bootstrap.sh and the scoped slm-foundry-ec2 instance profile before B03/B07. No training venv or S3 access is implied by working inference. Keep public IP discovery dynamic; never expose Ollama port 11434. Windows port 11434 is not the remote endpoint.

Gate 0 remains OPEN, owned by Brad/Broadbridge: approved rights and storage URI, named reviewer, approximately 30 engineering questions/reference answers and accepted output schema. The separately authorized Case Capture intake tools gather that evidence; they do not approve production training or close the gate. Bill Hurt enters cases in the database-backed page. Its JSON export is the intake contract; the DOCX parser task is cancelled and the Interview Guide remains a pre-read and call script. See [the pack runbook](packs/oil-gas/README.md) for schema validation, dispositions, family holdouts and the decision-time prompt guard.

## Critical path

| Gate | Work and evidence |
| --- | --- |
| 0 | Record scope, rights, reviewer, questions and schema. No GPU or source processing. |
| 1 | CPU-tested family/fixture splits, assistant-only masks/dry-run, engineering evaluation, generic fresh deployment builds and confidential-call guards. Live runtime remains unverified. |
| 2 | Process about 20 approved documents; build on-box retrieval; record S0/S1 accuracy, grounding, critical errors and latency before training. |
| 3 | Fix both host blockers; pin trainable base/runtime; prove QLoRA train/save/reload/resume; run bounded experiments only against baseline failures. |
| v0 acceptance | Appointed reviewer accepts improvement over S0 without new critical errors; second operator reproduces private serving and rollback. |

S0 uses stock Ollama qwen3:8b with its native template and think:false. S1 uses the same stock GGUF with pinned ChatML to expose template effects. At Gate 3 compare exact pinned base B with adapter A under identical tokenizer, ChatML, thinking policy, retrieval, limits and decoding. Match conversion/quantization for serving comparisons. Inspect actual rendered prompts; a custom template may ignore a think flag. The adapter must beat S0 as well as the matched base, not just a weaker template control.

## Minimum infrastructure and execution

v0 uses the existing box, one approved private encrypted/versioned bucket, on-box retrieval and JSON manifests. Keep gold answers outside retrieval and training access. No CloudFormation rollout, separate ingestion worker, multi-bucket/KMS framework, SSM deployment, CLI framework or vision model is needed to prove v0. Those capabilities remain explicitly retained in the brief's Post-v0 appendix.

The current Qwen3-8B model receives text messages JSONL, including reviewed textual representations of tables or diagrams. It does not receive pixels. Preserve originals and source locators for review. A native multimodal model is a later evaluated option.

All three Foundry entry points accept an absolute external pack path. Relative assets/configs resolve from the pack root; outputs remain in the domain boundary. The shared client now supports schema= (Ollama format), think:false and JSON mode. Callers still validate the answer schema and engineering evidence.

The approved local repository operations, pre-commit size inventory and confirmation-gated publication commands are in [Repository Commands](output/foundry-infrastructure/Repository_Commands.md). No remote repository was created and no push, EC2 start, live inference, GPU training or deployment was performed. Existing Broderick datasets remain tracked by Brad's explicit decision pending review before publishing.
