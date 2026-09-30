"""Review packaging must catch changed evidence, leakage and false approval."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from prepare_pressure_demo import build


def module():
    path = HERE / 'prepare_bill_meeting.py'
    assert path.is_file(), 'Meeting preparation validator is not implemented'
    spec = importlib.util.spec_from_file_location('bill_meeting', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def package(tmp_path):
    path = tmp_path / 'pressure'
    build(path)
    return path


def edit(package, name, change):
    import hashlib
    path = package / name
    value = json.loads(path.read_text()) if name.endswith('.json') else [json.loads(x) for x in path.read_text().splitlines()]
    change(value)
    path.write_text(json.dumps(value) if name.endswith('.json') else ''.join(json.dumps(x)+'\n' for x in value))
    if name != 'manifest.json':
        m = json.loads((package / 'manifest.json').read_text())
        m['artifacts'][name] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        (package / 'manifest.json').write_text(json.dumps(m))


def test_review_bundle_has_real_counts_but_no_execution_permission(package, tmp_path):
    result = module().prepare(package, tmp_path / 'meeting')
    assert result['status'] == 'review_ready_execution_blocked'
    assert result['candidate_count'] == 36 and result['probe_count'] == 8
    assert result['execution_authorized'] is False
    assert result['optimizer_steps_observed'] == result['model_calls_observed'] == 0
    assert {x['id'] for x in result['open_gates']} == {'source_use', 'family_allocation', 'release', 'host_packet', 'execution'}
    out = tmp_path / 'meeting'
    assert (out / 'index.html').is_file()
    assert not (out / 'authorization.json').exists()
    assert not (out / 'train.jsonl').exists()
    request = json.loads((out / 'execution-request.json').read_text())
    assert request['approved_by'] is None and request['release_id'] is None
    assert request['limits']['optimizer_steps'] == 20
    assert request['limits']['comparison_model_calls_max'] == 16
    assert request['independent_test_count'] == 0


def test_modified_artifact_is_refused_before_output(package, tmp_path):
    (package / 'demo_prompts.jsonl').write_text('{}\n')
    with pytest.raises(ValueError, match='hash|bytes'):
        module().prepare(package, tmp_path / 'meeting')
    assert not (tmp_path / 'meeting').exists()


@pytest.mark.parametrize('change', [
    lambda m: m.update(training_approved=True),
    lambda m: m.update(execution_authorized=True),
    lambda m: m.update(actual_bill_signoff={'name': 'Bill'}),
    lambda m: m['proposed_limits'].update(host_wall_seconds=7200),
    lambda m: m['proposed_limits'].update(optimizer_steps=200),
    lambda m: m['comparison'].update(thinking=True),
])
def test_cannot_turn_review_into_authorized_or_larger_run(package, tmp_path, change):
    edit(package, 'manifest.json', change)
    with pytest.raises(ValueError):
        module().prepare(package, tmp_path / 'meeting')


@pytest.mark.parametrize('change', [
    lambda rows: rows[0].update(split='train'),
    lambda rows: rows[0].update(family_id='different-family'),
    lambda rows: rows[0].update(training_approved=True),
])
def test_cannot_admit_pending_candidates_by_rehashing(package, tmp_path, change):
    edit(package, 'train_candidates.jsonl', change)
    with pytest.raises(ValueError):
        module().prepare(package, tmp_path / 'meeting')


def test_answer_in_model_input_is_refused_even_with_fresh_hash(package, tmp_path):
    edit(package, 'demo_prompts.jsonl', lambda rows: rows[0]['messages'].append({'role': 'assistant', 'content': '40.6 psia'}))
    with pytest.raises(ValueError, match='prompt|answer'):
        module().prepare(package, tmp_path / 'meeting')


def test_missing_question_and_duplicate_ids_are_refused(package, tmp_path):
    edit(package, 'demo_prompts.jsonl', lambda rows: rows[0].update(question_id=rows[1]['question_id']))
    with pytest.raises(ValueError, match='question|probe'):
        module().prepare(package, tmp_path / 'meeting')


def test_existing_meeting_material_is_preserved(package, tmp_path):
    out = tmp_path / 'meeting'
    out.mkdir()
    (out / 'notes.json').write_text('preserve')
    with pytest.raises(ValueError, match='fresh'):
        module().prepare(package, out)
    assert (out / 'notes.json').read_text() == 'preserve'
