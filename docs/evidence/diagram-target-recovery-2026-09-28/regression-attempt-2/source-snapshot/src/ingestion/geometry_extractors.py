"""Bounded, optional CPU geometry adapters; no model calls or runtime downloads.

Unsupported PDF visibility/mixed content and unsupported DXF entities fail closed.
Raster segmentation is an experimental straight-line detector; curved/poor scans
can be incomplete and must be measured against an independent reference.
"""
from math import dist, hypot, pi, ceil, atan2, degrees
from pathlib import Path
import hashlib
from .geometry_contract import projection


def base(path,route,tolerance=2.0):
    return {'schema':'foundry.diagram_detection/1','input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'route':route,'segments':[],'dots':[],'arrows':[],'junctions':[],
        'excluded_intersections':[],'tolerance':tolerance,'warnings':[]}


def segment(d,a,b,source,minimum=.2):
    if len(d['segments'])>=1500:raise ValueError('Geometry pilot bounds exceeded')
    for p in (a,b):
        if len(p)>2 and abs(p[2])>1e-8:raise ValueError('Nonplanar DXF geometry unsupported')
    a,b=list(map(float,list(a)[:2])),list(map(float,list(b)[:2]))
    if dist(a,b)<minimum:return False
    d['segments'].append({'id':f's{len(d["segments"])}','start':a,'end':b,'source':source});return True


def native_path(d,points,source,path_id,curved=True,index=0):
    """Keep every nonzero chord, its native identity and traversal order.

    Chords approximate geometry only; their vertices are not inferred branches.
    """
    for a,b in zip(points,points[1:]):
        if segment(d,a,b,source,minimum=1e-8):
            d['segments'][-1].update(path_id=path_id,path_index=index)
            if curved:d['segments'][-1]['primitive']='curve'
            index+=1
    return index


def dxf_curve_points(entity,contacts):
    """Insert proven source-curve contacts BEFORE tessellation becomes topology.

    A nearby chord is only a search filter. Admission requires coincidence with
    the actual circle/B-spline, never just the .3 drawing-unit flattening bound.
    """
    kind=entity.dxftype()
    if kind=='LINE':return [entity.dxf.start,entity.dxf.end]
    points=list(entity.flattening(.3))
    if kind=='ARC':
        center=entity.dxf.center;radius=entity.dxf.radius
        start=entity.dxf.start_angle;span=(entity.dxf.end_angle-start)%360
        def parameter(p):return (degrees(atan2(p[1]-center[1],p[0]-center[0]))-start)%360
        candidates=[p for p in contacts if abs(hypot(p[0]-center[0],p[1]-center[1])-radius)<=1e-7 and parameter(p)<=span]
        # Existing start/end points keep their intended order across 0 degrees.
        middle=[p for p in candidates if dist(p,points[0])>1e-7 and dist(p,points[-1])>1e-7]
        return [points[0]]+sorted(points[1:-1]+middle,key=parameter)+[points[-1]]
    curve=entity.construction_tool()
    # Keep t throughout subdivision. Chord projection order can run backwards
    # on a turning spline even when every inserted point lies on the source.
    knots=curve.knots();lo,hi=knots[curve.order-1],knots[curve.count]
    intervals=sorted({lo,hi,*[t for t in knots if lo<t<hi]})
    parameters={lo}
    def subdivide(a,b,depth=0):
        if depth>20 or len(parameters)>=1500:raise ValueError('Native curve approximation bound exceeded')
        p,q=curve.point(a),curve.point(b)
        gap=max(projection(list(curve.point(a+(b-a)*fraction))[:2],list(p)[:2],list(q)[:2])[1] for fraction in (.25,.5,.75))
        if gap>.3:
            middle=(a+b)/2;subdivide(a,middle,depth+1);subdivide(middle,b,depth+1)
        else:parameters.add(b)
    for a,b in zip(intervals,intervals[1:]):
        for i in range(4):subdivide(a+(b-a)*i/4,a+(b-a)*(i+1)/4)
    sample_params=sorted(parameters);points=[curve.point(t) for t in sample_params]
    for p in contacts:
        index=min(range(len(points)-1),key=lambda i:projection(list(p)[:2],list(points[i])[:2],list(points[i+1])[:2])[1])
        t,gap=projection(list(p)[:2],list(points[index])[:2],list(points[index+1])[:2])
        if gap>.31:continue
        value=curve.point_inversion(p,epsilon=1e-10,max_iterations=100)
        if dist(p,curve.point(value))>1e-7:continue
        if lo<=value<=hi:parameters.add(value)
    return [curve.point(t) for t in sorted(parameters)]


