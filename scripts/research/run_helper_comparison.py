"""FQ-07 paired OpenRouter execution and review. Default mode is offline mock.

Live runs require a hash-bound, short-lived approval and preflight evidence. This
module never loads .env, retries a slot, changes the v1 sample, or approves training.
"""
import argparse
from collections import Counter
from contextlib import ExitStack
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
from unittest.mock import patch

import requests

import prepare_helper_comparison as prep

v1 = prep.v1
HASH = re.compile(r'[a-f0-9]{64}')
IDENTITY = ['source_id', 'family_id', 'question_id', 'type', 'response_label',
            'response_status', 'response_sha256', 'run_sha256']
REVIEW = ['score', 'critical_error', 'hard_fail_matched', 'reference_dispute',
          'review_seconds', 'reviewer', 'review_date', 'notes']
REVISIONS = ['weights_revision', 'provider_revision', 'tokenizer_revision',
             'template_revision', 'quantization_revision']


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def money(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError('Invalid nonnegative amount')
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid nonnegative amount') from None
    if not result.is_finite() or result < 0:
        raise ValueError('Invalid nonnegative amount')
    return result


def text_required(value):
    return isinstance(value, str) and bool(value.strip())


def utc():
    return datetime.now(timezone.utc).isoformat()


def stamp(path, value):
    """Atomic, flushed checkpoint before and after every attempted call."""
    path = Path(path); temporary = path.with_suffix('.pending')
    with temporary.open('wb') as handle:
        handle.write(v1.canonical(value) + b'\n'); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def git_state(root):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    return {'commit': git('rev-parse', 'HEAD'), 'dirty': bool(git('status', '--porcelain'))}


def foundry_module(root):
    path = Path(root).resolve()/'src/openrouter_client.py'
    spec = importlib.util.spec_from_file_location('fq07_foundry_transport', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if not hasattr(module.OpenRouterClient, 'request_payload'):
        raise ValueError('Foundry helper receipt/payload revision required')
    return module


def verify_files(root, checks):
    for name, expected in checks.items():
        if Path(name).name != name or not HASH.fullmatch(str(expected)):
            raise ValueError('Invalid file hash manifest')
        if prep.sha((root/name).read_bytes()) != expected:
            raise ValueError('Artifact hash mismatch: '+name)


def read_packet(packet):
    packet = Path(packet)
    checks = load(packet/'checksums.json')
    expected = {'preparation.json', 'protocol.json', 'sample.json', 'prompt.md',
                'requests.jsonl', 'reviewer-only.json', 'scores.csv', 'README.md'}
    if set(checks) != expected:
        raise ValueError('Unexpected preparation files')
    verify_files(packet, checks)
    config = load(packet/'protocol.json'); sample = load(packet/'sample.json')
    # A changed protocol requires a new reviewed code/protocol version, not a rehashed packet.
    if config != prep.load_protocol(prep.protocol_version(config)) or (packet/'prompt.md').read_bytes() != prep.PROMPT.read_bytes():
        raise ValueError('Packet differs from this protocol/prompt revision')
    prep.validate_inputs(config, sample, (packet/'sample.json').read_bytes())
    stage = load(packet/'preparation.json')['stage']
    rows = [json.loads(line) for line in (packet/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    if rows != prep.build_requests(config, sample, stage):
        raise ValueError('Packet does not match recompiled requests')
    return config, sample, stage, rows, prep.sha((packet/'checksums.json').read_bytes())


def options(config, model, reasoning):
    limits = config['limits']; arm = config['models'][model]
    context_policy = prep.protocol_version(config) in {'v3', 'v4'}
    prices = arm['reservation']['max_price_usd_per_million'] if context_policy else limits['max_price_usd_per_million']
    result = {'model': arm['requested_model'], 'providers': [arm['requested_provider']],
            'max_tokens': limits['max_output_tokens'], 'max_input_bytes': limits['max_request_bytes'],
            'timeout': limits['timeout_seconds'], 'max_calls': 30,
            'max_price': {k: float(v) for k, v in prices.items()},
            'cost_stop_usd': float(config['limits']['proposed_total_ceiling_usd']),
            'reasoning': reasoning}
    if context_policy:
        if reasoning != 'native_nonreasoning':
            raise ValueError('Context-reservation protocols require native nonreasoning endpoints')
        result.update(provider_routes=[arm['provider_route']], disable_transforms=True)
    return result


def bound(config):
    amounts = set(prep.reservations(config).values())
    if len(amounts) != 1:
        raise ValueError('Use per-arm reservations for this protocol')
    return amounts.pop()


def plan(packet, output, foundry, *, reasoning=None):
    """Emit wire payloads and an intentionally INCOMPLETE approval worksheet offline."""
    config, sample, stage, rows, packet_hash = read_packet(packet)
    transport = foundry_module(foundry)
    version = prep.protocol_version(config)
    reasoning = reasoning or dict.fromkeys(config['models'], 'native_nonreasoning' if version in {'v3', 'v4'} else 'disabled')
    clients = {key: transport.OpenRouterClient(options(config, key, reasoning[key])) for key in config['models']}
    payloads = [clients[r['model_key']].request_payload(r['messages'], r['response_schema'], task='draft') for r in rows]
    proposal = {'schema': 'broadbridge.helper_execution_approval/'+version[1:], 'stage': stage, 'packet_sha256': packet_hash,
                'domain_commit': git_state(prep.ROOT)['commit'], 'foundry_commit': git_state(foundry)['commit'],
                'run_id': None, 'approved_by': None, 'technical_reviewer': None, 'approved_at': None, 'expires_at': None,
                'rights_and_cloud_route_accepted': False, 'protocol_and_references_accepted': False,
                'quality_screen_accepted': False, 'account_spend_limit_verified': False,
                'stage_ceiling_usd': config['stages'][stage]['proposed_ceiling_usd'],
                'total_ceiling_usd': config['limits']['proposed_total_ceiling_usd'],
                'evidence_files': {}, 'cloud_approval_sha256': None, 'prior_stage_a': None,
                'providers': {key: {**{k: config['models'][key][k] for k in ('requested_model', 'requested_provider')},
                                   'reasoning_mode': reasoning[key], 'controls_verified': False,
                                   'endpoint_snapshot_sha256': None, **dict.fromkeys(REVISIONS),
                                   'unknown_revision_reason': 'provider_not_disclosed'} for key in config['models']},
                'requests': [{'request_sha256': v1.digest(p), 'input_tokens_upper_bound': None,
                              'includes_template_schema_overhead': False, 'method': None, 'evidence_sha256': None} for p in payloads]}
    if version in {'v3', 'v4'}:
        amounts = prep.reservations(config)
        for key, provider in proposal['providers'].items():
            provider.update(provider_route=config['models'][key]['provider_route'],
                            context_tokens=config['models'][key]['reservation']['context_tokens'],
                            context_and_billing_verified=False, billing_evidence_sha256=None)
        proposal['requests'] = [{'request_sha256': v1.digest(p), 'reservation_usd': str(amounts[r['model_key']])}
                                for r, p in zip(rows, payloads)]
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    stamp(output/'approval.template.json', proposal)
    (output/'wire_requests.jsonl').write_bytes(b''.join(v1.canonical(p)+b'\n' for p in payloads))
    return proposal


def validate_approval(approval_path, approve_hash, context, payloads, *, now=None):
    """Validate operator attestations, evidence bytes and exact requests; never infer consent."""
    approval_path = Path(approval_path)
    raw = approval_path.read_bytes()
    if not approve_hash or prep.sha(raw) != approve_hash:
        raise ValueError('Explicit approval SHA-256 mismatch')
    approved = json.loads(raw)
    config = context['config']; version = prep.protocol_version(config)
    if not isinstance(approved, dict) or approved.get('schema') != 'broadbridge.helper_execution_approval/'+version[1:]:
        raise ValueError('Unsupported approval schema')
    for key in ('packet_sha256', 'stage', 'domain_commit', 'foundry_commit'):
        if approved.get(key) != context[key]:
            raise ValueError('approval does not bind '+key)
    for key in ('approved_by', 'technical_reviewer', 'run_id'):
        if not text_required(approved.get(key)):
            raise ValueError('approval missing '+key)
    for key in ('rights_and_cloud_route_accepted', 'protocol_and_references_accepted',
                'quality_screen_accepted', 'account_spend_limit_verified'):
        if approved.get(key) is not True:
            raise ValueError('approval missing '+key)
    now = now or datetime.now(timezone.utc)
    start = datetime.fromisoformat(approved['approved_at']); end = datetime.fromisoformat(approved['expires_at'])
    if start.tzinfo is None or end.tzinfo is None or not start <= now < end or (end-start).total_seconds() > 86400:
        raise ValueError('approval is expired, future, or exceeds 24 hours')
    config = context['config']; stage = context['stage']
    stage_cap = money(approved['stage_ceiling_usd']); total_cap = money(approved['total_ceiling_usd'])
    if (not 0 < stage_cap <= money(config['stages'][stage]['proposed_ceiling_usd'])
            or not 0 < total_cap <= money(config['limits']['proposed_total_ceiling_usd'])):
        raise ValueError('approval exceeds proposed budget')
    evidence = approved['evidence_files']
    if not isinstance(evidence, dict) or not evidence:
        raise ValueError('approval requires local preflight evidence files')
    verify_files(approval_path.parent, evidence)
    if approved.get('cloud_approval_sha256') not in evidence.values():
        raise ValueError('Rights/cloud route evidence is not pinned')
    providers = approved['providers']
    if set(providers) != set(config['models']):
        raise ValueError('Both provider preflights required')
    for model, provider in providers.items():
        for key in ('requested_model', 'requested_provider'):
            if provider.get(key) != config['models'][model][key]:
                raise ValueError('Provider preflight identity mismatch')
        if (provider.get('endpoint_snapshot_sha256') not in evidence.values()
                or provider.get('controls_verified') is not True
                or provider.get('reasoning_mode') not in {'disabled', 'native_nonreasoning'}):
            raise ValueError('Unverified provider controls or reasoning equivalence')
        for key in REVISIONS:
            if key not in provider or (provider[key] is not None and not text_required(provider[key])):
                raise ValueError('Explicit revision or null required: '+key)
        if any(provider[k] is None for k in REVISIONS) and provider.get('unknown_revision_reason') != 'provider_not_disclosed':
            raise ValueError('Unknown backend revisions must remain explicit')
        if version in {'v3', 'v4'}:
            validate_endpoint(provider, config['models'][model], evidence, approval_path.parent, now)
    tokens = approved['requests']
    if not isinstance(tokens, list) or len(tokens) != len(payloads):
        raise ValueError('Every exact wire request needs token preflight')
    for row, payload in zip(tokens, payloads):
        if version in {'v3', 'v4'}:
            model = next(k for k, a in config['models'].items() if a['requested_model'] == payload['model'])
            if (row.get('request_sha256') != v1.digest(payload)
                    or money(row.get('reservation_usd')) != prep.reservations(config)[model]):
                raise ValueError('Missing or invalid exact request reservation')
            continue
        if (row.get('request_sha256') != v1.digest(payload)
                or type(row.get('input_tokens_upper_bound')) is not int
                or not 0 < row['input_tokens_upper_bound'] <= config['limits']['max_input_tokens_for_budget']
                or row.get('includes_template_schema_overhead') is not True
                or row.get('method') not in {'provider_count', 'pinned_tokenizer_with_template'}
                or row.get('evidence_sha256') not in evidence.values()):
            raise ValueError('Missing or invalid exact request token preflight')
    return approved


def validate_endpoint(provider, arm, evidence, root, now):
    """Check fresh catalogue evidence; attestations still cover hosted enforcement/fees."""
    policy = arm['reservation']
    if (provider.get('provider_route') != arm['provider_route']
            or type(provider.get('context_tokens')) is not int
            or provider['context_tokens'] != policy['context_tokens']
            or provider.get('reasoning_mode') != 'native_nonreasoning'
            or provider.get('context_and_billing_verified') is not True
            or provider.get('billing_evidence_sha256') not in evidence.values()):
        raise ValueError('Unverified endpoint context/billing policy')
    name = next(n for n, digest in evidence.items() if digest == provider['endpoint_snapshot_sha256'])
    snapshot = load(root/name)
    try:
        if snapshot['schema'] != 'broadbridge.helper_endpoint_snapshot/1':
            raise ValueError('Unsupported endpoint snapshot')
        captured = datetime.fromisoformat(snapshot['retrieved_at'])
        if captured.tzinfo is None or not 0 <= (now-captured).total_seconds() <= 86400:
            raise ValueError('Endpoint snapshot stale or future dated')
        endpoint = snapshot['endpoint']
        if (endpoint['model_id'] != arm['requested_model']
                or endpoint['provider_name'] != arm['requested_provider']
                or endpoint['tag'] != arm['provider_route']
                or type(endpoint['context_length']) is not int
                or endpoint['context_length'] != policy['context_tokens']
                or type(endpoint['status']) is not int or endpoint['status'] != 0):
            raise ValueError('Endpoint identity, context or status changed')
        if not {'max_tokens', 'temperature', 'response_format', 'structured_outputs'} <= set(endpoint['supported_parameters']):
            raise ValueError('Endpoint lacks required parameters')
        for key, ceiling in policy['max_price_usd_per_million'].items():
            if money(endpoint['pricing'][key])*1000000 > money(ceiling):
                raise ValueError('Endpoint price exceeds reservation ceiling')
        if money(endpoint['pricing'].get('request', '0')) > money(policy['max_non_token_fee_usd']):
            raise ValueError('Endpoint request fee exceeds reservation')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('Malformed endpoint snapshot') from exc


def prior_stage(approved, config):
    """Recompute A's report from pinned run and scores; never trust a hand-edited summary."""
    prior = approved.get('prior_stage_a')
    if not prior:
        raise ValueError('Stage B requires reviewed stage A and separate approval')
    root = Path(prior['run_dir']); scores = Path(prior['scores_file'])
    if (prep.sha((root/'run.json').read_bytes()) != prior['run_sha256']
            or prep.sha(scores.read_bytes()) != prior['scores_sha256']):
        raise ValueError('Prior stage hash mismatch')
    run = load(root/'run.json')
    if (run['mode'] != 'live' or run['stage'] != 'stage_a'
            or run['protocol_sha256'] != prep.sha(prep.protocol_path(prep.protocol_version(config)).read_bytes())):
        raise ValueError('Prior stage is not a complete reviewed live A')
    report = summarize(root, scores)
    if not report['proposed_screen_passed'] or not run['billing_complete']:
        raise ValueError('Prior stage is not a complete reviewed live A')
    return money(run['known_cost_usd'])


def mock_http(failure=None):
    """Fabricated responses only. Exercises real Foundry serialization/validation at HTTP boundary."""
    attempted = 0
    def post(url, **kwargs):
        nonlocal attempted
        index = attempted; attempted += 1
        payload = kwargs['json']; content = json.loads(payload['messages'][1]['content'])
        question = content['questions'][0]; block = content['blocks'][0]
        answer = {'question_id': question['question_id'], 'answer': 'MOCK ONLY: not an engineering answer.',
                  'evidence': [{'source_id': content['source_id'], 'block_id': block['block_id'],
                                'quote': block['text'][:60]}], 'uncertainties': ['Fabricated software rehearsal.']}
        route = payload['provider']['only'][0]
        # These labels represent fabricated responses, not observed provider routing.
        provider = {'deepinfra/fp8': 'DeepInfra', 'nebius/fp8': 'Nebius', 'siliconflow/fp8': 'SiliconFlow'}.get(route, route)
        data = {'model': payload['model'], 'provider': provider,
                'usage': {'cost': 0.0001, 'prompt_tokens': 500, 'completion_tokens': 50,
                          'completion_tokens_details': {'reasoning_tokens': 0}},
                'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(answer)}}]}
        if failure and failure['index'] == index:
            kind = failure['kind']
            if kind == 'timeout': raise requests.Timeout('mock transport timeout')
            if kind == 'unknown_cost': del data['usage']['cost']
            if kind == 'identity': data['model'] = 'mock/unapproved'
            if kind == 'length': data['choices'][0]['finish_reason'] = 'length'
            if kind == 'over_budget': data['usage']['cost'] = 0.2
            if kind == 'citation': answer['evidence'][0]['quote'] = 'MOCK FABRICATED QUOTE'
            if kind == 'schema': answer['invented'] = True
            data['choices'][0]['message']['content'] = json.dumps(answer)
        response = requests.Response(); response.status_code = 200
        response._content = json.dumps(data).encode(); response._content_consumed = True
        return response
    return post


def execute(packet, output, foundry, *, mode='mock', approval=None, approve_hash=None, mock_failure=None):
    if mode not in {'mock', 'live'}: raise ValueError('Unknown mode')
    if mode == 'live' and (approval is None or approve_hash is None):
        raise ValueError('Live execution requires exact-run approval and SHA-256')
    if mode == 'live' and mock_failure is not None: raise ValueError('Mock fault is not a live option')
    config, sample, stage, requests_, packet_hash = read_packet(packet)
    version = prep.protocol_version(config)
    transport = foundry_module(foundry)
    domain_state = git_state(prep.ROOT); engine_state = git_state(foundry)
    if mode == 'live' and (domain_state['dirty'] or engine_state['dirty']):
        raise ValueError('Live execution requires clean, committed repositories')
    preliminary = load(approval) if mode == 'live' else None
    if mode == 'live' and (not isinstance(preliminary, dict) or not preliminary):
        raise ValueError('Live approval must be a nonempty approval object')
    clients = {key: transport.OpenRouterClient(options(config, key,
        preliminary['providers'][key]['reasoning_mode'] if mode == 'live' else
        ('native_nonreasoning' if version in {'v3', 'v4'} else 'disabled'))) for key in config['models']}
    payloads = [clients[r['model_key']].request_payload(r['messages'], r['response_schema'], task='draft') for r in requests_]
    context = {'config': config, 'packet_sha256': packet_hash, 'stage': stage,
               'domain_commit': domain_state['commit'], 'foundry_commit': engine_state['commit']}
    accepted = validate_approval(approval, approve_hash, context, payloads) if mode == 'live' else None
    earlier = prior_stage(accepted, config) if accepted and stage == 'stage_b' else Decimal(0)
    stage_cap = money(accepted['stage_ceiling_usd'] if accepted else config['stages'][stage]['proposed_ceiling_usd'])
    total_cap = money(accepted['total_ceiling_usd'] if accepted else config['limits']['proposed_total_ceiling_usd'])
    amounts = prep.reservations(config)
    pair_reservation = sum(amounts.values())
    if pair_reservation > stage_cap or earlier+pair_reservation > total_cap:
        raise ValueError('Budget cannot reserve both calls of the first pair')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    if accepted:
        # Local one-use interlock; retain it even after a crash. No automatic recovery/retry.
        with Path(str(approval)+'.used').open('x', encoding='utf-8') as handle:
            json.dump({'approval_sha256': approve_hash, 'output': str(output.resolve()), 'at': utc()}, handle)
    slots = [{**{k: r[k] for k in ('source_id', 'family_id', 'question_id', 'type', 'response_label', 'model_key')},
              'requested_model': r['requested_model'], 'requested_provider': r['requested_provider'],
              'request_sha256': v1.digest(p), 'prompt_sha256': r['prompt_sha256'], 'schema_sha256': r['schema_sha256'],
              'status': 'not_run', 'response': None, 'response_sha256': '', 'receipt': None,
              'error': None, 'reservation_usd': '0'} for r, p in zip(requests_, payloads)]
    result = {'schema': 'broadbridge.helper_comparison_run/'+version[1:], 'mode': mode, 'stage': stage,
              'evaluation_role': 'development_calibration', 'status': 'running', 'started_at': utc(),
              'ended_at': None, 'packet_sha256': packet_hash, 'sample_sha256': prep.sha(prep.SAMPLE.read_bytes()),
              'protocol_sha256': prep.sha(Path(packet, 'protocol.json').read_bytes()), 'prompt_sha256': prep.sha(prep.PROMPT.read_bytes()),
              'domain': domain_state, 'foundry': engine_state, 'approval_sha256': approve_hash if accepted else None,
              'approval': accepted, 'training_approved': False, 'calls_attempted': 0, 'live_calls': 0,
              'known_cost_usd': '0', 'held_reservations_usd': '0', 'billing_complete': True,
              'prior_stage_cost_usd': str(earlier), 'stage_ceiling_usd': str(stage_cap),
              'total_ceiling_usd': str(total_cap), 'slots': slots}
    (output/'sample.json').write_bytes(Path(packet, 'sample.json').read_bytes())
    (output/'protocol.json').write_bytes(Path(packet, 'protocol.json').read_bytes())
    (output/'requests.jsonl').write_bytes(Path(packet, 'requests.jsonl').read_bytes())
    (output/'prompt.md').write_bytes(Path(packet, 'prompt.md').read_bytes())
    billed = Decimal(0); held = Decimal(0)
    def checkpoint():
        result.update(known_cost_usd=str(billed), held_reservations_usd=str(held))
        stamp(output/'run.json', result)
    checkpoint()
    questions = {q['question_id']: q for q in sample['questions']}
    with ExitStack() as stack:
        if mode == 'mock':
            stack.enter_context(patch.dict(os.environ, {'OPENROUTER_API_KEY': 'mock-never-transmitted'}))
            stack.enter_context(patch.object(transport.requests, 'post', mock_http(mock_failure)))
        for pair in range(0, len(slots), 2):
            if billed+held+pair_reservation > stage_cap or earlier+billed+held+pair_reservation > total_cap:
                result['status'] = 'stopped'; result['stop_reason'] = 'pair_budget_exhausted'; break
            held += pair_reservation
            for slot in slots[pair:pair+2]: slot['reservation_usd'] = str(amounts[slot['model_key']])
            checkpoint()
            for index in (pair, pair+1):
                slot = slots[index]; request = requests_[index]
                reservation = amounts[slot['model_key']]
                slot['status'] = 'attempting'; result['calls_attempted'] += 1
                if mode == 'live': result['live_calls'] += 1
                checkpoint()
                try:
                    answer, receipt = clients[slot['model_key']].complete(request['messages'], request['response_schema'], task='draft')
                    slot.update(receipt=receipt, response=answer, response_sha256=v1.digest(answer))
                    errors = prep.check_answer(sample, questions[slot['question_id']], answer)
                    token_bound = (config['models'][slot['model_key']]['reservation']['context_tokens']
                                   if version in {'v3', 'v4'} else config['limits']['max_input_tokens_for_budget'])
                    if receipt['prompt_tokens'] > token_bound:
                        errors.append('input_token_cap_exceeded')
                    if receipt['completion_tokens'] > config['limits']['max_output_tokens']:
                        errors.append('output_token_cap_exceeded')
                    if accepted and version == 'v2' and receipt['prompt_tokens'] > accepted['requests'][index]['input_tokens_upper_bound']:
                        errors.append('token_preflight_bound_exceeded')
                    slot['status'] = 'failed' if errors else 'valid'
                    slot['error'] = ','.join(errors) if errors else None
                except transport.OpenRouterError as exc:
                    slot.update(status='failed', error=str(exc), receipt=exc.receipt)
                receipt = slot['receipt'] or {}
                if receipt.get('cost_usd') is None:
                    result['billing_complete'] = False; slot['status'] = 'failed'
                    slot['error'] = slot['error'] or 'unknown_billing'
                else:
                    cost = money(receipt['cost_usd']); billed += cost; held -= reservation
                    slot['reservation_usd'] = '0'
                    if cost > reservation:
                        slot.update(status='failed', error='reservation_exceeded')
                if slot['status'] == 'failed':
                    result['status'] = 'stopped'; result['stop_reason'] = slot['error']
                    if index == pair:
                        held -= amounts[slots[pair+1]['model_key']]; slots[pair+1]['reservation_usd'] = '0'
                    checkpoint(); break
                checkpoint()
            if result['status'] == 'stopped': break
    if result['status'] == 'running': result['status'] = 'completed'
    result['ended_at'] = utc(); checkpoint()
    write_review(output, result, sample)
    immutable = ['run.json', 'sample.json', 'protocol.json', 'prompt.md', 'requests.jsonl', 'review.md']
    stamp(output/'checksums.json', {name: prep.sha((output/name).read_bytes()) for name in immutable})
    return result


def score_identity(slot, run_hash):
    return {**{k: slot[k] for k in IDENTITY if k in slot},
            'response_status': slot['status'], 'run_sha256': run_hash}


def write_review(output, result, sample):
    run_hash = prep.sha((output/'run.json').read_bytes())
    with (output/'scores.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=IDENTITY+REVIEW); writer.writeheader()
        for slot in result['slots']:
            writer.writerow({**dict.fromkeys(REVIEW, ''), **score_identity(slot, run_hash)})
    lines = ['# Helper comparison review', '',
             '**MOCK REHEARSAL: fabricated answers; never engineering evidence.**' if result['mode'] == 'mock' else 'Saved public evaluation answers for independent technical review.',
             '', 'Use scores.csv. 0 = incorrect; 1 = needs correction; 2 = correct and supported.',
             'A matched hard-fail criterion requires score 0 and critical_error YES. Missing answers stay ungraded.',
             'Operator run/requests files disclose identities. Keep them separate until initial scoring is saved.', '']
    sources = {s['source_id']: s for s in sample['sources']}
    for q in sample['questions']:
        selected = [s for s in result['slots'] if s['question_id'] == q['question_id']]
        if not selected: continue
        lines += ['## '+q['question_id']+' — '+q['type'], '', html.escape(q['question']), '',
                  'Rubric: '+html.escape(json.dumps(v1.RUBRICS[q['type']])), '',
                  'Reference (requires technical acceptance): '+html.escape(str(q['reference_answer'])), '',
                  'Hard-fail criteria: '+html.escape(str(q['hard_fail_criteria'])), '',
                  'Tolerance: '+html.escape(str(q.get('tolerance'))), '', 'Source evidence:']
        for block in sources[q['source_id']]['blocks']:
            lines += ['', html.escape(block['block_id']+': '+block['text'])]
        for slot in selected:
            lines += ['', '### Response '+slot['response_label']+' — '+slot['status'], '',
                      html.escape(json.dumps(slot['response'], ensure_ascii=False)) if slot['response'] else 'Unavailable; do not assign an engineering grade.']
    (output/'review.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def summarize(run, scores):
    run = Path(run); checks = load(run/'checksums.json')
    if set(checks) != {'run.json', 'sample.json', 'protocol.json', 'prompt.md', 'requests.jsonl', 'review.md'}:
        raise ValueError('Incomplete run hash manifest')
    verify_files(run, checks)
    result = load(run/'run.json'); config = load(run/'protocol.json')
    if result['status'] not in {'completed', 'stopped'}: raise ValueError('Run is incomplete')
    run_hash = prep.sha((run/'run.json').read_bytes())
    with Path(scores).open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != IDENTITY+REVIEW: raise ValueError('Invalid score columns')
        rows = list(reader)
    slots = result['slots']; lookup = {(s['question_id'], s['response_label']): s for s in slots}
    if len(rows) != len(slots): raise ValueError('Every planned slot must remain visible')
    graded = {}; seen = set(); disputes = critical = 0; seconds = Decimal(0)
    for row in rows:
        key = (row['question_id'], row['response_label'])
        if key not in lookup or key in seen: raise ValueError('Duplicate or unexpected review slot')
        seen.add(key); slot = lookup[key]
        if {k: row[k] for k in IDENTITY} != score_identity(slot, run_hash):
            raise ValueError('Stale review or changed identity/hash')
        if slot['status'] != 'valid' and any(row[k].strip() for k in REVIEW):
            raise ValueError('Cannot grade unavailable/failed responses')
        if not row['score'].strip():
            if any(row[k].strip() for k in REVIEW): raise ValueError('Incomplete review row; clear it or finish all fields')
            continue
        if (row['score'] not in {'0', '1', '2'}
                or any(row[k] not in {'YES', 'NO'} for k in ('critical_error', 'hard_fail_matched', 'reference_dispute'))
                or any(not text_required(row[k]) for k in ('reviewer', 'review_date', 'review_seconds', 'notes'))):
            raise ValueError('Invalid or incomplete review')
        if row['critical_error'] == 'YES' and row['score'] != '0': raise ValueError('Critical errors require score 0')
        if row['hard_fail_matched'] == 'YES' and (row['score'] != '0' or row['critical_error'] != 'YES'):
            raise ValueError('Matched hard fail requires 0 / critical YES')
        date.fromisoformat(row['review_date']); seconds += money(row['review_seconds'])
        critical += row['critical_error'] == 'YES'; disputes += row['reference_dispute'] == 'YES'
        graded[key] = row
    aggregation_scope = 'stage_only'
    total_known_cost = money(result['known_cost_usd'])
    prior_hashes = None
    if result['mode'] == 'live' and result['stage'] == 'stage_b':
        prior_cost = prior_stage(result['approval'], config)
        if prior_cost != money(result['prior_stage_cost_usd']):
            raise ValueError('Prior cost differs from the execution reservation')
        prior = result['approval']['prior_stage_a']; prior_result = load(Path(prior['run_dir'])/'run.json')
        with Path(prior['scores_file']).open(encoding='utf-8', newline='') as handle:
            prior_rows = list(csv.DictReader(handle))
        prior_keys = {(r['question_id'], r['response_label']) for r in prior_rows}
        if prior_keys & seen: raise ValueError('Stage A/B review slots overlap')
        # prior_stage already validated every row, identity and immutable run file.
        for row in prior_rows:
            graded[(row['question_id'], row['response_label'])] = row
            seconds += money(row['review_seconds'])
            critical += row['critical_error'] == 'YES'; disputes += row['reference_dispute'] == 'YES'
        slots = prior_result['slots'] + slots
        total_known_cost += prior_cost
        aggregation_scope = 'stage_a_and_b'
        prior_hashes = {k: prior[k] for k in ('run_sha256', 'scores_sha256')}
    paired = [qid for qid in dict.fromkeys(s['question_id'] for s in slots)
              if all((qid, label) in graded for label in ('A', 'B'))]
    mean = lambda values: sum(values)/len(values) if values else None
    models = {}
    for model in config['models']:
        model_slots = [s for s in slots if s['model_key'] == model]
        matched = [s for s in model_slots if s['question_id'] in paired]
        score = lambda s: int(graded[(s['question_id'], s['response_label'])]['score'])
        models[model] = {
            'planned': len(model_slots), 'valid': sum(s['status'] == 'valid' for s in model_slots),
            'failed': sum(s['status'] == 'failed' for s in model_slots),
            'not_run': sum(s['status'] == 'not_run' for s in model_slots),
            'reviewed': sum((s['question_id'], s['response_label']) in graded for s in model_slots),
            'paired_count': len(matched),
            'per_type_paired_count': {t: sum(s['type'] == t for s in matched) for t in v1.TYPES},
            'paired_mean': mean([score(s) for s in matched]),
            'per_type_mean': {t: mean([score(s) for s in matched if s['type'] == t]) for t in v1.TYPES},
            'per_family_mean': {f: mean([score(s) for s in matched if s['family_id'] == f]) for f in sorted({s['family_id'] for s in model_slots})},
            'latency_mean_seconds': mean([s['receipt']['elapsed_seconds'] for s in model_slots if s['receipt'] and 'elapsed_seconds' in s['receipt']]),
            'critical_errors': sum(graded.get((s['question_id'], s['response_label']), {}).get('critical_error') == 'YES' for s in model_slots)}
        model_report = models[model]
        costs = [s['receipt'].get('cost_usd') for s in model_slots if s['receipt']]
        model_report['known_cost_usd'] = str(sum((money(c) for c in costs if c is not None), Decimal(0)))
        model_report['billing_complete'] = all(c is not None for c in costs)
        model_report['failure_flags'] = dict(Counter(s['error'] for s in model_slots if s['error']))
        model_report['per_family_paired_count'] = {f: sum(s['family_id'] == f for s in matched) for f in model_report['per_family_mean']}
    screen = config['quality_proposal']
    complete = len(graded) == len(slots) and len(paired)*2 == len(slots)
    passed = (complete and result['status'] == 'completed' and critical == 0 and disputes == 0
              and all(m['paired_mean'] is not None and m['paired_mean'] >= screen['overall_mean_min']
                      and all(v is not None and v >= screen['per_type_mean_min'] for v in m['per_type_mean'].values()) for m in models.values()))
    accepted_answers = sum(r['score'] == '2' and r['critical_error'] == 'NO' and r['reference_dispute'] == 'NO' for r in graded.values())
    eligible = passed and result['mode'] == 'live' and result['billing_complete']
    for model, report in models.items():
        model_scores = [graded[(s['question_id'], s['response_label'])] for s in slots
                        if s['model_key'] == model and (s['question_id'], s['response_label']) in graded]
        accepted_count = sum(r['score'] == '2' and r['reference_dispute'] == 'NO' for r in model_scores)
        quality = (complete and disputes == 0 and result['status'] == 'completed' and report['critical_errors'] == 0
                   and report['paired_mean'] >= screen['overall_mean_min']
                   and all(v is not None and v >= screen['per_type_mean_min'] for v in report['per_type_mean'].values()))
        report['proposed_quality_screen_passed'] = quality
        report['accepted_answers'] = accepted_count
        report['cost_per_accepted_answer_usd'] = str(money(report['known_cost_usd'])/accepted_count) if quality and result['mode'] == 'live' and result['billing_complete'] and accepted_count else None
    return {'schema': 'broadbridge.helper_scores_summary/2', 'mode': result['mode'], 'stage': result['stage'],
            'aggregation_scope': aggregation_scope, 'prior_stage_a_hashes': prior_hashes,
            'run_sha256': run_hash, 'scores_sha256': prep.sha(Path(scores).read_bytes()),
            'planned_slots': len(slots), 'reviewed_slots': len(graded), 'unreviewed_slots': len(slots)-len(graded),
            'matched_pairs': len(paired), 'critical_errors': critical, 'reference_disputes': disputes,
            'review_minutes': float(seconds/60), 'models': models,
            'paired_difference_qwen_minus_mistral': (models['qwen']['paired_mean']-models['mistral']['paired_mean']) if paired else None,
            'known_cost_usd': str(total_known_cost), 'held_reservations_usd': result['held_reservations_usd'],
            'billing_complete': result['billing_complete'], 'accepted_answers': accepted_answers,
            'cost_per_accepted_answer_usd': str(total_known_cost/accepted_answers) if eligible and accepted_answers else None,
            'proposed_screen_passed': passed, 'decision_eligible': False,
            'model_selection_approved': False, 'training_approved': False,
            'limitations': ['development calibration, not fresh independent confirmation',
                            'file review is an operator record, not authenticated engineering sign-off',
                            'mock billing and grades are never evidence']}


def aggregate(run, scores, output):
    summary = summarize(run, scores)
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    stamp(output/'scores_summary.json', summary)
    lines = ['# Paired helper scores', '', '**MOCK ONLY**' if summary['mode'] == 'mock' else 'Development calibration only.', '',
             f"Reviewed {summary['reviewed_slots']}/{summary['planned_slots']} slots; {summary['matched_pairs']} matched pairs.",
             f"Critical errors: {summary['critical_errors']}; reference disputes: {summary['reference_disputes']}.",
             f"Review time: {summary['review_minutes']} minutes. No model-selection or training approval.", '',
             '| Type | Mistral mean / 2 | Qwen mean / 2 |', '| --- | ---: | ---: |']
    for t in v1.TYPES:
        values = [summary['models'][m]['per_type_mean'][t] for m in ('mistral', 'qwen')]
        lines.append('| '+t+' | '+' | '.join('UNREVIEWED' if v is None else f'{v:.2f}' for v in values)+' |')
    lines += ['', f"Known reported cost: {summary['known_cost_usd']} USD; held for unresolved billing: {summary['held_reservations_usd']} USD.",
              'Mock costs are simulated. Full coverage, failures, family means and receipts are in the JSON report.', '']
    (output/'scores_summary.md').write_text('\n'.join(lines), encoding='utf-8')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    proposal = sub.add_parser('plan'); proposal.add_argument('--packet', type=Path, required=True)
    proposal.add_argument('--out', type=Path, required=True); proposal.add_argument('--foundry', type=Path, required=True)
    proposal.add_argument('--mistral-reasoning', choices=['disabled', 'native_nonreasoning'])
    proposal.add_argument('--qwen-reasoning', choices=['disabled', 'native_nonreasoning'])
    run = sub.add_parser('run'); run.add_argument('--packet', type=Path, required=True)
    run.add_argument('--out', type=Path, required=True); run.add_argument('--foundry', type=Path, required=True)
    run.add_argument('--mode', choices=['mock', 'live'], default='mock')
    run.add_argument('--approval', type=Path); run.add_argument('--approve-sha256')
    score = sub.add_parser('score'); score.add_argument('--run', type=Path, required=True)
    score.add_argument('--scores', type=Path, required=True); score.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'plan':
        config, *_ = read_packet(args.packet)
        default = 'native_nonreasoning' if prep.protocol_version(config) in {'v3', 'v4'} else 'disabled'
        plan(args.packet, args.out, args.foundry, reasoning={'mistral': args.mistral_reasoning or default, 'qwen': args.qwen_reasoning or default})
        print('Incomplete approval worksheet and wire payloads saved; no model called.')
    elif args.command == 'run':
        result = execute(args.packet, args.out, args.foundry, mode=args.mode, approval=args.approval, approve_hash=args.approve_sha256)
        print(json.dumps({k: result[k] for k in ('mode', 'stage', 'status', 'calls_attempted', 'live_calls', 'known_cost_usd', 'billing_complete')}))
    else:
        print(json.dumps(aggregate(args.run, args.scores, args.out), indent=2))


if __name__ == '__main__':
    main()
