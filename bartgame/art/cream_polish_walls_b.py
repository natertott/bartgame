"""Two original native Cream refinements: controlled cut stone and erosion beds.

Styles3/4 retain Rind's exact RGB555 material banks. Seven complete geological
paintings fit the existing native master footprints. Their silhouette and
fissures are inset from the asset boundary, and panel_mask explicitly separates
outer wall material from the geological form. No painter resizes source art.
"""
from PIL import Image, ImageDraw
from cream_style_rind import PALETTES as _RIND_PALETTES

PALETTES = {name:list(bank) for name,bank in _RIND_PALETTES.items()}
STYLES = {3:'Weathered Curdstone', 4:'Velvet Travertine'}
SPECS = [
    dict(name='shelf_fold',kind='shelf',variant=0,w=4,h=2),
    dict(name='shelf_cleft',kind='shelf',variant=1,w=4,h=2),
    dict(name='fracture_slant',kind='fracture',variant=0,w=6,h=2),
    dict(name='fracture_rib',kind='fracture',variant=1,w=6,h=2),
    dict(name='blind_bay',kind='arch',variant=0,w=4,h=3),
    dict(name='compact_knuckle',kind='compact',variant=0,w=2,h=2),
    dict(name='compact_split',kind='compact',variant=1,w=2,h=2),
]
SIZES={'shelf':(64,32),'fracture':(96,32),'arch':(64,48),'compact':(32,32)}


def _canvas(size,stage):
    image=Image.new('P',size,3)
    colors=[int(c[i:i+2],16) for c in PALETTES['cream_cliff%d'%stage] for i in (1,3,5)]
    image.putpalette(colors+[0]*(768-len(colors)))
    mask=Image.new('P',size,0)
    mask.putpalette([0,0,0,255,255,255]+[0]*762)
    return image,ImageDraw.Draw(image),mask


def _body(draw,mask,outline,fill=4):
    draw.polygon(outline,fill=fill)
    ImageDraw.Draw(mask).polygon(outline,fill=1)


def _moss(draw,points):
    # Moss is rooted in a stone recess, with one small lit upper-facing tuft.
    draw.polygon(points,fill=9)
    x,y=points[0]
    draw.line([(x+1,y+1),(x+4,y),(x+6,y+1)],fill=10)
    draw.point((x+3,y),fill=11)


def _fracture(draw,points,stage,branches=()):
    # One deliberate narrow stress fracture; sparse attached light, no white
    # zipper/ivory rib or repeated disconnected bright marks.
    draw.line(points,fill=12 if stage==2 else 2,width=1)
    for branch in branches:
        draw.line(branch,fill=2 if stage<2 else 12,width=1)
    if stage==1:
        middle=len(points)//2
        draw.line(points[max(1,middle-1):middle+1],fill=12)
        p=points[middle]
        draw.line([(p[0],p[1]),(p[0]+1,p[1]+2)],fill=1)
    elif stage==2:
        draw.line(points[1:-1],fill=13,width=1)
        for index in (2,len(points)-3):
            if 0<index<len(points)-1:
                x,y=points[index]
                draw.point((x,y),fill=14)
        if len(points)>5:
            x,y=points[3]
            draw.point((x+1,y),fill=12)


