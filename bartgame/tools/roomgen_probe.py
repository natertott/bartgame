"""Check generated room geometry inside the real GBA ROM in mGBA.

    python tools/roomgen_probe.py --seeds 0xB4A7,0xDEADBEEF,1,7,42 --out report.json

Debug room navigation selects the seed's actual rooms. The validator reads
collision quarters and metatile contracts from the loaded ROM, not art Python.
Required targets must be reachable with sword/basic lifting, before any future
progression item. Optional treasure pockets are measured separately.
"""
import argparse
from collections import deque
import json
from pathlib import Path
import re

import probe as P
import critical_path as CP

DIRECTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))
ROOM_SPOTS = {'chest': (25, 48), 'npc': (27, 49), 'relic': (29, 50),
              'boss': (40, 51), 'shrine': (42, 52), 'treasure': (44, 53), 'mouth': (46, 54)}


def definitions():
    h = Path(P.ROOT, 'build/gen/assets.h').read_text()
    return {name: int(value) for name, value in re.findall(r'^#define ((?:MT|TT)_\w+) (\d+)\s*$', h, re.M)}


class Layout:
    def __init__(self, c, defs):
        self.defs = defs
        room = P.sym('gRoom')
        self.w, self.h = P.r8(c, room), P.r8(c, room+1)
        typ, coll = P.sym('metatile_type'), P.sym('metatile_coll')
        self.types, self.masks, self.tiles, self.overlay = {}, {}, {}, {}
        for y in range(self.h):
            for x in range(self.w):
                g = P.r16(c, room+2+(y*32+x)*2) & 65535
                o = P.r16(c, room+2050+(y*32+x)*2) & 65535
                t = P.r8(c, typ+g)
                mask = P.r8(c, coll+g)
                if o != 65535 and P.r8(c, typ+o) != defs['TT_FLOOR']:
                    mask |= P.r8(c, coll+o)
                self.tiles[x, y], self.overlay[x, y] = g, o
                self.types[x, y], self.masks[x, y] = t, mask

    def blocked(self, qx, qy, items=0):
        x, y = qx//2, qy//2
        if not (0 <= x < self.w and 0 <= y < self.h):
            return True
        t, mask = self.types[x,y], self.masks[x,y]
        d = self.defs
        # Sword and basic lifting are available from the beginning. These
        # objects may be cleared without granting any future progression item.
        if t in (d['TT_THORN'], d['TT_LIFT1']):
            return False
        if (items & 1 and t == d['TT_CRACK']) or (items & 2 and t == d['TT_WEB']):
            return False
        if items & 4 and t == d['TT_PIT']:
            return False
        if t in (d['TT_PIT'], d['TT_WATER']):
            return True
        quarter = (qy%2)*2 + qx%2
        return bool(mask & (8 >> quarter))

    def flood(self, tile, items=0):
        # Stand on the centre's bottom-left quarter, as the player's feet do.
        starts = [(tile[0]*2+dx, tile[1]*2+dy) for dx,dy in ((0,1),(1,1),(0,0),(1,0))]
        starts = [q for q in starts if not self.blocked(*q, items)]
        if not starts:
            return set()
        seen, todo = set(starts), deque(starts)
        while todo:
            x,y = todo.popleft()
            for dx,dy in DIRECTIONS:
                q=(x+dx,y+dy)
                if q not in seen and not self.blocked(*q, items):
                    seen.add(q)
                    todo.append(q)
        return seen

    @staticmethod
    def reaches(seen, tile):
        return any((tile[0]*2+dx,tile[1]*2+dy) in seen for dx,dy in ((0,0),(1,0),(0,1),(1,1)))

    def bridges(self, seen):
        errors, count = [], 0
        for name, axis in (('MT_BRIDGE',(1,0)),('MT_BRIDGE_V',(0,1))):
            todo = {p for p,t in self.tiles.items() if t == self.defs[name]}
            while todo:
                origin=next(iter(todo)); line={origin}; todo.remove(origin)
                for sign in (-1,1):
                    p=origin
                    while True:
                        q=(p[0]+sign*axis[0],p[1]+sign*axis[1])
                        if q not in todo: break
                        line.add(q);todo.remove(q);p=q
                count += 1
                ordered=sorted(line,key=lambda p:p[0]*axis[0]+p[1]*axis[1])
                ends=((ordered[0][0]-axis[0],ordered[0][1]-axis[1]),
                      (ordered[-1][0]+axis[0],ordered[-1][1]+axis[1]))
                if not all(self.reaches(seen,p) and not self.blocked(p[0]*2,p[1]*2) for p in ends):
                    errors.append('%s crossing %s has no traversable destination at both ends %s' % (name,ordered,ends))
        return count, errors


