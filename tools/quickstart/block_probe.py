"""Play the block puzzles in the ROM, one push at a time.

block_puzzles.py builds a pool per room - frames (where a puzzle sits) and
up to 32 contents each - solves every content offline and writes the push
lists to build/block_solutions.json, in table order. This boots a puzzle
through the testbed - scenario SITE (kind BLOCKS, the frame in extra bits
5-7, the content in 0-4) for a ? room, scenario QUEST BLOCKS (frame + 1 in
scenario_c, content + 1 in scenario_d) for a pool row - and plays the list
in the emulator:

  * the dealt rocks must match the table: every mover and every fixed rock
    on its tile, with its class;
  * each push: the player is set down on the far side of the rock (the
    solver proved the walk there; this checks the push, not the walk),
    holds the direction, and the rock must land one tile on;
  * after the last push the room's SOLVED flag must be set (the ROM's own
    match or maze flood, not ours);
  * then the prize: a template's appears on its tile and is picked up, a
    maze's chest is opened from the target tile, a door maze counts once
    the player stands on the target. The ? room site's DONE bit (or the
    quest's WON state) must follow.

It plays `--contents` per frame (the first and a seeded draw; 0 for all):
`block_puzzles.py --verify` replays every content's solution offline, and
this confirms in the ROM that the table decodes and plays the same way.

With --rules it also checks, on every instance where each applies, that a
fixed rock, an axis-bound rock pushed across its axis and a push off the
board are all refused, and that striking the reset switch puts every rock
back.

    python3 tools/quickstart/block_probe.py [--rom tmc-d3.gba] [--only FRAME,...] [--contents N] [--rules] [--snap DIR]
"""
import argparse
import collections
import json
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import r16, w16, here, press, entities, room_dims, PLAYER, ROOM_CONTROLS, GENT, STRIDE, KIND_OBJECT
import scenario as S
import parse_tables as P

SOLUTIONS = os.path.join(P.ROOT, 'build', 'block_solutions.json')
ROOMFLAGS = 0x02034364   # gRoomVars.flags; QS room flag k = bit 256 + k
MSG = 0x02000050
ROCK_TYPE = 0xB7
SITE_FLAG_BASE = 64      # a lone site's room-flag window
QUEST_FLAG_BASE = 120
SOLVED, PAID, FREE, GROUND = 1, 2, 3, 4
GF_BLOCKQ_STATE = 692
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)
OBJ = P._enum(open(os.path.join(P.ROOT, 'include', 'object.h')).read())
ROCK = OBJ['PUSHABLE_ROCK']


def room_flag(c, k):
    b = 256 + k
    return (c.memory.u8[ROOMFLAGS + (b >> 3)] >> (b & 7)) & 1


