"""Offline FQ-07 packets must not leak references, call models or rewrite v1."""
import copy
import hashlib
import importlib
import json
from collections import Counter
from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))


def api():
    assert importlib.util.find_spec('prepare_helper_comparison') is not None, 'FQ-07 packet builder missing'
    return importlib.import_module('prepare_helper_comparison')


def test_preparation_emits_balanced_pairs_without_network_or_fake_results(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('Network is forbidden in offline preparation')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    module = api()
    before = module.SAMPLE.read_bytes()
    summary = module.prepare(tmp_path / 'new')
    assert summary['calls_attempted'] == 0
    assert summary['training_approved'] is False
    assert summary['live_authorized'] is False
    assert summary['question_count'] == 10
    assert summary['source_count'] == 10
    assert summary['family_count'] == 9
    assert summary['type_counts'] == dict.fromkeys(module.v1.TYPES, 2)
    rows = [json.loads(line) for line in (tmp_path/'new/requests.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 20
    assert Counter(r['model_key'] for r in rows) == {'mistral': 10, 'qwen': 10}
    assert [r['model_key'] for r in rows[:4]] == ['mistral', 'qwen', 'qwen', 'mistral']
    for first, second in zip(rows[::2], rows[1::2]):
        assert first['messages'] == second['messages']
        assert first['response_schema'] == second['response_schema']
        assert first['status'] == second['status'] == 'prepared_not_run'
        assert first['returned_model'] is None and first['actual_cost_usd'] is None
        payload = json.loads(first['messages'][1]['content'])
        assert len(payload['questions']) == 1
    assert module.SAMPLE.read_bytes() == before
    assert summary['proposed_stage_ceiling_usd'] == '0.10'
    assert summary['conditional_token_cost_bound_usd'] == '0.061152'


def test_selected_question_and_all_reviewer_fields_stay_separate():
    module = api(); sample = module.v1.load_sample(module.SAMPLE)
    for q in sample['questions']:
        q['reference_answer'] = 'DO_NOT_SEND_REFERENCE_ANSWER'
        q['hard_fail_criteria'] = 'DO_NOT_SEND_FAILURE_CRITERIA'
        q['tolerance'] = {'DO_NOT_SEND_TOLERANCE': True}
    q = sample['questions'][0]
    messages = module.messages_for(sample, q)
    rendered = json.dumps(messages)
    assert 'DO_NOT_SEND' not in rendered
    body = json.loads(messages[1]['content'])
    assert set(body['questions'][0]) == {'question_id', 'type', 'question'}
    assert body['questions'][0]['question_id'] == 'PUB-001'
    assert all(k not in rendered for k in ('reference_answer', 'hard_fail_criteria', 'tolerance'))


def test_approval_hashes_verify_the_emitted_protocol_and_input_snapshots(tmp_path):
    module = api(); output = tmp_path/'bound'
    summary = module.prepare(output)
    for field, filename in [('sample_sha256', 'sample.json'),
                            ('protocol_sha256', 'protocol.json'), ('prompt_sha256', 'prompt.md')]:
        assert hashlib.sha256((output/filename).read_bytes()).hexdigest() == summary[field]


@pytest.mark.parametrize('mutation', ['hash', 'private', 'duplicate', 'type-coverage', 'training'])
def test_invalid_sample_or_selection_refused_before_output(tmp_path, mutation):
    module = api(); config = module.load_protocol(); sample_bytes = module.SAMPLE.read_bytes()
    sample = json.loads(sample_bytes)
    if mutation == 'hash':
        sample_bytes += b' '
    elif mutation == 'private':
        sample['sources'][0]['confidentiality'] = 'internal'
    elif mutation == 'duplicate':
        config['stages']['stage_a']['question_ids'][1] = 'PUB-001'
    elif mutation == 'type-coverage':
        config['stages']['stage_a']['question_ids'][0] = 'PUB-002'
        config['stages']['stage_b']['question_ids'].remove('PUB-002')
        config['stages']['stage_b']['question_ids'].append('PUB-001')
    elif mutation == 'training':
        sample['questions'][0]['permitted_use'] = 'training'
    if mutation in {'private', 'training'}:
        sample_bytes = module.v1.canonical(sample)
        config['base_sample_sha256'] = module.sha(sample_bytes)
    with pytest.raises(ValueError):
        module.validate_inputs(config, sample, sample_bytes)


def test_changed_evidence_and_oversized_requests_are_not_silently_truncated():
    module = api(); sample = module.v1.load_sample(module.SAMPLE)
    config = module.load_protocol(); sample['sources'][0]['blocks'][0]['text'] += ' drift'
    with pytest.raises(ValueError, match='hash'):
        module.v1.validate_sample(sample)
    sample = module.v1.load_sample(module.SAMPLE)
    config['limits']['max_request_bytes'] = 10
    with pytest.raises(ValueError, match='request.*limit'):
        module.build_requests(config, sample, 'stage_a')


def test_stage_b_is_remaining_development_questions_not_a_holdout(tmp_path):
    module = api(); summary = module.prepare(tmp_path/'b', stage='stage_b')
    assert summary['question_count'] == 20 and summary['request_count'] == 40
    assert summary['type_counts'] == dict.fromkeys(module.v1.TYPES, 4)
    assert summary['evaluation_role'] == 'development_calibration'
    assert summary['live_authorized'] is False
    assert summary['conditional_token_cost_bound_usd'] == '0.122304'


def test_existing_outputs_and_frozen_v1_cannot_be_overwritten(tmp_path):
    module = api(); output = tmp_path/'existing'; output.mkdir()
    marker = output/'keep'; marker.write_text('original')
    with pytest.raises(FileExistsError):
        module.prepare(output)
    assert marker.read_text() == 'original'
    assert sorted(p.name for p in output.iterdir()) == ['keep']
    with pytest.raises(FileExistsError):
        module.prepare(module.SAMPLE.parent)


def test_response_is_one_question_with_exact_unmodified_citations():
    module = api(); sample = module.v1.load_sample(module.SAMPLE)
    q = sample['questions'][0]; source = sample['sources'][0]; block = source['blocks'][0]
    response = {'question_id': q['question_id'], 'answer': 'Synthetic test answer.',
                'evidence': [{'source_id': source['source_id'], 'block_id': block['block_id'],
                              'quote': block['text'][:60]}], 'uncertainties': []}
    assert module.check_answer(sample, q, response) == []
    bad = copy.deepcopy(response); bad['evidence'][0]['quote'] = 'fabricated quote'
    assert 'invalid_exact_citation' in module.check_answer(sample, q, bad)
    bad = copy.deepcopy(response); bad['question_id'] = 'PUB-999'
    assert 'response_schema_failed' in module.check_answer(sample, q, bad)
    bad = copy.deepcopy(response); bad['answer'] = 'x' * 1001
    assert 'response_schema_failed' in module.check_answer(sample, q, bad)


def test_cli_has_no_live_mode(tmp_path):
    module = api()
    with pytest.raises(SystemExit) as exc:
        module.main(['--live', '--out', str(tmp_path/'blocked')])
    assert exc.value.code == 2
    assert not (tmp_path/'blocked').exists()