def _cut_shelf(draw,mask,stage,v):
    if not v:
        outline=[(3,12),(10,6),(26,7),(35,4),(47,6),(60,13),(59,24),(48,28),(32,26),(17,29),(4,24)]
        _body(draw,mask,outline)
        draw.polygon([(4,11),(11,6),(25,8),(35,5),(47,7),(58,12),(50,16),(36,17),(21,15),(11,17),(4,15)],fill=6)
        draw.polygon([(7,10),(13,8),(24,10),(33,8),(41,8),(46,10),(35,12),(23,12),(12,13)],fill=7)
        draw.line([(6,11),(11,7),(20,8),(25,9)],fill=8)
        draw.polygon([(5,17),(15,19),(24,17),(37,19),(51,17),(57,14),(57,19),(48,23),(34,23),(20,21),(7,22)],fill=2)
        draw.line([(8,20),(20,23),(32,25),(45,25)],fill=3)
        draw.polygon([(9,23),(18,22),(26,24),(24,27),(17,28),(10,26)],fill=5)
        draw.line([(11,23),(18,23),(22,24)],fill=6)
        _moss(draw,[(37,23),(43,22),(49,24),(47,27),(40,28),(35,26)])
        _fracture(draw,[(30,8),(28,11),(30,14),(27,18),(29,21),(26,25)],stage,([(27,18),(21,17),(17,19)],))
    else:
        _body(draw,mask,[(3,9),(15,4),(28,7),(39,3),(52,6),(60,15),(58,25),(48,29),(33,26),(20,28),(5,24)])
        draw.polygon([(4,10),(15,5),(27,8),(32,12),(29,17),(17,19),(6,15)],fill=5)
        draw.polygon([(6,9),(15,5),(24,8),(28,11),(18,13),(9,12)],fill=7)
        draw.line([(6,9),(14,5),(20,6)],fill=8)
        draw.polygon([(6,16),(16,21),(29,18),(32,14),(32,20),(22,24),(9,22)],fill=2)
        draw.polygon([(31,11),(39,4),(51,7),(57,13),(53,18),(43,20),(33,17)],fill=6)
        draw.polygon([(34,10),(40,5),(49,8),(51,11),(42,13)],fill=7)
        draw.line([(34,10),(40,4),(46,6)],fill=8)
        draw.polygon([(32,18),(43,22),(54,19),(57,16),(56,22),(49,26),(37,24)],fill=2)
        draw.polygon([(36,25),(45,24),(54,26),(48,28),(38,27)],fill=5)
        _moss(draw,[(14,23),(20,23),(25,25),(22,27),(15,27),(11,25)])
        _fracture(draw,[(46,8),(43,11),(45,14),(41,18),(42,22),(39,26)],stage,([(41,18),(36,18),(32,20)],))


def _cut_span(draw,mask,stage,v):
    _body(draw,mask,[(3,11),(12,5),(29,6),(41,3),(58,6),(73,4),(87,8),(92,15),(90,26),(76,29),(58,26),(43,29),(25,25),(9,28),(3,23)])
    if not v:
        draw.polygon([(4,11),(13,6),(29,7),(40,4),(54,7),(52,12),(38,16),(24,14),(12,17),(4,15)],fill=6)
        draw.polygon([(7,11),(14,8),(27,9),(36,7),(43,7),(37,10),(26,11),(15,12)],fill=7)
        draw.line([(5,11),(13,6),(22,7)],fill=8)
        draw.polygon([(6,17),(14,20),(25,17),(38,19),(52,15),(56,11),(54,19),(40,23),(26,20),(15,23),(5,20)],fill=2)
        draw.polygon([(56,12),(66,7),(77,6),(87,10),(90,15),(84,19),(72,21),(59,18)],fill=5)
        draw.polygon([(58,12),(67,8),(77,7),(85,11),(81,14),(68,16)],fill=6)
        draw.line([(58,12),(66,7),(74,6)],fill=7)
        draw.line([(65,10),(70,8),(75,8)],fill=8)
        draw.polygon([(59,20),(71,23),(84,21),(90,18),(88,24),(77,27),(64,25)],fill=2)
        draw.polygon([(13,24),(24,22),(34,25),(29,28),(19,27)],fill=5)
        _moss(draw,[(40,23),(46,21),(53,23),(52,26),(46,28),(38,26)])
        _fracture(draw,[(20,8),(25,11),(32,11),(37,15),(45,14),(51,18),(59,20),(65,24),(73,26)],stage,([(37,15),(36,21),(32,25)],[(59,20),(64,16),(70,14),(72,10)]))
    else:
        draw.polygon([(4,12),(12,6),(28,7),(36,13),(33,19),(18,21),(5,17)],fill=6)
        draw.polygon([(8,11),(14,8),(25,9),(28,12),(18,14)],fill=7)
        draw.line([(5,12),(12,6),(20,7)],fill=8)
        draw.polygon([(5,18),(18,24),(32,21),(37,16),(37,22),(25,26),(10,25)],fill=2)
        draw.polygon([(36,12),(45,5),(59,7),(68,5),(81,8),(89,14),(86,19),(73,22),(61,19),(48,22),(37,18)],fill=5)
        draw.polygon([(39,12),(46,6),(57,8),(67,6),(78,9),(81,12),(69,16),(57,14),(48,17)],fill=6)
        draw.line([(40,11),(46,6),(54,7)],fill=8)
        draw.line([(62,8),(68,6),(75,8)],fill=7)
        draw.polygon([(40,20),(49,25),(61,22),(74,25),(87,22),(88,18),(89,24),(77,27),(61,25),(47,27)],fill=2)
        draw.polygon([(42,25),(49,24),(56,26),(51,28),(44,27)],fill=5)
        _moss(draw,[(15,24),(22,24),(27,26),(23,28),(16,28),(11,26)])
        _fracture(draw,[(62,8),(59,11),(61,14),(57,18),(59,21),(55,25)],stage,([(57,18),(49,18),(44,15),(39,16)],[(59,11),(68,12),(73,10),(79,11)]))


