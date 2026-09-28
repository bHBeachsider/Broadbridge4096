"""Deterministic diagram evidence rules. A valid graph is not training approval.

The convention is a declared project policy, not a universal ISA certification.
Legacy vision records can be compared historically but cannot satisfy this contract.
"""
from math import dist, isfinite
from jsonschema import Draft202012Validator

CONVENTION = 'no_dot_crossing_nonconnecting/1'
POINT = {'type':'array','minItems':2,'maxItems':2,'items':{'type':'number'}}
IDS = {'type':'array','minItems':1,'maxItems':1000,'uniqueItems':True,
       'items':{'type':'string','minLength':1}}
EVIDENCE = {'type':'object','additionalProperties':False,
    'required':['kind','point','segment_ids'],'properties':{
        'kind':{'enum':['tee','junction_dot','shared_endpoint']},'point':POINT,'segment_ids':IDS}}
EDGE_SCHEMA = {'$schema':'https://json-schema.org/draft/2020-12/schema',
    'type':'object','additionalProperties':False,
    'required':['a','b','direction','arrow_id','segment_ids','path','connection_evidence','convention'],
    'properties':{
        'a':{'type':'string','minLength':1},'b':{'type':'string','minLength':1},
        'direction':{'enum':['unknown','a_to_b','b_to_a']},
        'arrow_id':{'type':['string','null']},'segment_ids':IDS,
        'path':{'type':'array','minItems':2,'maxItems':2000,'items':POINT},
        'connection_evidence':{'type':'array','minItems':1,'maxItems':1000,'items':EVIDENCE},
        'convention':{'const':CONVENTION}},
    'allOf':[{'if':{'properties':{'direction':{'const':'unknown'}}},
              'then':{'properties':{'arrow_id':{'type':'null'}}},
              'else':{'properties':{'arrow_id':{'type':'string','minLength':1}}}}]}


def point(p):
    if not isinstance(p,(list,tuple)) or len(p)!=2 or any(type(v) not in (int,float) or not isfinite(v) for v in p):
        raise ValueError('Invalid finite point')
    return p


def projection(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];n=dx*dx+dy*dy
    if not n:return 0,dist(p,a)
    t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/n
    q=[a[0]+max(0,min(1,t))*dx,a[1]+max(0,min(1,t))*dy]
    return t,dist(p,q)


def indexed(items):
    values={v['id']:v for v in items}
    if len(values)!=len(items):raise ValueError('Duplicate detection IDs')
    return values


def validate_detection(d):
    if d['schema']!='foundry.diagram_detection/1' or d['route'] not in ('vector_pdf','vector_dxf','raster'):
        raise ValueError('Invalid detection route')
    t=d['tolerance']
    if type(t) not in (int,float) or not isfinite(t) or not 0<t<=10:raise ValueError('Invalid tolerance')
    segments=indexed(d['segments']);arrows=indexed(d['arrows'])
    for s in segments.values():
        if dist(point(s['start']),point(s['end']))==0:raise ValueError('Zero-length segment')
    for r in arrows.values():
        if dist(point(r['base']),point(r['tip']))==0:raise ValueError('Zero-length arrow')
        if r['segment_id'] is not None and r['segment_id'] not in segments:raise ValueError('Unknown arrow segment')
    return segments,arrows


