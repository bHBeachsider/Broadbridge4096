# Broadbridge4096

## Current core SLM v0 plan

[Infrastructure brief](output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.md) · [Editable Word brief](output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.docx) · [First-case runbook](docs/FIRST_CASE_RUNBOOK.md) · [Oil and gas pack](packs/oil-gas/README.md)

Bill Hurt enters cases directly in the Broadbridge Case Capture page, without a call first. The canonical contract is `broadbridge.case_record/1`. Bill is the named reviewer. Gate 0 requires recorded rights/storage and at least 30 Section C questions with reference answers across all five types, derived from signed cases. The dedicated Broadbridge Neon project is the new system of record; originals/documents remain in one approved S3 bucket. Keep the existing Claude page available until live sign-in and the export/import comparison pass the [capture app cutover procedure](docs/CAPTURE_APP.md).

The [capture app](apps/capture/) uses Auth.js email links, an explicit reviewer allowlist, and the same [SQL migrations](packs/oil-gas/db/) as the Python harness. [Deployment and operation instructions](docs/CAPTURE_APP.md) cover the dedicated dev branch, migration-only unpooled connection, preview activation, and retirement of the old intake page. No EC2 service is needed for capture.

Run **S0-cases** per signed case with decision-time information only; no documents or index are needed. After about 20 documents are admitted, **S0-retrieval** uses the same scoring sheet and must improve on S0-cases before training is considered. Existing Qwen3-8B on EC2 is the starting point. The generic engine belongs in [slm-foundry](https://github.com/bHBeachsider/slm-foundry); this repository owns domain schemas, prompts, plans and synthetic fixtures.

The [first-case runbook](docs/FIRST_CASE_RUNBOOK.md) supports single cases or batches through [first_case.ps1](scripts/first_case.ps1), plus offline [reviewer score aggregation](scripts/aggregate_scores.py). Gate 3 host work and S0-retrieval remain deferred until the first scored briefs reveal the failures to address.

## Planning documents and earlier implementation references

[Current foundry implementation update](Broadbridge-Foundry-Implementation-Update.md)

The existing SLM Foundry with `unsloth/Qwen3-8B` is now the starting architecture. The linked update supersedes the new-instance and Qwen3.5 startup instructions below, specifies the foundry `messages` JSONL format, and identifies the changes needed for oil-and-gas training and visual evidence processing. The earlier AWS artifacts remain reference material; their setup dates and native-vision training scripts are not the current execution baseline.

[AWS first implementation Gantt](output/multimodal-implementation/Broadbridge_AWS_Implementation_Gantt.xlsx)

[AWS first implementation runbook](output/multimodal-implementation/Broadbridge_AWS_Implementation_Runbook.docx)

[AWS model download and inference starter](output/multimodal-implementation/aws_start)

The 24 September revision starts with AWS provisioning and downloading Qwen3.5-4B. It targets the first text and image responses on working day 8, assuming existing AWS access, GPU quota and an authorized sandbox. The 70-task baseline still ends in week 31. AWS resources and model downloads have not been executed. Earlier versions follow for reference.

[Detailed implementation Gantt and task workbook](output/multimodal-implementation/Broadbridge_Multimodal_Implementation_Gantt.xlsx)

[Data processing and training implementation runbook](output/multimodal-implementation/Broadbridge_Multimodal_Implementation_Runbook.docx)

[Training format examples and reference templates](output/multimodal-implementation/format_examples)

The detailed implementation package expands the CTO framework into 70 tasks and a proposed 31-week baseline. It explains source processing, model setup, data formats and acceptance evidence. Production ingestion and training have not been performed.

[Multimodal SLM CTO delivery plan](output/docx/Broadbridge_Oil_and_Gas_Multimodal_SLM_CTO_Plan.docx)

[Multimodal execution register](output/multimodal-project/Broadbridge_Multimodal_Execution_Register.csv)

[Multimodal acceptance gates](output/multimodal-project/Broadbridge_Multimodal_Gate_Register.csv)

[Training information and internal-use assessment](Broadbridge-Training-Information-and-Internal-Use.md)

[Training information checklist](output/training-sources/Broadbridge_Training_Information_Checklist.csv)

[Norm Lieberman online source review](Norm-Lieberman-Online-Source-Review.md)

[Norm Lieberman source register](output/training-sources/Norm_Lieberman_Source_Register.csv)

[Expert knowledge capture guide and templates](output/docx/Broadbridge_Oil_and_Gas_Expert_Knowledge_Capture.docx)

[Training source synthesis](output/docx/Broadbridge_Oil_and_Gas_Training_Source_Synthesis.docx)

[Training source register](output/training-sources/Broadbridge_Training_Source_Register.csv)

[SLM development plan](output/docx/Broadbridge_Oil_and_Gas_SLM_Development_Plan.docx)

[Subsidiary organizational chart](output/docx/Broadbridge_Oil_and_Gas_Organizational_Chart.docx)

[Business and operating structure](output/docx/Broadbridge_Oil_and_Gas_Business_and_Operating_Structure.docx)

[Expert knowledge business assessment](Oil-and-Gas-Expert-Knowledge-Business-Assessment.md)

[Energy Trading source folder](<Energy Trading>)

The `Energy Trading` folder is a live Windows junction to `C:\Users\bradu\OneDrive\Documents\Claude\Projects\Energy Trading`. It does not duplicate the source files. Changes made through the link affect the original OneDrive files. The linked folder is excluded from Git.
