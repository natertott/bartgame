"""A step that forces a ? room's kind, dealt while the player is in it.

A win-chain step can force a site's kind: a portal pair's A and its landing
room fight, a torch or cleanup EVENT step deals its kind. The step can be
dealt while the player stands in that very room. The force used to apply
from that frame on and switch the room's kind under a running event
(measured at the Veil Falls cave's 1F hallway: a cleanup room became a wave
room that read the cleanup's flags as a finished survive clock and paid its
prize for no fight). QuickStartSiteForce now fixes the force for the visit.

For each site with a portal tile, in a run whose own roll there is not a
fight (sim.site_roll):

  KEPT     the room deals its own roll; a portal pair on this site is then
           written into the chain; for 600 frames the room keeps its kind:
           the latched force is "none" and the site is not DONE (no prize
           paid for a fight that never happened)
  NEXT     out and back in: the visit latches the force, and the wave room
           deals (its "decided" flag, our enemies standing)

    python3 tools/quickstart/site_force_probe.py [--rom tmc-d3.gba] [--sites N] [--seed S]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import here, entities, KIND_ENEMY
import scenario as S
import parse_tables as P
import block_probe as BP
import sim

SAVE = 0x02002a40
CHAIN_KIND, CHAIN_WHERE, CHAIN_DETAIL = SAVE + 0x26, SAVE + 0x2B, SAVE + 0x30
CHAIN_PROGRESS, CHAIN_ROLLED = SAVE + 0x35, SAVE + 0x36
RUN_SEED = SAVE + 0x4C
LATCHED, FORCE0, FORCE1 = 127, 128, 129
WAVE_DECIDED = 64 + 1      # a lone site's flagBase + 1: the wave room's "decided"
DONE_BASE = emu.FLAG_BANK_12 + 1


def done(c, site):
    b = DONE_BASE + site
    return (c.memory.u8[emu.SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1


def deal_pair(c, site):
    for i in range(5):
        c.memory.u8[CHAIN_KIND + i] = c.memory.u8[CHAIN_WHERE + i] = c.memory.u8[CHAIN_DETAIL + i] = 0
    c.memory.u8[CHAIN_KIND + 0], c.memory.u8[CHAIN_WHERE + 0], c.memory.u8[CHAIN_DETAIL + 0] = 1, site, 0x40
    c.memory.u8[CHAIN_KIND + 1], c.memory.u8[CHAIN_WHERE + 1] = 0, 0x40
    c.memory.u8[CHAIN_DETAIL + 1] = P.ITEMS['ITEM_PEGASUS_BOOTS']
    c.memory.u8[CHAIN_PROGRESS] = 0
    c.memory.u8[CHAIN_ROLLED] = 2


def probe(rom, site, seed):
    s = sim.SITES[site]
    c = S.boot(rom, S.KINDS['ROOM'], a=s['area'], b=s['room'], c=s['cx'] // 16, d=s['cy'] // 16 + 1,
               kit=0, diff=3, seed=seed, frames=120)
    BP.settle(c, 120)
    run_seed = int.from_bytes(bytes(c.memory.u8[RUN_SEED + i] for i in range(4)), 'little')
    kind = sim.EVENT_NAME[sim.site_roll(run_seed, site)[0]]
    if kind == 'WAVES':
        return None, 'own roll is WAVES (seed %#x)' % run_seed
    deal_pair(c, site)
    BP.settle(c, 600)
    latched = BP.room_flag(c, LATCHED)
    force = BP.room_flag(c, FORCE0) | (BP.room_flag(c, FORCE1) << 1)
    # (not the wave room's own flags: a miniboss uses the same window)
    kept = latched and force == 0 and not done(c, site)
    res = dict(KEPT=bool(kept))
    # out and back in: the next visit takes the force
    emu.warp(c, P.AREAS['AREA_HYRULE_FIELD'], P.ROOMS['ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD'], 200, 200, frames=200)
    emu.warp(c, s['area'], s['room'], s['cx'], s['cy'] + 16, frames=200)
    BP.settle(c, 240)
    force = BP.room_flag(c, FORCE0) | (BP.room_flag(c, FORCE1) << 1)
    res['NEXT'] = bool(BP.room_flag(c, LATCHED) and force == 1 and BP.room_flag(c, WAVE_DECIDED)
                       and len(entities(c, KIND_ENEMY)) > 0)
    return res, 'own roll %s' % kind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    ap.add_argument('--sites', type=int, default=6)
    ap.add_argument('--seed', type=int, default=11)
    a = ap.parse_args()
    bad = tested = 0
    for site in sorted(sim.PORTAL_TILES):
        if tested >= a.sites:
            break
        if site in {k['land_site'] for k in sim.PORTALS}:
            continue
        res, note = probe(a.rom, site, a.seed)
        if res is None:
            print('site %3d skipped: %s' % (site, note))
            continue
        tested += 1
        ok = all(res.values())
        bad += not ok
        print('site %3d %-40s %s  %s  (%s)' % (site, sim.SITES[site]['roomName'][5:], 'PASS' if ok else 'FAIL',
                                             ' '.join('%s=%d' % kv for kv in res.items()), note), flush=True)
    print('%d/%d sites' % (tested - bad, tested))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
