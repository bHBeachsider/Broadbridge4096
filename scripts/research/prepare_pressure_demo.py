"""Build an offline, rights-pending Qwen teaching package; never launch training.

The files are review candidates, NOT foundry.dataset_release/1 artifacts.
DOE family reallocation is proposed, not silently applied to the source register.
"""
import argparse
from collections import Counter
import hashlib
from importlib import metadata
import json
from pathlib import Path
import sys

from prepare_first_dataset_review import FAMILY, SOURCE, SOURCE_SHA, pressure_result, verify_extraction

ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / 'docs/evidence/first-pressure-review-2026-09-30/proposal.json'
PROPOSAL_SHA = '632adea4db2c9f8ab16f8882bcdb3993aabc9a80e06ee144cca316b99e1f3fef'
PACKET_SHA = '0ae8da768e4fbc5427d5c4acbd4b2193dcf93308fffac6e8cb61fce26f0b8150'
REVISION = '946bc9ac74a6c1f8cf012497c503a119b2fcf2eb'
SYSTEM = ('You are a pressure-basis checking assistant for an engineering demonstration. '
          'Return JSON with answer (string), calculation (object or null), '
          'missing_information (array of strings), limitations (array of strings), '
          'and source_ids (array of supplied evidence IDs). Use compatible units and stated references. '
          'Request missing inputs; do not invent atmospheric pressure or certify operating safety. '
          'Give a concise explanation, with no thinking trace. /no_think')
EVIDENCE = (f'Provided paraphrased evidence notes (not verbatim source): {SOURCE}:pdf-035: '
            'gauge pressure is relative to the relevant atmospheric reference; absolute pressure '
            'is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. '
            f'{SOURCE}:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. '
            'For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. '
            'The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. '
            f'{SOURCE}:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded '
            'water-column and mercury-column equivalents. These examples do not measure local atmosphere. '
            'Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or '
            'rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.')
RESPONSE_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
    'type': 'object', 'additionalProperties': False,
    'required': ['answer', 'calculation', 'missing_information', 'limitations', 'source_ids'],
    'properties': {'answer': {'type': 'string', 'minLength': 1},
        'calculation': {'anyOf': [{'type': 'null'}, {'type': 'object', 'additionalProperties': False,
            'required': ['mode', 'atmospheric_psia', 'reading_psi', 'formula', 'expression', 'result', 'unit'],
            'properties': {key: {'type': 'string'} for key in
                ['mode', 'atmospheric_psia', 'reading_psi', 'formula', 'expression', 'result', 'unit']}}]},
        **{key: {'type': 'array', 'items': {'type': 'string'}} for key in
            ['missing_information', 'limitations', 'source_ids']}}}


def verify_file(path, expected):
    payload = Path(path).read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError('Pinned input hash mismatch')
    return payload


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def messages(question):
    return [{'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': EVIDENCE + '\n\nTask: ' + question}]


def candidate(identifier, kind, question, answer, evidence_ids, calculation=None, origin=None):
    target = {'answer': answer, 'calculation': calculation,
              'missing_information': [],
              'limitations': ['Educational pressure-basis check; not an operating limit or safety approval.'],
              'source_ids': evidence_ids}
    # Missing inputs are already explicit in the authored answer; keep this array
    # populated for the dedicated examples rather than inventing numeric values.
    if kind == 'missing_data':
        target['missing_information'] = [answer]
    return {'example_id': identifier, 'type': kind, 'family_id': FAMILY,
            'source_id': SOURCE, 'source_sha256': SOURCE_SHA,
            'evidence_ids': evidence_ids, 'author': 'assistant-authored with deterministic Decimal arithmetic',
            'origin': origin, 'split': None, 'proposed_split': 'train',
            'rights_status': 'TBD', 'permission_status': 'pending', 'training_approved': False,
            'messages': messages(question) + [{'role': 'assistant', 'content': dumps(target)}]}


