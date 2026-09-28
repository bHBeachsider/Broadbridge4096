"""Small, deterministic line graph builder. No vision model, OCR or gold graph.

Port anchors identify labels/locations only. They are a separate measured input,
not an edge list. Missing/ambiguous anchors and incomplete curves remain warnings.
"""
from collections import defaultdict, deque
from copy import deepcopy
from math import dist, hypot
from .geometry_contract import CONVENTION, check_edges, point, projection, validate_detection
from .visual_connectivity import digest


def intersect(a,b,c,d,tolerance):
    x,y=b[0]-a[0],b[1]-a[1];u,v=d[0]-c[0],d[1]-c[1]
    den=x*v-y*u
    if abs(den)<1e-8:return None
    t=((c[0]-a[0])*v-(c[1]-a[1])*u)/den
    s=((c[0]-a[0])*y-(c[1]-a[1])*x)/den
    if -tolerance/hypot(x,y)<=t<=1+tolerance/hypot(x,y) and -tolerance/hypot(u,v)<=s<=1+tolerance/hypot(u,v):
        return [a[0]+t*x,a[1]+t*y]


def build_graph(detection,ports):
    d=deepcopy(detection);validate_detection(d);segs=d['segments'];tol=d['tolerance']
    if len(segs)>1500 or len(ports)>200:raise ValueError('Geometry pilot bounds exceeded')
    groups=[]
    # A native curve's small sampling chords may be much closer than the normal
    # endpoint snap tolerance. Merging them manufactures forks. Use exact
    # contacts on drawings containing native paths; unresolved gaps stay gaps.
    native=any(s.get('primitive')=='curve' for s in segs)
    contact_tol=1e-7 if native else tol
    def path_id(s):
        return s.get('path_id',s.get('source')) if s.get('primitive')=='curve' else None
    def group(p):
        for g in groups:
            if dist(g['point'],p)<=contact_tol:return g
        g={'point':list(p),'segments':set(),'ports':[]};groups.append(g);return g
    for s in segs:
        for k in ('start','end'):group(s[k])['segments'].add(s['id'])
    for i,s in enumerate(segs):
        for q in segs[i+1:]:
            if path_id(s) is not None and path_id(s)==path_id(q):continue
            p=intersect(s['start'],s['end'],q['start'],q['end'],contact_tol)
            if p is not None:group(p)['segments'].update((s['id'],q['id']))
    byid={s['id']:s for s in segs}
    # Include collinear shared endpoints and near-endpoint tee contacts.
    for g in groups:
        for s in segs:
            if projection(g['point'],s['start'],s['end'])[1]<=contact_tol:g['segments'].add(s['id'])
    for name,p in ports.items():
        point(p);g=group(p)
        candidates=[s for s in segs if projection(p,s['start'],s['end'])[1]<=contact_tol]
        if not candidates:d['warnings'].append('unattached_port:'+name);continue
        g['segments'].update(s['id'] for s in candidates);g['ports'].append(name)
    parent={};coordinates={};pointgroups={};junction_for={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    def union(a,b):parent[find(b)]=find(a)
    for i,g in enumerate(groups):
        members=sorted(g['segments']);p=g['point'];rays=[]
        for sid in members:
            token=(i,sid);find(token);coordinates[token]=p;pointgroups[token]=g
            for endpoint in (byid[sid]['start'],byid[sid]['end']):
                v=[endpoint[0]-p[0],endpoint[1]-p[1]];length=hypot(*v)
                if length<=contact_tol:continue
                v=[x/length for x in v]
                if not any(sum(a*b for a,b in zip(v,r))>.99 for r in rays):rays.append(v)
        dot=any(dist(p,x['point'])<=max(tol,x['radius']) for x in d.get('dots',[]))
        if (dot or len(rays)==3) and any(byid[s].get('path_id') and byid[s].get('primitive')=='curve'
                and min(dist(p,byid[s][k]) for k in ('start','end'))>contact_tol for s in members):
            raise ValueError('Unverified native curve contact; source tracing required')
        hop=len(rays)>=4 and any(byid[s].get('primitive')=='curve' for s in members)
        crossing=not dot and (hop or (len(rays)==4 and all(any(sum(a*b for a,b in zip(r,v))<-.97 for v in rays) for r in rays)))
        if crossing:
            d['excluded_intersections'].append({'kind':'hop' if hop else 'crossing','point':p,'segment_ids':members,'convention':CONVENTION})
            # Four separately drawn end segments at an X still make TWO paths.
            for a in members:
                av=[byid[a]['end'][k]-byid[a]['start'][k] for k in (0,1)];an=hypot(*av)
                for b in members:
                    bv=[byid[b]['end'][k]-byid[b]['start'][k] for k in (0,1)];bn=hypot(*bv)
                    samecurve=path_id(byid[a]) is not None and path_id(byid[a])==path_id(byid[b])
                    if samecurve or (byid[a].get('primitive')==byid[b].get('primitive') and abs(sum(x*y for x,y in zip(av,bv))/(an*bn))>.97):union((i,a),(i,b))
        elif len(members)>1:
            kind='junction_dot' if dot else 'tee' if len(rays)==3 else 'shared_endpoint'
            # More than four incident rays is outside the supported convention.
            if len(rays)>4:d['warnings'].append('complex_intersection');continue
            for sid in members[1:]:union((i,members[0]),(i,sid))
            ev={'kind':kind,'point':p,'segment_ids':members}
            d['junctions'].append({'id':f'j{i}',**ev});junction_for[i]=ev
    adjacent=defaultdict(list);rootpoints={}
    for token,p in coordinates.items():rootpoints[find(token)]=p
    for s in segs:
        seq=sorted(((projection(g['point'],s['start'],s['end'])[0],(i,s['id'])) for i,g in enumerate(groups) if s['id'] in g['segments']))
        for (_,a),(_,b) in zip(seq,seq[1:]):
            x,y=find(a),find(b)
            if x==y or dist(rootpoints[x],rootpoints[y])<1e-6:continue
            adjacent[x].append((y,s['id']));adjacent[y].append((x,s['id']))
    labels={}
    for i,g in enumerate(groups):
        roots={find((i,s)) for s in g['segments']}
        if g['ports'] and len(roots)!=1:
            d['warnings'].append('ambiguous_port_at_crossing');continue
        if len(g['ports'])>1:d['warnings'].append('duplicate_port_location');continue
        for name in g['ports']:labels[next(iter(roots))]=name
        if i in junction_for and len(adjacent[find((i,next(iter(g['segments']))))])>2 and not g['ports']:
            labels[find((i,next(iter(g['segments']))))]=f'J@{g["point"][0]:.2f},{g["point"][1]:.2f}'
    # Attach only if the closest line is within tolerance and orientation agrees.
    for arrow in d['arrows']:
        if d['route']=='raster' and arrow.get('attachment_blocked') is True:
            arrow['segment_id']=None
            continue
        scored=[];v=[arrow['tip'][k]-arrow['base'][k] for k in (0,1)];vn=hypot(*v)
        for s in segs:
            w=[s['end'][k]-s['start'][k] for k in (0,1)];wn=hypot(*w)
            distance=max(projection(arrow[k],s['start'],s['end'])[1] for k in ('base','tip'))
            if distance<=tol and abs(sum(x*y for x,y in zip(v,w))/(vn*wn))>.9:scored.append((distance,s['id']))
        scored.sort();arrow['segment_id']=scored[0][1] if scored else None
        if len(scored)>1 and abs(scored[0][0]-scored[1][0])<.01 and scored[0][1]!=scored[1][1]:
            arrow['segment_id']=None;d['warnings'].append('ambiguous_arrow_attachment')
    edges=[];seen=set()
    for start,name in sorted(labels.items(),key=lambda x:x[1]):
        queue=deque([(start,[start],[])]);visited={start}
        while queue:
            at,path,sids=queue.popleft()
            if at!=start and at in labels:
                other=labels[at];key=tuple(sorted((name,other)))
                if key in seen:continue
                seen.add(key)
                if name>other:continue
                points=[rootpoints[t] for t in path];unique=list(dict.fromkeys(sids));evs=[]
                for token in path:
                    i=token[0];ev=junction_for.get(i)
                    if ev:
                        ids=[sid for sid in ev['segment_ids'] if sid in unique]
                        if ids:evs.append({**ev,'segment_ids':ids})
                if not evs:
                    first=byid[sids[0]]
                    evs=[{'kind':'shared_endpoint','point':first['start'],'segment_ids':[sids[0]]}]
                candidates=[r for r in d['arrows'] if r['segment_id'] in unique and
                            min(projection(r['tip'],a,b)[1] for a,b in zip(points,points[1:]))<=tol]
                claims=[]
                for r in candidates:
                    a,b=min(zip(points,points[1:]),key=lambda pair:projection(r['tip'],*pair)[1])
                    dot=sum((b[k]-a[k])*(r['tip'][k]-r['base'][k]) for k in (0,1))
                    claims.append(('a_to_b' if dot>0 else 'b_to_a',r['id']))
                direction=claims[0][0] if claims and len({x[0] for x in claims})==1 else 'unknown'
                arrow_id=claims[0][1] if direction!='unknown' else None
                if claims and direction=='unknown':d['warnings'].append('conflicting_arrows')
                edges.append({'a':name,'b':other,'direction':direction,'arrow_id':arrow_id,
                    'segment_ids':unique,'path':points,'connection_evidence':evs,'convention':CONVENTION})
                continue
            for other,sid in adjacent[at]:
                if other not in visited:
                    visited.add(other);queue.append((other,path+[other],sids+[sid]))
    rules=check_edges(edges,d)
    return {'schema':'foundry.detected_connectivity/1','input_sha256':d['input_sha256'],
        'route':d['route'],'detection':d,'detection_sha256':digest(d),'ports_sha256':digest(ports),
        'edges':edges,'rules':rules,'uncertain':bool(d['warnings']),
        'training_approved':False,'convention':CONVENTION}
