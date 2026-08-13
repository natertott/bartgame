"""GFX slot lifetime tracer (F8, docs/QUICKSTART_BUDGET.md).

Samples the 44-entry gGFXSlots table every frame during a staged scenario
and reports what the summary numbers in measure_budget.py cannot show:
which sheets load WHEN, how long they live, how long a slot sits at
refCount 0 before it is actually freed (the reaper latency that makes the
spawn gates read stale counts), and how many frames the table spends with
zero free slots (the transient window where a quest sprite or reward
silently fails to load).

Slot layout (include/vram.h GfxSlot, 12 bytes each, array at
gGFXSlots+4 = 0x02024494): +0 status:4|vramStatus:4, +1 slotCount,
+2 referenceCount, +4 u16 gfxIndex. Status 0/1/2 count as free (matching
measure_budget.gfx_used and QuickStartFreeGfxSlots).

Usage:
  python3 tools/quickstart/gfx_trace.py [--region NAME] [--diff N]
      [--seed S] [--frames N] [--combo SPEC]

  SPEC as in measure_budget.py (id:form:count+...), staged through the
  measurement mailbox after the region's natural wave has spawned.
"""
import sys
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import warp, here, qs_set
from seed import boot_pinned
from measure_budget import regions, mailbox_spawn, HEALTH, MAX_GFX

GFX = 0x02024490
DIFF0 = 174


def snapshot(c):
    out = []
    for i in range(MAX_GFX):
        b = GFX + 4 + i * 12
        st = c.memory.u8[b] & 0x0F
        ref = c.memory.u8[b + 2]
        gi = c.memory.u8[b + 4] | (c.memory.u8[b + 5] << 8)
        out.append((st, ref, gi))
    return out


def run(region_name, diff, seed, frames, spec):
    r = regions[region_name]
    c = boot_pinned('tmc.gba', seed)
    for b in range(4):
        qs_set(c, DIFF0 + b, (diff >> b) & 1)
    warp(c, r['area'], r['room'], r['entrance'][0], r['entrance'][1], 400)
    assert here(c) == (r['area'], r['room']), 'no land'
    if spec:
        for part in spec.split('+'):
            bits = [int(x, 0) for x in part.split(':')]
            while len(bits) < 3:
                bits.append(1 if len(bits) == 2 else 0)
            mailbox_spawn(c, bits[0], bits[1], bits[2])

    prev = snapshot(c)
    born = {}          # slot -> (frame, gfxIndex)
    ref0_since = {}    # slot -> frame refCount hit 0 while occupied
    lifetimes = []     # (gfxIndex, frames alive)
    reap_lat = []      # frames from refCount-0 to freed
    loads = 0
    zero_free_frames = 0
    min_free = MAX_GFX

    for f in range(frames):
        c.memory.u8[HEALTH] = 0x20
        c.run_frame()
        cur = snapshot(c)
        free = sum(1 for st, _, _ in cur if st in (0, 1, 2))
        min_free = min(min_free, free)
        if free == 0:
            zero_free_frames += 1
        for i in range(MAX_GFX):
            pst, pref, pgi = prev[i]
            st, ref, gi = cur[i]
            occ_p = pst not in (0, 1, 2)
            occ_n = st not in (0, 1, 2)
            if occ_n and (not occ_p or gi != pgi):
                if occ_p and i in born:
                    lifetimes.append((born[i][1], f - born[i][0]))
                born[i] = (f, gi)
                loads += 1
                ref0_since.pop(i, None)
            elif occ_p and not occ_n:
                if i in born:
                    lifetimes.append((born[i][1], f - born[i][0]))
                    del born[i]
                if i in ref0_since:
                    reap_lat.append(f - ref0_since.pop(i))
            if occ_n:
                if ref == 0 and i not in ref0_since:
                    ref0_since[i] = f
                elif ref > 0:
                    ref0_since.pop(i, None)
        prev = cur

    still = sum(1 for st, _, _ in prev if st not in (0, 1, 2))
    print(f'{region_name} diff {diff} seed 0x{seed:x} frames {frames}'
          + (f' combo {spec}' if spec else ''))
    print(f'  loads seen: {loads}   slots occupied at end: {still}   '
          f'min free: {min_free}   zero-free frames: {zero_free_frames}')
    if lifetimes:
        short = sum(1 for _, life in lifetimes if life < 60)
        print(f'  completed lifetimes: {len(lifetimes)} '
              f'(median {sorted(l for _, l in lifetimes)[len(lifetimes)//2]}f, '
              f'{short} under 60f)')
    if reap_lat:
        s = sorted(reap_lat)
        print(f'  refcount-0 -> freed latency: n={len(s)} '
              f'median {s[len(s)//2]}f max {s[-1]}f')
    else:
        print('  refcount-0 -> freed latency: no completed reaps observed')
    # leaked-looking slots: occupied, refCount 0, older than 5s
    leaks = [(i, born[i][1]) for i, (st, ref, gi) in enumerate(prev)
             if st not in (0, 1, 2) and ref == 0 and i in born and frames - born[i][0] > 300]
    if leaks:
        print(f'  slots at refCount 0 for >300f at end (reaper backlog): {leaks}')


if __name__ == '__main__':
    args = sys.argv[1:]
    def opt(name, default, cast):
        return cast(args[args.index(name) + 1]) if name in args else default
    run(opt('--region', 'HYRULE_FIELD_SOUTH_HYRULE_FIELD', str),
        opt('--diff', 8, int),
        opt('--seed', 0x42, lambda s: int(s, 0)),
        opt('--frames', 900, int),
        opt('--combo', None, str))
