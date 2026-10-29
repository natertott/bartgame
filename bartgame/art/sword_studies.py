"""Five native sword studies; opt-in prototypes, never the default artwork.

Every body and weapon is authored on legal32x32 indexed canvases. Feet stay
anchored at(16,32). Torso/root/head poses and the actual hand drive a matching
blade; native contact masks contain only visible distal steel/cutting trails.
No high-resolution images, filtered reductions or imported game pixels enter.
"""
from functools import lru_cache
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import reboot_core as C

FACES=('n','e','s','w')
FORWARD={'n':(0,-1),'e':(1,0),'s':(0,1),'w':(-1,0)}
BASE_ANGLE={'n':-90,'e':0,'s':90,'w':180}
# Eight authored phases: ready, load, release, cutA, cutB, followA, followB,
# recover. Profiles differ in the physical gesture as well as its timing.
_PROFILES={
 1:dict(id=1,slug='planted-slash',name='Planted slash',
  description='A compact planted cut: small counter-turn, quick contact and a firm return.',
  durations=[2,2,1,2,2,2,2,3],active_flags=[False,False,True,True,True,True,False,False],
  angles=[-92,-85,-48,-8,34,66,72,47],length=16,
  weight=[0,-1,0,1,1,1,0,0],twist=[0,-1,-1,0,1,2,1,0],
  crouch=[0,1,1,0,0,0,1,0],step=[0,0,0,1,1,1,0,0],spread=[0,0,0,0,0,0,0,0]),
 2:dict(id=2,slug='broad-sweep',name='Broad sweep',
  description='A hip-led sweep: planted rear root, turning chest and a broader readable arc.',
  durations=[2,2,1,2,5,2,3,3],active_flags=[False,False,True,True,True,True,False,False],
  angles=[-114,-108,-66,-24,0,65,91,56],length=18,
  weight=[0,-1,-1,1,2,2,1,0],twist=[0,-2,-2,0,2,3,2,0],
  crouch=[0,1,1,0,0,1,1,0],step=[0,0,0,1,2,2,1,0],spread=[0,1,1,2,2,2,1,0]),
 3:dict(id=3,slug='step-and-cut',name='Step-and-cut',
  description='A deliberate forward root step and diagonal cut; drawn footwork has no world lunge.',
  durations=[2,2,2,3,2,2,2,3],active_flags=[False,False,True,True,True,False,False,False],
  angles=[-88,-78,-38,-4,31,51,43,27],length=17,
  weight=[0,-1,0,2,3,2,1,0],twist=[0,-1,-1,0,1,1,0,0],
  crouch=[0,1,1,0,0,1,1,0],step=[0,0,1,3,3,3,1,0],spread=[0,0,0,1,1,1,0,0]),
 4:dict(id=4,slug='overhand-chop',name='Overhand chop',
  description='A rooted overhead load, decisive downstroke and compressed impact pose.',
  durations=[3,3,2,2,3,2,3,4],active_flags=[False,False,False,True,True,False,False,False],
  angles=[-88,-68,-51,-12,23,37,31,24],length=18,
  weight=[0,-1,-1,1,2,2,1,0],twist=[0,-1,-1,0,1,1,0,0],
  crouch=[0,2,1,0,2,2,1,0],step=[0,0,0,1,2,2,1,0],spread=[0,1,1,1,2,2,1,0]),
 5:dict(id=5,slug='flowing-backhand',name='Flowing backhand',
  description='A reverse-direction cut with a low cross-body load and a flowing shoulder follow-through.',
  durations=[2,2,1,2,3,3,3,2],active_flags=[False,False,True,True,True,True,False,False],
  angles=[91,104,67,24,-24,-71,-86,-50],length=17,
  weight=[0,-1,-1,0,2,2,1,0],twist=[0,2,2,1,-1,-3,-2,0],
  crouch=[0,1,1,0,0,1,1,0],step=[0,0,0,1,2,2,1,0],spread=[0,1,1,1,2,2,1,0]),
}


def profile(variant):
    """Public metadata; durations are GBA logic updates, active_flags gates damage."""
    p=_PROFILES[int(variant)]
    return {key:(list(p[key]) if isinstance(p[key],list) else p[key])
            for key in ('id','slug','name','description','durations','active_flags')}


def blank():return Image.new('P',(32,32),0)


def ink_rows(im):
    return [''.join(format(im.getpixel((x,y)),'x') for x in range(im.width))
            for y in range(im.height)]


def stamp(dest,source,xy):
    alpha=Image.new('L',source.size)
    alpha.putdata([255 if value else 0 for value in source.tobytes()])
    dest.paste(source,xy,alpha)


def _line(d,points,ink,width=1):
    d.line(points,fill=1,width=width+2)
    d.line(points,fill=ink,width=width)


