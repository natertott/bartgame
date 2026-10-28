"""Native GBA art reboot vocabulary: shared RGB555 material ramps.

Every drawing starts on its native pixel canvas. Pixel indices are literal
4bpp inks, never a reduced high-resolution image. Production assets can use
these palettes and compact foreground silhouettes after mockup critique.
"""
from PIL import Image, ImageDraw

# Each family is a hardware-sized sixteen-colour bank; 0 is transparent.
PALETTES={
 'ground':['#000000','#101820','#182820','#283828','#385038','#506048','#687048','#384030','#504830','#685838','#887048','#a08858','#384848','#586060','#809078','#c8c8a0'],
 'foliage':['#000000','#101820','#102828','#183830','#204838','#306048','#487850','#689858','#302820','#483828','#685038','#907048','#b09058','#183838','#305850','#789880'],
 'water':['#000000','#101820','#102830','#183840','#204850','#306060','#488080','#70a098','#b0c0a8','#283828','#385038','#506048','#685838','#887048','#b09058','#e0d8b0'],
 'stone':['#000000','#101820','#202830','#303840','#485050','#606860','#889080','#b0b098','#d0d0b0','#302820','#504030','#786040','#a08048','#c0a060','#e8d098','#f8f0c8'],
 'gold':['#000000','#101820','#302020','#483020','#684028','#885830','#b07838','#705020','#a87828','#d8a038','#f0c858','#f8e0a0','#f8f0c8','#184848','#387870','#b04050'],
 'hero':['#000000','#101820','#802830','#b83838','#e06040','#f89050','#f0d898','#f8f0c0','#183828','#305030','#507038','#483820','#886038','#88a0a0','#d0e0c0','#f8f8d8'],
 'blight':['#000000','#101018','#201828','#302038','#483048','#604058','#805068','#a06878','#403030','#604038','#886048','#b08858','#882858','#c04888','#e890b8','#f0d8c0'],
 'decay_mix':['#000000','#101820','#283828','#385038','#506048','#504830','#685838','#887048','#201828','#302038','#483048','#604058','#305850','#886048','#f0d8c0','#f8e0a0'],
 'rot_water':['#000000','#101018','#201828','#382030','#583048','#804060','#a85888','#d080a8','#f0c0d0','#201828','#302038','#483048','#604038','#886048','#b08858','#f0d8c0'],
 'drain':['#000000','#101820','#182828','#283838','#384848','#506058','#708078','#98a090','#c0c0a0','#284038','#386050','#588068','#684028','#986040','#c09050','#f0d8a0'],
 'ui':['#000000','#101820','#182028','#283038','#484838','#707050','#a09058','#d0b878','#f0d898','#f8f0c8','#803030','#c04840','#f87850','#284838','#507858','#80a080'],
}
# Alternate direction: identical geometry, warmer/tarnished woodland ramps.
WARM_OVERRIDES={
 'ground':['#000000','#181820','#282820','#383828','#505030','#686038','#807848','#484030','#605030','#786040','#987848','#b09860','#404840','#606858','#909070','#d8c898'],
 'foliage':['#000000','#181820','#282828','#303830','#404830','#586038','#708048','#98a058','#382828','#503828','#705038','#987048','#b89058','#303838','#485848','#909878'],
}


def bank(name,warm=False):
    return WARM_OVERRIDES.get(name,PALETTES[name]) if warm else PALETTES[name]


def rgb(hex_):return tuple(int(hex_[i:i+2],16) for i in (1,3,5))


def indexed(w,h,fill=0):
    im=Image.new('P',(w,h),fill)
    return im,ImageDraw.Draw(im)


def rgba(im,pal):
    out=Image.new('RGBA',im.size)
    a=im.load();b=out.load()
    for y in range(im.height):
        for x in range(im.width):
            v=a[x,y]
            if v:b[x,y]=(*rgb(pal[v]),255)
    return out


def paste(scene,im,xy,pal):
    im=rgba(im,pal);scene.alpha_composite(im,xy)


