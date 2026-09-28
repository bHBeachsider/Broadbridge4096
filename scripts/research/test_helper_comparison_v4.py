"""Same-model SiliconFlow amendment; network forbidden, approvals are fixtures only."""
import copy
import json
import socket
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

import test_helper_comparison_execution as old
import test_helper_comparison_v3 as v3
import prepare_helper_comparison as prep
import run_helper_comparison as run


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Network forbidden'))


def packet(root, stage='stage_a'):
    path = root/'packet'
    prep.prepare(path, stage, protocol_version='v4')
    return path


def test_amendment_changes_only_version_and_qwen_provider():
    original = prep.load_protocol('v3')
    amended = prep.load_protocol('v4')
    assert amended['schema'] == 'broadbridge.helper_comparison_protocol/4'
    assert amended['version'] == 'public-v4-siliconflow-amendment-2026-09-28'
    assert amended['models']['qwen']['requested_provider'] == 'SiliconFlow'
    assert amended['models']['qwen']['provider_route'] == 'siliconflow/fp8'
    normalized = copy.deepcopy(amended)
    for key in ('schema', 'version'):
        normalized[key] = original[key]
    for key in ('requested_provider', 'provider_route'):
        normalized['models']['qwen'][key] = original['models']['qwen'][key]
    assert normalized == original
    # Historical evidence cannot be rewritten to make an old approval fit.
    assert prep.sha(prep.protocol_path('v3').read_bytes()) == '4c27be1251ce58198d6bd5419d282bf79b622e0d7690120a572b45258538d1ed'


def test_wire_pins_siliconflow_but_preserves_questions_prompts_and_caps(tmp_path):
    p = packet(tmp_path)
    proposal = run.plan(p, tmp_path/'plan', old.foundry())
    wires = [json.loads(x) for x in (tmp_path/'plan/wire_requests.jsonl').read_text(encoding='utf-8').splitlines()]
    previous = prep.build_requests(prep.load_protocol('v3'), run.load(prep.SAMPLE), 'stage_a')
    for wire, prior in zip(wires, previous):
        qwen = wire['model'] == 'qwen/qwen3-30b-a3b-instruct-2507'
        assert wire['messages'] == prior['messages']
        assert wire['provider']['only'] == ['siliconflow/fp8' if qwen else 'deepinfra/fp8']
        assert wire['provider']['allow_fallbacks'] is False
        assert wire['provider']['require_parameters'] is True
        assert wire['provider']['data_collection'] == 'deny'
        assert wire['provider']['zdr'] is True
        assert wire['provider']['enforce_distillable_text'] is True
        assert wire['max_tokens'] == 1000 and wire['temperature'] == 0
        assert wire['transforms'] == [] and 'reasoning' not in wire
        assert wire['plugins'] == [{'id': 'context-compression', 'enabled': False}]
    assert proposal['schema'] == 'broadbridge.helper_execution_approval/4'
    assert proposal['providers']['qwen']['requested_provider'] == 'SiliconFlow'
    assert proposal['providers']['qwen']['controls_verified'] is False
    assert proposal['rights_and_cloud_route_accepted'] is False
    assert proposal['approved_by'] is None
    assert proposal['stage_ceiling_usd'] == '0.10' and proposal['total_ceiling_usd'] == '0.25'
    assert prep.reservations(prep.load_protocol('v4')) == {'mistral': Decimal('.00206608'), 'qwen': Decimal('.03181728')}


@pytest.mark.parametrize('stage,calls', [('stage_a', 20), ('stage_b', 40)])
def test_both_stages_rehearse_without_implying_review_or_live_approval(tmp_path, stage, calls):
    p = packet(tmp_path, stage)
    result = run.execute(p, tmp_path/'run', old.foundry())
    assert result['calls_attempted'] == calls and result['status'] == 'completed'
    assert result['live_calls'] == 0 and result['training_approved'] is False
    report = run.summarize(tmp_path/'run', tmp_path/'run/scores.csv')
    assert report['planned_slots'] == calls and report['proposed_screen_passed'] is False


@pytest.mark.parametrize('mutation', ['none', 'v3-approval', 'nebius-route', 'degraded', 'stale'])
def test_new_approval_binds_exact_provider_and_fresh_healthy_evidence(tmp_path, mutation):
    p = packet(tmp_path); path, approved = v3.approval(p, tmp_path)
    ep = path.parent/'qwen-endpoint.json'; snapshot = run.load(ep)
    if mutation == 'v3-approval': approved['schema'] = 'broadbridge.helper_execution_approval/3'
    if mutation == 'nebius-route': approved['providers']['qwen']['provider_route'] = 'nebius/fp8'
    if mutation == 'degraded': snapshot['endpoint']['status'] = -2
    if mutation == 'stale': snapshot['retrieved_at'] = (datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
    run.stamp(ep, snapshot); digest = prep.sha(ep.read_bytes())
    approved['evidence_files'][ep.name] = digest
    approved['providers']['qwen']['endpoint_snapshot_sha256'] = digest
    if mutation == 'none': assert v3.validate(p, path, approved) == approved
    else:
        with pytest.raises(ValueError): v3.validate(p, path, approved)


def test_nebius_stage_a_cannot_qualify_siliconflow_stage_b(tmp_path):
    root = tmp_path/'old-a'; root.mkdir()
    run.stamp(root/'run.json', {'mode': 'live', 'stage': 'stage_a',
              'protocol_sha256': prep.sha(prep.protocol_path('v3').read_bytes())})
    (root/'scores.csv').write_text('SYNTHETIC prior-stage rejection fixture', encoding='utf-8')
    prior = {'run_dir': str(root), 'scores_file': str(root/'scores.csv'),
             'run_sha256': prep.sha((root/'run.json').read_bytes()),
             'scores_sha256': prep.sha((root/'scores.csv').read_bytes())}
    with pytest.raises(ValueError, match='not a complete reviewed live A'):
        run.prior_stage({'prior_stage_a': prior}, prep.load_protocol('v4'))


def test_nebius_returned_identity_stops_siliconflow_run(tmp_path, monkeypatch):
    p = packet(tmp_path); original = run.mock_http
    def factory(failure):
        respond = original(failure)
        def post(*args, **kwargs):
            reply = respond(*args, **kwargs)
            if kwargs['json']['provider']['only'] == ['siliconflow/fp8']:
                data = reply.json(); data['provider'] = 'Nebius'
                reply._content = json.dumps(data).encode()
            return reply
        return post
    monkeypatch.setattr(run, 'mock_http', factory)
    result = run.execute(p, tmp_path/'run', old.foundry())
    assert result['status'] != 'completed' and result['calls_attempted'] == 2
    assert result['slots'][1]['status'] != 'valid'
    assert all(s['status'] == 'not_run' for s in result['slots'][2:])
