"""Every sword variant drawn in its tint, everywhere a sword is drawn.

A sword variant (game.c, sQuickStartSwordVariants) is an item id that plays
as a sword but borrows a base sword's art and is recoloured. Each draw is
checked by the palette it reaches the screen with: a tinted slot's id is
0xF<tier><source palette> (QuickStartTintSlot), so the probe reads the
OBJ palette of every OAM entry it cares about and asks gPaletteList who
that slot is.

  hud     the B button's icon (the variant equipped on B)
  swing   the blade entity (PlayerItemSword, in gAuxPlayerEntities) while
          B is held
  menu    the pause menu's B button, the item grid's sword slot, and the
          name line (screenshot only)

    python3 tools/quickstart/sword_variant_probe.py [--rom tmc-d3.gba] [--out DIR]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
import scenario as S
import parse_tables as P
import block_probe as B

SAVE = 0x02002a40
INVENTORY = SAVE + 0xF2
EQUIPPED = SAVE + 0xB4
PALETTE_LIST = 0x02001a00
OAM = 0x07000000
AUX = 0x030011e8          # gAuxPlayerEntities
AUX_COUNT = 7
TIERS = {'QS_TINT_RUST': 3, 'QS_TINT_STONE': 4, 'QS_TINT_BLUE': 5, 'QS_TINT_RED': 6, 'QS_TINT_EARTH': 7,
         'QS_PASTRY_GREEN': 1, 'QS_PASTRY_GOLD': 2}


def variants():
    i = P.GAME.find('sQuickStartSwordVariants[] = {')
    body = P.GAME[i:P.GAME.find('};', i)]
    return [(P.ITEMS[a], P.ITEMS[b], TIERS[t]) for a, b, t in re.findall(r'\{ (ITEM_\w+), (ITEM_\w+), (QS_\w+) \}', body)]


def own(c, item, on):
    a, sh = INVENTORY + (item >> 2), (item & 3) * 2
    c.memory.u8[a] = (c.memory.u8[a] & ~(3 << sh)) | ((1 if on else 0) << sh)


def slot_id(c, slot):
    return c.memory.u8[PALETTE_LIST + slot * 4 + 2] | (c.memory.u8[PALETTE_LIST + slot * 4 + 3] << 8)


def oam(c):
    out = []
    for k in range(128):
        a0 = c.memory.u8[OAM + k * 8] | (c.memory.u8[OAM + k * 8 + 1] << 8)
        a1 = c.memory.u8[OAM + k * 8 + 2] | (c.memory.u8[OAM + k * 8 + 3] << 8)
        a2 = c.memory.u8[OAM + k * 8 + 4] | (c.memory.u8[OAM + k * 8 + 5] << 8)
        if (a0 & 0x300) == 0x200:
            continue
        out.append(dict(x=a1 & 0x1ff, y=a0 & 0xff, tile=a2 & 0x3ff, pal=a2 >> 12))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    ap.add_argument('--out')
    a = ap.parse_args()
    if a.out:
        os.makedirs(a.out, exist_ok=True)
    results = []
    for item, base, tier in variants():
        want = lambda pid, src: pid == (0xF000 | (tier << 8) | src)
        c = S.boot(a.rom, S.KINDS['ROOM'], P.AREAS['AREA_HYRULE_TOWN'], P.ROOMS['ROOM_HYRULE_TOWN_MAIN'], 30, 40,
                   kit=2, frames=300)
        B.dismiss(c)
        B.run(c, 60)
        for n in range(1, 7):
            own(c, n, n in (base, item))
        c.memory.u8[EQUIPPED + 1] = item
        B.run(c, 30)
        # HUD: the B icon sits in the top right
        hud = [o for o in oam(c) if o['y'] < 40 and 160 <= o['x'] < 200 and want(slot_id(c, o['pal']), 4)]
        results.append(('hud', item, bool(hud), '%d entries in the tint' % len(hud)))
        if a.out:
            emu.snap(c, os.path.join(a.out, 'variant%d_hud.png' % item))
        # swing: the blade entity's palette while B is held
        c.set_keys(c.KEY_B)
        seen = set()
        for f in range(12):
            c.run_frame()
            for k in range(AUX_COUNT):
                b = AUX + k * emu.STRIDE
                if c.memory.u8[b + 8] == 8 and c.memory.u8[b + 9] == 1:   # PLAYER_ITEM, PLAYER_ITEM_SWORD
                    seen.add(slot_id(c, c.memory.u8[b + 0x1a] & 15))
            if f == 6 and a.out:
                emu.snap(c, os.path.join(a.out, 'variant%d_swing.png' % item))
        c.clear_keys(c.KEY_B)
        ok = bool(seen) and all((p & 0xFF00) == (0xF000 | (tier << 8)) for p in seen)
        results.append(('swing', item, ok, 'blade palettes %s' % sorted('%04x' % p for p in seen)))
        B.run(c, 40)
        emu.press(c, c.KEY_START, 3, 90)
        tinted = [o for o in oam(c) if want(slot_id(c, o['pal']), 4)]
        results.append(('menu', item, len(tinted) >= 2, '%d entries in the tint (button and grid)' % len(tinted)))
        if a.out:
            emu.snap(c, os.path.join(a.out, 'variant%d_menu.png' % item))
        del c
    bad = 0
    for where, item, ok, note in results:
        bad += not ok
        print('%-5s %-6s item %d: %s' % ('PASS' if ok else 'FAIL', where, item, note))
    print('RESULT %s %d/%d' % ('PASS' if not bad else 'FAIL', len(results) - bad, len(results)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
