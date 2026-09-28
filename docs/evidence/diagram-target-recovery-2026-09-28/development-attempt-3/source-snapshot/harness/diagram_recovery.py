"""CPU development/regression execution with immutable receipts. Never qualifies.

The reference is loaded only after the detector output is written. All runs,
including extraction failures and evidence rejections, remain in denominators.
"""
import argparse
import hashlib
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import sys
import time


def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def sha(raw): return hashlib.sha256(raw).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')


def score(reference,result,category):
    metrics=module('deterministic_diagrams').metrics
    rules=result.get('rules');accepted=rules is not None and rules['status']=='pass'
    cls={'dense-crossings':'crossing','unexplained-break':'break'}.get(category,category)
    return {'raw':metrics(reference,result['edges'],cls),
            'accepted':metrics(reference,result['edges'] if accepted else [],cls),
            'checker_rejected':int(rules is not None and not accepted),
            'extraction_failed':int(result.get('status')=='failed')}


def aggregate(rows,field='raw'):
    from src.ingestion.diagram_metrics import summarize
    total=lambda k:sum(row[field][k] for row in rows)
    result=summarize(tp=total('edge_tp'),fp=total('edge_fp'),fn=total('edge_fn'),
        direction_claims=total('direction_claims'),directions_correct=total('direction_correct'),
        reference_directions=total('known_directions'),directions_reversed=total('direction_reversals'),
        unsupported_directions=total('unsupported_directions'),
        evidence_violations=sum(row.get('evidence_violations',0) for row in rows) if field=='raw' else 0,
        checker_rejections=sum(row['checker_rejected'] for row in rows))
    emitted=total('edge_tp')+total('edge_fp');violations=result['counts']['evidence_violations']
    result.update(drawings=len(rows),qualified=False,gate_eligible=False,
        false_edges_in_crossing_categories=total('false_edges_at_crossings'),
        unknown_directions=total('known_direction_unknown'),missed_directed_edges=total('known_direction_missing'),
        extraction_failed=sum(row['extraction_failed'] for row in rows),
        evidence_completeness={'successes':emitted-violations,'denominator':emitted,'estimate':(emitted-violations)/emitted if emitted else None},
        visible_arrow_recovery={'status':'pending_source_only_eligibility_review','estimate':None},
        port_tag_detection={'status':'unmeasured_supplied_ports','f1':None,'attachment_precision':None,'attachment_recall':None})
    return result


