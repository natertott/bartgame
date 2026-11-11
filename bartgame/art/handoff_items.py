"""Additive handoff tools and terrain, authored at native GBA pixel sizes.

No existing sprite, tile, identifier or palette is changed. Icons fit within
one16px tile, with a clear material outline and quiet transparent margins.
Terrain silhouettes describe their verbs, rather than relying on colour.
Source atlases are drawings, never claimed as emulator captures.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import reboot_core as R

NAMES=('NONE', 'SMITH_SWORD', 'GREEN_SWORD', 'RED_SWORD', 'BLUE_SWORD', 'UNUSED_SWORD', 'FOURSWORD', 'BOMBS', 'REMOTE_BOMBS', 'BOW', 'LIGHT_ARROW', 'BOOMERANG', 'MAGIC_BOOMERANG', 'SHIELD', 'MIRROR_SHIELD', 'LANTERN_OFF', 'LANTERN_ON', 'GUST_JAR', 'PACCI_CANE', 'MOLE_MITTS', 'ROCS_CAPE', 'PEGASUS_BOOTS', 'FIRE_ROD', 'OCARINA', 'ORB_GREEN', 'ORB_BLUE', 'ORB_RED', 'TRY_PICKUP_OBJECT', 'BOTTLE1', 'BOTTLE2', 'BOTTLE3', 'BOTTLE4', 'BOTTLE_EMPTY', 'BOTTLE_BUTTER', 'BOTTLE_MILK', 'BOTTLE_HALF_MILK', 'BOTTLE_RED_POTION', 'BOTTLE_BLUE_POTION', 'BOTTLE_WATER', 'BOTTLE_MINERAL_WATER', 'BOTTLE_FAIRY', 'BOTTLE_PICOLYTE_RED', 'BOTTLE_PICOLYTE_ORANGE', 'BOTTLE_PICOLYTE_YELLOW', 'BOTTLE_PICOLYTE_GREEN', 'BOTTLE_PICOLYTE_BLUE', 'BOTTLE_PICOLYTE_WHITE', 'CHARM_NAYRU', 'CHARM_FARORE', 'CHARM_DIN', '32', '33', 'QST_SWORD', 'QST_BROKEN_SWORD', 'QST_DOGFOOD', 'QST_LONLON_KEY', 'QST_MUSHROOM', 'QST_BOOK1', 'QST_BOOK2', 'QST_BOOK3', 'QST_GRAVEYARD_KEY', 'QST_TINGLE_TROPHY', 'QST_CARLOV_MEDAL', 'SHELLS', 'EARTH_ELEMENT', 'FIRE_ELEMENT', 'WATER_ELEMENT', 'WIND_ELEMENT', 'GRIP_RING', 'POWER_BRACELETS', 'FLIPPERS', 'MAP', 'SKILL_SPIN_ATTACK', 'SKILL_ROLL_ATTACK', 'SKILL_DASH_ATTACK', 'SKILL_ROCK_BREAKER', 'SKILL_SWORD_BEAM', 'SKILL_GREAT_SPIN', 'SKILL_DOWN_THRUST', 'SKILL_PERIL_BEAM', 'DUNGEON_MAP', 'COMPASS', 'BIG_KEY', 'SMALL_KEY', 'RUPEE1', 'RUPEE5', 'RUPEE20', 'RUPEE50', 'RUPEE100', 'RUPEE200', '5A', 'JABBERNUT', 'KINSTONE', 'BOMBS5', 'ARROWS5', 'HEART', 'FAIRY', 'SHELLS30', 'HEART_CONTAINER', 'HEART_PIECE', 'WALLET', 'BOMBBAG', 'LARGE_QUIVER', 'KINSTONE_BAG', 'BRIOCHE', 'CROISSANT', 'PIE', 'CAKE', 'BOMBS10', 'BOMBS30', 'ARROWS10', 'ARROWS30', 'ARROW_BUTTERFLY', 'DIG_BUTTERFLY', 'SWIM_BUTTERFLY', 'SKILL_FAST_SPIN', 'SKILL_FAST_SPLIT', 'SKILL_LONG_SPIN')

DIGITS='0123456789abcdef'
def rows(im):return [''.join(DIGITS[im.getpixel((x,y))] for x in range(im.width)) for y in range(im.height)]
def canvas(w=16,h=16,fill=0):
    im=Image.new('P',(w,h),fill);return im,ImageDraw.Draw(im)

def icon(name):
    im,d=canvas()
    if name in ('NONE','32','33','5A'):return im
    if 'SWORD' in name and 'SKILL' not in name and 'QST' not in name:
        d.polygon([(11,1),(14,1),(14,4),(7,11),(5,9)],fill=1)
        d.polygon([(12,2),(13,2),(12,4),(6,10),(6,8)],fill=12)
        d.line((11,3,6,8),fill=11)
        d.line((3,8,8,13),fill=1,width=3);d.line((3,8,8,13),fill=10)
        d.line((5,11,2,14),fill=1,width=3);d.line((5,11,2,14),fill=5)
        if name!='SMITH_SWORD':d.point((6,10),fill=13 if name=='GREEN_SWORD' else 15)
    elif name in ('LANTERN_OFF','LANTERN_ON'):
        d.arc((4,0,11,6),180,360,fill=10,width=2)
        d.rectangle((3,5,12,13),fill=1);d.rectangle((5,6,10,12),fill=13)
        d.line((3,4,12,4),fill=10);d.line((3,14,12,14),fill=10)
        d.line((4,5,4,12),fill=9);d.line((11,5,11,12),fill=9)
        d.line((7,8,7,11),fill=12);d.point((8,9),fill=12)
    elif name=='FAIRY':
        d.ellipse((1,2,6,7),fill=14);d.ellipse((9,2,14,7),fill=14)
        d.ellipse((2,7,6,12),fill=13);d.ellipse((9,7,13,12),fill=13)
        d.ellipse((5,4,10,11),fill=10);d.ellipse((6,5,9,9),fill=12)
        d.point((2,3),fill=12);d.point((12,3),fill=12)
    elif 'BOMB' in name and 'BAG' not in name:
        d.ellipse((3,4,13,14),fill=1);d.ellipse((4,5,12,13),fill=3)
        d.ellipse((5,5,10,10),fill=4);d.line((7,4,9,2,12,2),fill=9)
        d.line((12,1,12,3),fill=12);d.line((11,2,13,2),fill=10)
        if 'REMOTE' in name:d.rectangle((7,9,10,11),fill=13)
    elif 'SHIELD' in name:
        d.polygon([(2,2),(13,2),(14,8),(11,12),(8,15),(4,12),(1,8)],fill=1)
        d.polygon([(3,3),(12,3),(12,8),(10,11),(8,13),(5,11),(3,8)],fill=10)
        d.polygon([(4,4),(11,4),(11,8),(8,11),(5,9)],fill=13 if name=='MIRROR_SHIELD' else 4)
        d.line((5,4,5,8),fill=12);d.rectangle((7,6,9,8),fill=11)
    elif 'BOOMERANG' in name:
        d.polygon([(2,3),(4,1),(9,5),(14,11),(12,14),(7,8)],fill=1)
        d.polygon([(3,3),(4,3),(9,7),(13,12),(12,12),(7,7)],fill=9)
        d.line((4,4,8,7,12,11),fill=11)
        if name=='MAGIC_BOOMERANG':d.rectangle((6,5,8,7),fill=13)
    elif name=='GUST_JAR':
        d.polygon([(3,2),(10,2),(10,5),(13,7),(13,12),(10,14),(4,14),(2,11),(2,8),(5,5)],fill=1)
        d.polygon([(4,3),(9,3),(8,6),(11,8),(11,11),(9,12),(5,12),(4,10),(4,8),(6,6)],fill=13)
        d.line((5,8,5,10,8,11),fill=14);d.rectangle((3,2,10,3),fill=10)
    elif name=='PACCI_CANE' or name=='FIRE_ROD':
        d.line((4,14,10,5),fill=1,width=4);d.line((4,13,10,5),fill=6,width=2)
        if name=='PACCI_CANE':
            d.ellipse((7,1,14,7),fill=1);d.arc((8,2,13,6),180,480,fill=11,width=2);d.point((11,4),fill=15)
        else:
            d.polygon([(8,6),(8,3),(11,0),(11,3),(14,4),(13,7),(10,8)],fill=1)
            d.polygon([(9,5),(11,2),(11,4),(13,5),(11,7)],fill=10);d.line((10,5,11,6),fill=12)
    elif name in ('ROCS_CAPE','PEGASUS_BOOTS','MOLE_MITTS','POWER_BRACELETS','GRIP_RING','FLIPPERS'):
        if name=='ROCS_CAPE':
            d.polygon([(5,1),(11,1),(13,5),(11,6),(14,13),(10,14),(7,12),(3,14),(1,12),(4,6),(3,5)],fill=1)
            d.polygon([(5,3),(10,2),(11,5),(9,6),(12,12),(8,10),(4,12),(5,6)],fill=13);d.line((6,3,8,2,9,3),fill=14);d.point((8,6),fill=11)
        elif name=='GRIP_RING':
            d.ellipse((2,3,13,14),fill=1);d.ellipse((4,4,11,12),fill=10);d.ellipse((6,6,9,10),fill=0)
            d.polygon([(4,1),(11,1),(12,5),(8,7),(3,5)],fill=1);d.polygon([(5,2),(10,2),(10,4),(8,5),(5,4)],fill=13)
        else:
            for dx,dy in ((0,1),(6,-1)):
                d.polygon([(3+dx,5+dy),(7+dx,5+dy),(7+dx,10+dy),(9+dx,11+dy),(9+dx,13+dy),(2+dx,13+dy)],fill=1)
                d.rectangle((3+dx,6+dy,6+dx,11+dy),fill=13 if name=='FLIPPERS' else 6)
                d.line((3+dx,6+dy,5+dx,6+dy),fill=11)
                d.line((3+dx,12+dy,8+dx,12+dy),fill=10)
                if name=='MOLE_MITTS':d.line((3+dx,3+dy,3+dx,5+dy),fill=12);d.line((5+dx,3+dy,5+dx,5+dy),fill=12)
    elif name in ('BOW','LIGHT_ARROW') or 'ARROW' in name:
        if name=='BOW':
            d.arc((0,1,13,14),260,100,fill=1,width=4);d.arc((1,2,12,13),260,100,fill=9,width=2);d.line((7,2,7,13),fill=11)
        else:
            d.line((3,13,12,3),fill=1,width=3);d.line((3,13,12,3),fill=7)
            d.polygon([(8,3),(14,1),(12,7)],fill=1);d.polygon([(10,3),(13,2),(12,5)],fill=12)
            d.line((2,10,5,12),fill=13,width=2)
    elif name=='OCARINA':
        d.ellipse((2,4,13,12),fill=1);d.ellipse((3,5,12,11),fill=13);d.polygon([(9,9),(14,9),(14,12),(10,12)],fill=1)
        d.line((4,5,9,5),fill=14)
        for xy in ((5,7),(8,7),(7,9)):d.point(xy,fill=1)
    elif 'BOTTLE' in name or name.startswith('CHARM_'):
        d.polygon([(5,1),(10,1),(10,5),(12,7),(12,13),(10,15),(4,15),(2,13),(2,7),(5,5)],fill=1)
        d.polygon([(5,4),(9,4),(9,6),(11,8),(11,12),(9,13),(5,13),(4,12),(4,8),(6,6)],fill=14)
        d.rectangle((5,1,10,3),fill=6);d.line((6,1,9,1),fill=10)
        if not name.endswith('EMPTY') and name not in ('BOTTLE1','BOTTLE2','BOTTLE3','BOTTLE4'):
            c=15 if 'RED' in name else 13 if 'BLUE' in name or 'WATER' in name else 11
            d.rectangle((5,9,10,12),fill=c)
        d.line((4,8,4,11),fill=12)
    elif 'HEART' in name or name=='FAIRY':
        d.polygon([(1,5),(3,2),(6,2),(8,4),(10,2),(13,2),(15,5),(13,9),(8,14),(3,10)],fill=1)
        d.polygon([(2,5),(4,3),(6,3),(8,5),(10,3),(12,3),(14,5),(12,8),(8,12),(4,9)],fill=15)
        d.line((4,4,6,4),fill=12)
        if name=='HEART_PIECE':d.polygon([(9,4),(14,5),(12,8),(8,12),(8,6)],fill=3)
    elif name.startswith('SKILL_'):
        d.rectangle((2,1,13,14),fill=1);d.rectangle((3,2,12,13),fill=11);d.rectangle((4,3,11,12),fill=6)
        d.line((5,10,10,5),fill=12,width=2);d.line((5,5,10,10),fill=9)
        k=NAMES.index(name)-72
        for bit in range(4):
            if k&(1<<bit):d.point((4+bit*2,12),fill=12)
    elif name.startswith('QST_BOOK') or name in ('MAP','DUNGEON_MAP','COMPASS','JABBERNUT'):
        if name=='COMPASS':
            d.ellipse((2,2,13,13),fill=1);d.ellipse((3,3,12,12),fill=10);d.polygon([(8,3),(11,10),(8,8),(5,11)],fill=15);d.point((8,8),fill=12)
        else:
            d.polygon([(1,3),(6,1),(10,3),(14,1),(14,12),(10,14),(6,12),(1,14)],fill=1)
            d.polygon([(2,4),(6,3),(9,4),(13,3),(13,11),(10,12),(6,10),(2,12)],fill=11);d.line((7,4,7,10),fill=6)
            d.line((3,6,5,5),fill=6);d.line((9,7,11,6),fill=13)
    elif name in ('SMALL_KEY','BIG_KEY','QST_LONLON_KEY','QST_GRAVEYARD_KEY'):
        d.ellipse((1,1,9,9),fill=1);d.ellipse((2,2,8,8),fill=10);d.ellipse((4,4,6,6),fill=0)
        d.line((7,7,13,13),fill=1,width=4);d.line((7,7,13,13),fill=10,width=2);d.line((11,9,13,7),fill=11,width=2)
    elif name in ('RUPEE1','RUPEE5','RUPEE20','RUPEE50','RUPEE100','RUPEE200','KINSTONE'):
        d.polygon([(8,1),(13,5),(13,10),(8,15),(3,11),(3,5)],fill=1)
        d.polygon([(8,2),(11,5),(11,10),(8,13),(5,10),(5,5)],fill=10)
        d.line((8,3,8,11),fill=12);d.line((5,6,7,4),fill=11)
    elif 'BUTTERFLY' in name:
        for b in ((1,2,7,8),(8,2,14,8),(2,8,7,13),(8,8,13,13)):d.ellipse(b,fill=1);d.ellipse((b[0]+1,b[1]+1,b[2]-1,b[3]-1),fill=13)
        d.line((7,5,7,12),fill=11,width=2)
    elif 'ELEMENT' in name or name.startswith('ORB_'):
        d.ellipse((2,2,13,13),fill=1);d.ellipse((3,3,12,12),fill=13);d.arc((4,4,11,11),150,310,fill=14,width=2);d.point((6,4),fill=12)
        if 'FIRE' in name:d.polygon([(7,5),(10,9),(8,12),(5,9)],fill=15)
        elif 'WATER' in name:d.line((5,8,7,7,10,9),fill=12)
        elif 'WIND' in name:d.arc((5,5,11,10),40,290,fill=12)
    elif name in ('SHELLS','SHELLS30'):
        d.polygon([(1,9),(3,4),(8,2),(12,4),(15,9),(11,12),(8,14),(4,12)],fill=1)
        d.polygon([(2,9),(4,5),(8,3),(11,5),(14,9),(10,11),(8,12),(5,11)],fill=11)
        for x in (4,7,10):d.line((8,11,x,5),fill=8)
    elif name in ('BRIOCHE','CROISSANT','PIE','CAKE'):
        d.polygon([(2,6),(5,3),(10,3),(14,7),(14,12),(2,12)],fill=1);d.polygon([(3,7),(6,4),(10,4),(13,8),(13,10),(3,10)],fill=9)
        d.line((4,7,11,7),fill=11);d.line((4,11,12,11),fill=5)
    elif name in ('WALLET','BOMBBAG','LARGE_QUIVER','KINSTONE_BAG'):
        d.polygon([(5,1),(11,1),(10,5),(13,8),(13,13),(10,15),(4,14),(2,11),(3,7),(6,5)],fill=1)
        d.polygon([(5,2),(10,2),(8,5),(11,8),(11,12),(9,13),(5,12),(4,10),(5,7),(7,5)],fill=6)
        d.line((5,5,10,5),fill=10,width=2);d.ellipse((6,8,10,11),fill=9)
    else:
        # Original quest tokens have a distinct native seal/fragment shape;
        # they are added vocabulary, not replacement art for current objects.
        d.polygon([(3,2),(10,2),(13,5),(12,12),(8,14),(2,11)],fill=1)
        d.polygon([(4,3),(9,3),(11,6),(10,11),(8,12),(4,10)],fill=9)
        d.line((5,4,9,4),fill=11);d.line((6,7,9,10),fill=6)
        i=NAMES.index(name)
        if i&1:d.rectangle((5,7,7,9),fill=13)
        if i&2:d.line((8,6,10,8),fill=12)
    return im


def tool_fx(kind,phase):
    im,d=canvas();cx=7+phase
    if kind in (0,1):
        d.polygon([(2,2),(5,1),(14,10),(12,14),(6,8)],fill=1)
        d.line((3,3,7,5,12,11),fill=10,width=3);d.line((4,3,8,6,12,10),fill=12)
    elif kind==2:
        d.ellipse((3,3,12,12),fill=1);d.arc((4,4,11,11),20+phase*90,300+phase*90,fill=14,width=2);d.point((8,7),fill=15)
    elif kind==3:
        d.polygon([(2,10),(5,6),(6,1),(9,5),(12,4),(14,10),(11,14),(6,14)],fill=5)
        d.polygon([(5,10),(7,5),(10,9),(11,12),(7,13)],fill=10);d.line((7,10,8,12),fill=12)
    elif kind in (4,5):
        d.line((2,13,13,2),fill=9,width=3);d.line((3,12,12,3),fill=12)
        d.polygon([(8,3),(14,1),(12,7)],fill=11);d.point((7,7),fill=12)
    elif kind==6:
        for y,x,w in ((3,3,7),(7,1,11),(11,4,8)):
            d.arc((x,y,x+w,y+3),180,350,fill=12);d.point((x+w,y+1),fill=11)
    elif kind==7:
        d.arc((0,0,15,15),20+phase*40,170+phase*40,fill=11,width=2);d.arc((2,2,13,13),30+phase*40,160+phase*40,fill=12)
    elif kind==8:
        d.line((7,2,7,12),fill=10);d.line((3,7,12,7),fill=10);d.line((7,4,7,10),fill=12);d.line((5,7,10,7),fill=12)
    elif kind==12:
        d.ellipse((1,6,14,12),outline=13,width=1);d.arc((3,5,12,11),170+phase*20,300+phase*20,fill=14)
        d.line((5,8,8,8),fill=12);d.point((11,3+phase),fill=12);d.point((4,1+phase),fill=14)
    elif kind>=10:
        face=(kind-10)*2+phase
        ends=(((8,14),(8,1)),((1,8),(14,8)),((8,1),(8,14)),((14,8),(1,8)))
        root,tip=ends[face];d.line((*root,*tip),fill=1,width=4);d.line((*root,*tip),fill=12,width=2)
        x,y=root
        if face in (0,2):d.line((x-3,y,x+3,y),fill=10)
        else:d.line((x,y-3,x,y+3),fill=10)
    else:
        d.polygon([(2,12),(3,4),(8,1),(13,5),(14,13),(8,15)],fill=13)
        d.line((4,5,8,3,11,6),fill=14);d.line((8,3,8,10),fill=12)
    return im


def minish(face,pose):
    im,d=canvas(8,16)
    oy=1 if pose==2 else 0
    if pose==3:
        d.ellipse((1,7,6,12),fill=1);d.ellipse((2,8,5,11),fill=4);d.point((4,8),fill=7);return im
    if pose==6:
        d.ellipse((1,12,6,14),fill=1);d.line((2,12,5,12),fill=4);return im
    d.polygon([(3,9+oy),(5,9+oy),(6,13),(2,13)],fill=1);d.line((3,10,4,12),fill=10)
    d.line((3,13,2,14),fill=11);d.line((5,13,6,14),fill=11)
    d.ellipse((0,1+oy,7,9+oy),fill=2);d.ellipse((1,2+oy,6,8+oy),fill=4)
    d.ellipse((2,3+oy,5,7+oy),fill=7 if face!='n' else 5)
    if face!='n':d.point((3 if face!='e' else 4,5+oy),fill=1);d.point((5 if face!='w' else 2,5+oy),fill=1)
    if pose==4:d.line((2,4,5,7),fill=1)
    return im


def gold_half(kind):
    im,d=canvas()
    points={'flow':[(3,1),(11,1),(12,4),(9,6),(13,9),(11,14),(3,14),(3,10),(6,8),(3,6)],
            'left':[(3,1),(9,1),(9,5),(12,6),(12,9),(9,10),(9,14),(3,14)],
            'middle':[(3,1),(12,1),(12,5),(9,6),(9,9),(12,10),(12,14),(3,14),(3,10),(6,9),(6,6),(3,5)],
            'right':[(6,1),(12,1),(12,14),(6,14),(6,10),(3,9),(3,6),(6,5)]}[kind]
    d.polygon(points,fill=1)
    d.polygon([(x+1 if x<7 else x-1,y+1 if y<7 else y-1) for x,y in points],fill=9)
    d.line((5,3,9,3),fill=12);d.line((5,4,5,6),fill=11)
    if kind=='flow':d.line((6,10,9,10),fill=12)
    return im


def build_sheets():
    icons={n.lower():rows(icon(n)) for n in NAMES}
    icons.update({'gold_'+kind:rows(gold_half(kind)) for kind in ('flow','left','middle','right')})
    return [dict(name='handoff_items',w=16,h=16,pal='gear',frames=icons),
            dict(name='handoff_tool_fx',w=16,h=16,pal='fx',frames={'tool%d_%d'%(k,p):rows(tool_fx(k,p)) for k in range(13) for p in range(2)}),
            dict(name='handoff_minish',w=8,h=16,pal='hero',frames={'%s_%d'%(f,p):rows(minish(f,p)) for f in ('n','e','s','w') for p in range(7)})]

# Two compact new RGB555 banks loaded in annexes/Cream only. Current forest
# and sewer native palette payloads stay byte-identical.
BGPALETTES={
 'lh_earth':['#000000','#182028','#303830','#485040','#606850','#808060','#a0a078','#c0b898','#e0d8b8','#404830','#587050','#88a870','#683050','#984878','#d878b8','#f8e8d0'],
 'lh_element':['#000000','#182028','#203848','#305868','#508088','#80a8a8','#b0d0c8','#e0e8d8','#503028','#805038','#b87840','#e8a850','#582868','#9838b8','#d878e8','#f8e8f8']}


def surface(kind,phase=0):
    im,d=canvas(fill=4)
    # Quiet horizontal clusters keep all walkable treatments calm and tiled.
    for x,y,c in ((0,3,3),(6,11,5),(11,5,3),(3,8,5),(13,14,3)):d.line((x,y,min(15,x+2),y),fill=c)
    if kind=='ice':
        d.rectangle((0,0,15,15),fill=5);d.polygon([(0,7),(6,1),(11,1),(4,8)],fill=6);d.line((9,9,15,3),fill=7);d.line((1,15,5,11,9,11),fill=4)
    elif kind=='swamp':
        d.rectangle((0,0,15,15),fill=3);d.line((0,5,7,5),fill=2);d.line((9,11,15,11),fill=2);d.line((1,4,6,4),fill=5);d.ellipse((10,3,13,5),fill=9)
    elif kind=='dust':
        d.rectangle((0,0,15,15),fill=6);d.line((0,5,5,5),fill=5);d.line((7,11,14,11),fill=7);d.point((8,3),fill=7)
    elif kind=='lava':
        d.rectangle((0,0,15,15),fill=8);d.polygon([(0,4),(4,2),(9,5),(15,2),(15,6),(9,8),(4,5),(0,7)],fill=10)
        d.line((0,5+phase,5,3+phase,9,6+phase,15,3+phase),fill=11);d.line((2,13,7,11,13,14),fill=13);d.point((9,12),fill=15)
    elif kind in ('dig','dig_wall'):
        if kind=='dig_wall':d.rectangle((0,0,15,15),fill=2);d.line((0,0,15,0),fill=6);d.line((0,2,15,2),fill=5)
        for x,y in ((1,5),(8,7),(3,12),(11,14)):d.line((x,y,x+3,y),fill=2);d.point((x,y-1),fill=6)
        d.line((6,4,9,4),fill=7)
    elif kind=='spring':
        d.ellipse((1,2,14,14),fill=2);d.ellipse((3,4,12,12),fill=1);d.line((5,5,10,5),fill=8);d.ellipse((6,7,9,10),fill=13);d.point((7,7),fill=14)
    elif kind=='minish_portal':
        d.ellipse((1,2,14,15),fill=1);d.ellipse((3,4,12,13),fill=12);d.ellipse((5,6,10,11),fill=13);d.line((4,4,11,4),fill=11);d.point((7,7),fill=15)
    elif kind=='minish_gap':
        d.rectangle((0,0,15,15),fill=3);d.line((0,0,15,0),fill=6);d.line((0,3,15,3),fill=2);d.rectangle((5,8,10,15),fill=1);d.line((5,7,10,7),fill=6);d.point((8,11),fill=13)
    elif kind=='clone_plate':
        d.rectangle((1,1,14,14),fill=2);d.rectangle((2,2,13,13),fill=6);d.rectangle((3,3,12,12),fill=3)
        for x,y in ((4,4),(9,4),(4,9),(9,9)):d.rectangle((x,y,x+2,y+2),fill=13);d.point((x,y),fill=15)
    elif kind=='crumble':
        for x,y in ((0,0),(8,0),(0,8),(8,8)):d.rectangle((x,y,x+6,y+6),fill=5);d.line((x,y,x+6,y),fill=7)
        d.line((6,0,5,5,9,8,7,13,8,15),fill=1)
    elif kind.startswith('conveyor_'):
        d.rectangle((0,1,15,14),fill=2);d.line((0,2,15,2),fill=6);d.line((0,13,15,13),fill=1)
        for y in (3,12):
            for x in (1,6,11):d.rectangle((x,y,x+2,y+1),fill=7)
        d.polygon([(4,5),(8,5),(8,3),(12,8),(8,12),(8,10),(4,10)],fill=11)
        turns={'e':0,'s':3,'w':2,'n':1}[kind[-1]];im=im.rotate(90*turns)
    elif kind=='shallow':
        d.line((0,5,5,5),fill=6);d.line((9,12,15,12),fill=5);d.line((3,9,8,9),fill=7)
    elif kind.startswith('slope_'):
        d.rectangle((0,0,15,15),fill=3)
        for y in (1,6,11):d.line((0,y,15,y),fill=6);d.line((0,y+2,15,y+2),fill=2)
        if kind.endswith('x'):im=im.rotate(90)
    elif kind=='dash_wall':
        d.rectangle((0,0,15,15),fill=1);d.rectangle((1,1,14,14),fill=5)
        for x in (4,10):d.line((x,1,x,14),fill=2)
        d.line((2,2,13,2),fill=7);d.line((6,0,8,4,6,8,9,12,8,15),fill=1)
    elif kind=='ice_block':
        d.polygon([(2,2),(12,1),(15,4),(14,14),(4,15),(0,12),(1,4)],fill=1);d.polygon([(3,3),(11,2),(13,5),(12,12),(4,13),(2,11)],fill=5)
        d.line((3,4,10,3),fill=7);d.line((5,10,10,5),fill=6)
    elif kind=='water_sprout':
        d.line((8,14,8,7),fill=10,width=2);d.polygon([(8,12),(3,8),(3,6),(7,7)],fill=11);d.polygon([(8,10),(11,5),(14,5),(12,9)],fill=10)
        d.ellipse((5,2,11,8),fill=1);d.ellipse((6,3,10,7),fill=13);d.point((8,4),fill=15)
    return im

_SURFACES=('ice','swamp','dust','lava','dig','dig_wall','spring','minish_portal','minish_gap','clone_plate','crumble','conveyor_n','conveyor_e','conveyor_s','conveyor_w','shallow','slope_x','slope_y','dash_wall','ice_block','water_sprout')
SURFACE_METATILES=[]
for k in _SURFACES:
    pal='lh_element' if k in ('ice','lava','minish_portal','ice_block','shallow') else 'lh_earth'
    solid=k in ('dig_wall','minish_gap','dash_wall','ice_block')
    spec=dict(name='lh_'+k,pal=pal,type='SOLID' if solid else 'FLOOR',coll=15 if solid else 0)
    if k=='lava':spec.update(frames=[rows(surface(k,p)) for p in range(2)],anim_speed=16)
    else:spec['art']=rows(surface(k))
    SURFACE_METATILES.append(spec)


def write_review(destination):
    dst=Path(destination);dst.mkdir(parents=True,exist_ok=True)
    sheets=build_sheets();font=ImageFont.load_default();w=600;out=Image.new('RGB',(w,1010),'#181820');d=ImageDraw.Draw(out);y=6
    d.text((8,y),'NEW HANDOFF SOURCE ART | native16px / nearest2x | not emulator output',fill='#f8e8c0',font=font);y+=22
    for sheet in sheets[:1]:
        for i,(name,raw) in enumerate(sheet['frames'].items()):
            col=i%10;row=i//10;im=Image.new('P',(16,16));im.putdata([int(c,16) for r in raw for c in r]);pal=R.PALETTES['gold'];im.putpalette([v for c in pal for v in R.rgb(c)]+[0]*720)
            x=8+col*59;yy=y+row*62;out.paste(im.convert('RGB').resize((32,32),Image.Resampling.NEAREST),(x,yy));d.text((x,yy+34),name[:9],fill='#d8d0b0',font=font)
    y+=13*62+12
    for i,spec in enumerate(SURFACE_METATILES):
        k=spec['name'][3:];im=surface(k);im.putpalette([v for c in BGPALETTES[spec['pal']] for v in R.rgb(c)]+[0]*720)
        x=8+(i%10)*59;yy=y+(i//10)*62;out.paste(im.convert('RGB').resize((32,32),Image.Resampling.NEAREST),(x,yy));d.text((x,yy+34),k[:9],fill='#d8d0b0',font=font)
    out.crop((0,0,w,y+3*62)).save(dst/'items-surfaces-source.png')
    (dst/'items-source-manifest.json').write_text(json.dumps({'items':list(NAMES),'virtual_gold_icons':['flow','left','middle','right'],'surface_metatiles':list(_SURFACES),'new_palettes':BGPALETTES,'native':True,'existing_art_changed':False},indent=2)+'\n')

if __name__=='__main__':
    import sys
    write_review(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/handoff-items/source')
