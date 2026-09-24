# Case Capture implementation verification

24 September 2026. All checks were local. No EC2 start, model request, training,
cloud write or push was performed. The database-read SYN-001 and example export
in output/expert-capture were preserved; copies in tests/fixtures retain the
same JSON values. The two signed fixtures are explicitly synthetic test records.

## Import demonstrations

The supplied example export produced:

| Case | Disposition | Reason |
| --- | --- | --- |
| SYN-001 | eval-only | status=draft; permitted_use=reference_only; excluded from training |

Counts: **1 case file, 1 evaluation question, 0 training candidates**.

The three-case fixture export produced:

| Case | Disposition | Reason |
| --- | --- | --- |
| SYN-001 | eval-only | status=draft; permitted_use=reference_only |
| SYN-TRAIN-001 | imported | signed/training; family split=train |
| SYN-TRAIN-002 | imported | signed/training; family split=train |

Counts: **3 case files, 3 evaluation questions, 2 training candidates**.

Commands from the repository root (use fresh output directories):

```powershell
python packs/oil-gas/scripts/import_cases.py output/expert-capture/case_capture_export.example.json tmp/capture-example
python packs/oil-gas/scripts/import_cases.py packs/oil-gas/tests/fixtures/three_cases_export.json tmp/capture-three-cases
python -m pytest packs/oil-gas/tests -q -p no:cacheprovider
python -m pytest packs/oil-gas/tests -q -k 'leak or hindsight or brief' -p no:cacheprovider
```

## Test evidence

Complete suite: **38 passed in 2.51 seconds**, Python 3.13, jsonschema 4.26.0,
pytest 9.0.3. A fresh system temporary directory was passed with --basetemp.
An earlier workspace-temporary run hit one Windows access-denied error during
snapshot rename; no partial snapshot was published. The fresh full run passed
without code changes for that filesystem error.

Focused brief/leak suite: **8 passed, 30 deselected**. It checks the exact
decision-time projection, blocks injected hindsight/reference answers and
extra fields/system content before transport, and covers quoted/multiline
strings despite JSON escaping. The actual seed passes dry-run rendering.
A separate `python -O` probe confirmed the leak guard still raises.

Real Foundry integration was imported and refused missing explicit loopback
configuration before transport. Its global environment emits the existing
Requests dependency warning. No inference request was sent. The earlier
Foundry follow-up suite finished **206 passed, 3 warnings**, committed as
cd9fc19 on codex/broadbridge-gate1-data-training.

Review also caught a training-validator gap for dev/locked_test/no-question
cases. Three tests first failed, then passed after the admission fix. The CLI
validates every member of an export; validate a complete export rather than
an isolated case when certifying family closure.

## Files added for capture

```text
packs/oil-gas/
  CAPTURE_VERIFICATION.md
  requirements-capture.txt
  run_brief.py
  schemas/
    case_record.schema.json
    export.schema.json
  scripts/
    case_contract.py
    validate_cases.py
    import_cases.py
    run_brief.py
  tests/
    test_case_capture.py
    fixtures/
      SYN-001.json
      SYN-TRAIN-001.json
      SYN-TRAIN-002.json
      capture_export.json
      three_cases_export.json
```

The pack README and canonical infrastructure brief (Markdown and Word) were
updated. All 11 Word pages were rendered and visually inspected. The Interview
Guide is unchanged. scripts/case_from_form.py was never created and is explicitly
cancelled in the plan. Gate 0 remains open for production acceptance.

The seed's evidence array is empty. Its populated-item field names come from
the user contract; available_at_decision_time currently accepts string or
Boolean pending a populated export. The other observed narrative fields,
including evidence_ids, tolerance and hard_fail_criteria, remain strings.
