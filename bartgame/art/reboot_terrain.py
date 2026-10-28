"""Fresh native-resolution terrain for every retained metatile contract.

Only identifiers, layout and physical metadata come from reboot_contracts.
All pixels originate in this module or reboot_core. No old painter, image
pack, screenshot or indexed asset is imported.
"""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from PIL import Image,ImageDraw
import reboot_core as R

CONTRACTS=json.loads((Path(__file__).parent/'reboot_contracts.json').read_text())
COVERAGE={}


def rows(im):return [''.join('%x'%v for v in [im.getpixel((x,y)) for x in range(16)]) for y in range(16)]


def canvas(fill=0,w=16,h=16):return R.indexed(w,h,fill)


def crop(im,x,y):return im.crop((x,y,x+16,y+16))


def blit(dst,src,xy):
    # Pillow's palette0 is an explicit transparent ink, not a black floor.
    mask=src.point(lambda v:255 if v else 0,'1')
    dst.paste(src,xy,mask)


def spark(im,x,y,phase=0,white=15):
    d=ImageDraw.Draw(im);phase%=4
    if phase==0:d.point((x,y),fill=white)
    elif phase==1:
        d.line([(x-1,y),(x+1,y)],fill=white);d.line([(x,y-1),(x,y+1)],fill=white)
    elif phase==2:
        d.line([(x-2,y),(x+2,y)],fill=white);d.line([(x,y-2),(x,y+2)],fill=white)
    return im


def ground(variant=0,kind='grass'):
    if kind=='rot':
        im,d=canvas(9)
        if variant%3==0:d.polygon([(0,5),(5,2),(9,4),(12,10),(7,13),(0,11)],fill=10)
        if variant%3==1:d.line([(1,10),(6,8),(11,9)],fill=8)
        if variant%3==2:d.line([(8,3),(13,4),(15,7)],fill=11)
        return im
    if kind=='blight':
        im,d=canvas(2)
        if variant%3==0:d.polygon([(0,5),(5,2),(10,4),(13,9),(8,12),(0,10)],fill=3)
        if variant%3==1:d.line([(1,11),(6,9),(11,10)],fill=1)
        if variant%3==2:d.line([(9,3),(13,4),(15,7)],fill=3)
        return im
    im,d=canvas(4)
    if variant%3==0:d.polygon([(0,11),(4,9),(9,10),(11,15),(0,15)],fill=3)
    elif variant%3==1:d.line([(2,3),(4,3),(5,4)],fill=5)
    else:d.line([(10,10),(13,10),(14,11)],fill=3)
    if variant%7==5:d.line([(3,13),(4,11),(5,13)],fill=6)
    return im


def flowers(variant=0,large=False):
    im=ground(variant);d=ImageDraw.Draw(im)
    sites=[(4,7),(11,12)] if not large else [(3,4),(11,6),(7,12)]
    for x,y in sites:
        d.line([(x,y),(x,y+2)],fill=3);d.line([(x-1,y),(x+1,y)],fill=15)
        d.point((x,y-1),fill=15);d.point((x,y),fill=11)
    return im


def path_edge(mask=0,corners=0,variant=0):
    im,d=canvas(9)
    d.line([(3,11),(7,12),(11,10)],fill=8)
    d.line([(5,3),(9,3)],fill=10)
    for bit,edge in [(1,'n'),(2,'e'),(4,'s'),(8,'w')]:
        if not mask&bit:continue
        if edge=='n':d.polygon([(0,0),(15,0),(15,2),(11,3),(7,2),(3,4),(0,2)],fill=4);d.line([(0,3),(3,4),(7,2),(11,3),(15,2)],fill=8)
        elif edge=='s':d.polygon([(0,15),(15,15),(15,13),(10,12),(6,14),(2,12),(0,13)],fill=4);d.line([(0,12),(2,11),(6,13),(10,11),(15,12)],fill=8)
        elif edge=='w':d.polygon([(0,0),(2,0),(3,4),(2,8),(4,11),(2,15),(0,15)],fill=4);d.line([(3,0),(4,4),(3,8),(5,11),(3,15)],fill=8)
        else:d.polygon([(15,0),(13,0),(12,4),(13,8),(11,12),(13,15),(15,15)],fill=4);d.line([(12,0),(11,4),(12,8),(10,12),(12,15)],fill=8)
    for bit,pts in [(1,[(0,0),(5,0),(3,3),(0,5)]),(2,[(15,0),(10,0),(12,3),(15,5)]),(4,[(15,15),(10,15),(12,12),(15,10)]),(8,[(0,15),(5,15),(3,12),(0,10)])]:
        if corners&bit:d.polygon(pts,fill=4)
    return im


def grass_edge(mask=0,corners=0,kind='verge'):
    im=ground();d=ImageDraw.Draw(im)
    shade=2 if kind=='verge' else 8;lit=3 if kind=='verge' else 10
    for bit,pts,line in [
        (1,[(0,0),(15,0),(15,2),(11,3),(8,2),(5,4),(0,2)],[(1,3),(5,4),(8,2),(12,3)]),
        (2,[(15,0),(15,15),(13,15),(12,11),(13,8),(11,5),(13,0)],[(12,1),(11,5),(13,8),(12,12)]),
        (4,[(0,15),(15,15),(15,13),(10,12),(6,14),(2,12),(0,13)],[(1,12),(5,13),(8,12),(12,13)]),
        (8,[(0,0),(0,15),(2,15),(3,11),(2,8),(4,5),(2,0)],[(3,1),(4,5),(2,8),(3,12)])]:
        if mask&bit:d.polygon(pts,fill=shade);d.line(line,fill=lit)
    for bit,pts in [(1,[(0,0),(5,0),(3,3),(0,5)]),(2,[(15,0),(10,0),(12,3),(15,5)]),(4,[(15,15),(10,15),(12,12),(15,10)]),(8,[(0,15),(5,15),(3,12),(0,10)])]:
        if corners&bit:d.polygon(pts,fill=shade)
    return im


def rot_edge(sides=0,corners=0,variant=0):
    im=ground(variant,'rot');d=ImageDraw.Draw(im)
    # A shared bank carries exact living-grass and wine-soil inks together.
    for bit,pts in [(1,[(0,0),(15,0),(15,3),(12,2),(9,4),(6,2),(3,4),(0,3)]),(2,[(15,0),(15,15),(12,15),(13,12),(11,9),(13,6),(11,3),(12,0)]),(4,[(0,15),(15,15),(15,12),(11,13),(8,11),(5,13),(2,11),(0,12)]),(8,[(0,0),(0,15),(3,15),(2,11),(4,8),(2,5),(4,2),(3,0)])]:
        if sides&bit:d.polygon(pts,fill=3)
    for bit,pts in [(1,[(0,0),(6,0),(4,3),(3,4),(0,6)]),(2,[(15,0),(9,0),(11,3),(12,4),(15,6)]),(4,[(15,15),(9,15),(11,12),(12,11),(15,9)]),(8,[(0,15),(6,15),(4,12),(3,11),(0,9)])]:
        if corners&bit:d.polygon(pts,fill=3)
    return im


def canopy(variant=0,face=None,blighted=False,phase=0):
    im,d=canvas(2)
    patterns=[[(0,-2,10,8),(7,2,10,8),(-2,8,12,9)],[(2,-3,12,10),(-3,7,10,8),(9,9,10,8)], [(-3,-2,10,10),(5,2,12,10),(-2,10,10,8)]]
    for x,y,w,h in patterns[variant%3]:
        d.polygon([(x,y+3),(x+3,y),(x+w-2,y+1),(x+w,y+4),(x+w-3,y+h),(x+2,y+h-1)],fill=3)
        d.polygon([(x+2,y+3),(x+4,y+1),(x+w-3,y+2),(x+w-2,y+4),(x+4,y+5)],fill=4)
        d.line([(x+4,y+2),(x+w-4,y+2)],fill=5)
        if (x+y+variant)%3==0:d.point((x+4,y+2),fill=6)
    if blighted:
        d.line([(0,13),(6,9),(8,2)],fill=1,width=3);d.line([(0,13),(6,9),(8,2)],fill=8)
        d.line([(10,14),(12,10),(15,8)],fill=9)
        if variant%3==1:d.ellipse((9,3,12,7),fill=12);d.point((10,4),fill=14)
    if face=='s':
        d.rectangle((0,12,15,15),fill=1)
        d.line([(3,12),(3,15)],fill=9);d.line([(12,11),(12,15)],fill=8)
        d.polygon([(0,8),(4,9),(5,13),(3,12),(2,14),(1,11),(0,12)],fill=2)
        d.polygon([(7,8),(12,8),(15,10),(14,13),(12,11),(10,14),(9,11)],fill=3)
        d.line([(8,9),(11,9),(13,10)],fill=4)
    elif face=='n':
        d.rectangle((0,0,15,2),fill=1);d.line([(2,2),(6,2),(7,3),(12,2)],fill=3)
    return im


