"""Twenty native, mechanic-led alternatives for the two small enemy families.

Every pixel is authored on the actual 16x16 hardware canvas. Material indices
keep transparent zero; positive profiles use the approved actor-only bank.
Original identifiers remain first, with two genuine north poses appended for
the ground pursuer. These are studies, not a bestiary or new enemy mechanics.
"""
from PIL import Image, ImageDraw

CONCEPTS = {
    'beetle': ['Tarnished Teacup', 'Briar Turnip', 'Runaway Boot',
               'Crab Buckle', 'Louse Loaf', 'Acorn Urchin',
               'Snapping Purse', 'Crawling Inkpot', 'Coin Toad', 'Soap Slug'],
    'bat': ['Bell Wasp', 'Tattered Glove', 'Flying Teeth', 'Mouldy Bowtie',
            'Lantern Gnat', 'Fishbone Kite', 'Ribbon Ray', 'Mushroom Parasol',
            'Quill Moth', 'Wheezing Bagpipe'],
}
NOTES = {
    'beetle': [
        'A hollow cup on greasy feet; the planted gait accelerates with the existing chase clock. The handle and black rim stay readable.',
        'A pale root with a thorn-leaf crown; alternating forked roots expose its approach direction. No armored crown is implied.',
        'An abandoned boot walks itself toward Bloom; the sole flexes while its open ankle and toe keep a clear silhouette.',
        'A living brass buckle shuffles on crab legs; asymmetric pincers open the silhouette without implying a separate ranged attack.',
        'A crusty loaf with a blunt biting end; underside feet alternate under a broad highlighted crust, keeping the moving body connected.',
        'An acorn carried by thorn roots; the crown and tapered nut stay distinct while two roots plant in alternating positions.',
        'A purse with a toothed seam and grasping legs; the brass latch is attached, rather than a floating loot sparkle.',
        'A squat leaking inkpot crawls on bent nibs; the dark cavity, wide shoulder and glass reflection separate it from loose scenery.',
        'A muddy toad with a broad plated brow; its left/right feet paddle alternately. The bright brow is decorative, not actual armor.',
        'A dirty soap bar dragged by a slug; two eye stalks and a continuous dark underside distinguish the hunter from a dropped object.',
    ],
    'bat': [
        'A tiny living bell with insect wings; folded rest versus full wing extension communicates when the drifting pursuit is active.',
        'A discarded glove flaps its fingers; fingers close around the palm during rest, never becoming separate flying particles.',
        'A winged pair of teeth; a clamped resting jaw opens in flight. Its bite is contact damage, with no invented attack interval.',
        'A rotted bowtie with an eye-bearing knot; cloth lobes lift and fold as wings while the knot remains the collision-bearing body.',
        'A square lantern carried by two ragged wings; the handle and glowing central cavity remain attached through both flight poses.',
        'A small fish skeleton swims through air; rib-fins open and draw inward around a continuous spine, with a folded resting tail.',
        'A pale ribbon-like ray; broad flexible membranes alternate above/below the face and the trailing tail follows the same connected body.',
        'A parasol fungus pulses its cap; the narrow closed rest silhouette becomes a broad canopy in flight. No new umbrella shielding is implied.',
        'A moth made from dirty quills; pointed overlapping wing vanes open and fold while the small eye-bearing thorax stays stable.',
        'A wheezing bagpipe flaps its bellows; three uneven pipes identify the creature even in its compressed resting pose.',
    ],
}
EXTRA_FRAMES = {'beetle': ('walk_n1','walk_n2')}
FRAMES = {'beetle': ('walk_s1', 'walk_s2', 'walk_e1', 'walk_e2','walk_n1','walk_n2'),
          'bat': ('fly1', 'fly2', 'rest')}


def _new():
    im = Image.new('P', (16, 16), 0)
    return im, ImageDraw.Draw(im)


def _poly(d, points, fill, edge=1):
    d.polygon(points, fill=fill)
    if edge is not None:
        d.line(points + [points[0]], fill=edge)


def _limb(d, points, ink=10):
    d.line(points, fill=1, width=3)
    d.line(points, fill=ink)


def _eyes(d, face='s', y=9, light=15):
    if face == 'e':
        d.rectangle((11, y-1, 13, y+1), fill=1)
        d.point((12, y-1), fill=light)
        d.point((13, y), fill=light)
    else:
        d.rectangle((5, y-1, 7, y+1), fill=1)
        d.rectangle((9, y-1, 11, y+1), fill=1)
        d.point((6, y-1), fill=light)
        d.point((10, y-1), fill=light)


