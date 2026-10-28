"""Native item drawings for the selected gilt-and-rot art direction.

World, HUD and menu drawings are authored separately at their final pixel
sizes. Only metadata comes from reboot_contracts; no imported art is read.
Every frame uses one of reboot_core's literal RGB555 material banks.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw
import reboot_core as R

MATERIAL_ALIAS={'gold':'gear','hero':'hero','blight':'blight','foliage':'bugs','stone':'iron'}
OWNED={'sword','shield','items','lift','arrow','pick32','icon32','interactivechest','interactiveentry'}
HELD_GRIPS={'n':(21,15),'e':(23,20),'s':(19,23),'w':(8,20)}
SHIELD_GRIP=(8,8)
BOMB_GRIP=(8,7)
ARROW_NOCKS={'e':(3,8),'s':(8,3),'n':(8,12)}
ARROW_TIPS={'e':(14,8),'s':(8,14),'n':(8,1)}


def rows(im):
    return [''.join('%x'%im.getpixel((x,y)) if im.getpixel((x,y)) else '.'
                    for x in range(im.width)) for y in range(im.height)]


def blank(w=16,h=16):return R.indexed(w,h)


def place(im,size,at):
    out=Image.new('P',size,0);out.paste(im,at);return out


def material(kind):
    if kind in ('bombs','bomb_pickup','bomb_lit'):return 'blight'
    if kind in ('heart','heart_piece','heart_container'):return 'hero'
    if kind=='cloak':return 'foliage'
    if kind in ('sword','hubcap','arrow1','arrow5','arrow10'):return 'stone'
    return 'gold'


def small(kind):
    """Literal 16px drawing, including the compact world-drop variants."""
    im,d=blank()
    if kind=='none':return im
    if kind in ('bombs','bomb_pickup','bomb_lit'):
        d.ellipse((2,5,13,15),fill=1);d.ellipse((3,6,12,14),fill=4)
        d.polygon([(4,6),(8,6),(9,8),(7,10),(4,9)],fill=6)
        d.line([(4,7),(6,6)],fill=14)
        d.line([(8,5),(8,3),(10,2),(12,3)],fill=10)
        d.line([(9,4),(9,3),(10,3)],fill=11)
        if kind=='bomb_lit':
            d.line([(12,0),(12,4)],fill=15);d.line([(10,2),(14,2)],fill=15)
            d.point((12,2),fill=14)
    elif kind=='lamp':
        d.arc((5,0,10,6),180,360,fill=1,width=2)
        d.line([(6,2),(6,1),(9,1)],fill=9)
        d.polygon([(4,5),(5,3),(10,3),(12,5),(11,6),(11,13),(12,14),(3,14),(4,13),(4,6)],fill=1)
        d.line([(4,5),(11,5)],fill=10);d.line([(4,13),(11,13)],fill=10)
        d.line([(5,6),(5,12)],fill=8);d.line([(10,6),(10,12)],fill=6)
        d.rectangle((6,6,9,12),fill=2)
        d.line([(7,11),(7,8),(8,7),(8,10)],fill=12)
        d.point((8,9),fill=11)
    elif kind=='cloak':
        d.polygon([(5,1),(10,1),(12,4),(12,7),(14,13),(10,13),(8,15),(5,13),(1,14),(3,8),(3,4)],fill=1)
        d.polygon([(5,2),(9,2),(11,5),(9,7),(6,7),(4,5)],fill=4)
        d.polygon([(6,3),(9,3),(10,5),(8,7),(5,6)],fill=2)
        d.polygon([(4,7),(7,8),(6,12),(3,13)],fill=5)
        d.polygon([(8,8),(10,7),(12,12),(9,13)],fill=3)
        d.line([(4,8),(3,11)],fill=6);d.rectangle((7,7,8,8),fill=12)
    elif kind=='key':
        im=R.pickup('key')
    elif kind in ('heart','heart_piece','heart_container'):
        # Shared outline; a missing half reads through shape and shadow.
        d.polygon([(2,4),(4,2),(6,2),(8,4),(10,2),(12,2),(14,4),(14,7),(8,14),(2,8)],fill=1)
        d.polygon([(3,4),(5,3),(7,5),(8,5),(10,3),(12,3),(13,4),(13,7),(8,12),(3,7)],fill=3)
        d.polygon([(3,4),(5,3),(7,5),(8,5),(9,4),(11,4),(10,7),(8,9),(4,7)],fill=4)
        d.line([(4,4),(5,4),(4,5)],fill=7)
        if kind=='heart_piece':
            d.polygon([(9,3),(12,3),(13,4),(13,7),(8,12),(8,9),(10,7),(8,6),(9,4)],fill=2)
            d.line([(9,4),(8,6),(10,7),(8,9),(8,12)],fill=1)
        elif kind=='heart_container':
            d.line([(2,4),(4,2),(6,2),(8,4),(10,2),(12,2),(14,4)],fill=6)
            d.point((8,12),fill=5)
    elif kind=='gilt':
        im=R.pickup('coin')
    elif kind=='gilt_big':
        # A small purse, not the former character-sized coin-pile icon.
        d.polygon([(5,2),(11,2),(11,4),(9,5),(12,8),(13,12),(11,15),(3,15),(1,12),(2,8),(5,5),(4,4)],fill=1)
        d.polygon([(5,3),(10,3),(8,5),(5,5)],fill=6)
        d.polygon([(5,6),(9,6),(11,9),(11,13),(8,14),(3,13),(3,9)],fill=5)
        d.line([(5,7),(4,9),(4,11)],fill=6)
        d.line([(5,5),(9,5)],fill=10);d.line([(6,9),(8,9),(8,11),(6,11)],fill=10)
    elif kind in ('relic','astrolabe'):
        d.ellipse((1,1,14,14),fill=1);d.ellipse((2,2,13,13),fill=8)
        d.ellipse((4,4,11,11),fill=13)
        d.line([(4,3),(9,2)],fill=11);d.line([(11,5),(12,10)],fill=6)
        if kind=='relic':
            d.polygon([(8,4),(9,7),(11,8),(9,9),(8,12),(7,9),(4,8),(7,7)],fill=11)
            d.point((8,8),fill=12)
        else:
            d.line([(8,4),(8,11)],fill=10);d.line([(4,8),(11,8)],fill=10)
            d.line([(8,8),(11,5)],fill=12)
    elif kind=='spark':
        d.polygon([(8,1),(9,6),(14,8),(9,9),(8,14),(6,9),(1,8),(6,6)],fill=8)
        d.line([(8,3),(8,12)],fill=12);d.line([(3,8),(12,8)],fill=11)
    elif kind=='grail':
        d.polygon([(2,2),(13,2),(12,7),(10,9),(9,9),(9,12),(12,13),(12,15),(3,15),(3,13),(6,12),(6,9),(4,8),(2,5)],fill=1)
        d.polygon([(3,3),(12,3),(11,6),(9,8),(6,8),(4,6)],fill=9)
        d.line([(3,3),(12,3)],fill=12);d.line([(4,4),(5,6)],fill=11)
        d.line([(7,8),(7,12)],fill=10);d.line([(4,13),(11,13)],fill=10)
        d.rectangle((7,5,8,6),fill=15)
    elif kind=='gauntlet':
        d.polygon([(3,12),(2,8),(3,6),(4,7),(4,3),(6,2),(7,3),(7,1),(9,1),(10,3),(11,2),(13,3),(13,7),(14,7),(14,10),(11,13),(10,15),(4,15)],fill=1)
        d.polygon([(4,11),(3,8),(4,8),(5,10),(5,4),(6,4),(7,8),(8,8),(8,2),(9,2),(10,8),(11,8),(12,4),(12,9),(13,8),(13,10),(10,12)],fill=8)
        d.line([(5,4),(6,4),(6,7)],fill=11);d.line([(8,3),(8,7)],fill=11)
        d.rectangle((5,12,10,14),fill=9);d.line([(5,12),(10,12)],fill=12)
    elif kind=='bow':
        d.line([(4,1),(8,2),(11,5),(12,9),(10,13),(6,15)],fill=1,width=3)
        d.line([(4,2),(8,3),(10,5),(11,9),(9,12),(6,14)],fill=6,width=1)
        d.line([(4,2),(6,14)],fill=11)
        d.line([(10,7),(11,10)],fill=8,width=2)
        d.line([(5,2),(7,3)],fill=14);d.line([(7,13),(8,12)],fill=14)
    elif kind in ('arrow1','arrow5','arrow10'):
        offsets=[0] if kind=='arrow1' else [-2,1] if kind=='arrow5' else [-3,0,3]
        for off in offsets:
            d.line([(3+off,13),(12+off,4)],fill=1,width=3)
            d.line([(3+off,13),(11+off,5)],fill=12,width=1)
            d.polygon([(10+off,3),(14+off,2),(13+off,6),(12+off,5)],fill=7)
            d.line([(3+off,10),(6+off,12)],fill=5,width=2)
    elif kind=='hubcap':
        d.ellipse((1,1,14,14),fill=1);d.ellipse((2,2,13,13),fill=5)
        d.arc((2,2,13,13),190,300,fill=8,width=1)
        d.ellipse((6,6,9,9),fill=1)
        for x,y in ((5,4),(10,4),(4,10),(10,10)):d.rectangle((x,y,x+1,y+1),fill=2)
        d.point((4,3),fill=7)
    elif kind=='map':
        d.polygon([(2,2),(6,1),(10,3),(13,2),(14,14),(10,15),(6,13),(2,14)],fill=1)
        d.polygon([(3,3),(6,2),(10,4),(12,3),(13,13),(10,14),(6,12),(3,13)],fill=11)
        d.line([(6,3),(6,11)],fill=9);d.line([(10,5),(10,13)],fill=9)
        d.line([(4,9),(5,7),(8,8),(11,6)],fill=13);d.point((11,6),fill=15)
    elif kind=='sword':
        d.line([(8,1),(8,10)],fill=1,width=3);d.line([(8,2),(8,9)],fill=7)
        d.line([(7,3),(7,8)],fill=8);d.line([(4,10),(12,10)],fill=1,width=3)
        d.line([(4,10),(12,10)],fill=13);d.line([(8,11),(8,15)],fill=10,width=2)
        d.point((7,12),fill=14)
    elif kind in ('shield','shield_upgraded'):
        return shield('front',kind=='shield_upgraded')
    else:raise KeyError(kind)
    return im


def shield(view='front',upgraded=False):
    im,d=blank()
    if view=='side':
        d.polygon([(7,2),(9,3),(10,8),(9,13),(7,13),(6,8)],fill=1)
        d.line([(8,3),(9,4),(10,8),(8,12)],fill=10 if upgraded else 8,width=2)
        d.line([(7,5),(7,10)],fill=13 if upgraded else 5)
        return im
    d.polygon([(4,2),(11,2),(12,4),(11,10),(9,13),(6,13),(4,10),(3,4)],fill=1)
    d.polygon([(5,3),(10,3),(11,4),(10,9),(9,12),(6,12),(5,9),(4,4)],fill=9 if upgraded else 8)
    d.polygon([(5,4),(10,4),(10,9),(8,11),(6,10),(5,8)],fill=13 if upgraded else 5)
    d.line([(4,3),(10,3)],fill=12 if upgraded else 10)
    if view=='back':
        d.line([(5,6),(10,6)],fill=3,width=2);d.line([(5,9),(10,9)],fill=3)
        d.line([(6,7),(6,9)],fill=8);d.line([(9,7),(9,9)],fill=8)
    elif upgraded:
        d.line([(8,5),(8,9)],fill=11);d.line([(6,7),(9,7)],fill=11)
    else:
        d.line([(7,4),(7,10)],fill=3);d.rectangle((7,7,8,8),fill=10)
    return im


def large(kind):
    """Separate menu illustration, drawn directly on its native32px grid."""
    im,d=blank(32,32)
    if kind=='none':return im
    if kind in ('bombs','bomb_pickup','bomb_lit'):
        d.ellipse((5,9,26,29),fill=1);d.ellipse((6,10,25,28),fill=4)
        d.polygon([(8,11),(15,10),(19,13),(18,17),(12,19),(8,16)],fill=6)
        d.line([(9,12),(12,11),(14,12)],fill=14,width=2)
        d.line([(17,9),(17,5),(20,2),(24,3)],fill=10,width=2)
        d.line([(19,6),(20,4),(23,4)],fill=11)
        d.point((25,2),fill=15)
    elif kind=='lamp':
        d.arc((11,1,21,11),180,360,fill=1,width=3);d.arc((12,2,20,10),180,360,fill=9,width=1)
        d.polygon([(7,10),(11,7),(21,7),(25,10),(23,12),(23,26),(25,28),(7,28),(9,26),(9,12)],fill=1)
        d.line([(8,10),(24,10)],fill=10,width=2);d.line([(8,27),(24,27)],fill=10,width=2)
        d.line([(10,12),(10,25)],fill=8,width=2);d.line([(22,12),(22,25)],fill=6,width=2)
        d.rectangle((12,12,20,25),fill=2)
        d.polygon([(16,24),(13,21),(14,17),(16,14),(17,18),(19,20),(18,23)],fill=9)
        d.line([(16,22),(16,18)],fill=12,width=2)
    elif kind=='cloak':
        d.polygon([(10,2),(20,2),(24,7),(23,14),(28,27),(22,26),(18,29),(13,27),(5,29),(8,15),(7,8)],fill=1)
        d.polygon([(11,3),(18,3),(22,7),(20,13),(13,14),(9,10)],fill=4)
        d.polygon([(13,5),(18,5),(20,8),(18,12),(12,12),(10,9)],fill=2)
        d.polygon([(9,15),(15,16),(12,25),(7,27)],fill=5)
        d.polygon([(17,16),(21,14),(25,25),(19,27)],fill=3)
        d.line([(10,16),(9,22)],fill=6);d.line([(20,16),(22,22)],fill=4)
        d.rectangle((15,14,17,17),fill=12)
    elif kind=='key':
        d.line([(13,13),(25,27)],fill=1,width=6);d.ellipse((3,2,18,17),fill=1)
        d.line([(13,12),(25,25)],fill=9,width=4);d.ellipse((5,4,16,15),fill=9)
        d.ellipse((8,7,12,11),fill=1);d.line([(7,5),(12,5)],fill=12,width=2)
        d.line([(20,23),(24,19)],fill=10,width=3);d.line([(24,27),(28,23)],fill=10,width=3)
    elif kind in ('heart','heart_piece','heart_container'):
        d.polygon([(3,8),(7,4),(11,4),(16,8),(21,4),(25,4),(29,8),(29,14),(16,29),(3,15)],fill=1)
        d.polygon([(5,8),(8,6),(11,6),(16,11),(21,6),(25,6),(27,8),(27,14),(16,26),(5,14)],fill=3)
        d.polygon([(5,9),(8,6),(11,6),(16,11),(21,7),(24,8),(22,14),(16,20),(9,16),(5,13)],fill=4)
        d.line([(8,8),(10,8),(8,12)],fill=7,width=2)
        if kind=='heart_piece':
            d.polygon([(20,7),(25,6),(27,8),(27,14),(16,26),(16,22),(20,18),(17,15),(19,12),(17,10)],fill=2)
            d.line([(18,9),(19,12),(17,15),(20,18),(16,22),(16,26)],fill=1,width=2)
        elif kind=='heart_container':
            d.line([(3,8),(7,4),(11,4),(16,8),(21,4),(25,4),(29,8)],fill=6,width=1)
            d.line([(5,16),(16,28),(27,16)],fill=5)
    elif kind=='gilt_big':
        d.polygon([(10,3),(23,3),(22,7),(18,10),(25,15),(27,24),(23,29),(6,29),(3,24),(5,16),(12,10),(9,7)],fill=1)
        d.polygon([(11,4),(21,4),(18,8),(13,9)],fill=6)
        d.polygon([(12,11),(18,11),(23,16),(24,23),(21,27),(8,27),(5,23),(7,17)],fill=5)
        d.line([(11,13),(8,17),(8,22)],fill=6,width=2)
        d.line([(11,10),(20,10)],fill=10,width=2)
        d.ellipse((14,17,21,24),fill=9);d.line([(17,18),(17,22)],fill=11)
    elif kind in ('relic','astrolabe'):
        d.ellipse((3,3,28,28),fill=1);d.ellipse((5,5,26,26),fill=8)
        d.ellipse((8,8,23,23),fill=13)
        d.arc((5,5,26,26),180,275,fill=11,width=2)
        d.arc((5,5,26,26),5,80,fill=6,width=2)
        if kind=='relic':
            d.polygon([(16,8),(18,13),(23,16),(18,18),(16,24),(14,18),(8,16),(14,14)],fill=11)
            d.line([(16,11),(16,21)],fill=12)
        else:
            d.line([(16,9),(16,23)],fill=10);d.line([(9,16),(23,16)],fill=10)
            d.line([(16,16),(21,11)],fill=12,width=2)
            for x,y in [(16,6),(25,16),(16,25),(6,16)]:d.rectangle((x-1,y-1,x+1,y+1),fill=10)
    elif kind=='gauntlet':
        d.polygon([(7,24),(4,16),(5,12),(8,13),(8,6),(11,4),(13,6),(14,2),(18,2),(20,6),(22,4),(26,6),(25,15),(27,12),(29,14),(27,21),(22,26),(21,29),(9,29)],fill=1)
        d.polygon([(8,22),(6,16),(7,15),(10,20),(10,7),(11,6),(13,8),(13,18),(15,18),(16,4),(18,4),(19,18),(21,18),(23,7),(24,8),(23,19),(27,15),(27,19),(21,24)],fill=8)
        d.line([(11,7),(11,14)],fill=11,width=2);d.line([(17,5),(17,14)],fill=11,width=2)
        d.line([(23,8),(22,15)],fill=10,width=2)
        d.polygon([(10,24),(21,25),(20,29),(11,29)],fill=9)
        d.line([(11,25),(20,26)],fill=12,width=2)
    elif kind=='bow':
        d.line([(9,3),(17,5),(23,11),(25,18),(21,24),(13,28)],fill=1,width=3)
        d.line([(9,4),(17,7),(21,12),(24,18),(20,24),(13,27)],fill=6,width=1)
        d.line([(9,3),(13,28)],fill=11,width=1)
        d.line([(22,14),(23,20)],fill=8,width=3)
        d.line([(10,4),(14,5)],fill=14,width=2);d.line([(14,27),(17,25)],fill=14,width=2)
    elif kind=='hubcap':
        d.ellipse((3,3,28,28),fill=1);d.ellipse((5,5,26,26),fill=5)
        d.arc((5,5,26,26),190,300,fill=8,width=2)
        d.arc((6,6,25,25),5,90,fill=3,width=2)
        d.ellipse((13,13,18,18),fill=1)
        for x,y in [(10,9),(21,9),(9,21),(21,21)]:d.ellipse((x-2,y-2,x+1,y+1),fill=2)
        d.line([(8,7),(13,6)],fill=7)
    elif kind=='map':
        d.polygon([(4,5),(11,3),(20,6),(26,4),(28,27),(20,29),(12,26),(5,28)],fill=1)
        d.polygon([(6,6),(11,5),(20,8),(24,6),(26,25),(20,27),(12,24),(7,26)],fill=11)
        d.line([(12,6),(12,23)],fill=9);d.line([(20,9),(20,26)],fill=9)
        d.line([(8,19),(10,15),(15,17),(19,13),(23,14)],fill=13,width=2)
        d.rectangle((21,11,24,14),fill=15)
        d.line([(7,7),(10,6)],fill=12)
    elif kind=='sword':
        d.polygon([(15,2),(18,5),(18,21),(13,21),(13,5)],fill=1)
        d.polygon([(16,4),(17,6),(17,20),(14,20),(14,6)],fill=7)
        d.line([(15,6),(15,18)],fill=8)
        d.line([(8,22),(23,22)],fill=1,width=5);d.line([(9,21),(22,21)],fill=13,width=2)
        d.rectangle((14,24,17,28),fill=10);d.line([(15,25),(15,28)],fill=14)
        d.line([(13,29),(18,29)],fill=1,width=1)
    elif kind in ('shield','shield_upgraded'):
        up=kind=='shield_upgraded'
        d.polygon([(7,3),(24,3),(27,7),(25,21),(19,28),(13,28),(6,21),(4,7)],fill=1)
        d.polygon([(8,5),(23,5),(25,8),(23,20),(18,26),(14,26),(8,20),(6,8)],fill=9 if up else 8)
        d.polygon([(10,7),(21,7),(21,19),(17,23),(13,20),(10,17)],fill=13 if up else 5)
        d.line([(8,5),(22,5)],fill=12 if up else 10,width=2)
        if up:
            d.line([(16,10),(16,20)],fill=11,width=2)
            d.line([(12,14),(20,14)],fill=11,width=2)
        else:
            d.line([(14,7),(14,21)],fill=3);d.line([(19,7),(19,20)],fill=4)
            d.ellipse((13,13,18,18),fill=10);d.point((14,14),fill=12)
    else:raise KeyError(kind)
    return im


def arrow(direction):
    im,d=blank()
    if direction=='e':
        d.line([(3,8),(12,8)],fill=1,width=3)
        d.line([(3,8),(12,8)],fill=12)
        d.polygon([(10,4),(15,8),(10,12),(11,9),(8,9),(8,7),(11,7)],fill=1)
        d.polygon([(11,5),(14,8),(11,10),(12,8)],fill=7)
        d.line([(3,6),(5,8),(3,10)],fill=5)
    elif direction=='s':
        d.line([(8,3),(8,12)],fill=1,width=3);d.line([(8,3),(8,12)],fill=12)
        d.polygon([(4,10),(8,15),(12,10),(9,11),(9,8),(7,8),(7,11)],fill=1)
        d.polygon([(5,11),(8,14),(10,11),(8,12)],fill=7)
        d.line([(6,3),(8,5),(10,3)],fill=5)
    else:
        d.line([(8,12),(8,3)],fill=1,width=3);d.line([(8,12),(8,3)],fill=12)
        d.polygon([(4,5),(8,0),(12,5),(9,4),(9,7),(7,7),(7,4)],fill=1)
        d.polygon([(5,4),(8,1),(10,4),(8,3)],fill=7)
        d.line([(6,12),(8,10),(10,12)],fill=5)
    return im


def held_item(kind,facing='e',phase=0):
    """A small gripped tool on the32×32actioncanvas, never a menu icon.

    The grip is invariant through recoil. W is the pixel-exact mirror of E.
    Effect canvas origin is world(-16,-32), relative to Bloom's feet.
    """
    if facing=='w':return held_item(kind,'e',phase).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    im,d=blank(32,32);gx,gy=HELD_GRIPS[facing]
    if kind=='bow':
        # Draw cardinal bows, with the released string settling behind the
        # wooden grip. This does not draw a duplicate physical arrow.
        if facing=='e':
            pts=[(gx-3,gy-6),(gx-1,gy-5),(gx+1,gy-2),(gx+1,gy+2),(gx-1,gy+5),(gx-3,gy+6)]
            d.line(pts,fill=1,width=3);d.line(pts,fill=6,width=1)
            pull=0 if phase==0 else -2 if phase==1 else -3
            d.line([(gx-3,gy-6),(gx+pull,gy),(gx-3,gy+6)],fill=11)
            d.rectangle((gx,gy-1,gx+1,gy+1),fill=8)
            d.point((gx,gy),fill=10)
        else:
            sign=-1 if facing=='n' else 1
            pts=[(gx-6,gy-sign*3),(gx-5,gy-sign),(gx-2,gy+sign),(gx+2,gy+sign),(gx+5,gy-sign),(gx+6,gy-sign*3)]
            d.line(pts,fill=1,width=3);d.line(pts,fill=6,width=1)
            pull=0 if phase==0 else -sign*2 if phase==1 else -sign*3
            d.line([(gx-6,gy-sign*3),(gx,gy+pull),(gx+6,gy-sign*3)],fill=11)
            d.rectangle((gx-1,min(gy,gy+sign),gx+1,max(gy,gy+sign)),fill=8)
            d.point((gx,gy),fill=10)
    elif kind=='lamp':
        # Ring is the hand anchor; a tiny caged light hangs below it.
        d.ellipse((gx-1,gy-1,gx+1,gy+1),outline=9)
        d.line([(gx,gy+1),(gx,gy+2)],fill=8)
        d.rectangle((gx-3,gy+2,gx+3,gy+8),fill=1)
        d.line([(gx-3,gy+2),(gx+3,gy+2)],fill=10)
        d.line([(gx-3,gy+8),(gx+3,gy+8)],fill=10)
        d.line([(gx-2,gy+3),(gx-2,gy+7)],fill=8)
        d.line([(gx+2,gy+3),(gx+2,gy+7)],fill=6)
        d.rectangle((gx-1,gy+3,gx+1,gy+7),fill=2)
        d.line([(gx,gy+6),(gx,gy+4)],fill=12)
        if phase==1:d.point((gx+1,gy+4),fill=11)
        elif phase==2:d.point((gx-1,gy+5),fill=11)
        else:d.point((gx+1,gy+5),fill=11)
    else:raise KeyError(kind)
    return im


def held_palette(kind):return 'gear'


def build_sheets(contracts):
    source={s['name']:s for s in contracts['sheets']};out={}
    def emit(name,w,h,frames,mats,default=None,exact=False):
        expected=source[name]['frames'] if name in source else source['icon32']['frames']
        assert list(frames)==expected,(name,list(frames),expected)
        aliases={f:MATERIAL_ALIAS[mats[f]] for f in frames}
        sh={'name':name,'w':w,'h':h,'pal':default or aliases[next(iter(frames))],
            'frames':{f:rows(im) for f,im in frames.items()},'frame_pal':aliases}
        if exact:sh['exact_frames']={f:(sh['frames'][f],R.PALETTES[mats[f]]) for f in frames}
        out[name]=sh
    for name in ('items','pick32','icon32'):
        frames={};mats={}
        for f in source[name]['frames']:
            frames[f]=large(f) if name=='icon32' else small(f);mats[f]=material(f)
        emit(name,32 if name=='icon32' else 16,32 if name=='icon32' else 16,frames,mats,source[name]['pal'],name=='icon32')
    frames={f:small(f) for f in source['icon32']['frames']};mats={f:material(f) for f in frames}
    emit('huditems',16,16,frames,mats,'gear')
    emit('shield',16,16,{f:shield(f.split('_')[-1],f.startswith('upgraded')) for f in source['shield']['frames']},{f:'gold' for f in source['shield']['frames']},'gear')
    blade=small('sword')
    # Small equipment blade frames retain their old orientation contracts.
    sw={'blade_s':blade.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
        'blade_e':blade.transpose(Image.Transpose.ROTATE_270),
        'blade_se':Image.new('P',(16,16),0)}
    im=sw['blade_se'];d=ImageDraw.Draw(im)
    d.line([(4,4),(13,13)],fill=1,width=3);d.line([(5,5),(12,12)],fill=7)
    d.line([(2,7),(7,2)],fill=13,width=2);d.line([(2,2),(4,4)],fill=10,width=2)
    emit('sword',16,16,sw,{f:'stone' for f in sw},'iron')
    lift={};mats={}
    for f in source['lift']['frames']:
        lift[f],mats[f]=R.lift_object(f)
        assert lift[f].getbbox() is not None and lift[f].getbbox()[3]==16,(f,lift[f].getbbox())
    emit('lift',16,16,lift,mats,'lift')
    emit('arrow',16,16,{f:arrow(f) for f in source['arrow']['frames']},{f:'stone' for f in source['arrow']['frames']},'iron')
    emit('interactivechest',32,32,{f:R.chest(('wooden','brass','relic').index(f.split('_')[0]),f.endswith('_open')) for f in source['interactivechest']['frames']},{f:'gold' for f in source['interactivechest']['frames']},'lift')
    frames={};mats={}
    for f in source['interactiveentry']['frames']:
        style=f.split('_')[0];frames[f]=place(R.portal(style,f.endswith('_closed')),(32,64),(0,16));mats[f]='stone' if style=='cave' else 'gold'
    emit('interactiveentry',32,64,frames,mats,'lift')
    assert set(out)==OWNED|{'huditems'},set(out)
    for sh in out.values():
        assert sh['w'] in (16,32) and sh['h'] in (16,32,64)
        for f,rs in sh['frames'].items():
            assert len(rs)==sh['h'] and all(len(r)==sh['w'] for r in rs),(sh['name'],f)
    return out


def preview(outdir='/workspace/setup/art-reboot-items'):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    contracts=json.loads((Path(__file__).parent/'reboot_contracts.json').read_text());sheets=build_sheets(contracts)
    reverse={v:k for k,v in MATERIAL_ALIAS.items()};catalog=[]
    for name,sh in sheets.items():
        for f,rs in sh['frames'].items():
            im=Image.new('P',(sh['w'],sh['h']));im.putdata([int(ch,16) if ch!='.' else 0 for row in rs for ch in row])
            box=im.getbbox();catalog.append({'sheet':name,'frame':f,'canvas':[sh['w'],sh['h']],'visible_bbox':box,'visible_size':[box[2]-box[0],box[3]-box[1]] if box else [0,0],'palette':sh['frame_pal'][f]})
    # 1× images beside enlarged copies, explicitly labelled source artwork.
    cols=7;cellw=144;cellh=160;im=Image.new('RGB',(cols*cellw,44+((len(catalog)+cols-1)//cols)*cellh),'#101820');d=ImageDraw.Draw(im)
    d.text((10,10),'Native item source catalogue / 1x + 3x / NOT emulator captures',fill='#f8f0c8')
    for i,row in enumerate(catalog):
        sh=sheets[row['sheet']];rs=sh['frames'][row['frame']];a=Image.new('P',tuple(row['canvas']));a.putdata([int(ch,16) if ch!='.' else 0 for r in rs for ch in r]);bank=reverse[row['palette']];a=R.rgba(a,R.PALETTES[bank]);x=i%cols*cellw+8;y=44+i//cols*cellh
        big=a.resize((a.width*3,a.height*3),Image.Resampling.NEAREST);im.paste(big,(x,y),big);im.paste(a,(x+104,y+68),a)
        d.text((x,y+108),row['sheet'],fill='#f8f0c8');d.text((x,y+122),row['frame'],fill='#b0c0a8');d.text((x,y+136),'%sx%s'%tuple(row['visible_size']),fill='#b0c0a8')
    im.save(outdir/'item-source-catalogue.png')
    (outdir/'item-source-catalogue.json').write_text(json.dumps({'method':'Direct native indexed drawings; nearest enlargements are inspection only.','sheets':len(sheets),'frames':len(catalog),'frames_detail':catalog},indent=2)+'\n')
    # Critical held-tool grips in every direction, three chronological phases.
    im=Image.new('RGB',(4*144,2*144),'#101820');d=ImageDraw.Draw(im)
    for r,kind in enumerate(('bow','lamp')):
        for c,facing in enumerate(('n','e','s','w')):
            for phase in range(3):
                a=held_item(kind,facing,phase);a=R.rgba(a,R.PALETTES['gold']);im.paste(a,(c*144+phase*44,r*144+30),a)
            d.text((c*144+4,r*144+8),kind+' '+facing,fill='#f8f0c8');d.text((c*144+4,r*144+72),'fixed grip '+str(HELD_GRIPS[facing]),fill='#b0c0a8')
    im.save(outdir/'held-source.png')
    return outdir


if __name__=='__main__':print(preview())
