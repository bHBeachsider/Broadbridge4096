"""Prepare FQ-07 paired requests offline. No keys, HTTP, models or live mode.

This is a protocol compiler, not a replacement for the v1 live runner.
"""
import argparse
from collections import Counter
import copy
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import public_document_evaluation as v1

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'packs/oil-gas-public-intake/eval/public-v1/sample.json'
PROTOCOL = SAMPLE.parent.parent / 'public-v2/protocol.json'
PROMPT = PROTOCOL.with_name('prompt.md')
FIELDS = ['source_id', 'family_id', 'question_id', 'type', 'response_label',
          'response_status', 'score', 'critical_error', 'reference_dispute',
          'review_seconds', 'reviewer', 'review_date', 'notes']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def protocol_path(version='v2'):
    if version not in {'v2', 'v3', 'v4'}:
        raise ValueError('Unknown comparison protocol version')
    return PROTOCOL.parent.parent / ('public-'+version) / 'protocol.json'


def protocol_version(config):
    for version in ('v2', 'v3', 'v4'):
        if config['schema'] == 'broadbridge.helper_comparison_protocol/'+version[1:]:
            return version
    raise ValueError('Unknown comparison protocol schema')


def load_protocol(version='v2'):
    return json.loads(protocol_path(version).read_text(encoding='utf-8'))


def reservations(config):
    """Per-arm reservations, not predictions of input length or final charges."""
    limits = config['limits']; result = {}
    for key, arm in config['models'].items():
        policy = arm['reservation'] if protocol_version(config) in {'v3', 'v4'} else limits
        context = policy['context_tokens'] if protocol_version(config) in {'v3', 'v4'} else policy['max_input_tokens_for_budget']
        prices = policy['max_price_usd_per_million']
        fee = Decimal(policy.get('max_non_token_fee_usd', '0'))
        values = [Decimal(prices['prompt']), Decimal(prices['completion']), fee]
        if type(context) is not int or context <= 0 or any(not n.is_finite() or n < 0 for n in values):
            raise ValueError('Invalid reservation policy')
        result[key] = (Decimal(context)*values[0] + Decimal(limits['max_output_tokens'])*values[1])/Decimal(1000000) + fee
    return result


def validate_inputs(config, sample, sample_bytes):
    if sha(sample_bytes) != config['base_sample_sha256']:
        raise ValueError('Frozen public-v1 sample hash mismatch')
    if sample != json.loads(sample_bytes):
        raise ValueError('Parsed sample does not match frozen sample bytes')
    v1.validate_sample(sample)
    protocol_version(config)
    if (config['live_authorized'] is not False or config['training_approved'] is not False
            or config['evaluation_role'] != 'development_calibration'):
        raise ValueError('Preparation cannot authorize live use, training or a held-out claim')
    questions = {q['question_id']: q for q in sample['questions']}
    stages = config['stages']
    ids = stages['stage_a']['question_ids'] + stages['stage_b']['question_ids']
    if len(ids) != 30 or len(set(ids)) != 30 or set(ids) != set(questions):
        raise ValueError('Stage selection must partition all thirty questions exactly once')
    for stage, count in [('stage_a', 2), ('stage_b', 4)]:
        selected = [questions[qid] for qid in stages[stage]['question_ids']]
        if Counter(q['type'] for q in selected) != Counter(dict.fromkeys(v1.TYPES, count)):
            raise ValueError('Stage type coverage is unbalanced')
        if stages[stage]['max_calls'] != len(selected) * 2:
            raise ValueError('Call bound does not match paired questions')
    if len({questions[q]['source_id'] for q in stages['stage_a']['question_ids']}) != 10:
        raise ValueError('Stage A must cover each publication once')
    if set(config['models']) != {'mistral', 'qwen'}:
        raise ValueError('Two specified comparison arms required')
    limits = config['limits']
    if (limits['question_batch_size'] != 1 or limits['max_attempts_per_slot'] != 1
            or limits['concurrency'] != 1):
        raise ValueError('Single-question serial protocol required')


