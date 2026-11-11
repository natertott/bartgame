"""New collision-study rocks; exact two-pixel native collision footprints.

Transparent art exposes the room's real floor. These appended originals do
not alter any previous rock, floor, palette or collision identifier.
"""
from PIL import Image,ImageDraw
KINDS=('nw','ne','se','sw','north','south','west','east','three_eighths')
def occupied(kind,x,y):
    return {'nw':x+y<=7,'ne':x>=y,'se':x+y>=7,'sw':x<=y,
            'north':y<4,'south':y>=4,'west':x<4,'east':x>=4,
            'three_eighths':x<3}[kind]
def image(kind):
    im=Image.new('P',(16,16),0);d=ImageDraw.Draw(im)
    for y in range(16):
        for x in range(16):
            if not occupied(kind,x//2,y//2):continue
            edge=x==0 or y==0 or x==15 or y==15 or any(not occupied(kind,max(0,min(7,(x+dx)//2)),max(0,min(7,(y+dy)//2))) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))
            im.putpixel((x,y),1 if edge else 7 if y%5==1 else 5)
    return im
def rows(im):return [''.join(format(im.getpixel((x,y)),'x') for x in range(16)) for y in range(16)]
METATILES=[dict(name='lh_shape_'+kind,pal='lh_earth',type='SOLID',coll=15,prop=1,art=rows(image(kind))) for kind in KINDS]
MASKS=[tuple(sum(int(occupied(kind,x,y))<<((y%4)*8+x) for y in range(part*4,part*4+4) for x in range(8)) for part in range(2)) for kind in KINDS]