def _feet(d, phase, face='s', ink=10, broad=False):
    # Feet end at row15, with an alternating planted pair rather than a
    # whole-sprite vertical bob. Side-facing drawings keep a clear front.
    if face == 's':
        for x, step in ((4, phase), (11, 1-phase)):
            end = (x-1 if x < 8 else x+1, 15 if step else 14)
            _limb(d, [(x,11), (x-1 if x<8 else x+1,13), end], ink)
            if broad:d.line((end[0]-1,end[1],end[0]+1,end[1]),fill=ink)
    else:
        for x, step in ((4, phase), (10, 1-phase)):
            _limb(d, [(x,11),(x+1 if step else x-1,13),(x+2 if step else x-2,15)],ink)


def _ground(variant, face, phase):
    im,d = _new()
    if variant == 1: # Cup: an unmistakable open rim and continuous handle.
        _feet(d,phase,face,9)
        if face == 's':
            d.ellipse((10,5,15,11),fill=1);d.ellipse((11,6,14,10),fill=11);d.ellipse((12,7,13,9),fill=0)
            _poly(d,[(3,5),(11,5),(11,11),(9,13),(5,13),(3,11)],10)
            d.polygon([(4,6),(7,6),(7,11),(5,12),(4,10)],fill=12)
            d.ellipse((3,3,11,7),fill=1);d.ellipse((4,4,10,6),fill=2)
            d.line((4,4,8,4),fill=15);d.line((4,7,4,10),fill=11)
            _eyes(d,face,10)
        else:
            d.ellipse((1,5,6,10),fill=1);d.ellipse((2,6,5,9),fill=11);d.rectangle((3,7,4,8),fill=0)
            _poly(d,[(5,4),(12,4),(13,10),(11,13),(6,12)],10)
            d.polygon([(6,5),(8,5),(8,11),(6,10)],fill=12)
            d.ellipse((5,3,12,6),fill=1);d.line((6,4,11,4),fill=15);d.line((7,5,11,5),fill=2)
            d.point((12,8),fill=15)
    elif variant == 2: # A broad pale turnip under a thorn-leaf crown.
        _feet(d,phase,face,10)
        _poly(d,[(3,7),(5,4),(10,4),(13,7),(12,11),(8,14),(4,11)],12)
        d.polygon([(4,7),(6,5),(9,5),(9,10),(7,12),(4,10)],fill=15)
        d.line((5,8,5,10),fill=7)
        _poly(d,[(7,6),(4,3),(4,1),(7,3),(8,0),(10,3),(13,2),(11,6)],4)
        d.line([(6,3),(8,5),(9,2)],fill=6)
        _eyes(d,face,9)
        if face=='e':d.polygon([(11,9),(14,10),(11,11)],fill=12)
    elif variant == 3: # A bent boot, not another domed bug.
        # The two sole contacts deform, while the ankle remains upright.
        _poly(d,[(5,2),(11,2),(11,8),(14,10),(14,13),(3,14),(2,12),(4,9)],8)
        d.polygon([(6,4),(9,4),(9,10),(6,11),(4,12),(12,12),(12,10),(10,9),(10,4)],fill=10)
        d.line([(6,4),(6,9),(4,11)],fill=11)
        d.rectangle((5,2,11,4),fill=1);d.line((6,2,10,2),fill=12)
        d.line((3,13,13,13),fill=1);d.line((4,14 if phase else 13,7,14 if phase else 13),fill=11)
        d.line((10,13 if phase else 14,13,13 if phase else 14),fill=10)
        if face=='s':d.point((6,6),fill=15);d.point((9,6),fill=15);d.line((7,9,9,9),fill=1)
        else:d.point((10,6),fill=15);d.line((10,7,11,8),fill=1)
    elif variant == 4: # Rectangular buckle with real negative space.
        _feet(d,phase,face,10)
        _limb(d,[(4,8),(1,8),(1,5 if phase else 6)],11)
        _limb(d,[(11,8),(14,8),(14,6 if phase else 5)],11)
        _poly(d,[(4,4),(11,4),(12,5),(12,11),(10,12),(4,11)],10)
        d.line([(4,5),(4,10),(5,11)],fill=12);d.line((5,4,10,4),fill=15)
        d.rectangle((6,6,10,9),fill=1);d.rectangle((7,7,9,8),fill=2)
        d.line((8,6,8,10),fill=11)
        if face=='s':d.point((5,11),fill=15);d.point((10,11),fill=15)
        else:d.point((12,9),fill=15);d.line((13,6,15,5),fill=12)
    elif variant == 5: # Low crusty louse: horizontal silhouette, short legs.
        _feet(d,phase,face,9)
        _poly(d,[(1,9),(3,6),(6,4),(10,4),(13,6),(14,11),(11,13),(4,13),(2,12)],10)
        d.polygon([(3,8),(5,5),(9,5),(12,7),(12,9),(4,10)],fill=12)
        d.line([(4,6),(7,5),(9,5)],fill=15)
        d.line([(5,6),(5,8)],fill=9);d.line([(9,6),(8,8)],fill=9)
        if face=='s':_eyes(d,face,11);d.line((6,13,9,13),fill=1)
        else:_eyes(d,face,10);d.line((13,12,14,11),fill=15)
    elif variant == 6: # Root-walking acorn, angular cap rather than green dome.
        _feet(d,phase,face,9)
        _poly(d,[(4,6),(11,6),(12,9),(10,13),(8,14),(5,12),(3,9)],10)
        d.polygon([(5,7),(8,7),(8,12),(7,13),(5,11)],fill=12)
        d.line((5,8,5,10),fill=15)
        _poly(d,[(2,6),(4,3),(7,2),(11,3),(13,6),(12,8),(3,8)],3)
        d.line([(3,6),(6,4),(10,4),(12,6)],fill=6)
        d.line([(7,3),(8,0),(10,1)],fill=1);d.point((8,1),fill=11)
        d.point((5,6),fill=5);d.point((9,5),fill=5)
        _eyes(d,face,10)
    elif variant == 7: # Sagging purse with latch, seam and connected limbs.
        _feet(d,phase,face,9)
        _poly(d,[(4,6),(11,6),(13,10),(12,13),(3,13),(2,10)],8)
        d.polygon([(4,7),(7,7),(6,11),(4,12),(3,10)],fill=10)
        d.line([(5,6),(5,4),(7,2),(9,2),(11,4),(11,6)],fill=1,width=3)
        d.line([(5,5),(6,3),(9,3),(10,5)],fill=11)
        d.line([(4,9),(8,10+phase),(11,9)],fill=1,width=2)
        d.point((5,9),fill=15);d.point((10,9),fill=15)
        d.rectangle((7,5,9,7),fill=11);d.point((7,5),fill=15)
        if face=='e':d.polygon([(12,8),(14,9),(12,11)],fill=10);d.point((13,9),fill=15)
    elif variant == 8: # Glass shoulder and dark opening of a walking inkpot.
        _feet(d,phase,face,9)
        _poly(d,[(5,5),(10,5),(10,7),(13,9),(12,13),(3,13),(2,9),(5,7)],3)
        d.polygon([(4,9),(6,7),(7,7),(7,12),(4,12)],fill=5)
        d.line((4,9,4,11),fill=15)
        d.rectangle((4,2,11,5),fill=1);d.rectangle((5,3,10,4),fill=10)
        d.line((5,2,9,2),fill=12);d.rectangle((6,5,9,6),fill=2)
        _eyes(d,face,10)
        d.line((8,13,11,13),fill=2)
    elif variant == 9: # Squat toad with projecting eye lobes and paddle feet.
        _feet(d,phase,face,10,True)
        _poly(d,[(3,8),(4,5),(7,6),(9,5),(12,6),(14,10),(12,13),(4,13),(2,11)],3)
        d.polygon([(3,9),(5,7),(10,7),(12,9),(11,12),(4,11)],fill=5)
        d.ellipse((3,4,7,8),fill=1);d.ellipse((9,4,13,8),fill=1)
        d.line((4,5,6,5),fill=12);d.line((10,5,12,5),fill=12)
        d.point((5,6),fill=15);d.point((11,6),fill=15)
        d.line((5,11,10,11),fill=1);d.line((6,12,9,12),fill=11)
        if face=='e':d.polygon([(11,8),(15,9),(14,11),(11,11)],fill=5)
    else: # Soap slug: one continuous low body plus clear eye stalks.
        _poly(d,[(1,13),(3,10),(9,10),(13,11),(15,13),(13,14),(3,14)],3)
        d.line([(2,13),(6,12),(11,12),(13,13)],fill=5)
        _poly(d,[(3,5),(10,5),(12,7),(12,10),(10,12),(3,11),(2,8)],12)
        d.polygon([(4,6),(9,6),(10,7),(8,8),(3,8)],fill=15)
        d.line((3,9,9,10),fill=11);d.line((5,7,7,7),fill=7)
        if face=='s':
            _limb(d,[(5,11),(4-phase,8)],5);_limb(d,[(10,11),(11+phase,8)],5)
            d.point((4-phase,8),fill=15);d.point((11+phase,8),fill=15)
        else:
            _limb(d,[(11,11),(13,7+phase)],5);d.point((13,7+phase),fill=15)
    return im


