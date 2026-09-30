# First dataset review: pressure-basis checking

30 September 2026 UTC. Scope: offline preparation in Broadbridge4096; Foundry unchanged.

**Subsequent decision from Brad:** scoring and the current 15-question pressure test set are approved for this exercise, assuming Bill agrees; source rights remain **TBD**. See the [frozen diagnostic set and decision](../packs/oil-gas/eval/pressure-diagnostic-v1/README.md) and [six-source register](../packs/oil-gas/manifests/evaluation_sources.json). This is Brad's recorded instruction, not actual Bill signoff. The original proposal below remains historical; no model scores, signed cases, rights clearance or training acceptance are implied. The entire pressure-handbook family is reserved to diagnostic dev/testing-only.

**Brad's follow-up:** no new expert review or signed case is available. [Offline first-case preflight/rehearsal](FIRST_CASE_PREFLIGHT.md) proceeds while those inputs are pending; the pressure packet's acceptance status is unchanged.

The next useful work is accepting a small, explicit engineering task and its references. The Qwen3-8B runtime and NF4 load already passed on the retained A10G. Another installation or weight download does not resolve the remaining data and baseline gates.

## Review material

- [Reviewer worksheet: fifteen draft questions and answers](evidence/first-pressure-review-2026-09-30/REVIEW.md).
- [Blank decision sheet](evidence/first-pressure-review-2026-09-30/review.csv): task, rights, family, nine exceptions and fifteen questions. Copy it for review; preserve this blank original and its receipt.
- [Structured proposal](evidence/first-pressure-review-2026-09-30/proposal.json) and [file-hash receipt](evidence/first-pressure-review-2026-09-30/receipt.json).

These are assistant-authored educational drafts for independent review, not approved training examples, a model run or a replacement for `broadbridge.case_record/1`. Do not feed `proposal.json` to the case importer. The internal proposal schema carries pending decisions and cannot confer release approval. No email was sent or capture application changed.

The proposed task is to identify pressure-reference mistakes, request missing inputs, perform explicitly bounded pressure-basis arithmetic and decline unsupported conclusions. Bill or another appointed engineer should first confirm whether this task has practical value. A different task can be chosen before building a larger corpus.

## What was checked and what was excluded

The existing local DOE-HDBK-1012/1-92 Volume 1 original was re-extracted with the pinned parsers. PDF pages 35-37 (printed HT-01 pages 9-11) were visually inspected. The resulting `packet.json` SHA-256 is `0ae8da768e4fbc5427d5c4acbd4b2193dcf93308fffac6e8cb61fce26f0b8150`, identical to the earlier extraction packet. The original 1,910,060-byte PDF SHA-256 is `3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9`. Raw files stay in ignored local storage.

The page-image transcriptions propose `P_abs = P_atm + P_gauge` and `P_abs = P_atm - P_vac`, where the latter uses a positive vacuum-depression magnitude. Decimal arithmetic independently checks three illustrative references: `14.2 + 36.8 = 51.0`, `14.5 + (-2.1) = 12.4`, and `14.7 - 5.0 = 9.7`, all in psia with compatible supplied inputs. The proposed +/-0.05 psi answer tolerance is rounding tolerance, not instrument accuracy or an accepted engineering criterion.

The hydrostatic worked examples use lbm notation with an implicit force/gravity convention. Numerical hydrostatic candidates are excluded pending an explicit method decision; the source is not silently rewritten. Rounded water/mercury-column conversions are also excluded from numerical generation. Figure 2 is a pressure-scale illustration, not P&ID topology. The visible `10^3` transcription is recorded as a review proposal; it does not authorize a general conversion recipe.

All nine source issues have proposed dispositions; none is marked independently closed. The source's public-distribution statement and contractor credits are included in the extraction evidence. Rights/credits and the permitted processing/training scope remain for Brad to record. This preparation makes no legal determination.

## Decisions still required