def training_rows():
    proposal = json.loads(verify_file(PROPOSAL, PROPOSAL_SHA))
    rows = []
    # Deliberately small fixed recipes; these are 24 numerical variants, not
    # 24 independent engineering case families. No random train/test partition.
    gauge = [('14.2', '20.0'), ('14.2', '-3.0'), ('13.6', '7.5'), ('15.0', '-1.2'),
             ('14.7', '0.0'), ('12.5', '22.8'), ('14.8', '31.1'), ('13.9', '-0.7'),
             ('14.0', '18.6'), ('14.6', '5.4'), ('13.2', '-2.5'), ('14.9', '41.3')]
    vacuum = [('14.3', '2.0'), ('14.6', '6.2'), ('13.7', '3.1'), ('14.8', '0.0'),
              ('12.8', '4.4'), ('14.1', '8.0'), ('14.5', '1.7'), ('13.8', '5.5'),
              ('14.4', '7.2'), ('15.0', '10.1'), ('13.5', '9.0'), ('14.7', '9.1')]
    for mode, inputs in [('gauge', gauge), ('vacuum', vacuum)]:
        for atmosphere, reading in inputs:
            result = pressure_result(mode, atmosphere, reading)
            label = 'gauge reading (psig)' if mode == 'gauge' else 'positive vacuum depression (psi below atmosphere)'
            question = (f'Illustrative instrument record: local atmospheric pressure {atmosphere} psia; '
                        f'{label} {reading}. Calculate absolute pressure in psia and show the sign convention.')
            sign = '+' if mode == 'gauge' else '-'
            calculation = {'mode': mode, 'atmospheric_psia': atmosphere, 'reading_psi': reading,
                           'formula': 'P_abs = P_atm ' + sign + (' P_gauge' if mode == 'gauge' else ' P_vac'),
                           'expression': f'{atmosphere} {sign} ({reading})', 'result': result, 'unit': 'psia'}
            rows.append(candidate(f'DOE-DEMO-CALC-{len(rows)+1:02}', 'calculation', question,
                f'Absolute pressure is {result} psia using the supplied local atmospheric reference.',
                [f'{SOURCE}:pdf-036'], calculation, 'fixed_decimal_recipe_v1'))
    for q in proposal['questions']:
        if q['type'] != 'calculation':
            rows.append(candidate('DOE-DEMO-' + q['question_id'], q['type'], q['question'],
                q['reference_answer'], q['evidence_ids'], origin=q['question_id']))
    return rows


def demonstration_rows():
    # New wording/values, but the SAME source family and recipes. Not independent.
    specs = [
        ('calculation', 'A transmitter is explicitly referenced to local atmosphere. It reads 27.4 psig; the relevant atmospheric pressure is 13.2 psia. Convert to psia.',
         '40.6 psia, obtained by adding 13.2 and 27.4.', 'Wrong sign, units or result.', {'result': '40.6', 'unit': 'psia'}),
        ('calculation', 'An instrument reads -1.4 psig with atmospheric reference 14.6 psia. Report absolute pressure.',
         '13.2 psia; negative gauge does not imply negative absolute pressure.', 'Negative absolute claim or wrong conversion.', {'result': '13.2', 'unit': 'psia'}),
        ('calculation', 'Positive vacuum depression is 6.1 psi, and local atmosphere is 13.2 psia. What is the absolute pressure?',
         '7.1 psia, obtained by subtracting 6.1 from 13.2.', 'Adding the depression or using an unstated atmosphere.', {'result': '7.1', 'unit': 'psia'}),
        ('missing_data', 'A field note says pressure = 25 psi. The pressure reference and local atmospheric pressure are not recorded. Give an absolute pressure or request what is needed.',
         'Request the pressure basis and, if gauge or vacuum, the relevant atmospheric reference and sign convention. Do not invent a numerical absolute pressure.',
         'Assuming psig or 14.7 psia without disclosure and supplying a definitive result.', None),
        ('brief', 'Two records list 30 psia and 30 psig from a remote site. Describe a check before treating them as equal pressures.',
         'They have different pressure references. Obtain the gauge reference, convert onto one basis with compatible units, and retain both originals.',
         'Treating them as interchangeable or declaring a plant condition safe.', None),
        ('grounded_explanation', 'A colleague says every vacuum value is added to atmosphere because it is a positive number. Explain the error using the supplied note.',
         'A positive vacuum-depression magnitude is subtracted from the relevant atmospheric pressure. Confirm the convention before applying the equation and cite the supplied page 36.',
         'Adding a positive depression or citing absent evidence.', None),
        ('abstention', 'This pressure-basis note is the only evidence. Is a reactor at 55 psig safe to operate? Give a go/no-go decision.',
         'The definitions cannot establish safe operation. Request equipment limits, design basis, process conditions and qualified review; do not issue operating approval.',
         'Certifying safety or supplying a permissible limit without evidence.', None),
        ('abstention', 'A watch limit and a fluid density in lbm/ft3 are given, but the force/gravity convention is omitted. Use this demonstration to calculate an allowable dive depth.',
         'Decline the depth calculation in this limited pressure-basis recipe; the explicit hydrostatic method and mass/force convention need review.',
         'Giving a numerical safe depth through the excluded hydrostatic recipe.', None),
    ]
    prompts, keys = [], []
    for number, (kind, question, answer, fail, calculation) in enumerate(specs, 1):
        identifier = f'DOE-DEMO-PROBE-{number:02}'
        prompts.append({'question_id': identifier, 'type': kind, 'family_id': FAMILY,
                        'independent_test': False, 'usage': 'same-family demonstration only',
                        'messages': messages(question)})
        keys.append({'question_id': identifier, 'reference_answer': answer,
                     'hard_fail_criteria': fail, 'calculation': calculation,
                     'tolerance': '+/-0.05 psi rounding tolerance, not sensor accuracy' if calculation else 'not applicable'})
    return prompts, keys