def _cut_arch(draw,mask,stage):
    _body(draw,mask,[(3,37),(4,23),(10,14),(20,6),(31,3),(43,6),(53,14),(59,26),(60,39),(55,44),(40,43),(25,45),(10,43)])
    draw.polygon([(7,34),(8,24),(13,16),(21,10),(31,6),(41,9),(49,16),(54,26),(55,37),(50,40),(15,40)],fill=2)
    # A rock-filled shallow niche, not a black mouth or a false tunnel.
    draw.polygon([(15,35),(15,27),(19,20),(25,16),(32,13),(39,17),(45,23),(48,31),(47,37),(34,39),(20,38)],fill=4)
    draw.polygon([(17,26),(23,20),(31,16),(38,20),(42,25),(35,27),(25,25)],fill=5)
    draw.line([(17,27),(25,25),(34,28),(44,27)],fill=2)
    draw.polygon([(19,31),(29,29),(37,32),(45,31),(46,36),(34,37),(22,35)],fill=3)
    draw.line([(23,34),(31,33),(38,35)],fill=4)
    # The left stone shoulder carries the upper-left light; only some joints
    # interrupt the irregular broad planes, avoiding repetitive voussoirs.
    draw.polygon([(6,34),(7,23),(12,15),(21,8),(31,4),(40,7),(49,14),(54,24),(56,36),(51,37),(49,25),(44,18),(38,13),(31,10),(24,14),(17,20),(12,27),(12,35)],fill=5)
    draw.polygon([(7,26),(12,16),(21,9),(31,5),(36,7),(29,10),(22,14),(16,20),(11,29),(10,34),(7,34)],fill=6)
    draw.line([(8,24),(13,15),(22,8),(30,4)],fill=7)
    draw.line([(12,17),(16,13),(22,10)],fill=8)
    draw.polygon([(41,13),(47,18),(51,26),(52,34),(49,32),(47,25),(43,19)],fill=3)
    draw.line([(14,18),(17,20)],fill=3)
    draw.line([(24,10),(25,13)],fill=4)
    draw.line([(43,13),(45,16)],fill=3)
    # A broad seated sill visibly closes the entire base of the blind relief.
    draw.polygon([(5,37),(14,34),(26,36),(39,34),(52,37),(58,41),(52,43),(40,41),(27,43),(12,41),(5,40)],fill=5)
    draw.line([(6,37),(14,35),(25,37)],fill=7)
    draw.line([(11,42),(25,44),(39,42),(51,43)],fill=2)
    _moss(draw,[(42,27),(47,26),(50,29),(48,34),(44,36),(39,33)])
    _fracture(draw,[(35,7),(34,12),(37,17),(34,22),(36,27),(33,32),(34,37),(30,41)],stage,([(34,22),(27,24),(22,22),(18,24)],))