| Owner | Concrete decision or input | Why it matters |
| --- | --- | --- |
| Bill / appointed engineer | Useful task; accept/revise/exclude each reference, assumption, tolerance and hard-fail criterion | Arithmetic alone cannot establish engineering usefulness or correctness of the method |
| Brad | Exact source/page permission basis and credits; authorized use | Public access is not a recorded source-admission decision |
| Operator + release reviewer | Handbook-family history and one split for all related volumes, versions and derivatives; separate accepted evaluation families | Fifteen paraphrases from one family are not independent train/test evidence |
| Case contributor + reviewer | Canonical signed cases and Section-C references | Gate 0 still needs at least 30 signed case-derived questions across all five types; these drafts contribute zero |
| Operator + reviewer | S0-cases scores; retrieval comparison when scored failures and admitted documents justify it | Preserve the accepted baseline sequence before training |

The earlier aggregate database query reached dev, not production. This work reads no credentials or database. It therefore does not establish whether Bill has since submitted a case. No new signed case/export was supplied during preparation. Keep that uncertainty explicit rather than treating dev fixtures as real acceptance.

After review, use the existing source/candidate acceptance and immutable release workflow in [INGESTION_PIPELINE_RUNBOOK.md](INGESTION_PIPELINE_RUNBOOK.md). Record reviewer identity, date, corrections and the exact proposal hash; changes require a new version/review. Do not fabricate a reviewer or `approved_by`, and do not take a checked box in an unverified local CSV as authenticated release authority. The review sheet is evidence to reconcile in that workflow, not an automatic admission tool.

## Offline reproduction

From PowerShell, choose new output directories. Do not overwrite a prior packet or edit its hashed original files. The PDF step requires the already installed pinned `pypdf==6.10.0`, `pdfplumber==0.11.9` and `pypdfium2==5.13.0`; the proposal builder is standard-library Python only. Nothing below downloads a file or calls a model.

```powershell
$domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$pdf = 'C:\Users\bradu\Documents\Broadbridge4096\packs\oil-gas\data\public-start-2026-09-24\raw\doe\DOE-HDBK-1012-92_VOL1.pdf'
$pdfPython = 'C:\Users\bradu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$evidence = Join-Path $domain 'packs\oil-gas\outputs\doe-pressure-repeat'
$proposal = Join-Path $domain 'packs\oil-gas\outputs\first-pressure-review-repeat'
& $pdfPython "$domain\scripts\research\prepare_doe_pressure_review.py" --pdf $pdf --out $evidence
if ($LASTEXITCODE -ne 0) { throw 'Extraction failed' }
python "$domain\scripts\research\prepare_first_dataset_review.py" --packet-dir $evidence --out $proposal
if ($LASTEXITCODE -ne 0) { throw 'Review preparation failed' }
```

The builder checks the extraction receipt, all twelve listed evidence files, source family/hash and page coverage. Changed, missing, duplicate or unsafe paths are rejected before creating an output directory. It writes only `proposal.json`, `REVIEW.md`, `review.csv` and `receipt.json`; no messages JSONL, release, token audit or training run is produced. Review outputs use LF line endings so Git normalization does not invalidate their receipt. The worksheet's local render link varies by workstation; the proposal itself binds the exact extraction packet hash.

## Validation and next AWS action

The offline review/calculation tests cover all five types, arithmetic, invalid inputs, answer-free prompt projection, pending rights/technical decisions, no family split, tampered evidence, output preservation and receipt hashes: **67 passed**, no skips, one existing Requests dependency warning. See [the validation receipt](evidence/first-pressure-review-validation-2026-09-30.json) for the command/results. No cloud or model acceptance test is claimed.

The AWS readiness runbook now points to the retained A10G environment/cache and guarded load-reuse tooling. It removes the stale future replacement-L4 launch instructions and the instruction to unload another model. A busy GPU still blocks preflight. The generic load-only packet is not a training authorization. The next paid session awaits accepted data/baseline gates and a separately bound smoke plan; no EC2 start occurred here.
