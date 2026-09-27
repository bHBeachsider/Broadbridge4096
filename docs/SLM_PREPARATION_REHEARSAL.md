# Offline preparation: calculation checks and DOE evidence

27 September 2026. FQ-01 and FQ-02 software/extraction preparation is complete;
independent method, source-rights and engineering decisions remain pending.
Neither package creates an approved training release or starts a model.

## What was prepared

The domain `absolute_pressure_ratio_v1` checker uses decimal strings, explicit
absolute basis and matching units. It checks discharge/suction only. Gauge or
unknown basis, mixed units and requests for power are sent for review, without
inventing a conversion or physical model. Invalid input, nonpositive pressure or
ratio, and incorrect arithmetic fail. Tolerance is provisional: absolute 1e-9 or
relative 1e-6, whichever is larger. A qualified independent reviewer must accept
the method, tolerance and applicability before use with real candidates.

The artifact records givens, formula, result, method, tolerances, pending review
and a deterministic SHA-256. The mock source-admission rehearsal binds separate
original-givens and calculated-artifact records to one family. A correct answer
remains pending; pending/revoked artifact rights, changed bytes and historical
holdout ancestry block admission. Release without technical review is rejected.
Foundry's existing generated-number guard is unchanged. This is not a live
calculation-generation or synthetic-release adapter; SD-06 remains open.

The acquired DOE-HDBK-1012/1-92 PDF was inspected at pages 35-37 (printed HT-01
9-11). The packet preserves the exact source hash, native text, a second layout
extraction, glyph positions, page renders, two proposed equation transcriptions,
four proposed conversion rows, nine exceptions, and blank review fields.
No table was detected automatically; the conversion list is explicitly a manual
normalization proposal. No QA pairs were generated.

Poppler's trial render omitted rho. PDFium retained it, so the packet uses PDFium
and all three resulting pages were visually inspected. Text extraction still
separates subscripts, splits a superscript exponent and omits diagram meaning.
The handbook's assumed atmospheric pressure and hydrostatic conventions require
technical review. Frontmatter credits a DOE program managed by EG&G Idaho;
item-level rights are pending, not automatically approved as government material.

## Reproduce locally

From this Broadbridge checkout, select the Foundry checkout with SD-02/SD-03
installed (tested engine `f1790dff35d15739afb77999414c7cc2f6153c6f`). All output
directories must be new. Existing receipts are never overwritten.

```powershell
$Foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http'
$env:SLM_FOUNDRY_PATH = $Foundry
$Run = Join-Path $PWD ('packs/oil-gas/outputs/fq01-' + [guid]::NewGuid().ToString('N'))
python scripts/research/rehearse_calculations.py --mock --foundry $Foundry --out $Run
python -m pytest packs/oil-gas/tests/test_synthetic_checks.py scripts/research/test_rehearse_calculations.py -q

# Use a separate CPU environment with these pinned PDF dependencies.
python -m pip install -r scripts/research/requirements-evidence-review.txt
$Pdf = 'C:\Users\bradu\Documents\Broadbridge4096\packs\oil-gas\data\public-start-2026-09-24\raw\doe\DOE-HDBK-1012-92_VOL1.pdf'
$Packet = Join-Path $PWD ('packs/oil-gas/outputs/fq02-' + [guid]::NewGuid().ToString('N'))
python scripts/research/prepare_doe_pressure_review.py --pdf $Pdf --out $Packet
# Open $Packet/REVIEW.md and complete $Packet/review.csv against the original.
```

The original must hash to
`3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9`.
Any changed revision requires a new selection/inspection. The script accepts no
arbitrary URL and never downloads source data, models or parser artifacts.
This run used Codex's bundled PDF environment with the same pinned versions.

Local outputs from this run are under ignored `packs/oil-gas/outputs/`:

- `fq01-calculation-2026-09-27/`: fixed vectors, normalized source records, pending packet and rejection receipt.
- `fq02-doe-pressure-2026-09-27/`: REVIEW.md, review.csv, packet.json, receipt.json, raw/layout text and PNG renders.

The review packet is local; it has not been loaded into the website, Neon or R2.
Blank fields are not expert approval. Any qualified appointed reviewer can
review within their competence; Bill's responses remain important for priorities
but are not required to run these software rehearsals.

## Validation and next work

The checker and two new rehearsal tools were tested red-to-green. Fixed vectors
also cover nonpositive proposed ratios inside an absolute tolerance. Foundry
source/curation/synthetic/dataset regression tests preserve the existing
numerical guard and release boundary. Full results are recorded in
[the verification receipt](verification/slm-preparation.json).

Next independent work: FQ-03 source-family preparation, FQ-04 math-sample audit,
FQ-06 release/CPU-audit rehearsal, and the proposed
[FQ-05 vision companion pilot](VISION_INGESTION_PILOT.md). The voice questionnaire
remains on its separate development branch. No EC2, training, production change
or reviewer invitation is part of this package.
