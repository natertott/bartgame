"""Twenty native enemy concepts, built from final 16px silhouettes.

Source art only: mechanics, actor anchors, ordinary hurt/death and hitboxes are
owned by the engine. Every variant supplies every current frame. No image is
resized to generate a pose; contours/features are placed on the native canvas.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import reboot_core as C

CONCEPTS = {
    'spitter': [
        'Waddling kettle', 'Bellows hen', 'Hollow porcelain mask',
        'Barrel organ grub', 'Trumpet bellflower', 'Inside-out umbrella',
        'Coughing pipe elbow', 'Conch-foot pilgrim', 'Trumpet tick',
        'Blinking box camera',
    ],
    'slime': [
        'Concertina mushroom', 'Tallow pudding', 'Spring walnut',
        'Loose molar', 'Leech purse', 'Puddle snail', 'Unruly boot',
        'Haunted handkerchief', 'Pear bladder', 'Scum bucket',
    ],
}
NOTES = {
    'spitter': [
        'Loop handle and broad belly identify the kettle; cheeks swell, the directional spout opens, then the body recoils.',
        'Plump hen with tiny pumping legs; the bill contracts before a seed cough and projects in the real firing direction.',
        'A pale, empty ceramic face on short rooted feet; the round mouth inflates and opens, with a visible top vent when north-facing.',
        'A squat wooden organ on grub feet; the bellows rise and brass outlet opens after the inhalation.',
        'An upright folded flower with a trumpet mouth; petals draw inward for charge and flare around the directional opening.',
        'A living inverted umbrella walks on its handle and ribs; a central nozzle flexes as the canopy pulls in and snaps outward.',
        'A broken pipe section with two dripping feet; the elbow points at the target and its seam bulges before discharge.',
        'A curled shell supported by a fleshy sole; the short feeding tube contracts then flares in the actual firing direction.',
        'A squat trumpet carried by four jointed feet; the round brass bell is the clear dangerous end, with no shield implication.',
        'A box camera on two wooden legs; the lens draws in for charge and extends on release, never flashing like treasure.',
    ],
    'slime': [
        'The cap sits over accordion gills; the body compresses wide, extends tall on hop and folds again on landing.',
        'A greasy wax pudding with a bent wick and drooping eye sockets; it pools, stretches and settles without implying fire damage.',
        'A split walnut squeezes its root spring flat then extends it on hop; the shell seam is expressive, not an armored phase.',
        'A loose molar waddles on two wet roots; the crown flattens into its socket and the roots trail during a leap.',
        'A mouthy purse with leech feet; its broad clasp and angry face avoid looking like a passive coin pickup.',
        'A snail in a living puddle; the shell pitches and the eye stalks fold before the whole animal hops.',
        'An abandoned boot with two eyes in its cuff; its sole folds under the shaft then snaps long as it jumps.',
        'A knotted handkerchief with a face in the fold; its corners pull inward, billow on hop and flatten on landing.',
        'A pear-shaped swollen bladder with a pinched stem; the rubbery lower body spreads during charge and pulls tall in flight.',
        'A dented bucket animated by scum; its handle folds, liquid compresses below the rim and its sludge feet extend during the hop.',
    ],
}
EXTRA_FRAMES = {'spitter': ('charge_s', 'charge_n', 'charge_e')}
PALETTE_ALIASES = {'spitter': 'blight', 'slime': 'items', 'proj': 'fx'}


def _canvas(w=16, h=16):
    im = Image.new('P', (w, h), 0)
    return im, ImageDraw.Draw(im)


def _edge(d, points, fill, width=1):
    d.line(points, fill=1, width=width+2)
    d.line(points, fill=fill, width=width)


def _oval(d, box, fill, light=None):
    d.ellipse(box, fill=1)
    x0,y0,x1,y1 = box
    if x1-x0 > 2 and y1-y0 > 2:
        d.ellipse((x0+1,y0+1,x1-1,y1-1), fill=fill)
        if light is not None:
            d.line((x0+2,y0+1,max(x0+2,x1-3),y0+1),fill=light)
            if y1-y0 >= 5:d.point((x0+1,y0+2),fill=light)


def _feet(d, walking=False, ink=10):
    # Planted baseline stays y15. Walking moves one limb, not the entire body.
    d.line(((4,11),(3 if walking else 4,14),(1 if walking else 3,15)), fill=1, width=2)
    d.line(((10,11),(11 if walking else 10,13),(12 if walking else 11,15)), fill=1, width=2)
    d.point((2 if walking else 3,14), fill=ink)
    d.point((11,14 if walking else 15), fill=ink)


def _eyes(d, face, y=8, ink=15, angry=False):
    if face=='n':return
    xs=(5,9) if face=='s' else (10,)
    for x in xs:
        d.rectangle((x,y,x+1,y+1),fill=1)
        d.point((x,y),fill=ink)
        if angry:d.point((x-1,y-1),fill=1)


def _nozzle(d, face, action, material=11, wide=False):
    """Cardinal mouth stays at the existing projectile emission anchor.

    North ends at top y0, south at y15, east x15/y12; west mirrors east.
    Charge constricts the exit, release opens its dark interior and lower lip.
    """
    opening = action=='spit'
    charging = action=='charge'
    r=3 if wide or opening else 2
    if face=='s':
        d.polygon([(6,10),(9,10),(10 if opening else 9,13),(10,15),(5,15),(5,13)],fill=1)
        d.line((6,11,9,11),fill=material)
        if opening:
            d.rectangle((6,12,9,14),fill=2);d.line((6,12,9,12),fill=15);d.point((6,15),fill=material)
        elif charging:d.line((7,13,8,13),fill=1);d.point((6,12),fill=15)
        else:d.line((6,13,9,13),fill=material);d.line((7,14,8,14),fill=1)
    elif face=='n':
        d.polygon([(5,5),(6,1),(6,0),(9,0),(9,1),(10,5)],fill=1)
        d.line((6,2,6,5),fill=material);d.line((7,1,8,1),fill=15 if opening else material)
        if opening:d.rectangle((7,0,8,2),fill=2);d.point((6,0),fill=15);d.line((9,1,9,3),fill=material)
        elif charging:d.point((7,0),fill=material);d.point((8,0),fill=1)
        else:d.line((7,0,8,0),fill=material)
    else:
        d.polygon([(10,9),(12,10),(15,10 if opening else 11),(15,14),(12,14),(10,13)],fill=1)
        d.line((11,10,13,11),fill=material)
        if opening:
            d.line((14,11,14,13),fill=2);d.point((15,10),fill=15);d.point((15,14),fill=material)
        elif charging:d.point((14,12),fill=1);d.point((13,11),fill=15)
        else:d.line((14,11,14,13),fill=material);d.point((15,12),fill=1)


def _spitter(v, name):
    action,face=name.split('_')
    assert action in ('idle','walk','spit','charge') and face in ('n','s','e')
    im,d=_canvas();walk=action=='walk';charge=action=='charge';shot=action=='spit'
    top=2 if charge else 4 if shot else 3
    _feet(d,walk,11)
    if v==1: # Kettle: loop handle, lid, round body, bright attached metal.
        d.arc((0,5,7,12),70,290,fill=1,width=3);d.arc((1,6,6,11),70,290,fill=10,width=1)
        _oval(d,(3,top,12,13),10,11)
        d.line((4,10,5,12),fill=8);d.line((5,top+2,6,top+2),fill=15)
        d.rectangle((5,top-2,10,top),fill=1);d.line((6,top-1,9,top-1),fill=11);d.point((7,top-2),fill=15)
        _eyes(d,face,7,15,True);_nozzle(d,face,action,11)
    elif v==2: # Hen: tail, feather belly, fleshy comb, two separate chicken feet.
        d.polygon([(3,8),(0,5),(0,9),(3,12)],fill=1);d.line((1,7,3,9),fill=13)
        _oval(d,(3,top+1,12,13),7,15)
        d.polygon([(6,top+3),(3,top+5),(5,12),(8,11),(8,top+5)],fill=5)
        d.line((4,top+5,5,10),fill=14)
        d.line((8,top,8,top-2),fill=13,width=2);d.point((10,top-1),fill=14)
        _eyes(d,face,7,15,True);_nozzle(d,face,action,11)
    elif v==3: # Walking porcelain mask, stretched pale planes over dark interior.
        d.polygon([(4,top),(10,top),(13,top+4),(11,12),(8,14),(3,12),(2,7)],fill=1)
        d.polygon([(4,top+1),(9,top+1),(11,7),(10,11),(7,12),(4,11),(3,7)],fill=15)
        d.line((4,top+2,5,top+2),fill=7);d.line((10,9,9,11),fill=6)
        if face!='n':
            d.line((4,7,6,8),fill=1,width=2);d.line((9,8,10,6),fill=1)
        else:d.line((4,7,5,10),fill=7);d.line((8,6,10,9),fill=9)
        _nozzle(d,face,action,7,True)
    elif v==4: # Organ: wide wooden box and folded bellows, not a radial blob.
        d.polygon([(2,top+1),(11,top),(13,6),(12,13),(3,13),(1,10)],fill=1)
        d.rectangle((3,top+2,11,12),fill=9)
        d.line((3,top+1,10,top+1),fill=11)
        for y in (6,8,10):d.line((4,y,9,y+1),fill=3);d.point((4,y),fill=7)
        d.line((2,top+2,2,10),fill=11);d.line((11,6,11,11),fill=10)
        _eyes(d,face,5,15,True);_nozzle(d,face,action,11,True)
    elif v==5: # Bellflower: irregular petals flare/collapse; stalk toes.
        pts=[(7,top-2),(9,top),(12,top-1),(12,top+3),(14,top+5),(11,top+7),(9,13),(6,12),(2,12),(3,9),(0,7),(3,5),(4,top)]
        if charge:pts=[(7,1),(10,3),(11,6),(12,9),(10,12),(5,13),(3,10),(3,6),(5,3)]
        d.polygon(pts,fill=1)
        d.polygon([(6,top),(9,top+1),(11,top+4),(10,11),(6,12),(3,10),(3,7)],fill=13)
        d.line(((4,6),(5,4),(7,3)),fill=15,width=2);d.line(((10,7),(11,10),(9,12)),fill=6)
        d.line((4,12,2,14),fill=10);d.line((10,12,13,14),fill=9)
        _eyes(d,face,7,15,True);_nozzle(d,face,action,14,True)
    elif v==6: # Inverted umbrella with points, ribs, and bent handle feet.
        points=[(1,top+3),(3,top+1),(7,top-1),(11,top),(14,top+3),(12,top+6),(9,top+5),(7,top+8),(4,top+5),(2,top+6)]
        d.polygon(points,fill=1)
        d.polygon([(2,top+3),(7,top),(12,top+2),(10,top+4),(7,top+6),(4,top+4)],fill=12)
        d.polygon([(2,top+3),(7,top),(6,top+6),(4,top+4)],fill=14)
        d.line(((7,top),(7,top+6)),fill=7);d.line(((7,top+6),(8,13),(6,14)),fill=10,width=2)
        d.point((4,top+3),fill=15);d.point((9,top+3),fill=15)
        _nozzle(d,face,action,11)
    elif v==7: # Plumbing elbow: angular heavy pipe with an unmistakable opening.
        d.polygon([(3,top-1),(10,top-1),(10,5),(12,7),(12,12),(4,13),(2,10),(2,6)],fill=1)
        d.rectangle((4,top,9,6),fill=6);d.polygon([(3,7),(5,5),(9,6),(11,8),(10,12),(4,12),(3,10)],fill=5)
        d.line((4,top,8,top),fill=15);d.line(((4,6),(3,8),(4,10)),fill=7)
        d.line((8,top+1,8,5),fill=3);d.line((5,12,5,14),fill=13)
        _eyes(d,face,7,15,True);_nozzle(d,face,action,7,True)
    elif v==8: # Shell and foot: offset coil, triangular curl and a soft forward sole.
        d.polygon([(1,12),(4,10),(11,10),(14,12),(12,14),(2,14)],fill=1)
        d.line((3,12,11,12),fill=7,width=2)
        d.polygon([(2,8),(3,3 if charge else 4),(8,1),(11,4),(11,9),(8,12),(4,11)],fill=1)
        d.polygon([(3,7),(4,4),(8,2),(10,5),(9,9),(6,10),(4,9)],fill=11)
        d.line(((5,7),(5,5),(8,4),(9,7),(7,8)),fill=8)
        d.point((5,4),fill=15);d.point((4,5),fill=15)
        _eyes(d,face,9,15);_nozzle(d,face,action,7)
    elif v==9: # Trumpet-tick: long folded tube plus jointed legs and an oversized bell.
        for x in (3,10):
            d.line(((x,7),(x-2,10),(x-2 if walk else x-1,14)),fill=1,width=2)
            d.point((x-2,11),fill=10)
        d.polygon([(3,top+2),(6,top),(10,top+1),(12,6),(9,9),(5,9)],fill=1)
        d.line(((5,top+2),(7,top+1),(10,top+3),(8,7),(5,7)),fill=11,width=2)
        d.point((5,top+1),fill=15)
        d.line((5,9,8,11),fill=10,width=2)
        _eyes(d,face,6,15,True);_nozzle(d,face,action,11,True)
    elif v==10: # Box camera: square shoulders, top viewfinder and telescoping lens.
        d.rectangle((2,top+1,12,12),fill=1);d.rectangle((3,top+2,11,11),fill=9)
        d.line((3,top+2,10,top+2),fill=11);d.line((3,top+3,3,8),fill=15)
        d.rectangle((5,top-1,9,top),fill=1);d.line((6,top-1,8,top-1),fill=7)
        if face=='n':d.rectangle((4,5,10,9),fill=4);d.line((5,6,9,6),fill=7)
        else:
            d.line((4,7,5,7),fill=15);d.point((10,7),fill=15)
            d.rectangle((5,8,9,11),fill=3);d.line((6,9,8,9),fill=13)
        _nozzle(d,face,action,11,True)
    else:raise ValueError(v)
    return im


def _slime(v, name):
    assert name in ('idle','squash','jump')
    im,d=_canvas();sq=name=='squash';jump=name=='jump'
    if v==1: # Concertina mushroom.
        captop=6 if sq else 1 if jump else 3
        base=10 if sq else 9 if jump else 9
        d.polygon([(2,base),(3,captop+2),(6,captop),(10,captop),(13,captop+2),(14,base),(12,base+1),(3,base+1)],fill=1)
        d.polygon([(3,base-1),(4,captop+2),(7,captop+1),(10,captop+1),(12,captop+3),(13,base-1)],fill=11)
        d.line((5,captop+2,9,captop+2),fill=12);d.point((5,captop+3),fill=15)
        if sq:
            d.line((3,12,12,12),fill=15);d.line((2,14,13,14),fill=1);d.point((5,13),fill=1);d.point((10,13),fill=1)
        else:
            d.polygon([(5,base),(10,base),(11,14),(9,15),(5,15),(4,14)],fill=1)
            d.rectangle((6,base+1,9,14),fill=15)
            for y in range(base+2,14,2):d.line((5,y,10,y),fill=9)
            d.point((6,base+2),fill=1);d.point((9,base+2),fill=1)
    elif v==2: # Tallow pudding.
        top=9 if sq else 2 if jump else 5
        d.polygon([(1 if sq else 3,13),(3,top+3),(5,top),(10,top),(12,top+3),(14 if sq else 12,13),(14,15),(10,15),(9,14),(5,15),(1,15)],fill=1)
        d.polygon([(3,12),(4,top+3),(6,top+1),(9,top+1),(11,top+3),(12,14),(10,14),(8,13),(4,14)],fill=15)
        d.line((5,top+2,8,top+2),fill=12);d.line((10,top+4,11,12),fill=14)
        d.line(((7,top),(7,top-2),(8,top-3)),fill=1)
        ey=top+3;d.point((5,ey),fill=1);d.point((9,ey+1),fill=1);d.line((6,ey+3,8,ey+3),fill=8)
    elif v==3: # Spring walnut.
        top=7 if sq else 1 if jump else 4
        _oval(d,(2 if sq else 3,top,13 if sq else 12,11 if jump else 13),10,12)
        d.line(((7,top+1),(8,top+3),(7,top+5),(8,top+7)),fill=8)
        d.point((5,top+3),fill=15);d.point((10,top+3),fill=15)
        if jump:
            d.line(((6,11),(4,12),(10,13),(5,14),(10,15)),fill=1,width=2)
            d.point((5,12),fill=7);d.point((9,14),fill=7)
        else:
            d.line((4,14,11,14),fill=1);d.line((5,15,10,15),fill=7)
    elif v==4: # Loose molar.
        top=8 if sq else 1 if jump else 4
        d.polygon([(2,top+2),(3,top),(6,top+1),(9,top),(12,top+1),(13,top+4),(11,12),(10,15),(8,14),(6,15),(4,13)],fill=1)
        d.polygon([(3,top+2),(4,top+1),(6,top+2),(9,top+1),(11,top+2),(11,top+5),(9,11),(6,12),(4,10)],fill=15)
        d.line((4,top+2,5,top+2),fill=12);d.line((9,top+2,10,top+2),fill=12)
        d.point((5,top+4),fill=1);d.point((10,top+4),fill=1)
        d.line((6,top+6,9,top+6),fill=8)
        if jump:d.line((5,11,4,15),fill=7);d.line((10,11,11,15),fill=9)
        elif sq:d.line((2,15,13,15),fill=8)
    elif v==5: # Leech purse.
        top=8 if sq else 2 if jump else 5
        d.polygon([(3,top),(11,top),(13,top+3),(13,13),(11,15),(3,15),(1,13),(2,top+3)],fill=1)
        d.polygon([(4,top+1),(10,top+1),(11,top+3),(11,13),(4,14),(3,12),(3,top+4)],fill=9)
        d.line((4,top+2,9,top+2),fill=12);d.line((4,top+3,4,top+5),fill=11)
        d.line((4,top,10,top),fill=15);d.point((5,top-1),fill=12);d.point((9,top-1),fill=12)
        d.line((4,top+4,6,top+5),fill=1);d.line((9,top+5,11,top+4),fill=1)
        d.line((5,top+7,10,top+7),fill=1)
        if jump:d.line((3,13,1,15),fill=7);d.line((11,13,14,15),fill=7)
        elif sq:d.line((1,15,14,15),fill=7)
    elif v==6: # Puddle snail.
        shelltop=7 if sq else 2 if jump else 4
        d.polygon([(1,13),(4,11),(11,11),(14,13),(14,15),(2,15)],fill=1)
        d.line((3,13,12,13),fill=15,width=2)
        _oval(d,(3,shelltop,11,12),5,7)
        d.line(((5,shelltop+4),(5,shelltop+2),(8,shelltop+2),(9,shelltop+4),(7,shelltop+6)),fill=2)
        d.point((5,shelltop+1),fill=15)
        if sq:d.line((11,12,13,11),fill=7);d.point((14,11),fill=1)
        else:
            d.line((11,13,12,8 if jump else 10),fill=1,width=2);d.line((13,13,14,7 if jump else 9),fill=1,width=2)
            d.point((12,8 if jump else 10),fill=15);d.point((14,7 if jump else 9),fill=15)
    elif v==7: # Unruly boot.
        top=8 if sq else 1 if jump else 3
        d.polygon([(3,top),(10,top),(10,9 if jump else 12),(13,11 if jump else 12),(14,14),(13,15),(2,15),(2,12)],fill=1)
        d.polygon([(4,top+1),(9,top+1),(8,10 if jump else 12),(12,12),(12,13),(4,13),(3,12)],fill=9)
        d.line((4,top+1,8,top+1),fill=12);d.line((4,top+2,4,min(11,top+5)),fill=11)
        d.line((3,14,12,14),fill=15);d.point((5,top+3),fill=15);d.point((8,top+3),fill=15)
        if not sq:
            d.line((6,top+5,8,top+5),fill=1);d.line((5,top+7,7,top+7),fill=1)
        else:d.line((5,12,8,12),fill=1)
    elif v==8: # Folded laundry: asymmetrical square folds, never a loot star.
        top=9 if sq else 3 if jump else 6
        if sq:
            points=[(2,10),(5,9),(8,10),(12,9),(14,12),(12,14),(8,14),(5,15),(1,14)]
            light=[(3,11),(6,10),(8,11),(11,10),(12,12),(10,13),(5,14),(2,13)]
        elif jump:
            points=[(6,1),(9,2),(10,5),(13,6),(14,11),(12,15),(9,13),(6,14),(2,13),(3,9),(2,6),(5,4)]
            light=[(7,2),(8,3),(8,6),(11,7),(12,11),(11,13),(8,11),(6,12),(4,11),(5,8),(4,6),(6,5)]
        else:
            points=[(5,3),(8,4),(10,6),(13,6),(14,11),(12,15),(8,13),(4,15),(1,12),(3,9),(2,6),(5,6)]
            light=[(5,4),(7,5),(8,8),(11,7),(12,10),(11,13),(8,11),(5,13),(3,11),(5,8),(4,7),(6,7)]
        d.polygon(points,fill=1);d.polygon(light,fill=15)
        ey=12 if sq else 8 if jump else 10
        d.line((5,ey,6,ey),fill=1);d.point((10,ey),fill=1)
        d.line(((7,ey+1),(7,ey+2),(9,ey+2)),fill=14)
        d.point((6,top-1),fill=12)
    elif v==9: # Pear bladder.
        top=7 if sq else 2 if jump else 4
        d.polygon([(6,top),(9,top),(10,top+3),(13,top+5),(14,13),(12,15),(3,15),(1,13),(2,top+5),(5,top+3)],fill=1)
        d.polygon([(6,top+1),(8,top+1),(9,top+4),(12,top+6),(12,13),(10,14),(4,14),(3,12),(4,top+6)],fill=6)
        d.line(((6,top+2),(6,top+4),(4,top+6)),fill=7);d.point((7,top+2),fill=15)
        d.line(((7,top),(7,top-2),(9,top-3)),fill=9)
        d.point((5,top+6),fill=1);d.point((10,top+6),fill=1)
        if sq:d.line((6,14,9,14),fill=2)
        else:d.line((6,top+8,9,top+8),fill=2)
    elif v==10: # Bucket of scum: squared rim and hinged handle are distinct.
        top=8 if sq else 3 if jump else 5
        d.arc((3,top-4,12,top+5),180,360,fill=1,width=2);d.point((5,top-3),fill=15)
        d.polygon([(2,top),(13,top),(11,13),(10,14),(4,14),(3,12)],fill=1)
        d.polygon([(3,top+1),(12,top+1),(10,12),(5,13),(4,11)],fill=14)
        d.line((3,top+1,11,top+1),fill=15);d.line((5,top+2,5,11),fill=12)
        d.line((5,top+3,6,top+3),fill=1);d.point((10,top+3),fill=1)
        if jump:
            d.line(((5,12),(3,14),(2,15)),fill=3,width=2);d.line(((10,12),(11,14),(13,15)),fill=7,width=2)
        else:d.line((3,15,12,15),fill=3);d.point((4,14),fill=7)
    else:raise ValueError(v)
    return im


def _seed(v):
    # Every seed is one solid projectile; tiny highlights are attached and
    # elongated tails indicate travel, never four-point treasure glitter.
    im,d=_canvas(8,8)
    if v==1:
        _oval(d,(2,2,6,6),9,11);d.line((1,4,2,3),fill=4);d.point((4,3),fill=12)
    elif v==2:
        d.polygon([(1,3),(4,1),(6,3),(5,6),(3,6)],fill=1);d.polygon([(2,3),(4,2),(5,3),(4,5),(3,5)],fill=10);d.point((3,3),fill=12)
    elif v==3:
        d.polygon([(1,3),(5,1),(6,3),(5,6),(2,5)],fill=1);d.line(((2,3),(4,2),(5,3)),fill=12);d.line((3,4,5,4),fill=9)
    elif v==4:
        d.rectangle((2,2,6,5),fill=1);d.line((3,2,5,2),fill=11);d.rectangle((3,3,5,4),fill=8);d.point((1,4),fill=5)
    elif v==5:
        # A narrow bronze pod with one attached tail, not a four-arm flare.
        d.polygon([(3,1),(5,1),(6,2),(6,4),(4,6),(2,5),(2,3)],fill=1)
        d.polygon([(3,3),(4,2),(5,2),(5,4),(4,5),(3,4)],fill=6)
        d.point((4,2),fill=11);d.point((5,3),fill=9)
        d.point((1,5),fill=1);d.point((1,6),fill=4)
    elif v==6:
        d.polygon([(1,2),(5,2),(6,4),(3,6),(2,5)],fill=1);d.line(((2,3),(4,3),(4,4),(3,5)),fill=10);d.point((2,3),fill=12)
    elif v==7:
        _oval(d,(2,2,6,6),6,10);d.line((1,3,3,4),fill=4);d.point((4,3),fill=11)
    elif v==8:
        d.polygon([(1,4),(4,1),(6,2),(6,5),(4,6)],fill=1);d.line(((3,3),(4,2),(5,3),(4,5)),fill=11);d.point((4,3),fill=12)
    elif v==9:
        d.polygon([(1,3),(3,2),(6,3),(6,5),(3,6),(2,5)],fill=1);d.line((2,3,5,3),fill=11);d.line((3,4,5,4),fill=9)
    else:
        d.polygon([(1,3),(3,1),(6,2),(6,5),(4,6),(2,5)],fill=1);d.line((3,2,5,2),fill=12);d.line((2,3,4,4),fill=13);d.point((4,5),fill=14)
    return im


def frame(family, variant, name):
    assert 1 <= variant <= 10, variant
    if family=='spitter':im=_spitter(variant,name)
    elif family=='slime':im=_slime(variant,name)
    elif family=='proj' and name=='seed':im=_seed(variant)
    else:raise ValueError((family,name))
    assert im.mode=='P' and set(im.tobytes())<=set(range(16))
    assert im.getbbox() is not None,(family,variant,name)
    return im


def _rgba(im, family):
    if family=='slime':
        import enemy_studies_palette
        return C.rgba(im,enemy_studies_palette.colors())
    pal={'spitter':'blight','proj':'gold'}[family]
    return C.rgba(im,C.PALETTES[pal])


def source_previews(out):
    """Named source boards, all frames, scene motion and native validations."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    contracts=json.loads(Path(__file__).with_name('reboot_contracts.json').read_text())
    reports=[]
    for family in ('spitter','slime'):
        names=next(s['frames'] for s in contracts['sheets'] if s['name']==family)+list(EXTRA_FRAMES.get(family,()))
        cw=230;ch=128
        overview=Image.new('RGB',(cw*5,34+ch*2),'#101820');draw=ImageDraw.Draw(overview)
        draw.text((8,7),f'{family} mechanics / ten forms / SOURCE ART, not emulator / 1x + 3x',font=font,fill='#f0d898')
        atlas=Image.new('RGB',(260+len(names)*50,32+10*70),'#101820');ad=ImageDraw.Draw(atlas)
        ad.text((8,7),f'{family}: full native source frame inventory / 3x inspection',font=font,fill='#f0d898')
        for variant in range(1,11):
            x=((variant-1)%5)*cw;y=34+((variant-1)//5)*ch
            draw.text((x+6,y+4),f'{variant}. {CONCEPTS[family][variant-1]}',font=font,fill='#f0d898')
            canonical='idle_s' if family=='spitter' else 'idle'
            a=_rgba(frame(family,variant,canonical),family)
            big=a.resize((48,48),Image.Resampling.NEAREST)
            overview.paste(big,(x+8,y+24),big)
            for bx,(mat,ink) in enumerate((('ground',4),('blight',3),('drain',4),('stone',4))):
                tile=Image.new('RGBA',(36,48),C.PALETTES[mat][ink])
                tile.alpha_composite(a,(10,16));tile=tile.convert('RGB')
                overview.paste(tile,(x+64+bx*40,y+24))
            draw.text((x+8,y+86),'3x',font=font,fill='#b0c0a0')
            draw.text((x+64,y+86),'1x: grass / rot / hub / cave',font=font,fill='#b0c0a0')
            ad.text((6,38+(variant-1)*70),f'{variant}. {CONCEPTS[family][variant-1]}',font=font,fill='#f0d898')
            hashes=[]
            import hashlib
            for i,name in enumerate(names):
                im=frame(family,variant,name);a=_rgba(im,family)
                atlas.paste(a.resize((48,48),Image.Resampling.NEAREST),(260+i*50,33+(variant-1)*70),a.resize((48,48),Image.Resampling.NEAREST))
                ad.text((260+i*50,83+(variant-1)*70),name,font=font,fill='#b0c0a0')
                p=out/'native'/family/f'v{variant:02}'/f'{name}.png';p.parent.mkdir(parents=True,exist_ok=True);a.save(p)
                hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
                reports.append({'family':family,'variant':variant,'frame':name,'size':im.size,'opaque':sum(bool(p) for p in im.tobytes()),'sha256_indexed':hashes[-1]})
            assert len(set(hashes))==len(hashes),(family,variant,'duplicate animation frames')
        overview.save(out/f'{family}-ten-source.png');atlas.save(out/f'{family}-all-frames-source.png')
    # Chronology uses the engine's key visual states but is a source animation,
    # not a simulation of AI/physics. Clear every-frame native background.
    seq=['idle_s']*9+['walk_s','idle_s']*4+['charge_s']*6+['spit_s']*17+['idle_s']*9
    for family in ('spitter','slime'):
        sequence=seq if family=='spitter' else ['idle']*18+['squash']*18+['jump']*29+['squash']*24
        gifs=[]
        for tick,name in enumerate(sequence):
            board=Image.new('RGB',(5*152,2*108+28),'#101820');bd=ImageDraw.Draw(board)
            bd.text((6,6),f'{family} SOURCE pose chronology / NOT a game run',font=font,fill='#f0d898')
            for variant in range(1,11):
                x=(variant-1)%5*152;y=(variant-1)//5*108+28
                bd.text((x+5,y+4),f'{variant}. {CONCEPTS[family][variant-1]}',font=font,fill='#f0d898')
                a=_rgba(frame(family,variant,name),family)
                board.paste(a.resize((48,48),Image.Resampling.NEAREST),(x+12,y+29),a.resize((48,48),Image.Resampling.NEAREST))
                board.paste(a,(x+92,y+50),a)
                bd.text((x+6,y+85),name,font=font,fill='#b0c0a0')
            gifs.append(board)
        # Source viewing aid only; actual indexed frames remain the evidence.
        gifs[0].save(out/f'{family}-motion-source.gif',save_all=True,append_images=gifs[1:],duration=17,loop=0,optimize=False,disposal=2)
    # Companion seeds are the existing reflectable projectile, not a new attack.
    seeds=Image.new('RGB',(10*112,86),'#101820');sd=ImageDraw.Draw(seeds)
    sd.text((8,6),'Reflectable seed companions / source, 1x + 4x / same game hitbox and damage',font=font,fill='#f0d898')
    seed_hashes=[]
    for variant in range(1,11):
        im=frame('proj',variant,'seed');a=_rgba(im,'proj');x=(variant-1)*112
        big=a.resize((32,32),Image.Resampling.NEAREST)
        seeds.paste(big,(x+8,31),big);seeds.paste(a,(x+64,43),a)
        sd.text((x+7,67),str(variant),font=font,fill='#f0d898')
        p=out/'native'/'proj'/f'v{variant:02}'/'seed.png';p.parent.mkdir(parents=True,exist_ok=True);a.save(p)
        digest=hashlib.sha256(im.tobytes()).hexdigest();seed_hashes.append(digest)
        reports.append({'family':'proj','variant':variant,'frame':'seed','size':im.size,'opaque':sum(bool(p) for p in im.tobytes()),'sha256_indexed':digest})
    assert len(set(seed_hashes))==10,'Seeds must be distinct native designs'
    seeds.save(out/'seed-companions-source.png')
    # Native grayscale and silhouette inspection keeps material/value judgment
    # separate from color and from an unverified claim about real game scenes.
    diagnostics=Image.new('RGB',(10*96,4*88+30),'#101820');dd=ImageDraw.Draw(diagnostics)
    dd.text((7,6),'Source grayscale / silhouette check, 1x + 3x / no world rendering',font=font,fill='#f0d898')
    for row,family in enumerate(('spitter','slime')):
        for variant in range(1,11):
            name='idle_s' if family=='spitter' else 'idle';a=_rgba(frame(family,variant,name),family)
            gray=a.convert('LA').convert('RGBA');gray.putalpha(a.getchannel('A'))
            sil=Image.new('RGBA',a.size,'#f0d898');sil.putalpha(a.getchannel('A'))
            for sub,graphic in enumerate((gray,sil)):
                x=(variant-1)*96;y=30+(row*2+sub)*88
                diagnostics.paste(graphic.resize((48,48),Image.Resampling.NEAREST),(x+5,y+4),graphic.resize((48,48),Image.Resampling.NEAREST))
                diagnostics.paste(graphic,(x+65,y+26),graphic)
                dd.text((x+5,y+59),f'{family} {variant}',font=font,fill='#b0c0a0')
    diagnostics.save(out/'soft-silhouette-grayscale-source.png')
    (out/'native-validation.json').write_text(json.dumps({'frames':reports,'frame_count':len(reports),'all_native':True,'all_exact_indexed':True,'note':'Source frame completeness/geometry checks, not mGBA or visual-quality scores.'},indent=2)+'\n')
    return reports


if __name__=='__main__':
    source_previews('/workspace/setup/appearance-enemy-studies/soft')