def messages_for(sample, question):
    source = next(s for s in sample['sources'] if s['source_id'] == question['source_id'])
    # All frozen blocks from this document, not answer-conditioned evidence selection.
    body = {'source_id': source['source_id'], 'source_title': source['title'],
            'publication_context': source['publication_context'],
            'blocks': [{k: b[k] for k in ('block_id', 'text')} for b in source['blocks']],
            'questions': [{k: question[k] for k in ('question_id', 'type', 'question')}]}
    messages = [{'role': 'system', 'content': PROMPT.read_text(encoding='utf-8')},
                {'role': 'user', 'content': json.dumps(body, ensure_ascii=False)}]
    v1.assert_no_reference_leak(sample, source, messages)
    return messages


def answer_schema(question_id):
    text = {'type': 'string', 'minLength': 1, 'maxLength': 240}
    return {'type': 'object', 'additionalProperties': False,
            'required': ['question_id', 'answer', 'evidence', 'uncertainties'],
            'properties': {
                'question_id': {'const': question_id},
                'answer': {'type': 'string', 'minLength': 1, 'maxLength': 1000},
                'uncertainties': {'type': 'array', 'maxItems': 3,
                                  'items': {'type': 'string', 'minLength': 1, 'maxLength': 160}},
                'evidence': {'type': 'array', 'minItems': 1, 'maxItems': 2, 'items': {
                    'type': 'object', 'additionalProperties': False,
                    'required': ['source_id', 'block_id', 'quote'],
                    'properties': {k: copy.deepcopy(text) for k in ('source_id', 'block_id', 'quote')}}}}}


def check_answer(sample, question, response):
    if next(Draft202012Validator(answer_schema(question['question_id'])).iter_errors(response), None):
        return ['response_schema_failed']
    source = next(s for s in sample['sources'] if s['source_id'] == question['source_id'])
    blocks = {b['block_id']: b['text'] for b in source['blocks']}
    errors = []
    if len(response['answer'].split()) > 100:
        errors.append('answer_word_limit')
    for evidence in response['evidence']:
        if (evidence['source_id'] != source['source_id'] or not evidence['quote'].strip()
                or evidence['block_id'] not in blocks
                or evidence['quote'] not in blocks[evidence['block_id']]):
            errors.append('invalid_exact_citation')
    return sorted(set(errors))


def build_requests(config, sample, stage):
    questions = {q['question_id']: q for q in sample['questions']}
    rows = []
    for index, qid in enumerate(config['stages'][stage]['question_ids']):
        question = questions[qid]
        messages = messages_for(sample, question)
        schema = answer_schema(qid)
        for label, model in v1.labels(index).items():
            prepared = {'model': config['models'][model]['requested_model'],
                        'messages': messages, 'response_schema': schema,
                        'settings': config['limits'],
                        'routing': {**config['routing_requirements'],
                                    'provider': config['models'][model]['requested_provider']}}
            request_bytes = len(v1.canonical(prepared))
            if request_bytes > config['limits']['max_request_bytes']:
                raise ValueError('Serialized request exceeds byte limit; no truncation allowed')
            rows.append({'question_id': qid, 'type': question['type'],
                         'source_id': question['source_id'], 'family_id': question['family_id'],
                         'model_key': model, 'response_label': label,
                         'status': 'prepared_not_run', 'execution_disabled': True,
                         'requested_model': prepared['model'],
                         'requested_provider': prepared['routing']['provider'],
                         'messages': messages, 'response_schema': schema,
                         'settings': config['limits'], 'routing_requirements': prepared['routing'],
                         'prompt_sha256': v1.digest(messages), 'schema_sha256': v1.digest(schema),
                         'request_bytes': request_bytes,
                         'input_tokens': None, 'returned_model': None, 'returned_provider': None,
                         'weights_revision': None, 'provider_revision': None,
                         'actual_cost_usd': None, 'latency_seconds': None})
    return rows


