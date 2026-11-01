"""Retire old canopy pictures and retain the non-canopy forest context.

Large compositions are packed separately and fitted by canopy_scene.c after
the semantic room exists. These cheap logical pictures are quiet backing or
new drawings for authored tree footprints; no rejected canopy is reused.
"""
from PIL import Image
import forest_canopy_adaptive as A
import forest_concepts_v2_terrain as BASE
import forest_concepts_v2_topology as T

BANKS = BASE.BANKS
_TREE = ('tree_top_nw','tree_top_ne','tree_mid_w','tree_mid_e',
         'tree_trunk_w','tree_trunk_e')

def owns(name):
    return (name in T.HEALTHY or name in T.BLIGHT or name in T.CONNECTORS or
            name in _TREE or name.startswith(('tree2_','birch_','fir_',
            'sicktree_','gtree_','gtree2_')) or
            (name.startswith('btree_') and int(name[6:]) < 6) or
            name in ('dead_tree','forest_blight_dead_tree'))

def supports(name):
    return BASE.supports(name)

def palette(name, variant=1):
    return A.stage_palette(variant,3) if name == A.PALETTE_NAME else BASE.palette(name,1)

def extra_palettes(variant=1):
    return A.extra_palettes(variant)

def _part(image, index, columns=2):
    x=(index%columns)*16;y=(index//columns)*16
    return image.crop((x,y,x+16,y+16))

def paint(name, phase=0, variant=1):
    if not owns(name):return BASE.paint(name,phase,1)
    if name in T.HEALTHY or name in T.BLIGHT or name in T.CONNECTORS:
        return A.quiet_fill(variant),A.PALETTE_NAME
    if name in _TREE:
        return _part(A.authored_tree(variant),_TREE.index(name)),A.PALETTE_NAME
    for prefix in ('tree2_','birch_','fir_','sicktree_','btree_'):
        if name.startswith(prefix):
            return _part(A.authored_tree(variant,second=prefix in ('tree2_','fir_')),
                         int(name[len(prefix):])),A.PALETTE_NAME
    for prefix in ('gtree_','gtree2_'):
        if name.startswith(prefix):
            return _part(A.authored_tree(variant,large=True,second=prefix=='gtree2_'),
                         int(name[len(prefix):]),3),A.PALETTE_NAME
    return A.prefab(variant,'small'),A.PALETTE_NAME

def paint_adjacency(parent, mask, corners=0, phase=0, variant=1, quadrant=None):
    plain=parent.split('@q')[0]
    if not owns(plain):
        return BASE.paint_adjacency(parent,mask,corners,phase,1,quadrant)
    image=A.quiet_fill(variant).copy();pixels=image.load()
    # Only the subordinate forest boundary needs local corner joins. The
    # visible tree compositions have no world-parity or repeating block rule.
    # A quiet contact edge has unequal two-to-four-pixel tufts. A constant
    # two-pixel inset made neighboring residual cells read as a straight
    # planter rim even when the large tree anatomy was organic.
    contact=(3,3,2,2,4,3,2,2,3,4,3,2,2,3,2,3)
    for y in range(16):
        for x in range(16):
            west=x<8;north=y<8;sx=x if west else 15-x;sy=y if north else 15-y
            hb=8 if west else 2;vb=1 if north else 4
            cb=1 if west and north else 2 if north else 8 if west else 4
            eh=bool(mask&hb);ev=bool(mask&vb)
            hm=contact[(y+(2 if west else 5))%16]
            vm=contact[(x+(0 if north else 7))%16]
            outside=(eh and sx<hm) or (ev and sy<vm)
            if eh and ev and sx<6 and sy<6:outside=(sx-5)**2+(sy-5)**2>24
            if not eh and not ev and corners&cb and sx+sy<4:outside=True
            if outside:pixels[x,y]=0
    return image,A.PALETTE_NAME

def fringe(parent, mask, variant=1):
    # The spatial composer places an actual long branch only where it fits.
    return Image.new('P',(16,16),0),A.PALETTE_NAME

def arch_group(variant=1):
    return BASE.arch_group(1)

def pulse_palettes(variant=1):
    # Existing non-canopy blight keeps its own exact pulse. The new bank uses
    # the room-stage table emitted for canopy_scene_palette_tick().
    return BASE.pulse_palettes(1)