def check_edges(edges,detection):
    result={'schema':'foundry.geometry_rules_check/1','status':'fail','training_approved':False}
    try:
        segments,arrows=validate_detection(detection);t=detection['tolerance'];seen=set()
        if not isinstance(edges,list) or len(edges)>1000:raise ValueError('Invalid edge count')
        for e in edges:
            errors=list(Draft202012Validator(EDGE_SCHEMA).iter_errors(e))
            if errors:raise ValueError('Edge evidence schema: '+errors[0].message)
            pair=tuple(sorted((e['a'],e['b'])))
            if e['a']==e['b'] or pair in seen:raise ValueError('Self or duplicate edge')
            seen.add(pair)
            if any(s not in segments for s in e['segment_ids']):raise ValueError('Unknown path segment')
            for p in e['path']:point(p)
            used=[]
            for a,b in zip(e['path'],e['path'][1:]):
                if dist(a,b)<1e-6:raise ValueError('Zero path span')
                matches=[sid for sid in e['segment_ids'] if max(projection(p,segments[sid]['start'],segments[sid]['end'])[1] for p in (a,b))<=t]
                if not matches:raise ValueError('Path span lacks detected line')
                used.append(matches[0])
            for i,(left,right) in enumerate(zip(used,used[1:])):
                if left==right:continue
                p=e['path'][i+1]
                junction=any(dist(j['point'],p)<=t and {left,right}<=set(j['segment_ids']) for j in detection['junctions'])
                shared=all(min(dist(p,segments[s][k]) for k in ('start','end'))<=t for s in (left,right))
                excluded=any(dist(x['point'],p)<=t for x in detection['excluded_intersections'])
                if excluded:
                    a,b=e['path'][i],e['path'][i+2]
                    u=[p[k]-a[k] for k in (0,1)];v=[b[k]-p[k] for k in (0,1)]
                    straight=abs(u[0]*v[1]-u[1]*v[0])<=.25*dist(a,p)*dist(p,b)
                    samecurve=segments[left].get('primitive')=='curve' and segments[right].get('primitive')=='curve' and segments[left].get('source')==segments[right].get('source')
                    if not straight and not samecurve:raise ValueError('Path turns at non-connecting crossing')
                if not junction and not shared:raise ValueError('Path join lacks tee, dot or shared endpoint')
            for ev in e['connection_evidence']:
                if any(s not in e['segment_ids'] for s in ev['segment_ids']):raise ValueError('Evidence outside path')
                if ev['kind']=='shared_endpoint':
                    if not all(min(dist(ev['point'],segments[s][end]) for end in ('start','end'))<=t for s in ev['segment_ids']):
                        raise ValueError('No shared endpoint at claimed location')
                elif not any(j['kind']==ev['kind'] and dist(j['point'],ev['point'])<=t
                             and set(ev['segment_ids'])<=set(j['segment_ids']) for j in detection['junctions']):
                    raise ValueError('No detected junction evidence')
            if e['direction']!='unknown':
                r=arrows.get(e['arrow_id'])
                if not r or r['segment_id'] not in e['segment_ids']:raise ValueError('Direction requires attached detected arrow')
                s=segments[r['segment_id']]
                if any(projection(r[k],s['start'],s['end'])[1]>t for k in ('base','tip')):
                    raise ValueError('Arrow outside line tolerance')
                # Local tangent in the a-to-b path, not left-to-right page order.
                paths=list(zip(e['path'],e['path'][1:]))
                a,b=min(paths,key=lambda pair:projection(r['tip'],*pair)[1])
                if projection(r['tip'],a,b)[1]>t:raise ValueError('Arrow absent from path')
                dot=(b[0]-a[0])*(r['tip'][0]-r['base'][0])+(b[1]-a[1])*(r['tip'][1]-r['base'][1])
                expected='a_to_b' if dot>0 else 'b_to_a' if dot<0 else 'unknown'
                if e['direction']!=expected:raise ValueError('Direction contradicts detected tip/base')
        return {**result,'status':'pass','reason':'Evidence rules satisfied; independent graph review still required'}
    except (ValueError,KeyError,TypeError,IndexError) as exc:
        return {**result,'reason':str(exc)}


def gate_blockers(manifest):
    blockers=[]
    if manifest.get('provenance')!='pre-run-checksum':blockers.append('provenance_not_pre_run')
    if manifest.get('crop_history_pinned') is not True:blockers.append('crop_history_metadata_unpinned')
    # Future integrations must also supply affirmative, independent acceptances.
    for key in ('rights_approved','technical_approved','reference_independently_verified',
                'heldout_metrics_accepted','release_approved'):
        if manifest.get(key) is not True:blockers.append(key)
    return blockers
