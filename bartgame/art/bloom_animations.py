"""Bloom's action bodies, with the original flower and clothing preserved.

Idle/walking art and palette remain untouched. Weapons, carried objects and
swing trails are separate engine layers, so these poses contain Bloom only.
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
    _line(c,[shoulder,elbow,hand],1,5)
    _line(c,[shoulder,elbow,hand],3,3)
    _line(c,[shoulder,(elbow[0],elbow[1]-1),hand],5,2)
    _line(c,[(shoulder[0]-1,shoulder[1]-1),(elbow[0]-1,elbow[1]-1)],10)
    hx,hy = hand
    c.rect(hx-1,hy-1,hx+1,hy+1,1)
    c.rect(hx-1,hy-1,hx,hy,15)
    c.set(hx+1,hy,14)


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
        _arm(c,(27,17),(25,19),(24,22))
        _arm(c,(37,17),(hand[0],19),hand)
    elif facing == 's':
        _arm(c,(27,18),(24,20),(23,22))
        _arm(c,(37,18),(hand[0],22),hand)
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
    return _finish(c)


def _guard(idle, facing):
    c = _base(idle,facing,0,1)
    if facing == 'n':
        _arm(c,(27,18),(25,16),(27,13))
        _arm(c,(37,18),(39,16),(37,13))
    elif facing == 's':
        _arm(c,(27,19),(28,22),(31,23))
        _arm(c,(37,19),(36,22),(33,23))
    else:
        _arm(c,(29,19),(32,22),(36,22))
        _arm(c,(36,18),(40,20),(41,22))
    return _finish(c)


def _carry(idle, facing, step):
    c = _base(idle,facing,0,1 if step else 0)
    if facing == 'n':
        _arm(c,(27,17),(25,19),(26,18))
        _arm(c,(37,17),(40,19),(39,18))
    elif facing == 's':
        _arm(c,(27,18),(29,21),(34,19))
        _arm(c,(37,18),(42,20),(43,17))
    else:
        _arm(c,(29,18),(32,21),(37,20))
        _arm(c,(36,18),(42,21),(44,17))
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
    frames['itemget'] = _itemget(idle)
    for name,rows in frames.items():
        assert len(rows) == 32 and all(len(row) == 64 for row in rows),name
