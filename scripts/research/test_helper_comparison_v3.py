"""Context reservations: real runner/files/client, fabricated HTTP only."""
import copy
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import socket

import pytest
import requests

import test_helper_comparison_execution as old
import prepare_helper_comparison as prep
import run_helper_comparison as run


def packet(root, stage='stage_a'):
    path = root/'packet'
    prep.prepare(path, stage, protocol_version='v3')
    return path


def test_v3_compiles_without_inventing_request_token_counts(tmp_path):
    p = packet(tmp_path)
    summary = run.load(p/'preparation.json')
    assert summary['request_count'] == 20
    assert summary['pair_reservation_usd'] == '0.03388336'
    assert summary['all_calls_fit_at_full_reservation'] is False
    assert summary['token_count_verified'] is False
    assert 'exact_input_token_preflight' not in summary['live_blockers']
    assert run.load(p/'protocol.json')['schema'].endswith('/3')
    assert (p/'sample.json').read_bytes() == prep.SAMPLE.read_bytes()
    assert (p/'prompt.md').read_bytes() == prep.PROMPT.read_bytes()


def test_v3_wire_pins_routes_prices_and_disables_truncation(tmp_path):
    p = packet(tmp_path)
    proposal = run.plan(p, tmp_path/'plan', old.foundry())
    wires = [json.loads(x) for x in (tmp_path/'plan/wire_requests.jsonl').read_text(encoding='utf-8').splitlines()]
    for wire in wires:
        mistral = wire['model'].startswith('mistralai/')
        assert wire['provider']['only'] == ['deepinfra/fp8' if mistral else 'nebius/fp8']
        assert wire['provider']['max_price'] == ({'prompt': .06, 'completion': .10} if mistral else {'prompt': .12, 'completion': .36})
        assert wire['transforms'] == [] and 'reasoning' not in wire
        assert wire['plugins'] == [{'id': 'context-compression', 'enabled': False}]
    assert proposal['schema'].endswith('/3')
    assert proposal['providers']['qwen']['context_and_billing_verified'] is False
    assert proposal['requests'][0]['reservation_usd'] == '0.00206608'
    assert 'input_tokens_upper_bound' not in proposal['requests'][0]


def mock_run(tmp_path, monkeypatch, fault=None, prices=None):
    p = packet(tmp_path); output = tmp_path/'run'
    original = run.mock_http
    def factory(failure):
        respond = original(failure)
        def post(*args, **kwargs):
            # A wrong equal-per-arm reservation would break this durable checkpoint.
            saved = run.load(output/'run.json')
            if saved['calls_attempted'] == 1:
                assert Decimal(saved['held_reservations_usd']) == Decimal('.03388336')
                assert [Decimal(s['reservation_usd']) for s in saved['slots'][:2]] == [Decimal('.00206608'), Decimal('.03181728')]
            reply = respond(*args, **kwargs)
            if prices:
                data = reply.json(); arm = 'mistral' if data['model'].startswith('mistralai/') else 'qwen'
                data['usage']['cost'] = prices[arm]; reply._content = json.dumps(data).encode()
            return reply
        return post
    monkeypatch.setattr(run, 'mock_http', factory)
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: pytest.fail('Network forbidden'))
    return run.execute(p, output, old.foundry(), mock_failure=fault)


def test_reconciled_small_charges_allow_all_twenty_calls(tmp_path, monkeypatch):
    result = mock_run(tmp_path, monkeypatch)
    assert result['status'] == 'completed' and result['calls_attempted'] == 20
    assert result['known_cost_usd'] == '0.0020'
    assert Decimal(result['held_reservations_usd']) == 0
    assert result['live_calls'] == 0 and result['training_approved'] is False


def test_budget_stops_before_a_pair_and_keeps_missing_pairs_visible(tmp_path, monkeypatch):
    result = mock_run(tmp_path, monkeypatch, prices={'mistral': .002, 'qwen': .03})
    assert result['calls_attempted'] == 6
    assert result['stop_reason'] == 'pair_budget_exhausted'
    assert Decimal(result['known_cost_usd']) == Decimal('.096')
    assert [s['status'] for s in result['slots']] == ['valid']*6 + ['not_run']*14
    report = run.summarize(tmp_path/'run', tmp_path/'run/scores.csv')
    assert report['proposed_screen_passed'] is False and report['planned_slots'] == 20


@pytest.mark.parametrize('index,want', [(0, '.00206608'), (1, '.03181728')])
@pytest.mark.parametrize('kind', ['timeout', 'unknown_cost'])
def test_unknown_cost_retains_only_the_attempted_arm_reservation(tmp_path, monkeypatch, index, want, kind):
    result = mock_run(tmp_path, monkeypatch, {'index': index, 'kind': kind})
    assert result['calls_attempted'] == index+1 and result['billing_complete'] is False
    assert Decimal(result['held_reservations_usd']) == Decimal(want)
    assert result['slots'][index+1]['status'] == 'not_run'


def test_known_overcharge_is_recorded_and_stops_before_second_member(tmp_path, monkeypatch):
    result = mock_run(tmp_path, monkeypatch, prices={'mistral': .003, 'qwen': .0001})
    assert result['calls_attempted'] == 1
    assert result['stop_reason'] == 'reservation_exceeded'
    assert Decimal(result['known_cost_usd']) == Decimal('.003')
    assert Decimal(result['held_reservations_usd']) == 0