def hero(facing='s',step=0):
    im,d=indexed(16,24)
    # Four leaf limbs stay connected to a compact stem, with two root feet.
    d.polygon([(6,12),(10,12),(11,15),(10,19),(6,19),(5,15)],fill=1)
    d.rectangle((7,13,9,18),fill=8);d.line([(7,13),(7,17)],fill=10)
    if facing in ('e','w'):
        d.polygon([(6,14),(3,16),(4,18),(7,17)],fill=1)
        d.line([(4,16),(6,15)],fill=9)
        d.polygon([(9,15),(12,16),(13,18),(10,18)],fill=1);d.line([(10,16),(12,17)],fill=10)
    else:
        d.polygon([(5,13),(2,15),(1,18),(5,17),(7,15)],fill=1)
        d.line([(2,17),(4,15),(5,15)],fill=9)
        d.polygon([(10,13),(13,15),(14,18),(10,17),(9,15)],fill=1)
        d.line([(11,15),(13,17)],fill=10)
    d.line([(6,18),(5-step,20),(3-step,20)],fill=1,width=2)
    d.line([(9,18),(10+step,20),(12+step,20)],fill=1,width=2)
    d.line([(5-step,19),(4-step,20)],fill=12)
    d.line([(10+step,19),(11+step,20)],fill=12)
    # One ink perimeter, five large petal clusters, no detached fluff.
    petals=[(5,0,10,5),(1,3,6,9),(9,3,14,9),(2,8,7,13),(8,8,13,13)]
    for x0,y0,x1,y1 in petals:
        d.ellipse((x0,y0,x1,y1),fill=1)
        d.ellipse((x0+1,y0+1,x1-1,y1-1),fill=3)
        d.line([(x0+2,y0+1),(x1-2,y0+1)],fill=4)
        d.point((x0+2,y0+2),fill=5)
    if facing=='n':
        d.ellipse((4,4,11,11),fill=2);d.ellipse((5,4,10,9),fill=4)
        d.line([(5,4),(8,3),(10,5)],fill=5)
        d.rectangle((6,11,9,13),fill=8)
    else:
        d.ellipse((4,4,11,11),fill=1)
        d.ellipse((5,5,10,10),fill=6);d.line([(6,5),(9,5)],fill=7)
        if facing=='s':d.point((6,7),fill=1);d.point((9,7),fill=1)
        else:d.point((9 if facing=='e' else 6,7),fill=1)
    return im


def tree(blighted=False):
    if blighted:
        im,d=indexed(32,48)
        # The corrupted tree is a different anatomy: bare broken limbs,
        # swollen wet cambium, hanging seed ulcers and exposed root claws.
        limbs=[[(15,45),(15,29),(10,20),(8,7),(3,2)],[(16,35),(21,24),(26,17),(29,4)],[(14,28),(7,24),(2,15)],[(18,28),(21,13),(19,4)],[(16,40),(22,45),(29,47)],[(14,41),(8,46),(1,47)]]
        for pts in limbs:
            d.line(pts,fill=1,width=5);d.line(pts,fill=8,width=3);d.line([(x-1,y) for x,y in pts],fill=9,width=1)
        d.polygon([(13,30),(18,27),(21,35),(19,42),(17,45),(12,43),(11,37)],fill=1)
        d.polygon([(14,30),(17,30),(19,35),(17,41),(14,42),(13,37)],fill=9)
        d.line([(15,43),(16,37),(14,33),(16,29)],fill=13)
        d.point((16,37),fill=14)
        for x,y in [(7,10),(24,15),(19,5)]:
            d.ellipse((x-2,y-2,x+2,y+3),fill=1);d.ellipse((x-1,y-1,x+1,y+2),fill=12)
            d.point((x,y),fill=14)
        # A pale fungus tears through one side of the trunk, dripping wine.
        d.polygon([(18,24),(22,22),(26,24),(25,27),(20,28)],fill=1)
        d.line([(19,24),(22,23),(25,24)],fill=15,width=2)
        d.line([(21,27),(21,30)],fill=13)
        return im
    im,d=indexed(32,48)
    # A readable low trunk and roots, with canopy hovering above its footprint.
    d.polygon([(13,21),(19,21),(20,37),(24,43),(29,45),(28,47),(20,46),(16,42),(11,47),(3,47),(3,45),(10,42),(13,36)],fill=1)
    d.polygon([(14,23),(18,23),(18,37),(21,43),(18,41),(16,38),(13,43),(8,45),(12,39)],fill=9)
    d.line([(14,25),(14,37),(11,43)],fill=10);d.line([(17,30),(18,38),(22,44)],fill=8)
    d.line([(15,33),(16,38),(14,43)],fill=11)
    crown=[(1,7),(6,7),(3,4),(8,2),(10,0),(13,2),(19,0),(23,3),(28,3),(26,7),(31,10),(28,12),(31,18),(27,19),(28,23),(23,23),(22,28),(17,26),(12,29),(9,26),(5,27),(6,23),(1,22),(3,17),(0,15),(3,11)]
    d.polygon(crown,fill=1)
    d.polygon([(7,2),(23,2),(25,5),(28,6),(27,10),(29,12),(27,16),(29,19),(25,22),(23,25),(8,26),(5,23),(3,20),(4,16),(2,13),(4,10),(4,6)],fill=2)
    clusters=[(8,3,6,5),(15,2,7,5),(22,6,5,5),(4,9,6,6),(12,8,8,6),(21,12,6,6),(5,17,7,5),(13,17,7,7),(22,20,4,4)]
    for i,(x,y,w,h) in enumerate(clusters):
        d.polygon([(x,y+1),(x+2,y),(x+w-2,y),(x+w,y+2),(x+w-1,y+h-1),(x+2,y+h),(x,y+h-2)],fill=3)
        d.polygon([(x+1,y+1),(x+w-2,y+1),(x+w-1,y+2),(x+2,y+3),(x+1,y+h-2)],fill=4)
        d.line([(x+2,y+1),(x+w-3,y+1)],fill=5)
        if i in (0,1,3,4):
            d.line([(x+2,y+2),(x+3,y+2)],fill=6)
            d.point((x+2,y+1),fill=7)
    d.polygon([(5,22),(9,23),(11,26),(9,31),(7,28),(5,29),(3,26)],fill=2)
    d.line([(5,24),(7,25),(8,28)],fill=4)
    d.polygon([(20,22),(24,21),(28,23),(26,27),(23,30),(22,27)],fill=2)
    d.line([(22,23),(25,23),(24,26)],fill=4)
    if blighted:
        # Bare torn limbs and a few wet magenta fissures, not a violet recolour.
        for pts in [[(16,37),(13,27),(9,20),(8,12)],[(17,32),(22,26),(25,17)],[(15,29),(12,20),(16,12)]]:
            d.line(pts,fill=1,width=3);d.line(pts,fill=9,width=1)
        d.line([(16,44),(17,36),(15,32),(17,28)],fill=13)
        d.line([(22,25),(24,20),(24,17)],fill=13)
        d.point((16,36),fill=14);d.point((24,20),fill=14)
    return im