def water(mask=0,corners=0,phase=0,lily=False,rot=False):
    im,d=canvas(3)
    d.polygon([(0,10),(4,8),(8,9),(10,12),(15,11),(15,15),(0,15)],fill=2)
    d.line([(2+(phase&1),4),(6+(phase&1),4)],fill=5)
    d.line([(9-(phase&1),11),(13-(phase&1),11)],fill=4)
    if phase&1:d.line([(3,5),(5,5)],fill=6)
    for bit,edge in [(1,'n'),(2,'e'),(4,'s'),(8,'w')]:
        if not mask&bit:continue
        if edge=='n':d.polygon([(0,0),(15,0),(15,2),(10,1),(6,3),(0,2)],fill=10);d.line([(0,3),(5,3),(9,1),(14,2)],fill=9)
        elif edge=='s':d.rectangle((0,13,15,15),fill=9);d.line([(0,13),(15,13)],fill=11);d.line([(3,14),(8,14)],fill=12)
        elif edge=='w':d.polygon([(0,0),(2,0),(3,6),(1,9),(2,15),(0,15)],fill=10);d.line([(3,0),(4,5),(2,9)],fill=9)
        else:d.polygon([(15,0),(13,0),(12,6),(14,10),(13,15),(15,15)],fill=10);d.line([(12,1),(11,6),(13,10)],fill=9)
    for bit,pts in [(1,[(0,0),(5,0),(0,5)]),(2,[(15,0),(10,0),(15,5)]),(4,[(15,15),(10,15),(15,10)]),(8,[(0,15),(5,15),(0,10)])]:
        if corners&bit:d.polygon(pts,fill=10)
    if lily:
        d.ellipse((4,6,12,10),fill=9);d.line([(5,6),(10,6)],fill=11);d.line([(9,8),(12,10)],fill=3)
        d.point((6,6),fill=15)
    if rot:
        d.line([(2,9),(5,7),(9,8),(12,6)],fill=5);d.point((7+phase%2,8),fill=7)
    return im


def pit(rot=False,inner=False,phase=0):
    im,d=canvas(1)
    if inner:return im
    d.polygon([(0,0),(15,0),(15,2),(12,1),(10,3),(5,2),(2,3),(0,2)],fill=4 if rot else 4)
    d.line([(2,1),(6,0),(10,1),(13,0)],fill=6)
    d.rectangle((0,13,15,15),fill=3);d.line([(0,12),(3,13),(8,12),(12,13),(15,12)],fill=6)
    d.line([(2,15),(6,15)],fill=2)
    if rot:d.line([(11,0),(12,2),(10,4)],fill=12+phase%2)
    return im


def bridge(vertical=False):
    im,d=canvas()
    d.rectangle((0,1,15,14),fill=1)
    for x in range(0,16,4):
        d.rectangle((x+1,3,x+3,12),fill=4);d.line([(x+1,3),(x+3,3)],fill=6)
    d.line([(0,1),(15,1)],fill=8);d.line([(0,14),(15,14)],fill=7)
    return im.transpose(Image.Transpose.ROTATE_90) if vertical else im


def stone_wall(phase=0,rot=False,face=False):
    im,d=canvas(2)
    d.rectangle((0,1,15,6),fill=4);d.rectangle((0,9,15,14),fill=3)
    d.line([(0,0),(15,0)],fill=6);d.line([(0,8),(15,8)],fill=5)
    for x,y in [(5,1),(12,9)]:d.line([(x,y),(x,y+5)],fill=1);d.point((x+1,y+1),fill=6)
    if face:d.rectangle((0,13,15,15),fill=1)
    if rot:
        d.line([(12,0),(10,4),(12,8),(9,12),(10,15)],fill=12)
        d.point((11,8),fill=13+phase%2)
    return im


def ledger(mask=4):
    im,d=canvas(2)
    d.rectangle((0,0,15,4),fill=5);d.line([(0,0),(15,0)],fill=7)
    d.rectangle((0,5,15,13),fill=3)
    d.line([(3,5),(3,11)],fill=2);d.line([(10,8),(10,13)],fill=1)
    d.line([(0,14),(15,14)],fill=1);d.line([(1,15),(5,15),(6,14),(12,15)],fill=9)
    if mask==1:return im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return im


def gate(kind='crack',phase=0):
    im,d=canvas()
    if kind=='crack':
        im=stone_wall();d=ImageDraw.Draw(im)
        pts=[(9,0),(8,3),(10,5),(6,8),(8,10),(5,13),(6,15)]
        d.line([(x+1,y) for x,y in pts],fill=8,width=2);d.line(pts,fill=1,width=2)
        d.rectangle((2,6,3,7),fill=1);d.rectangle((11,11,12,12),fill=1)
        return im,'stone'
    if kind=='web':
        d.line([(0,0),(3,4),(12,13),(15,15)],fill=8)
        d.line([(15,0),(12,4),(3,12),(0,15)],fill=8)
        for pts in [[(2,7),(5,4),(10,4),(13,8),(10,11),(5,11),(2,7)],[(4,7),(6,5),(9,5),(11,8),(9,10),(6,10),(4,7)]]:d.line(pts,fill=15)
        for pts in [[(0,0),(7,7),(15,15)],[(15,0),(7,7),(0,15)],[(7,0),(7,15)],[(0,7),(15,7)]]:d.line(pts,fill=15)
        return im,'stone'
    if kind in ('locked','open'):
        d.rectangle((0,0,15,15),fill=1);d.line([(1,0),(1,15),(14,15),(14,0)],fill=6)
        if kind=='locked':
            d.rectangle((3,2,12,13),fill=12);d.line([(3,2),(12,2)],fill=15)
            d.rectangle((5,4,10,10),fill=15);d.ellipse((6,5,9,8),fill=1);d.line([(8,8),(8,10)],fill=1)
        else:d.line([(3,14),(12,14)],fill=12)
        return im,'stone'
    raise KeyError(kind)


def censer(lit=False,phase=0):
    im,d=canvas()
    d.ellipse((2,13,13,15),fill=1);d.line([(7,8),(7,13)],fill=5,width=3)
    d.rectangle((4,13,11,14),fill=12)
    d.polygon([(1,5),(14,5),(12,9),(9,11),(5,10),(2,8)],fill=1)
    d.line([(2,5),(13,5)],fill=15);d.line([(3,7),(5,9),(11,9),(13,7)],fill=12)
    if lit:
        d.polygon([(5,4),(6,2),(7,3),(8,0),(9,2),(11,3),(10,4)],fill=14)
        d.line([(7,4),(8,2),(9,4)],fill=15)
        if phase%2:d.point((6,1),fill=15)
    else:d.line([(6,4),(7,3),(9,4)],fill=5)
    return im


def prop_image(name):return R.lift_object(name)


