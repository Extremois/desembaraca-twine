"""Independent implementation of the Twine 2.12.1 SVG centerline profile.

SVG endpoint conversion follows W3C SVG implementation notes. Ellipse intersection
uses a quartic from the rational parametrization of a circle, not sampled chords.
No Twine source code is included. Stroke width and markers are outside the metric.
"""
from dataclasses import dataclass
import itertools
import math
import time

EPS=1e-6
TAU=2*math.pi


def check(deadline):
    if time.monotonic()>=deadline:
        raise TimeoutError('Geometry time allowance exceeded')


def real_roots(coeff):
    """Degree <=4 real roots, isolated using derivative monotonic intervals."""
    coeff=list(coeff)
    scale=max(map(abs,coeff),default=0)
    if scale==0: return []
    coeff=[c/scale for c in coeff]
    while len(coeff)>1 and abs(coeff[-1])<1e-12: coeff.pop()
    degree=len(coeff)-1
    if degree==0: return []
    if degree==1: return [-coeff[0]/coeff[1]]
    def value(x):
        total=0.
        for c in reversed(coeff): total=total*x+c
        return total
    bound=1+max(abs(c/coeff[-1]) for c in coeff[:-1])
    critical=sorted(x for x in real_roots([i*coeff[i] for i in range(1,len(coeff))]) if -bound<x<bound)
    points=[-bound,*critical,bound]
    roots=[x for x in critical if abs(value(x))<=1e-9]
    for lo,hi in zip(points,points[1:]):
        flo,fhi=value(lo),value(hi)
        if flo*fhi>=0: continue
        for _ in range(100):
            mid=(lo+hi)/2
            fm=value(mid)
            if fm==0 or hi-lo<1e-12*max(1,abs(mid)):
                lo=hi=mid
                break
            if flo*fm<0: hi=mid
            else: lo,flo=mid,fm
        roots.append((lo+hi)/2)
    return roots


@dataclass(frozen=True)
class Arc:
    center: tuple
    u: tuple
    v: tuple
    theta: float
    delta: float

    def point(self,t):
        angle=self.theta+t*self.delta
        return tuple(self.center[i]+self.u[i]*math.cos(angle)+self.v[i]*math.sin(angle) for i in (0,1))

    def local(self,p):
        x,y=p[0]-self.center[0],p[1]-self.center[1]
        det=self.u[0]*self.v[1]-self.u[1]*self.v[0]
        return ((x*self.v[1]-y*self.v[0])/det,(self.u[0]*y-self.u[1]*x)/det)

    def parameter(self,p):
        x,y=self.local(p)
        angle=math.atan2(y,x)
        step=(angle-self.theta)%TAU if self.delta>0 else (self.theta-angle)%TAU
        if TAU-step<1e-8: step=0
        return step/abs(self.delta)

    def contains(self,p):
        return self.parameter(p)<=1+1e-7


def svg_arc(a,b,rx,ry,phi=0,large=False,sweep=True):
    if math.dist(a,b)<EPS: return None
    co,si=math.cos(phi),math.sin(phi)
    dx,dy=(a[0]-b[0])/2,(a[1]-b[1])/2
    xp,yp=co*dx+si*dy,-si*dx+co*dy
    adjustment=xp*xp/(rx*rx)+yp*yp/(ry*ry)
    if adjustment>1:
        rx*=math.sqrt(adjustment); ry*=math.sqrt(adjustment)
    numerator=max(0,rx*rx*ry*ry-rx*rx*yp*yp-ry*ry*xp*xp)
    factor=math.sqrt(numerator/(rx*rx*yp*yp+ry*ry*xp*xp))
    if large==sweep: factor=-factor
    cxp,cyp=factor*rx*yp/ry,-factor*ry*xp/rx
    center=(co*cxp-si*cyp+(a[0]+b[0])/2,si*cxp+co*cyp+(a[1]+b[1])/2)
    first=((xp-cxp)/rx,(yp-cyp)/ry)
    last=((-xp-cxp)/rx,(-yp-cyp)/ry)
    theta=math.atan2(first[1],first[0])
    delta=math.atan2(first[0]*last[1]-first[1]*last[0],first[0]*last[0]+first[1]*last[1])
    if sweep and delta<0: delta+=TAU
    if not sweep and delta>0: delta-=TAU
    return Arc(center,(rx*co,rx*si),(-ry*si,ry*co),theta,delta)


def border(n,a,b):
    # Match the specified side priority when overlapping rectangles yield >1 hit.
    dx,dy=b[0]-a[0],b[1]-a[1]
    for axis,value,otherlo,otherhi in (
        (0,n['x'],n['y'],n['y']+n['h']),
        (0,n['x']+n['w'],n['y'],n['y']+n['h']),
        (1,n['y'],n['x'],n['x']+n['w']),
        (1,n['y']+n['h'],n['x'],n['x']+n['w'])):
        delta=(dx,dy)[axis]
        if abs(delta)<EPS: continue
        t=(value-a[axis])/delta
        p=(a[0]+t*dx,a[1]+t*dy)
        if -1e-10<=t<=1+1e-10 and otherlo-EPS<=p[1-axis]<=otherhi+EPS:
            return p
    return None


