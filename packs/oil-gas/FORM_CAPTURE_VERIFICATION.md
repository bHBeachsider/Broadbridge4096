# Canonical DOCX fallback verification

24 September 2026, v3 review correction. The Case Capture web page is the primary intake. Bill enters cases directly without a prerequisite call. The Interview Guide remains a pre-read/call script and is parsed only for a reviewer who cannot use the page.

## One external contract

scripts/case_from_form_fallback.py emits broadbridge.case_record/1, validated by schemas/case_record.schema.json and schemas/export.schema.json. The alternative form schema and its validator were removed. Importer, brief runner and scorecard accept the canonical case contract only. evidence_ids and hard_fail_criteria remain strings with their captured text intact.

The original output/expert-capture/Broadbridge_Expert_Interview_Guide_v1.docx and synthetic filled fixture were preserved. The fixture is explicitly synthetic and contains no actual case, source-rights grant or signed consent.

## Reproduce offline

From the Broadbridge4096 repository root, choose fresh output directories:

```powershell
python packs/oil-gas/scripts/case_from_form_fallback.py packs/oil-gas/tests/fixtures/Synthetic_Filled_Interview_Guide.docx tmp/fallback-demo --case-id FORM-SYN-001 --family-id FORM-FAMILY-001 --standalone-family --case-signed-off
python packs/oil-gas/scripts/import_cases.py tmp/fallback-demo/capture_export.json tmp/fallback-demo-import
python packs/oil-gas/run_brief.py tmp/fallback-demo-import/data/cases/FORM-SYN-001.json --dry-run
python -m pytest packs/oil-gas/tests -q -p no:cacheprovider --basetemp <fresh-temporary-directory>
```

The parser writes case_record.json, capture_export.json and form_review.json. It supplies canonical capture timestamps and preserves source hash/consent/workflow mapping in the separate review report. Default status is draft. Explicit --case-signed-off is an operator attestation after reviewer approval, not signature authentication. Name / YYYY-MM-DD signatures map to canonical name/date; otherwise the operator must explicitly supply both fields. Literal unknown cannot identify the reviewer.

Blank narrative boxes remain empty strings and are flagged. Missing/unknown enum choices are refused before canonical publication. Part D signatures alone do not approve the case. The parser requires reviewed case/family IDs and a complete base export or an explicit standalone-family attestation; duplicate IDs, invalid members and conflicting workflow answers fail without silently dropping records. Derived splits still follow the strictest family question.

## Verification result

The full offline pack suite passed **123 tests**. An independent review reran the three pack test files and also reported **123 passed**. Coverage includes canonical field parity, rejection of the retired contract by downstream tools, exact string criteria, default draft behavior, signoff mapping, enum gaps, blank boxes, family holdouts, merged exports, actual hindsight/reference leakage and the mocked first-case scoring flow. No live model, EC2 or database calls were made.

The literal unknown marker is treated consistently as missing knowledge for the single canonical contract. Other hindsight/reference strings, including escaped values, still fail before transport. Human review remains necessary for paraphrased hindsight, source rights, signature authenticity and engineering acceptance.