def prop(name,phase=0):
    if name in ('bush','rock_small','boulder','myst_pot','pot'):return prop_image(name)
    im,d=canvas()
    if name in ('rock','rock2','rock3','mossy_stone','sick_rock'):
        im,_=R.lift_object('boulder');d=ImageDraw.Draw(im)
        if name in ('mossy_stone','sick_rock'):d.line([(2,6),(5,4),(8,5)],fill=6)
        return im,'stone'
    if name in ('stump','sick_stump'):
        d.ellipse((1,11,14,15),fill=1);d.polygon([(3,4),(12,4),(12,10),(15,13),(12,14),(3,14),(0,13),(3,10)],fill=1)
        d.rectangle((4,5,11,12),fill=9);d.ellipse((3,2,12,7),fill=10);d.ellipse((5,3,10,5),fill=8)
        d.line([(4,8),(4,12)],fill=11);d.line([(10,7),(11,11)],fill=8)
        return im,'foliage' if name=='stump' else 'blight'
    if name=='log':
        d.rectangle((0,5,15,13),fill=1);d.rectangle((0,6,15,11),fill=9);d.line([(0,6),(15,6)],fill=11)
        d.ellipse((0,5,5,13),fill=10);d.ellipse((1,7,3,11),fill=8);d.line([(8,8),(14,9)],fill=8)
        return im,'foliage'
    if name=='fence':
        for x in (1,11):d.rectangle((x,2,x+3,15),fill=1);d.line([(x+1,3),(x+1,14)],fill=10)
        d.rectangle((0,6,15,8),fill=9);d.line([(0,6),(15,6)],fill=11)
        return im,'foliage'
    if name=='thorn':
        for pts in [[(1,15),(5,9),(3,1)],[(7,15),(10,8),(15,5)],[(2,7),(9,3),(14,0)]]:d.line(pts,fill=1,width=3);d.line(pts,fill=8)
        for x,y in [(4,4),(6,9),(11,6),(10,2)]:d.polygon([(x,y),(x+3,y-2),(x+1,y+2)],fill=10)
        return im,'foliage'
    if name in ('pillar','ruin_wall'):
        d.rectangle((3,1,12,14),fill=1);d.rectangle((4,2,11,12),fill=4)
        d.line([(4,2),(4,12)],fill=7);d.line([(10,3),(10,12)],fill=3)
        d.rectangle((1,12,14,15),fill=1);d.line([(2,12),(13,12)],fill=6)
        d.rectangle((2,0,13,3),fill=5);d.line([(3,0),(12,0)],fill=8)
        if name=='ruin_wall':d.rectangle((0,4,15,11),fill=3);d.line([(0,4),(15,4)],fill=6);d.line([(7,4),(7,10)],fill=1)
        return im,'stone'
    if name=='statue':
        d.ellipse((2,12,13,15),fill=1);d.polygon([(4,13),(5,8),(4,6),(6,3),(9,3),(11,6),(10,8),(12,13)],fill=1)
        d.polygon([(5,12),(6,8),(5,6),(7,4),(9,5),(9,8),(11,12)],fill=4)
        d.line([(6,5),(7,4),(8,5)],fill=7);d.rectangle((6,9,9,11),fill=14);d.point((7,9),fill=15)
        return im,'stone'
    if name in ('bones','sick_bones'):
        d.line([(2,11),(11,5)],fill=1,width=3);d.line([(2,10),(11,4)],fill=15)
        for x,y in [(1,9),(10,3)]:d.rectangle((x,y,x+2,y+2),fill=15)
        d.ellipse((9,9,14,13),fill=1);d.ellipse((10,9,13,12),fill=15);d.point((11,11),fill=1)
        return im,'stone'
    if name=='leaf_litter':
        for x,y in [(2,10),(6,8),(10,12)]:d.line([(x,y),(x+2,y-1),(x+3,y+1)],fill=9);d.line([(x,y+1),(x+2,y)],fill=11)
        return im,'foliage'
    if name=='fern_patch':
        d.line([(8,15),(8,4)],fill=2)
        for y in (6,9,12):d.line([(8,y),(3,y-2),(5,y+1)],fill=4);d.line([(8,y),(13,y-2),(11,y+1)],fill=5)
        return im,'foliage'
    if name=='blight_crystal':
        for x,y,h in [(2,13,6),(7,14,13),(12,13,7)]:
            d.polygon([(x,y),(x-2,y-h+2),(x,y-h),(x+2,y-h+2),(x+2,y-1)],fill=1)
            d.line([(x,y-h+1),(x,y-1)],fill=13);d.line([(x+1,y-h+3),(x+1,y-2)],fill=12)
        d.point((7,3),fill=15)
        return im,'blight'
    if name in ('dead_tree','forest_blight_dead_tree'):
        for pts in [[(8,15),(7,7),(3,2)],[(8,10),(12,6),(14,0)],[(7,7),(7,1)]]:d.line(pts,fill=1,width=3);d.line(pts,fill=9)
        d.line([(8,14),(9,10),(8,7)],fill=13);d.point((12,5),fill=14)
        return im,'blight'
    if name=='lantern_post':
        d.line([(4,15),(4,1),(11,1),(11,4)],fill=1,width=3);d.line([(4,14),(4,1),(10,1)],fill=10)
        d.rectangle((8,4,14,11),fill=1);d.rectangle((9,5,13,9),fill=14);d.line([(10,5),(10,8)],fill=15)
        d.line([(8,10),(14,10)],fill=12)
        if phase%2:d.point((12,6),fill=15)
        return im,'stone'
    if name=='relic':
        d.polygon([(8,1),(13,8),(8,14),(3,8)],fill=1);d.polygon([(8,3),(11,8),(8,12),(5,8)],fill=14)
        d.line([(8,4),(8,11)],fill=15);d.line([(5,8),(11,8)],fill=15)
        return im,'stone'
    if name=='shrine_plate':
        d.ellipse((0,0,15,15),fill=1);d.ellipse((1,1,14,14),fill=4);d.ellipse((3,3,12,12),fill=2)
        for pts in [[(7,2),(7,13)],[(2,7),(13,7)],[(4,4),(11,11)],[(11,4),(4,11)]]:d.line(pts,fill=14)
        d.ellipse((6,6,9,9),fill=15)
        return im,'stone'
    raise KeyError('Unmapped prop '+name)


def spring(phase=0):
    im,d=canvas()
    d.ellipse((0,3,15,15),fill=1);d.ellipse((1,3,14,13),fill=4);d.ellipse((3,5,12,11),fill=2)
    d.arc((4,6,11,10),0,180,fill=6);d.line([(4,5),(11,5)],fill=7)
    spark(im,7,7,phase,15)
    return im


def myst_floor(style='cave',variant=0,edge=0):
    if style=='thicket':return ground(variant)
    im,d=canvas(3 if style=='cave' else 8)
    if style=='cave':
        d.line([(2,11),(6,10),(10,11)],fill=2)
        if variant:d.line([(10,3),(13,4),(15,7)],fill=4)
    else:
        d.line([(0,5),(5,4),(10,6),(15,5)],fill=9);d.line([(2,12),(7,11),(12,12)],fill=7)
    for bit,pts in [(1,[(0,0),(15,0),(15,2),(0,2)]),(2,[(13,0),(15,0),(15,15),(13,15)]),(4,[(0,13),(15,13),(15,15),(0,15)]),(8,[(0,0),(2,0),(2,15),(0,15)])]:
        if edge&bit:d.polygon(pts,fill=2 if style=='cave' else 7)
    return im


def exit_steps(style='cave'):
    im,d=canvas(1)
    for y in (2,6,10,14):
        d.line([(1,y),(14,y)],fill=6 if style=='cave' else 11)
        if y<14:d.line([(1,y+1),(14,y+1)],fill=3 if style=='cave' else 8)
    return im

@lru_cache(None)
def tree_group(kind='oak'):
    if kind in ('oak','lantern','birch','fir','sick','dead'):
        im=R.tree(kind in ('sick','dead'));d=ImageDraw.Draw(im)
        if kind=='birch':
            # The lower two metatiles have their own stone bank for pale bark.
            d.polygon([(13,32),(18,32),(19,40),(24,45),(20,46),(16,42),(12,47),(7,47),(11,42)],fill=6)
            d.line([(14,33),(14,39),(10,44)],fill=8)
            for y in (34,38,42):d.line([(15,y),(18,y+1)],fill=2)
        if kind=='fir':
            im,d=canvas(0,32,48)
            d.line([(15,10),(15,44)],fill=1,width=7);d.line([(14,30),(14,43)],fill=9,width=3)
            for y,w in [(0,9),(8,16),(16,24),(24,30)]:
                x=16-w//2
                d.polygon([(16,y),(x+w,y+12),(x+w-4,y+13),(x+w-2,y+16),(x+2,y+16),(x+4,y+13),(x,y+12)],fill=1)
                d.polygon([(16,y+2),(x+w-3,y+12),(x+3,y+12)],fill=3)
                d.line([(16,y+3),(x+5,y+11),(x+9,y+10)],fill=5)
            d.line([(14,43),(10,46),(6,47)],fill=9,width=2);d.line([(17,43),(23,47),(27,47)],fill=8,width=2)
        if kind=='lantern':
            d.line([(20,19),(24,20),(24,24)],fill=1)
            d.rectangle((21,24,27,31),fill=1);d.rectangle((22,25,26,29),fill=11);d.line([(23,25),(23,28)],fill=12)
        return im
    if kind in ('great','great_lantern'):
        im,d=canvas(0,48,64)
        # Multiple native leaf masses share a broad trunk; no scaled-up tree.
        blit(im,R.tree(),(0,0));blit(im,R.tree(),(16,1));blit(im,R.tree(),(8,13))
        d.polygon([(20,30),(27,30),(29,49),(33,56),(45,61),(44,63),(32,62),(25,56),(20,62),(4,63),(3,61),(15,57),(19,50)],fill=1)
        d.polygon([(21,33),(25,32),(26,48),(29,56),(24,53),(20,59),(12,61),(19,53)],fill=9)
        d.line([(21,34),(21,48),(18,56)],fill=11);d.line([(25,43),(26,51),(32,58)],fill=8)
        if kind=='great_lantern':
            d.line([(30,31),(34,32),(34,39)],fill=1);d.rectangle((31,39,37,46),fill=1);d.rectangle((32,40,36,44),fill=11);d.point((33,40),fill=12)
        return im
    if kind=='rotten_extensions':
        im,d=canvas(0,48,32)
        for pts in [[(0,28),(10,21),(12,8),(19,1)],[(9,30),(20,25),(27,13),(37,7)],[(20,29),(30,27),(45,31)]]:d.line(pts,fill=1,width=5);d.line(pts,fill=8,width=3);d.line(pts,fill=9)
        d.line([(24,24),(28,15),(32,13)],fill=13);d.point((28,15),fill=14)
        return im
    raise KeyError(kind)


