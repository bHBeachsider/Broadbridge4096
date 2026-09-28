"""Local PNG review bundle. All correction exports require authenticated review.

Only untransformed PNG coordinates are supported. Rendered PDF/DXF proposals must
first supply a verified transform to these pixels; this tool never guesses one.
No live app, credentials, model calls or reference-file writes.
"""
import argparse
import base64
import hashlib
import html
import json
from math import isfinite
from pathlib import Path


def sha(raw): return hashlib.sha256(raw).hexdigest()


def canonical(value): return json.dumps(value,sort_keys=True,allow_nan=False).encode()


def point(value):
    if not isinstance(value,list) or len(value)!=2 or any(type(x) not in (int,float) or not isfinite(x) for x in value):
        raise ValueError('Invalid pixel coordinate')
    return ','.join(format(x,'g') for x in value)


def validate_proposal(proposal, bundle):
    """Validate a pending proposal's immutable bindings, never approve its content."""
    errors=[]; template=bundle['proposal_template']
    for key in ('schema','revision','source_sha256','detection_sha256','reference_sha256','before_sha256','mode'):
        if proposal.get(key)!=template[key]: errors.append('stale_'+key.removesuffix('_sha256'))
    if proposal.get('status')!='pending_authenticated_review': errors.append('unauthenticated_status')
    if not isinstance(proposal.get('after'),list): errors.append('invalid_after')
    if not isinstance(proposal.get('reviewer'),str) or not proposal['reviewer'].strip(): errors.append('reviewer_missing')
    return errors