def bank12(c, n):
    b = emu.FLAG_BANK_12 + n
    return (c.memory.u8[emu.SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1


def origin(c):
    return r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)


def frame(c):
    # Health pinned and hits ignored (entity +0x3d, invulnerability
    # frames): a field puzzle shares its room with the region's waves, and
    # a knockback mid-push is not what this probe measures.
    c.memory.u8[PLAYER + 0x45] = 24
    c.memory.u8[PLAYER + 0x3d] = 30
    c.run_frame()


def run(c, n):
    for _ in range(n):
        frame(c)


def dismiss(c, limit=900):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            frame(c)
            quiet += 1
            if quiet >= 40:
                return
            continue
        press(c, c.KEY_A, 3, 17)
        quiet = 0


def rocks(c):
    """{(tx, ty): class} for our rocks, at rest or not (tile of the centre)."""
    ox, oy = origin(c)
    out = {}
    for i, k, ident, typ, x, y in entities(c, KIND_OBJECT, ROCK):
        if typ != ROCK_TYPE:
            continue
        out[((x - ox) // 16, (y - oy) // 16)] = c.memory.u8[GENT + i * STRIDE + 0x0b] & 3
    return out


def put_player(c, tx, ty):
    ox, oy = origin(c)
    w16(c, PLAYER + 0x2e, ox + tx * 16 + 8)
    w16(c, PLAYER + 0x32, oy + ty * 16 + 8)
    run(c, 4)


KEY = None


def settle(c, frames=240):
    """Run out the delayed Ezlo lines (a region's intro hint comes a few
    seconds after landing and freezes the player while it shows)."""
    for _ in range(frames):
        if c.memory.u8[MSG]:
            dismiss(c)
        frame(c)


def push(c, x, y, d):
    """Stand behind the rock at (x, y) and push it towards d, up to three
    tries (a line or a hit can steal the first). True if it moved."""
    for _ in range(3):
        if push_once(c, x, y, d):
            return True
        settle(c, 60)
    return False


def push_once(c, x, y, d):
    sx, sy = x - DX[d], y - DY[d]
    if c.memory.u8[MSG]:
        dismiss(c)   # an Ezlo line arriving mid-solve (a region's intro) freezes the player
    put_player(c, sx, sy)
    ox, oy = origin(c)
    key = KEY[d]
    c.set_keys(key)
    moved = False
    for _ in range(150):
        # Pinned to the tile's centre line across the push until the push
        # starts: in a one-tile corridor the game's corner slide would
        # otherwise walk the player off the line before the push builds up.
        # (Pinning both axes stops the push from building at all.)
        if d & 1:
            w16(c, PLAYER + 0x32, oy + sy * 16 + 8)
        else:
            w16(c, PLAYER + 0x2e, ox + sx * 16 + 8)
        frame(c)
        if (x, y) not in rocks(c):
            moved = True
            break
    c.clear_keys(key)
    run(c, 40 if moved else 10)
    return moved


def instance(frame, k):
    """Content k of a frame, as one puzzle: every rock it deals and the
    solver's pushes."""
    c = frame['contents'][k]
    bx, by = frame['board'][:2]
    fixed = [tuple(x) for x in frame['fixed']]
    if frame['kind'] == 0:
        rx, ry = frame['ref']
        fixed += [(rx + x - bx, ry + y - by) for x, y in c['goal']]
    else:
        fixed += [tuple(x) for x in c['walls']]
    inst = dict(frame)
    inst.update(move=c['move'], fixed=fixed, solution=c['solution'], pushes=c['pushes'], content=k)
    return inst


def boot_instance(rom, inst, ordinal):
    """`ordinal`: the frame's place among its owner's frames. Content
    inst['content']. A ? room site takes both in extra (frame in bits 5-7,
    content in 0-4); the quest in scenario_c and scenario_d (each + 1)."""
    owner = inst['owner']
    k = inst.get('content', 0)
    if owner.startswith('site:'):
        site = int(owner[5:])
        c = S.boot(rom, S.KINDS['SITE'], site, S.EVENTS.index('BLOCKS'), (ordinal << 5) | k, 0, kit=2, frames=300)
        return c, SITE_FLAG_BASE, ('site', site)
    row = int(owner[4:])
    c = S.boot(rom, S.KINDS['QUEST'], S.QUESTS.index('BLOCKS'), row, ordinal + 1, k + 1, kit=2, frames=300)
    return c, QUEST_FLAG_BASE, ('row', row)


def done(c, who):
    if who[0] == 'site':
        return bank12(c, emu.SITE_ORIGIN + who[1])
    return bank12(c, GF_BLOCKQ_STATE) and bank12(c, GF_BLOCKQ_STATE + 1)


def land(rom, inst, ordinal):
    """Boot the instance and settle in its room: (c, flag base, owner,
    landed)."""
    c, base, who = boot_instance(rom, inst, ordinal)
    global KEY
    KEY = (c.KEY_UP, c.KEY_RIGHT, c.KEY_DOWN, c.KEY_LEFT)
    dismiss(c)
    run(c, 30)
    dismiss(c)
    area, room = P.AREAS[inst['area']], P.ROOMS[inst['room']]
    # The boot's title-screen START can land after a fast landing and open
    # the pause menu (seen in Minish Woods: the room reads origin 0 and
    # size 0 under it). Close it, then let the room settle.
    for _ in range(10):
        if room_dims(c)[0] and tuple(here(c)) == (area, room):
            break
        press(c, c.KEY_START, 3, 60)
    settle(c)
    return c, base, who, tuple(here(c)) == (area, room)


def probe(rom, idx, inst, ordinal, snapdir, rules):
    c, base, who, landed = land(rom, inst, ordinal)
    if not landed:
        return 'NOT LANDED %s' % (here(c),), None
    got = rocks(c)
    want = {(x, y): k for x, y, k in inst['move']}
    want.update({(x, y): 3 for x, y in inst['fixed']})
    free = room_flag(c, base + FREE)
    if free:
        want = {(x, y): 3 for x, y in inst['fixed']}
    if got != want:
        miss = sorted(set(want) - set(got))
        extra = sorted(set(got) - set(want))
        return 'DEALT WRONG missing %s extra %s' % (miss[:6], extra[:6]), c
    if snapdir:
        emu.snap(c, os.path.join(snapdir, 'block%05d_dealt.png' % idx))
    notes = []
    if rules:
        notes += rule_checks(c, inst, base)
        if notes and notes[0].startswith('FAIL'):
            return notes[0], c
    if not free:
        if not inst['solution']:
            return 'NO SOLUTION recorded', c
        for n, (x, y, d) in enumerate(inst['solution']):
            if not push(c, x, y, d):
                return 'PUSH %d of %d refused: rock (%d,%d) dir %d' % (n + 1, len(inst['solution']), x, y, d), c
            if (x + DX[d], y + DY[d]) not in rocks(c):
                return 'PUSH %d landed wrong: rocks %s' % (n + 1, sorted(rocks(c))), c
    run(c, 30)
    if not room_flag(c, base + SOLVED):
        return 'NOT SOLVED after %d pushes' % len(inst['solution']), c
    if snapdir:
        emu.snap(c, os.path.join(snapdir, 'block%05d_solved.png' % idx))
    px, py = inst['prize']
    if inst['kind'] == 0 or room_flag(c, base + GROUND):
        for _ in range(60):
            run(c, 2)
            if room_flag(c, base + PAID):
                break
        put_player(c, px, py)
        run(c, 20)
        dismiss(c)
    elif inst['door']:
        put_player(c, inst['target'][0], inst['target'][1])
        run(c, 10)
    else:
        tx, ty = inst['target']
        d = [k for k in range(4) if (tx + DX[k], ty + DY[k]) == (px, py)][0]
        put_player(c, tx, ty)
        c.set_keys(KEY[d]); run(c, 8); c.clear_keys(KEY[d])
        press(c, c.KEY_A, 3, 30)
        dismiss(c)
    run(c, 60)
    dismiss(c)
    if not done(c, who):
        return 'PRIZE: solved but not DONE', c
    return 'ok %d pushes%s' % (len(inst['solution']), (' ' + ' '.join(notes)) if notes else ''), c


EQUIPPED = 0x02002a40 + 0xb4   # gSave.stats.equipped: the A item, then the B item


def sword_key(c):
    """The button the sword is on. The test kit does not always put it on B
    (a Minish Woods boot had it on A, and B swung nothing at the switch)."""
    return c.KEY_A if 1 <= c.memory.u8[EQUIPPED] <= 6 else c.KEY_B


def rule_checks(c, inst, base):
    """Refusals and the reset switch, on this instance's starting layout."""
    out = []
    start = rocks(c)
    bx, by, bw, bh = inst['board']

    def free(t):
        # Open floor with no rock: a tile to stand on, or to push into
        # (otherwise a refusal proves nothing - vanilla refuses that too).
        return emu.coll_at(c, t[0], t[1]) == 0 and t not in start
    for (x, y), k in sorted(start.items()):
        if k == 3:
            for d in range(4):
                if free((x + DX[d], y + DY[d])) and free((x - DX[d], y - DY[d])):
                    if push(c, x, y, d):
                        return ['FAIL fixed rock (%d,%d) moved' % (x, y)]
                    out.append('fixed-refused')
                    break
            if out:
                break
    for (x, y), k in sorted(start.items()):
        if k in (1, 2):
            for d in ((0, 2) if k == 1 else (1, 3)):
                nx, ny = x + DX[d], y + DY[d]
                if bx <= nx < bx + bw and by <= ny < by + bh and free((nx, ny)) and free((x - DX[d], y - DY[d])):
                    if push(c, x, y, d):
                        return ['FAIL %s rock (%d,%d) moved dir %d' % ('horizontal' if k == 1 else 'vertical', x, y, d)]
                    out.append('axis-refused')
                    break
            if out and out[-1] == 'axis-refused':
                break
    for (x, y), k in sorted(start.items()):
        if k == 3:
            continue
        for d in range(4):
            nx, ny = x + DX[d], y + DY[d]
            if not (bx <= nx < bx + bw and by <= ny < by + bh) and free((nx, ny)) and \
                    free((x - DX[d], y - DY[d])):
                if push(c, x, y, d):
                    return ['FAIL rock (%d,%d) left the board dir %d' % (x, y, d)]
                out.append('edge-refused')
                break
        if out and out[-1] == 'edge-refused':
            break
    # Move one rock legally, then strike the switch: every rock goes home.
    x, y, d = inst['solution'][0] if inst['solution'] else (0, 0, 0)
    if inst['solution'] and push(c, x, y, d):
        sx, sy = inst['switch']
        # Up to three swings: in a field a wave can spoil one (South Hyrule
        # Field missed once in a run and struck clean when tried alone).
        for _ in range(3):
            for d2 in range(4):
                ax, ay = sx - DX[d2], sy - DY[d2]
                if emu.coll_at(c, ax, ay) == 0 and (ax, ay) not in rocks(c):
                    if c.memory.u8[MSG]:
                        dismiss(c)
                    put_player(c, ax, ay)
                    c.set_keys(KEY[d2]); run(c, 4); c.clear_keys(KEY[d2])
                    press(c, sword_key(c), 3, 40)
                    break
            run(c, 30)
            if rocks(c) == start:
                break
        if rocks(c) != start:
            return ['FAIL reset left rocks at %s' % sorted(set(rocks(c)) ^ set(start))]
        out.append('reset-ok')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    ap.add_argument('--only')
    ap.add_argument('--rules', action='store_true')
    ap.add_argument('--snap')
    ap.add_argument('--solutions', default=SOLUTIONS)
    ap.add_argument('--contents', type=int, default=2,
                    help='contents played per frame: the first, then a seeded draw (0 = all)')
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    frames = json.load(open(a.solutions))
    only = set(int(v) for v in a.only.split(',')) if a.only else None
    if a.snap:
        os.makedirs(a.snap, exist_ok=True)
    rng = random.Random(a.seed)
    seen = {}
    jobs = []
    for fi, f in enumerate(frames):
        ordinal = seen.get(f['owner'], 0)
        seen[f['owner']] = ordinal + 1
        n = len(f['contents'])
        ks = list(range(n)) if a.contents == 0 else [0] + rng.sample(range(1, n), min(n - 1, a.contents - 1))
        if only is None or fi in only:
            jobs += [(fi, k, ordinal) for k in ks]
    ok = bad = 0
    ruled = collections.Counter()
    for fi, k, ordinal in jobs:
        inst = instance(frames[fi], k)
        idx = fi * 100 + k
        verdict, c = probe(a.rom, idx, inst, ordinal, a.snap, a.rules)
        for note in ('fixed-refused', 'axis-refused', 'edge-refused', 'reset-ok'):
            ruled[note] += note in verdict
        good = verdict.startswith('ok')
        ok += good
        bad += not good
        print('%3d.%-2d %-8s %-44s %s%s  %s' % (fi, k, inst['owner'], inst['room'][5:],
                                               'TM'[inst['kind']] if not inst['door'] else 'D', inst['cls'], verdict),
              flush=True)
        if c is not None and not good and a.snap:
            emu.snap(c, os.path.join(a.snap, 'block%05d_fail.png' % idx))
        del c
    print('%d/%d puzzles solved in the ROM (%d frames, %s per frame)'
          % (ok, ok + bad, len({j[0] for j in jobs}), a.contents or 'every content'))
    if a.rules:
        print('rules held: ' + ', '.join('%s %d' % kv for kv in sorted(ruled.items())))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