def chest(tier=0,opened=False):
    im,d=indexed(32,32)
    left,right=6,25
    d.ellipse((6,26,25,28),fill=1)
    d.rectangle((left,14,right,27),fill=1)
    d.rectangle((left+1,17,right-1,26),fill=4 if tier<2 else 13)
    d.line([(left+2,24),(right-2,24)],fill=3 if tier<2 else 2)
    if opened:
        d.rectangle((left,7,right,15),fill=1);d.rectangle((left+1,8,right-1,13),fill=5)
        d.line([(left+2,8),(right-2,8)],fill=9 if tier else 6)
        d.rectangle((left+1,15,right-1,19),fill=2)
    else:
        d.polygon([(left,15),(left+1,11),(left+4,10),(right-4,10),(right-1,11),(right,15)],fill=1)
        d.polygon([(left+1,15),(left+2,12),(left+4,10),(right-4,10),(right-2,12),(right-1,15)],fill=5)
        d.line([(left+4,11),(right-4,11)],fill=6)
        d.line([(left+1,16),(right-1,16)],fill=2)
    if not opened:
        d.line([(9,12),(12,12)],fill=6)
        d.line([(20,14),(23,14)],fill=4)
    d.line([(9,21),(12,21)],fill=5)
    d.line([(19,23),(23,23)],fill=3 if tier<2 else 2)
    metal=8 if tier else 7
    for x in (left+3,right-3):
        d.line([(x,12 if not opened else 20),(x,27)],fill=metal,width=2)
        d.point((x,13 if not opened else 20),fill=11)
    d.rectangle((14,15,17,20),fill=9 if tier else 6)
    d.rectangle((15,16,16,18),fill=1)
    if tier==2:
        d.polygon([(16,14),(19,17),(16,21),(13,17)],fill=11)
        d.polygon([(16,15),(17,17),(16,19),(15,17)],fill=13)
    return im


