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
    rows=[]
    for item in m['drawings']:
        name=item['id'];p=json.loads((root/(name+'.ports.json')).read_bytes())
        for ext in ('pdf','dxf','png'):
            try:
                detection=ge.extract(root/(name+'.'+ext),masks=p['text_masks'])
                result=dg.build_graph(detection,p['ports']);result['status']='completed'
            except Exception as exc:result={'status':'failed','error':str(exc),'edges':[],'training_approved':False}
            result.update(id=name,input_format=ext,manifest_sha256=job['manifest_sha256'])
            write(out/(name+'.'+ext+'.json'),result);rows.append({'id':name,'format':ext,'status':result['status'],'route':result.get('route')})
    write(out/'routes.json',rows);return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run'])
    p.add_argument('--foundry',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.action=='prepare':r=prepare(a.work,a.foundry)
    else:
        if a.out is None:p.error('run requires --out')
        r=run(a.work,a.out,a.foundry)
    print(json.dumps(r,indent=2))


if __name__=='__main__':main()