def connection(start,end):
    if start['id']==end['id']:
        x,y=start['x'],start['y']
        r=.4*min(start['w'],start['h'])
        return svg_arc((x,y+start['h']/2),(x,y),r,r,large=True)
    a=(start['x']+start['w']/2,start['y']+start['h']/2)
    b=(end['x']+end['w']/2,end['y']+end['h']/2)
    a=border(start,a,b)
    if a is None: return None
    b=border(end,a,b)
    if b is None: return None
    d=math.dist(a,b)
    if d<EPS: return None
    sweep=a[0]<b[0] or (a[0]==b[0] and a[1]<b[1])
    return svg_arc(a,b,d,.75*d,math.atan2(b[1]-a[1],b[0]-a[0]),sweep=sweep)


def arc_intersections(a,b):
    c=b.local(a.center)
    pu=b.local((a.center[0]+a.u[0],a.center[1]+a.u[1]))
    pv=b.local((a.center[0]+a.v[0],a.center[1]+a.v[1]))
    u=(pu[0]-c[0],pu[1]-c[1]); v=(pv[0]-c[0],pv[1]-c[1])
    coeff=[-1.,0.,-2.,0.,-1.]
    for k in (0,1):
        poly=(c[k]+u[k],2*v[k],c[k]-u[k])
        for i in range(3):
            for j in range(3): coeff[i+j]+=poly[i]*poly[j]
    if max(map(abs,coeff))<1e-9:
        # Same ellipse: partition arc a by endpoints of b, then test open intervals.
        stops=sorted([0.,1.]+[t for p in (b.point(0),b.point(1)) if 0<(t:=a.parameter(p))<1])
        if any(b.contains(a.point((lo+hi)/2)) for lo,hi in zip(stops,stops[1:])):
            return True,[]
        return False,[p for p in (a.point(0),a.point(1)) if b.contains(p)]
    points=[]
    angles=[2*math.atan(t) for t in real_roots(coeff)]+[math.pi]
    for angle in angles:
        p=tuple(a.center[i]+a.u[i]*math.cos(angle)+a.v[i]*math.sin(angle) for i in (0,1))
        x,y=b.local(p)
        if abs(x*x+y*y-1)<1e-7 and a.contains(p) and b.contains(p): points.append(p)
    return False,points


def through(arc,n):
    stops=[0.,1.]
    for axis,values in ((0,(n['x'],n['x']+n['w'])),(1,(n['y'],n['y']+n['h']))):
        amplitude=math.hypot(arc.u[axis],arc.v[axis])
        phase=math.atan2(arc.v[axis],arc.u[axis])
        for value in values:
            ratio=(value-arc.center[axis])/amplitude
            if -1<=ratio<=1:
                for angle in (phase+math.acos(ratio),phase-math.acos(ratio)):
                    p=tuple(arc.center[i]+arc.u[i]*math.cos(angle)+arc.v[i]*math.sin(angle) for i in (0,1))
                    t=arc.parameter(p)
                    if 0<t<1: stops.append(t)
    stops.sort()
    for lo,hi in zip(stops,stops[1:]):
        x,y=arc.point((lo+hi)/2)
        if n['x']+EPS<x<n['x']+n['w']-EPS and n['y']+EPS<y<n['y']+n['h']-EPS: return True
    return False


def counts(graph,deadline=float('inf')):
    nodes={n['id']:n for n in graph['nodes']}
    edges=list(dict.fromkeys(tuple(e) for e in graph['edges']))
    arcs=[connection(nodes[a],nodes[b]) for a,b in edges]
    ee=nn=en=0
    for a,b in itertools.combinations(nodes.values(),2):
        check(deadline)
        nn+=min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x'])>EPS and min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y'])>EPS
    for i,j in itertools.combinations(range(len(edges)),2):
        check(deadline)
        if arcs[i] is None or arcs[j] is None: continue
        overlap,points=arc_intersections(arcs[i],arcs[j])
        shared=set(edges[i])&set(edges[j])
        def normal(p):
            return any(nodes[k]['x']-EPS<=p[0]<=nodes[k]['x']+nodes[k]['w']+EPS and nodes[k]['y']-EPS<=p[1]<=nodes[k]['y']+nodes[k]['h']+EPS for k in shared)
        ee+=overlap or any(not normal(p) for p in points)
    for edge,arc in zip(edges,arcs):
        if arc is None: continue
        for k,n in nodes.items():
            check(deadline)
            if k not in edge: en+=through(arc,n)
    return [int(ee),int(nn),int(en)]