def _ground_n(variant,phase):
    """Genuine north-heading backs on the same planted native baseline.

    Feet are authored in place rather than vertically flipping the south
    body. Broad construction/appendage changes carry facing before detail.
    """
    im,d=_new()
    if variant==1:
        _feet(d,phase,'s',9)
        # The handle now projects to the opposite side of the back. The
        # deep far opening and broad plain cup back replace its face.
        d.ellipse((0,5,5,11),fill=1);d.ellipse((1,6,4,10),fill=11);d.ellipse((2,7,3,9),fill=0)
        _poly(d,[(4,5),(12,5),(12,11),(10,13),(6,13),(4,11)],10)
        d.polygon([(5,6),(8,6),(8,12),(6,12),(5,10)],fill=12)
        d.ellipse((4,3,12,7),fill=1);d.ellipse((5,4,11,6),fill=2)
        d.line((5,4,9,4),fill=15);d.line((5,7,5,10),fill=11)
        d.line([(10,9),(10,11),(9,12)],fill=8)
    elif variant==2:
        _feet(d,phase,'s',10)
        _poly(d,[(4,6),(6,4),(10,4),(12,7),(11,11),(8,14),(4,11),(3,8)],12)
        d.polygon([(4,7),(6,5),(8,5),(8,12),(6,12),(4,10)],fill=15)
        # A broad rear leaf fan and the connected neck root carry heading.
        _poly(d,[(7,7),(3,4),(2,1),(6,2),(8,0),(10,3),(14,2),(13,5),(9,8)],3)
        d.line([(4,2),(7,5),(8,7),(10,4),(13,3)],fill=6)
        d.line((7,8,8,11),fill=11);d.line((9,9,9,12),fill=10)
    elif variant==3:
        # A narrow heel, high rear shaft and stitched back replace the
        # south-facing broad toe. Two sole contacts still alternate.
        _poly(d,[(5,2),(11,2),(11,10),(12,12),(11,14),(4,14),(3,12),(5,10)],8)
        d.polygon([(6,4),(9,4),(9,11),(11,12),(10,13),(5,13),(5,11),(6,9)],fill=10)
        d.rectangle((5,2,11,4),fill=1);d.line((6,2,10,2),fill=12)
        d.line((6,5,6,10),fill=11);d.line((8,5,8,11),fill=8)
        d.rectangle((4,12,11,14),fill=1);d.line((5,12,10,12),fill=10)
        d.line((4,14 if phase else 15,6,14 if phase else 15),fill=11)
        d.line((9,15 if phase else 14,11,15 if phase else 14),fill=10)
    elif variant==4:
        _feet(d,phase,'s',10)
        # Pincers reach toward the far/top edge; the buckle's leather
        # fastening bar is visible on its back rather than an open face.
        _limb(d,[(4,7),(2,5),(2,2 if phase else 3)],11)
        _limb(d,[(11,7),(13,5),(13,3 if phase else 2)],11)
        _poly(d,[(4,4),(11,4),(12,6),(12,11),(10,12),(4,11)],9)
        d.line([(4,5),(4,10),(5,11)],fill=12);d.line((5,4,10,4),fill=15)
        d.rectangle((6,5,10,10),fill=8);d.line((5,7,11,7),fill=11)
        d.point((5,8),fill=12);d.point((11,8),fill=12)
    elif variant==5:
        _feet(d,phase,'s',9)
        # The blunt feeding end projects north, ahead of a broad crusted
        # back; score lines describe that back rather than eyes.
        _poly(d,[(6,2),(10,2),(11,5),(13,7),(14,11),(11,13),(4,13),(1,10),(2,7),(5,5)],10)
        d.polygon([(4,7),(6,5),(10,5),(12,8),(11,10),(4,10)],fill=12)
        d.line([(5,6),(7,5),(9,5)],fill=15)
        d.line([(4,8),(6,9),(7,11)],fill=9)
        d.line([(9,7),(10,9),(11,10)],fill=9)
        d.line((6,3,9,3),fill=11);d.point((6,4),fill=12)
    elif variant==6:
        _feet(d,phase,'s',9)
        _poly(d,[(4,6),(11,6),(12,9),(10,13),(8,14),(5,12),(3,9)],10)
        d.polygon([(4,8),(7,7),(8,10),(7,13),(5,11)],fill=12)
        # A dark rear shell groove and overlapping back cap scales remain
        # attached to the same root crown and alternating supports.
        d.line([(8,8),(9,11),(8,13)],fill=8)
        _poly(d,[(2,6),(4,3),(7,2),(11,3),(13,6),(12,8),(3,8)],3)
        d.line([(3,6),(6,4),(10,4),(12,6)],fill=6)
        d.line([(5,5),(6,7),(9,6),(10,8)],fill=2)
        d.line([(7,3),(8,0),(10,1)],fill=1);d.point((8,1),fill=11)
    elif variant==7:
        _feet(d,phase,'s',9)
        _poly(d,[(4,6),(11,6),(13,10),(12,13),(3,13),(2,10)],8)
        d.polygon([(4,7),(6,6),(7,8),(6,12),(4,12),(3,10)],fill=10)
        d.line([(5,6),(5,4),(7,2),(9,2),(11,4),(11,6)],fill=1,width=3)
        d.line([(5,5),(6,3),(9,3),(10,5)],fill=11)
        # Back straps and broad folded leather, with no false front jaw.
        d.rectangle((7,7,10,12),fill=9);d.line((7,7,7,11),fill=11)
        d.line([(3,10),(5,11),(11,10)],fill=1)
        d.line((8,8,8,10),fill=8)
    elif variant==8:
        _feet(d,phase,'s',9)
        # The rear is tall and square-shouldered. The bottle neck and
        # tilted cap project away while the front face disappears.
        _poly(d,[(5,5),(10,5),(11,7),(12,8),(12,13),(3,13),(3,8),(5,7)],3)
        d.polygon([(4,8),(6,7),(7,7),(7,12),(4,12)],fill=5)
        d.line((4,8,4,11),fill=15)
        _poly(d,[(4,3),(10,2),(12,4),(11,5),(5,6)],10)
        d.line((5,3,9,2),fill=12);d.rectangle((6,5,9,6),fill=2)
        d.rectangle((8,8,10,11),fill=2);d.line((8,9,8,11),fill=4)
    elif variant==9:
        _feet(d,phase,'s',10,True)
        # Broad hind thighs are nearest the viewer; far eye lids frame
        # a small forward head rather than staring back at Bloom.
        _poly(d,[(4,6),(5,3),(10,3),(12,6),(13,8),(14,12),(11,14),(4,14),(1,12),(2,8)],3)
        d.polygon([(4,7),(6,5),(10,5),(11,8),(11,12),(5,12),(3,10)],fill=5)
        d.line([(4,5),(5,4),(6,4)],fill=12);d.line([(9,4),(10,4),(11,5)],fill=11)
        d.line([(3,10),(4,12),(6,13)],fill=2);d.line([(12,10),(11,12),(9,13)],fill=2)
        d.line([(5,7),(7,6),(9,7)],fill=6);d.point((6,9),fill=4)
    else:
        # Eye stalks now lead toward the top; the connected low tail is
        # behind the bar. Only limb placement changes with the gait.
        _poly(d,[(3,11),(9,10),(12,12),(13,14),(11,15),(6,14),(2,13)],3)
        d.line([(4,12),(8,12),(11,14)],fill=5)
        _poly(d,[(3,6),(10,6),(12,8),(11,12),(4,12),(2,9)],12)
        d.polygon([(4,7),(9,7),(10,8),(8,9),(3,9)],fill=15)
        d.line((4,10,9,11),fill=11)
        _limb(d,[(5,7),(4-phase,3)],5);_limb(d,[(9,7),(10+phase,3)],5)
        d.point((4-phase,3),fill=15);d.point((10+phase,3),fill=15)
        d.line((6,14,8,15 if phase else 14),fill=4)
    return im


