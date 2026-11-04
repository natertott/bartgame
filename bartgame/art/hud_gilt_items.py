"""Gilt HUD item family: three independently authored native pixel scales.

The16px HUD canvas uses14–16px silhouettes. World drops retain compact8–14px
painted bodies; menu art is24–28px on32px canvases. No resize, imported image,
palette conversion, alpha fringe or effect-sheet replacement is used here.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw
import reboot_core as R


def _canvas(size):
    return R.indexed(size, size)


def hud(name):
    """Literal16px equipped/key-item drawing. All coordinates are native."""
    im,d=_canvas(16)
    if name=='none': return im
    if name in ('bombs','bomb_pickup','bomb_lit'):
        d.ellipse((0,4,13,15),fill=1);d.ellipse((1,5,12,14),fill=4)
        d.polygon([(2,6),(5,5),(9,6),(10,9),(7,11),(3,10)],fill=12)
        d.polygon([(3,6),(6,6),(8,7),(7,9),(3,9)],fill=13)
        d.line([(3,6),(5,6)],fill=14)
        d.line([(8,4),(8,2),(11,0),(14,1)],fill=1,width=3)
        d.line([(8,4),(8,2),(11,1),(14,1)],fill=10)
        d.line([(10,2),(11,1),(13,1)],fill=11)
        if name=='bomb_lit':d.line((14,0,14,3),fill=15);d.line((12,1,15,1),fill=15)
    elif name=='lamp':
        d.arc((4,0,11,7),180,360,fill=1,width=3);d.arc((5,1,10,6),180,360,fill=10)
        d.polygon([(3,4),(12,4),(14,6),(13,7),(13,13),(14,15),(1,15),(2,13),(2,7),(1,6)],fill=1)
        d.line((3,5,12,5),fill=10);d.line((3,6,12,6),fill=8)
        d.rectangle((3,7,12,12),fill=3);d.rectangle((5,7,10,12),fill=2)
        d.polygon([(7,12),(6,10),(7,7),(8,8),(9,11),(8,12)],fill=10)
        d.line((7,9,7,11),fill=12)
        d.line((3,7,3,12),fill=11);d.line((12,7,12,12),fill=6)
        d.line((3,13,12,13),fill=10);d.line((3,14,12,14),fill=8)
    elif name=='cloak':
        d.polygon([(5,0),(10,0),(13,3),(12,7),(15,14),(11,13),(9,15),(6,14),(2,15),(0,13),(3,7),(2,4)],fill=1)
        d.polygon([(3,7),(7,8),(11,7),(14,13),(11,12),(9,14),(6,13),(2,14),(1,13)],fill=4)
        d.polygon([(5,1),(9,1),(11,3),(11,6),(8,8),(4,6),(3,4)],fill=5)
        d.polygon([(6,2),(9,2),(10,4),(9,6),(6,6),(5,5)],fill=2)
        d.line([(8,1),(5,1),(3,4),(4,6)],fill=7)
        d.polygon([(3,7),(6,9),(5,12),(2,14),(1,13)],fill=6)
        d.polygon([(3,8),(6,9),(5,12),(2,14),(1,13)],fill=6)
        d.polygon([(8,9),(10,8),(13,13),(10,12),(9,14),(7,13)],fill=5)
        d.line([(8,10),(7,13)],fill=3)
        d.line([(4,8),(3,11),(2,12)],fill=7)
        d.rectangle((7,7,8,8),fill=12)
    elif name=='key':
        d.line((6,6,13,13),fill=1,width=5);d.ellipse((0,0,9,9),fill=1)
        d.line((7,7,13,13),fill=9,width=3);d.ellipse((1,1,8,8),fill=10)
        d.ellipse((3,3,6,6),fill=1);d.line((2,2,5,1),fill=12)
        d.line((10,12,12,10),fill=10,width=2);d.line((12,14,15,11),fill=10,width=2)
        d.line((7,8,10,11),fill=11)
    elif name in ('heart','heart_piece','heart_container'):
        d.polygon([(0,4),(3,1),(6,1),(8,3),(10,1),(12,1),(15,4),(15,8),(8,15),(0,8)],fill=1)
        d.polygon([(1,4),(3,2),(5,2),(8,5),(11,2),(12,2),(14,4),(14,7),(8,13),(1,7)],fill=3)
        d.polygon([(2,4),(3,3),(5,3),(7,5),(8,6),(11,4),(12,4),(11,7),(8,10),(3,7)],fill=4)
        d.line([(3,3),(4,3),(3,4)],fill=7)
        if name=='heart_piece':
            d.polygon([(10,2),(12,2),(14,4),(14,7),(8,13),(8,10),(10,8),(8,6),(10,4)],fill=2)
            d.line([(9,3),(8,6),(10,8),(8,10),(8,13)],fill=1)
        if name=='heart_container':
            d.line([(0,4),(3,1),(6,1),(8,3),(10,1),(12,1),(15,4)],fill=6)
            d.line([(1,8),(8,15),(14,9)],fill=5)
    elif name in ('gilt','spark'):
        d.polygon([(8,0),(10,5),(15,8),(10,10),(8,15),(5,10),(0,8),(5,5)],fill=1)
        d.polygon([(8,1),(9,6),(14,8),(9,9),(8,14),(6,9),(1,8),(6,6)],fill=9)
        d.line((8,3,8,12),fill=12);d.line((3,8,12,8),fill=11)
    elif name=='gilt_big':
        d.polygon([(4,0),(11,0),(12,3),(10,5),(14,9),(15,13),(12,15),(2,15),(0,12),(1,8),(5,5),(3,3)],fill=1)
        d.polygon([(5,1),(10,1),(10,3),(7,4),(5,3)],fill=6)
        d.polygon([(5,6),(9,6),(12,9),(13,12),(11,14),(3,14),(2,11),(3,8)],fill=5)
        d.line([(5,7),(4,9),(4,11)],fill=6)
        d.line((5,5,10,5),fill=10);d.rectangle((7,9,9,11),fill=9);d.point((7,9),fill=12)
    elif name in ('relic','astrolabe'):
        d.ellipse((0,0,15,15),fill=1);d.ellipse((1,1,14,14),fill=8)
        d.ellipse((3,3,12,12),fill=2);d.arc((1,1,14,14),185,285,fill=11)
        d.arc((1,1,14,14),0,85,fill=6)
        if name=='relic':
            d.polygon([(8,3),(9,6),(12,8),(9,9),(8,12),(6,9),(3,8),(6,6)],fill=13)
            d.line((8,5,8,10),fill=12);d.line((5,8,10,8),fill=11)
        else:
            d.line((8,4,8,11),fill=10);d.line((4,8,11,8),fill=10)
            d.line((8,8,11,5),fill=12);d.point((8,1),fill=12)
    elif name=='grail':
        d.polygon([(0,1),(15,1),(14,6),(11,10),(9,10),(9,13),(13,13),(13,15),(2,15),(2,13),(6,13),(6,10),(4,9),(1,6)],fill=1)
        d.polygon([(1,2),(14,2),(13,6),(10,9),(5,9),(2,6)],fill=9)
        d.line((1,2,14,2),fill=12);d.line([(2,3),(3,6),(5,7)],fill=11)
        d.line((7,10,7,13),fill=10);d.line((3,14,12,14),fill=10);d.rectangle((7,4,8,6),fill=15)
    elif name=='gauntlet':
        d.polygon([(3,15),(2,12),(0,8),(1,6),(3,7),(3,3),(5,1),(7,3),(7,0),(10,0),(11,3),(13,2),(15,4),(14,9),(12,13),(11,15)],fill=1)
        d.polygon([(4,12),(2,8),(3,8),(5,10),(4,4),(5,3),(6,4),(6,9),(8,9),(8,1),(9,1),(10,9),(11,9),(12,4),(13,3),(14,5),(13,10),(10,13)],fill=8)
        d.rectangle((5,8,11,12),fill=8)
        d.polygon([(5,10),(10,9),(12,11),(10,13),(5,13)],fill=9)
        d.line((5,4,5,7),fill=11);d.line((8,2,8,7),fill=12)
        d.rectangle((4,13,10,14),fill=9);d.line((4,13,10,13),fill=12)
    elif name=='bow':
        d.line([(3,0),(8,2),(12,6),(14,10),(11,13),(7,15)],fill=1,width=4)
        d.line([(3,1),(8,3),(11,6),(13,10),(10,13),(7,14)],fill=6,width=2)
        d.line((3,1,7,14),fill=11)
        d.line((11,7,12,10),fill=8,width=2);d.line((4,1,6,2),fill=11)
    elif name in ('arrow1','arrow5','arrow10'):
        count=1 if name=='arrow1' else 2 if name=='arrow5' else 3
        for off in tuple(range(0,count*3,3)):
            x=2+off
            d.line((x,13,10+off//2,3),fill=1,width=3)
            d.line((x,13,10+off//2,3),fill=12)
            d.polygon([(8+off//2,2),(12+off//2,1),(11+off//2,5)],fill=7)
            d.line((x-1,10,x+2,13),fill=5,width=2)
    elif name=='hubcap':
        d.ellipse((0,0,15,15),fill=1);d.ellipse((1,1,14,14),fill=5)
        d.polygon([(3,3),(6,1),(10,2),(13,5),(11,7),(6,6),(2,8)],fill=6)
        d.arc((1,1,14,14),185,285,fill=8);d.arc((2,2,13,13),10,90,fill=3)
        d.rectangle((6,6,9,9),fill=1)
        for x,y in ((4,3),(10,3),(3,10),(10,10)):d.rectangle((x,y,x+1,y+1),fill=2)
        d.line((4,2,7,2),fill=7)
    elif name=='map':
        d.polygon([(0,2),(5,0),(10,2),(14,0),(15,13),(10,15),(5,13),(1,15)],fill=1)
        d.polygon([(1,3),(5,1),(10,3),(13,2),(14,12),(10,14),(5,12),(2,13)],fill=11)
        d.line((5,2,5,11),fill=9);d.line((10,4,10,13),fill=9)
        d.line([(3,9),(4,7),(7,8),(9,6),(12,7)],fill=13);d.point((12,6),fill=15)
    elif name=='sword':
        # Broad diagonal blade, a real guard, and separated leather grip.
        d.polygon([(11,0),(15,0),(15,4),(7,12),(3,8)],fill=1)
        d.polygon([(12,1),(14,1),(14,3),(7,10),(5,8)],fill=7)
        d.line((6,8,13,1),fill=8,width=2);d.line((7,9,13,3),fill=6)
        d.line((2,6,9,13),fill=1,width=3);d.line((2,6,9,13),fill=13)
        d.line((1,13,5,9),fill=1,width=3);d.line((1,13,5,9),fill=10)
        d.point((0,14),fill=12)
    elif name in ('shield','shield_upgraded'):
        up=name.endswith('upgraded')
        d.polygon([(3,0),(12,0),(15,3),(14,10),(10,15),(5,15),(1,10),(0,3)],fill=1)
        d.polygon([(3,1),(11,1),(14,3),(13,9),(10,13),(6,14),(2,9),(1,3)],fill=9 if up else 8)
        d.polygon([(4,3),(11,3),(12,4),(11,9),(8,12),(4,9),(3,4)],fill=13 if up else 5)
        d.line((3,1,10,1),fill=12 if up else 11)
        if up:
            d.line((8,5,8,11),fill=11);d.line([(5,6),(8,8),(11,6)],fill=11);d.line([(6,9),(8,10),(10,9)],fill=11);d.point((8,4),fill=12)
        else:
            d.line((5,3,5,9),fill=3);d.line((10,3,10,9),fill=4)
            d.ellipse((6,6,9,9),fill=10);d.point((7,6),fill=12)
    else:raise KeyError(name)
    assert im.mode=='P' and im.size==(16,16)
    assert max(im.getdata())<16
    return im


def world(name):
    """Independently drawn compact world pickup,14px maximum body extent."""
    im,d=_canvas(16)
    if name=='none':return im
    if name in ('bombs','bomb_pickup','bomb_lit'):
        d.ellipse((3,6,12,14),fill=1);d.ellipse((4,7,11,13),fill=4)
        d.polygon([(5,7),(8,7),(10,9),(8,11),(5,10)],fill=12)
        d.line((5,7,7,7),fill=14);d.line([(8,6),(8,4),(10,2),(12,3)],fill=10)
        if name=='bomb_lit':d.line((12,1,12,4),fill=15);d.point((13,2),fill=15)
    elif name=='lamp':
        d.arc((5,1,10,7),180,360,fill=1,width=2);d.point((7,2),fill=10)
        d.rectangle((3,5,12,14),fill=1);d.rectangle((4,6,11,13),fill=8)
        d.rectangle((6,7,9,12),fill=2);d.line((7,8,7,11),fill=12)
        d.line((4,6,11,6),fill=11);d.line((4,13,11,13),fill=10)
    elif name=='cloak':
        d.polygon([(5,2),(10,2),(12,5),(11,8),(14,13),(10,12),(8,14),(5,13),(2,14),(3,8),(3,5)],fill=1)
        d.polygon([(4,8),(8,9),(10,8),(12,12),(9,12),(8,13),(5,12),(3,13)],fill=4)
        d.polygon([(5,3),(9,3),(10,5),(9,7),(6,7),(4,5)],fill=5)
        d.polygon([(6,4),(9,4),(9,6),(6,6)],fill=2)
        d.polygon([(4,8),(6,9),(5,12),(3,13)],fill=5);d.line((4,9,4,11),fill=7)
        d.polygon([(8,9),(10,8),(12,12),(9,12)],fill=3);d.point((7,8),fill=12)
    elif name=='key':
        d.line((7,7,12,12),fill=1,width=4);d.ellipse((2,2,9,9),fill=1)
        d.ellipse((3,3,8,8),fill=10);d.rectangle((5,5,6,6),fill=1)
        d.line((8,8,12,12),fill=10,width=2);d.line((11,13,13,11),fill=10,width=2)
        d.point((4,3),fill=12)
    elif name in ('heart','heart_piece','heart_container'):
        d.polygon([(2,5),(4,3),(6,3),(8,5),(10,3),(12,3),(14,5),(14,8),(8,14),(2,8)],fill=1)
        d.polygon([(3,5),(4,4),(6,4),(8,6),(10,4),(12,4),(13,5),(13,8),(8,12),(3,8)],fill=3)
        d.polygon([(4,5),(5,4),(7,6),(9,6),(10,5),(11,5),(9,8),(7,9),(4,7)],fill=4)
        d.point((4,5),fill=7)
        if name=='heart_piece':
            d.polygon([(10,4),(12,4),(13,5),(13,8),(8,12),(8,9),(10,7),(8,6)],fill=2)
            d.line([(9,5),(8,6),(10,7),(8,9),(8,12)],fill=1)
        if name=='heart_container':d.line([(2,5),(4,3),(6,3),(8,5),(10,3),(12,3),(14,5)],fill=6)
    elif name=='gilt':
        d.ellipse((4,4,11,13),fill=1);d.ellipse((5,5,10,12),fill=9)
        d.line((6,5,8,5),fill=12);d.line((7,7,7,10),fill=11)
    elif name=='gilt_big':
        d.polygon([(5,2),(11,2),(11,4),(9,6),(12,9),(13,12),(11,14),(3,14),(2,12),(3,8),(6,6),(4,4)],fill=1)
        d.polygon([(6,3),(10,3),(8,5),(6,5)],fill=6)
        d.polygon([(6,7),(9,7),(11,9),(11,12),(9,13),(4,12),(4,9)],fill=5)
        d.line((6,6,10,6),fill=10);d.line((5,9,5,11),fill=6);d.point((8,10),fill=11)
    elif name in ('relic','astrolabe'):
        d.ellipse((2,2,13,13),fill=1);d.ellipse((3,3,12,12),fill=8);d.ellipse((5,5,10,10),fill=2)
        d.arc((3,3,12,12),185,280,fill=11)
        if name=='relic':d.line((8,5,8,10),fill=12);d.line((5,8,10,8),fill=13)
        else:d.line((8,5,8,10),fill=10);d.line((5,8,10,8),fill=10);d.point((10,6),fill=12)
    elif name=='spark':
        d.polygon([(8,2),(9,6),(13,8),(9,9),(8,13),(6,9),(2,8),(6,6)],fill=9)
        d.line((8,4,8,11),fill=12);d.line((4,8,11,8),fill=11)
    elif name=='grail':
        d.polygon([(2,2),(13,2),(12,7),(10,9),(9,9),(9,12),(12,13),(12,14),(3,14),(3,13),(6,12),(6,9),(4,8)],fill=1)
        d.polygon([(3,3),(12,3),(11,6),(9,8),(6,8),(4,6)],fill=9)
        d.line((3,3,12,3),fill=12);d.line((4,4,5,6),fill=11);d.line((7,9,7,12),fill=10)
        d.line((4,13,11,13),fill=10);d.point((8,5),fill=15)
    elif name=='gauntlet':
        d.polygon([(4,14),(2,10),(2,7),(4,8),(4,4),(6,3),(7,5),(7,2),(9,2),(10,5),(11,3),(13,4),(12,9),(14,8),(14,10),(11,13),(10,14)],fill=1)
        d.polygon([(5,12),(3,9),(5,10),(5,5),(6,5),(6,9),(8,9),(8,3),(9,3),(9,9),(11,9),(12,5),(12,10),(10,12)],fill=8)
        d.line((8,4,8,7),fill=12);d.line((5,13,10,13),fill=10)
    elif name=='bow':
        d.line([(4,3),(8,4),(11,6),(12,9),(10,11),(6,13)],fill=1,width=3)
        d.line([(4,4),(8,5),(10,6),(11,9),(9,11),(6,12)],fill=6)
        d.line((4,4,6,12),fill=11);d.line((10,7,11,9),fill=8,width=2);d.point((6,3),fill=12)
    elif name in ('arrow1','arrow5','arrow10'):
        # Bundles stay in a12px box: shaft count conveys stack identity.
        offsets=(0,) if name=='arrow1' else (-1,1) if name=='arrow5' else (-2,0,2)
        for off in offsets:
            d.line((4+off,13,10+off,5),fill=1,width=3);d.line((4+off,13,10+off,5),fill=12)
            d.polygon([(8+off,4),(12+off,3),(11+off,7)],fill=7)
            d.line((3+off,10,6+off,12),fill=5,width=2)
    elif name=='hubcap':
        d.ellipse((2,2,13,13),fill=1);d.ellipse((3,3,12,12),fill=5);d.arc((3,3,12,12),185,280,fill=8)
        d.rectangle((7,7,8,8),fill=1)
        for x,y in ((5,4),(10,4),(4,10),(10,10)):d.point((x,y),fill=2)
    elif name=='map':
        d.polygon([(2,3),(6,2),(10,4),(13,2),(14,13),(10,14),(6,12),(2,14)],fill=1)
        d.polygon([(3,4),(6,3),(10,5),(12,4),(13,12),(10,13),(6,11),(3,12)],fill=11)
        d.line((6,4,6,10),fill=9);d.line([(4,8),(5,6),(9,8),(11,6)],fill=13)
    elif name=='sword':
        d.polygon([(10,2),(13,2),(13,5),(7,11),(4,8)],fill=1)
        d.line((6,8,12,3),fill=8,width=2);d.line((3,6,9,12),fill=13)
        d.line((3,12,5,10),fill=10,width=2)
    elif name in ('shield','shield_upgraded'):
        up=name.endswith('upgraded');d.polygon([(4,2),(11,2),(13,4),(12,10),(9,14),(6,13),(3,10),(2,4)],fill=1)
        d.polygon([(4,3),(10,3),(12,4),(11,9),(8,12),(4,9),(3,4)],fill=9 if up else 8)
        d.polygon([(5,4),(10,4),(10,9),(8,11),(5,9)],fill=13 if up else 5)
        d.line((4,3,10,3),fill=12)
        if up:
            d.line((8,5,8,10),fill=11);d.line([(6,6),(8,8),(10,6)],fill=11)
        else:d.point((7,7),fill=10)
    else:raise KeyError(name)
    return im


def menu(name):
    """Separate32px illustrations, broad quiet planes and simple identities."""
    im,d=_canvas(32)
    if name=='none':return im
    if name in ('bombs','bomb_pickup','bomb_lit'):
        d.ellipse((3,9,27,30),fill=1);d.ellipse((4,10,26,29),fill=4)
        d.polygon([(7,12),(12,10),(19,11),(23,16),(22,21),(16,24),(8,22),(6,18)],fill=12)
        d.polygon([(8,13),(12,11),(17,12),(19,15),(17,19),(10,19),(7,16)],fill=13)
        d.line([(9,12),(12,12),(13,13)],fill=14,width=2)
        d.line([(17,9),(17,5),(21,2),(26,3)],fill=1,width=4)
        d.line([(17,9),(17,5),(21,3),(26,3)],fill=10,width=2)
        d.line([(20,5),(22,4),(25,4)],fill=11)
    elif name=='lamp':
        d.arc((10,1,21,12),180,360,fill=1,width=3);d.arc((12,2,19,11),180,360,fill=10)
        d.line((10,6,10,9),fill=1,width=2);d.line((21,6,21,9),fill=1,width=2)
        d.line((11,6,11,8),fill=10)
        d.polygon([(7,8),(24,8),(27,11),(25,13),(25,26),(27,29),(4,29),(6,26),(6,13),(4,11)],fill=1)
        d.line((7,10,24,10),fill=10,width=2);d.line((7,12,24,12),fill=8)
        d.rectangle((8,13,23,25),fill=3);d.rectangle((11,13,20,25),fill=2)
        d.polygon([(15,25),(12,22),(13,18),(16,14),(16,18),(19,21),(18,24)],fill=10)
        d.line((15,20,15,23),fill=12,width=2)
        d.line((8,13,8,25),fill=11);d.line((23,13,23,25),fill=6)
        d.line((7,27,24,27),fill=10,width=2)
    elif name=='cloak':
        d.polygon([(10,1),(20,1),(25,6),(24,13),(29,28),(23,27),(19,30),(13,28),(4,30),(2,27),(7,14),(6,7)],fill=1)
        d.polygon([(7,14),(15,16),(23,13),(27,27),(23,25),(19,28),(13,26),(5,28),(4,27)],fill=4)
        d.polygon([(11,3),(19,3),(23,7),(22,12),(17,16),(10,13),(8,8)],fill=5)
        d.polygon([(13,5),(18,5),(20,8),(19,12),(13,12),(11,9)],fill=2)
        d.line([(17,3),(12,3),(9,6),(8,9),(10,12)],fill=7,width=2)
        d.polygon([(7,14),(12,17),(10,23),(5,28),(4,27)],fill=6)
        d.polygon([(8,15),(13,17),(11,24),(5,28),(4,27)],fill=6)
        d.polygon([(17,18),(22,14),(26,26),(22,25),(19,28),(15,26)],fill=5)
        d.line([(16,19),(14,26)],fill=3,width=2)
        d.line([(9,16),(7,23),(6,25)],fill=7)
        d.rectangle((14,14,17,17),fill=12);d.point((14,14),fill=7)
    elif name=='key':
        d.line((13,13,26,26),fill=1,width=7);d.ellipse((2,1,19,18),fill=1)
        d.line((14,14,26,26),fill=9,width=5);d.ellipse((4,3,17,16),fill=10)
        d.ellipse((8,7,13,12),fill=1);d.line([(6,5),(10,4),(13,4)],fill=12,width=2)
        d.line((21,26,25,22),fill=10,width=3);d.line((25,29,30,24),fill=10,width=3)
        d.line((15,16,21,22),fill=11)
    elif name in ('heart','heart_piece','heart_container'):
        d.polygon([(2,9),(7,4),(12,4),(16,8),(20,4),(25,4),(30,9),(30,15),(16,30),(2,15)],fill=1)
        d.polygon([(4,9),(8,6),(11,6),(16,11),(21,6),(24,6),(28,9),(28,15),(16,27),(4,15)],fill=3)
        d.polygon([(5,10),(8,7),(11,7),(16,12),(21,8),(24,9),(23,13),(16,20),(9,17),(5,14)],fill=4)
        d.line([(8,8),(10,8),(8,11)],fill=7,width=2)
        if name=='heart_piece':
            d.polygon([(20,7),(24,6),(28,9),(28,15),(16,27),(16,21),(20,17),(17,14),(19,11),(17,9)],fill=2)
            d.line([(18,9),(19,11),(17,14),(20,17),(16,21),(16,27)],fill=1,width=2)
        if name=='heart_container':
            d.line([(2,9),(7,4),(12,4),(16,8),(20,4),(25,4),(30,9)],fill=6)
            d.line([(3,16),(16,30),(29,16)],fill=5)
    elif name=='gilt_big':
        d.polygon([(9,2),(23,2),(24,6),(20,10),(27,17),(29,25),(24,30),(6,30),(2,25),(4,16),(12,10),(8,6)],fill=1)
        d.polygon([(11,4),(21,4),(19,7),(14,9),(11,7)],fill=6)
        d.polygon([(12,12),(19,12),(24,17),(26,24),(22,28),(8,28),(5,24),(7,18)],fill=5)
        d.line([(12,14),(9,18),(9,23)],fill=6,width=2)
        d.line((11,10,21,10),fill=10,width=2)
        d.ellipse((14,18,21,25),fill=9);d.line((17,19,17,23),fill=12)
    elif name in ('relic','astrolabe'):
        d.ellipse((2,2,29,29),fill=1);d.ellipse((4,4,27,27),fill=8)
        d.ellipse((8,8,23,23),fill=2);d.arc((4,4,27,27),185,285,fill=11,width=2)
        d.arc((4,4,27,27),0,85,fill=6,width=2)
        if name=='relic':
            d.polygon([(16,8),(18,13),(23,16),(18,18),(16,24),(13,18),(8,16),(13,13)],fill=13)
            d.line((16,11,16,21),fill=12,width=2);d.line((11,16,21,16),fill=11)
        else:
            d.line((16,9,16,23),fill=10,width=2);d.line((9,16,23,16),fill=10,width=2)
            d.line((16,16,22,10),fill=12,width=2)
            for x,y in ((16,5),(26,16),(16,26),(5,16)):d.rectangle((x-1,y-1,x+1,y+1),fill=10)
    elif name=='gauntlet':
        d.polygon([(7,30),(4,25),(1,17),(3,12),(7,15),(7,6),(10,3),(14,7),(14,1),(18,1),(20,7),(24,3),(28,5),(26,16),(30,13),(30,19),(24,26),(22,30)],fill=1)
        d.polygon([(8,25),(5,17),(7,19),(9,23),(9,7),(10,6),(12,9),(12,19),(16,19),(16,3),(18,3),(18,19),(22,19),(24,7),(26,6),(24,21),(28,17),(28,19),(22,25)],fill=8)
        d.line((10,7,10,14),fill=11,width=2);d.line((16,4,16,14),fill=12,width=2)
        d.rectangle((8,26,21,29),fill=9);d.line((8,26,21,26),fill=12)
    elif name=='bow':
        d.line([(7,2),(16,6),(23,12),(27,20),(22,25),(15,30)],fill=1,width=4)
        d.line([(7,3),(16,7),(22,12),(26,20),(21,25),(15,29)],fill=6,width=2)
        d.line((7,3,15,29),fill=11)
        d.line((23,15,25,20),fill=8,width=4);d.point((12,5),fill=12)
    elif name=='hubcap':
        d.ellipse((2,2,29,29),fill=1);d.ellipse((4,4,27,27),fill=5)
        d.polygon([(8,6),(13,4),(20,5),(25,10),(22,14),(12,12),(5,16)],fill=6)
        d.arc((4,4,27,27),185,285,fill=8,width=2);d.arc((6,6,25,25),10,90,fill=3,width=2)
        d.ellipse((12,12,19,19),fill=1)
        for x,y in ((10,8),(22,9),(8,22),(22,22)):d.ellipse((x-2,y-2,x+1,y+1),fill=2)
        d.line((9,6,14,5),fill=7)
    elif name=='map':
        d.polygon([(2,5),(11,2),(21,5),(28,2),(30,26),(21,30),(11,26),(3,30)],fill=1)
        d.polygon([(4,6),(11,4),(21,7),(26,5),(28,25),(21,28),(11,24),(5,27)],fill=11)
        d.line((11,5,11,23),fill=9);d.line((21,8,21,26),fill=9)
        d.line([(7,18),(9,14),(15,17),(19,12),(25,14)],fill=13,width=2)
        d.rectangle((23,11,26,14),fill=15);d.line((6,7,9,6),fill=12)
    elif name=='sword':
        d.polygon([(24,2),(29,2),(29,7),(13,23),(7,17)],fill=1)
        d.polygon([(25,4),(27,4),(27,6),(13,20),(10,17)],fill=7)
        d.line((12,17,25,4),fill=8,width=2);d.line((14,19,25,8),fill=6)
        d.line((5,14,18,27),fill=1,width=5);d.line((5,14,18,27),fill=13,width=2)
        d.line((4,27,10,21),fill=1,width=5);d.line((4,27,10,21),fill=10,width=3)
        d.rectangle((1,27,4,30),fill=1);d.point((2,28),fill=12)
    elif name in ('shield','shield_upgraded'):
        up=name.endswith('upgraded')
        d.polygon([(7,2),(24,2),(29,7),(27,21),(20,30),(11,30),(4,21),(2,7)],fill=1)
        d.polygon([(8,4),(23,4),(27,8),(25,20),(19,28),(12,28),(6,20),(4,8)],fill=9 if up else 8)
        d.polygon([(10,7),(22,7),(23,9),(21,19),(16,25),(10,19),(8,9)],fill=13 if up else 5)
        d.line((8,4,21,4),fill=12 if up else 11,width=2)
        if up:
            d.line((16,10,16,23),fill=11,width=2)
            d.line([(11,12),(16,16),(21,12)],fill=11,width=2)
            d.line([(11,18),(16,21),(21,18)],fill=11,width=2)
            d.point((16,8),fill=12)
        else:
            d.line((12,7,12,20),fill=3);d.line((20,7,20,20),fill=4)
            d.ellipse((12,13,19,20),fill=10);d.point((14,14),fill=12)
    else:raise KeyError(name)
    assert im.mode=='P' and im.size==(32,32) and max(im.getdata())<16
    return im


def preview(outdir):
    """Source-only comparison board and exact native RGBA/indexed frames."""
    import reboot_items as old
    root=Path(outdir);root.mkdir(parents=True,exist_ok=True)
    c=json.loads((Path(__file__).with_name('reboot_contracts.json')).read_text())
    identities=next(s['frames'] for s in c['sheets'] if s['name']=='icon32')
    cols=6;cw=150;ch=176
    board=Image.new('RGB',(cols*cw,44+((len(identities)+cols-1)//cols)*ch),'#101820');d=ImageDraw.Draw(board)
    d.text((8,8),'SOURCE ART: native HUD16 / menu32 / world16; 1x + integer zoom',fill='#f8e0a0')
    records=[]
    for i,name in enumerate(identities):
        x=i%cols*cw+8;y=44+i//cols*ch;d.text((x,y),name,fill='#f8e0a0')
        for mode,painter,yy in (('hud',hud,y+19),('menu',menu,y+67),('world',world,y+135)):
            native=painter(name);pal=R.PALETTES[old.material(name)]
            rgb=R.rgba(native,pal);big=rgb.resize((rgb.width*2,rgb.height*2),Image.Resampling.NEAREST)
            board.paste(big,(x,yy),big);board.paste(rgb,(x+76,yy+4),rgb)
            native.putpalette([v for color in pal for v in R.rgb(color)])
            native.save(root/f'{mode}-{name}-indexed.png',transparency=0)
            rgb.save(root/f'{mode}-{name}.png')
            records.append({'mode':mode,'name':name,'canvas':list(native.size),'bbox':native.getbbox(),'inks':sorted(set(native.getdata())-{0}),'material':old.material(name)})
    board.save(root/'items-source.png')
    (root/'items-source.json').write_text(json.dumps({'method':'Native indexed source drawings. Enlargements use nearest neighbour. Not emulator captures.','frames':records},indent=2)+'\n')
    return board


def export(outdir):
    """Export all65 implemented frames, not just the representative board."""
    import os,hashlib
    import reboot_items as I
    assert os.environ.get('BART_HUD','1')=='1'
    root=Path(outdir);root.mkdir(parents=True,exist_ok=True)
    contracts=json.loads((Path(__file__).with_name('reboot_contracts.json')).read_text())
    sheets=I.build_sheets(contracts);records=[]
    for family in ('items','pick32','icon32','huditems'):
        sh=sheets[family]
        for name,rs in sh['frames'].items():
            image=Image.new('P',(sh['w'],sh['h']),0)
            image.putdata([0 if ch=='.' else int(ch,16) for row in rs for ch in row])
            material=I.material(name);pal=R.PALETTES[material]
            image.putpalette([v for color in pal for v in R.rgb(color)])
            filename=f'{family}-{name}'
            image.save(root/(filename+'-indexed.png'),transparency=0)
            R.rgba(image,pal).save(root/(filename+'.png'))
            bbox=image.getbbox()
            records.append({'sheet':family,'frame':name,'canvas':list(image.size),
                            'visible_bbox':list(bbox) if bbox else None,
                            'visible_size':[bbox[2]-bbox[0],bbox[3]-bbox[1]] if bbox else [0,0],
                            'material':material,'palette_alias':sh['frame_pal'][name],
                            'palette_rgb555':[list(R.rgb(color)) for color in pal],
                            'inks':sorted(set(image.getdata())-{0}),
                            'indexed':filename+'-indexed.png','rgba':filename+'.png',
                            'indexed_sha256':hashlib.sha256((root/(filename+'-indexed.png')).read_bytes()).hexdigest(),
                            'rgba_sha256':hashlib.sha256((root/(filename+'.png')).read_bytes()).hexdigest()})
    preview(root/'representative')
    manifest={'method':'Native P/4bpp drawings, palette index0 transparent. RGB colors are authored RGB555-aligned multiples of8. No imported images or downscaling. Source art, not emulator captures.',
              'variant':1,'frame_count':len(records),'frames':records}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