def cubic_points(controls,contacts):
    import numpy as np
    def evaluate(t):
        return [(1-t)**3*controls[0][k]+3*(1-t)**2*t*controls[1][k]+3*(1-t)*t*t*controls[2][k]+t**3*controls[3][k] for k in (0,1)]
    parameters={n/12 for n in range(13)}
    axis=max((0,1),key=lambda k:max(p[k] for p in controls)-min(p[k] for p in controls))
    a,b,c,d=(p[axis] for p in controls)
    for p in contacts:
        coefficients=np.trim_zeros([-a+3*b-3*c+d,3*a-6*b+3*c,-3*a+3*b,a-p[axis]],'f')
        for root in np.roots(coefficients):
            if abs(root.imag)>1e-9 or not 0<=root.real<=1:continue
            t=float(root.real)
            if dist(evaluate(t),p)<=1e-7:parameters.add(t)
    return [evaluate(t) for t in sorted(parameters)]


def triangle(points):
    pts=[]
    for p in points:
        p=list(map(float,p[:2]))
        if not any(dist(p,q)<.01 for q in pts):pts.append(p)
    if len(pts)!=3:return None
    # An arrow is an elongated triangle; shortest side is its base. Equilateral
    # or broad/ambiguous triangles cannot supply direction.
    sides=sorted((dist(pts[(i+1)%3],pts[(i+2)%3]),i) for i in range(3))
    width,i=sides[0];a,b=pts[(i+1)%3],pts[(i+2)%3]
    mid=[(a[k]+b[k])/2 for k in (0,1)]
    if width<1 or dist(pts[i],mid)<width*.9:return None
    return {'tip':pts[i],'base':mid}


def add_arrow(d,pts,source):
    if any(len(p)>2 and abs(p[2])>1e-8 for p in pts):raise ValueError('Nonplanar DXF arrow unsupported')
    r=triangle(pts)
    if r is None:d['warnings'].append('ambiguous_filled_polygon:'+source);return
    d['arrows'].append({'id':f'a{len(d["arrows"])}',**r,'segment_id':None,'source':source})


def pdf(path,page):
    import pymupdf
    with pymupdf.open(path) as doc:
        if doc.get_ocgs():raise ValueError('PDF optional-content visibility requires review')
        p=doc[page];draws=p.get_drawings(extended=True);images=p.get_images()
        if images and draws:raise ValueError('mixed raster/vector PDF requires reviewed separation')
        if not draws:
            if not images:raise ValueError('No drawing geometry')
            if ceil(p.rect.width)*ceil(p.rect.height)>4_000_000:raise ValueError('Raster pixel bound exceeded before rendering')
            pix=p.get_pixmap(alpha=False)
            import numpy as np
            arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
            return raster(path,arr)
        d=base(path,'vector_pdf');pending=[]
        for index,item in enumerate(draws):
            if item['type'] in ('clip','group'):raise ValueError('PDF clipping/groups require reviewed flattening')
            if any(item.get(k) is not None and item[k]<1 for k in ('stroke_opacity','fill_opacity')):
                raise ValueError('PDF transparency unsupported')
            source='path:'+str(index);ops=item['items'];fill=item.get('fill')
            colors=[c for c in (item.get('color'),fill) if c is not None]
            if any(any(channel>.15 for channel in c) for c in colors):
                raise ValueError('PDF color/visibility requires reviewed monochrome separation')
            if fill is not None:
                if all(op[0]=='l' for op in ops):
                    pts=[list(op[1]) for op in ops]+[list(ops[-1][2])]
                    add_arrow(d,pts,source)
                elif len(ops)==4 and all(op[0]=='c' for op in ops):
                    rect=item['rect']
                    if abs(rect.width-rect.height)<.1 and 2<=rect.width<=16:
                        d['dots'].append({'point':list(rect.tl+(rect.br-rect.tl)/2),'radius':rect.width/2,'source':source})
                    else:d['warnings'].append('unclassified_filled_curve:'+source)
                else:d['warnings'].append('unclassified_fill:'+source)
                continue
            if item.get('dashes','[] 0')!='[] 0':d['warnings'].append('dashed_line_requires_review:'+source);continue
            for op_index,op in enumerate(ops):
                if op[0]=='l':segment(d,list(op[1]),list(op[2]),source)
                elif op[0]=='c':
                    pending.append(([list(v) for v in op[1:]],source,f'{source}:curve:{op_index}'))
                else:d['warnings'].append('unsupported_path:'+source)
        contacts=[s[k] for s in d['segments'] for k in ('start','end')]
        contacts.extend(p for controls,_,_ in pending for p in (controls[0],controls[-1]))
        contacts.extend(dot['point'] for dot in d['dots'])
        for controls,source,path_id in pending:native_path(d,cubic_points(controls,contacts),source,path_id)
        return d


