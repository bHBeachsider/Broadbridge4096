# Public/synthetic OpenRouter intake trial

This step connects normalized evidence to advisory classification and pending
training-example drafts. It is an explicit operator command after CPU extraction;
it does not automatically call a model when somebody uploads a file. The capture
app and the confidential oil-gas pack remain unchanged.

The generic implementation is in slm-foundry, after draft #8. The companion
`packs/oil-gas-public-intake/` was scaffolded from `packs/_template`, with Broadbridge
taxonomy, prompts and trial model selection. This pack has no training config.
Qwen3-8B remains the fine-tuning target. The cloud drafting teacher is a separate
model; no weights need downloading and no EC2 session is used here.

## What is implemented

| Stage | Tool and result |
|---|---|
| Raw text, CSV, email, Word, Excel | Existing Foundry native extraction produces normalized blocks with source identity and locations |
| Cloud eligibility | Explicit public pack/source, approved source rights, complete extraction, separate document/policy-hash approval |
| Classification | `python -m src.ingestion.assist --task classify`; labels, exact quotes and a usage receipt |
| Drafting | Same CLI with `--task draft`; self-contained messages, exact source/block references and pending review |
| Human review | Existing `ingestion_release.py register-candidates`, capture review UI, then hash-bound release approval |
| Training | Existing bounded Foundry process, after dataset and compute approval; not started by this tool |

The canonical case-capture path remains separate. Do not pass full expert case
records to this helper, relabel confidential sources public, or move them into
this companion pack to evade local-only policy. Public accessibility alone is
not source-rights approval. Refresh source rights from the authoritative register
before authorizing external processing; the file CLI cannot detect a stale local
snapshot. Registration/release still rechecks current database rights.

## Reproduce without cloud access

Use the reviewed helper branches/checkouts from the paired draft PRs. Set the
two variables to absolute checkout paths. Example paths on Brad's machine:

```powershell
$Foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http'
$Domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-live-test'
$Run = Join-Path $Domain ('tmp\helper-rehearsal-' + (Get-Date -Format yyyyMMdd-HHmmss))
python "$Domain\scripts\research\rehearse_openrouter_intake.py" --foundry $Foundry --out $Run
```

Dependencies: Foundry `requirements-ingestion.txt`, plus `openpyxl==3.1.5` for the
synthetic XLSX authoring step (already in Foundry requirements-dev.txt). The
default rehearsal uses actual native parsers and real curation with HTTP mocked
only at the external model boundary. It creates five fixtures and five pending
candidates, proves release is blocked, and proves the confidential pack is denied.
No database, bucket, app account, model key or GPU is needed. Mock cost receipts
are labeled synthetic and do not measure a model's quality or price.

For the optional live smoke, export OPENROUTER_API_KEY in the process environment
using the approved local secret-loading practice, then add `--live` with a fresh
output directory. The script accepts only embedded synthetic fixtures, caps the
live selection at two files/four calls, and stops on the first failure. It never
loads .env automatically. Never put the key in a command, transcript or Git file.

## Process an admitted public document

1. Obtain its current complete `foundry.normalized_document/1` from the CPU
   extraction artifact. Keep it and any results outside Git. Record source use
   rights; drafting requires approved training permission.
2. Follow Foundry `docs/INGESTION_OPENROUTER.md` to calculate the canonical full
   document hash and `load_policy($PublicPack)['sha256']`. Write and review the
   separate cloud-processing approval for that document/policy/task. No tool
   infers this approval from source content.
3. From the Foundry checkout, with absolute file paths:

```powershell
$PublicPack = Join-Path $Domain 'packs\oil-gas-public-intake'
python -m src.ingestion.assist --pack $PublicPack --document $Normalized `
  --approval $CloudApproval --task classify --check
python -m src.ingestion.assist --pack $PublicPack --document $Normalized `
  --approval $CloudApproval --task classify --live --output $NewClassificationRun
python -m src.ingestion.assist --pack $PublicPack --document $Normalized `
  --approval $CloudApproval --task draft --split train --live --output $NewDraftRun
```

4. Inspect exact quotations, values/units/basis, limitations and receipt. A valid
   schema or matching quotation does not prove that the answer correctly uses it.
5. For a source already registered in the intended domain environment, use the
   existing domain bridge with its explicit environment and store settings:

```powershell
python "$Domain\packs\oil-gas\scripts\ingestion_release.py" `
  --foundry $Foundry --pack "$Domain\packs\oil-gas" `
  register-candidates --input "$NewDraftRun\candidates.json" --actor $ReviewerEmail
```

The helper's standalone synthetic rehearsal sources are local files, not
registered Neon/R2 sources. Do not execute registration for them without the
separate trusted source-registration step. In a local rehearsal also provide
`--local-object-root`; in dev use only the verified Broadbridge dev database and
bucket. This implementation did not perform that live registration.

6. A named reviewer accepts or rejects each exact candidate hash in the capture
   flow. Preserve source rights review separately. Freeze the dataset only after
   acceptance; use the existing release, token audit and compute gates. The helper
   itself writes no train-ready JSONL, changes no database, and starts no training.

## Live findings and model selection

The first Mistral classification timed out at 40 seconds. A manually initiated
run with a 90-second limit returned an invalid citation, correctly rejected by
the engine. A separate diagnostic classification succeeded with matching quotes.
These failures are retained, not hidden by an automatic retry or counted as zero
cost. The timeout's final billed cost is unknown.

Mistral then produced structurally valid draft JSON quoting `3 bar absolute` but
claiming the basis was unknown. This fails the synthetic engineering check and
is not an acceptable training target. It demonstrates why schema/quote checks
and model confidence cannot replace technical review.

The same source and drafting prompt with `qwen/qwen3-30b-a3b-instruct-2507` on
Nebius returned a pending draft preserving `3 bar absolute` and `45 degC`.
Its receipt was 7.52 seconds and $0.0000748; Mistral's incorrect draft was 13.12
seconds and $0.0000271. These are single observed calls, not a statistical quality
or latency comparison. Different drafted questions further limit comparison.
The pack therefore uses Qwen provisionally for drafting and keeps Mistral only
as an advisory classification trial. Existing deterministic classification
remains the default upload behavior. Jev remains an optional classification
research path, not a generative teacher.

All calls required an explicit provider, schema support, no data collection, ZDR,
and price caps; drafting also required distillable-text routing. These controls
follow [OpenRouter's provider routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection).
No data went to a direct OpenAI endpoint and no confidential content was sent.
See the [machine-readable evidence](verification/openrouter-helper.json).

Before wider use: collect unseen reviewer-labeled documents, measure errors and
cost per accepted example, add numerical/unit/basis checks, and validate the
chosen helper across that sample. Native OCR/audio/vision and automatic worker
invocation remain separate work. Nothing here closes Gate 0 or authorizes QLoRA.

The next public-document sample is now available in
[PUBLIC_DOCUMENT_EVALUATION.md](PUBLIC_DOCUMENT_EVALUATION.md): ten agency pages,
thirty fixed questions, draft references and unscored reviewer sheets. Live
observations include Mistral output-limit failure and Qwen quotation-check flags;
there is no completed technical score or approved training batch.
