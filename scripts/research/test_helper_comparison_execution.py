"""Bounded v2 execution and scoring; HTTP is always mocked in this suite."""
import copy
import csv
from datetime import datetime, timedelta, timezone
import importlib
import json
import os
from pathlib import Path
import socket
import sys

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_helper_comparison as prep


def api():
    assert importlib.util.find_spec('run_helper_comparison'), 'v2 executor missing'
    return importlib.import_module('run_helper_comparison')


@pytest.fixture
def packet(tmp_path):
    path = tmp_path/'packet'
    prep.prepare(path)
    return path


def foundry():
    if not os.environ.get('SLM_FOUNDRY_PATH'):
        pytest.skip('Select the Foundry helper-receipts checkout via SLM_FOUNDRY_PATH')
    return Path(os.environ['SLM_FOUNDRY_PATH'])


def run_mock(packet, out, monkeypatch, failure=None):
    module = api()
    def no_network(*args, **kwargs):
        raise AssertionError('Offline rehearsal must never open a socket')
    monkeypatch.setattr(socket.socket, 'connect', no_network)
    return module.execute(packet, out, foundry(), mode='mock', mock_failure=failure)


def fill_scores(run, path, *, score='2', critical='NO', dispute='NO'):
    rows = list(csv.DictReader((run/'scores.csv').open(encoding='utf-8')))
    for row in rows:
        if row['response_status'] == 'valid':
            row.update(score=score, critical_error=critical, reference_dispute=dispute,
                       hard_fail_matched='NO', reviewer='SYNTHETIC REVIEWER',
                       review_date='2026-09-28', review_seconds='60', notes='Mock scoring only.')
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    return rows


def test_mock_executes_actual_foundry_http_contract_and_preserves_all_pairs(packet, tmp_path, monkeypatch):
    original = (packet/'checksums.json').read_bytes()
    run = tmp_path/'run'
    result = run_mock(packet, run, monkeypatch)
    assert result['mode'] == 'mock' and result['live_calls'] == 0
    assert result['calls_attempted'] == 20
    assert result['status'] == 'completed'
    assert result['training_approved'] is False
    assert len(result['slots']) == 20
    assert all(s['status'] == 'valid' and s['receipt']['raw_response_sha256'] for s in result['slots'])
    assert all(s['receipt']['request_sha256'] == s['request_sha256'] for s in result['slots'])
    assert all(not r['score'] for r in csv.DictReader((run/'scores.csv').open()))
    assert (packet/'checksums.json').read_bytes() == original
    assert (run/'review.md').exists()
    assert 'mistral' not in (run/'review.md').read_text(encoding='utf-8').lower()
    assert 'qwen' not in (run/'review.md').read_text(encoding='utf-8').lower()


@pytest.mark.parametrize('failure', ['timeout', 'unknown_cost', 'identity', 'length', 'citation', 'schema', 'over_budget'])
def test_second_slot_failure_stops_both_arms_no_retry_and_retains_billing(packet, tmp_path, monkeypatch, failure):
    result = run_mock(packet, tmp_path/'run', monkeypatch, {'index': 1, 'kind': failure})
    assert result['calls_attempted'] == 2
    assert [s['status'] for s in result['slots']] == ['valid', 'failed'] + ['not_run']*18
    assert result['status'] == 'stopped'
    assert result['slots'][1]['error']
    if failure in {'timeout', 'unknown_cost'}:
        assert result['billing_complete'] is False
        assert float(result['held_reservations_usd']) > 0
    else:
        assert result['billing_complete'] is True
        assert float(result['known_cost_usd']) > 0


def test_first_failure_does_not_run_other_model(packet, tmp_path, monkeypatch):
    result = run_mock(packet, tmp_path/'run', monkeypatch, {'index': 0, 'kind': 'timeout'})
    assert result['calls_attempted'] == 1
    assert result['slots'][1]['status'] == 'not_run'


