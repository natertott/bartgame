"""Append-only native wall masks, projecting ledges, shade, ladders and falls."""
from PIL import Image, ImageDraw
import cream_style_polish as S
import cream_polish_ladders as L
import cream_polish_water as W
import cream_depth_edges as E
from cream_depth_assets import landing_path

SPECS = S.WALLS.SPECS
DIGITS='0123456789abcdef'


def rows(image,alpha=False):
    assert image.mode=='P' and image.size==(16,16)
    assert all(0<=p<16 for p in image.getdata())
    if not alpha:assert 0 not in image.getdata()
    return [''.join(DIGITS[image.getpixel((x,y))] for x in range(16)) for y in range(16)]


def underside(stage=0):
    im=Image.new('P',(32,16),3);d=ImageDraw.Draw(im)
    d.rectangle((0,0,31,3),fill=7)
    d.line((0,0,31,0),fill=8)
    d.line((0,4,31,4),fill=2)
    d.polygon([(1,5),(30,5),(28,9),(24,10),(22,8),(10,8),(7,11),(3,9)],fill=4)
    d.line([(0,5),(3,9),(7,11),(10,8)],fill=5)
    d.line([(12,7),(21,7),(25,9),(29,7)],fill=2)
    d.line((0,12,31,12),fill=2)
    if stage==2:
        d.line([(26,4),(25,6),(27,8)],fill=12)
    return im


def shade(stage=0,variant=0,vertical=0,lateral=1):
    """Shade the actual underlying native floor, retaining pressed path grain."""
    im=S.floor(stage,variant%4,variant>=4).copy()
    for y in range(16):
        for x in range(16):
            inside=True
            if lateral==0:inside=x>=2+(y//6)%2
            if lateral==2:inside=x<=13-(y//7)%2
            if vertical==2:inside=inside and y<11+(x//5)%3
            if inside:
                v=im.getpixel((x,y))
                im.putpixel((x,y), 4 if v>=5 else 3)
    # A small number of retained grain clusters describe floor under shadow,
    # never a smooth enclosed oval or a second platform.
    d=ImageDraw.Draw(im)
    if vertical==0:d.line((2 if lateral==0 else 0,0,13 if lateral==2 else 15,0),fill=2)
    if vertical==2:
        for x,y in ((3,12),(6,13),(9,12),(12,14)):
            if (lateral!=0 or x>2) and (lateral!=2 or x<13):d.point((x,y),fill=3)
    return im


def build():
    mts=[]; tables={k:[] for k in ('panels','backing','rim','drop','edge','landing','floor_toe','landing_path','climb','underside','shade','fall')}
    def add(name,im,pal,typ='SOLID',alpha=False,frames=None):
        mt=dict(name='cream_polish_'+name,pal=pal,type=typ,coll=15 if typ=='SOLID' else 0,prop=0)
        if frames:mt.update(frames=[rows(f,alpha) for f in frames],anim_speed=8)
        else:mt['art']=rows(im,alpha)
        mts.append(mt);return mt['name']
    for s in range(3):
        cb='cream_cliff%d'%s;fb='cream_floor%d'%s
        panels=[]
        for p,spec in enumerate(SPECS):
            im=S.WALLS.panel(S.STYLE,s,spec['kind'],spec['variant']).copy()
            mask=S.WALLS.panel_mask(S.STYLE,s,spec['kind'],spec['variant'])
            for y in range(im.height):
                for x in range(im.width):
                    if not mask.getpixel((x,y)):im.putpixel((x,y),0)
            names=[add('panel_s%d_p%d_%d_%d'%(s,p,x,y),im.crop((16*x,16*y,16*x+16,16*y+16)),cb,alpha=True)
                   for y in range(spec['h']) for x in range(spec['w'])]
            panels.append(dict(first=names[0],w=spec['w'],h=spec['h']))
        tables['panels'].append(panels)
        im=S.WALLS.backing(S.STYLE,s)
        tables['backing'].append([add('backing_s%d_%d_%d'%(s,x,y),im.crop((x*16,y*16,x*16+16,y*16+16)),cb)
                                  for y in range(3) for x in range(8)])
        tables['rim'].append([add('rim_s%d_v%d'%(s,v),S.rim(s,v),fb) for v in range(2)])
        tables['drop'].append([add('drop_s%d_v%d'%(s,v),S.rim(s,v,True),fb,'FLOOR') for v in range(2)])
        edges=[]
        for k,kind in enumerate(('solid_left','solid_right','drop_left','drop_right','toe')):
            im=E.edge(s,kind)
            if kind.startswith('drop_'):
                im=S.rim(s,k-2,True);d=ImageDraw.Draw(im)
                x=0 if kind=='drop_left' else 15
                d.line((x,8,x,14),fill=6 if x==0 else 3)
            edges.append(add('edge_s%d_%s'%(s,kind),im,fb if kind.startswith('drop_') else cb,
                             'FLOOR' if kind.startswith('drop_') else 'SOLID'))
        tables['edge'].append(edges)
        climbs=[]
        for k,kind in enumerate(('top','mid','bottom')):
            im=L.foot_floor(S.LADDER,s) if kind=='bottom' else L.ladder(S.LADDER,s,kind)
            climbs.append([add('climb_s%d_k%d_h%d'%(s,k,x),im.crop((x*16,0,x*16+16,16)),fb if kind=='bottom' else cb,'CLIMB') for x in range(2)])
        tables['climb'].append(climbs)
        im=underside(s)
        tables['underside'].append([add('underside_s%d_h%d'%(s,x),im.crop((x*16,0,x*16+16,16)),cb) for x in range(2)])
        shades=[[[add('shade_s%d_v%d_y%d_x%d'%(s,v,y,x),shade(s,v,y,x),fb,'FLOOR') for x in range(3)] for y in range(3)] for v in range(8)]
        tables['shade'].append(shades)
        # Terminal arrival shade is part of the same continuous cast shadow,
        # not a separate round patch. Reuse exact native contacts/fades.
        tables['landing'].append([shades[0][1 if p<3 else 2][p%3] for p in range(6)])
        tables['floor_toe'].append([shades[v][0][1] for v in range(2)])
        tables['landing_path'].append([[shades[v+4][1 if p<3 else 2][p%3] for p in range(6)] for v in range(4)])
        falls=[]
        for width in range(1,4):
            kinds=[]
            for k,kind in enumerate(('top','mid','bottom')):
                kinds.append([add('fall_s%d_w%d_k%d_x%d'%(s,width,k,x),None,'cream_water',frames=[
                    W.fall(S.STYLE,s,width,kind,phase).crop((x*16,0,x*16+16,16)) for phase in range(W.PHASES)])
                    for x in range(width)]+[None]*(3-width))
            falls.append(kinds)
        tables['fall'].append(falls)
    return mts,tables


METATILES,TABLES=build()