def run(root,out,foundry,kind,attempt=1):
    if type(attempt) is not int or not 1<=attempt<=3: raise ValueError('At most three documented configurations')
    root,out,foundry=Path(root),Path(out),Path(foundry)
    import cv2
    old=module('deterministic_diagrams');_,extractor,builder,_=old.foundry(foundry)
    from src.ingestion.geometry_contract import check_edges
    if kind=='development':
        manifest=module('diagram_fixture_suite').verify_suite(root)
    elif kind=='regression':
        _,manifest=old.verify(root)
    else:raise ValueError('Only development and pinned regression are authorized')
    if any(row.get('split','regression') not in ('development','regression') for row in manifest['drawings']):
        raise ValueError('Cannot run an untouched reserve with the development command')
    out.mkdir(parents=True,exist_ok=False)
    engine_files=['src/ingestion/'+name+'.py' for name in ('geometry_contract','geometry_extractors','diagram_geometry','raster_connectivity','diagram_metrics')]
    snapshots={name:(foundry/name).read_bytes() for name in engine_files}
    snapshots['harness/diagram_recovery.py']=Path(__file__).read_bytes()
    snapshots['harness/deterministic_diagrams.py']=Path(old.__file__).read_bytes()
    snapshots['harness/diagram_fixture_suite.py']=Path(__file__).with_name('diagram_fixture_suite.py').read_bytes()
    for name,raw in snapshots.items():
        target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    receipt={'schema':'broadbridge.diagram_recovery_run/1','input_manifest_sha256':sha((root/'manifest.json').read_bytes()),
        'engine_sources':{name:sha((foundry/name).read_bytes()) for name in engine_files},
        'harness_sha256':sha(Path(__file__).read_bytes()),
        'legacy_metrics_sha256':sha(Path(old.__file__).read_bytes()),
        'source_snapshot':{name:sha(raw) for name,raw in snapshots.items()},
        'versions':{'opencv':cv2.__version__,**{name:importlib.metadata.version(name) for name in ('PyMuPDF','ezdxf','scikit-image','numpy')}},
        'evaluation_role':kind,'provenance':'pre-run-checksum','training_approved':False,
        'config_id':'independent-raster-v'+str(attempt),'attempt':attempt,'model_calls':0,
        'notes':'Masks and ports supplied. Same construction family; no independent qualification.'}
    write(out/'run.json',receipt); run_hash=sha((out/'run.json').read_bytes()); rows=[]
    for item in manifest['drawings']:
        name=item['id'];ports=json.loads((root/(name+'.ports.json')).read_bytes())
        spec=json.loads((root/(name+'.model.json')).read_bytes())['spec']
        for ext in ('pdf','dxf','png'):
            start=time.perf_counter()
            try:
                detection=extractor.extract(root/(name+'.'+ext),masks=ports['text_masks'])
                result=builder.build_graph(detection,ports['ports']);result['status']='completed'
            except Exception as exc:
                result={'status':'failed','error':str(exc),'edges':[],'training_approved':False}
            result.update(input_sha256=sha((root/(name+'.'+ext)).read_bytes()),run_sha256=run_hash)
            write(out/(name+'.'+ext+'.json'),result)
            # Scoring boundary: never provide reference edges to extraction.
            if kind=='development':reference=json.loads((root/(name+'.reference.json')).read_bytes())['edges']
            else:reference=json.loads((root/'references.json').read_bytes())[name]['edges']
            category=item.get('case',item.get('category'))
            row={'id':name,'route':ext,'family_id':'original-simple-line-generator','category':category,
                'elapsed_seconds':round(time.perf_counter()-start,4),**score(reference,result,category),
                'evidence_violations':sum(check_edges([e],result['detection'])['status']!='pass' for e in result['edges']),
                'buckets':{'angle_degrees':spec.get('angle','unrecorded'),'arrow_length':spec.get('arrow_length','unrecorded'),
                    'scan_dpi':72 if ext=='png' else 'not_applicable','scan_noise':'none' if ext=='png' else 'not_applicable',
                    'intersection':category}}
            rows.append(row)
    routes={}
    for route in ('pdf','dxf','png'):
        selected=[row for row in rows if row['route']==route]
        buckets={}
        for dimension in ('angle_degrees','arrow_length','scan_dpi','scan_noise','intersection'):
            values=sorted({str(row['buckets'][dimension]) for row in selected})
            buckets[dimension]={value:aggregate([row for row in selected if str(row['buckets'][dimension])==value]) for value in values}
        routes[route]={'raw':aggregate(selected),'accepted':aggregate(selected,'accepted'),
            'per_drawing':{row['id']:aggregate([row]) for row in selected},
            'per_family':{'original-simple-line-generator':aggregate(selected)},'buckets':buckets}
    report={'schema':'broadbridge.diagram_recovery_report/1','run_sha256':run_hash,'rows':rows,'routes':routes,
        'training_approved':False,'qualified':False,
        'blocking_gates':['independent_families','source_only_visibility_and_reference_review',
            'convention_acceptance','cluster_aware_uncertainty','end_to_end_port_measurements',
            'authenticated_technical_acceptance','rights','complete_crop_lineage','release_approval'],
        'miss_groups_needing_regression':sorted({r['category'] for r in rows if r['raw']['edge_fn']>1}),
        'critical_error_note':'Crossing-category flags are not localized intersection diagnoses; errors may overlap.'}
    write(out/'report.json',report)
    write(out/'checksums.json',{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()})
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','out','foundry'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--kind',choices=['development','regression'],required=True)
    p.add_argument('--attempt',type=int,choices=(1,2,3),default=1);a=p.parse_args()
    r=run(a.root,a.out,a.foundry,a.kind,a.attempt)
    print(json.dumps({route:value['raw']['counts'] for route,value in r['routes'].items()},indent=2))


if __name__=='__main__':main()