def build_review_bundle(source, detection, reference, out, *, revision):
    from PIL import Image
    source,out=Path(source),Path(out)
    if source.suffix.lower()!='.png': raise ValueError('PNG pixel coordinate input required')
    source_raw=source.read_bytes()
    with Image.open(source) as im:
        if im.format!='PNG' or im.width*im.height>4_000_000: raise ValueError('Bounded PNG required')
        width,height=im.size
    mode='source_only' if reference is None else 'detector_overlay'
    # Source-only mode deliberately does not even open the detector/reference.
    proposed={}; detection_hash=None; reference_hash=None
    if mode=='detector_overlay':
        raw=Path(detection).read_bytes(); proposed=json.loads(raw); detection_hash=sha(raw)
        if proposed.get('input_sha256')!=sha(source_raw): raise ValueError('Detector/source hash mismatch')
        reference_hash=sha(Path(reference).read_bytes())
        route=proposed.get('route')
        if route is not None and route!='raster': raise ValueError('Vector-to-pixel transform must be verified separately')
    before=proposed.get('edges',[])
    template={'schema':'broadbridge.diagram_correction_proposal/1','mode':mode,
        'revision':revision,'source_sha256':sha(source_raw),'detection_sha256':detection_hash,
        'reference_sha256':reference_hash,'before_sha256':sha(canonical(before)),
        'reviewer':'','date':None,'status':'pending_authenticated_review','after':before,'comment':''}
    bundle={'schema':'broadbridge.diagram_review_bundle/1','mode':mode,
        'coordinate_frame':'pixels-top-left','width':width,'height':height,
        'training_approved':False,'proposal_template':template}
    paths=[]
    for edge in before:
        title=html.escape(str(edge['a'])+' → '+str(edge['b'])+' ('+str(edge['direction'])+')')
        points=' '.join(point(p) for p in edge['path'])
        color='#b66a00' if edge['direction']=='unknown' else '#007f75'
        paths.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" opacity=".65"><title>{title}</title></polyline>')
    arrows=[]
    for arrow in proposed.get('detection',{}).get('arrows',[]):
        xy=' '.join(point(arrow[k]) for k in ('base','tip'))
        arrows.append(f'<polyline points="{xy}" stroke="#af2175" stroke-width="3" marker-end="url(#tip)"><title>{html.escape(str(arrow))}</title></polyline>')
    warnings=proposed.get('detection',{}).get('warnings',[])
    uncertain=[]
    for item in proposed.get('detection',{}).get('excluded_intersections',[]):
        x,y=item['point']; point([x,y])
        uncertain.append(f'<circle cx="{x:g}" cy="{y:g}" r="7" fill="none" stroke="#b42318" stroke-width="2"><title>{html.escape(str(item))}</title></circle>')
    title='Source-only tracing' if mode=='source_only' else 'Detector review'
    data=json.dumps(template,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    # No reference values appear in the HTML, including the source-only variant.
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Broadbridge diagram review</title><style>
body{font:16px system-ui,sans-serif;color:#183248;background:#f3f6f8;margin:0}main{max-width:1100px;margin:auto;padding:28px}
h1{font-size:30px}p{line-height:1.5}.notice{border-left:4px solid #447799;background:#e6eef4;padding:16px}
svg{width:100%;height:auto;border:1px solid #bbcbd6;background:white}label{display:inline-block;margin:10px 18px 10px 0}
textarea{width:100%;box-sizing:border-box;min-height:180px;font:14px ui-monospace,monospace;padding:12px}input{padding:8px}
button{padding:12px 20px;background:#244e71;color:white;border:0;border-radius:5px}details{margin:16px 0}code{overflow-wrap:anywhere}
</style><main><h1>@@TITLE@@</h1><p class="notice">Local engineering review preparation. Corrections remain pending authenticated review. This does not approve a reference, training batch or release.</p>
<p>Revision: <strong>@@REVISION@@</strong>. Unknown directions are amber; supported proposals teal; arrow keypoints magenta. Hover for evidence. Input hash: <code>@@HASH@@</code>.</p>
<label><input type="checkbox" checked data-layer="edges">Proposed edges</label><label><input type="checkbox" checked data-layer="arrows">Arrow keypoints</label><label><input type="checkbox" checked data-layer="contacts">Excluded contacts</label>
<svg viewBox="0 0 @@WIDTH@@ @@HEIGHT@@" role="img" aria-label="Original drawing with toggleable proposed geometry"><defs><marker id="tip" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="#af2175"/></marker></defs>
<image width="@@WIDTH@@" height="@@HEIGHT@@" href="data:image/png;base64,@@IMAGE@@"/><g id="edges">@@PATHS@@</g><g id="arrows">@@ARROWS@@</g><g id="contacts">@@CONTACTS@@</g></svg>
<details><summary>Warnings and evidence records</summary><pre>@@WARNINGS@@</pre></details>
<h2>Propose a correction or source-only trace</h2><p>Enter an edge array using a, b, direction (unknown / a_to_b / b_to_a) and path coordinates. Record uncertainty in notes. Export creates a new local proposal; it never replaces the evaluated reference. A typed name is attribution, not sign-off.</p>
<label>Reviewer <input id="reviewer" autocomplete="name"></label><label>Review minutes <input id="minutes" type="number" min="0" step=".1"></label>
<label for="after">Proposed edge array</label><textarea id="after" spellcheck="false">@@AFTER@@</textarea>
<label for="notes">Notes, convention evidence and unresolved issues</label><textarea id="notes" style="min-height:90px"></textarea>
<p><button id="export">Export pending proposal</button></p><p id="status" role="status"></p>
<script>const template=@@TEMPLATE@@;
document.querySelectorAll('[data-layer]').forEach(x=>x.addEventListener('change',()=>document.getElementById(x.dataset.layer).style.display=x.checked?'':'none'));
document.getElementById('export').addEventListener('click',()=>{try{
const after=JSON.parse(document.getElementById('after').value);if(!Array.isArray(after))throw Error('The proposed edges must be an array.');
const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer)throw Error('Enter the reviewer name for attribution.');
const proposal={...template,after,reviewer,date:new Date().toISOString(),comment:document.getElementById('notes').value,review_minutes:document.getElementById('minutes').value||null};
const blob=new Blob([JSON.stringify(proposal,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='diagram-correction-pending.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
document.getElementById('status').textContent='Pending proposal exported. Authenticated independent review is still required.';
}catch(e){document.getElementById('status').textContent=e.message;}});</script></main></html>'''
    values={'TITLE':title,'REVISION':html.escape(str(revision)),'HASH':sha(source_raw),
        'WIDTH':str(width),'HEIGHT':str(height),'IMAGE':base64.b64encode(source_raw).decode(),
        'PATHS':''.join(paths),'ARROWS':''.join(arrows),'CONTACTS':''.join(uncertain),
        'WARNINGS':html.escape(json.dumps(warnings,indent=2)),
        'AFTER':html.escape(json.dumps(before,indent=2)),'TEMPLATE':data}
    for key,value in values.items(): page=page.replace('@@'+key+'@@',value)
    out.mkdir(parents=True,exist_ok=False)
    (out/'review.html').write_text(page,encoding='utf-8',newline='\n')
    (out/'bundle.json').write_text(json.dumps(bundle,indent=2),encoding='utf-8',newline='\n')
    hashes={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}
    (out/'checksums.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8',newline='\n')
    return bundle


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','detection','out'): p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--reference',type=Path);p.add_argument('--revision',required=True)
    a=p.parse_args();result=build_review_bundle(a.source,a.detection,a.reference,a.out,revision=a.revision)
    print(json.dumps({'mode':result['mode'],'training_approved':False,'html':str(a.out/'review.html')}))


if __name__=='__main__':main()
