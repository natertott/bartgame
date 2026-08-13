"""Overworld budget probe: entity slots and GFX slots per region, per
difficulty - plus, since the F8 measurement pass, arbitrary staged
COMBOS (a boss with an escort roster) through the in-game measurement
mailbox (QuickStartMeasureMailbox, game.c).

Answers "how much room is left for new content" with measured numbers
rather than estimates. MAX_ENTITIES is 72 and MAX_GFX_SLOTS is 44, both
game-wide; the GFX table is the one that actually runs out (see
docs/QUICKSTART_QUEST_RESEARCH.md and docs/QUICKSTART_BUDGET.md). Run this
after any change to the enemy rosters, the density spawner, or anything
that adds a sprite to a region.

Usage:
  python3 tools/quickstart/measure_budget.py
      The classic sweep: every region row, difficulties 0/4/8/12, peak
      entity/GFX use over 900 frames of natural wave play.

  python3 tools/quickstart/measure_budget.py --combo SPEC [--diff N]
        [--region NAME] [--seed S] [--frames N] [--keep-wave]
      Stage SPEC on top of a cleared region and measure it. SPEC is
      id:form:count entries joined by '+', e.g.
        19:0:1            the green chuchu boss family
        19:4:1+41:0:6     the blue boss plus six ice wizzrobes
      The mailbox spawns raw CreateEnemy calls (no caps, no reserve
      gates), so the numbers show what the guards WOULD have to absorb.
      Default region HYRULE_FIELD_SOUTH_HYRULE_FIELD (region names are
      the room enum minus 'ROOM_'), diff 8, 600 frames. --keep-wave
      leaves the region's natural wave alive under the combo.
"""
import sys, gc, time
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import boot, warp, here, qs_set, GENT, STRIDE, MAX_ENT
import parse_tables as P

RC, GFX, MAX_GFX, DIFF0 = 0x03000bf0, 0x02024490, 44, 174
BOX, MAGIC = 0x0203FF00, 0x51534D42
HEALTH = 0x02002a40 + 0xA8 + 2
regions = {r['roomName'][5:]: r for r in P.region_pool()}  # strip 'ROOM_'


def gfx_used(c):
    return sum(1 for i in range(MAX_GFX)
               if (c.memory.u8[GFX + 4 + i * 12] & 0x0F) not in (0, 1, 2))


def counts(c):
    tot = enemies = 0
    types = set()
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        k = c.memory.u8[b + 8]
        if k == 0:
            continue
        tot += 1
        if k == 3:
            enemies += 1
            types.add((c.memory.u8[b + 9], c.memory.u8[b + 0xa]))
    return tot, enemies, len(types)


def live_of(c, eid, form=None):
    n = 0
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        if c.memory.u8[b + 8] == 3 and c.memory.u8[b + 9] == eid and c.memory.u8[b + 0x45] > 0:
            if form is None or c.memory.u8[b + 0xa] == form:
                n += 1
    return n


def mailbox_spawn(c, eid, form, count, x=0, y=0):
    c.memory.u32[BOX + 4] = eid | (form << 8) | (count << 16)
    c.memory.u32[BOX + 8] = x | (y << 16)
    c.memory.u32[BOX] = MAGIC
    for _ in range(10):
        c.run_frame()
        if c.memory.u32[BOX] == 0:
            return True
    return False


def kill_everything(c, frames=600):
    for f in range(frames):
        c.memory.u8[HEALTH] = 0x20
        alive = 0
        for i in range(MAX_ENT):
            b = GENT + i * STRIDE
            if c.memory.u8[b + 8] == 3:
                c.memory.u8[b + 0x45] = 0
                alive += 1
        if f % 12 < 3:
            c.set_keys(c.KEY_A)
        else:
            c.clear_keys(c.KEY_A)
        c.run_frame()
        if alive == 0:
            return True
    return False


def sweep():
    print(f'{"region":34s} {"diff":>4s} {"ents":>5s} {"enemies":>7s} {"types":>5s} {"gfx":>5s} {"gfxfree":>7s}')
    for name in regions:
        r = regions[name]
        for diff in (0, 4, 8, 12):
            gc.collect()
            c = boot()
            for b in range(4):
                qs_set(c, DIFF0 + b, (diff >> b) & 1)
            c.memory.u8[RC + 4] = 0
            warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1], 400)
            if here(c) != (r['area'], r['room']):
                print(f'{name} diff {diff}: no land')
                continue
            pe = pen = pty = pg = 0
            for _ in range(900):
                c.run_frame()
                t, e, ty = counts(c)
                pe, pen, pty = max(pe, t), max(pen, e), max(pty, ty)
                pg = max(pg, gfx_used(c))
            print(f'{name:34s} {diff:4d} {pe:5d} {pen:7d} {pty:5d} {pg:5d} {MAX_GFX-pg:7d}')
            del c


def combo(spec, region_name, diff, seed, frames, keep_wave):
    from seed import boot_pinned
    entries = []
    for part in spec.split('+'):
        bits = [int(x, 0) for x in part.split(':')]
        while len(bits) < 3:
            bits.append(1 if len(bits) == 2 else 0)
        entries.append(tuple(bits[:3]))
    r = regions[region_name]
    c = boot_pinned('tmc.gba', seed)
    for b in range(4):
        qs_set(c, DIFF0 + b, (diff >> b) & 1)
    warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1], 400)
    assert here(c) == (r['area'], r['room']), 'no land'
    if not keep_wave:
        kill_everything(c)
    base_ents, base_en, _ = counts(c)
    base_gfx = gfx_used(c)
    for eid, form, count in entries:
        ok = mailbox_spawn(c, eid, form, count)
        if not ok:
            print(f'  WARN: mailbox not serviced for {eid}:{form}:{count}')
    pe = pen = pg = 0
    min_free = MAX_GFX
    for f in range(frames):
        c.memory.u8[HEALTH] = 0x20
        c.run_frame()
        t, e, ty = counts(c)
        pe, pen = max(pe, t), max(pen, e)
        g = gfx_used(c)
        pg = max(pg, g)
        min_free = min(min_free, MAX_GFX - g)
    print(f'combo {spec} in {region_name} diff {diff} seed 0x{seed:x} '
          f'({frames} frames, wave {"kept" if keep_wave else "cleared"})')
    print(f'  baseline: ents {base_ents} enemies {base_en} gfx {base_gfx}')
    print(f'  peaks:    ents {pe} enemies {pen} gfx {pg}  min free gfx {min_free}')
    for eid, form, count in entries:
        print(f'  requested {eid}:{form} x{count} -> live now: {live_of(c, eid)} (all forms of id {eid})')


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--combo' in args:
        spec = args[args.index('--combo') + 1]
        def opt(name, default, cast):
            return cast(args[args.index(name) + 1]) if name in args else default
        combo(spec,
              opt('--region', 'HYRULE_FIELD_SOUTH_HYRULE_FIELD', str),
              opt('--diff', 8, int),
              opt('--seed', 0x42, lambda s: int(s, 0)),
              opt('--frames', 600, int),
              '--keep-wave' in args)
    else:
        sweep()
