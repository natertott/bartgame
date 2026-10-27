"""Carried and thrown objects retain their woodland material silhouettes.

The four 16x16 frames share the existing lift palette and resident sheet.
Only foreground pixels are borrowed; no patch of terrain travels with them.
"""
import pack
import forest_art as F
import healthy_reference as H

SOURCE={'bush':'bush','rock':'rock_small','boulder':'boulder','pot':'myst_pot'}


def rgb(hex_):
    return tuple(int(hex_[i:i+2],16) for i in (1,3,5))


def material_pixels(name):
    if name == 'myst_pot':
        # Keep the lifted vessel identical to the final interactive-ground
        # painter rather than reverting to the earlier, smaller pot.
        import interactive_tiles
        return interactive_tiles.REPLACEMENTS[name][0], H.GROUPS['glade_wood_stone']
    if name in H.TILES:
        group,frames,_=H.TILES[name]
        rows=H.quantize(frames[0],group)
        palette=H.GROUPS[group]
    else:
        group,frames,_=F.TILES[name];group=F.PREFIX+group
        old=F.GROUPS[group]
        rows=[''.join('%x'%F.closest(F.HEX[int(v)],old) if v else '0'
                      for v in row) for row in frames[0]]
        palette=H.GROUPS.get(group,old)
    return rows,palette


def frame(name,palette):
    rows,source=material_pixels(SOURCE[name])
    # The scene's mossy stone and green leaves are mapped to the existing
    # load ramp, keeping actor palette use and allocation exactly the same.
    colors=[rgb(c) for c in palette]
    lookup={0:'.'}
    for index,color in enumerate(source[1:],1):
        target=rgb(color)
        match=min(range(1,16),key=lambda k:sum((target[j]-colors[k][j])**2*w
                                              for j,w in enumerate((2,3,2))))
        lookup[index]='%x'%match
    result=[''.join(lookup[int(ch,16)] for ch in row) for row in rows]
    # Loose litter belongs to the ground, never to a floating carried rock.
    points={(x,y) for y,row in enumerate(result) for x,ch in enumerate(row) if ch!='.'}
    components=[]
    while points:
        todo=[points.pop()];component=set(todo)
        while todo:
            x,y=todo.pop()
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    point=(x+dx,y+dy)
                    if point in points:
                        points.remove(point);component.add(point);todo.append(point)
        components.append(component)
    keep=max(components,key=len)
    return [''.join(ch if (x,y) in keep else '.' for x,ch in enumerate(row))
            for y,row in enumerate(result)]


def apply(sheets):
    sheet=next(s for s in sheets if s['name']=='lift')
    names=list(sheet['frames'])
    assert names==list(SOURCE) and (sheet['w'],sheet['h'])==(16,16)
    palette=pack.GROUPS[sheet['pal']]
    sheet['frames']={name:frame(name,palette) for name in names}
    assert all(len(rows)==16 and all(len(row)==16 for row in rows)
               for rows in sheet['frames'].values())