def approval(p, root):
    """Synthetic catalogue and attestations; never use these files with real HTTP."""
    directory = root/'approval'
    approved = run.plan(p, directory, old.foundry())
    now = datetime.now(timezone.utc)
    approved.update(approved_by='SYNTHETIC OPERATOR', technical_reviewer='SYNTHETIC REVIEWER',
                    run_id='TEST-ONLY', approved_at=now.isoformat(), expires_at=(now+timedelta(minutes=30)).isoformat())
    for key in ('rights_and_cloud_route_accepted','protocol_and_references_accepted','quality_screen_accepted','account_spend_limit_verified'):
        approved[key] = True
    run.stamp(directory/'billing-rights.json', {'fixture': 'SYNTHETIC, not real authorization'})
    digest = prep.sha((directory/'billing-rights.json').read_bytes())
    approved['evidence_files'] = {'billing-rights.json': digest}; approved['cloud_approval_sha256'] = digest
    for arm, provider in approved['providers'].items():
        raw = run.load(prep.ROOT/f'docs/verification/helper-preflight-20260928/{arm}-endpoints.json')
        endpoint = copy.deepcopy(next(e for e in raw['data']['endpoints'] if e['provider_name']==provider['requested_provider']))
        endpoint['status'] = 0  # deliberately fabricated healthy fixture
        snapshot = {'schema':'broadbridge.helper_endpoint_snapshot/1','retrieved_at':now.isoformat(),'endpoint':endpoint}
        name = arm+'-endpoint.json'; run.stamp(directory/name, snapshot)
        digest = prep.sha((directory/name).read_bytes()); approved['evidence_files'][name] = digest
        provider.update(endpoint_snapshot_sha256=digest, controls_verified=True,
                        context_and_billing_verified=True, billing_evidence_sha256=approved['cloud_approval_sha256'])
    path = directory/'approval.json'; run.stamp(path, approved)
    return path, approved


def validate(p, path, approved):
    config, _, stage, _, packet_hash = run.read_packet(p)
    context = {'config':config,'stage':stage,'packet_sha256':packet_hash,
               'domain_commit':approved['domain_commit'],'foundry_commit':approved['foundry_commit']}
    wires = [json.loads(x) for x in (path.parent/'wire_requests.jsonl').read_text(encoding='utf-8').splitlines()]
    run.stamp(path, approved)
    return run.validate_approval(path, prep.sha(path.read_bytes()), context, wires)


@pytest.mark.parametrize('mutation', ['none','context','price','negative-price','status','tag','model','provider','parameters','expired','future','fee','attestation','wire','reservation','v2-schema'])
def test_v3_approval_checks_endpoint_evidence_and_each_reservation(tmp_path, mutation):
    p = packet(tmp_path); path, approved = approval(p, tmp_path)
    ep = path.parent/'qwen-endpoint.json'; snap = run.load(ep); e = snap['endpoint']
    if mutation=='context': e['context_length'] += 1
    if mutation=='price': e['pricing']['prompt'] = '.001'
    if mutation=='negative-price': e['pricing']['prompt'] = '-.001'
    if mutation=='status': e['status'] = -2
    if mutation=='tag': e['tag'] = 'nebius/fp16'
    if mutation=='model': e['model_id'] = 'other/model'
    if mutation=='provider': e['provider_name'] = 'Other'
    if mutation=='parameters': e['supported_parameters'].remove('structured_outputs')
    if mutation=='expired': snap['retrieved_at'] = (datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
    if mutation=='future': snap['retrieved_at'] = (datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
    if mutation=='fee': e['pricing']['request'] = '.01'
    if mutation=='attestation': approved['providers']['qwen']['context_and_billing_verified'] = False
    if mutation=='wire': approved['requests'][0]['request_sha256'] = '0'*64
    if mutation=='reservation': approved['requests'][0]['reservation_usd'] = '.00001'
    if mutation=='v2-schema': approved['schema'] = 'broadbridge.helper_execution_approval/2'
    run.stamp(ep, snap); digest = prep.sha(ep.read_bytes())
    approved['evidence_files'][ep.name] = digest; approved['providers']['qwen']['endpoint_snapshot_sha256'] = digest
    if mutation=='none': assert validate(p,path,approved)==approved
    else:
        with pytest.raises(ValueError): validate(p,path,approved)


def test_v3_live_path_with_fake_http_reuses_scoring_and_stage_dependency(tmp_path, monkeypatch):
    p = packet(tmp_path/'a'); path, approved = approval(p,tmp_path/'a')
    monkeypatch.setattr(run,'git_state',lambda root:{'commit':approved['domain_commit' if Path(root).resolve()==prep.ROOT.resolve() else 'foundry_commit'],'dirty':False})
    monkeypatch.setenv('OPENROUTER_API_KEY','fake-test-key')
    monkeypatch.setattr(requests,'post',run.mock_http())
    monkeypatch.setattr(socket.socket,'connect',lambda *a,**k:pytest.fail('Network forbidden'))
    a = tmp_path/'a/run'; run.execute(p,a,old.foundry(),mode='live',approval=path,approve_hash=prep.sha(path.read_bytes()))
    scores = tmp_path/'a/review.csv'; old.fill_scores(a,scores)
    bp = packet(tmp_path/'b','stage_b'); bpath, ba = approval(bp,tmp_path/'b')
    ba['prior_stage_a'] = {'run_dir':str(a),'scores_file':str(scores),'run_sha256':prep.sha((a/'run.json').read_bytes()),'scores_sha256':prep.sha(scores.read_bytes())}
    run.stamp(bpath,ba)
    b = tmp_path/'b/run'; result=run.execute(bp,b,old.foundry(),mode='live',approval=bpath,approve_hash=prep.sha(bpath.read_bytes()))
    assert result['calls_attempted']==40 and Decimal(result['prior_stage_cost_usd'])==Decimal('.002')
    bs = tmp_path/'b/review.csv'; old.fill_scores(b,bs)
    summary=run.summarize(b,bs)
    assert summary['planned_slots']==60 and summary['matched_pairs']==30
    assert Decimal(summary['known_cost_usd'])==Decimal('.006')