def _soft_shelf(draw,mask,stage,v):
    if not v:
        _body(draw,mask,[(3,13),(7,7),(18,4),(31,5),(39,8),(51,7),(59,13),(60,23),(51,27),(37,28),(24,26),(11,29),(4,25)])
        draw.polygon([(4,12),(8,8),(18,5),(30,6),(39,10),(34,14),(20,16),(8,16),(4,15)],fill=6)
        draw.line([(6,11),(11,8),(19,6),(27,7)],fill=7)
        draw.line([(9,10),(14,8),(20,8)],fill=8)
        draw.polygon([(6,17),(20,20),(34,17),(41,12),(40,19),(30,23),(16,23),(6,21)],fill=2)
        draw.polygon([(39,12),(49,9),(56,12),(58,17),(52,20),(44,20),(38,17)],fill=5)
        draw.line([(40,13),(48,10),(53,12)],fill=6)
        draw.polygon([(30,24),(40,22),(52,24),(52,26),(43,28),(32,26)],fill=5)
        draw.line([(31,24),(39,23),(46,24)],fill=6)
        _moss(draw,[(10,23),(17,23),(21,25),(19,27),(12,28),(7,26)])
        _fracture(draw,[(29,8),(27,12),(29,16),(26,20),(28,23),(25,26)],stage,([(26,20),(20,19),(16,21)],))
    else:
        _body(draw,mask,[(3,12),(10,6),(23,5),(33,9),(44,4),(54,7),(60,15),(58,25),(47,29),(34,26),(20,28),(7,25)])
        draw.polygon([(5,12),(11,7),(23,6),(31,10),(30,16),(18,20),(7,17)],fill=5)
        draw.polygon([(7,11),(13,8),(22,8),(27,11),(18,14),(9,14)],fill=6)
        draw.line([(9,10),(14,8),(20,8)],fill=7)
        draw.polygon([(7,18),(19,23),(30,18),(33,13),(33,21),(23,26),(12,24)],fill=2)
        draw.polygon([(32,12),(43,5),(53,8),(57,14),(52,19),(40,20),(33,17)],fill=6)
        draw.line([(35,11),(43,6),(50,8)],fill=7)
        draw.line([(39,9),(43,7),(47,8)],fill=8)
        draw.polygon([(35,21),(43,24),(53,21),(56,18),(56,23),(47,27),(38,25)],fill=2)
        _moss(draw,[(12,24),(18,23),(24,25),(21,27),(14,27),(9,26)])
        _fracture(draw,[(47,9),(44,12),(46,15),(42,19),(43,22),(40,26)],stage,([(42,19),(35,20),(31,18)],))


def _soft_span(draw,mask,stage,v):
    _body(draw,mask,[(3,12),(10,6),(23,4),(38,7),(50,4),(63,6),(74,4),(86,8),(92,16),(90,25),(77,29),(63,26),(49,29),(34,26),(20,29),(6,25)])
    if not v:
        draw.polygon([(4,12),(11,7),(23,5),(37,8),(44,13),(40,18),(27,20),(13,18),(5,16)],fill=6)
        draw.line([(7,11),(13,8),(24,6),(34,9)],fill=7)
        draw.line([(11,10),(16,8),(23,8)],fill=8)
        draw.polygon([(6,18),(15,22),(27,24),(41,20),(47,14),(47,21),(36,26),(24,25),(10,25)],fill=2)
        draw.polygon([(47,13),(55,7),(65,8),(74,6),(84,10),(89,16),(84,20),(71,22),(59,19),(49,20)],fill=5)
        draw.polygon([(50,12),(56,8),(64,9),(73,7),(81,10),(82,13),(71,16),(61,14),(55,16)],fill=6)
        draw.line([(51,12),(57,8),(63,9)],fill=7)
        draw.line([(70,9),(75,8),(80,10)],fill=7)
        draw.polygon([(50,21),(59,24),(71,25),(85,22),(89,19),(88,24),(77,27),(64,25),(53,26)],fill=2)
        _moss(draw,[(22,24),(29,23),(34,25),(31,28),(24,28),(19,26)])
        _fracture(draw,[(26,8),(31,11),(37,12),(43,16),(50,16),(55,20),(63,21),(69,25),(77,26)],stage,([(43,16),(41,21),(37,25)],[(63,21),(67,17),(73,15),(75,11)]))
    else:
        draw.polygon([(4,12),(10,7),(23,5),(35,8),(40,13),(35,18),(22,20),(9,18),(4,16)],fill=5)
        draw.line([(7,11),(13,8),(24,6),(31,9)],fill=7)
        draw.polygon([(6,19),(20,24),(35,21),(42,15),(41,22),(28,26),(13,25)],fill=2)
        draw.polygon([(39,13),(48,6),(61,8),(73,5),(85,9),(90,16),(85,21),(73,23),(60,20),(46,23),(38,19)],fill=6)
        draw.polygon([(42,12),(50,8),(60,10),(72,7),(81,10),(82,13),(73,16),(62,14),(51,17)],fill=7)
        draw.line([(45,11),(50,8),(56,9)],fill=8)
        draw.polygon([(42,23),(48,26),(61,23),(74,27),(86,23),(88,19),(88,25),(77,28),(62,25),(49,28)],fill=2)
        _moss(draw,[(13,24),(20,23),(26,25),(24,28),(16,28),(10,26)])
        _fracture(draw,[(62,9),(59,12),(61,15),(57,19),(59,22),(55,26)],stage,([(57,19),(50,18),(45,15),(40,17)],[(59,12),(67,13),(73,11),(79,12)]))