def _wings(d, up, shape='leaf', light=15, mid=5):
    if shape=='leaf':
        left=[(6,8),(3,2 if up else 8),(0,3 if up else 13),(2,9 if up else 14),(5,11)]
    elif shape=='cloth':
        left=[(6,7),(2,3 if up else 7),(0,2 if up else 12),(1,9 if up else 14),(5,11)]
    else:
        left=[(6,8),(2,2 if up else 9),(0,1 if up else 14),(3,9 if up else 13),(5,11)]
    right=[(15-x,y) for x,y in left]
    for points in (left,right):
        _poly(d,points,mid)
    if up:
        d.line([(1,3),(3,4),(5,8)],fill=light);d.line([(14,3),(12,4),(10,8)],fill=light)
    else:
        d.line([(1,12),(4,10),(5,10)],fill=light);d.line([(14,12),(11,10),(10,10)],fill=light)


def _air(variant, name):
    im,d=_new();rest=name=='rest';up=name=='fly1'
    if variant == 1: # Bell wasp.
        if not rest:_wings(d,up,'leaf',15,5)
        else:
            _poly(d,[(5,5),(3,8),(5,12),(7,10)],4)
            _poly(d,[(10,5),(12,8),(10,12),(8,10)],3)
        _poly(d,[(6,5),(9,5),(10,9),(11,11),(4,11),(5,9)],10)
        d.line([(6,6),(6,9),(5,10),(9,10)],fill=12)
        d.line((6,5,8,5),fill=15);d.rectangle((6,11,9,12),fill=1)
        d.point((7,13),fill=11);d.point((8,13),fill=11)
        d.point((6,7),fill=1);d.point((9,7),fill=1)
    elif variant == 2: # Tattered glove fingers, no literal wings.
        if rest:
            _poly(d,[(4,6),(6,4),(8,6),(10,5),(12,8),(11,12),(9,14),(6,13),(3,10)],10)
            d.line([(5,7),(7,9),(10,8)],fill=8)
        else:
            points=[(5,11),(2,8),(1,4 if up else 9),(3,3 if up else 8),(5,6),
                    (5,1 if up else 5),(7,1 if up else 4),(8,6),(9,2 if up else 6),
                    (11,2 if up else 5),(11,7),(14,5 if up else 8),(15,7 if up else 10),
                    (12,12),(9,14),(6,14)]
            _poly(d,points,10)
            d.line([(6,3 if up else 6),(6,9),(8,11)],fill=12)
            d.line([(10,4 if up else 7),(10,10)],fill=11)
        d.polygon([(5,11),(11,11),(10,14),(6,14)],fill=8)
        d.point((6,9),fill=15);d.point((9,9),fill=15)
    elif variant == 3: # Teeth with abbreviated rib wings.
        if not rest:_wings(d,up,'cloth',12,9)
        _poly(d,[(4,6),(6,4),(10,4),(12,6),(12,9 if rest else 8),(4,9 if rest else 8)],12)
        d.line((5,5,10,5),fill=15)
        if rest:
            _poly(d,[(4,9),(12,9),(11,12),(5,12)],10)
            d.line((5,9,11,9),fill=1);d.point((6,10),fill=15);d.point((9,10),fill=15)
        else:
            d.rectangle((5,8,11,11),fill=1)
            for x in (5,8,11):d.line((x,8,x,9),fill=15)
            _poly(d,[(4,11),(6,12),(10,12),(12,11),(11,14),(5,14)],12)
            d.point((6,11),fill=15);d.point((10,11),fill=15)
        d.point((6,6),fill=1);d.point((10,6),fill=1)
    elif variant == 4: # Living cloth bowtie.
        if rest:
            _poly(d,[(5,4),(8,7),(10,4),(12,12),(9,11),(7,14),(4,12)],4)
            d.line([(5,6),(7,11),(9,7),(11,11)],fill=7)
        else:_wings(d,up,'cloth',7,4)
        _poly(d,[(6,6),(9,6),(10,8),(9,12),(6,12),(5,9)],8)
        d.line((6,7,6,10),fill=11);d.point((6,8),fill=15);d.point((9,8),fill=15)
    elif variant == 5: # Lantern gnat.
        if not rest:_wings(d,up,'leaf',7,4)
        else:
            _poly(d,[(5,6),(3,9),(5,13),(7,11)],4)
            _poly(d,[(10,6),(12,9),(10,13),(8,11)],3)
        d.line([(6,5),(6,3),(9,3),(9,5)],fill=1,width=3)
        d.line([(6,4),(6,3),(9,3),(9,4)],fill=11)
        _poly(d,[(5,5),(10,5),(11,7),(11,12),(4,12),(4,7)],10)
        d.rectangle((6,7,9,10),fill=2);d.line((6,7,6,10),fill=15);d.point((7,8),fill=7)
        d.line((5,5,9,5),fill=12);d.line((5,12,9,12),fill=11)
    elif variant == 6: # Fishbone kite: opened ribs and spine.
        if rest:
            _poly(d,[(6,5),(10,5),(11,8),(9,12),(10,14),(7,13),(5,10)],11)
            d.line([(7,7),(8,10),(8,12)],fill=15)
        else:
            # The rib tips change height, connected along the same spine.
            for offset in (-1,1):
                for y,l in ((7,5),(9,6),(11,4)):
                    _limb(d,[(8,y),(8+offset*l,y-3 if up else y+2)],12)
            _limb(d,[(8,6),(8,12)],15)
            _poly(d,[(8,12),(5,14),(8,14),(11,15),(10,12)],11)
        _poly(d,[(5,4),(7,3),(10,4),(11,7),(8,8),(5,7)],12)
        d.line((6,4,8,4),fill=15);d.point((6,6),fill=1);d.point((9,6),fill=1)
    elif variant == 7: # Ray with a broad flexible membrane and trailing tail.
        if rest:
            _poly(d,[(7,3),(10,5),(11,11),(8,13),(5,11),(4,6)],13)
            d.line([(6,5),(7,9),(9,11)],fill=15)
        else:
            points=[(7,4),(10,6),(15,2 if up else 11),(13,10 if up else 13),
                    (10,12),(8,11),(5,12),(2,10 if up else 13),(0,2 if up else 11),(5,6)]
            _poly(d,points,13)
            d.polygon([(2,5 if up else 11),(6,7),(8,5),(10,8),(13,5 if up else 11),(10,10),(6,10)],fill=15)
            d.line([(4,7),(7,9),(11,8)],fill=14)
        _limb(d,[(8,10),(8,13),(10 if up else 6,15)],13)
        d.point((6,7),fill=1);d.point((9,7),fill=1)
    elif variant == 8: # Parasol fungus.
        if rest:
            _poly(d,[(7,2),(9,3),(11,7),(10,11),(5,11),(4,7)],5)
            d.line([(6,5),(6,9)],fill=7)
        else:
            bottom=8 if up else 11;top=3 if up else 6
            _poly(d,[(0,bottom-1),(2,top+1),(5,top),(10,top),(13,top+1),(15,bottom-1),(13,bottom),(2,bottom)],5)
            d.polygon([(2,bottom-2),(4,top+1),(9,top+1),(12,top+2),(7,top+2),(4,bottom-1)],fill=7)
            d.line((2,bottom,13,bottom),fill=1);d.line((4,bottom-1,11,bottom-1),fill=12)
        _poly(d,[(6,9 if rest else (8 if up else 10)),(9,9 if rest else (8 if up else 10)),(9,13),(7,14),(5,12)],11)
        d.point((6,10 if rest or up else 11),fill=1);d.point((9,10 if rest or up else 11),fill=1)
    elif variant == 9: # Quill moth: narrow spear-like overlapping vanes.
        if rest:
            _poly(d,[(4,4),(8,6),(11,3),(12,10),(9,14),(5,12)],9)
            d.line([(5,6),(7,12),(10,5)],fill=12)
        else:
            for flip in (False,True):
                pts=[(6,8),(3,1 if up else 8),(2,5 if up else 12),(0,3 if up else 10),(1,9 if up else 15),(5,12)]
                if flip:pts=[(15-x,y) for x,y in pts]
                _poly(d,pts,10)
            if up:
                d.line([(3,3),(4,7),(6,10)],fill=12);d.line([(12,3),(11,7),(9,10)],fill=12)
            else:
                d.line([(2,11),(5,10)],fill=12);d.line([(13,11),(10,10)],fill=12)
        _poly(d,[(6,6),(9,6),(10,9),(8,13),(5,10)],3)
        d.point((6,7),fill=15);d.point((9,7),fill=15)
    else: # A saggy bagpipe, recognizable three uneven pipes in every pose.
        if not rest:
            _poly(d,[(5,7),(1,4 if up else 9),(0,6 if up else 13),(5,12)],9)
            _poly(d,[(10,7),(14,4 if up else 9),(15,6 if up else 13),(10,12)],10)
            d.line([(1,6 if up else 11),(4,9)],fill=12)
        _poly(d,[(4,7),(6,5),(11,6),(13,10),(11,13),(5,13),(3,10)],4)
        d.polygon([(5,7),(7,6),(10,7),(10,9),(6,10),(4,9)],fill=6)
        for points in [[(5,8),(4,2),(6,2)],[(8,7),(8,1),(10,1)],[(11,8),(12,4),(14,4)]]:
            _limb(d,points,10);d.point(points[-1],fill=15)
        d.point((6,10),fill=15);d.point((10,10),fill=15)
        d.line((6,12,9,12),fill=1)
    return im