def build(out, *, pdf=None, evidence_dir=None):
    out = Path(out)
    if not out.is_absolute() or out.exists():
        raise ValueError('Use a fresh absolute output directory')
    proposal_bytes = verify_file(PROPOSAL, PROPOSAL_SHA)
    if pdf:
        verify_file(pdf, SOURCE_SHA)
    if evidence_dir and verify_extraction(Path(evidence_dir)) != PACKET_SHA:
        raise ValueError('Extraction packet hash mismatch')
    rows = training_rows()
    prompts, keys = demonstration_rows()
    config = {
        'name': 'broadbridge-doe-pressure-demo-v1',
        'model': {'base': 'unsloth/Qwen3-8B', 'revision': REVISION,
                  'chat_template': 'qwen-2.5', 'max_seq_length': 2048, 'load_in_4bit': True},
        'lora': {'r': 16, 'alpha': 16, 'dropout': 0.0},
        'train': {'evaluate': False, 'epochs': 1, 'max_steps': 20, 'per_device_batch_size': 1,
                  'grad_accum': 8, 'learning_rate': 0.0002, 'warmup_steps': 2,
                  'lr_scheduler': 'cosine', 'weight_decay': 0.01, 'seed': 3407,
                  'save_steps': 5, 'save_total_limit': 2, 'logging_steps': 1},
        'data': {'train': str(out / 'train_candidates.jsonl')},
        'output_dir': str(out / 'NOT_AUTHORIZED_MODEL_OUTPUT')}
    scorecard = ['# Bill demonstration scorecard', '',
        '**Unrun and unscored. Same-family probes; not an independent benchmark.**', '',
        'Score each answer: 0 incorrect/missing, 1 needs correction, 2 correct and supported. '
        'A critical error matching demo_answer_key.jsonl forces 0. Compare all eight, including regressions.', '',
        '| Question | Base 0/1/2 | Adapter 0/1/2 | Critical error base/adapter | Reviewer notes |',
        '| --- | --- | --- | --- | --- |']
    scorecard += [f"| {p['question_id']} | | | | |" for p in prompts]
    scorecard += ['', 'Reviewer / date: __________',
                  'Useful in Bill\'s work? What harder case should be next? __________', '']
    files = {'train_candidates.jsonl': ''.join(dumps(r) + '\n' for r in rows),
             'demo_prompts.jsonl': ''.join(dumps(r) + '\n' for r in prompts),
             'demo_answer_key.jsonl': ''.join(dumps(r) + '\n' for r in keys),
             'response.schema.json': json.dumps(RESPONSE_SCHEMA, indent=2) + '\n',
             'proposed_config.json': json.dumps(config, indent=2) + '\n',
             'scorecard.md': '\n'.join(scorecard)}
    manifest = {'schema': 'broadbridge.pressure_demo_preparation/1', 'status': 'prepared_not_released',
        'training_approved': False, 'execution_authorized': False, 'rights_status': 'TBD',
        'actual_bill_signoff': None, 'model_calls': 0, 'optimizer_steps': 0,
        'counts': {'train_candidates': len(rows), 'demo_probes': len(prompts),
                   'independent_validation': 0, 'independent_test': 0},
        'type_counts': dict(Counter(r['type'] for r in rows)),
        'source': {'source_id': SOURCE, 'family_id': FAMILY, 'sha256': SOURCE_SHA,
                   'pdf_pages': [35, 36, 37], 'raw_pdf_reverified': bool(pdf),
                   'extraction_reverified': bool(evidence_dir), 'extraction_sha256': PACKET_SHA,
                   'proposal_sha256': hashlib.sha256(proposal_bytes).hexdigest()},
        'family_transition': {'status': 'proposed_not_applied', 'from': 'dev/testing_only',
            'to': 'train for a bounded demonstration',
            'condition': 'Record source-use decision and explicit family reallocation before release.',
            'consequence': 'pressure-diagnostic-v1 and all DOE-HDBK-1012 derivatives lose independent-test eligibility after training; preserve historical files.'},
        'pending': ['source-use/rights decision', 'family reallocation', 'exact candidate acceptance/release',
                    'bounded execution approval and training-capable host packet'],
        'proposed_limits': {'optimizer_steps': 20, 'training_wall_seconds': 1800,
             'host_wall_seconds': 5400, 'guest_stop_minute': 80, 'api_stop_minute': 85,
             'force_stop_by_minute': 87, 'verify_stopped_by_minute': 90,
             'comparison_model_calls_max': 16, 'max_new_tokens_per_call': 384,
             'comparison_phase_seconds_max': 900},
        'comparison': {'template': 'qwen-2.5 pinned Foundry ChatML for both',
             'thinking': False, 'do_sample': False, 'max_new_tokens': 384,
             'retrieval': 'fixed identical evidence note supplied in each prompt; no document index',
             'base': 'same pinned NF4 checkpoint; adapter disabled/absent',
             'adapter': 'same checkpoint and quantization with the produced adapter',
             'not_claimed': ['independent accuracy improvement', 'S0-retrieval acceptance', 'Gate 0 closure']},
        'artifacts': {name: {'sha256': hashlib.sha256(value.encode()).hexdigest(), 'bytes': len(value.encode())}
                      for name, value in files.items()}}
    out.mkdir(parents=True)
    for name, value in files.items():
        (out / name).write_text(value, encoding='utf-8', newline='\n')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    return manifest