_statics = None


def warp(c, cell, side):
    global _statics
    if _statics is None:
        lines=Path(P.MAP).read_text().splitlines()
        _statics={}
        for i,line in enumerate(lines):
            parts=line.split()
            if parts and parts[0].startswith('.bss.'):
                raw=parts[1] if len(parts)>1 and parts[1].startswith('0x') else lines[i+1].split()[0]
                _statics[parts[0][5:]]=int(raw,16)
    for name,val in (('sNextArea',1),('sNextCell',cell),('sNextSide',side),('sTransPhase',0)):
        P.w8(c,_statics[name],val)
    P.w8(c,P.sym('gGame'),2)
    P.run(c,70)


def landing(side):
    return ((15,2),(30,11),(15,22),(1,11))[side]


def inspect(c, cell, desc, defs):
    layout = Layout(c,defs)
    sides=[i for i,g in enumerate(desc['gate']) if g]
    seen=layout.flood(landing(sides[0]))
    errors=[]
    for side in sides:
        if not layout.reaches(seen,landing(side)):
            errors.append('door %d inner landing unreachable' % side)
    g=P.sym('gSpots')
    required=[]
    for name,(off,flag) in ROOM_SPOTS.items():
        if name=='treasure' or not P.r8(c,g+flag): continue
        x,y=P.r8(c,g+off),P.r8(c,g+off+1)
        if name in ('chest','npc','mouth','shrine'):y+=1
        required.append((name,(x,y)))
    for i in range(P.r8(c,g+39)):
        required.append(('torch %d'%i,(P.r8(c,g+31+i*2),P.r8(c,g+32+i*2)+1)))
    for name,spot in required:
        if not layout.reaches(seen,spot): errors.append('%s approach %s unreachable before future items' % (name,spot))
    for i in range(P.r8(c,g+24)):
        spot=(P.r8(c,g+i*2),P.r8(c,g+i*2+1))
        if not layout.reaches(seen,spot):errors.append('enemy spawn %s unreachable'%str(spot))
    # Every guaranteed key event must have a mouth, not a free field chest.
    if desc['role']==3 and not P.r8(c,g+54): errors.append('mandatory task has no mystery mouth')
    crossings,bridge_errors=layout.bridges(seen)
    errors += bridge_errors
    pocket=None
    if P.r8(c,g+53):
        spot=(P.r8(c,g+44),P.r8(c,g+45))
        pocket={'spot':spot,'accessible_without_items':layout.reaches(seen,spot),
                'accessible_with_all_items':layout.reaches(layout.flood(landing(sides[0]),7),spot)}
        # Legacy hoards behind liftable boulders remain optional and need the
        # gauntlet rather than one of the three route keys, so only pocket
        # kind metadata (when provided by the generator) makes this required.
    return {'cell':cell,'stage':desc['stage'],'role':desc['role'],
            'reachable_quarters':len(seen),'bridge_crossings':crossings,
            'optional_treasure':pocket,'failures':errors}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seeds',default='0xB4A7,0xDEADBEEF,1,7,42')
    ap.add_argument('--out')
    args=ap.parse_args()
    defs=definitions(); records=[]
    for seed in (int(n,0) for n in args.seeds.split(',')):
        c=P.boot(seed=seed); CP.dismiss(c); world=CP.world(c); P.enter_forest(c)
        for cell,desc in enumerate(world['cells']):
            side=next(i for i,g in enumerate(desc['gate']) if g)
            CP.heal(c);warp(c,cell,side);CP.clear_enemies(c)
            record=inspect(c,cell,desc,defs);record['seed']=hex(seed);records.append(record)
            print('%s seed=%s cell=%02d stage=%d bridges=%d %s'%('FAIL' if record['failures'] else 'PASS',hex(seed),cell,desc['stage'],record['bridge_crossings'],'; '.join(record['failures'])),flush=True)
        # Release cores between seeds (mGBA's binding retains allocations).
        del c
    failed=sum(bool(r['failures']) for r in records)
    report={'checked_rooms':len(records),'failed_rooms':failed,'rooms':records}
    if args.out:Path(args.out).write_text(json.dumps(report,indent=2))
    print('RESULT %s %d/%d rooms'%('FAIL' if failed else 'PASS',len(records)-failed,len(records)))
    return int(bool(failed))


if __name__=='__main__':raise SystemExit(main())
