"""Native-size forest enemies: jeweled vermin and ruined chivalry.

Animation names, frame bounds, facing order and hitboxes stay unchanged.
Palette groups are enemy-only; the hero, gear, UI and Drain folk retain theirs.
"""
from px import Canvas, ball, hflip, vflip

PALETTES = {
'bugs': ['#000000','#101420','#202838','#383848','#586048','#889860','#c8c890',
         '#883058','#e868b8','#fff0c8','#284840','#408078','#88c0a0','#483050','#885090','#e8e0b8'],
'blight':['#000000','#100c20','#202830','#384038','#586848','#88a050','#d0c880',
          '#502038','#983858','#e87898','#281838','#503060','#905098','#d878e8','#f8c8f0','#fff0c0'],
'iron':['#000000','#101820','#203038','#384848','#607068','#98a090','#d8d8b8',
        '#504030','#987048','#d8b060','#f8e8a0','#282838','#484050','#806080','#b8a0b0','#e8d8b0']}


def line(c,x0,y0,x1,y1,color):
    n=max(abs(x1-x0),abs(y1-y0),1)
    for i in range(n+1): c.set(round(x0+(x1-x0)*i/n),round(y0+(y1-y0)*i/n),color)


def beetle(frame):
    phase=int(frame[-1])-1
    c=Canvas(16,16)
    for side in (-1,1):
        for j in range(3):
            y=5+j*3; x=8+side*4
            line(c,x,y,x+side*2,y+(-1 if (j+phase)%2 else 1),2)
    ball(c,8,8,5,5,(1,2,3,4,5),False)
    # The shell is a tarnished scarab, with a thin gold suture.
    for y in range(4,11):
        c.set(7,y,2); c.set(8,y,6 if y<7 else 5)
    line(c,4,6,6,4,6)
    c.ellipse(8,12,3,2,2); c.set(6,11,8); c.set(9,11,8)
    line(c,6,13,4,15,4); line(c,9,13,11,15,4)
    rs=c.rows()
    # Preserve the engine's south/east facing convention.
    return [''.join(rs[15-x][y] for x in range(16)) for y in range(16)] if '_e' in frame else rs


def moth(frame):
    c=Canvas(16,16)
    tucked=frame=='rest'; down=frame=='fly2'
    for side in (-1,1):
        for k in range(6 if not tucked else 3):
            x=8+side*(k+1)
            top=(2+k//3 if not down else 6-k//3)
            bottom=10-(k//2)+ (2 if down else 0)
            for y in range(top,bottom): c.set(x,y,13 if k>3 else 14)
            c.set(x,top,5); c.set(x,bottom,1)
        if not tucked:
            c.set(8+side*4,7,7); c.set(8+side*4,8,8)
    c.ellipse(8,8,2,4,3)
    c.set(7,6,9); c.set(9,6,9)
    c.set(8,10,6); line(c,7,4,5,2,5); line(c,9,4,11,2,5)
    return c.rows()


def slime(frame):
    c=Canvas(16,16)
    squash=frame=='squash'; jump=frame=='jump'
    cy=11 if squash else 7 if jump else 9
    ball(c,8,cy,7 if squash else 5.5,3 if squash else 5,(1,10,11,12,15),False)
    line(c,5,cy-2,7,cy-3,15)
    c.set(6,cy,1); c.set(10,cy,1)
    # Rot has a beautiful surface, and dark sediment caught inside.
    for x,y in ((5,cy+2),(8,cy+1),(11,cy+2)): c.set(x,y,13)
    c.set(10,cy-3,8)
    return c.rows()


def flower(frame):
    c=Canvas(16,16); spit=frame.startswith('spit'); step=frame.startswith('walk')
    c.ellipse(8,13,6,2,2)
    line(c,7,9,4+(1 if step else 0),14,4); line(c,9,9,12,14,3)
    # A bone-white lily with a purple, hungry throat.
    for x,y in ((4,6),(6,3),(10,3),(12,6),(10,9),(6,9)):
        c.ellipse(x,y,2.3,2.5,6); c.set(x,y-1,15)
    c.ellipse(8,6,3,3,10); c.ellipse(8,6,2,2,12 if spit else 1)
    c.set(8,5,14 if spit else 9)
    rs=c.rows()
    return vflip(rs) if frame.endswith('_n') else hflip(rs) if frame.endswith('_e') else rs


def knight(frame):
    c=Canvas(16,32); north='_n' in frame; east='_e' in frame; attack=frame.startswith('atk')
    step=1 if frame.startswith('walk') and frame.endswith('2') else 0
    # Torn cloak, long readable silhouette, moss in the folds.
    for y in range(11,29):
        span=3+(y-11)//6
        c.hline(8-span,8+span,y,11)
        c.set(8-span,y,2); c.set(8+span,y,1)
    c.vline(5,15,26,4); c.vline(10,17,27,3)
    c.rect(5-step,27,7-step,30,2); c.rect(9+step,27,11+step,30,2)
    c.hline(4-step,7-step,30,7); c.hline(9+step,12+step,30,7)
    ball(c,8,16,5,5,(1,2,3,4,5),False)
    c.hline(5,10,14,8); c.hline(5,10,20,7); c.set(7,15,9)
    # Tarnished crown above the closed visor, thorns growing through it.
    ball(c,8,8,4,5,(1,2,3,5,6),False)
    c.hline(4,11,5,8); c.vline(5,2,5,9); c.vline(8,1,4,10); c.vline(10,2,5,8)
    if not north:
        c.hline(5,10,8,1); c.set(6,8,10); c.set(9,8,9)
    c.hline(5,10,11,7)
    if east: c.vline(11,7,10,7)
    # Shield with a sun, a polished fleck amid the rust.
    c.ellipse(3,19,3,5,7); c.ellipse(3,18,2,3,8); c.set(3,17,10); c.set(3,19,9)
    if attack:
        line(c,11,16,15,9,6); c.set(14,9,10)
    else:
        line(c,13,16,13,25,5); c.set(13,14,9)
    return c.rows()


def heart(frame):
    c=Canvas(32,32); pulse=frame=='pulse2'; hurt=frame=='hurt'
    # A reliquary's broken gold halo over a rooted, wet heart.
    for x,y in ((16,2),(23,4),(28,11),(28,19),(23,26),(16,29),(8,26),(3,19),(3,11),(8,4)):
        line(c,16+(x-16)*3//4,16+(y-16)*3//4,x,y,6)
        c.set(x,y,15)
    for side in (-1,1):
        line(c,16+side*3,22,16+side*12,30,2)
        line(c,16+side*7,17,16+side*13,9,3)
        line(c,16+side*11,11,16+side*12,4,4)
    ball(c,16,16,9+int(pulse),10,(1,7,8,9,15 if hurt else 14),False)
    c.ellipse(12,12,4,4,9); c.ellipse(19,12,4,4,12)
    line(c,14,9,16,21,10); line(c,16,21,19,25,10)
    line(c,17,11,21,15,13); c.set(20,14,14)
    c.set(10,11,15); c.set(11,10,15)
    # The dark vertical wound reads even during the attack pulse.
    c.ellipse(16,17,2.5,4,1); c.set(16,16,14); c.set(16,17,15)
    return c.rows()


def apply(sheets):
    painters={'beetle':beetle,'bat':moth,'slime':slime,'spitter':flower,'knight':knight,'boss':heart}
    for s in sheets:
        if s['name'] in painters:
            s['frames']={n:painters[s['name']](n) for n in s['frames']}
            assert all(len(a)==s['h'] and all(len(r)==s['w'] for r in a) for a in s['frames'].values())