def test_packet_tampering_and_overwrite_rejected_before_network(packet, tmp_path, monkeypatch):
    run_mock(packet, tmp_path/'run', monkeypatch)
    with pytest.raises(FileExistsError):
        run_mock(packet, tmp_path/'run', monkeypatch)
    with (packet/'requests.jsonl').open('a') as handle:
        handle.write('\n')
    with pytest.raises(ValueError, match='hash'):
        run_mock(packet, tmp_path/'tampered', monkeypatch)
    assert not (tmp_path/'tampered').exists()


def test_rehashed_edited_request_is_rejected_by_recompilation(packet, tmp_path, monkeypatch):
    rows = (packet/'requests.jsonl').read_text(encoding='utf-8').splitlines()
    row = json.loads(rows[0]); row['messages'][0]['content'] += ' injected instructions'
    rows[0] = json.dumps(row)
    (packet/'requests.jsonl').write_text('\n'.join(rows)+'\n', encoding='utf-8')
    checks = json.loads((packet/'checksums.json').read_text())
    checks['requests.jsonl'] = prep.sha((packet/'requests.jsonl').read_bytes())
    prep.v1.write_json(packet/'checksums.json', checks)
    with pytest.raises(ValueError, match='compiled'):
        run_mock(packet, tmp_path/'tampered', monkeypatch)


def test_live_refuses_absent_approval_before_keys_or_http(packet, tmp_path, monkeypatch):
    monkeypatch.setattr(requests, 'post', lambda *a, **k: pytest.fail('HTTP before approval'))
    with pytest.raises(ValueError, match='approval'):
        api().execute(packet, tmp_path/'live', foundry(), mode='live')
    assert not (tmp_path/'live').exists()


@pytest.mark.parametrize('empty', [{}, None, [], False])
def test_empty_live_approval_cannot_select_mock_preflight_defaults(packet, tmp_path, monkeypatch, empty):
    module = api(); approval = tmp_path/'empty.json'; module.stamp(approval, empty)
    monkeypatch.setattr(module, 'git_state', lambda root: {'commit': 'a'*40, 'dirty': False})
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-only')
    monkeypatch.setattr(requests, 'post', lambda *a, **k: pytest.fail('Approval bypass reached HTTP'))
    with pytest.raises(ValueError, match='approval'):
        module.execute(packet, tmp_path/'live', foundry(), mode='live', approval=approval,
                       approve_hash='intentionally-wrong')
    assert not (tmp_path/'live').exists()


def test_mock_full_review_cannot_become_real_quality_approval(packet, tmp_path, monkeypatch):
    run = tmp_path/'run'; run_mock(packet, run, monkeypatch)
    scores = tmp_path/'review.csv'; fill_scores(run, scores)
    report = api().aggregate(run, scores, tmp_path/'report')
    assert report['reviewed_slots'] == 20 and report['matched_pairs'] == 10
    assert report['proposed_screen_passed'] is True
    assert report['decision_eligible'] is False
    assert report['model_selection_approved'] is False
    assert report['cost_per_accepted_answer_usd'] is None
    for model in report['models'].values():
        assert model['paired_mean'] == 2
        assert set(model['per_type_mean'].values()) == {2}
    assert report['review_minutes'] == 20


def test_blank_partial_and_disputed_scores_are_holds(packet, tmp_path, monkeypatch):
    run = tmp_path/'run'; run_mock(packet, run, monkeypatch)
    module = api()
    blank = module.aggregate(run, run/'scores.csv', tmp_path/'blank')
    assert blank['matched_pairs'] == 0
    assert blank['unreviewed_slots'] == 20
    assert blank['models']['mistral']['paired_mean'] is None
    scores = tmp_path/'review.csv'; fill_scores(run, scores, dispute='YES')
    disputed = module.aggregate(run, scores, tmp_path/'disputed')
    assert disputed['reference_disputes'] == 20
    assert disputed['proposed_screen_passed'] is False


@pytest.mark.parametrize('field,value', [('response_sha256', 'bad'), ('score', '3'),
    ('critical_error', 'YES'), ('hard_fail_matched', 'YES'), ('review_seconds', 'NaN'), ('reviewer', ''),
    ('review_date', 'not-a-date'), ('type', 'invented')])