def prepare(output, stage='stage_a', *, protocol_version='v2'):
    config_path = protocol_path(protocol_version)
    config = load_protocol(protocol_version); sample_bytes = SAMPLE.read_bytes(); sample = json.loads(sample_bytes)
    validate_inputs(config, sample, sample_bytes)
    rows = build_requests(config, sample, stage)
    selected_ids = set(config['stages'][stage]['question_ids'])
    questions = [q for q in sample['questions'] if q['question_id'] in selected_ids]
    amounts = reservations(config)
    bound = sum((amounts[r['model_key']] for r in rows), Decimal(0))
    if protocol_version == 'v2' and bound > Decimal(config['stages'][stage]['proposed_ceiling_usd']):
        raise ValueError('Conditional token cost exceeds proposed stage budget')
    summary = {'schema': 'broadbridge.helper_comparison_preparation/'+protocol_version[1:],
               'version': config['version'], 'stage': stage, 'mode': 'offline_prepare',
               'evaluation_role': config['evaluation_role'], 'live_authorized': False,
               'training_approved': False, 'calls_attempted': 0, 'actual_cost_usd': '0',
               'question_count': len(questions), 'request_count': len(rows),
               'source_count': len({q['source_id'] for q in questions}),
               'family_count': len({q['family_id'] for q in questions}),
               'type_counts': dict(Counter(q['type'] for q in questions)),
               'proposed_stage_ceiling_usd': config['stages'][stage]['proposed_ceiling_usd'],
               'conditional_token_cost_bound_usd': str(bound.normalize()),
               'token_count_verified': False, 'model_availability_checked': False,
               'max_prepared_request_bytes': max(r['request_bytes'] for r in rows),
               'sample_sha256': sha(sample_bytes), 'protocol_sha256': sha(config_path.read_bytes()),
               'prompt_sha256': sha(PROMPT.read_bytes()), 'compiler_sha256': sha(Path(__file__).read_bytes()),
               'live_blockers': ['protocol_reference_and_budget_acceptance', 'fresh_source_rights_check',
                                 'provider_revision_and_capability_snapshot', 'exact_input_token_preflight',
                                 'clean_committed_v2_executor_and_foundry_receipts', 'spend_controls_and_exact_run_approval']}
    if protocol_version in {'v3', 'v4'}:
        del summary['conditional_token_cost_bound_usd']
        summary.update(pair_reservation_usd=str(sum(amounts.values())),
                       all_calls_fit_at_full_reservation=bound <= Decimal(config['stages'][stage]['proposed_ceiling_usd']),
                       full_stage_reservations_usd=str(bound),
                       reservation_policy='per_arm_full_context_plus_maximum_output')
        summary['live_blockers'] = [b.replace('exact_input_token_preflight', 'endpoint_context_billing_and_truncation_evidence')
                                   .replace('committed_v2', 'committed_'+protocol_version) for b in summary['live_blockers']]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    v1.write_json(output/'preparation.json', summary)
    (output/'protocol.json').write_bytes(config_path.read_bytes())
    (output/'prompt.md').write_bytes(PROMPT.read_bytes())
    (output/'sample.json').write_bytes(sample_bytes)
    (output/'requests.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    v1.write_json(output/'reviewer-only.json', {'reference_status': sample['reference_status'],
                                              'questions': questions, 'rubrics': v1.RUBRICS})
    with (output/'scores.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader()
        for request in rows:
            row = dict.fromkeys(FIELDS, '')
            row.update({k: request[k] for k in ('source_id', 'family_id', 'question_id', 'type', 'response_label')})
            row['response_status'] = 'prepared_not_run'
            writer.writerow(row)
    (output/'README.md').write_text(
        '# Offline helper comparison packet\n\nNo model was called. All score rows remain blank.\n'
        'requests.jsonl is a preparation artifact, not executable OpenRouter request syntax.\n'
        'reviewer-only.json contains references and must never be sent to a model.\n'
        'Do not upload this packet into public-v1 or reuse the v1 runner with v2 labels.\n'
        'See docs/HELPER_COMPARISON_'+protocol_version.upper()+'.md for approval, receipt and scoring requirements.\n', encoding='utf-8')
    v1.write_json(output/'checksums.json', {p.name: sha(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()})
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New exclusive output directory')
    parser.add_argument('--stage', choices=['stage_a', 'stage_b'], default='stage_a')
    parser.add_argument('--protocol-version', choices=['v2', 'v3', 'v4'], default='v2')
    args = parser.parse_args(argv)
    print(json.dumps(prepare(args.out, args.stage, protocol_version=args.protocol_version), indent=2))


if __name__ == '__main__':
    main()