def audit(out, foundry, tokenizer_dir):
    """Use the real Foundry assistant-mask renderer, with only local tokenizer files."""
    sys.path.insert(0, str(ROOT / 'packs/oil-gas/scripts'))
    from case_preflight import load_token_counter
    _, token_receipt = load_token_counter(tokenizer_dir)  # verifies all four pinned files
    sys.path.insert(0, str(Path(foundry).resolve()))
    from src.train import prepare_records
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(Path(tokenizer_dir).resolve()),
        local_files_only=True, trust_remote_code=False, use_fast=True)
    out = Path(out)
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    for name, artifact in manifest['artifacts'].items():
        verify_file(out / name, artifact['sha256'])
    rows = [json.loads(line) for line in (out / 'train_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
    records, stats = prepare_records(rows, tokenizer, max_length=2048, chat_template='qwen-2.5')
    if stats['overlength_count']:
        raise ValueError('Candidate exceeds context; no truncation permitted')
    prompt_lengths = []
    for line in (out / 'demo_prompts.jsonl').read_text(encoding='utf-8').splitlines():
        prompt = json.loads(line)
        ids = tokenizer.apply_chat_template(prompt['messages'], tokenize=True,
            add_generation_prompt=True, return_dict=False)
        prompt_lengths.append(len(ids))
    if max(prompt_lengths) + 384 > 2048:
        raise ValueError('Demo prompt plus output reserve exceeds context')
    result = {'schema': 'broadbridge.pressure_demo_token_audit/1', 'status': 'offline_checks_passed_not_release',
        'training_approved': False, 'execution_authorized': False, 'train': stats,
        'supervised_tokens': sum(sum(t != -100 for t in r['labels']) for r in records),
        'total_tokens': sum(len(r['input_ids']) for r in records),
        'demo_prompt_token_lengths': prompt_lengths, 'demo_output_reserve': 384,
        'tokenizer': token_receipt, 'actual_template': 'Foundry qwen-2.5 pinned ChatML, overriding native HF thinking template',
        'train_renderer_sha256': hashlib.sha256((Path(foundry) / 'src/train.py').read_bytes()).hexdigest(),
        'python': sys.version.split()[0], 'transformers': metadata.version('transformers'),
        'scope': 'Local CPU rendering only; does not validate installed AWS runtime or GPU training.',
        'package_manifest_sha256': hashlib.sha256((out / 'manifest.json').read_bytes()).hexdigest()}
    preview = {'rendered': records[0]['text'], 'token_ids': records[0]['input_ids'],
               'labels': records[0]['labels'], 'assistant_mask': [int(t != -100) for t in records[0]['labels']]}
    for name, value in [('token_audit.json', result), ('rendered_batch.json', preview)]:
        with (out / name).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(value, indent=2) + '\n')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pdf', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--foundry', type=Path)
    parser.add_argument('--tokenizer-dir', type=Path)
    args = parser.parse_args(argv)
    if bool(args.foundry) != bool(args.tokenizer_dir):
        parser.error('--foundry and --tokenizer-dir must be supplied together')
    result = build(args.out, pdf=args.pdf, evidence_dir=args.evidence_dir)
    if args.foundry:
        audit(args.out, args.foundry, args.tokenizer_dir)
    print(dumps({'status': result['status'], 'counts': result['counts'], 'training_approved': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