def test_stale_or_invalid_review_rejected(packet, tmp_path, monkeypatch, field, value):
    run = tmp_path/'run'; run_mock(packet, run, monkeypatch)
    scores = tmp_path/'review.csv'; rows = fill_scores(run, scores)
    rows[0][field] = value
    with scores.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    with pytest.raises(ValueError):
        api().aggregate(run, scores, tmp_path/'bad')


def test_failed_response_cannot_receive_engineering_grade(packet, tmp_path, monkeypatch):
    run = tmp_path/'run'; run_mock(packet, run, monkeypatch, {'index': 0, 'kind': 'timeout'})
    scores = tmp_path/'review.csv'; rows = fill_scores(run, scores)
    rows[0].update(score='0', critical_error='YES')
    with scores.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    with pytest.raises(ValueError, match='unavailable'):
        api().aggregate(run, scores, tmp_path/'bad')


def test_valid_zero_with_hard_fail_is_counted_not_dropped(packet, tmp_path, monkeypatch):
    run = tmp_path/'run'; run_mock(packet, run, monkeypatch)
    scores = tmp_path/'review.csv'; fill_scores(run, scores, score='0', critical='YES')
    report = api().aggregate(run, scores, tmp_path/'report')
    assert report['critical_errors'] == 20
    assert report['proposed_screen_passed'] is False
    assert report['models']['mistral']['paired_mean'] == 0


def test_stage_b_mock_retains_development_label(tmp_path, monkeypatch):
    packet = tmp_path/'b'; prep.prepare(packet, 'stage_b')
    run = run_mock(packet, tmp_path/'run', monkeypatch)
    assert run['calls_attempted'] == 40
    assert run['evaluation_role'] == 'development_calibration'


def fake_approval(packet, tmp_path):
    """Fabricated local attestations for software tests, never used with real HTTP."""
    module = api(); directory = tmp_path/'approval'
    approved = module.plan(packet, directory, foundry())
    now = datetime.now(timezone.utc)
    approved.update(approved_by='SYNTHETIC OPERATOR', technical_reviewer='SYNTHETIC REVIEWER',
                    run_id='TEST-ONLY', approved_at=now.isoformat(), expires_at=(now+timedelta(minutes=30)).isoformat())
    for key in ('rights_and_cloud_route_accepted', 'protocol_and_references_accepted',
                'quality_screen_accepted', 'account_spend_limit_verified'):
        approved[key] = True
    evidence = directory/'test-evidence.txt'; evidence.write_text('MOCK ONLY — not provider evidence', encoding='utf-8')
    digest = prep.sha(evidence.read_bytes())
    approved.update(evidence_files={evidence.name: digest}, cloud_approval_sha256=digest)
    for provider in approved['providers'].values():
        provider.update(endpoint_snapshot_sha256=digest, controls_verified=True)
    for request in approved['requests']:
        request.update(input_tokens_upper_bound=8192, includes_template_schema_overhead=True,
                       method='provider_count', evidence_sha256=digest)
    path = directory/'approval.json'; module.stamp(path, approved)
    return path, approved


def test_approval_template_is_actionable_but_cannot_authorize_calls(packet, tmp_path):
    module = api(); approved = module.plan(packet, tmp_path/'plan', foundry())
    assert len(approved['requests']) == 20
    assert all(len(r['request_sha256']) == 64 for r in approved['requests'])
    assert approved['approved_by'] is None
    assert approved['rights_and_cloud_route_accepted'] is False
    assert (tmp_path/'plan/wire_requests.jsonl').exists()


@pytest.mark.parametrize('mutation', ['none', 'expired', 'wrong-packet', 'wrong-commit', 'no-reviewer',
    'rights', 'budget', 'nan-budget', 'evidence', 'reasoning', 'tokens', 'wire', 'revisions', 'overhead'])
