"""Frozen two-stage diagram development replay; no reference answers in inference."""
import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'docs/evidence/reference-graphs-2026-09-27'
NAMES=('forward-chain','reverse-chain','junction','crossing-clear','unknown-chain','mixed-junction')
CROPS={'forward-chain':(80,215,800,330),'reverse-chain':(80,215,800,330),
       'crossing-clear':(55,60,805,470),'mixed-junction':(85,55,790,325)}


def sha(data):return hashlib.sha256(data).hexdigest()


def write(path,obj):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')


def load(foundry):
    if not foundry.is_absolute():raise ValueError('Use an absolute Foundry checkout')
    sys.path.insert(0,str(foundry.resolve()))
    modules={n:importlib.import_module('src.ingestion.'+n) for n in
             ('diagram_tracing','reference_graphs','visual_connectivity','local_vision')}
    if any(not Path(m.__file__).resolve().is_relative_to(foundry.resolve()) for m in modules.values()):
        raise ValueError('Foundry checkout mismatch')
    modules['pins']=json.loads((foundry/'infra/vision/models.json').read_bytes())
    return modules


def prepare(out,modules):
    out.mkdir(parents=True,exist_ok=False)
    requests=[];drawings=[];trace=modules['diagram_tracing'];vc=modules['visual_connectivity']
    for name in NAMES:
        src=EVIDENCE/('crossing-correction' if name=='crossing-clear' else 'pilot')
        oldraw=(src/'job.json').read_bytes();old=json.loads(oldraw)
        q=next(q for q in old['requests'] if q['id']==name)
        raw=(src/'references.json').read_bytes()
        if sha(raw)!=old['references_sha256']:raise ValueError('Historical reference changed')
        ref=json.loads(raw)[name]['reference'];pixels=(src/q['image']).read_bytes()
        if sha(pixels)!=q['sha256'] or ref['image_sha256']!=q['sha256']:raise ValueError('Image changed')
        with (out/(name+'.png')).open('xb') as f:f.write(pixels)
        baseline_raw=(src/'results-qwen'/(name+'.json')).read_bytes();baseline=json.loads(baseline_raw)
        bindings={'id':name,'job_sha256':sha(oldraw),'input_sha256':q['sha256'],
                  'prompt_sha256':sha(q['prompt'].encode()),'profile':q['profile'],'model':q['model']}
        if baseline.get('status')!='completed' or any(baseline.get(k)!=v for k,v in bindings.items()):
            raise ValueError('Historical result binding mismatch')
        modules['local_vision'].validate_profile(baseline['proposal'],'connectivity_v2')
        check=vc.check_connectivity(baseline,ref,expected_reference_sha256=vc.digest(ref))
        ids=[]
        for profile,prompt in (('connections_v3',trace.CONNECTION_PROMPT),('arrows_v3',trace.ARROW_PROMPT)):
            rid=name+'-'+profile.split('_')[0];ids.append(rid)
            requests.append({'id':rid,'image':name+'.png','sha256':q['sha256'],'model':q['model'],
                             'structured':True,'profile':profile,'prompt':prompt})
        drawings.append({'id':name,'request_ids':ids,'image_sha256':q['sha256'],
            'reference':ref,'reference_sha256':vc.digest(ref),'baseline_sha256':sha(baseline_raw),
            'baseline_job_sha256':sha(oldraw),'baseline_proposal':baseline['proposal'],
            'baseline_check':check,'baseline_seconds':baseline['elapsed_seconds']})
    write(out/'evaluation.json',{'schema':'broadbridge.diagram_tracing_evaluation/1',
        'drawings':drawings,'training_approved':False,
        'scope':'Known development fixtures; not held-out evaluation or engineering acceptance'})
    job={'schema':'broadbridge.diagram_tracing_job/1','requests':requests,'training_approved':False,
         'evaluation_sha256':sha((out/'evaluation.json').read_bytes())}
    write(out/'job.json',job)
    return {'images':len(drawings),'requests':len(requests),'job_sha256':sha((out/'job.json').read_bytes())}


def total(metrics):
    keys=('edge_tp','edge_fp','edge_fn','direction_tp','direction_scored_claims',
          'known_reference_directions','unsupported_direction_claims')
    t={k:sum(row[k] for row in metrics) for k in keys}
    divide=lambda a,b:a/b if b else None
    t.update(edge_precision=divide(t['edge_tp'],t['edge_tp']+t['edge_fp']),
             edge_recall=divide(t['edge_tp'],t['edge_tp']+t['edge_fn']),
             direction_precision=divide(t['direction_tp'],t['direction_scored_claims']),
             direction_recall=divide(t['direction_tp'],t['known_reference_directions']))
    return t


