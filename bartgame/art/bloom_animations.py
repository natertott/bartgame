"""Bloom's action bodies, with the original flower and clothing preserved.

Idle/walking art and palette remain untouched. Weapons, carried objects and
swing trails are separate engine layers, so these poses contain Bloom only.
Directional guard steps, lift poses and collapse frames append to the old
frame order. Existing frame IDs and the 32-tile streamed body stay stable.
All frames use the original 64x32 sheet, with feet anchored at (32, 32).
"""
from px import Canvas


# Hands are native positions inside the 64x32 hero frame. The action layers
# use these same points; west mirrors east at x = 31.5.
SWORD_HAND = {
    'n': ((42, 16), (32, 15), (22, 16)),
    'e': ((36, 15), (43, 19), (36, 23)),
    's': ((42, 19), (32, 26), (22, 20)),
}
USE_HAND = {'n': (39, 16), 'e': (42, 19), 's': (39, 23)}
BOW_HAND = {'n': (32, 9), 'e': (42, 14), 's': (32, 24)}
CARRY_HAND = ((25, 7), (39, 7))


def _poly(c, points, color):
    for y in range(c.h):
        for x in range(c.w):
            px, py = x + .5, y + .5
            inside = False
            for i, (ax, ay) in enumerate(points):
                bx, by = points[(i + 1) % len(points)]
                if (ay > py) != (by > py) and px < (bx-ax)*(py-ay)/(by-ay)+ax:
                    inside = not inside
            if inside:
                c.set(x, y, color)