def test_exact_approval_validation(packet, tmp_path, mutation):
    module = api(); path, approved = fake_approval(packet, tmp_path)
    config, _, stage, rows, packet_hash = module.read_packet(packet)
    context = {'config': config, 'stage': stage, 'packet_sha256': packet_hash,
               'domain_commit': approved['domain_commit'], 'foundry_commit': approved['foundry_commit']}
    payloads = [json.loads(line) for line in (path.parent/'wire_requests.jsonl').read_text(encoding='utf-8').splitlines()]
    if mutation == 'expired': approved['expires_at'] = approved['approved_at']
    if mutation == 'wrong-packet': approved['packet_sha256'] = '0'*64
    if mutation == 'wrong-commit': approved['foundry_commit'] = '0'*40
    if mutation == 'no-reviewer': approved['technical_reviewer'] = ''
    if mutation == 'rights': approved['rights_and_cloud_route_accepted'] = False
    if mutation == 'budget': approved['stage_ceiling_usd'] = '10'
    if mutation == 'nan-budget': approved['total_ceiling_usd'] = 'NaN'
    if mutation == 'evidence': approved['cloud_approval_sha256'] = '0'*64
    if mutation == 'reasoning': approved['providers']['mistral']['reasoning_mode'] = 'exclude'
    if mutation == 'tokens': approved['requests'][0]['input_tokens_upper_bound'] = 8193
    if mutation == 'wire': approved['requests'][0]['request_sha256'] = '0'*64
    if mutation == 'revisions': del approved['providers']['mistral']['weights_revision']
    if mutation == 'overhead': approved['requests'][0]['includes_template_schema_overhead'] = False
    module.stamp(path, approved)
    if mutation == 'none':
        assert module.validate_approval(path, prep.sha(path.read_bytes()), context, payloads) == approved
    else:
        with pytest.raises(ValueError):
            module.validate_approval(path, prep.sha(path.read_bytes()), context, payloads)


def test_live_path_with_mocked_http_consumes_approval_once(packet, tmp_path, monkeypatch):
    module = api(); path, approved = fake_approval(packet, tmp_path)
    def git(root):
        key = 'domain_commit' if Path(root).resolve() == prep.ROOT.resolve() else 'foundry_commit'
        return {'commit': approved[key], 'dirty': False}
    monkeypatch.setattr(module, 'git_state', git)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'fake-key-for-mocked-http')
    monkeypatch.setattr(requests, 'post', module.mock_http())
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Real HTTP forbidden'))
    digest = prep.sha(path.read_bytes())
    result = module.execute(packet, tmp_path/'run', foundry(), mode='live', approval=path, approve_hash=digest)
    assert result['calls_attempted'] == 20
    assert result['status'] == 'completed'
    assert Path(str(path)+'.used').exists()
    with pytest.raises(FileExistsError):
        module.execute(packet, tmp_path/'duplicate', foundry(), mode='live', approval=path, approve_hash=digest)


def test_budget_stops_before_starting_a_pair_that_cannot_fit(packet, tmp_path, monkeypatch):
    module = api(); path, approved = fake_approval(packet, tmp_path)
    approved['stage_ceiling_usd'] = str(module.bound(prep.load_protocol())*2)
    module.stamp(path, approved)
    monkeypatch.setattr(module, 'git_state', lambda root: {
        'commit': approved['domain_commit' if Path(root).resolve() == prep.ROOT.resolve() else 'foundry_commit'], 'dirty': False})
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-only')
    monkeypatch.setattr(requests, 'post', module.mock_http())
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Network forbidden'))
    result = module.execute(packet, tmp_path/'run', foundry(), mode='live', approval=path,
                            approve_hash=prep.sha(path.read_bytes()))
    assert result['calls_attempted'] == 2
    assert result['stop_reason'] == 'pair_budget_exhausted'
    assert [s['status'] for s in result['slots']] == ['valid', 'valid'] + ['not_run']*18


def test_unpaired_review_has_no_paired_quality_mean(packet, tmp_path, monkeypatch):
    module = api(); run = tmp_path/'run'; run_mock(packet, run, monkeypatch)
    path = tmp_path/'review.csv'; rows = fill_scores(run, path)
    for row in rows[1:]:
        for key in module.REVIEW: row[key] = ''
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    result = module.aggregate(run, path, tmp_path/'report')
    assert result['reviewed_slots'] == 1 and result['matched_pairs'] == 0
    assert all(m['paired_mean'] is None for m in result['models'].values())