def dxf(path):
    import ezdxf
    from ezdxf.path import make_path
    doc=ezdxf.readfile(path);d=base(path,'vector_dxf');pending=[]
    for e in doc.modelspace():
        kind=e.dxftype();src=kind+':'+e.dxf.handle
        if kind in ('TEXT','MTEXT'):continue
        layer=doc.layers.get(e.dxf.layer)
        attr=lambda name,default:e.dxf.get(name,default) if e.dxf.is_supported(name) else default
        if layer.is_off() or layer.is_frozen() or attr('invisible',0):
            raise ValueError('DXF visibility requires reviewed flattening')
        if tuple(attr('extrusion',(0,0,1)))!=(0,0,1):raise ValueError('Nonplanar DXF extrusion unsupported')
        elevation=attr('elevation',0)
        z=float(elevation) if isinstance(elevation,(int,float)) else elevation[2]
        if abs(z)>1e-8 or abs(attr('thickness',0))>1e-8:raise ValueError('Nonplanar DXF elevation/thickness unsupported')
        style=e.dxf.get('linetype','BYLAYER').upper()
        if style=='BYLAYER':style=layer.dxf.linetype.upper()
        if style!='CONTINUOUS':raise ValueError('DXF non-continuous line convention requires review')
        if kind=='LINE':segment(d,e.dxf.start,e.dxf.end,src)
        elif kind=='SOLID':add_arrow(d,[list(v) for v in e.wcs_vertices(close=False)],src)
        elif kind=='CIRCLE' and 1<=e.dxf.radius<=8:
            # CIRCLE is an outline, not proof of a filled junction dot.
            d['warnings'].append('outline_circle_not_junction:'+src)
        elif kind in ('ARC','LWPOLYLINE','POLYLINE','SPLINE'):
            if kind=='LWPOLYLINE' and e.closed:
                d['warnings'].append('closed_outline_not_filled:'+src);continue
            if len(pending)>=1500:raise ValueError('Geometry pilot bounds exceeded')
            pending.append((e,src))
        elif kind=='HATCH':
            if not e.dxf.solid_fill:raise ValueError('DXF hatch must be solid to support a junction')
            # Filled circles/triangles must have simple explicit boundaries.
            paths=list(e.paths)
            if len(paths)!=1:raise ValueError('Unsupported DXF hatch islands')
            p=paths[0]
            if hasattr(p,'vertices') and not any(v[2] for v in p.vertices):add_arrow(d,p.vertices,src)
            elif hasattr(p,'edges') and len(p.edges)==1:
                arc=p.edges[0]
                if hasattr(arc,'radius') and abs(arc.end_angle-arc.start_angle)>=359 and 1<=arc.radius<=8:
                    d['dots'].append({'point':list(arc.center),'radius':float(arc.radius),'source':src})
                else:raise ValueError('Unsupported DXF filled curve')
            else:raise ValueError('Unsupported DXF hatch')
        elif kind not in ('TEXT','MTEXT'):raise ValueError('Unsupported DXF entity '+kind)
    # All entities have passed visibility/planarity checks before their endpoints
    # are used as possible contacts. Virtual polyline parts retain line/arc type.
    parts=[];contacts=[]
    for e,src in pending:
        children=list(e.virtual_entities()) if e.dxftype() in ('LWPOLYLINE','POLYLINE') else [e]
        if any(c.dxftype() not in ('LINE','ARC','SPLINE') for c in children):
            raise ValueError('Unsupported native polyline part')
        parts.append((src,children))
        for c in children:
            p=make_path(c);contacts.extend((p.start,p.end))
    from ezdxf.math import Vec3
    contacts.extend(Vec3(s[k]) for s in d['segments'] for k in ('start','end'))
    contacts.extend(Vec3(dot['point']) for dot in d['dots'])
    for src,children in parts:
        index=0
        for c in children:
            pts=dxf_curve_points(c,contacts)
            index=native_path(d,pts,src,src,curved=c.dxftype()!='LINE',index=index)
    return d


