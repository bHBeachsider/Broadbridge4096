# Broadbridge Oil and Gas foundry implementation update

24 September 2026 revised for core SLM v0

The [canonical infrastructure brief](output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.md) and [editable Word version](output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.docx) are the source of truth. Core v0 is a broadbridge-oil-gas adapter that beats the S0 retrieval baseline on the Gate 0 question set without new critical errors, served on the existing box and reproducible by a second operator from the two repositories.

## Organisation and ownership

The role titles are the approved target organisation in [the business assessment](Oil-and-Gas-Expert-Knowledge-Business-Assessment.md). Until positions are filled, Brad holds all roles; Technical Director acceptance is exercised by a Broadbridge-appointed reviewer named at Gate 0.

slm-foundry owns the generic engine, Gates 1a–1e, client, deployment script, tests and packs/_template. Broadbridge4096 owns the domain and plan. [packs/oil-gas](packs/oil-gas) was copied from the generic template and contains draft schemas, prompts, rubrics, manifests guidance and configuration. It contains no approved source corpus or question set. Domain assets are consumed through --pack <absolute-path>, not copied into the engine repository. Foundry's infrastructure brief is now only a pointer; its engineering log records tests.

## Verified baseline and open scope

infra/status.ps1 and docs/SLM_SERVING_BRIEF.md at Foundry commit f8f5827 identify i-0e5e1cbc7b1367566 in us-east-1. The June-plan i-02d15a1d9645210ad is stale. B01/B02/B04/B05 are complete for qwen3:8b Q4_K_M on the L4, localhost:11435 SSH-tunnel access and external port 11434 closed. These facts were verified from repository records, without starting EC2.

The serving box still needs ~/slm through infra/bootstrap.sh and the scoped slm-foundry-ec2 instance profile before B03/B07. No training venv or S3 access is implied by working inference. Keep public IP discovery dynamic; never expose Ollama port 11434. Windows port 11434 is not the remote endpoint.

Bill Hurt is the named reviewer and enters as many cases as he chooses directly in the Broadbridge Case Capture page, without a call first. The page's broadbridge.case_record/1 export is primary and canonical. The Interview Guide is a pre-read/call script; case_from_form_fallback.py is only for a reviewer who cannot use the page and emits that same contract.

Gate 0 remains OPEN until rights/storage are recorded and signed cases supply at least 30 Section C questions with reference answers spanning brief, missing_data, calculation, grounded_explanation and abstention. The reviewer requirement is complete. Pilot case records live in the Claude artifact store; originals and any documents live in the one approved S3 bucket. Record its exact URI/prefix and the artifact identifier. Questions are derived from cases, not supplied separately. See [the pack runbook](packs/oil-gas/README.md) for intake, family holdouts and the prompt guard.

## Critical path

| Gate | Work and evidence |
| --- | --- |
| 0 | Record rights/storage; Bill Hurt named (done); collect at least 30 referenced Section C questions across all five types from signed cases. |
| 1 | CPU-tested family/fixture splits, assistant-only masks/dry-run, engineering evaluation, generic fresh deployment builds and confidential-call guards. Live runtime remains unverified. |
| 2 | Run S0-cases per signed case without documents/index. After about 20 documents are admitted, S0-retrieval must beat S0-cases using the same scorecards before training is considered. |
| 3 | Fix both host blockers; pin trainable base/runtime; prove QLoRA train/save/reload/resume; run bounded experiments only against baseline failures. |
| v0 acceptance | Appointed reviewer accepts improvement over S0 without new critical errors; second operator reproduces private serving and rollback. |

S0-cases and S0-retrieval use stock Ollama qwen3:8b with its native template and think:false; compare the same case-derived questions, schema, settings and 0/1/2 scorecards. The first-case runbook implements S0-cases; retrieval is the later document/index stage. S1 uses the same stock GGUF with pinned ChatML to expose template effects. At Gate 3 compare exact pinned base B with adapter A under identical tokenizer, ChatML, thinking policy, retrieval, limits and decoding. Match conversion/quantization for serving comparisons. Inspect actual rendered prompts; a custom template may ignore a think flag. The adapter must beat S0 as well as the matched base, not just a weaker template control.

## Minimum infrastructure and execution

v0 uses the existing box, one approved private encrypted/versioned bucket, on-box retrieval and JSON manifests. Keep gold answers outside retrieval and training access. No CloudFormation rollout, separate ingestion worker, multi-bucket/KMS framework, SSM deployment, CLI framework or vision model is needed to prove v0. Those capabilities remain explicitly retained in the brief's Post-v0 appendix.

The current Qwen3-8B model receives text messages JSONL, including reviewed textual representations of tables or diagrams. It does not receive pixels. Preserve originals and source locators for review. A native multimodal model is a later evaluated option.

All three Foundry entry points accept an absolute external pack path. Relative assets/configs resolve from the pack root; outputs remain in the domain boundary. The shared client now supports schema= (Ollama format), think:false and JSON mode. Callers still validate the answer schema and engineering evidence.

Publication is authorized for Broadbridge4096 main and the three requested slm-foundry branches after the tracked-file size check. [Repository Commands](output/foundry-infrastructure/Repository_Commands.md) records the publication procedure and audit. Engine commits for Gates 1c–1e are present; Brad verified 116 passing tests in test_evaluate.py, test_deploy_pack.py and test_confidential_llm.py. This update does not start EC2, run live inference, train or deploy a model.
