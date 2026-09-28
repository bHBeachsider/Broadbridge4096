"""Frozen original DEXPI stress data and offline deterministic comparison.

Only baseline replay uses the separately invoked installed local CPU model.
Neither detector receives reference edges. Supplied ports isolate connectivity
from OCR; this is development evaluation, not engineering/training acceptance.
"""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
import importlib.metadata
from math import hypot
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,obj):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')


def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def specs():
    chain=[(100,200),(500,200)]
    tee=[(100,200),(300,200),(500,200),(300,80)]
    cross=[(100,200),(500,200),(300,70),(300,330)]
    dense=[(80,140),(520,140),(80,260),(520,260),(220,60),(220,340),(380,60),(380,340)]
    definitions=[
      ('forward','forward',chain,[(0,1,'a_to_b')],[]),
      ('reverse','reverse',chain,[(0,1,'b_to_a')],[]),
      ('no-arrow','no_arrow',chain,[(0,1,'unknown')],[]),
      ('dense-crossings','crossing',dense,[(0,1,'unknown'),(2,3,'unknown'),(4,5,'unknown'),(6,7,'unknown')],[]),
      ('hop','hop',cross,[(0,1,'unknown'),(2,3,'unknown')],[]),
      ('tee','tee',tee,[(0,1,'a_to_b'),(1,2,'unknown'),(1,3,'unknown')],[]),
      ('tee-dot','tee',tee,[(0,1,'b_to_a'),(1,2,'unknown'),(1,3,'unknown')],[1]),
      ('cross-dot','junction',cross+[(300,200)],[(0,4,'unknown'),(4,1,'unknown'),(2,4,'unknown'),(4,3,'unknown')],[4]),
      ('rotated-forward','rotated',[(100,300),(500,100)],[(0,1,'a_to_b')],[]),
      ('rotated-reverse','rotated',[(100,100),(500,300)],[(0,1,'b_to_a')],[]),
      ('small-arrow','small_arrow',chain,[(0,1,'b_to_a')],[]),
      ('break-crossing','break',cross,[(0,1,'unknown'),(2,3,'unknown')],[]),
    ]
    result=[]
    for i,(name,cat,xy,edges,dots) in enumerate(definitions):
        seed=2100+i;junctions={1} if cat=='tee' else {4} if name=='cross-dot' else set()
        tags=[('J-' if k in junctions else 'V-')+str(seed*10+k) for k in range(len(xy))]
        result.append({'id':name,'category':cat,'seed':seed,'positions':xy,'tags':tags,
            'edges':edges,'dots':dots,'training_approved':False,'family_id':'geometry-stress-'+str(seed)})
    return result


def historical_disposition():
    return {'schema':'broadbridge.diagram_experiment_disposition/1',
        'experiment':'diagram-repair-2026-09-27','provenance':'retrospective-checksum',
        'gate_eligible':False,'training_approved':False,
        'reason':'Original evaluation pin was recorded after inference; historical development diagnosis only.',
        'required_before_unblocking':['crop-history metadata pinned','pre-run freeze verified',
             'source rights cleared','independent technical acceptance','new held-out geometry evaluation',
             'real drawing/OCR and conventions validated','release approved']}