def frame(family, variant, name):
    """Return one native indexed pose without replacing any engine timing."""
    if family not in FRAMES or variant not in range(1,11) or name not in FRAMES[family]:
        raise ValueError((family,variant,name))
    if family=='beetle':
        if '_n' in name:return _ground_n(variant,0 if name.endswith('1') else 1)
        return _ground(variant,'e' if '_e' in name else 's',0 if name.endswith('1') else 1)
    return _air(variant,name)


def _exact_gif(frames,durations,path):
    """Write a small source animation with an exact union palette."""
    from PIL import ImageSequence
    colors=sorted(set(color for im in frames for color in im.getdata()))
    assert len(colors)<=256,('source palette union',len(colors))
    lookup={rgb:i for i,rgb in enumerate(colors)}
    palette=[channel for rgb in colors for channel in rgb]+[0]*(768-3*len(colors))
    encoded=[]
    for im in frames:
        p=Image.new('P',im.size);p.putpalette(palette)
        p.putdata([lookup[rgb] for rgb in im.getdata()]);encoded.append(p)
    encoded[0].save(path,save_all=True,append_images=encoded[1:],duration=durations,
                    loop=0,optimize=False,disposal=2)
    decoded=Image.open(path)
    actual=[(f.convert('RGB').copy(),f.info['duration']) for f in ImageSequence.Iterator(decoded)]
    # GIF durations have10ms granularity; pixels may not be quantized.
    assert len(actual)==len(frames),(len(actual),len(frames))
    assert all(a.tobytes()==b.tobytes() for (a,_),b in zip(actual,frames))
    return {'exact_palette':True,'colors':len(colors),'frames':len(actual),
            'duration_ms':sum(t for _,t in actual),
            'note':'Source pose loop with engine frame holds, not actual AI/position simulation.'}