def prepare_crops(out):
    """Operator-selected visible regions, not a general automatic crop detector."""
    from copy import deepcopy
    from PIL import Image
    out.mkdir(parents=True,exist_ok=False)
    requests=[];refs={};lineage={}
    for name,box in CROPS.items():
        root=EVIDENCE/('crossing-correction' if name=='crossing-clear' else 'pilot')
        jobraw=(root/'job.json').read_bytes();job=json.loads(jobraw)
        old=next(q for q in job['requests'] if q['id']==name)
        pixels=(root/old['image']).read_bytes()
        if sha(pixels)!=old['sha256']:raise ValueError('Historical image changed')
        refr=(root/'references.json').read_bytes()
        if sha(refr)!=job['references_sha256']:raise ValueError('Historical reference changed')
        bundle=deepcopy(json.loads(refr)[name]);rid=name+'-crop2x'
        image=Image.open(root/old['image']).convert('RGB')
        x0,y0,x1,y1=box
        if not 0<=x0<x1<=image.width or not 0<=y0<y1<=image.height:raise ValueError('Bad crop box')
        crop=image.crop(box).resize(((x1-x0)*2,(y1-y0)*2),Image.Resampling.NEAREST)
        path=out/(rid+'.png');crop.save(path);imagehash=sha(path.read_bytes())
        ref=bundle['reference']
        if ref['image_sha256']!=old['sha256']:raise ValueError('Reference image mismatch')
        ref['image_sha256']=imagehash
        ref['evidence_id']+='; parent='+old['sha256']+'; crop='+str(box)+'; scale=2 nearest'
        # Other bundle hashes describe the parent projection, so emit only the
        # transformed reference and explicit ancestry; never re-use a stale digest.
        refs[rid]={'reference':ref,'training_approved':False}
        q=deepcopy(old);q.update(id=rid,image=path.name,sha256=imagehash);requests.append(q)
        lineage[rid]={'parent_image_sha256':old['sha256'],'parent_job_sha256':sha(jobraw),
            'parent_prompt':old['prompt'],'box':list(box),'scale':2,'resampling':'nearest',
            'image_sha256':imagehash,'scope':'All named components and pipe routes retained by visual inspection; no retouching or redrawing'}
    # Compatible with the existing frozen v2 reporter.
    raw=(json.dumps(refs,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
    (out/'references.json').write_bytes(raw)
    write(out/'job.json',{'schema':'broadbridge.reference_graph_pilot/1','references_sha256':sha(raw),
        'requests':requests,'training_approved':False})
    write(out/'crop-lineage.json',lineage)
    return {'images':len(refs),'requests':len(requests),'job_sha256':sha((out/'job.json').read_bytes())}


def report_crops(root,results,modules):
    job=json.loads((root/'job.json').read_bytes())
    for q in job['requests']:
        if not re.fullmatch('[a-zA-Z0-9_-]{1,80}',q['id']):raise ValueError('Unsafe result path')
        path=results/(q['id']+'.json')
        if path.exists():
            r=json.loads(path.read_bytes())
            if r.get('model_digest')!=modules['pins'][q['model']]:
                raise ValueError('Pinned model digest mismatch')
    spec=importlib.util.spec_from_file_location('reference_pilot',Path(__file__).with_name('reference_graph_pilot.py'))
    pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)
    return pilot.report(root,results,modules['reference_graphs'])


def report(root,results,modules,*,legacy_evaluation_sha256=None):
    jobraw=(root/'job.json').read_bytes();job=json.loads(jobraw)
    evaluationraw=(root/'evaluation.json').read_bytes();evaluation=json.loads(evaluationraw)
    expected=job.get('evaluation_sha256')
    binding='evaluation digest frozen in job before inference'
    if expected is None:
        # Preserve old run bytes; never imply this later pin was in its model job.
        expected=legacy_evaluation_sha256
        binding='legacy run: external retrospective evaluation pin, not frozen in model job'
        if evaluation.get('job_sha256')!=sha(jobraw):raise ValueError('Frozen job changed')
    if not expected or sha(evaluationraw)!=expected:raise ValueError('Evaluation digest mismatch or missing pin')
    qs={q['id']:q for q in job['requests']};rows=[]
    if len(qs)!=12 or sorted(d['id'] for d in evaluation['drawings'])!=sorted(NAMES):
        raise ValueError('Unexpected experiment size')
    vc,rg,lv=(modules[n] for n in ('visual_connectivity','reference_graphs','local_vision'))
    for d in evaluation['drawings']:
        ref=d['reference']
        if vc.digest(ref)!=d['reference_sha256']:raise ValueError('Reference changed')
        historical=EVIDENCE/('crossing-correction' if d['id']=='crossing-clear' else 'pilot')
        oldbaseline=(historical/'results-qwen'/(d['id']+'.json')).read_bytes()
        oldrefs=json.loads((historical/'references.json').read_bytes())
        baseline=json.loads(oldbaseline)
        if (sha(oldbaseline)!=d['baseline_sha256'] or baseline['proposal']!=d['baseline_proposal']
            or oldrefs[d['id']]['reference']!=ref or baseline['elapsed_seconds']!=d['baseline_seconds']):
            raise ValueError('Evaluation differs from canonical historical evidence')
        records=[];elapsed=0
        for rid in d['request_ids']:
            q=qs[rid]
            if not re.fullmatch('[a-zA-Z0-9_-]{1,80}',rid) or Path(q['image']).name!=q['image']:
                raise ValueError('Unsafe artifact path')
            if sha((root/q['image']).read_bytes())!=q['sha256']:raise ValueError('Image changed')
            p=results/(rid+'.json')
            if not p.exists():records.append(None);continue
            r=json.loads(p.read_bytes())
            bindings={'id':rid,'job_sha256':sha(jobraw),'input_sha256':q['sha256'],
                'prompt_sha256':sha(q['prompt'].encode()),'profile':q['profile'],'model':q['model'],
                'model_digest':modules['pins'][q['model']]}
            if any(r.get(k)!=v for k,v in bindings.items()):raise ValueError('Result binding mismatch')
            elapsed+=r['elapsed_seconds'];records.append(r)
        combined=None;reason=None
        try:
            combined=modules['diagram_tracing'].compose(*records,expected_image_sha256=d['image_sha256'])
        except ValueError as exc:reason=str(exc)
        check=vc.check_connectivity(combined,ref,expected_reference_sha256=d['reference_sha256'])
        actual=[] if combined is None else combined['proposal']['edges']
        row={'id':d['id'],'elapsed_seconds':round(elapsed,3),'check':check,'composition_error':reason,
             'composed':combined,'metrics':rg.connectivity_metrics(ref['edges'],actual),
             'baseline_metrics':rg.connectivity_metrics(ref['edges'],d['baseline_proposal']['edges']),
             'baseline_check':d['baseline_check']['status'],'baseline_seconds':d['baseline_seconds']}
        rows.append(row)
    return {'schema':'broadbridge.diagram_tracing_results/1','job_sha256':sha(jobraw),
        'evaluation_sha256':expected,'evaluation_binding':binding,
        'rows':rows,'totals':total([r['metrics'] for r in rows]),
        'baseline_totals':total([r['baseline_metrics'] for r in rows]),'training_approved':False,
        'limitation':'Same development fixtures. Passing exact graph checks is not engineering sign-off. No reference graph was sent to either model call.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','report','prepare-crops','report-crops'));p.add_argument('--foundry',required=True,type=Path)
    p.add_argument('--work',required=True,type=Path);p.add_argument('--results',type=Path)
    p.add_argument('--legacy-evaluation-sha256',help='Explicit retrospective pin for the preserved first run only')
    p.add_argument('--report-name',default='report.json')
    a=p.parse_args(argv);modules=load(a.foundry)
    if a.action=='prepare':r=prepare(a.work,modules)
    elif a.action=='prepare-crops':r=prepare_crops(a.work)
    else:
        if a.results is None:p.error('report requires --results')
        if not re.fullmatch('[a-zA-Z0-9_-]+[.]json',a.report_name):p.error('report-name must be a JSON basename')
        if a.action=='report-crops':
            r=report_crops(a.work,a.results,modules)
        else:r=report(a.work,a.results,modules,legacy_evaluation_sha256=a.legacy_evaluation_sha256)
        write(a.work/a.report_name,r)
    print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
