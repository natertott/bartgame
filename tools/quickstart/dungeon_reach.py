"""The dungeon reach map (Oct 2026, the redesign's P3 section 7): what a
probe can see of every dungeon room before anyone walks it.

For each room of the dungeons and the castle (the AREAS list below) this
reads the room's real exit list out of transitions.c, finds every point a
transition ARRIVES at in that room (the far side of every exit row in the
whole file that targets it), warps in at each arrival, floods the live
collision grid from the tile the player actually stands on, and records:

  - which of the room's exits that arrival reaches on foot (a door's
    trigger tile or a border's edge in the flood), and where each leads;
  - every small-key door (LOCKED_DOOR) and boss door (BOSS_DOOR) standing
    in the room, and whether the arrival's flood touches it - a door the
    flood touches is the one a key would open from this side.

What it cannot see is what a door's far side wants beyond a key: a switch,
a block push, a clone puzzle. Those are the user's walk, room by room, as
the overworld's were; this is the half a probe can do, and it says which
rooms are open floor and which are split, so the walk can start at the
splits.

Warps are free (scenario_d 0x51, QuickStartProbeWarpsFree). A room that
will not hold the player (a cutscene room, a falling room) is reported as
not landed rather than guessed at.

    python3 tools/quickstart/dungeon_reach.py [--rom tmc-d3.gba] [--areas AREA_X,AREA_Y]
        [--json docs/dungeon_reach.json] [--md docs/QUICKSTART_DUNGEON_REACH.md]
"""
import os, re, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, here, coll_at, room_dims, entities, press, poison_here, r16, PLAYER, ROOM_CONTROLS, KIND_OBJECT
import scenario as S
import parse_tables as P

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
AREAS = (args[args.index('--areas') + 1].split(',') if '--areas' in args else
         ['AREA_DEEPWOOD_SHRINE', 'AREA_DEEPWOOD_SHRINE_BOSS', 'AREA_DEEPWOOD_SHRINE_ENTRY',
          'AREA_CAVE_OF_FLAMES', 'AREA_CAVE_OF_FLAMES_BOSS',
          'AREA_FORTRESS_OF_WINDS', 'AREA_FORTRESS_OF_WINDS_TOP',
          'AREA_TEMPLE_OF_DROPLETS', 'AREA_ROYAL_CRYPT',
          'AREA_PALACE_OF_WINDS', 'AREA_PALACE_OF_WINDS_BOSS',
          'AREA_HYRULE_CASTLE', 'AREA_DARK_HYRULE_CASTLE', 'AREA_DARK_HYRULE_CASTLE_OUTSIDE'])
JSON_OUT = args[args.index('--json') + 1] if '--json' in args else os.path.join(P.ROOT, 'docs/dungeon_reach.json')
MD_OUT = args[args.index('--md') + 1] if '--md' in args else os.path.join(P.ROOT, 'docs/QUICKSTART_DUNGEON_REACH.md')
SRC = os.path.join(P.ROOT, 'src/data/transitions.c')
SAVE = 0x02002a40
MSG = 0x02000050
OBJ = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())
DOORS = {OBJ['LOCKED_DOOR']: 'KEY', OBJ['BOSS_DOOR']: 'BOSS_KEY'}
ROOM_NAMES = {}
for k, v in P.ROOMS.items():
    ROOM_NAMES.setdefault(v, []).append(k)


def parse_transitions():
    """{list name: [row]}, and {area name: {room name: list name}}."""
    txt = open(SRC).read()
    lists = {}
    for m in re.finditer(r'const Transition (\w+)\[\] = \{(.*?)\n\};', txt, re.S):
        rows = []
        for row in re.findall(r'\{([^{}]*)\}', ' '.join(m.group(2).split())):
            f = [x.strip() for x in row.split(',')]
            if len(f) < 8 or not f[0].startswith('WARP_TYPE'):
                continue
            rows.append(dict(type=f[0], sx=int(f[1], 0), sy=int(f[2], 0), ex=int(f[3], 0), ey=int(f[4], 0),
                             shape=f[5], area=f[6], room=f[7]))
        lists[m.group(1)] = rows
    tables = {}
    for m in re.finditer(r'const Transition\* const (\w+)\[\] = \{(.*?)\n\};', txt, re.S):
        tables[m.group(1)] = dict(re.findall(r'\[(ROOM_\w+)\]\s*=\s*(\w+)', m.group(2)))
    area_table = dict(re.findall(r'/\*(AREA_\w+)\*/\s*(\w+),', txt))
    rooms = {a: tables.get(t, {}) for a, t in area_table.items()}
    return lists, rooms