def _proofs(out):
    """Source-only review boards; never label these as mGBA output."""
    import hashlib,json
    from pathlib import Path
    from PIL import ImageFont
    import reboot_core as C
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    import enemy_studies_palette
    pal=enemy_studies_palette.colors();checks=[];files={}
    def label(d,xy,s,fill='#e0d8b0'):d.fontmode='1';d.text(xy,s,font=font,fill=fill)
    swatches=[C.PALETTES['drain'][4],C.PALETTES['ground'][4],C.PALETTES['blight'][4],C.PALETTES['stone'][3]]
    for family in FRAMES:
        names=FRAMES[family];cw=max(320,len(names)*75+16);rh=92
        board=Image.new('RGB',(cw*2,48+rh*5),'#101820');draw=ImageDraw.Draw(board)
        label(draw,(8,6),f'{family} mechanic / ten alternatives / SOURCE POSE ART, not emulator output')
        label(draw,(8,24),'Native 16x16 plus 3x nearest-neighbour / actor-only material bank / all original and north poses')
        all_sheet=Image.new('RGB',(max(620,175+len(names)*110),40+rh*10),'#101820');ad=ImageDraw.Draw(all_sheet)
        label(ad,(8,8),f'{family}: ALL CONTRACT FRAMES / SOURCE ART / not mGBA')
        for variant in range(1,11):
            x=((variant-1)%2)*cw;y=48+((variant-1)//2)*rh
            label(draw,(x+7,y+3),f'{variant}. {CONCEPTS[family][variant-1]}')
            ay=40+(variant-1)*rh
            label(ad,(8,ay+3),f'{variant}. {CONCEPTS[family][variant-1]}')
            hashes=[]
            for j,name in enumerate(names):
                im=frame(family,variant,name)
                assert im.mode=='P' and im.size==(16,16) and set(im.getdata())<=set(range(16))
                assert any(im.getdata())
                hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
                checks.append({'family':family,'variant':variant,'frame':name,'native':True,'sha256':hashes[-1]})
                # The first board puts every original frame on two quiet value fields.
                rgba=C.rgba(im,pal);big=rgba.resize((48,48),Image.Resampling.NEAREST)
                bx=x+8+j*75;by=y+22
                draw.rectangle((bx,by,bx+47,by+47),fill=swatches[j%4]);board.paste(big,(bx,by),big)
                board.paste(rgba,(bx+49,by+31),rgba)
                label(draw,(bx,by+51),name.replace('walk_',''))
                # Full frame strip also shows silhouette and grayscale diagnostics.
                sx=175+j*110
                all_sheet.paste(big,(sx,ay+5),big);all_sheet.paste(rgba,(sx+49,ay+37),rgba)
                silhouette=Image.new('RGBA',(16,16));silhouette.putdata([(240,232,192,255) if v else (0,0,0,0) for v in im.getdata()])
                all_sheet.paste(silhouette,(sx+75,ay+37),silhouette)
                label(ad,(sx,ay+58),name)
            # Distinct gait/flap is required; no meaningless uniqueness pixels.
            assert len(set(hashes))==len(hashes),(family,variant)
        p=out/f'{family}-ten-source.png';board.save(p);files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
        p=out/f'{family}-all-frames-source.png';all_sheet.save(p);files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    animations={}
    sequences={
        'beetle':[('walk_s1',130),('walk_s2',140),('walk_s1',130),('walk_s2',140),
                  ('walk_e1',70),('walk_e2',60),('walk_e1',70),('walk_e2',70),
                  ('walk_n1',130),('walk_n2',140),('walk_n1',70),('walk_n2',60)],
        'bat':[('rest',670)]+[('fly1',70),('fly2',60),('fly1',70),('fly2',70)]*4,
    }
    for family,sequence in sequences.items():
        frames=[]
        for name,duration in sequence:
            board=Image.new('RGB',(640,216),'#101820');bd=ImageDraw.Draw(board)
            label(bd,(8,5),f'{family}: SOURCE POSE LOOP / not mGBA / {name}')
            label(bd,(8,22),'Existing state holds; movement and damage behavior remain in the engine')
            for variant in range(1,11):
                x=((variant-1)%5)*128;y=44+((variant-1)//5)*84
                label(bd,(x+3,y),f'{variant}. {CONCEPTS[family][variant-1]}')
                im=frame(family,variant,name);rgba=C.rgba(im,pal)
                board.paste(rgba.resize((48,48),Image.Resampling.NEAREST),(x+24,y+19),rgba.resize((48,48),Image.Resampling.NEAREST))
                board.paste(rgba,(x+79,y+50),rgba)
            frames.append(board)
        p=out/f'{family}-poses-source.gif'
        animations[p.name]=_exact_gif(frames,[duration for _,duration in sequence],p)
        files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'status':'source art only; native bank/canvas/frame validation, not a gameplay test','source_sha256':hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),'palette':'approved actor-only enemy_studies_palette.colors(), items OBJ10, original shared bugs protected','frames':checks,'files':files,'source_animations':animations,'concepts':CONCEPTS,'notes':NOTES}
    (out/'small-native-validation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    import sys
    result=_proofs(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/appearance-enemy-studies/small')
    print('native frames validated:',len(result['frames']))