def render(s,pdf,dxf):
    import pymupdf,ezdxf
    doc=pymupdf.open();page=doc.new_page(width=600,height=400)
    cad=ezdxf.new();msp=cad.modelspace();masks=[]
    for n,(i,j,direction) in enumerate(s['edges']):
        a,b=s['positions'][i],s['positions'][j]
        if s['id']=='hop' and n==0:
            page.draw_line(a,(280,200),width=2);page.draw_bezier((280,200),(280,170),(320,170),(320,200),width=2);page.draw_line((320,200),b,width=2)
            msp.add_line(a,(280,200));msp.add_open_spline(control_points=[(280,200),(280,170),(320,170),(320,200)],degree=3);msp.add_line((320,200),b)
        elif s['id']=='break-crossing' and n==0:
            page.draw_line(a,(289,200),width=2);page.draw_line((311,200),b,width=2)
            msp.add_line(a,(289,200));msp.add_line((311,200),b)
        else:page.draw_line(a,b,width=2);msp.add_line(a,b)
        if direction!='unknown':
            tail,head=(a,b) if direction=='a_to_b' else (b,a)
            dx,dy=head[0]-tail[0],head[1]-tail[1];length=hypot(dx,dy);u,v=dx/length,dy/length
            tip=(tail[0]+dx*.55,tail[1]+dy*.55)
            h,w=(5,3) if s['id']=='small-arrow' else (18,12)
            base=(tip[0]-h*u,tip[1]-h*v)
            pts=[tip,(base[0]+w/2*v,base[1]-w/2*u),(base[0]-w/2*v,base[1]+w/2*u)]
            shape=page.new_shape();shape.draw_polyline(pts+[pts[0]]);shape.finish(fill=(0,0,0),color=(0,0,0));shape.commit()
            msp.add_solid(pts)
    for index in s['dots']:
        xy=s['positions'][index];page.draw_circle(xy,5,fill=(0,0,0),color=(0,0,0))
        hatch=msp.add_hatch(color=7);p=hatch.paths.add_edge_path();p.add_arc(xy,5,0,360)
    for tag,(x,y) in zip(s['tags'],s['positions']):
        tx,ty=x+9,y+18
        page.insert_text((tx,ty),tag,fontsize=11);msp.add_text(tag,dxfattribs={'height':11,'insert':(tx,ty)})
        masks.append([tx-1,ty-12,tx+len(tag)*7,ty+3])
    doc.save(pdf,no_new_id=True);page.get_pixmap(alpha=False).save(pdf.with_suffix('.png'));doc.close()
    cad.saveas(dxf);return masks


def foundry(path):
    if not path.is_absolute():raise ValueError('Absolute Foundry checkout required')
    sys.path.insert(0,str(path))
    from src.ingestion import reference_graphs as rg,geometry_extractors as ge,diagram_geometry as dg,local_vision as lv
    for m in (rg,ge,dg,lv):
        if not Path(m.__file__).resolve().is_relative_to(path.resolve()):raise ValueError('Wrong Foundry module')
    return rg,ge,dg,lv