def test_edited_saved_answer_is_rejected_before_scoring(packet, tmp_path, monkeypatch):
    module = api(); run = tmp_path/'run'; run_mock(packet, run, monkeypatch)
    result = module.load(run/'run.json'); result['slots'][0]['response']['answer'] = 'changed'
    module.stamp(run/'run.json', result)
    with pytest.raises(ValueError, match='hash'):
        module.aggregate(run, run/'scores.csv', tmp_path/'report')


def test_both_reservations_are_durable_before_http(packet, tmp_path, monkeypatch):
    module = api(); run = tmp_path/'run'; original = module.mock_http
    def recording(failure):
        respond = original(failure)
        def post(*args, **kwargs):
            checkpoint = module.load(run/'run.json')
            attempting = next(s for s in checkpoint['slots'] if s['status'] == 'attempting')
            assert float(attempting['reservation_usd']) > 0
            if checkpoint['calls_attempted'] % 2 == 1:
                assert float(checkpoint['held_reservations_usd']) >= 2*float(attempting['reservation_usd'])
            return respond(*args, **kwargs)
        return post
    monkeypatch.setattr(module, 'mock_http', recording)
    assert run_mock(packet, run, monkeypatch)['status'] == 'completed'


def test_stage_b_refuses_mock_prior_even_when_scores_are_perfect(packet, tmp_path, monkeypatch):
    module = api(); run = tmp_path/'a'; run_mock(packet, run, monkeypatch)
    scores = tmp_path/'scores.csv'; fill_scores(run, scores)
    approved = {'prior_stage_a': {'run_dir': str(run), 'scores_file': str(scores),
                                'run_sha256': prep.sha((run/'run.json').read_bytes()),
                                'scores_sha256': prep.sha(scores.read_bytes())}}
    with pytest.raises(ValueError, match='reviewed live A'):
        module.prior_stage(approved, prep.load_protocol())


def test_live_stage_b_report_includes_prior_a_pairs_and_costs_with_http_mocked(packet, tmp_path, monkeypatch):
    module = api(); a_path, a_approval = fake_approval(packet, tmp_path/'a')
    monkeypatch.setattr(module, 'git_state', lambda root: {
        'commit': a_approval['domain_commit' if Path(root).resolve() == prep.ROOT.resolve() else 'foundry_commit'], 'dirty': False})
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-only')
    monkeypatch.setattr(requests, 'post', module.mock_http())
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Network forbidden'))
    a_run = tmp_path/'a/run'
    module.execute(packet, a_run, foundry(), mode='live', approval=a_path, approve_hash=prep.sha(a_path.read_bytes()))
    a_scores = tmp_path/'a/scores.csv'; fill_scores(a_run, a_scores)
    b_packet = tmp_path/'b/packet'; prep.prepare(b_packet, 'stage_b')
    b_path, b_approval = fake_approval(b_packet, tmp_path/'b')
    b_approval['prior_stage_a'] = {'run_dir': str(a_run), 'scores_file': str(a_scores),
                                 'run_sha256': prep.sha((a_run/'run.json').read_bytes()),
                                 'scores_sha256': prep.sha(a_scores.read_bytes())}
    module.stamp(b_path, b_approval)
    b_run = tmp_path/'b/run'
    module.execute(b_packet, b_run, foundry(), mode='live', approval=b_path, approve_hash=prep.sha(b_path.read_bytes()))
    b_scores = tmp_path/'b/scores.csv'; fill_scores(b_run, b_scores)
    report = module.aggregate(b_run, b_scores, tmp_path/'combined')
    assert report['aggregation_scope'] == 'stage_a_and_b'
    assert report['planned_slots'] == report['reviewed_slots'] == 60
    assert report['matched_pairs'] == 30
    assert float(report['known_cost_usd']) == pytest.approx(0.006)
    assert float(report['cost_per_accepted_answer_usd']) == pytest.approx(0.0001)
    assert report['review_minutes'] == 60
