"""Does sim.roll_step deal the same chain step as the ROM?

sim_validate.py checks the reach flood and site_roll_validate.py the ?
room roll. This checks the layer on top: QuickStartChainRollStep itself -
the keyed pair, the escalation pair and its rare-region seek, the spread
rule, the kind rotation and the rare-region weights. Everything it reads is
save state, so one boot serves every case:

  * a random run seed (the memory-pair cache key cleared with it),
  * a random handful of reach items and chain keys written into the
    inventory,
  * a step index 0-2 with the earlier steps cleared,
  * a random drop row,

then the ROM deals the step and the model is asked the same question with
the ROM's own drop row, quest host, held reach mask and golden-gate rolls.

    python3 tools/quickstart/chain_roll_validate.py [--cases 300] [--rom tmc.gba]
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from callrom import call_keep, game_sym
import parse_tables as P
import sim

SAVE = 0x02002a40
CHAIN_KIND, CHAIN_WHERE, CHAIN_DETAIL = SAVE + 0x26, SAVE + 0x2B, SAVE + 0x30
RUN_SEED = SAVE + 0x4C
MEMORY_KEY = SAVE + 0x86
INVENTORY = SAVE + 0xF2
ITEM_NAME = {v: k for k, v in P.ITEMS.items()}


def set_item(c, name, on):
    n = P.ITEMS[name]
    a, sh = INVENTORY + (n >> 2), (n & 3) * 2
    v = c.memory.u8[a] & ~(3 << sh)
    c.memory.u8[a] = v | ((1 << sh) if on else 0)


def get_item(c, name):
    n = P.ITEMS[name]
    return (c.memory.u8[INVENTORY + (n >> 2)] >> ((n & 3) * 2)) & 3


def item_of(detail):
    if 0xF0 <= detail < 0xF0 + len(sim.CHAIN_KEYS):
        return sim.CHAIN_KEYS[detail - 0xF0]
    return ITEM_NAME.get(detail, detail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cases', type=int, default=300)
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc.gba'))
    a = ap.parse_args()
    fn = {n: game_sym(n) for n in ('QuickStartChainRollStep', 'QuickStartRollDropRegionOnce',
                                   'QuickStartDropRegionIndexUsable', 'QuickStartQuestSlot',
                                   'QuickStartHeldReachMask', 'QuickStartGoldGateOpen',
                                   'QuickStartRandomizeQuestOnce', 'QuickStartWritePoolIdx')}
    c = emu.boot(a.rom)
    call_keep(c, fn['QuickStartRollDropRegionOnce'], ())
    call_keep(c, fn['QuickStartRandomizeQuestOnce'], ())
    quest = call_keep(c, fn['QuickStartQuestSlot'], ()) & 0xff
    gates = [call_keep(c, fn['QuickStartGoldGateOpen'], (g,)) & 1 for g in (0, 1)]
    pool = sim.ESC_ITEMS + ['ITEM_QST_LONLON_KEY', 'ITEM_QST_GRAVEYARD_KEY']
    rng = random.Random(0xC4A1)
    agree, bad, kinds, drops = 0, [], {}, {}
    for case in range(a.cases):
        seed = rng.getrandbits(32)
        for b in range(4):
            c.memory.u8[RUN_SEED + b] = (seed >> (8 * b)) & 0xff
        c.memory.u8[MEMORY_KEY] = c.memory.u8[MEMORY_KEY + 1] = 0
        held_items = set(rng.sample(pool, rng.randrange(0, 6)))
        for it in pool:
            set_item(c, it, it in held_items)
        step = rng.randrange(3)
        # A drop row per case (GF_DROP_REGION_BIT(0) = 467, GF_POOL_HI_DROP
        # = 211 in game.c), so every region's weight is exercised.
        call_keep(c, fn['QuickStartWritePoolIdx'], (467, 211, rng.randrange(sim.POOL_SIZE)))
        drop = call_keep(c, fn['QuickStartDropRegionIndexUsable'], ()) & 0xff   # the USABLE drop, as QuickStartReachCompute reads it
        drops[drop] = drops.get(drop, 0) + 1
        for i in range(5):
            c.memory.u8[CHAIN_KIND + i] = c.memory.u8[CHAIN_WHERE + i] = c.memory.u8[CHAIN_DETAIL + i] = 0
        held = call_keep(c, fn['QuickStartHeldReachMask'], ()) & 0xffffffff
        dealt = call_keep(c, fn['QuickStartChainRollStep'], (step,), budget=40000000)
        rom = [(c.memory.u8[CHAIN_KIND + s], c.memory.u8[CHAIN_WHERE + s], c.memory.u8[CHAIN_DETAIL + s])
               for s in range(step, step + max(1, dealt))]
        # Owned as the ROM sees it: every reach item and chain key read back
        # from the inventory (a harness boot need not hold the boot items).
        owned = {it for it in set(sim.REACH_ITEMS) | set(pool) | set(sim.BOOT_ITEMS)
                 if it in P.ITEMS and get_item(c, it)}
        if gates[0]:
            owned.add('GATE_FLOW_OPEN')
        if gates[1]:
            owned.add('GATE_STATUES_OPEN')
        nodes = sim.reachable_nodes(held, drop)
        model = sim.roll_step(seed, step, set(), nodes, held, owned, quest, set(),
                              carrier=sim.carrier_preferred(seed), drop_pool=drop)

        # An ITEM step compares by item (the ROM stores a key as 0xF0 + its
        # index and a plain item as its id; the model stores the name);
        # every other step by kind and site or row.
        r = [(k, item_of(d) if d else None) if k == sim.KIND_ITEM else (k, w) for k, w, d in rom]
        m = [(k, d) if k == sim.KIND_ITEM else (k, w) for k, w, d in model]
        tag = '+'.join(sim.KIND_NAME[k] for k, _ in r)
        kinds[tag] = kinds.get(tag, 0) + 1
        if r == m:
            agree += 1
        else:
            bad.append((hex(seed), step, sorted(held_items), r, m))
    del c
    print(f'{agree}/{a.cases} chain rolls agree over {len(drops)} drop rows (quest row {quest}, gates open {gates})')
    print('  dealt:', ', '.join(f'{k} {v}' for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])))
    for row in bad[:15]:
        print('  MISMATCH seed=%s step=%d held=%s rom=%s model=%s' % row)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
