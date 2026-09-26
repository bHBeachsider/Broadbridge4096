"""SD-03 mock rehearsal: two fabricated jobs, no model transport or release."""
import argparse
from copy import deepcopy
import importlib
import importlib.util
import json
from pathlib import Path
import sys

import yaml


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mock', action='store_true', required=True)
    parser.add_argument('--foundry', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args=parser.parse_args(argv)
    if not args.foundry.is_absolute() or not (args.foundry/'src/ingestion/synthetic_batch.py').is_file():
        raise ValueError('Choose an absolute Foundry checkout with SD-03 installed')
    if not args.out.is_absolute() or args.out.exists(): raise ValueError('Choose a new absolute output directory')
    sys.path.insert(0,str(args.foundry.resolve()))
    modules={n: importlib.import_module('src.ingestion.'+n) for n in ('synthetic_batch','contracts','datasets')}
    if any(not Path(m.__file__).resolve().is_relative_to(args.foundry.resolve()) for m in modules.values()):
        raise ValueError('Loaded Foundry modules do not belong to the selected checkout')
    digest=modules['contracts'].content_hash
    domain=Path(__file__).resolve().parents[2]/'packs/oil-gas/synthetic'
    curriculum=yaml.safe_load((domain/'recipes.yaml').read_text(encoding='utf-8'))
    if curriculum['priority_decision']['status']!='awaiting_bill':
        raise ValueError('This mock-only script expects the unchanged draft curriculum')
    prompts={role: (domain/'prompts'/f'{role}.md').read_text(encoding='utf-8') for role in ('author','challenger')}
    rubric=(domain/'rubric.md').read_text(encoding='utf-8')
    # Reuse SD-02's explicit fictional sources; no real case/export is accepted.
    spec=importlib.util.spec_from_file_location('sd02_rehearsal',Path(__file__).with_name('rehearse_synthetic_experts.py'))
    seed=importlib.util.module_from_spec(spec); spec.loader.exec_module(seed)
    args.out.mkdir(parents=True,exist_ok=False)
    seed.main(['--foundry',str(args.foundry),'--out',str(args.out/'seed')])
    documents=[]; jobs=[]; answers={}
    for proposal in curriculum['recipes']:
        identity=proposal['fixture_source']
        doc=json.loads((args.out/'seed'/f'{identity}.document.json').read_text())
        original=json.loads((args.out/'seed'/f'{identity}.packet.json').read_text())
        recipe=deepcopy(original['recipe'])
        recipe.update(recipe_id=proposal['recipe_id'],version=proposal['version'],task_type=proposal['task_type'],
                      prompt_sha256=digest(prompts),rubric_sha256=digest(rubric))
        jobs.append({'job_id':identity,'document':doc,'recipe':recipe,'prompts':prompts,'rubric':rubric,
            'forbidden_strings':['PRIVATE SYNTHETIC HINDSIGHT','PRIVATE SYNTHETIC REFERENCE'],'cloud_approvals':{}})
        candidate=original['candidate']
        answers[doc['blocks'][0]['text']]={'question':candidate['messages'][0]['content'].split('\n\nSource evidence:')[0],
            'answer':candidate['messages'][-1]['content'],'task_type':proposal['task_type'],
            'evidence':[{'block_id':b['block_id'],'quote':b['text']} for b in doc['blocks']]}
        documents.append(doc)
    plan={'schema':'foundry.synthetic_batch_plan/1','run_id':'broadbridge-fabricated-batch','mode':'mock',
        'max_candidates':2,'max_calls':4,'cost_stop_usd':0.01,'verifier_id':'pending-expert-checks-v1',
        'roles':{r:{'model':f'fixture/{r}-v1','providers':['offline'],'settings':{'temperature':0,'think':False,'max_tokens':512},
                    'pack_path':None,'policy_sha256':None} for r in ('author','challenger')},
        'family_history':[],'approval':None,'jobs':jobs}
    def call(role, request):
        payload=json.loads(request['messages'][1]['content'])
        value=deepcopy(answers[payload['evidence_blocks'][0]['text']]) if role=='author' else {'objections':[]}
        return value, {'requested_model':f'fixture/{role}-v1','returned_model':f'fixture/{role}-v1','provider':'offline',
                       'cost_usd':0,'prompt_tokens':0,'completion_tokens':0,'valid':True,'retries':0}
    def verifier(candidate, document):
        checks={name:{'status':'needs_review','evidence':[],'limitation':'Independent expert review not performed.'}
                for name in modules['synthetic_batch'].CHECKS}
        checks['arithmetic']={'status':'not_applicable','evidence':[],'limitation':'No calculation requested.'}
        return checks
    batch=modules['synthetic_batch'].run_batch(plan,author=lambda r:call('author',r),
        challenger=lambda r:call('challenger',r),verifier=verifier,output_root=args.out/'batch')
    packets=[json.loads(f.read_text()) for f in sorted((args.out/'batch').glob('*.packet.json'))]
    try:
        modules['datasets'].prepare_release_candidate([p['candidate'] for p in packets],documents,
            pack_name='synthetic-batch-rehearsal',recipe_version='draft-1')
    except modules['datasets'].DatasetError: blocked=True
    else: raise AssertionError('Pending synthetic drafts must not become a release')
    report={'schema':'broadbridge.synthetic_batch_rehearsal/1','external_model_calls':0,
        'mock_role_calls':batch['calls'],'pending_packets':batch['pending_packets'],
        'priority_decision':curriculum['priority_decision']['status'],'curriculum_sha256':digest(curriculum),
        'release_blocked_without_review':blocked,'training_approved':False}
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0


if __name__=='__main__': raise SystemExit(main())
