"""Does a normal run deal the block puzzle the model predicts?

block_probe.py forces each puzzle through the testbed. This takes the
run's own path: for a few ? room sites, find a run seed whose roll deals
BLOCKS there (sim.site_roll), predict the frame and content the ROM draws
(QuickStartBlocksPick: uniform over every puzzle the site holds, salted
0xB10D + site), boot that seed into the site's room (scenario ROOM, so
nothing is forced) and compare the rocks the room deals with the
prediction.

    python3 tools/quickstart/block_runpick.py [--rom tmc-d3.gba] [--sites 6]
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import block_probe as B
import emu
import parse_tables as P
import scenario as S
import sim


def predict(frames, site, seed):
    owned = [(i, f) for i, f in enumerate(frames) if f['owner'] == 'site:%d' % site]
    total = sum(len(f['contents']) for _, f in owned)
    k = ((sim.chain_hash(seed, 0xB10D + site) >> 3) & 0x7fff) % total
    for i, f in owned:
        if k < len(f['contents']):
            return i, k
        k -= len(f['contents'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    ap.add_argument('--solutions', default=B.SOLUTIONS)
    ap.add_argument('--sites', type=int, default=6)
    a = ap.parse_args()
    frames = json.load(open(a.solutions))
    rooms = json.load(open(os.path.join(P.ROOT, 'build', 'block_rooms.json')))
    rng = random.Random(7)
    # sites whose kind can become BLOCKS (an elite, rare or miniboss site
    # holds a pool but never deals it)
    sites = sorted({int(f['owner'][5:]) for f in frames if f['owner'].startswith('site:')
                    and sim.SITES[int(f['owner'][5:])]['kinds'] in ('ANY', 'LARGE', 'SMALL')})
    ok = bad = 0
    for site in rng.sample(sites, min(a.sites, len(sites))):
        seed = next(s for s in (rng.getrandbits(32) for _ in range(5000)) if sim.site_roll(s, site)[0] == sim.EV_BLOCKS)
        fi, k = predict(frames, site, seed)
        inst = B.instance(frames[fi], k)
        r = rooms['site:%d' % site]
        px, py = r['player']
        c = S.boot(a.rom, S.KINDS['ROOM'], P.AREAS[inst['area']], P.ROOMS[inst['room']], px // 16, py // 16,
                   kit=2, seed=seed, frames=300)
        B.KEY = (c.KEY_UP, c.KEY_RIGHT, c.KEY_DOWN, c.KEY_LEFT)
        B.dismiss(c)
        B.settle(c)
        want = {(x, y): kk for x, y, kk in inst['move']}
        want.update({t: 3 for t in inst['fixed']})
        got = B.rocks(c)
        good = got == want
        ok += good
        bad += not good
        print('site %3d %-40s seed %08x frame %3d content %2d: %s' % (
            site, inst['room'][5:], seed, fi, k, 'dealt as predicted' if good else
            'MISMATCH missing %s extra %s' % (sorted(set(want) - set(got))[:4], sorted(set(got) - set(want))[:4])),
            flush=True)
        del c
    print('%d/%d run-dealt puzzles as predicted' % (ok, ok + bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