def _soft_arch(draw,mask,stage):
    _body(draw,mask,[(3,36),(4,24),(10,14),(20,7),(31,3),(44,7),(54,17),(59,29),(59,40),(52,44),(39,42),(26,45),(12,42)])
    # Erosion has softened the shoulders, but the geological bay is visibly
    # backed by connected bedding, not cut through like a traversable cave.
    draw.polygon([(8,35),(9,24),(15,16),(23,11),(31,8),(40,12),(48,20),(52,30),(52,38),(44,40),(19,40)],fill=2)
    draw.polygon([(15,35),(16,27),(21,20),(31,15),(39,20),(44,28),(46,37),(35,39),(21,37)],fill=4)
    draw.polygon([(18,28),(23,22),(31,18),(38,23),(41,28),(34,30),(25,28)],fill=5)
    draw.line([(18,30),(26,28),(35,31),(42,29)],fill=2)
    draw.polygon([(21,34),(29,32),(37,35),(44,33),(45,37),(35,38),(24,36)],fill=3)
    draw.polygon([(7,34),(8,24),(13,16),(22,9),(31,5),(41,10),(49,18),(54,29),(54,37),(49,36),(47,26),(42,19),(36,14),(31,12),(24,16),(18,23),(13,30),(12,36)],fill=5)
    draw.polygon([(8,28),(13,18),(22,11),(31,7),(36,10),(28,14),(21,20),(16,27),(12,35),(9,34)],fill=6)
    draw.line([(9,25),(14,17),(22,11),(30,6)],fill=7)
    draw.line([(14,19),(18,15),(23,13)],fill=8)
    draw.line([(41,15),(45,21),(48,29)],fill=3)
    draw.polygon([(6,37),(15,34),(27,36),(40,34),(52,37),(57,41),(50,42),(39,40),(27,43),(14,40),(7,41)],fill=5)
    draw.line([(7,37),(15,35),(25,37)],fill=6)
    draw.line([(11,41),(25,44),(39,41),(51,43)],fill=2)
    _moss(draw,[(40,28),(46,27),(50,30),(47,35),(42,36),(38,33)])
    _fracture(draw,[(35,9),(33,13),(36,18),(33,23),(35,28),(32,33),(33,37),(29,41)],stage,([(33,23),(27,25),(22,23),(18,25)],))


def _compact(draw,mask,stage,v,soft):
    if not v:
        _body(draw,mask,[(3,12),(8,5),(18,4),(26,9),(29,18),(25,26),(16,29),(5,25)])
        draw.polygon([(4,12),(9,6),(18,5),(25,10),(26,14),(19,18),(9,16),(4,15)],fill=6 if not soft else 5)
        draw.line([(6,11),(10,7),(17,6),(22,9)],fill=7)
        draw.line([(9,9),(12,7),(16,7)],fill=8 if not soft else 6)
        draw.polygon([(5,17),(13,21),(22,21),(27,16),(26,22),(20,25),(9,22)],fill=2)
        draw.polygon([(9,25),(16,23),(24,26),(20,28),(12,27)],fill=5)
        _moss(draw,[(5,21),(11,21),(15,24),(12,26),(7,25),(4,24)])
        _fracture(draw,[(19,8),(17,11),(19,14),(16,18),(18,22),(15,26)],stage,([(16,18),(12,17),(8,19)],))
    else:
        _body(draw,mask,[(3,12),(8,6),(15,8),(21,4),(28,10),(29,23),(23,28),(14,26),(5,28)])
        draw.polygon([(4,12),(8,7),(14,9),(17,13),(14,18),(6,18),(4,15)],fill=5)
        draw.line([(6,11),(9,8),(13,10)],fill=7 if not soft else 6)
        draw.polygon([(6,19),(13,22),(18,16),(18,22),(13,25),(7,23)],fill=2)
        draw.polygon([(16,13),(22,5),(27,10),(27,16),(22,19),(17,17)],fill=6)
        draw.line([(19,11),(22,7),(25,10)],fill=7)
        draw.polygon([(18,20),(23,23),(28,20),(27,24),(23,26),(19,24)],fill=2)
        _moss(draw,[(7,24),(13,23),(18,25),(15,27),(9,27),(5,26)])
        _fracture(draw,[(13,10),(14,13),(11,17),(14,21),(13,24),(16,26)],stage,([(14,21),(20,20),(24,18)],))


