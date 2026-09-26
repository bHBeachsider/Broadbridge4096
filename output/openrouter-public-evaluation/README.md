# Public-document evaluation: start here

The [reviewer instructions](public-v1-live/REVIEW_INSTRUCTIONS.md) explain the
30-question packet. The [runbook](../../docs/PUBLIC_DOCUMENT_EVALUATION.md) includes
commands and observed limitations. Use [scores.csv](public-v1-live/scores.csv) for
human grades; all grades currently remain blank.

| Source | Reviewer packet |
| --- | --- |
| Refining process | [EIA refining](public-v1-live/scorecard_EIA-REFINING.md) |
| Refinery volume gain | [EIA inputs/outputs](public-v1-live/scorecard_EIA-YIELD.md) |
| LNG | [EIA LNG](public-v1-live/scorecard_EIA-LNG.md) |
| Gas transmission | [EIA pipelines](public-v1-live/scorecard_EIA-PIPELINE.md) |
| Gas processing/fractionation | [EIA HGL](public-v1-live/scorecard_EIA-HGL.md) |
| Octane/basis arithmetic | [EIA octane](public-v1-live/scorecard_EIA-OCTANE.md) |
| Sulfidation | [CSB Chevron](public-v1-live/scorecard_CSB-CHEVRON.md) |
| Hydrogen partial pressure / HTHA | [CSB Tesoro](public-v1-live/scorecard_CSB-TESORO.md) |
| Blocked-in reboiler | [CSB Williams](public-v1-live/scorecard_CSB-WILLIAMS.md) |
| BAHX thermal fatigue | [CSB Enterprise](public-v1-live/scorecard_CSB-ENTERPRISE.md) |

Observed: Qwen returned 30 answers; Mistral's first response exhausted the output
limit and its client stopped. Thirty Mistral answer slots are failure/not-run
placeholders. Strict citation checks flagged five Qwen document responses.
The [citation audit](public-v1-live/citation_audit.json) preserves exact differences.
No answer was silently repaired, retried or approved for training.

[Summary](public-v1-live/scores_summary.md): human review pending; inference cost
$0.0034673 with all 11 attempted-call cost receipts present. This is not a
balanced model-quality ranking. No EC2, training, database/bucket writes or
production changes occurred.
