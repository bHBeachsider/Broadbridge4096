"""Bounded CPU raster experiment: independent original-pixel arrows and lines.

Templates are geometric proposals, not engineering truth. No learning, model
weights, pixel erasure/reconstruction or external services. Weak/ambiguous marks
remain unclaimed. Provenance points to the original pixels, not a cleaned image.
"""
import hashlib
from math import cos, sin, radians, hypot, dist, pi, isfinite

import cv2
import numpy as np
from skimage.morphology import skeletonize

from .geometry_contract import projection


def binary(image):
    if image.ndim not in (2,3) or image.shape[0]*image.shape[1]>4_000_000:
        raise ValueError('Bounded raster array required')
    gray=image if image.ndim==2 else cv2.cvtColor(image[:,:,:3],cv2.COLOR_RGB2GRAY)
    return (gray<128).astype('uint8')*255


def blobs(image):
    mask=binary(image); candidates=[]
    for size in (3,5):
        opened=cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(size,size)))
        contours,_=cv2.findContours(opened,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area=cv2.contourArea(contour); perimeter=cv2.arcLength(contour,True)
            x,y,w,h=cv2.boundingRect(contour)
            if not 5<=area<=600 or not perimeter or max(w,h)>65 or min(w,h)<3: continue
            candidates.append((contour,(x,y,w,h),area,perimeter))
    if len(candidates)>128: raise ValueError('Raster mark candidate bound exceeded')
    return mask,candidates


def detect_arrows(image, *, exclude_regions=()):
    for rect in exclude_regions:
        if (len(rect)!=4 or any(type(v) not in (int,float) or not isfinite(v) for v in rect)
                or rect[0]>rect[2] or rect[1]>rect[3]):
            raise ValueError('Invalid excluded text region')
    mask,candidates=blobs(image); found=[]
    for contour,(x,y,w,h),area,perimeter in candidates:
        if 4*pi*area/perimeter**2>.78 and max(w,h)/min(w,h)<1.3: continue
        m=cv2.moments(contour)
        if not m['m00']: continue
        cx,cy=m['m10']/m['m00'],m['m01']/m['m00']
        x0,y0=max(0,x-4),max(0,y-4);x1,y1=min(mask.shape[1],x+w+4),min(mask.shape[0],y+h+4)
        if any(x0<r[2] and x1>r[0] and y0<r[3] and y1>r[1] for r in exclude_regions):
            continue  # Exclude a whole ambiguous candidate, never alter its pixels.
        original=mask[y0:y1,x0:x1]>0; fits=[]
        for length in (5,8,12,18,20,24):
            if not .65*max(w,h)<=length<=1.8*max(w,h): continue
            for angle in range(0,360,15):
                u,v=cos(radians(angle)),sin(radians(angle))
                best=None
                for sx in (-1,0,1):
                    for sy in (-1,0,1):
                        center=np.array([cx-x0+sx,cy-y0+sy])
                        tip=center+length*2/3*np.array([u,v]); base=center-length/3*np.array([u,v])
                        half=length*.335*np.array([-v,u])
                        polygon=np.rint([tip,base+half,base-half]).astype('int32')
                        template=np.zeros(original.shape,dtype='uint8');cv2.fillPoly(template,[polygon],255)
                        # The through-pipe is a matching hypothesis, never written
                        # back into either original pixels or the line detector.
                        a=np.rint(center-70*np.array([u,v])).astype(int);b=np.rint(center+70*np.array([u,v])).astype(int)
                        cv2.line(template,tuple(a),tuple(b),255,2)
                        predicted=template>0; union=np.count_nonzero(original|predicted)
                        score=np.count_nonzero(original&predicted)/union if union else 0
                        if best is None or score>best[0]:
                            best=(score,(tip+np.array([x0,y0])).tolist(),(base+np.array([x0,y0])).tolist(),angle)
                fits.append(best)
        if not fits: continue
        fits.sort(reverse=True,key=lambda z:z[0]); best=fits[0]
        opposite=max((f[0] for f in fits if abs((f[3]-best[3]+180)%360-180)>90),default=0)
        if best[0]<.70 or best[0]-opposite<.08: continue
        proposed={'tip':best[1],'base':best[2],'bbox':[x0,y0,x1,y1],
                  'pixel_sha256':hashlib.sha256(image[y0:y1,x0:x1].tobytes()).hexdigest(),
                  'coordinate_frame':'pixels-top-left','template_iou':best[0],
                  'source':'original-pixels:contour-rotated-template','segment_id':None}
        if any(dist(proposed['tip'],a['tip'])<5 and dist(proposed['base'],a['base'])<5 for a in found): continue
        proposed['id']='a'+str(len(found));found.append(proposed)
    return found


def detect_lines(image):
    from .geometry_extractors import merge_lines
    mask=binary(image); sk=skeletonize(mask>0)
    lines=cv2.HoughLinesP(sk.astype('uint8')*255,1,np.pi/180,threshold=15,minLineLength=16,maxLineGap=2)
    raw=[] if lines is None else [(list(map(float,v[:2])),list(map(float,v[2:]))) for v in lines[:,0,:]]
    segments=[{'id':'s'+str(i),'start':a,'end':b,'source':'unchanged-skeleton-hough'} for i,(a,b) in enumerate(merge_lines(raw))]
    dots=[]
    for _,(x,y,w,h),area,perimeter in blobs(image)[1]:
        # A 2px crossing leaves a tiny round opening artifact. A filled dot needs
        # a resolvable disk, not merely the opening's apparent circularity.
        if min(w,h)>=6 and 4*pi*area/perimeter**2>.8 and max(w,h)/min(w,h)<1.3:
            p=[x+(w-1)/2,y+(h-1)/2]
            if not any(dist(p,d['point'])<3 for d in dots):
                dots.append({'point':p,'radius':max(w,h)/2,'source':'original-raster-blob'})
    return {'segments':segments,'skeleton_pixels':int(sk.sum()),'dots':dots}


def reconcile(arrows, lines, tolerance):
    output=[];warnings=[]
    for arrow in arrows:
        r=dict(arrow); scores=[];v=[r['tip'][k]-r['base'][k] for k in (0,1)];vn=hypot(*v)
        for s in lines['segments']:
            w=[s['end'][k]-s['start'][k] for k in (0,1)];wn=hypot(*w)
            gap=max(projection(r[k],s['start'],s['end'])[1] for k in ('base','tip'))
            if vn and wn and gap<=tolerance and abs(sum(a*b for a,b in zip(v,w))/(vn*wn))>.95:
                scores.append((gap,s['id']))
        scores.sort();unique=bool(scores) and (len(scores)==1 or scores[1][0]-scores[0][0]>.5)
        r['segment_id']=scores[0][1] if unique else None
        r['attachment_blocked']=not unique
        if not unique: warnings.append('unresolved_raster_arrow_attachment:'+r['id'])
        output.append(r)
    return {'arrows':output,'warnings':warnings}