def _line(c, points, color, width=1):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        steps = max(abs(bx-ax), abs(by-ay), 1)
        for k in range(steps+1):
            x = round(ax + (bx-ax)*k/steps)
            y = round(ay + (by-ay)*k/steps)
            c.rect(x-(width-1)//2, y-(width-1)//2,
                   x+width//2, y+width//2, color)


def _components(rows):
    points = {(x,y) for y,row in enumerate(rows) for x,ch in enumerate(row) if ch != '.'}
    result = []
    while points:
        q = [points.pop()]
        cc = set(q)
        while q:
            x,y = q.pop()
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    p = (x+dx,y+dy)
                    if p in points:
                        points.remove(p); cc.add(p); q.append(p)
        result.append(cc)
    return result


def _roll(rows, turn):
    c = Canvas.from_rows(rows)
    # The imported turns mix the body with green debris, long cream speed
    # strokes, and a baked gray shadow. Retain only the compact tumbler.
    for y in range(32):
        for x in range(64):
            col = c.get(x,y)
            air = col in (14,15) and (
                (turn == 2 and x >= 40) or
                (turn == 3 and (x >= 43 or y >= 23 or (x >= 38 and y <= 9))) or
                turn in (4,5) or
                (turn == 6 and x < 30))
            extra_leaf = turn == 1 and (y < 5 or (x < 27 and y < 12))
            if col == 7 or air or extra_leaf or (turn == 5 and y < 6):
                c.set(x,y,-1)
    keep = max(_components(c.rows()), key=len)
    clean = Canvas(64,32)
    x0,x1 = min(x for x,y in keep),max(x for x,y in keep)
    y1 = max(y for x,y in keep)
    dx = 32 - round((x0+x1)/2)
    dy = 29-y1
    for x,y in keep:
        clean.set(x+dx,y+dy,c.get(x,y))
    return clean.rows()


def _base(idle, facing, dx=0, dy=0):
    """Keep the head, torso, coat hem and boots; make room for posed arms."""
    c = Canvas(64,32)
    for y,row in enumerate(idle[facing]):
        for x,ch in enumerate(row):
            if ch == '.' or (int(ch,16) == 7 and y >= 26):
                continue
            arm = 16 <= y <= 22 and ((20 <= x <= 26) or (37 <= x <= 43))
            if not arm:
                c.set(x+dx,y+dy,int(ch,16))
    return c


def _arm(c, shoulder, elbow, hand, raised=False):
    """One compact leaf sleeve and a small cream hand, with joined clusters."""
    _line(c,[shoulder,elbow,hand],1,3)
    _line(c,[shoulder,elbow,hand],3,2)
    _line(c,[shoulder,(elbow[0],elbow[1]-1),hand],5)
    _line(c,[(shoulder[0]-1,shoulder[1]-1),(elbow[0]-1,elbow[1]-1)],10)
    hx,hy = hand
    c.rect(hx-1,hy-1,hx+1,hy+1,1)
    c.rect(hx-1,hy-1,hx,hy,15)
    c.set(hx+1,hy,14)


def _head_in_front(c, idle, facing, dy=0):
    """The blossom occludes far-side arms instead of wearing gloves on it."""
    for y,row in enumerate(idle[facing][:17]):
        for x,ch in enumerate(row):
            if ch != '.':c.set(x,y+dy,int(ch,16))


def _boots(c, rows):
    for y in range(25,32):
        for x in range(64):c.set(x,y,-1)
    for y,row in enumerate(rows):
        if y<25:continue
        for x,ch in enumerate(row):
            if ch not in '.7':c.set(x,y,int(ch,16))


def _finish(c):
    # Clearing the imported resting arms can leave a loose coat tip. Every
    # new action body is one joined silhouette, including its hands/boots.
    rows = c.rows()
    keep = max(_components(rows),key=len)
    return [''.join(ch if (x,y) in keep else '.' for x,ch in enumerate(row))
            for y,row in enumerate(rows)]


def _attack(idle, facing, phase):
    hand = SWORD_HAND[facing][phase]
    lean = (-1,0,1)[phase] if facing == 'e' else (1,0,-1)[phase]
    c = _base(idle,facing,lean,1 if phase == 0 else 0)
    # The free arm balances the changing sword arm; the flower's head and
    # expression stay intact while the shoulders turn into the blow.
    if facing == 'n':
        active=27 if phase==2 else 37
        free=37 if phase==2 else 27
        _arm(c,(free,18),(free,20),(free+(-1 if free<32 else 1),22))
        _arm(c,(active,17),((active+hand[0])//2,18),hand)
        _head_in_front(c,idle,facing,1 if phase==0 else 0)
    elif facing == 's':
        active=27 if phase==2 else 37
        free=37 if phase==2 else 27
        _arm(c,(free,18),(free,20),(free+(-2 if free<32 else 2),22))
        _arm(c,(active,18),((active+hand[0])//2,22),hand)
    else:
        _arm(c,(29,18),(27,20),(28,22))
        _arm(c,(36,18),(39,19),hand)
    return _finish(c)


def _use(idle, facing, phase):
    c = _base(idle,facing,0,1 if phase == 0 else 0)
    # The hand stays on a fixed item grip; the supporting elbow and stance
    # supply anticipation, extension and recovery without sliding the prop.
    hand = USE_HAND[facing]
    if facing == 'n':
        _arm(c,(27,17),(28,19-phase//2),(31,18))
        _arm(c,(37,17),(40,18 if phase == 1 else 19),hand)
    elif facing == 's':
        _arm(c,(27,18),(28,22),(33,23))
        _arm(c,(37,18),(40,20 if phase == 1 else 21),hand)
    else:
        _arm(c,(29,18),(32,21),(37,20))
        _arm(c,(36,17),(39,17 if phase == 1 else 18),hand)
    if facing=='n':_head_in_front(c,idle,facing,1 if phase==0 else 0)
    return _finish(c)


def _bow(idle, facing, phase):
    c=_base(idle,facing,0,1 if phase==2 else 0)
    hand=BOW_HAND[facing]
    if facing=='n':
        _arm(c,(27,18),(24,13),(27,10))
        _arm(c,(37,18),(40,13),hand)
        _head_in_front(c,idle,facing,1 if phase==2 else 0)
    elif facing=='s':
        _arm(c,(27,18),(27,22),(29,24))
        _arm(c,(37,18),(37,22),hand)
    else:
        _arm(c,(29,18),(33,17),(36,15))
        _arm(c,(36,18),(39,16),hand)
    return _finish(c)


def _guard(idle, facing):
    c = _base(idle,facing,0,1)
    if facing == 'n':
        _arm(c,(27,18),(30,17),(34,14))
        _arm(c,(37,18),(40,18),(42,16))
        _head_in_front(c,idle,facing,1)
    elif facing == 's':
        _arm(c,(27,19),(28,22),(31,23))
        _arm(c,(37,19),(36,22),(33,23))
    else:
        _arm(c,(29,19),(32,22),(36,22))
        _arm(c,(36,18),(40,20),(41,22))
    return _finish(c)


def _carry(idle, facing, step):
    c = _base(idle,facing)
    _arm(c,(27,18),(21,13),CARRY_HAND[0])
    _arm(c,(37,18),(43,13),CARRY_HAND[1])
    _head_in_front(c,idle,facing)
    if facing!='n':
        # Near-side palms wrap the bottom corners of the overhead load;
        # far-side north hands remain naturally behind the blossom.
        for hx,hy in CARRY_HAND:
            c.rect(hx-1,hy-1,hx+1,hy+1,1)
            c.rect(hx-1,hy-1,hx,hy,15)
            c.set(hx+1,hy,14)
    if step:
        # An alternating one-pixel boot step; the held load remains stable.
        for y in range(25,32):
            for x in range(64):
                c.set(x,y,-1)
        for y,row in enumerate(idle[facing]):
            if y < 25:
                continue
            for x,ch in enumerate(row):
                if ch == '.' or ch == '7':
                    continue
                lift = (x < 32) == (step == 1)
                c.set(x,y-int(lift),int(ch,16))
    return _finish(c)


def _lift(idle, facing, phase):
    if phase==2:return _carry(idle,facing,0)
    c=_base(idle,facing,0,2 if phase==0 else 1)
    hands={
        'n':(((27,23),(37,23)),((25,13),(39,13))),
        'e':(((39,27),(45,25)),((35,17),(42,16))),
        's':(((27,29),(37,29)),((26,17),(38,17))),
    }[facing][phase]
    if phase==0:
        _arm(c,(27,20),(hands[0][0]-1,24),hands[0])
        _arm(c,(37,20),(hands[1][0]+1,24),hands[1])
    else:
        _arm(c,(27,19),(23,17),hands[0])
        _arm(c,(37,19),(42,17),hands[1])
    if facing=='n':_head_in_front(c,idle,facing,2 if phase==0 else 1)
    return _finish(c)


def _cape(idle, facing, phase):
    # The separate item-coloured cape layer unfolds behind this body.
    c = _base(idle,facing,0,1 if phase != 1 else 0)
    if phase == 1:
        # Tuck the boots at the apex; keep the world shadow in the engine.
        for y in range(25,32):
            for x in range(64):
                c.set(x,y,-1)
        _poly(c,[(27,23),(30,23),(30,25),(27,26),(25,25)],1)
        c.rect(27,23,29,24,2)
        _poly(c,[(34,23),(37,22),(39,23),(38,25),(35,25)],1)
        c.rect(35,23,37,24,2)
    if facing == 'n':
        _arm(c,(27,17),(24,18),(22,19))
        _arm(c,(37,17),(40,18),(42,19))
    elif facing == 's':
        _arm(c,(27,18),(24,19),(22,20))
        _arm(c,(37,18),(40,19),(42,20))
    else:
        _arm(c,(28,18),(25,17),(24,16))
        _arm(c,(36,18),(39,17),(41,16))
    return _finish(c)


def _itemget(idle):
    c = _base(idle,'s',0,0)
    # Raise both hands around the original blossom, with its original face.
    _arm(c,(27,18),(20,13),(19,5))
    _arm(c,(37,18),(44,13),(45,5))
    return _finish(c)


def _crouch(idle, facing, depth):
    """Keep the flower round while folding the coat and legs below it."""
    src=idle[facing];c=Canvas(64,32)
    for y,row in enumerate(src):
        if y<17:
            dest=y+depth
        else:
            dest=17+depth+round((y-17)*(14-depth)/14)
        for x,ch in enumerate(row):
            if ch!='.' and not (ch=='7' and y>=26):c.set(x,dest,int(ch,16))
    return _finish(c)


def _resample(rows, width, height, cx=32, cy=24, turns=0):
    points=[(x,y) for y,row in enumerate(rows) for x,ch in enumerate(row) if ch!='.']
    left,right=min(x for x,y in points),max(x for x,y in points)
    top,bottom=min(y for x,y in points),max(y for x,y in points)
    a=[list(row[left:right+1]) for row in rows[top:bottom+1]]
    for _ in range(turns%4):a=[list(row) for row in zip(*a[::-1])]
    h,w=len(a),len(a[0]);c=Canvas(64,32)
    for y in range(height):
        for x in range(width):
            ch=a[min(h-1,int((y+.5)*h/height))][min(w-1,int((x+.5)*w/width))]
            if ch!='.':c.set(cx-width//2+x,cy-height//2+y,int(ch,16))
    return _finish(c)


def _drown(idle, phase):
    """A progressively submerged blossom and one small surface reflection.

    No solid blue skirt, detached bubbles or baked terrain rectangle is
    carried to a pond whose actual water may have a different colour.
    """
    c=Canvas(64,32);shift=(10,18,24)[phase]
    for y,row in enumerate(idle['s'][:18]):
        for x,ch in enumerate(row):
            if ch!='.' and y+shift<29:c.set(x,y+shift,int(ch,16))
    # The single connected lip fits inside the 16px water cell.
    _line(c,[(25,27),(26,28),(29,29),(35,29),(38,28),(39,27)],12)
    return c.rows()


def _hurt(idle, facing):
    c=_base(idle,facing,0,1)
    if facing=='e':
        _arm(c,(29,19),(26,22),(26,24))
        _arm(c,(36,19),(39,22),(39,24))
    else:
        _arm(c,(27,19),(24,21),(24,23))
        _arm(c,(37,19),(40,21),(40,23))
    if facing=='n':_head_in_front(c,idle,facing,1)
    return _finish(c)


def _death(idle, phase):
    if phase==0:return _crouch(idle,'s',3)
    kneel=_crouch(idle,'s',7)
    c=Canvas.from_rows(kneel)
    # The little face closes its eyes while the flower slumps; preserve its
    # petal outline and palette instead of flashing a standing hurt pose.
    for y in (18,19):
        for x in range(27,36):
            if c.get(x,y)==1:c.set(x,y,15)
    _line(c,[(27,18),(29,18)],1)
    _line(c,[(33,18),(35,18)],1)
    if phase==1:return _finish(c)
    # Settle on the ground, a compact sideways flower and folded coat.
    return _resample(_finish(c),29,18,cx=32,cy=23,turns=1)


def apply(sheets):
    hero = next(s for s in sheets if s['name'] == 'hero')
    frames = hero['frames']
    idle = {f:frames['idle_'+f] for f in 'nes'}
    for turn in range(1,8):
        frames['roll_'+str(turn)] = _roll(frames['roll_'+str(turn)],turn)
    for f in 'nes':
        for phase,suffix in enumerate(('1','','3')):
            frames['atk_'+f+suffix] = _attack(idle,f,phase)
        frames['guard_'+f] = _guard(idle,f)
        for step,suffix in enumerate(('', '1', '2')):
            frames['carry_'+f+suffix] = _carry(idle,f,step)
        for phase in range(3):
            frames['use_'+f+str(phase+1)] = _use(idle,f,phase)
            frames['cape_'+f+str(phase+1)] = _cape(idle,f,phase)
        frames['jump_'+f] = frames['cape_'+f+'2']
        frames['hurt_'+f] = _hurt(idle,f)
    frames['itemget'] = _itemget(idle)
    clean_roll=frames['roll_3']
    for phase,(w,h,cy) in enumerate(((22,20,22),(16,15,25),(10,9,27))):
        frames['fall_'+str(phase+1)]=_resample(clean_roll,w,h,cy=cy,turns=phase)
        frames['drown_'+str(phase+1)]=_drown(idle,phase)
    # Append only: save data and every established F_HERO_* index stay put.
    for f in 'nes':
        for step in (1,2):
            c=Canvas.from_rows(frames['guard_'+f])
            _boots(c,frames['walk_'+f+str(step)])
            frames['guard_'+f+str(step)]=_finish(c)
    for f in 'nes':
        for phase in range(3):frames['lift_'+f+str(phase)]=_lift(idle,f,phase)
    for phase in range(3):frames['dead_'+str(phase)]=_death(idle,phase)
    for f in 'nes':
        for phase in range(3):frames['bow_'+f+str(phase)]=_bow(idle,f,phase)
    for f in 'ns':
        for phase,depth in ((1,3),(6,7),(7,1)):
            frames['roll_'+f+str(phase)]=_crouch(idle,f,depth)
    for name,rows in frames.items():
        assert len(rows) == 32 and all(len(row) == 64 for row in rows),name