def portal(style='hollow',closed=False):
    im,d=indexed(32,48)
    # 20x31 dark aperture, tall enough for a 22-pixel flower traveller.
    d.polygon([(1,44),(1,20),(4,10),(8,5),(12,3),(20,3),(24,6),(28,12),(31,23),(30,44)],fill=1)
    d.polygon([(3,42),(3,20),(6,12),(10,7),(14,5),(19,5),(23,8),(26,14),(29,23),(28,42)],fill=4 if style=='cave' else 5)
    d.polygon([(7,42),(6,23),(8,16),(11,12),(14,10),(18,10),(22,14),(25,22),(25,42)],fill=1)
    if style=='cave':
        for pts in [[(3,24),(6,22)],[(5,16),(8,17)],[(8,10),(11,12)],[(14,5),(14,9)],[(21,7),(19,11)],[(25,13),(22,16)],[(28,23),(25,24)]]:d.line(pts,fill=7)
        d.line([(3,30),(6,28),(6,39)],fill=6)
        d.line([(26,28),(28,29),(27,41)],fill=3)
    else:
        # A living hollow is a trunk aperture with knots and flared roots,
        # rather than the stone arch recoloured brown.
        d.polygon([(4,14),(2,9),(5,3),(10,0),(23,1),(27,5),(26,12),(29,23),(28,36),(31,45),(25,45),(27,39),(25,25),(23,15),(19,10),(14,10),(10,13),(7,22),(6,38),(4,45),(0,45),(3,36)],fill=4)
        d.line([(7,5),(10,2),(16,3),(22,2),(25,6)],fill=6)
        d.line([(5,11),(7,15),(5,21)],fill=3)
        d.line([(25,10),(24,14),(27,21)],fill=2)
        for x,y in [(4,23),(5,30),(6,36),(26,24),(27,32),(25,38)]:
            d.line([(x,y),(x+1,y+4)],fill=3);d.point((x,y),fill=6)
        d.line([(3,42),(1,45),(7,44)],fill=6)
        d.line([(27,40),(30,45),(24,44)],fill=4)
    if style=='thicket':
        for x,y in [(3,19),(5,12),(10,5),(20,5),(26,14),(28,23),(26,33),(4,34)]:
            d.polygon([(x-2,y-3),(x+3,y-2),(x+4,y+1),(x+2,y+5),(x-2,y+4),(x-3,y+1)],fill=1)
            d.polygon([(x-1,y-2),(x+2,y-1),(x+3,y+1),(x+1,y+4),(x-1,y+2)],fill=13)
            d.line([(x,y-1),(x+1,y+2)],fill=14,width=1)
            if y<15:d.point((x,y),fill=11)
    # Two tiny warm rivets and a broad clean sill, no large blinking halo.
    d.line([(7,42),(25,42)],fill=9);d.line([(7,43),(25,43)],fill=11)
    d.rectangle((14,5,18,8),fill=9);d.line([(15,5),(17,5)],fill=11)
    if closed:
        for x in (10,15,20):d.line([(x,15),(x,41)],fill=6,width=2)
        d.line([(8,28),(24,28)],fill=7,width=2)
    return im


def pickup(kind='key'):
    im,d=indexed(16,16)
    if kind=='key':
        d.line([(6,7),(12,13)],fill=1,width=4);d.ellipse((1,1,9,9),fill=1)
        d.line([(6,6),(12,12)],fill=9,width=2);d.ellipse((2,2,8,8),fill=9);d.ellipse((4,4,6,6),fill=1)
        d.line([(10,12),(12,10)],fill=11);d.point((3,3),fill=12)
    elif kind=='bomb':
        d.ellipse((2,4,12,14),fill=1);d.ellipse((3,5,11,13),fill=13)
        d.line([(8,4),(10,2),(12,3)],fill=6);d.rectangle((4,6,6,7),fill=14);d.point((12,2),fill=11)
    elif kind=='heart':
        d.polygon([(2,3),(5,2),(8,4),(11,2),(14,3),(14,7),(8,14),(2,8)],fill=1)
        d.polygon([(3,4),(5,3),(8,5),(11,3),(13,4),(13,7),(8,12),(3,7)],fill=15)
        d.line([(4,4),(5,4),(4,6)],fill=11)
    elif kind=='coin':
        d.ellipse((3,2,12,13),fill=1);d.ellipse((4,3,11,12),fill=8)
        d.line([(6,4),(9,4),(10,6),(10,10)],fill=11);d.line([(7,6),(7,10)],fill=9)
    return im