def flood(c, start, tw, th):
    seen, stack = {start}, [start]
    while stack:
        q = stack.pop()
        for nb in ((q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)):
            if nb in seen or not (0 <= nb[0] < tw and 0 <= nb[1] < th) or coll_at(c, nb[0], nb[1]) != 0:
                continue
            seen.add(nb); stack.append(nb)
    return seen


def dismiss(c, limit=300):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            c.run_frame(); quiet += 1
            if quiet >= 20:
                return
            continue
        press(c, c.KEY_A, 3, 10); quiet = 0


def touches(seen, t, r=1):
    return any((t[0] + ox, t[1] + oy) in seen for ox in range(-r, r + 1) for oy in range(-r, r + 1))


def exit_reached(row, seen, tw, th):
    if row['type'] == 'WARP_TYPE_BORDER':
        shape = row['shape']
        if 'NORTH' in shape:
            return any(t[1] == 0 for t in seen) or any(t[1] <= 1 for t in seen)
        if 'SOUTH' in shape:
            return any(t[1] >= th - 2 for t in seen)
        if 'WEST' in shape:
            return any(t[0] <= 1 for t in seen)
        if 'EAST' in shape:
            return any(t[0] >= tw - 2 for t in seen)
        return False
    return touches(seen, (row['sx'] // 16, row['sy'] // 16))


def components(c, tw, th):
    comp, out = {}, []
    for ty in range(th):
        for tx in range(tw):
            if coll_at(c, tx, ty) != 0 or (tx, ty) in comp:
                continue
            seen = flood(c, (tx, ty), tw, th)
            for t in seen:
                comp[t] = len(out)
            out.append(seen)
    return comp, out


def land(c, an, rn, pts):
    """Warp in at a real arrival if the file has one, else at the middle
    and then onto the nearest open tile. Returns the live core or None."""
    tries = [p for p in pts[:2]] or [(0x78, 0x78)]
    for ax, ay in tries:
        poison_here(c)
        warp(c, P.AREAS[an], P.ROOMS[rn], ax, ay, frames=150)
        dismiss(c)
        if here(c) == (P.AREAS[an], P.ROOMS[rn]):
            return (ax, ay)
    return None


def main():
    lists, rooms = parse_transitions()
    arrivals = collections.defaultdict(set)
    for name, rows in lists.items():
        for row in rows:
            arrivals[(row['area'], row['room'])].add((row['ex'], row['ey']))
    c = S.boot(ROM, 0, frames=300)
    c.memory.u8[SAVE + 0x3C] = 0x51
    out = []
    for an in AREAS:
        for rn, listname in sorted(rooms.get(an, {}).items()):
            if re.search(r'_[0-9a-f]{1,2}$', rn) and not arrivals.get((an, rn)):
                # an unnamed slot (ROOM_..._c): a placeholder id with no room
                # behind it and nothing arriving - skipped, not landed in
                out.append(dict(area=an, room=rn, exits=[], arrival_points=[], landed=False,
                                note='an unnamed room slot, skipped'))
                continue
            rows = lists.get(listname, [])
            pts = sorted(arrivals.get((an, rn), set()))
            rec = dict(area=an, room=rn, exits=[dict(type=r['type'][10:], to=r['area'][5:] + '/' + r['room'][5:]) for r in rows],
                       arrival_points=[list(p) for p in pts], landed=False)
            at = land(c, an, rn, pts)
            if at is None:
                rec['note'] = 'did not land (got %s)' % (here(c),)
                if c.memory.u8[SAVE + 0xA8 + 2] == 0:
                    c = S.boot(ROM, 0, frames=300); c.memory.u8[SAVE + 0x3C] = 0x51
                elif here(c)[1] == 0xff:
                    # a failed landing leaves the poisoned room byte; a warp
                    # to the hub recovers faster than a reboot
                    warp(c, P.AREAS['AREA_WIND_TRIBE_TOWER'], 3, 120, 120, frames=120)
                out.append(rec)
                print('%-34s %-44s did not land' % (an, rn), flush=True)
                continue
            w, h = room_dims(c)
            tw, th = w // 16, h // 16
            if tw == 0 or th == 0:
                rec['note'] = 'an unused room id (no header)'
                out.append(rec)
                continue
            rec['landed'] = True
            ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
            comp, comps = components(c, tw, th)
            doors = []
            for e in entities(c, KIND_OBJECT):
                if e[2] in DOORS:
                    doors.append(dict(kind=DOORS[e[2]], at=[e[4] - ox, e[5] - oy],
                                      tile=[(e[4] - ox) // 16, (e[5] - oy) // 16]))
            big = []
            for i, seen in enumerate(comps):
                if len(seen) < 6:      # a lone tile behind a pillar is not a part of the room
                    continue
                edges = ''.join(k for k, f in (('N', lambda t: t[1] <= 1), ('S', lambda t: t[1] >= th - 2),
                                               ('W', lambda t: t[0] <= 1), ('E', lambda t: t[0] >= tw - 2))
                                if any(f(t) for t in seen))
                ex = [j for j, r in enumerate(rows) if exit_reached(r, seen, tw, th)]
                dr = [d['kind'] for d in doors if touches(seen, tuple(d['tile']), 2)]
                arr = [p for p in pts if (p[0] // 16, p[1] // 16) in seen or touches(seen, (p[0] // 16, p[1] // 16), 1)]
                big.append(dict(size=len(seen), edges=edges, exits=ex, doors=dr, arrivals=[list(p) for p in arr]))
            big.sort(key=lambda d: -d['size'])
            rec.update(size=[tw, th], open=sum(len(s) for s in comps), parts=big, doors=doors)
            out.append(rec)
            print('%-34s %-44s %2dx%-2d parts %s doors %s' % (an, rn, tw, th,
                  [(p['size'], p['edges'], len(p['exits'])) for p in big][:5], [d['kind'] for d in doors]), flush=True)
    json.dump(out, open(JSON_OUT, 'w'), indent=1)
    write_md(out)


def write_md(out):
    lines = ['# The dungeon reach map (probe-made)', '',
             'Generated by `tools/quickstart/dungeon_reach.py` (Oct 2026, the redesign\'s P3 section 7). Every room of the',
             'dungeons and the castle, landed in and flooded: its open floor split into the PARTS a player can walk',
             'between without a door, a key or a puzzle (parts under six tiles are left out), and for each part the room',
             'edges it reaches (N/S/E/W - dungeon rooms join by scrolling at their edges), the transitions.c exits it',
             'reaches, the small-key (KEY) and boss (BOSS_KEY) doors it touches, and the arrival points that land in it.',
             'One part is an open room; two or more is a room the walk has to explain: what joins them (a key door, a',
             'switch, a block, a clone puzzle) is what this probe cannot see.', '']
    by_area = collections.OrderedDict()
    for r in out:
        by_area.setdefault(r['area'], []).append(r)
    total = landed = split = 0
    for an, rs in by_area.items():
        lines += ['## %s' % an[5:], '', '| room | tiles | parts (size, edges, exits, doors) |', '|---|---|---|']
        for r in rs:
            total += 1
            if not r['landed']:
                lines.append('| %s | - | %s |' % (r['room'][5:], r.get('note', 'did not land')))
                continue
            landed += 1
            split += 1 if len(r['parts']) > 1 else 0
            parts = '; '.join('%d %s%s%s' % (p['size'], p['edges'] or '-',
                                             (' exits ' + ','.join(r['exits'][j]['to'].split('/')[-1] for j in p['exits'])) if p['exits'] else '',
                                             (' ' + '+'.join(p['doors'])) if p['doors'] else '') for p in r['parts'])
            lines.append('| %s | %dx%d | %s |' % (r['room'][5:], r['size'][0], r['size'][1], parts or 'no floor'))
        lines.append('')
    lines[10:10] = ['**%d rooms; %d landed; %d of those split into two or more parts.**' % (total, landed, split), '']
    open(MD_OUT, 'w').write('\n'.join(lines) + '\n')
    print('wrote %s and %s: %d rooms, %d landed, %d split' % (JSON_OUT, MD_OUT, total, landed, split))


if __name__ == '__main__':
    main()
