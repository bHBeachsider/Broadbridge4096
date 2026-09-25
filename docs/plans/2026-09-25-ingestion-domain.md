# Broadbridge ingestion implementation binding

Status: implementation authorized, 25 September 2026. Companion to the generic Foundry plan in [draft PR #1](https://github.com/bHBeachsider/slm-foundry/pull/1).

The accepted architecture is [R2 ingestion and training pipeline design](../R2_INGESTION_AND_TRAINING_PIPELINE_DESIGN.md). Generic engine implementation and its delivery ledger live in slm-foundry. Broadbridge owns domain schemas, policy, taxonomy, review, source rights, customer data, its database migration and capture interface. No domain records are committed to either repository.

The delivery method follows the previously approved CoreBuild controller/lane structure. Work occurs in isolated worktrees with exclusive file owners, separate specification and code reviews, tested task commits and draft PRs. The desktop task has three worker slots; the eight packages run in waves. Code acceptance, deployed acceptance and model-quality acceptance are separate states.

## Current foundation

- Domain base 912ee86 contains the existing capture app and dedicated database implementation. Remote main currently predates three local capture/batch commits. Keep this dependency explicit in any new PR; do not push ingestion directly to main.
- The system of record for expert cases is the dedicated Broadbridge Neon project, not the old Claude artifact. Existing case_record/1 and export contracts remain canonical.
- Brad supplied the R2 location on 25 September: bucket `broadbridge`, endpoint `https://af7446fd472b9a8d087250687882a487.r2.cloudflarestorage.com`. Configure endpoint and bucket separately. Access and contents are not yet verified; no PermitHub resource is inferred. This replaces the older unconfigured S3 assumption for this pipeline only.
- Bill Hurt remains the named technical reviewer. Source permission approval and technical acceptance are separate recorded decisions.
- Existing text-only Qwen3-8B receives normalized text/task examples. Original diagrams/images/audio remain linked for later native multimodal work.

## Domain packages

| Task | Deliverable | Dependencies | Required evidence |
|---|---|---|---|
| T6 | oil-gas ingestion policy/taxonomy, canonical case/source adapter, additive migration 0005_ingestion.sql | Foundry contracts and release builder | disposable PostgreSQL schema verification; signed/training eligibility; source permissions; preserved family holdouts |
| T7 | authenticated incoming upload, status, evidence preview and review controls in capture | T6 plus Foundry CPU service | server-side authorization and stale-review tests; isolated browser flow; real nonproduction integration when configured |
| T8 | operator runbook and domain end-to-end acceptance | T4-T7 | exact commands and artifact hashes, reviewed examples, verified dataset/CPU audit, explicit remaining live gates |

T6 owns packs/oil-gas/ingestion.yaml, prompts/ingestion-classify.md, prompts/ingestion-examples.md, scripts/ingestion_adapter.py, db/migrations/0005_ingestion.sql, db/tests/test_ingestion.py, pack.yaml and docs/INGESTION_PIPELINE_RUNBOOK.md. T7 receives an explicit file lease after reviewing the existing capture app; no shared component has two writers. The controller alone updates this plan and the shared delivery log.

## Domain constraints

- Broadbridge scripts connect only through explicitly supplied BROADBRIDGE_DATABASE_URL. DATABASE_URL_UNPOOLED remains migration-only, with existing identity checks. No PermitHub project or credential fallback.
- Preserve the case contract, existing migrations and capture auth. Do not rename old schemas or repurpose case runs/scorecards for corpus jobs. New pipeline records are additive.
- A source document can exist without a case. Raw reports and public data never acquire a fictional Bill sign-off. Case training requires status signed and permitted_use training; generic source training needs its own documented rights and review.
- Stage/review decisions bind source version, content hash and candidate hash. No stale browser review can approve a new revision. Source text cannot assign rights or reviewer identity.
- Keep all original permission, quality, unit/basis, page/time and family metadata. dev maps to val; locked_test maps to test; the strictest assignment applies across a whole family.
- New uploads use unique authorized incoming keys. Pipeline outputs are outside the event-triggering prefix. R2 prefixes do not replace server authorization.
- Use an owned disposable local PostgreSQL instance and synthetic files for write-capable tests. Do not read a root .env as a test-target fallback. Do not reset or migrate production.
- No live model calls or EC2 operations. Confidential model-assisted stages require explicit loopback OLLAMA_URL and remain queued if unavailable.
- The Broadbridge repository is public. Only code, generic/domain policy and synthetic verification fixtures may be proposed for publication; expert records, documents, manifests containing proprietary content and credentials stay out of Git.

## Open live acceptance decisions

| Decision | Owner | Needed before |
|---|---|---|
| Scoped upload/worker credentials for the supplied Broadbridge R2 bucket; verify private access | Brad | live storage acceptance |
| CPU worker deployment target, available CPU/RAM and parser model artifacts | Brad / implementation controller | live OCR and unattended ingestion |
| Rights authority, default pending-source workflow, upload limits and retention | Brad / rights owner | admitting real raw documents |
| Dedicated nonproduction R2/Neon/Vercel target mapping | controller, confirmed by Brad | deployed write-capable acceptance |
| Reviewed training batch, baseline failures to address and bounded GPU budget | Brad / Bill Hurt | first QLoRA run |
| Production migration and model promotion | Brad | separate production release |

These are deployment gates, not reasons to stop independent engine implementation. The final report must distinguish tested local behavior, unrun cloud checks and unmeasured model quality.
