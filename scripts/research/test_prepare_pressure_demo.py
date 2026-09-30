"""Offline package checks: incorrect math, answer leakage and fake admission fail."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).parent


def module():
    path = HERE / 'prepare_pressure_demo.py'
    assert path.exists(), 'The offline demonstration package builder is missing'
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location('pressure_demo', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_candidates_keep_one_family_and_do_not_grant_permission():
    rows = module().training_rows()
    assert len(rows) == 36
    assert len({r['example_id'] for r in rows}) == 36
    assert {r['family_id'] for r in rows} == {'DOE-HDBK-1012'}
    assert all(r['split'] is None and r['proposed_split'] == 'train' for r in rows)
    assert all(r['training_approved'] is False and r['rights_status'] == 'TBD' for r in rows)
    assert {r['type'] for r in rows} == {'brief', 'calculation', 'missing_data', 'grounded_explanation', 'abstention'}


@pytest.mark.parametrize('example,want', [('DOE-DEMO-CALC-01', '34.2'), ('DOE-DEMO-CALC-02', '11.2'), ('DOE-DEMO-CALC-24', '5.6')])
def test_generated_answers_have_hand_checked_sign_and_units(example, want):
    row = next(r for r in module().training_rows() if r['example_id'] == example)
    answer = json.loads(row['messages'][-1]['content'])
    assert answer['calculation']['result'] == want
    assert answer['calculation']['unit'] == 'psia'
    assert answer['source_ids'] == ['DOE-HDBK-1012-1-92:pdf-036']


def test_probes_do_not_contain_reference_answers_or_claim_independence():
    prompts, keys = module().demonstration_rows()
    assert len(prompts) == len(keys) == 8
    assert {p['question_id'] for p in prompts} == {k['question_id'] for k in keys}
    train_prompts = {r['messages'][1]['content'] for r in module().training_rows()}
    for prompt, key in zip(prompts, keys):
        assert [m['role'] for m in prompt['messages']] == ['system', 'user']
        assert prompt['messages'][1]['content'] not in train_prompts
        assert key['reference_answer'] not in json.dumps(prompt)
        assert 'hard_fail_criteria' not in prompt
        assert prompt['independent_test'] is False
    assert keys[0]['calculation']['result'] == '40.6'
    assert keys[1]['calculation']['result'] == '13.2'
    assert keys[2]['calculation']['result'] == '7.1'


def test_pinned_input_change_is_rejected(tmp_path):
    path = tmp_path / 'proposal.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='hash'):
        module().verify_file(path, 'a' * 64)


def test_training_targets_cite_evidence_actually_supplied_and_match_response_schema():
    from jsonschema import Draft202012Validator
    m = module()
    for row in m.training_rows():
        target = json.loads(row['messages'][-1]['content'])
        Draft202012Validator(m.RESPONSE_SCHEMA).validate(target)
        assert all(identifier in row['messages'][1]['content'] for identifier in target['source_ids'])


def test_package_preserves_old_diagnostic_and_has_no_release_authorization(tmp_path):
    m = module()
    historical = HERE.parents[1] / 'packs/oil-gas/eval/pressure-diagnostic-v1/manifest.json'
    before = historical.read_bytes()
    out = tmp_path / 'package'
    m.build(out)
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['training_approved'] is False
    assert manifest['execution_authorized'] is False
    assert manifest['family_transition']['status'] == 'proposed_not_applied'
    assert manifest['counts'] == {'train_candidates': 36, 'demo_probes': 8, 'independent_validation': 0, 'independent_test': 0}
    assert historical.read_bytes() == before
    assert not (out / 'authorization.json').exists()
    assert not (out / 'train.jsonl').exists()
    for name, value in manifest['artifacts'].items():
        payload = (out / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == value['sha256']
        assert len(payload) == value['bytes']


def test_existing_package_not_overwritten(tmp_path):
    out = tmp_path / 'existing'
    out.mkdir()
    (out / 'keep').write_text('preserve')
    with pytest.raises(ValueError, match='fresh'):
        module().build(out)
    assert (out / 'keep').read_text() == 'preserve'
