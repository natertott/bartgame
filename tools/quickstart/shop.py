"""What the hub shop is actually stocking, and for how much.

The shelf is eight slots in two kinds (see sQuickStartShopFixed and
sQuickStartShopPool in game.c): four permanent and repeatable - a recovery
heart, ten arrows, ten bombs, a heart piece - and four drawn once per run and
sellable once each. This reads the run's rolled state straight out of the flag
bank and reports it, then optionally drives a real purchase through the
merchant so the whole chain gets exercised: lift, carry, confirm, pay, and the
slot retiring itself afterwards.

Usage:
    python3 tools/quickstart/shop.py [seed ...]
    python3 tools/quickstart/shop.py --buy <slot> [seed]

`--buy` takes a slot index 0-7 in display order (0-3 near row, 4-7 far row).
Buying slot 3 twice is the heart-piece price ramp: 50, then 75.

`--arm` grants the Bow and Bombs first, so the two ammo slots stock.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from emu import here, entities, warp, press, ROOM_CONTROLS, PLAYER, r16, w16
from seed import boot_pinned

SAVE_BASE = 0x02002a40
SAVE_FLAGS = SAVE_BASE + 0x25C
RUPEES = SAVE_BASE + 0xA8 + 0x18   # gSave.stats.rupees
HEART_PIECES = SAVE_BASE + 0xA8 + 0x01
INVENTORY = SAVE_BASE + 0xF2  # 2 bits per item, indexed by Item id
ITEM_BOW, ITEM_BOMBS = 9, 7
FLAG_BANK_12 = 0xA80
QS_ORIGIN = 700
PLAYER_STATE = 0x03003f80

# Mirrors of game.c's flag block. Kept here rather than parsed for the same
# reason HUB_SHOP_SPOTS is: a reader that derives its own expectations from
# the thing it is checking cannot catch that thing moving.
GF_SHOP_RANDOMIZED = 657
GF_SHOP_REFILL_PRICE = 266  # i*7 + b, i = 0..2
GF_SHOP_ONEOFF_PRICE = 287  # i*9 + b, i = 0..3
GF_SHOP_HEART_PIECE_BUYS = 323  # 5 bits
GF_SHOP_SLOT_SOLD = 328  # i, i = 0..3
GF_SHOP_SLOT_BIT = 97  # bank 11, i*6 + b, i = 0..3
FLAG_BANK_11 = 0x9C0

HEART_PIECE_BASE = 50
HEART_PIECE_STEP = 25

SHOP_AREA, SHOP_ROOM = 48, 1
WALKWAY_Y = 104
SPOTS = [(64, 120), (96, 120), (128, 120), (160, 120),
         (48, 88), (80, 88), (112, 88), (144, 88)]
MERCHANT = (192, 104)

names = {}
for line in open(os.path.join(HERE, '..', '..', 'build/USA/enum_include/item.inc')):
    m = re.match(r'\.set (\w+), (\d+)', line.strip())
    if m:
        names.setdefault(int(m.group(2)), m.group(1))


def _bit(c, bank, off):
    b = bank + off
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1


def qs(c, off):
    return _bit(c, FLAG_BANK_12, QS_ORIGIN + off)


def qs_field(c, base, bits):
    return sum(qs(c, base + i) << i for i in range(bits))


def slot_entry(c, i):
    return sum(_bit(c, FLAG_BANK_11, GF_SHOP_SLOT_BIT + i * 6 + b) << b for b in range(6))


def stock(c):
    """(spot, item id or None) for each of the eight slots, from the room."""
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    at = {}
    for e in entities(c):
        if e[1] != 6:  # OBJECT
            continue
        at[(e[4] - ox, e[5] - oy)] = e[3]
    return [(s, at.get(s)) for s in SPOTS]


def price(c, slot):
    if slot == 3:
        return HEART_PIECE_BASE + HEART_PIECE_STEP * qs_field(c, GF_SHOP_HEART_PIECE_BUYS, 5)
    if slot < 3:
        return qs_field(c, GF_SHOP_REFILL_PRICE + slot * 7, 7) + 1
    return qs_field(c, GF_SHOP_ONEOFF_PRICE + (slot - 4) * 9, 9) + 1


def report(c):
    print(f'  randomized={bool(qs(c, GF_SHOP_RANDOMIZED))}  '
          f'heart pieces bought={qs_field(c, GF_SHOP_HEART_PIECE_BUYS, 5)}')
    for i, (spot, item) in enumerate(stock(c)):
        kind = 'permanent' if i < 4 else 'one-off'
        sold = '' if i < 4 else ('  SOLD' if qs(c, GF_SHOP_SLOT_SOLD + i - 4) else '')
        shown = names.get(item, 'bare' if item is None else hex(item))
        print(f'  slot {i} {spot!s:>10} {kind:<9} {shown:<24} {price(c, i):>4} rupees{sold}')


def give(c, item, value=1):
    """Set an inventory slot directly - gSave.inventory, 2 bits per item."""
    a = INVENTORY + (item >> 2)
    sh = (item & 3) * 2
    c.memory.u8[a] = (c.memory.u8[a] & ~(3 << sh)) | ((value & 3) << sh)


def enter_shop(c):
    warp(c, SHOP_AREA, SHOP_ROOM, 120, WALKWAY_Y, frames=300)
    return here(c) == (SHOP_AREA, SHOP_ROOM)


def buy(c, slot, purse=900):
    """Lift the slot's item, carry it to the merchant, and accept the sale.

    A run starts with a maxed wallet and ZERO rupees in it, so without topping
    the purse up first every purchase takes the merchant's "you can't afford
    that" branch and nothing is exercised at all.
    """
    w16(c, RUPEES, purse)
    ix, iy = SPOTS[slot]
    warp(c, SHOP_AREA, SHOP_ROOM, ix, WALKWAY_Y, frames=240)
    key = c.KEY_UP if iy < WALKWAY_Y else c.KEY_DOWN
    for _ in range(10):
        c.set_keys(key)
        c.run_frame()
    c.clear_keys(key)
    for _ in range(10):
        c.run_frame()
    for _ in range(10):
        press(c, c.KEY_R, 4, 6)
        if c.memory.u8[PLAYER_STATE + 5]:
            break
    if not c.memory.u8[PLAYER_STATE + 5]:
        return 'could not lift it'
    # WALK it over, rather than teleporting. The merchant is talked to
    # through CheckEntityInteractType, which needs the player adjacent AND
    # facing him; a teleport leaves them facing whichever way the lift left
    # them (down), so an A press there does nothing at all. Walking east
    # along the walkway sets the facing as a side effect of arriving.
    #
    # Two details this took to get right: the lift leaves the player a few
    # pixels below the walkway, so snap y back first or the approach ends
    # off-row and out of range; and stop at 14px, not 18 - at 18 the talk
    # simply does not fire.
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    w16(c, PLAYER + 0x32, oy + WALKWAY_Y)
    for _ in range(10):
        c.run_frame()
    for _ in range(400):
        c.set_keys(c.KEY_RIGHT)
        c.run_frame()
        if r16(c, PLAYER + 0x2e) - ox >= MERCHANT[0] - 14:
            break
    c.clear_keys(c.KEY_RIGHT)
    for _ in range(10):
        c.run_frame()
    # Talk, accept the confirm box, then sit through the item-get animation.
    for _ in range(60):
        press(c, c.KEY_A, 3, 6)
    for _ in range(200):
        c.run_frame()
    for _ in range(40):
        press(c, c.KEY_A, 3, 6)
    return None


def main(argv):
    if '--buy' in argv:
        i = argv.index('--buy')
        slot = int(argv[i + 1])
        rest = argv[:i] + argv[i + 2:]
        sd = int(rest[0], 0) if rest else 0x1
        c = boot_pinned('tmc.gba', sd)
        if not enter_shop(c):
            print(f'could not reach the shop, landed in {here(c)}')
            return 1
        print(f'########## seed 0x{sd:08x}  before')
        report(c)
        w16(c, RUPEES, 900)
        before = r16(c, RUPEES)
        print(f'  rupees {before}, heart pieces held {c.memory.u8[HEART_PIECES]}')
        err = buy(c, slot)
        if err:
            print(f'  buy slot {slot}: {err}')
            return 1
        after = r16(c, RUPEES)
        print(f'########## after buying slot {slot}: rupees {before} -> {after} '
              f'(spent {before - after}), heart pieces held '
              f'{c.memory.u8[HEART_PIECES]}')
        # Re-enter so QuickStartMaintainShop gets a clean pass at restocking.
        warp(c, SHOP_AREA, 2, 120, 200, frames=240)
        enter_shop(c)
        report(c)
        return 0

    # --arm grants the Bow and Bombs before walking in, which is the only way
    # to see the two ammo slots stocked: they carry QS_REQ_BOW / QS_REQ_BOMBS
    # and a fresh run holds neither weapon.
    #
    # Expect a knock-on: if this run's WEAPON slot drew the Bow or the Bombs,
    # that slot now reads bare, because the shelf hides anything the player
    # already owns. That is the shop working, not a missed draw - compare
    # against the same seed without --arm before calling it a bug.
    arm = '--arm' in argv
    if arm:
        argv = [a for a in argv if a != '--arm']
    for sd in [int(a, 0) for a in argv] or [0x1, 0xDEADBEEF, 0x5EED5EED]:
        c = boot_pinned('tmc.gba', sd)
        print(f'########## seed 0x{sd:08x}' + ('  (bow + bombs granted)' if arm else ''))
        if arm:
            give(c, ITEM_BOW)
            give(c, ITEM_BOMBS)
        if not enter_shop(c):
            print(f'  could not reach the shop, landed in {here(c)}')
            continue
        report(c)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