def plate(down=False):
    """A flat stone pressure plate, using the stone bank, never wood inks."""
    im,d=indexed(16,16)
    d.polygon([(2,0),(13,0),(15,2),(15,13),(13,15),(2,15),(0,13),(0,2)],fill=1)
    d.polygon([(2,1),(13,1),(14,2),(14,12),(12,14),(2,14),(1,12),(1,2)],fill=4)
    d.line([(2,1),(12,1),(14,3)],fill=7)
    d.line([(1,3),(1,11),(3,13),(12,13)],fill=2)
    d.rectangle((3,3 if not down else 4,12,11),fill=5 if not down else 12)
    d.line([(3,3 if not down else 4),(11,3 if not down else 4)],fill=6 if not down else 14)
    # Broad central stamp identifies a plate without looking like a lock.
    if down:
        d.line([(5,8),(7,10),(10,6)],fill=15)
    else:
        d.polygon([(7,5),(10,7),(8,9),(5,7)],fill=2)
        d.line([(6,6),(7,5),(9,6)],fill=7)
    for x,y in ((2,2),(13,2),(2,12),(13,12)):d.point((x,y),fill=6)
    return im


def lift_object(name):
    """Exact ground/carried foreground, bottom-aligned to the16pxcell.

    Returns(image,bank). The renderer uses per-frame palette tables, so no
    material changes colour when picked up or thrown.
    """
    name={'rock_small':'rock','myst_pot':'pot'}.get(name,name)
    im,d=indexed(16,16)
    if name=='bush':
        d.polygon([(2,7),(4,4),(7,4),(9,3),(12,5),(14,8),(13,12),(10,15),(5,15),(2,12)],fill=1)
        d.polygon([(3,7),(6,5),(8,6),(10,4),(12,7),(13,10),(10,13),(5,14),(3,11)],fill=3)
        d.polygon([(4,7),(6,5),(8,7),(7,10),(4,10)],fill=5)
        d.polygon([(9,6),(11,6),(12,8),(10,10),(8,9)],fill=4)
        d.line([(4,7),(6,6)],fill=7);d.line([(6,11),(9,10),(11,12)],fill=2)
        return im,'foliage'
    if name=='rock':
        d.polygon([(2,9),(5,5),(10,4),(13,7),(14,11),(12,14),(5,15),(2,13)],fill=1)
        d.polygon([(3,9),(6,6),(10,5),(12,8),(13,11),(10,13),(5,13),(3,12)],fill=4)
        d.polygon([(4,9),(6,6),(10,6),(9,9),(6,10)],fill=6)
        d.line([(4,10),(6,9)],fill=7);d.line([(10,9),(12,11),(10,13)],fill=3)
        d.line([(4,13),(6,14),(10,14)],fill=2)
        return im,'stone'
    if name=='boulder':
        d.polygon([(0,7),(4,2),(11,1),(15,6),(15,12),(12,15),(3,15),(0,12)],fill=1)
        d.polygon([(1,7),(5,3),(11,2),(14,6),(14,11),(11,13),(4,14),(1,11)],fill=4)
        d.polygon([(2,7),(5,3),(10,3),(11,6),(7,8),(3,9)],fill=6)
        d.line([(4,4),(6,3),(9,3)],fill=7)
        d.polygon([(9,8),(13,6),(14,10),(11,13),(8,12)],fill=3)
        d.line([(3,12),(6,13),(10,13)],fill=2)
        return im,'stone'
    if name=='pot':
        d.polygon([(4,3),(11,3),(11,6),(14,9),(13,13),(10,15),(5,15),(2,13),(1,9),(4,6)],fill=1)
        d.polygon([(5,5),(10,5),(10,7),(12,9),(12,12),(9,14),(5,13),(3,11),(3,9),(5,7)],fill=4)
        d.polygon([(5,7),(7,7),(6,12),(4,11),(4,9)],fill=6)
        d.line([(3,9),(12,9)],fill=7)
        d.rectangle((3,2,12,4),fill=1);d.line([(4,2),(11,2)],fill=8);d.line([(4,3),(11,3)],fill=11)
        d.line([(7,5),(10,5)],fill=2)
        return im,'gold'
    raise KeyError('Unknown lift material '+name)


def beetle(blight=False):
    im,d=indexed(16,16)
    for x,y in [(2,5),(1,9),(3,12),(12,5),(14,9),(12,12)]:d.line([(x,y),(7 if x<8 else 8,y+1)],fill=1,width=2)
    d.ellipse((3,2,12,13),fill=1);d.ellipse((4,3,11,11),fill=3 if not blight else 12)
    d.polygon([(5,3),(8,2),(10,4),(9,7),(5,8)],fill=5 if not blight else 13)
    d.line([(8,3),(8,11)],fill=1);d.ellipse((5,11,10,15),fill=1)
    d.point((6,12),fill=10 if not blight else 14);d.point((9,12),fill=10 if not blight else 14)
    return im