def _render(style,stage,kind,variant):
    if style not in STYLES:raise ValueError('walls_b supplies styles3 and4')
    stage=max(0,min(2,int(stage)))
    if kind not in SIZES:raise ValueError('unknown wall kind '+kind)
    image,draw,mask=_canvas(SIZES[kind],stage)
    variant=int(variant)%2
    if style==3:
        if kind=='shelf':_cut_shelf(draw,mask,stage,variant)
        elif kind=='fracture':_cut_span(draw,mask,stage,variant)
        elif kind=='arch':_cut_arch(draw,mask,stage)
        else:_compact(draw,mask,stage,variant,False)
    else:
        if kind=='shelf':_soft_shelf(draw,mask,stage,variant)
        elif kind=='fracture':_soft_span(draw,mask,stage,variant)
        elif kind=='arch':_soft_arch(draw,mask,stage)
        else:_compact(draw,mask,stage,variant,True)
    # Guarantee the whole meaningful silhouette ends naturally before the
    # asset boundary, rather than sawing off a cliff detail at the lastpixel.
    w,h=image.size
    for y in range(h):
        for x in range(w):
            if image.getpixel((x,y))!=3:
                mask.putpixel((x,y),1)
            if x<2 or y<2 or x>=w-2 or y>=h-2:
                image.putpixel((x,y),3);mask.putpixel((x,y),0)
    return image,mask


def panel(style=3,stage=0,kind='shelf',variant=0):
    return _render(style,stage,kind,variant)[0]


def panel_mask(style=3,stage=0,kind='shelf',variant=0):
    return _render(style,stage,kind,variant)[1]


def backing(style=3,stage=0):
    if style not in STYLES:raise ValueError('walls_b supplies styles3 and4')
    stage=max(0,min(2,int(stage)))
    image,draw,_=_canvas((128,48),stage)
    # Broad quiet beds use long native pixel runs, not a centered motif per
    # cell. Their simple edges retain budget for the more important figures.
    if style==3:
        draw.polygon([(4,8),(29,8),(33,6),(58,6),(64,9),(89,9),(94,12),(123,12),(123,19),(95,19),(89,17),(65,17),(59,15),(35,15),(29,18),(4,18)],fill=4)
        draw.polygon([(4,31),(21,31),(28,28),(54,28),(60,31),(86,31),(92,29),(123,29),(123,39),(97,39),(90,41),(63,41),(57,37),(31,37),(24,39),(4,39)],fill=4)
        draw.line([(14,21),(29,21),(34,23),(46,23)],fill=2)
        draw.line([(63,41),(75,42),(84,41)],fill=2)
        _moss(draw,[(91,21),(98,20),(105,23),(102,26),(95,26),(89,24)])
        _fracture(draw,[(105,16),(103,19),(105,23),(102,27),(104,30)],stage)
    else:
        draw.polygon([(4,12),(19,12),(27,8),(49,8),(57,11),(80,11),(87,8),(108,8),(123,14),(123,21),(111,21),(104,18),(82,18),(75,21),(53,21),(46,17),(26,17),(20,20),(4,20)],fill=4)
        draw.polygon([(4,32),(19,32),(26,29),(48,29),(56,32),(80,32),(88,30),(112,30),(123,34),(123,40),(103,40),(96,42),(74,42),(67,38),(45,38),(38,40),(17,40),(4,37)],fill=4)
        draw.line([(15,23),(28,24),(41,23),(50,25)],fill=2)
        draw.line([(68,40),(78,42),(89,41)],fill=2)
        _moss(draw,[(92,24),(99,23),(106,26),(103,29),(96,29),(90,27)])
        _fracture(draw,[(107,17),(104,21),(106,24),(103,28),(105,31)],stage)
    return image


def filler(style=3,stage=0,kind='mid',variant=0):
    if style not in STYLES:raise ValueError('walls_b supplies styles3 and4')
    image,draw,_=_canvas((16,16),max(0,min(2,int(stage))))
    if kind=='top':
        draw.rectangle((0,0,15,2),fill=4);draw.line((0,3,15,3),fill=2)
    elif kind in ('base','bottom'):
        draw.rectangle((0,13,15,15),fill=2);draw.line((0,15,15,15),fill=1)
    elif kind=='left':
        draw.rectangle((0,0,1,15),fill=2);draw.line((2,0,2,15),fill=4)
    elif kind=='right':draw.rectangle((14,0,15,15),fill=2)
    elif kind!='mid':raise ValueError('unknown wall backing kind '+kind)
    return image