def prepare(out,repo):
    rg,_,_,_=foundry(repo);pilot=module('reference_graph_pilot')
    out.mkdir(parents=True,exist_ok=False);references={};rows=[];requests=[]
    old=ROOT/'docs/evidence/reference-graphs-2026-09-27/pilot/job.json'
    original=json.loads(old.read_bytes())['requests'][0]
    for s in specs():
        name=s['id'];model=pilot.build_model(s);snap=rg.serialize_dexpi(model)
        source=json.dumps({'spec':s,'model':snap},sort_keys=True).encode()
        g=rg.topology_from_dexpi(model,source_sha256=sha(source));g['origin']='synthetic-by-construction'
        for edge in g['edges']:
            i=int(edge['id'][1:]);a,b,direction=s['edges'][i]
            assert (edge['a'],edge['b'])==(s['tags'][a],s['tags'][b])
            edge.update(direction=direction,direction_basis='construction seed '+str(s['seed']))
        write(out/(name+'.model.json'),{'spec':s,'snapshot':snap,'topology':g})
        masks=render(s,out/(name+'.pdf'),out/(name+'.dxf'))
        ports=dict(zip(s['tags'],s['positions']));write(out/(name+'.ports.json'),{'ports':ports,'text_masks':masks,
            'origin':'supplied label/port annotations only; no connectivity','training_approved':False})
        imagehash=sha((out/(name+'.png')).read_bytes());ref=rg.project_reference(g,image_sha256=imagehash)['reference']
        references[name]=ref
        rows.append({'id':name,'category':s['category'],'family_id':s['family_id'],'seed':s['seed']})
        requests.append({**original,'id':name,'image':name+'.png','sha256':imagehash})
    write(out/'references.json',references)
    assets={p.name:sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
    manifest={'schema':'broadbridge.geometry_stress_manifest/1','provenance':'pre-run-checksum',
        'drawings':rows,'assets':assets,'training_approved':False,'gate_eligible':False,
        'crop_history_pinned':False,'limitations':['No cropping in this set; system-wide crop-history gate still deferred',
        'Supplied ports isolate connectivity from OCR','Synthetic development set, no expert sign-off'],
        'detector_config':{'pdf_tolerance':2,'dxf_tolerance':2,'raster_tolerance':3,
          'raster_threshold':128,'opening':5,'skeleton':'zhang','hough_threshold':15,'minimum_line':16,'gap':2},
        'baseline_model_pins':json.loads((repo/'infra/vision/models.json').read_bytes())}
    write(out/'manifest.json',manifest)
    write(out/'job.json',{'schema':'broadbridge.geometry_stress_job/1','manifest_sha256':sha((out/'manifest.json').read_bytes()),
        'requests':requests,'training_approved':False})
    return {'drawings':12,'baseline_requests':12,'manifest_sha256':sha((out/'manifest.json').read_bytes()),'job_sha256':sha((out/'job.json').read_bytes())}


def verify(root):
    raw=(root/'job.json').read_bytes();job=json.loads(raw);mraw=(root/'manifest.json').read_bytes()
    if sha(mraw)!=job['manifest_sha256']:raise ValueError('Manifest changed after freeze')
    m=json.loads(mraw)
    for name,value in m['assets'].items():
        if Path(name).name!=name or sha((root/name).read_bytes())!=value:raise ValueError('Frozen asset changed: '+name)
    return job,m


def run(root,out,repo):
    _,ge,dg,_=foundry(repo);job,m=verify(root);out.mkdir(parents=True,exist_ok=False)
    sources={name:sha((repo/name).read_bytes()) for name in ('src/ingestion/geometry_contract.py',
        'src/ingestion/diagram_geometry.py','src/ingestion/geometry_extractors.py')}
    receipt={'manifest_sha256':job['manifest_sha256'],'engine_sources':sources,
        'config':m['detector_config'],'training_approved':False,
        'versions':{name:importlib.metadata.version(name) for name in ('PyMuPDF','ezdxf','scikit-image','numpy')},
        'provenance':'pre-run-checksum','gate_eligible':False}
    write(out/'run.json',receipt);outputs={}
    rows=[]
    for item in m['drawings']:
        name=item['id'];p=json.loads((root/(name+'.ports.json')).read_bytes())
        for ext in ('pdf','dxf','png'):
            try:
                detection=ge.extract(root/(name+'.'+ext),masks=p['text_masks'])
                result=dg.build_graph(detection,p['ports']);result['status']='completed'
            except Exception as exc:result={'status':'failed','error':str(exc),'edges':[],'training_approved':False}
            result.update(id=name,input_format=ext,manifest_sha256=job['manifest_sha256'])
            result['input_sha256']=m['assets'][name+'.'+ext]
            result['run_sha256']=sha((out/'run.json').read_bytes())
            fname=name+'.'+ext+'.json';write(out/fname,result);outputs[fname]=sha((out/fname).read_bytes())
            rows.append({'id':name,'format':ext,'status':result['status'],'route':result.get('route')})
    write(out/'routes.json',rows);write(out/'outputs.json',{'files':outputs,'run_sha256':sha((out/'run.json').read_bytes())});return rows


def edges_map(edges):
    result={}
    for e in edges:
        a,b=e['a'],e['b'];direction=e['direction']
        if a>b:a,b=b,a;direction={'a_to_b':'b_to_a','b_to_a':'a_to_b','unknown':'unknown'}[direction]
        if (a,b) in result:raise ValueError('Duplicate evaluated edge')
        result[(a,b)]=direction
    return result


def metrics(reference,actual,category):
    r,a=edges_map(reference),edges_map(actual);correct=r.keys()&a.keys()
    return {'edge_tp':len(correct),'edge_fp':len(a.keys()-r.keys()),'edge_fn':len(r.keys()-a.keys()),
        'false_edges_at_crossings':len(a.keys()-r.keys()) if category in ('crossing','hop','break') else 0,
        'known_directions':sum(v!='unknown' for v in r.values()),
        'direction_claims':sum(v!='unknown' for v in a.values()),
        'direction_correct':sum(r[k]!='unknown' and a[k]==r[k] for k in correct),
        'known_direction_claims':sum(r[k]!='unknown' and a[k]!='unknown' for k in correct),
        'known_direction_unknown':sum(r[k]!='unknown' and a[k]=='unknown' for k in correct),
        'known_direction_missing':sum(r[k]!='unknown' for k in r.keys()-a.keys()),
        'direction_reversals':sum(r[k]!='unknown' and a[k]!='unknown' and a[k]!=r[k] for k in correct),
        'unsupported_directions':sum(v!='unknown' and r.get(k,'unknown')=='unknown' for k,v in a.items())}


def evidence_metrics(edges,detection):
    claims=[e for e in edges if e['direction']!='unknown']
    if detection is None:unsupported=len(claims)
    else:
        from src.ingestion.geometry_contract import check_edges
        unsupported=sum(check_edges([e],detection)['status']!='pass' for e in claims)
    return {'direction_claims':len(claims),'unbacked_directions':unsupported,
        'unbacked_direction_rate':unsupported/len(claims) if claims else None}


def score_prediction(reference,actual,category,rules):
    # Quality is measured before rejection, so safety gates cannot hide errors.
    return {'metrics':metrics(reference,actual,category),
        'accepted_metrics':metrics(reference,actual if rules and rules['status']=='pass' else [],category)}


def aggregate(rows):
    keys=('edge_tp','edge_fp','edge_fn','false_edges_at_crossings','known_directions','direction_claims',
          'direction_correct','known_direction_claims','known_direction_unknown','known_direction_missing','direction_reversals','unsupported_directions')
    t={k:sum(r['metrics'][k] for r in rows) for k in keys}
    ratio=lambda a,b:a/b if b else None
    t.update(edge_precision=ratio(t['edge_tp'],t['edge_tp']+t['edge_fp']),edge_recall=ratio(t['edge_tp'],t['edge_tp']+t['edge_fn']),
        direction_reversal_rate=ratio(t['direction_reversals'],t['known_directions']),
        supported_direction_recall=ratio(t['direction_correct'],t['known_directions']),
        known_direction_coverage=ratio(t['known_direction_claims'],t['known_directions']),
        direction_accuracy_when_claimed=ratio(t['direction_correct'],t['known_direction_claims']),
        unsupported_direction_rate=ratio(t['unsupported_directions'],t['direction_claims']))
    return t


def report(root,detected,baseline,repo):
    _,_,_,lv=foundry(repo);job,m=verify(root);rows=[]
    from src.ingestion.geometry_contract import check_edges,gate_blockers
    from src.ingestion.visual_connectivity import digest
    refs=json.loads((root/'references.json').read_bytes());receipts=json.loads((detected/'outputs.json').read_bytes())
    runraw=(detected/'run.json').read_bytes();run=json.loads(runraw)
    if receipts['run_sha256']!=sha(runraw) or run['manifest_sha256']!=job['manifest_sha256']:raise ValueError('Detector run binding mismatch')
    requests={q['id']:q for q in job['requests']}
    for item in m['drawings']:
        name=item['id'];ref=refs[name]['edges'];category=item['category']
        for route in ('pdf','dxf','png','baseline'):
            status='not_run';actual=[];rules=None;d=None
            if route=='baseline':
                path=baseline/(name+'.json')
                if path.exists():
                    r=json.loads(path.read_bytes());q=requests[name]
                    binds={'id':name,'job_sha256':sha((root/'job.json').read_bytes()),'input_sha256':q['sha256'],
                           'model':q['model'],'model_digest':m['baseline_model_pins'][q['model']],
                           'prompt_sha256':sha(q['prompt'].encode()),'profile':q['profile']}
                    if any(r.get(k)!=v for k,v in binds.items()):raise ValueError('Baseline binding mismatch')
                    status=r['status']
                    if status=='completed':
                        try:lv.validate_profile(r['proposal'],'connectivity_v2');actual=r['proposal']['edges']
                        except (ValueError,KeyError,TypeError):status='invalid'
            else:
                fname=name+'.'+route+'.json';path=detected/fname
                if path.exists():
                    raw=path.read_bytes()
                    if receipts['files'].get(fname)!=sha(raw):raise ValueError('Detector output changed')
                    r=json.loads(raw)
                    if (r['id']!=name or r['input_format']!=route or r['input_sha256']!=m['assets'][name+'.'+route]
                        or r['manifest_sha256']!=job['manifest_sha256'] or r['run_sha256']!=sha(runraw)):
                        raise ValueError('Detector binding mismatch')
                    status=r['status']
                    if status=='completed':
                        d=r['detection'];ports=json.loads((root/(name+'.ports.json')).read_bytes())['ports']
                        if digest(d)!=r['detection_sha256'] or digest(ports)!=r['ports_sha256'] or d['input_sha256']!=r['input_sha256']:
                            raise ValueError('Detector evidence mismatch')
                        rules=check_edges(r['edges'],d)
                        actual=r['edges']
                        if rules['status']!='pass':status='invalid_evidence'
            rows.append({'id':name,'category':category,'route':route,'status':status,'rules':rules,
                'arrow_evidence':evidence_metrics(actual,d),**score_prediction(ref,actual,category,rules)})
    summary={route:aggregate([r for r in rows if r['route']==route]) for route in ('pdf','dxf','png','baseline')}
    by_category={route:{cat:aggregate([r for r in rows if r['route']==route and r['category']==cat])
        for cat in sorted({x['category'] for x in rows})} for route in summary}
    return {'schema':'broadbridge.geometry_stress_results/1','manifest_sha256':job['manifest_sha256'],
        'rows':rows,'summary':summary,'by_category':by_category,
        'arrow_evidence_summary':{route:{'direction_claims':sum(r['arrow_evidence']['direction_claims'] for r in rows if r['route']==route),
            'unbacked_directions':sum(r['arrow_evidence']['unbacked_directions'] for r in rows if r['route']==route)} for route in summary},
        'accepted_summary':{route:aggregate([{'metrics':r['accepted_metrics']} for r in rows if r['route']==route]) for route in ('pdf','dxf','png')},'provenance':'pre-run-checksum',
        'training_approved':False,'gate_eligible':False,'blocking_gates':gate_blockers(m),
        'limitations':m['limitations'],
        'metric_definitions':{'reversal_rate':'reversed matched edges / all known reference directions',
            'unsupported_rate':'claims absent from directed reference / all direction claims',
            'zero_denominator':'null, not zero','invalid_or_missing':'malformed/missing predictions count as empty; evidence-rejected geometry remains in raw quality metrics',
            'accepted_summary':'only geometry whose evidence checker passes; not training approval',
            'baseline_evidence':'image-only baseline has no detected arrow IDs; it is never accepted by the new evidence contract'}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run','report'])
    p.add_argument('--foundry',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path)
    p.add_argument('--detected',type=Path);p.add_argument('--baseline',type=Path)
    a=p.parse_args()
    if a.action=='prepare':r=prepare(a.work,a.foundry)
    elif a.action=='run':
        if a.out is None:p.error('run requires --out')
        r=run(a.work,a.out,a.foundry)
    else:
        if None in (a.out,a.detected,a.baseline):p.error('report requires --out, --detected and --baseline')
        r=report(a.work,a.detected,a.baseline,a.foundry);write(a.out,r)
    print(json.dumps(r.get('summary',r) if isinstance(r,dict) else r,indent=2))


if __name__=='__main__':main()
