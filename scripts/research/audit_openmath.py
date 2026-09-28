"""Offline audit of the existing pinned 1200-row intake; never writes candidates."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

RAW_SHA = 'd3d0c3e9fcce74234e80f2f529226c64c8e258296dc5aaa14725b1cd2e4b112d'
DATASET_REVISION = '469216e3f46f4dacf476b382e192485ea51a143e'


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def checked_file(root, relative, sha):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path.read_bytes()) != sha:
        raise ValueError('Missing, escaped or changed input file')
    return path


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def audit_inputs(raw, splits, rejected):
    seen = {}; rejects = {}
    for split, candidates in splits.items():
        if split not in {'train','val','test'}: raise ValueError('Invalid original split')
        for c in candidates:
            index = c['source_row_index']
            if type(index) is not int or index in seen or not 0 <= index < len(raw):
                raise ValueError('Invalid/duplicate candidate index')
            r = raw[index]
            family = digest(' '.join(r['problem'].casefold().split()).encode())
            bucket = int(family[:8], 16) % 10
            original_split = 'train' if bucket < 8 else 'val' if bucket == 8 else 'test'
            expected_messages = [{'role':'user','content':r['problem']},
                                 {'role':'assistant','content':r['generated_solution']}]
            if (c['expected_answer'] != r['expected_answer'] or c['messages'] != expected_messages
                or c['family_id'] != family or c['split'] != split or split != original_split):
                raise ValueError('Candidate does not match original row/split')
            seen[index] = split
    for r in rejected:
        i = r['row_index']
        if type(i) is not int or i in rejects or i in seen or not 0 <= i < len(raw):
            raise ValueError('Invalid/duplicate rejected index')
        rejects[i] = r['reason']
    if set(seen) | set(rejects) != set(range(len(raw))):
        raise ValueError('Incomplete historical rows')
    return [{'id': f'OMI2-first-shard-{i:04d}', 'problem': r['problem'],
             'expected_answer': r['expected_answer'], 'historical_splits': [seen[i]] if i in seen else [],
             'excluded': i in rejects, 'exclusion_reason': rejects.get(i)} for i,r in enumerate(raw)]


def independent_results():
    """Fixed checks written for the pinned sample; no dataset answers used as oracle."""
    cubes = [n for n in range(100,1000) if n**3 % 1000 == 125]
    return {
        0: {'result': 5*3*(2+1), 'method':'people * days * bars/person/day'},
        1: {'result': sum(cubes), 'count':len(cubes), 'method':'enumerate every integer 100..999 with cube modulo 1000 = 125'},
        99: {'result':5+9+4, 'method':'quadratic formula in standard unsimplified form: m=5,n=9,p=4; representation convention assumed'},
        199: {'result':next(r for r in range(1,10) if r**3>24), 'method':'sphere volume inequality becomes r^3 > 24'},
        399: {'result':'(-1/2, 2)', 'method':'2=2r+3; 4=2k'},
        599: {'result':'ambiguous_or_inconsistent','witness_1':[10,10,10,10,8,10,10,12],
              'witness_2':[9,10,10,10,9,10,10,12], 'prefix_seven_total':80-12,
              'prefix_seven_remainder':(80-12)%7,
              'method':'If every prefix average is integer, first seven total 68 contradicts divisibility by 7. If only overall average is intended, two allocations give different fifth shelves; witnesses apply only to this weaker interpretation.'},
        799: {'result':[[2,0,7],[3,5,-1],[-8,-2,4]], 'method':'images of standard basis vectors are matrix columns'},
        999: {'result':str(Fraction(5,9)**4), 'method':'multiplicativity of complex modulus; |z|^8=(5/9)^4'},
        1099: {'result':(-3)**4//3**2 + 2**6 - 8, 'method':'integer exponent arithmetic'},
        1199: {'result':'inconsistent','height_squared_from_volume':(500//25)**2,
               'height_squared_from_diagonal':15**2-4*5**2,'method':'volume and supplied diagonal constraints imply different h^2'}
    }


def spot_checks(raw, raw_sha):
    if raw_sha != RAW_SHA or len(raw) != 1200:
        raise ValueError('Spot checks require the pinned 1200-row sample')
    results = []
    for index, check in independent_results().items():
        status = {1:'wrong_answer',599:'ambiguous_or_inconsistent',1199:'inconsistent'}.get(index,'final_answer_consistent')
        results.append({'source_row_index':index, 'problem_sha256':digest(raw[index]['problem'].encode()),
            'dataset_expected_answer':raw[index]['expected_answer'], 'status':status, **check})
    return results


def load_foundry(path, modules):
    path = path.resolve()
    if not (path/'src/data_audit.py').is_file(): raise ValueError('Select Foundry data-audit checkout')
    sys.path.insert(0,str(path))
    loaded = [importlib.import_module(name) for name in modules]
    if any(not Path(m.__file__).resolve().is_relative_to(path) for m in loaded):
        raise ValueError('Foundry module already imported from another checkout')
    return loaded


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('intake','foundry','tokenizer','out'): p.add_argument('--'+name,required=True,type=Path)
    a = p.parse_args(argv)
    if any(not x.is_absolute() for x in (a.intake,a.foundry,a.tokenizer,a.out)) or a.out.exists():
        raise ValueError('Use absolute inputs and a new output directory')
    receipt = json.loads((a.intake/'intake-report.json').read_text())
    if receipt['math']['revision'] != DATASET_REVISION: raise ValueError('Wrong dataset revision')
    # Resolve receipt paths relative to this exact intake folder, not the repository.
    prefix = 'packs/oil-gas/data/public-start-2026-09-24/'
    verified = []
    for entry in receipt['source_files'] + receipt['outputs']:
        if not entry['path'].startswith(prefix): raise ValueError('Unexpected receipt path')
        checked_file(a.intake,entry['path'][len(prefix):],entry['sha256'])
        verified.append(entry)
    for entry in receipt['tokenizer_files']: checked_file(a.tokenizer,entry['file'],entry['sha256'])
    raw_path = checked_file(a.intake,'raw/openmath/sample.jsonl',RAW_SHA)
    raw = jsonl(raw_path)
    splits = {s:jsonl(a.intake/f'candidates/math/{s}.jsonl') for s in ('train','val','test')}
    inputs = audit_inputs(raw,splits,jsonl(a.intake/'candidates/math/rejected.jsonl'))
    audit, train = load_foundry(a.foundry,['src.data_audit','src.train'])
    similarities = audit.audit_records(inputs)
    checks = spot_checks(raw,RAW_SHA)
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(a.tokenizer,local_files_only=True,use_fast=True)
    all_rows = [{'messages':[{'role':'user','content':r['problem']},
                            {'role':'assistant','content':r['generated_solution']}]} for r in raw]
    encoded, token_stats = train.prepare_records(all_rows,tokenizer,max_length=2048,chat_template='qwen-2.5')
    split_stats = {}
    for name, rows in splits.items():
        _,split_stats[name] = train.prepare_records(rows,tokenizer,max_length=2048,chat_template='qwen-2.5')
    preview = encoded[0]
    families = similarities['families']
    cross = [f for f in families if f['cross_split']]
    summary = {'schema':'broadbridge.math_audit/1','training_approved':False,'disposition':'quality_and_family_review_hold',
        'dataset':receipt['math'], 'raw_sha256':RAW_SHA, 'verified_files':verified,
        'tokenizer_files':receipt['tokenizer_files'], 'tokenizer_revision':json.loads((a.tokenizer/'revision.json').read_text()),
        'rows':len(raw),'excluded_history_rows':sum(r['excluded'] for r in inputs),
        'unassigned_history_rows':sum(not r['historical_splits'] for r in inputs),
        'original_split_counts':{s:len(r) for s,r in splits.items()},
        'exact_groups':len(similarities['exact_groups']),'template_groups':len(similarities['template_groups']),
        'near_pairs':len(similarities['near_pairs']),'proposed_families':len(families),
        'cross_split_families':len(cross),'cross_split_rows':sum(len(f['members']) for f in cross),
        'answer_conflict_groups':len(similarities['answer_conflicts']),
        'spot_check_statuses':dict(Counter(c['status'] for c in checks)), 'spot_checks':checks,
        'all_raw_token_stats':token_stats,'original_split_token_stats':split_stats,
        'assistant_target_tokens':sum(label!=-100 for r in encoded for label in r['labels']),
        'limitation':'Ten disclosed convenience spot-checks, final answers only; no population accuracy or full solution verification. Similarity families need manual adjudication. Originals are unchanged. No model weights, inference or training.'}
    a.out.mkdir(parents=True,exist_ok=False)
    outputs = {'summary':summary,'similarities':similarities,'history':inputs,
        'rendered-batch':{'rendered_text':preview['text'],'input_ids':preview['input_ids'],'labels':preview['labels'],
                          'assistant_mask':[int(x!=-100) for x in preview['labels']]}}
    for name,value in outputs.items():
        (a.out/(name+'.json')).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('dataset','verified_files','tokenizer_files','spot_checks')},indent=2))
    return 0


if __name__=='__main__': raise SystemExit(main())
