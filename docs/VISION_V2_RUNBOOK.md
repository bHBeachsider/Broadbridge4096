# Focused extraction and connectivity validation

Use Broadbridge branch `codex/vision-connectivity` and Foundry branch
`codex/foundry-vision-connectivity`. The original [v1 runbook](LOCAL_VISION_RUNBOOK.md)
and all v1 receipts remain unchanged. This is FQ-05 preparation, not training.

## Freeze the inputs

From the Broadbridge checkout, with Pillow from `scripts/research/vision/requirements.txt`:

```powershell
python scripts/research/vision/prepare_v2.py `
  --v1 packs/oil-gas/outputs/vision-pilot-2026-09-27 `
  --doe-packet packs/oil-gas/outputs/fq02-doe-pressure-2026-09-27 `
  --out packs/oil-gas/outputs/vision-v2-2026-09-27
```

The command verifies the original job and DOE receipt, copies four unchanged
synthetic figures, and crops two formulas without scaling or retouching.
`fixture-receipt.json` records parent hashes and crop boxes in page-image pixels.
`references.json` freezes label expectations and three direct-edge graphs based
on the fixture drawing specification. `job.json` contains nine single-task
requests and the reference-file hash; the reference answers are never sent to
the models. Existing output directories are refused.

## Run once locally

The two model volumes are already installed. In the Foundry checkout:

```powershell
.\infra\vision\vision.ps1 Batch `
  -WorkDir 'C:\absolute\Broadbridge4096\packs\oil-gas\outputs\vision-v2-2026-09-27' `
  -ResultName results-v2
```

Maximum nine requests, each 180 seconds; allow up to approximately 30 minutes
including loading/stopping. The wrapper stops the CPU vision stack afterward.
There is no cloud fallback, exposed port, EC2 session or paid inference. On a
transport timeout the batch stops; inspect the receipt and explicitly select
only unrun IDs with `-Only` in a new result directory. Keep failures in reports.

## Check separately

From Broadbridge, pointing at the actual Foundry checkout:

```powershell
python scripts/research/vision/prepare_v2.py `
  --out packs/oil-gas/outputs/vision-v2-2026-09-27 `
  --report packs/oil-gas/outputs/vision-v2-2026-09-27/results-v2 `
  --foundry 'C:\absolute\slm-foundry'
```

Repeat `--report` for explicit continuation directories. Duplicate attempts,
changed reference/image bytes or mismatched job/prompt/profile/model receipts
are refused. Missing responses remain in the nine-request denominator.

`checks.json` distinguishes schema completion from label, transcription and
graph checks. Graph comparison catches invented bridge connections, skipped
junctions and unsupported arrows. It does not derive topology from the pixels.
For real diagrams, freeze a separately reviewed trace or CAD topology instead
of treating another model's answer as the truth.

Formula outputs require visual review of operators, rho, subscripts, exponent,
units and physical meaning. Matching literal words is only a development check.
All outputs stay unapproved. Raw vision proposals cannot enter the current
training-example contract; reviewed normalization/export is still a future
step. Rights, source-family exclusions and independent technical acceptance
remain required even after a graph matches.

The development set was selected from v1 failures. Shorter tasks, schemas,
cropping and decoding changed together; this is neither a held-out engineering
accuracy result nor an isolated prompt experiment. See the [plan](VISION_CONNECTIVITY_PLAN.md).