def merge_lines(lines,tolerance=2):
    """Merge only collinear overlapping/touching Hough fragments, not gaps."""
    result=[]
    for a,b in sorted(lines,key=lambda l:-dist(*l)):
        merged=False
        for i,(c,e) in enumerate(result):
            if max(projection(p,c,e)[1] for p in (a,b))<=tolerance:
                merged=True;break  # contained duplicate
            v=[e[k]-c[k] for k in (0,1)];n=hypot(*v)
            perpendicular=lambda p:abs(v[0]*(p[1]-c[1])-v[1]*(p[0]-c[0]))/n
            if max(perpendicular(a),perpendicular(b))>tolerance:continue
            params=[sum((p[k]-c[k])*v[k] for k in (0,1))/(n*n) for p in (a,b)]
            if max(params)<-tolerance/n or min(params)>1+tolerance/n:continue
            lo,hi=min(0,*params),max(1,*params)
            result[i]=([c[k]+lo*v[k] for k in (0,1)],[c[k]+hi*v[k] for k in (0,1)])
            merged=True;break
        if not merged:result.append((a,b))
    return result


def raster(path,array=None,masks=()):
    import numpy as np
    from PIL import Image
    from .raster_connectivity import detect_arrows,detect_lines,reconcile
    if array is None:
        with Image.open(path) as im:
            if im.width*im.height>4_000_000:raise ValueError('Raster pixel bound exceeded')
            array=np.array(im.convert('RGB'))
    if array.shape[0]*array.shape[1]>4_000_000:raise ValueError('Raster pixel bound exceeded')
    analysis=array.copy()
    for x0,y0,x1,y1 in masks:
        analysis[max(0,int(y0)):min(array.shape[0],int(y1)),max(0,int(x0)):min(array.shape[1],int(x1))]=255
    d=base(path,'raster',3.0)
    arrows=detect_arrows(analysis);lines=detect_lines(analysis)
    attached=reconcile(arrows,lines,d['tolerance'])
    d.update(segments=lines['segments'],dots=lines['dots'],arrows=attached['arrows'],skeleton_pixels=lines['skeleton_pixels'])
    d['warnings'].extend(attached['warnings'])
    d['raster_input_policy']='supplied text masks only; arrows never erased from independent line branch'
    d['coordinate_frame']='pixels-top-left'
    d['pixel_shape']=list(array.shape)
    d['pixel_sha256']=hashlib.sha256(array.tobytes()).hexdigest()
    for arrow in d['arrows']:
        x0,y0,x1,y1=arrow['bbox']
        arrow['pixel_sha256']=hashlib.sha256(array[y0:y1,x0:x1].tobytes()).hexdigest()
        arrow['source_sha256']=d['input_sha256']
        arrow['transform_to_source_pixels']=[1,0,0,1,x0,y0]
    d['warnings'].append('experimental_raster_requires_reference_review')
    return d


def extract(path,*,page=0,masks=()):
    path=Path(path)
    if path.stat().st_size>30_000_000:raise ValueError('Local pilot file bound exceeded')
    if path.suffix.lower()=='.pdf':return pdf(path,page)
    if path.suffix.lower()=='.dxf':return dxf(path)
    if path.suffix.lower() in ('.png','.jpg','.jpeg','.tif','.tiff'):return raster(path,masks=masks)
    raise ValueError('Unsupported local diagram format')