def _arm(d,start,elbow,grip,near):
    d.line([start,elbow,grip],fill=1,width=3)
    d.line([start,elbow,grip],fill=10 if near else 9,width=1)
    d.point(grip,fill=10 if near else 9)


def _pose(variant,face,phase):
    assert face in FACES and 0<=phase<8
    p=_PROFILES[int(variant)];fx,fy=FORWARD[face];tx,ty=-fy,fx
    w=p['weight'][phase];tw=p['twist'][phase];squat=p['crouch'][phase]
    # Feet are independently planted; pelvis, chest and head describe a
    # connected weight transfer rather than translating an unchanged sprite.
    pelvis=(16+round(fx*w*.55+tx*tw*.24),26+round(fy*w*.35)+squat//2)
    chest=(16+round(fx*w*.9+tx*tw*.45),22+round(fy*w*.55)+squat)
    head=(8+round(fx*w*.9+tx*tw*.65),10+round(fy*w*.65)+squat)
    # The flower lags the leading shoulder by a pixel in the release, then
    # follows it. Draw a tiny row-wise tilt; never rotate/scale a bitmap.
    tilt=max(-1,min(1,round((tx*tw+fx*w)/2)))
    step=p['step'][phase];spread=p['spread'][phase]
    left=(11-spread,31);right=(21+spread,31)
    if face=='e':left=(11-spread,30 if step else 31);right=(21+step,31)
    elif face=='w':left=(11-step,31);right=(21+spread,30 if step else 31)
    elif face=='n':left=(11-spread,31);right=(21+spread,31-step)
    elif face=='s':left=(11-spread,31-step);right=(21+spread,31)
    shoulders=((chest[0]-3,chest[1]+1),(chest[0]+3,chest[1]+1))
    hand0={'n':(24,16),'e':(24,23),'s':(20,25),'w':(8,23)}[face]
    if variant==5 and face=='n':hand0=(8,16)  # visible cross-body backhand load
    # Coil/release grip follows its shoulder and varies slightly through the
    # arc. North lives beyond the flower's right edge, never on the back.
    hand=(hand0[0]+round(fx*w*.65+tx*tw*.45),
          hand0[1]+round(fy*w*.4+ty*tw*.35)+squat//2)
    if variant==4:
        # Overhead load uses both hands and a genuinely raised weapon grip.
        raise_=(-1,-3,-4,-2,0,1,0,0)[phase]
        hand=(hand[0],hand[1]+raise_)
    face_for_head=face
    if variant in (2,5) and phase in (1,5):
        # A quarter-turn at the ends shows the body winding and following;
        # the contact centre keeps the original combat-facing silhouette.
        order=('n','e','s','w');idx=order.index(face)
        side=(-1 if phase==1 else 1)*(1 if variant==2 else -1)
        face_for_head=order[(idx+side)%4]
    return dict(pelvis=pelvis,chest=chest,head=head,tilt=tilt,left=left,right=right,
                shoulders=shoulders,hand=hand,head_face=face_for_head,
                twist=tw,squat=squat,step=step)


@lru_cache(maxsize=None)
def _body_frame(variant,face,phase):
    q=_pose(variant,face,phase);im=blank();d=ImageDraw.Draw(im)
    px,py=q['pelvis'];cx,cy=q['chest'];left,right=q['left'],q['right']
    # Back root, bent knees and planted toes are authored separately.
    for foot,side in ((left,-1),(right,1)):
        knee=(round((px+foot[0])/2)+side,py+2)
        _line(d,[(px+side,py-1),knee,(foot[0]+(1 if side<0 else -1),foot[1]),foot],9,1)
        d.point((foot[0]+(1 if side<0 else -1),foot[1]-1),fill=12)
    # Chest and leaf-tunic counter-rotate around the planted hips.
    d.polygon([(cx-2,cy-2),(cx+2,cy-2),(cx+3,cy+3),(px+2,py+1),
               (px,py),(px-3,py+1),(cx-3,cy+2)],fill=1)
    d.polygon([(cx-1,cy-1),(cx+1,cy-1),(cx+2,cy+2),(px+1,py),
               (px-1,py-1),(px-2,py)],fill=8)
    d.line([(cx-1,cy),(px-1,py-1)],fill=10,width=2)
    d.line([(cx+1,cy),(px+1,py-1)],fill=9)
    # Free leaf is a counterweight. The cutting arm is connected through an
    # elbow, not pasted as a floating hand at the old constant anchor.
    shoulder=q['shoulders'][1 if face!='w' else 0]
    grip=q['hand'];gx,gy=grip
    elbow=(round((shoulder[0]+gx)/2)+(1 if face!='w' else -1),
           round((shoulder[1]+gy)/2)+1)
    other=q['shoulders'][0 if face!='w' else 1]
    counter=-q['twist'];free=(other[0]-3 if face!='w' else other[0]+3,
                            min(29,other[1]+3+abs(counter)//2))
    if variant==4 and phase in (1,2,3):
        free=(gx-2 if face!='w' else gx+2,gy+2)
    _arm(d,other,(round((other[0]+free[0])/2),other[1]+2),free,False)
    _arm(d,shoulder,elbow,grip,face!='n')
    # Flower is redrawn at native size; limited row offsets articulate a
    # one-pixel tilt while preserving its petal cluster grammar.
    head=C.hero(q['head_face'],0).crop((0,0,16,14))
    hx,hy=q['head'];tilt=q['tilt']
    for y in range(14):
        shift=tilt if y<5 else 0 if y<10 else -tilt
        for x in range(16):
            ink=head.getpixel((x,y))
            xx,yy=hx+x+shift,hy+y
            if ink and 0<=xx<32 and 0<=yy<32:im.putpixel((xx,yy),ink)
    # Front-side palm reconnects visibly after the flower overlap. North's
    # hand remains far-side, with its distal sword exposed beyond the head.
    if face!='n':d.point(grip,fill=10)
    return im


def body_frame(variant,face,phase):return _body_frame(int(variant),face,int(phase)).copy()


def hand(variant,face,phase):
    x,y=_pose(int(variant),face,int(phase))['hand']
    return (x-16,y-32)


def _angle(variant,face,phase):
    p=_PROFILES[int(variant)];side=-1 if face in ('n','w') else 1
    # A front-view overhead lift projects above the flower before the
    # downstroke; reusing a rotated side-view arm would only wave sideways.
    if variant==4 and face=='s':
        return math.radians((-100,-94,-75,35,95,113,94,55)[phase])
    return math.radians(BASE_ANGLE[face]+side*p['angles'][phase])


@lru_cache(maxsize=None)
def _parts(variant,face,phase):
    p=_PROFILES[int(variant)];live=p['active_flags'][phase]
    a=_angle(variant,face,phase);length=p['length'];ux,uy=math.cos(a),math.sin(a)
    def point(radius,angle=a):return (round(math.cos(angle)*radius),round(math.sin(angle)*radius))
    tip=point(length);proximal=point(4);guardc=point(1);pommel=point(-2)
    nx,ny=-uy,ux
    guard=[(round(guardc[0]+nx*r),round(guardc[1]+ny*r)) for r in (-2,2)]
    # Live trails show the short just-completed segment of the cutting edge,
    # never a whole-circle range contour or full opaque fan.
    trail=[]
    if live:
        previous=_angle(variant,face,max(0,phase-1))
        arc_limit={1:42,2:56,3:34,4:38,5:52}[variant]
        sweep=max(-math.radians(arc_limit),min(math.radians(arc_limit),a-previous))
        for i in range(7):
            t=i/6;angle=a-sweep*(1-t)
            trail.append(point(length-1,angle))
    pts=[tip,proximal,pommel,*guard,*trail,(0,0)]
    minx=min(x for x,y in pts)-2;miny=min(y for x,y in pts)-2
    maxx=max(x for x,y in pts)+2;maxy=max(y for x,y in pts)+2
    assert maxx-minx<32 and maxy-miny<32,(variant,face,phase,'effect does not fit')
    def local(pt):return (pt[0]-minx,pt[1]-miny)
    im=blank();d=ImageDraw.Draw(im);damage=Image.new('1',(32,32),0)
    cutting=blank();cd=ImageDraw.Draw(cutting)
    # Anticipation/recovery steel is subdued. Only active poses receive a
    # bright cutting edge and short ivory stroke.
    edge=8 if live else 6
    if trail:
        ld=[local(pt) for pt in trail]
        # The trail is a faded, tapered ribbon behind the leading steel.
        # No white perpendicular cap may turn the sword into an axe/hook.
        ribbon=blank();rd=ImageDraw.Draw(ribbon)
        widths=(1,2,3,3,2,1) if variant==2 else (1,1,2,2,2,1)
        for i,width in enumerate(widths):
            rd.line(ld[i:i+2],fill=5 if i<3 else 6,width=width)
        stamp(im,ribbon,(0,0))
        damage.putdata([bool(value) for value in ribbon.tobytes()])
    cd.line([local(proximal),local(tip)],fill=1,width=3)
    cd.line([local(proximal),local(tip)],fill=edge,width=1)
    if live:cd.point(local(tip),fill=15)
    # A consistent bevel belongs to the steel, not a decorative glow halo.
    normal=(round(nx),round(ny))
    if normal[0]+normal[1]>0:normal=(-normal[0],-normal[1])
    for radius in range(5,length):
        x,y=local(point(radius));at=(x+normal[0],y+normal[1])
        if 0<=at[0]<32 and 0<=at[1]<32 and cutting.getpixel(at):cd.point(at,fill=7 if live else 5)
    if live:
        pixels=damage.load()
        for y in range(32):
            for x in range(32):
                if cutting.getpixel((x,y)):pixels[x,y]=1
    stamp(im,cutting,(0,0))
    d.line([local(point(1)),local(point(4))],fill=7 if live else 5,width=1)
    d.line([local(pommel),local((0,0))],fill=10,width=2)
    d.line([local(guard[0]),local(guard[1])],fill=13,width=1)
    d.point(local(pommel),fill=13)
    hx,hy=hand(variant,face,phase);origin=(hx+minx,hy+miny)
    # Far-side north equipment disappears precisely beneath the current
    # flower silhouette; hidden steel never enlarges contact geometry.
    if face=='n':
        body=_body_frame(variant,face,phase)
        for y in range(32):
            for x in range(32):
                bx=x+origin[0]+16;by=y+origin[1]+32
                if 0<=bx<32 and 0<=by<25 and body.getpixel((bx,by)):
                    im.putpixel((x,y),0);damage.putpixel((x,y),0)
    if live:
        assert damage.getbbox(),(variant,face,phase,'active edge hidden')
        assert all(not damage.getpixel((x,y)) or im.getpixel((x,y))
                   for y in range(32) for x in range(32)),(variant,face,phase,'invisible damage')
    return im,damage,origin


def fx_frame(variant,face,phase):return _parts(int(variant),face,int(phase))[0].copy()


def damage_mask(variant,face,phase):return _parts(int(variant),face,int(phase))[1].copy()


def geometry(variant):
    p=profile(variant);origins=[];bounds=[];hands=[]
    for face in FACES:
        oo=[];bb=[];hh=[]
        for phase in range(8):
            im,mask,origin=_parts(int(variant),face,phase);box=mask.getbbox()
            oo.append(list(origin));hh.append(list(hand(variant,face,phase)))
            bb.append([origin[0]+box[0],origin[1]+box[1],
                       origin[0]+box[2]-1,origin[1]+box[3]-1] if box else [0,0,0,0])
        origins.append(oo);bounds.append(bb);hands.append(hh)
    return {'origins':origins,'bounds':bounds,'hands':hands,
            'durations':p['durations'],'active_flags':p['active_flags']}


def preview(out):
    """Source-only diagnostics. Not substituted for actual mGBA recordings."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default();rows=[]
    for variant in range(1,6):
        p=profile(variant);g=geometry(variant)
        screen=Image.new('RGB',(8*172,4*150+28),'#182028')
        draw=ImageDraw.Draw(screen);draw.text((5,5),'SOURCE ONLY: '+p['name'],font=font,fill='#f0d898')
        phases=[]
        for phase in range(8):
            phase_view=Image.new('RGB',(4*160,150),'#182028');pd=ImageDraw.Draw(phase_view)
            for row,face in enumerate(FACES):
                layer=Image.new('RGBA',(80,64),'#283828')
                floor=ImageDraw.Draw(layer);floor.ellipse((36,43,44,46),fill='#101820')
                C.paste(layer,body_frame(variant,face,phase),(24,12),C.PALETTES['hero'])
                ox,oy=g['origins'][row][phase]
                C.paste(layer,fx_frame(variant,face,phase),(40+ox,44+oy),C.PALETTES['stone'])
                enlarged=layer.convert('RGB').resize((160,128),Image.Resampling.NEAREST)
                x=phase*172;y=row*150+26
                screen.paste(enlarged,(x,y));draw.text((x+2,y+128),face+' '+str(phase)+(' LIVE' if p['active_flags'][phase] else ''),font=font,fill='#f0d898')
                phase_view.paste(enlarged,(row*160,20))
                pd.text((row*160+3,3),face+' '+str(phase)+(' LIVE' if p['active_flags'][phase] else ''),font=font,fill='#f0d898')
            phases.append(phase_view)
        screen.save(out/(p['slug']+'-source.png'));rows.append(screen)
        durations=[round(t*1000/59.7275/10)*10 for t in p['durations']]
        # Playback is a native-source preview; actual trials use emulator time.
        frames=[phases[0],*phases,phases[-1]]
        frames[0].save(out/(p['slug']+'-source.gif'),save_all=True,append_images=frames[1:],duration=[500,*durations,350],loop=0,optimize=False,disposal=2)
    board=Image.new('RGB',(1376,sum(im.height for im in rows)),'#182028');y=0
    for im in rows:board.paste(im,(0,y));y+=im.height
    board.save(out/'all-five-source.png')


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='/workspace/setup/sword-studies/source');args=ap.parse_args()
    preview(args.out)
