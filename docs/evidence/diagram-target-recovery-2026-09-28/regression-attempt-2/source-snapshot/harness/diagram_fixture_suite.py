"""Bounded, original construction fixtures. Preparation never runs a detector.

All these variants share the historical construction family. They are development
data; reserve cohorts intentionally remain empty pending independent sources.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False); f.write('\n')


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def validate_split(records):
    groups = {}
    for row in records:
        groups.setdefault(row['family_id'], set()).add(row['split'])
    return ['family_leakage:'+key for key in sorted(groups) if len(groups[key]) > 1]


def validate_design(design):
    rows = design['drawings']
    if type(design['existing_count']) is not int or design['existing_count'] != 12 or len(rows)+12 > 50:
        raise ValueError('Stress program bounded to 50 including existing twelve')
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r'[A-Za-z0-9_-]+', i) for i in ids):
        raise ValueError('Unsafe or duplicate drawing ID')
    normalized = [{**r, 'family_id': r.get('family_id', design.get('family_id')),
                   'split': r.get('split', design.get('split'))} for r in rows]
    errors = validate_split(normalized)
    if errors:
        raise ValueError(', '.join(errors))
    # This generator's descendants cannot be declared independent reserves.
    if any(r['split'] != 'development' for r in normalized):
        raise ValueError('Construction derivatives are development only')
    return normalized


def construction(row):
    """Define reference topology independently of PDF/DXF extraction."""
    case = row['case']; arrows = []; dots = []
    if case in ('arrow', 'no-arrow', 'conflicting-arrows'):
        angle = math.radians(row.get('angle', 0)); u,v = math.cos(angle),math.sin(angle)
        xy = [[300-150*u,200-150*v], [300+150*u,200+150*v]]
        direction = row.get('direction', 'unknown')
        edges = [(0,1,direction)]
        if case == 'arrow':
            arrows = [(0,1,direction,.55,row['arrow_length'])]
        elif case == 'conflicting-arrows':
            arrows = [(0,1,'a_to_b',.4,18), (0,1,'b_to_a',.4,18)]
    elif case == 'dense-crossings':
        xy = [(80,140),(520,140),(80,260),(520,260),(220,60),(220,340),(380,60),(380,340)]
        edges = [(0,1,'unknown'),(2,3,'unknown'),(4,5,'unknown'),(6,7,'unknown')]
    elif case == 'hop':
        xy = [(80,200),(520,200),(300,60),(300,340)]
        edges = [(0,1,'unknown'),(2,3,'unknown')]
    elif case in ('tee','tee-dot'):
        xy = [(80,200),(300,200),(520,200),(300,60)]
        edges = [(0,1,'unknown'),(1,2,'unknown'),(1,3,'unknown')]
        if case == 'tee-dot': dots = [1]
    elif case == 'unexplained-break':
        xy = [(80,200),(520,200)]
        edges = [(0,1,'unknown')]  # Native source continuity; visible gap remains ambiguous.
    elif case == 'unmatched-off-page':
        xy = [(80,160),(270,160),(330,240),(520,240)]
        edges = [(0,1,'unknown'),(2,3,'unknown')]
    else:
        raise ValueError('Unknown source construction class: '+case)
    tags = [('J-' if case in ('tee','tee-dot') and i == 1 else 'V-')+str(row['seed']*10+i) for i in range(len(xy))]
    return {**row, 'positions':xy,'tags':tags,'edges':edges,'dots':dots,'arrows':arrows}


def render(spec, out):
    import pymupdf
    import ezdxf
    doc = pymupdf.open(); page = doc.new_page(width=600,height=400)
    cad = ezdxf.new(); msp = cad.modelspace(); masks = []
    for index,(i,j,_) in enumerate(spec['edges']):
        a,b = spec['positions'][i],spec['positions'][j]
        if spec['case'] == 'hop' and index == 0:
            page.draw_line(a,(280,200),width=2); page.draw_bezier((280,200),(280,170),(320,170),(320,200),width=2); page.draw_line((320,200),b,width=2)
            msp.add_line(a,(280,200)); msp.add_open_spline(control_points=[(280,200),(280,170),(320,170),(320,200)],degree=3); msp.add_line((320,200),b)
        elif spec['case'] == 'unexplained-break':
            page.draw_line(a,(289,200),width=2); page.draw_line((311,200),b,width=2)
            msp.add_line(a,(289,200)); msp.add_line((311,200),b)
        else:
            page.draw_line(a,b,width=2); msp.add_line(a,b)
    for i,j,direction,location,length in spec['arrows']:
        a,b = spec['positions'][i],spec['positions'][j]
        if direction == 'b_to_a': a,b = b,a
        dx,dy = b[0]-a[0],b[1]-a[1]; size = math.hypot(dx,dy); u,v = dx/size,dy/size
        tip = [a[0]+location*dx,a[1]+location*dy]; base = [tip[0]-length*u,tip[1]-length*v]
        width = length*.67
        points = [tip,[base[0]+width*v/2,base[1]-width*u/2],[base[0]-width*v/2,base[1]+width*u/2]]
        shape = page.new_shape(); shape.draw_polyline(points+[points[0]]); shape.finish(fill=(0,0,0),color=(0,0,0)); shape.commit()
        msp.add_solid(points)
    for index in spec['dots']:
        xy = spec['positions'][index]; page.draw_circle(xy,5,fill=(0,0,0),color=(0,0,0))
        msp.add_hatch(color=7).paths.add_edge_path().add_arc(xy,5,0,360)
    for tag,(x,y) in zip(spec['tags'],spec['positions']):
        tx,ty = x+9,y+18; page.insert_text((tx,ty),tag,fontsize=11)
        msp.add_text(tag,dxfattribs={'height':11,'insert':(tx,ty)})
        masks.append([tx-1,ty-12,tx+len(tag)*7,ty+3])
    if spec['case'] == 'unmatched-off-page':
        page.insert_text((240,125),'UNMATCHED CONNECTOR - REVIEW',fontsize=9)
        msp.add_text('UNMATCHED CONNECTOR - REVIEW',dxfattribs={'height':9,'insert':(240,125)})
        masks.append([239,113,450,130])
    doc.save(out.with_suffix('.pdf'),no_new_id=True)
    page.get_pixmap(alpha=False).save(out.with_suffix('.png')); doc.close()
    cad.saveas(out.with_suffix('.dxf'))
    return masks


def prepare_suite(out, foundry, design):
    out,foundry,design = Path(out),Path(foundry),Path(design)
    if not foundry.is_absolute(): raise ValueError('Absolute Foundry path required')
    data = json.loads(design.read_bytes()); rows = validate_design(data)
    specs = [construction(row) for row in rows]  # Validate before directory side effects.
    sys.path.insert(0,str(foundry))
    from src.ingestion import reference_graphs as rg
    if not Path(rg.__file__).resolve().is_relative_to(foundry.resolve()):
        raise ValueError('Wrong Foundry checkout')
    pilot = load_module('reference_graph_pilot')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'design.json',data); summary = []
    for spec in specs:
        name = spec['id']; model = pilot.build_model(spec); snapshot = rg.serialize_dexpi(model)
        raw = json.dumps({'spec':spec,'snapshot':snapshot},sort_keys=True).encode()
        graph = rg.topology_from_dexpi(model,source_sha256=digest(raw)); graph['origin'] = 'synthetic-by-construction'
        for edge in graph['edges']:
            i,j,direction = spec['edges'][int(edge['id'][1:])]
            if (edge['a'],edge['b']) != (spec['tags'][i],spec['tags'][j]): raise ValueError('Unexpected DEXPI edge ordering')
            edge.update(direction=direction,direction_basis='original construction')
        write(out/(name+'.model.json'),{'spec':spec,'snapshot':snapshot,'topology':graph})
        masks = render(spec,out/name)
        reference = rg.project_reference(graph,image_sha256=digest((out/(name+'.png')).read_bytes()))['reference']
        write(out/(name+'.reference.json'),reference)
        write(out/(name+'.ports.json'),{'ports':dict(zip(spec['tags'],spec['positions'])),'text_masks':masks,'origin':'supplied annotations; not automatic port detection'})
        summary.append({k:spec[k] for k in ('id','family_id','split','seed','case')})
    assets = {p.name:digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {'schema':'broadbridge.diagram_fixture_suite/1','drawings':summary,'assets':assets,
        'generator_sha256':digest(Path(__file__).read_bytes()),'design_sha256':digest(design.read_bytes()),
        'dexpi_builder_sha256':digest(Path(pilot.__file__).read_bytes()),
        'coordinate_frame':'page-points-top-left; 72 dpi PNG; identity page-to-image transform',
        'provenance':'pre-run-checksum','training_approved':False,'gate_eligible':False,
        'new_drawings':len(specs),'program_drawings':12+len(specs),'reserves_generated':0,'detector_runs':0,
        'limitations':['Same construction ancestry; development only','Supplied ports/masks','Source-only human reference and visibility review pending']}
    write(out/'manifest.json',manifest)
    write(out/'freeze.json',{'manifest_sha256':digest((out/'manifest.json').read_bytes())})
    return {k:manifest[k] for k in ('new_drawings','program_drawings','reserves_generated','detector_runs')}


def verify_suite(out):
    out = Path(out); raw = (out/'manifest.json').read_bytes()
    if digest(raw) != json.loads((out/'freeze.json').read_bytes())['manifest_sha256']:
        raise ValueError('Frozen manifest changed')
    manifest = json.loads(raw)
    for name,expected in manifest['assets'].items():
        if Path(name).name != name or digest((out/name).read_bytes()) != expected:
            raise ValueError('Frozen asset changed: '+name)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True); p.add_argument('--foundry',type=Path,required=True)
    p.add_argument('--design',type=Path,default=Path(__file__).resolve().parents[2]/'packs/oil-gas/manifests/diagram_fixture_design.json')
    args = p.parse_args(); print(json.dumps(prepare_suite(args.out,args.foundry,args.design),indent=2))


if __name__ == '__main__': main()