@lru_cache(None)
def ground_group(kind):
    sizes={'meadow':(48,48),'clover':(32,32),'shroomring':(32,32),'gboulder':(32,32),'treerock':(32,32),'hlog':(32,16),'raft':(32,32)}
    w,h=sizes[kind];im,d=canvas(0,w,h)
    if kind in ('meadow','clover','shroomring'):
        for y in range(0,h,16):
            for x in range(0,w,16):im.paste(ground((x//16+y//16)%3),(x,y))
        if kind=='meadow':
            for x,y in [(4,9),(20,6),(36,11),(9,24),(28,26),(39,37),(14,40)]:
                d.line([(x,y+4),(x+2,y),(x+3,y+3)],fill=3);d.point((x+2,y),fill=6)
                d.line([(x+5,y+3),(x+6,y+1),(x+7,y+4)],fill=5)
                if x%3:d.line([(x+2,y-1),(x+4,y-1)],fill=15)
        elif kind=='clover':
            for x,y in [(5,5),(16,8),(10,19),(23,23)]:
                for dx,dy in [(-2,0),(2,0),(0,-2)]:d.ellipse((x+dx-1,y+dy-1,x+dx+2,y+dy+2),fill=5)
                d.line([(x,y),(x,y+4)],fill=3);d.point((x,y-2),fill=6)
        else:
            for x,y in [(4,7),(14,3),(23,9),(23,23),(11,26),(3,20)]:
                d.line([(x,y+2),(x,y+5)],fill=8)
                d.arc((x-3,y-2,x+3,y+3),180,360,fill=15,width=2);d.line([(x-2,y+1),(x+2,y+1)],fill=11)
        return im,'ground'
    if kind=='gboulder':
        d.polygon([(0,11),(5,4),(13,1),(22,3),(29,8),(31,16),(29,25),(23,30),(8,31),(1,26)],fill=1)
        d.polygon([(2,11),(7,5),(14,2),(22,5),(28,10),(29,18),(25,26),(10,28),(3,24)],fill=4)
        d.polygon([(4,10),(8,5),(14,3),(21,5),(22,10),(16,14),(7,16),(3,14)],fill=6)
        d.line([(8,6),(13,4),(17,5)],fill=7)
        d.polygon([(20,12),(28,10),(29,20),(24,26),(18,25)],fill=3)
        d.line([(8,27),(14,29),(22,28)],fill=2)
        return im,'stone'
    if kind=='treerock':
        rock,_=ground_group('gboulder');lut={0:0,1:1,2:13,3:14,4:15,6:15,7:7}
        for y in range(32):
            for x in range(32):im.putpixel((x,y),lut.get(rock.getpixel((x,y)),15))
        d.line([(16,7),(16,21)],fill=1,width=3);d.line([(16,8),(16,20)],fill=9)
        for x,y in [(10,4),(17,1),(21,8)]:
            d.polygon([(x,y+3),(x+3,y),(x+7,y+2),(x+5,y+7),(x+1,y+6)],fill=2)
            d.line([(x+2,y+2),(x+5,y+2)],fill=5)
        return im,'foliage'
    if kind=='hlog':
        d.rectangle((0,4,31,14),fill=1);d.rectangle((1,5,30,12),fill=9)
        d.line([(2,5),(29,5)],fill=11);d.line([(10,8),(16,9),(25,8)],fill=8)
        d.ellipse((0,4,8,14),fill=10);d.ellipse((2,6,6,12),fill=8);d.line([(3,7),(4,10)],fill=11)
        d.line([(20,11),(28,10)],fill=10)
        return im,'foliage'
    if kind=='raft':
        for y in range(0,32,16):
            for x in range(0,32,16):im.paste(water(),(x,y))
        d.rectangle((3,2,28,29),fill=1)
        for x in range(4,29,5):d.rectangle((x,3,x+3,28),fill=13);d.line([(x,4),(x,26)],fill=14)
        d.line([(3,9),(28,9)],fill=12);d.line([(3,24),(28,24)],fill=12)
        return im,'water'
    raise KeyError(kind)


def waterfall(phase=0,w=16,h=16):
    im,d=canvas(2,w,h)
    for x in range(1,w,4):
        d.line([(x,0),(x,h-1)],fill=3+(x//4)%3)
        y=(phase*3+x*2)%max(1,h-4)
        d.line([(x,y),(x,y+3)],fill=6)
    for x in range(2,w-2,5):d.line([(x,h-3),(x+2,h-2)],fill=8)
    return im


def sw_art(name,phase=0):
    """The retired named Drain tile vocabulary is redrawn, never imported."""
    suffix=name[3:]
    if suffix.startswith('floor'):
        im,d=canvas(3)
        d.line([(0,0),(15,0)],fill=5);d.line([(0,15),(15,15)],fill=1);d.line([(7,1),(7,14)],fill=2)
        if suffix in ('floor1','floor_crack','floor_crack2'):d.line([(2,1),(4,6),(3,9),(6,13)],fill=1)
        if suffix in ('floor2','floor_slime','floor_grime','floor_grime2','floor_moss','floor_moss2'):d.polygon([(0,8),(5,5),(10,7),(14,10),(11,13),(4,12),(0,14)],fill=9);d.line([(3,8),(7,7),(10,9)],fill=10)
        if suffix=='floor_puddle':d.ellipse((1,5,14,13),fill=2);d.line([(4+phase%2,7),(10+phase%2,7)],fill=6)
        if suffix=='floor_bones':blit(im,prop('bones')[0],(0,0))
        if suffix=='floor_shroom':
            d.line([(7,9),(7,13)],fill=8);d.arc((3,5,12,12),180,360,fill=15,width=2);d.point((8,6),fill=14+phase%2)
        if suffix=='floor_drip':spark(im,8,9,phase,8)
        return im,'drain'
    if suffix.startswith('wall'):
        im=stone_wall();d=ImageDraw.Draw(im)
        if any(k in suffix for k in ('slime','moss','fungus')):d.polygon([(0,1),(15,1),(13,5),(10,3),(9,10),(6,6),(4,12),(2,5)],fill=9);d.line([(5,2),(6,5),(7,4)],fill=11)
        if 'crack' in suffix:d.line([(12,0),(9,6),(11,9),(8,15)],fill=1)
        if 'chain' in suffix:
            for y in (1,5,9,13):d.ellipse((6,y,9,y+3),outline=7)
        if 'drip' in suffix:d.line([(3,0),(3,8)],fill=9);d.point((3,9+phase%4),fill=11)
        if 'web' in suffix:
            web,_=gate('web');blit(im,web,(0,0))
        if 'tally' in suffix:
            for x in (3,5,7,9):d.line([(x,4),(x,10)],fill=8)
            d.line([(2,10),(10,4)],fill=8)
        if 'window' in suffix:d.rectangle((3,2,12,13),fill=1);d.line([(7,3),(7,12)],fill=4);d.point((10,6),fill=14+phase%2)
        if 'skull' in suffix:
            d.ellipse((4,3,11,10),fill=8);d.point((6,6),fill=1);d.point((9,6),fill=1);d.rectangle((5,9,10,11),fill=7)
        if 'rust' in suffix:d.line([(2,2),(3,10),(5,13)],fill=12,width=2)
        return im,'drain'
    if suffix.startswith('water') or suffix=='lilypad':
        if suffix=='waterfall':return waterfall(phase),'water'
        im=water(phase=phase,lily=suffix=='lilypad');d=ImageDraw.Draw(im)
        if 'edge_n' in suffix:d.rectangle((0,0,15,3),fill=10);d.line([(0,3),(15,3)],fill=12)
        if 'edge_s' in suffix:d.rectangle((0,12,15,15),fill=9);d.line([(0,12),(15,12)],fill=11)
        if 'scum' in suffix:d.polygon([(0,5),(5,3),(9,6),(15,4),(15,9),(9,10),(6,8),(0,9)],fill=9)
        if 'bubble' in suffix:d.ellipse((5,5,9+phase%2,9+phase%2),outline=6)
        if 'glint' in suffix:spark(im,8,7,phase,8)
        return im,'water'
    if suffix.startswith('glint'):
        im=canvas()[0];return spark(im,8,8,phase,15),'drain'
    if suffix in ('ladder','ladder_down','hole','arch','arch_r'):
        im,d=canvas(1)
        d.line([(1,0),(1,15)],fill=6);d.line([(14,0),(14,15)],fill=3)
        if suffix in ('ladder','ladder_down','hole'):
            d.line([(5,0),(5,15)],fill=12);d.line([(10,0),(10,15)],fill=12)
            for y in (2,7,12):d.line([(5,y),(10,y)],fill=15)
        else:d.line([(2,1),(6,0),(12,1)],fill=8)
        return im,'drain'
    if suffix in ('pipe','pipe_h'):
        im,d=canvas();d.rectangle((5,0,11,15),fill=1);d.rectangle((6,0,10,15),fill=13);d.line([(6,0),(6,15)],fill=14);d.rectangle((4,5,12,8),fill=12);d.line([(5,5),(11,5)],fill=15)
        if suffix=='pipe_h':im=im.transpose(Image.Transpose.ROTATE_90)
        return im,'drain'
    if suffix in ('grate','grate_r') or suffix.startswith('drain_'):
        im,d=canvas(1);d.rectangle((0,0,15,15),outline=6)
        for y in (4,8,12):d.line([(1,y),(14,y)],fill=4)
        for x in (4,8,12):d.line([(x,1),(x,14)],fill=3)
        return im,'drain'
    if suffix in ('torch_lit','candles','lantern'):
        im=censer(True,phase)
        return im,'stone'
    if suffix in ('banner_teal','banner_red'):
        im,d=canvas();d.rectangle((2,0,13,13),fill=9 if suffix.endswith('teal') else 12);d.polygon([(2,13),(7,15),(13,13)],fill=9 if suffix.endswith('teal') else 12);d.line([(2,0),(13,0)],fill=14);d.line([(7,3),(7,10)],fill=15)
        return im,'drain'
    if suffix in ('counter','counter_r','crate','barrel'):
        im,d=canvas();d.rectangle((1,1,14,15),fill=1);d.rectangle((2,3,13,13),fill=12);d.line([(2,2),(13,2)],fill=14)
        if suffix=='barrel':d.line([(2,5),(13,5)],fill=6);d.line([(2,11),(13,11)],fill=5)
        else:d.line([(3,4),(12,12)],fill=13);d.line([(12,4),(3,12)],fill=13)
        return im,'drain'
    if suffix in ('awning_l','awning_r'):
        im,d=canvas()
        for x in range(0,16,4):d.rectangle((x,0,x+3,10),fill=9 if x%8 else 14);d.polygon([(x,10),(x+1,13),(x+3,11)],fill=9 if x%8 else 14)
        return im,'drain'
    if suffix.startswith('rug_'):
        im,d=canvas(9);d.rectangle((1,1,14,14),outline=14);d.line([(3,5),(12,5),(12,10),(3,10)],fill=10)
        return im,'drain'
    if suffix in ('rubble','skull','pot','gold'):
        if suffix=='pot':return prop('myst_pot')
        if suffix=='gold':return crop(R.pickup('coin'),0,0),'gold'
        if suffix=='skull':return prop('bones')
        return prop('rock_small')
    if suffix.startswith('fall_'):
        n=int(suffix.split('_')[-1]);return crop(waterfall(phase,48,32),(n%3)*16,(n//3)*16),'water'
    raise KeyError('Unmapped legacy Drain family '+name)

@lru_cache(None)
def drain_layers(phase=0):
    """The480x320hub, painted directly at native resolution in one bank.

    Brick, damp stone, scum, copper and ivory share a controlled resident
    material ramp. Original tile IDs and quarter collisions retain the room
    plan, including the real ladder at9,2 and the narrow central bridge.
    """
    g,d=canvas(3,480,320);o,od=canvas(0,480,320)
    # Quiet offset flagstones, not coloured rectangular floor patches.
    for y in range(64,272,16):
        d.line([(16,y),(463,y)],fill=2)
        for x in range(16+(8 if (y//16)%2 else 0),464,32):
            d.line([(x,y+1),(x,y+14)],fill=2)
            d.line([(x+1,y+1),(min(463,x+28),y+1)],fill=4)
    # Raised masonry has a lit upper lip and a dark near face.
    for y in range(0,64,8):
        d.rectangle((0,y,479,y+6),fill=3 if (y//8)%2 else 4)
        d.line([(0,y),(479,y)],fill=5)
        for x in range(-8 if (y//8)%2 else 8,480,24):
            d.line([(x,y+1),(x,y+6)],fill=1)
            d.point((x+1,y+1),fill=6)
    d.line([(0,62),(479,62)],fill=6);d.line([(0,63),(479,63)],fill=1)
    for x in (0,464):
        d.rectangle((x,64,x+15,271),fill=2)
        for y in range(64,272,16):d.rectangle((x+1,y+1,x+14,y+13),fill=4);d.line([(x+1,y+1),(x+12,y+1)],fill=6)
    # The sewage channel and its two usable bridge landings.
    d.rectangle((16,144,463,207),fill=1)
    d.rectangle((16,154,463,192),fill=2)
    for y in range(157,190,8):
        for x in range(18,460,24):
            d.line([(x+(phase%3),y),(x+7+(phase%3),y)],fill=9)
            if (x//24+y//8)%4==0:d.line([(x+2,y+1),(x+5,y+1)],fill=10)
    # Scum is an accumulation on a bank; the middle stays visibly liquid.
    for x in (24,87,156,295,376,424):
        d.polygon([(x,154),(x+25,154),(x+23,158),(x+16,157),(x+12,161),(x+5,159),(x,160)],fill=9)
        d.line([(x+4,155),(x+10,156),(x+16,155)],fill=11)
    d.rectangle((16,144,463,150),fill=4);d.line([(16,144),(463,144)],fill=7);d.line([(16,151),(463,151)],fill=1)
    d.rectangle((16,193,463,207),fill=3);d.line([(16,193),(463,193)],fill=6);d.line([(16,207),(463,207)],fill=1)
    # Posts/rail shadow are shared overlay tiles, preserving their repeated IDs.
    for x in range(16,464,32):
        if 224<=x<256:continue
        d.line([(x+7,142),(x+7,150)],fill=12,width=3)
        od.rectangle((x+6,132,x+8,143),fill=1);od.line([(x+7,133),(x+7,141)],fill=14);od.point((x+7,132),fill=15)
    for y in range(144,208,4):
        d.rectangle((225,y,254,min(207,y+2)),fill=12)
        d.line([(226,y),(253,y)],fill=14);d.line([(226,min(207,y+3)),(253,min(207,y+3))],fill=1)
    d.line([(224,144),(224,207)],fill=13);d.line([(255,144),(255,207)],fill=12)
    # Lower coping, hanging moss and the dark water beneath the playable floor.
    d.rectangle((0,272,479,287),fill=2);d.line([(16,272),(463,272)],fill=7)
    d.rectangle((0,288,479,319),fill=2)
    for y in (293,301,311):
        for x in range(4,480,24):d.line([(x+phase%2,y),(x+8+phase%2,y)],fill=9)
    for x in range(16,464,16):
        d.line([(x,275),(x,283)],fill=1)
        d.polygon([(x+2,273),(x+8,273),(x+7,281),(x+5,279),(x+4,287),(x+2,281)],fill=9)
        d.line([(x+3,274),(x+4,280)],fill=10)
    for x in range(16,448,16):
        od.line([(x+1,260),(x+1,271)],fill=1,width=3);od.line([(x+1,261),(x+1,270)],fill=14)
        od.line([(x,267),(x+15,267)],fill=12);od.line([(x,266),(x+15,266)],fill=14)
    # The cistern is visibly barred and pours into an impassable basin.
    d.ellipse((184,0,292,89),fill=1);d.ellipse((190,4,286,84),fill=4)
    d.ellipse((199,13,277,83),fill=1)
    for x in range(205,275,12):d.line([(x,24),(x,72)],fill=5,width=3);d.line([(x-1,25),(x-1,65)],fill=7)
    d.line([(202,42),(274,42)],fill=3,width=3)
    d.ellipse((192,62,287,105),fill=1);d.ellipse((194,64,285,103),fill=5);d.ellipse((198,66,281,98),fill=2)
    d.arc((194,64,285,103),0,180,fill=7,width=2)
    for x in range(226,252,4):
        d.line([(x,27),(x,88)],fill=9 if x%8 else 10,width=3)
        y=(phase*3+x)%45+31;d.line([(x,y),(x,y+7)],fill=11)
    for x in range(219,260,9):d.arc((x,81,x+14,91),0,180,fill=11)
    # The functional forest ladder is wide, pale-runged and warmly framed.
    ladder=R.portal('cave');mapped=Image.new('P',ladder.size)
    lut={0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:12,10:13,11:13,12:13,13:14,14:14,15:15}
    mapped.putdata([lut[v] for v in ladder.getdata()]);blit(g,mapped,(136,18))
    d.rectangle((144,30,159,63),fill=1)
    d.line([(146,29),(146,63)],fill=12,width=2);d.line([(157,29),(157,63)],fill=12,width=2)
    for y in range(32,64,5):d.line([(147,y),(156,y)],fill=14);d.point((148,y),fill=15)
    d.line([(149,27),(154,27)],fill=11);d.line([(144,63),(159,63)],fill=15)
    d.rectangle((145,19,159,25),fill=1);d.line([(146,20),(158,20)],fill=14);d.point((151,22),fill=15)
    d.line([(140,35),(140,44)],fill=14);d.line([(164,35),(164,44)],fill=13)
    d.line([(143,21),(141,18),(143,16)],fill=11);d.line([(161,22),(165,20),(165,17)],fill=10)
    # Only the frame, not its dark aperture, belongs in front of Bloom.
    for yy in range(16,48):
        for xx in range(128,176):
            v=g.getpixel((xx,yy))
            if v and (xx<144 or xx>159 or yy<29):o.putpixel((xx,yy),v)
    # Copper pipes pick up the same warm specular ink as treasure.
    d.rectangle((18,32,125,41),fill=1);d.rectangle((18,33,124,38),fill=12);d.line([(19,33),(122,33)],fill=14)
    for x in (27,55,88,116):d.rectangle((x,31,x+3,42),fill=13);d.line([(x,31),(x+2,31)],fill=15)
    d.line([(423,6),(423,62)],fill=1,width=10);d.line([(421,6),(421,60)],fill=13,width=6);d.line([(419,7),(419,59)],fill=14)
    for y in (12,35,54):d.rectangle((417,y,427,y+3),fill=12);d.line([(418,y),(425,y)],fill=14)
    # A cramped shop with shared brass, green cloth and wet wood.
    d.rectangle((16,64,127,110),fill=1);d.rectangle((19,66,124,108),fill=12)
    for x in range(16,128,8):
        d.rectangle((x,57,x+7,76),fill=9 if x%16 else 13)
        d.polygon([(x,76),(x+2,80),(x+5,80),(x+7,76)],fill=9 if x%16 else 13)
        d.line([(x+1,58),(x+5,58)],fill=14)
    d.rectangle((24,87,111,109),fill=12);d.line([(25,88),(110,88)],fill=14)
    for x in (33,55,77,99):d.line([(x,91),(x,108)],fill=1);d.line([(x+1,92),(x+1,104)],fill=13)
    d.rectangle((24,93,111,97),fill=1);d.line([(25,93),(110,93)],fill=15)
    # Preserve the authored counter occlusion footprint with a shallow near face.
    od.rectangle((32,94,111,106),fill=12);od.line([(33,94),(110,94)],fill=15)
    od.line([(33,104),(110,104)],fill=13)
    for x in (43,67,91):od.line([(x,97),(x,104)],fill=1)
    for x,y in [(38,82),(99,81)]:
        d.rectangle((x,y-5,x+4,y+6),fill=1);d.rectangle((x+1,y-3,x+3,y+4),fill=10);d.point((x+2,y-3),fill=15)
    # Keeper's worn teal rug, shelf and brass candles.
    d.rectangle((304,71,382,111),fill=1);d.rectangle((307,74,379,108),fill=9)
    d.rectangle((310,77,376,105),outline=14)
    d.line([(314,84),(368,84),(368,99),(314,99)],fill=10)
    d.rectangle((288,62,382,68),fill=12);d.line([(289,62),(380,62)],fill=14)
    for x in (299,310,363,374):
        d.line([(x,53),(x,61)],fill=8,width=2);d.point((x,51),fill=15);d.point((x+phase%2,52),fill=14)
    # Two storage masses match the already solid quarter-grid.
    for x in (400,424):
        d.rectangle((x,65,x+23,94),fill=1);d.rectangle((x+2,67,x+21,91),fill=12)
        d.line([(x+3,68),(x+20,88)],fill=13,width=2);d.line([(x+20,68),(x+3,88)],fill=13,width=2);d.line([(x+2,67),(x+20,67)],fill=14)
    d.ellipse((440,72,458,95),fill=1);d.ellipse((442,73,456,93),fill=12)
    d.line([(442,78),(456,78)],fill=6);d.line([(442,89),(456,89)],fill=5)
    # Grease and dripping lichen are located below the pipes and bank edges.
    for x,y in [(28,43),(87,43),(429,62),(166,108),(368,116),(50,224),(389,246)]:
        d.polygon([(x,y),(x+20,y),(x+17,y+5),(x+13,y+3),(x+11,y+11),(x+7,y+7),(x+3,y+13),(x,y+5)],fill=9)
        d.line([(x+5,y+1),(x+7,y+5),(x+9,y+3)],fill=10)
    for x,y in [(139,101),(320,122),(88,228),(322,228),(213,209)]:
        d.polygon([(x,y+3),(x+7,y),(x+17,y+2),(x+24,y+7),(x+17,y+10),(x+8,y+8),(x+2,y+10)],fill=2)
        d.line([(x+5,y+3),(x+10,y+2),(x+17,y+4)],fill=9)
    # A corroded outfall pours visibly into the channel, not onto the floor.
    d.rectangle((431,116,443,141),fill=1);d.rectangle((433,116,441,139),fill=12);d.line([(433,117),(433,136)],fill=14)
    d.ellipse((427,134,448,146),fill=1);d.ellipse((430,135,445,144),fill=13);d.ellipse((433,136,442,141),fill=1)
    d.polygon([(434,141),(441,141),(443,164),(448,170),(445,175),(431,175),(428,170),(433,163)],fill=9)
    d.line([(436,143),(435,164),(432,170)],fill=11)
    # The lower floor's big barred drain is walkable metal, never a false pit.
    d.ellipse((207,225,273,255),fill=1);d.ellipse((209,226,271,253),fill=5);d.ellipse((214,229,266,249),fill=1)
    for x in range(219,265,7):d.line([(x,230),(x,248)],fill=5);d.line([(x-1,231),(x-1,246)],fill=7)
    for y in (234,241,247):d.line([(216,y),(264,y)],fill=3)
    d.arc((209,226,271,253),180,360,fill=8,width=2)
    # Small, authored glints coexist with engine surface-aware dew.
    for i,(x,y) in enumerate([(33,34),(119,33),(151,30),(225,16),(261,83),(295,62),(372,62),(438,137),(219,229),(265,246)]):spark(g,x,y,phase+i,15)
    return g,o


@lru_cache(None)
def drain_occurrences():
    result={}
    for layer in ('ground','overlay'):
        for y,row in enumerate(CONTRACTS['rooms'][0][layer]):
            for x,n in enumerate(row):
                if n is not None:result.setdefault(n,[]).append((layer,x,y))
    return result


def drain_repeated_tile(name,phase=0):
    positions=drain_occurrences()[name]
    layer,x,y=positions[0]
    if layer=='overlay':return None
    if len(positions)==1:return None
    # A reused background ID must remain a reusable material. Taking an
    # arbitrary crop of a large object would repeat that object's corner in
    # distant floor cells; these are deliberate matching plain panels.
    c=next(t for t in CONTRACTS['tiles'] if t['name']==name)
    if y<4:
        im,d=canvas(3)
        for yy in (0,8):
            d.rectangle((0,yy+1,15,yy+6),fill=4);d.line([(0,yy),(15,yy)],fill=5)
            d.line([(7 if yy==0 else 3,yy+1),(7 if yy==0 else 3,yy+6)],fill=1)
        return im
    if all(xx in (14,15) and 9<=yy<=12 for _,xx,yy in positions):
        im,d=canvas(12)
        for yy in (0,4,8,12):d.line([(0,yy),(15,yy)],fill=14);d.line([(0,yy+3),(15,yy+3)],fill=1)
        d.line([(0 if x==14 else 15,0),(0 if x==14 else 15,15)],fill=13)
        return im
    if c['coll']==0:
        im,d=canvas(3);d.line([(0,0),(15,0)],fill=2);d.line([(0,1),(15,1)],fill=4)
        d.line([(7 if int(name[4:])%2 else 11,2),(7 if int(name[4:])%2 else 11,14)],fill=2)
        return im
    if c['coll']==12 and y<9:
        im,d=canvas(3);d.rectangle((0,0,15,6),fill=4);d.line([(0,0),(15,0)],fill=7);d.line([(0,7),(15,7)],fill=1)
        return im
    if y==9:
        im,d=canvas(1);d.rectangle((0,0,15,6),fill=4);d.line([(0,0),(15,0)],fill=7);d.rectangle((0,10,15,15),fill=2)
        return im
    if y in (10,11,18,19):
        im,d=canvas(2)
        d.line([(2+phase%2,5),(9+phase%2,5)],fill=9)
        d.line([(8-phase%2,12),(14-phase%2,12)],fill=10)
        return im
    if y==12:
        im,d=canvas(3);d.line([(0,1),(15,1)],fill=6);d.line([(7,3),(7,15)],fill=2)
        return im
    if y==17:
        im,d=canvas(2);d.line([(0,0),(15,0)],fill=7);d.line([(0,3),(15,3)],fill=1)
        d.polygon([(3,1),(8,1),(8,9),(6,7),(5,14),(3,8)],fill=9);d.point((4,3),fill=10)
        return im
    im,d=canvas(3);d.line([(0,0),(15,0)],fill=2);d.line([(7,1),(7,14)],fill=2)
    return im


@lru_cache(None)
def drain_positions():
    room=CONTRACTS['rooms'][0];pos={}
    for layer in ('ground','overlay'):
        for y,row in enumerate(room[layer]):
            for x,n in enumerate(row):
                if n is not None and n not in pos:pos[n]=(layer,x,y)
    return pos


def paint(name,phase=0):
    """Return(image,bank,family,glitter) for an explicitly named family."""
    if name.startswith('swh_'):
        layer,x,y=drain_positions()[name]
        g,o=drain_layers(phase)
        repeat=drain_repeated_tile(name,phase)
        return (repeat if repeat is not None else crop(g if layer=='ground' else o,x*16,y*16)),'drain','painted-drain-'+('repeated-material' if repeat is not None else layer),layer=='overlay' or y<4 or 9<=y<=12 or y>=17 or (x+y)%7==0
    if name.startswith('sw_'):
        im,pal=sw_art(name,phase)
        reflective=any(s in name for s in ('water','pipe','torch','candle','lantern','grate','drain','glint','wall','puddle'))
        return im,pal,'named-drain-material',reflective
    if name=='black':return canvas(1)[0],'ground','closed-void',False
    if name.startswith(('pedge_','verge_','shore_')):
        family,code=name.split('_',1);corner=code.startswith('c') and len(code)>1;mask=int(code[1:] if corner else code,16)
        im=path_edge(corners=mask) if family=='pedge' and corner else path_edge(mask) if family=='pedge' else grass_edge(corners=mask,kind=family) if corner else grass_edge(mask,kind=family)
        return im,'ground',family+'-transition',family=='shore'
    if name.startswith('rot_'):
        sides,corners=[int(v,16) for v in name[4:]]
        return rot_edge(sides,corners),'decay_mix','living-rot-transition',False
    if name.startswith('water_c') and len(name)>7:
        return water(corners=int(name[7:],16),phase=phase),'water','water-inner-corner',True
    if name=='water' or name.startswith('water_'):
        if name=='water_lily':im=water(phase=phase,lily=True)
        elif name=='water_foam':
            im=water(phase=phase);d=ImageDraw.Draw(im);d.line([(0,8),(4,6),(8,8),(12,6),(15,8)],fill=8)
        else:im=water(int(name[6:],16),phase=phase) if name!='water' else water(phase=phase)
        return im,'water','water-surface-or-bank',True
    if name=='waterfall':return waterfall(phase),'water','falling-water',True
    if name in ('moss0','moss1','moss2','moss_shade','tall_grass','moss_flowers','moss_flowers2','path','path_edge_n'):
        if name.startswith('moss_flowers'):im=flowers(1 if name.endswith('2') else 0,name.endswith('2'))
        elif name=='path':im=path_edge()
        elif name=='path_edge_n':im=path_edge(1)
        elif name=='tall_grass':
            im=ground();d=ImageDraw.Draw(im)
            for x,y in [(2,7),(8,4),(10,12)]:d.line([(x,y+3),(x+1,y),(x+2,y+3)],fill=3);d.line([(x+1,y),(x+1,y+2)],fill=6)
        elif name=='moss_shade':im=ground(0);d=ImageDraw.Draw(im);d.polygon([(0,0),(15,0),(12,5),(9,4),(5,7),(0,5)],fill=3)
        else:im=ground(int(name[-1]))
        return im,'ground','living-floor',False
    if name in ('moss_blight','moss_blight2'):
        return rot_edge(15 if name=='moss_blight' else 11),'decay_mix','early-decay-stain',False
    if name.startswith('forest_rot'):
        n=int(name[10:]);im=rot_edge(0,0,n);d=ImageDraw.Draw(im)
        if n&1:d.polygon([(0,0),(7,0),(4,3),(0,5)],fill=3)
        if n&2:d.polygon([(15,15),(9,15),(12,12),(15,10)],fill=3)
        return im,'decay_mix','mixed-decay-earth',False
    if name.startswith('blight_ground'):
        im=ground(int(name[-1]),'rot')
        if name.endswith('2'):
            d=ImageDraw.Draw(im);d.line([(2,14),(5,9),(8,7),(9,2)],fill=8);d.point((6,9),fill=11+phase)
        return im,'decay_mix','stained-earth',name.endswith('2')
    if name in ('blight_floor','blight_floor2','blight_vein') or name.startswith('forest_blight_vein'):
        im=ground(0,'blight');d=ImageDraw.Draw(im)
        if name!='blight_floor':
            n=int(name[-1]) if name.startswith('forest_blight_vein') else 0
            pts=[(0,11),(4,9),(6,5),(11,3),(15,4)]
            d.line(pts,fill=1,width=2);d.line([(x,y+1) for x,y in pts],fill=8)
            if name!='blight_floor2':d.line([(5,9),(8,11),(13,10)],fill=12)
            d.point((6+n%3,6),fill=12+phase%2)
        return im,'blight','deep-earth-or-exposed-vein',name!='blight_floor'
    if name in ('blight_wall','blight_wall2','blight_wall_lit'):
        im=stone_wall(phase,True);d=ImageDraw.Draw(im)
        if name=='blight_wall2':
            d.line([(2,0),(3,6),(1,10),(4,15)],fill=8,width=2);d.line([(0,3),(7,6),(10,10)],fill=9)
        if name=='blight_wall_lit':
            d.line([(8,0),(8,4)],fill=9);d.ellipse((5,4,11,12),fill=1);d.ellipse((6,5,10,11),fill=12+phase%2);d.line([(8,6),(8,9)],fill=15)
        return im,'blight','wet-corrupt-masonry',True
    if name=='blight_pool':
        im,d=canvas(2);d.polygon([(0,6),(3,2),(10,1),(15,4),(15,12),(12,15),(4,14),(0,11)],fill=1)
        d.line([(2,6),(5,4),(9,5),(12,3)],fill=4);d.line([(4,11),(8,12),(12,9)],fill=5)
        spark(im,9,8,phase+1,8)
        return im,'rot_water','stagnant-wine-pool',True
    if name=='blight_mist':
        im,d=canvas();y=8+phase*2
        d.line([(0,y),(4,y-2),(9,y-1),(15,y-3)],fill=3,width=2)
        d.line([(0,y+3),(5,y+1),(10,y+2),(15,y)],fill=4)
        return im,'blight','low-decay-mist',False
    if name.startswith('canopy') or name.startswith('forest_canopy'):
        n=int(name[-1]) if name.startswith('forest_canopy') else 1 if name.endswith('2') else 0
        rot='blight' in name;face='s' if name=='canopy_s' else 'n' if name=='canopy_n' else None
        im=canopy(n,face,rot,phase);d=ImageDraw.Draw(im)
        if name=='canopy_lantern':
            d.line([(10,3),(10,8)],fill=9);d.rectangle((7,8,13,14),fill=1);d.rectangle((8,9,12,12),fill=11);d.line([(9,9),(9,11)],fill=12)
            if phase&1:d.point((11,10),fill=12)
        elif name=='canopy_glint':d.point((5,5),fill=7)
        return im,'blight' if rot else 'foliage','connected-corrupt-canopy' if rot else 'connected-living-canopy',True
    tree_names=['tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e','tree_trunk_w','tree_trunk_e']
    if name in tree_names:
        n=tree_names.index(name);return crop(tree_group('oak'),(n%2)*16,(n//2)*16),'foliage','oak-tree',True
    for prefix,kind in [('tree2_','lantern'),('birch_','birch'),('fir_','fir'),('sicktree_','sick')]:
        if name.startswith(prefix):
            n=int(name[len(prefix):]);pal='blight' if kind=='sick' else 'stone' if kind=='birch' and n>=4 else 'foliage'
            return crop(tree_group(kind),(n%2)*16,(n//2)*16),pal,kind+'-tree',True
    for prefix,kind in [('gtree_','great'),('gtree2_','great_lantern')]:
        if name.startswith(prefix):
            n=int(name[len(prefix):]);return crop(tree_group(kind),(n%3)*16,(n//3)*16),'foliage','great-tree',True
    if name.startswith('btree_'):
        n=int(name[6:])
        if n<6:return crop(tree_group('dead'),(n%2)*16,(n//2)*16),'blight','bare-corrupt-tree',True
        n-=6;return crop(tree_group('rotten_extensions'),(n%3)*16,(n//3)*16),'blight','reserved-corrupt-root-extensions',True
    if name.startswith('forest_blight_tree'):
        n=int(name[-1]);im=canopy(1,None,True);blit(im,crop(tree_group('dead'),(n%2)*16,(n//2)*16),(0,0))
        return im,'blight','corrupted-wall-tree',True
    for prefix,w,kind in [('meadow_',3,'meadow'),('clover_',2,'clover'),('shroomring_',2,'shroomring'),('gboulder_',2,'gboulder'),('treerock_',2,'treerock'),('hlog_',2,'hlog'),('raft_',2,'raft')]:
        if name.startswith(prefix):
            n=int(name[len(prefix):]);source,pal=ground_group(kind);im=crop(source,(n%w)*16,(n//w)*16)
            if kind=='raft' and phase&1:
                d=ImageDraw.Draw(im);d.line([(0,0),(2,0)],fill=6)
            return im,pal,'native-'+kind+'-group',kind in ('raft','shroomring')
    if name in ('ledge_s','ledge_s_w','ledge_s_e','ledge_n'):
        return ledger(1 if name=='ledge_n' else 4),'stone','raised-ledge',False
    if name in ('bridge','bridge_v'):return bridge(name.endswith('_v')),'gold','bridge-planks',True
    if name in ('pit','pit_inner','forest_blight_pit'):
        rot=name=='forest_blight_pit';return pit(rot,name=='pit_inner',phase),'blight' if rot else 'stone','recessed-pit',False
    if name in ('crack','web','door_locked','door_open'):
        im,pal=gate({'crack':'crack','web':'web','door_locked':'locked','door_open':'open'}[name],phase)
        return im,pal,'interactive-barrier',name.startswith('door')
    if name in ('torch','torch_lit'):return censer(name.endswith('lit'),phase),'stone','candle-censer',True
    if name in ('chest','chest_open','myst_chest','myst_chest_open'):
        im=R.chest(0,name.endswith('open'));return crop(im,8,13),'gold','fallback-chest',True
    if name in ('sparkle','sparkle_white'):
        im=canvas()[0];return spark(im,8,8,phase+1,12 if name=='sparkle' else 15),'gold' if name=='sparkle' else 'stone','surface-sparkle',False
    if name=='stairs_down':
        im,d=canvas(1)
        d.line([(1,0),(1,15),(14,15),(14,0)],fill=4)
        for y in (2,6,10,14):d.line([(3,y),(12,y)],fill=6);d.line([(3,y+1),(12,y+1)],fill=2)
        return im,'stone','descending-stair-opening',True
    if name.startswith('mouth_'):
        style=name[6:];im,d=canvas(1)
        d.line([(1,14),(1,6),(4,2),(8,0),(12,2),(14,6),(14,14)],fill=6)
        d.line([(3,14),(12,14)],fill=14 if style=='cave' else 12)
        return im,'stone' if style=='cave' else 'gold','small-portal-fallback',True
    if name in ('myst_switch','myst_switch_down'):return R.plate(name.endswith('down')),'stone','flat-pressure-plate',name.endswith('down')
    if name in ('myst_spring',):return spring(phase),'water','healing-basin',True
    for style in ('cave','hollow','thicket'):
        prefix=style+'_'
        if not name.startswith(prefix):continue
        rest=name[len(prefix):];pal='stone' if style=='cave' else 'foliage' if style=='hollow' else 'ground'
        if rest in ('floor0','floor1','floor_switch','floor_lift','floor_chest'):
            im=myst_floor(style,1 if rest=='floor1' else 0)
        elif rest.startswith('edge_'):im=myst_floor(style,0,int(rest[5:],16))
        elif rest in ('wall','face','crown'):
            if style=='thicket':im=canopy(1,'s' if rest=='face' else 'n' if rest=='crown' else None)
            elif style=='cave':im=stone_wall(face=rest!='wall')
            else:
                im,d=canvas(8)
                for x in (2,7,12):d.line([(x,0),(x+1,7),(x,15)],fill=9);d.line([(x+1,1),(x+2,6)],fill=10)
                if rest!='wall':d.rectangle((0,13,15,15),fill=1)
            pal='foliage' if style!='cave' else 'stone'
        elif rest=='prop':
            im,pal=prop('rock' if style=='cave' else 'stump')
        elif rest=='glow':
            im=canvas()[0];im=spark(im,8,7,1,8 if style=='cave' else 12);pal='stone' if style=='cave' else 'foliage'
        elif rest=='exit':im=exit_steps(style)
        elif rest=='spring':im=spring(phase);pal='water'
        else:raise KeyError('Unmapped mystery '+name)
        return im,pal,style+'-interior-'+rest,rest in ('wall','face','glow','spring')
    if name in ('bush','rock_small','boulder','rock','rock2','rock3','mossy_stone','sick_rock','stump','sick_stump','log','fence','thorn','pillar','ruin_wall','statue','bones','sick_bones','leaf_litter','fern_patch','blight_crystal','dead_tree','forest_blight_dead_tree','lantern_post','relic','shrine_plate','myst_pot'):
        im,pal=prop(name,phase);return im,pal,'foreground-'+name,name in ('statue','blight_crystal','dead_tree','forest_blight_dead_tree','lantern_post','relic','shrine_plate')
    raise KeyError('No native painter for '+name)


@lru_cache(None)
def build():
    result=[]
    for c in CONTRACTS['tiles']:
        frames=[];pal=None;family=None;glitter=False
        for f in range(c['frames']):
            im,pal,family,reflective=paint(c['name'],f)
            assert im.size==(16,16),(c['name'],im.size)
            assert max(im.getdata())<=15,c['name']
            frames.append(rows(im));glitter|=bool(reflective)
        m={k:c[k] for k in ('name','type','coll','prop','anim_speed')}
        m['pal']=pal;m['glitter']=int(glitter)
        if len(frames)==1:m['art']=frames[0]
        else:m['frames']=frames
        result.append(m)
        COVERAGE[c['name']]={'family':family,'palette':pal,'frames':len(frames),'owner':'reboot_terrain','native_size':[16,16]}
    assert len(result)==913 and len(COVERAGE)==913
    return result


def audit():
    """Pack only this fresh terrain using hardware flips, without old imports."""
    mts=build();room=CONTRACTS['rooms'][0]
    hub={n for layer in ('ground','overlay') for row in room[layer] for n in row if n}
    extra={'torch','torch_lit','boulder','chest','chest_open','sparkle','black','moss0','moss1','moss2'}
    tests={'forest':lambda n:not n.startswith(('sw_','swh_','cave_','hollow_','thicket_','myst_')),'sewer':lambda n:n.startswith('swh_') or n in hub,'myst':lambda n:n.startswith(('cave_','hollow_','thicket_','myst_')) or n in extra}
    report={}
    for area,pred in tests.items():
        keys={tuple([0]*64)};animated=0;held=0;pals=set()
        for m in mts:
            if not pred(m['name']):continue
            held+=1;pals.add(m['pal']);fs=m.get('frames') or [m['art']]
            if len(fs)>1:animated+=4;continue
            a=fs[0]
            for y in (0,8):
                for x in (0,8):
                    grid=[tuple(int(a[yy][xx],16) for xx in range(x,x+8)) for yy in range(y,y+8)]
                    variants=[]
                    for hf in (False,True):
                        for vf in (False,True):
                            rs=grid[::-1] if vf else grid;variants.append(tuple(v for row in rs for v in (row[::-1] if hf else row)))
                    keys.add(min(variants))
        count=len(keys)+animated
        report[area]={'subtiles':count,'palettes':len(pals),'palette_names':sorted(pals),'metatiles':held,'animated_base_subtiles':animated}
    return report


def preview(path='/workspace/setup/art-reboot-terrain-source.png'):
    from PIL import ImageFont
    mts=build();names=['moss0','path','pedge_3','shore_6','water_9','canopy_s','moss_blight','rot_38','forest_rot3','blight_floor','blight_pool','blight_wall_lit','bush','rock_small','boulder','myst_pot','crack','web','pit','myst_switch','myst_switch_down','torch_lit','statue','shrine_plate']
    out=Image.new('RGB',(8*132,36+3*113),'#101820');d=ImageDraw.Draw(out);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    for i,n in enumerate(names):
        m=next(m for m in mts if m['name']==n);a=m.get('frames',[m.get('art')])[0]
        p=Image.new('P',(16,16));p.putdata([int(v,16) for row in a for v in row]);a=R.rgba(p,R.PALETTES[m['pal']]);x=(i%8)*132+7;y=36+(i//8)*113
        out.paste(a.resize((80,80),Image.Resampling.NEAREST),(x,y),a.resize((80,80),Image.Resampling.NEAREST));out.paste(a,(x+94,y+64),a)
        d.text((x,y+84),n,font=font,fill='#e8dfbf')
    d.text((8,9),'New native terrain / source art, not emulator screenshots',font=font,fill='#f0d898');out.save(path)
    # Full room preview uses the exact retainedroom IDs, including canonical reuse.
    room=CONTRACTS['rooms'][0];lookup={m['name']:m for m in mts}
    scene=Image.new('RGBA',(480,320),'#101820')
    for layer in ('ground','overlay'):
        for y,row in enumerate(room[layer]):
            for x,n in enumerate(row):
                if n is None:continue
                m=lookup[n];fs=m.get('frames') or [m['art']];im=Image.new('P',(16,16));im.putdata([int(v,16) for r in fs[0] for v in r]);R.paste(scene,im,(x*16,y*16),R.PALETTES[m['pal']])
    scene.convert('RGB').save('/workspace/setup/art-reboot-drain-native.png');scene.resize((960,640),Image.Resampling.NEAREST).convert('RGB').save('/workspace/setup/art-reboot-drain-2x.png')
    return path
