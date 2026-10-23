"""Record what one enemy kind does, frame by frame, in the real ROM.

AI timing (how often an Octorok spits, how long a Darknut winds up, how
fast a Keese dives) lives in code, not tables. A new engine matches it by
copying the AI's logic from src/enemy/<name>.c AND checking the result
against this trace: position, speed, action, timer and animation per frame,
plus every projectile the kind fires (kind 4 entities whose parent is
one of them), so fire intervals come out measured.

Spawns through the QUICKSTART measurement mailbox into South Hyrule Field
with the region's wave cleared and the player held still with full health.

    python3 tools/newgame/feel_trace.py ID [FORM] [--frames N] [--csv OUT] [--at DX,DY]

--at spawns the enemy at that offset from the player (room pixels).
    python3 tools/newgame/feel_trace.py 0            # Octorok: fire interval
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'quickstart'))
import measure_budget as M
from emu import warp, qs_set, GENT, STRIDE, MAX_ENT, PLAYER, r16
from seed import boot_pinned
from chain_audit import dismiss


def u32(c, a):
    m = c.memory.u8
    return m[a] | m[a + 1] << 8 | m[a + 2] << 16 | m[a + 3] << 24


def main():
    args = sys.argv[1:]
    frames = int(args[args.index('--frames') + 1]) if '--frames' in args else 1800
    out = args[args.index('--csv') + 1] if '--csv' in args else None
    pos = [a for a in args if not a.startswith('--') and (args.index(a) == 0 or not args[args.index(a) - 1].startswith('--'))]
    eid = int(pos[0], 0)
    form = int(pos[1], 0) if len(pos) > 1 else 0
    r = M.regions['HYRULE_FIELD_SOUTH_HYRULE_FIELD']
    c = boot_pinned(os.path.join(HERE, '..', '..', 'tmc.gba'), 0x42)
    for b in range(4):
        qs_set(c, M.DIFF0 + b, 0)
    warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1], 400)
    M.kill_everything(c)
    dismiss(c)
    before = set(GENT + i * STRIDE for i in range(MAX_ENT) if c.memory.u8[GENT + i * STRIDE + 8] == 3)
    at = [int(v) for v in args[args.index('--at') + 1].split(',')] if '--at' in args else [0, 0]
    px = r16(c, PLAYER + 0x2e) - r16(c, 0x03000bf0 + 6)
    py = r16(c, PLAYER + 0x32) - r16(c, 0x03000bf0 + 8)
    M.mailbox_spawn(c, eid, form, 1, px + at[0], py + at[1])
    # the traced entity: the new enemy of this id, pinned by address
    b = next((GENT + i * STRIDE for i in range(MAX_ENT) if c.memory.u8[GENT + i * STRIDE + 8] == 3
              and c.memory.u8[GENT + i * STRIDE + 9] == eid and GENT + i * STRIDE not in before), None)
    if b is None:
        raise SystemExit('the mailbox spawned nothing')
    rows, shots, seen = [], [], set()
    m = c.memory
    for f in range(frames):
        m.u8[M.HEALTH] = 0x20
        if f % 60 == 0 and m.u8[0x02000050] != 0:
            dismiss(c, 120)
        # the region's endless wave refills the room: keep it empty
        for i in range(MAX_ENT):
            e = GENT + i * STRIDE
            if e != b and m.u8[e + 8] == 3:
                m.u8[e + 0x45] = 0
        c.run_frame()
        if m.u8[b + 8] != 3 or m.u8[b + 9] != eid:
            print('  the traced enemy is gone at frame %d' % f)
            break
        rows.append((f, r16(c, b + 0x2e), r16(c, b + 0x32), r16(c, b + 0x36), r16(c, b + 0x24), m.u8[b + 0x15],
                     m.u8[b + 0x0c], m.u8[b + 0x0d], m.u8[b + 0x0e], m.u8[b + 0x58], m.u8[b + 0x5a]))
        for i in range(MAX_ENT):
            p = GENT + i * STRIDE
            if m.u8[p + 8] == 4 and p not in seen:
                seen.add(p)
                # parent is the shooter for EnemyCreateProjectile; the
                # room is otherwise empty, so any new projectile counts
                shots.append((f, m.u8[p + 9], r16(c, p + 0x24), u32(c, p + 0x50) == b))
            elif m.u8[p + 8] != 4:
                seen.discard(p)
    if out:
        with open(out, 'w') as fh:
            fh.write('frame,x,y,z,speed_q8_8,direction,action,subAction,timer,animIndex,frameFlags\n')
            for row in rows:
                fh.write(','.join(map(str, row)) + '\n')
    print('enemy 0x%02x form %d: traced %d frames' % (eid, form, len(rows)))
    speeds = sorted(set(r[4] for r in rows))
    print('  speeds seen (Q8.8):', speeds[:12])
    print('  actions seen:', sorted(set(r[6] for r in rows)))
    print('  projectiles: %d' % len(shots), shots[:8])
    if len(shots) > 1:
        gaps = [b[0] - a[0] for a, b in zip(shots, shots[1:])]
        print('  frames between shots: min %d median %d max %d' % (min(gaps), sorted(gaps)[len(gaps) // 2], max(gaps)))


if __name__ == '__main__':
    main()
