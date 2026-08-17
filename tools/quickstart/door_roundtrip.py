"""In, and back out again, without bouncing.

The failure this exists for: a dead-door box sits exactly where the room's
own return border puts the player down, so arriving from inside would fire
the box again and the player would ping-pong forever. QuickStartProcessLinks
holds a box the player is already standing in until they step off it - this
walks the whole round trip and checks that they can.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, r16, PLAYER, ROOM_CONTROLS

ROM = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tmc.gba'))
HF = 3

# label, field room, door, walk-in key, the key that leaves the interior
TRIPS = [
    ('EH South minish hole', 2, 56, 40, 'UP', 'DOWN'),
    ('EH Center keese cave', 3, 168, 152, 'UP', 'DOWN'),
    ('NHF fairy fountain tree', 6, 752, 312, 'UP', 'DOWN'),
    ('NHF boomerang tree NW', 6, 432, 296, 'UP', 'DOWN'),
    ('Trilby keese chest', 7, 136, 546, 'UP', 'DOWN'),
    ('Trilby rupee cave', 7, 56, 680, 'UP', 'DOWN'),
    ('WW North heart tree', 8, 160, 488, 'UP', 'DOWN'),
    ('SHF minish house', 1, 72, 456, 'UP', 'DOWN'),
]


def pos(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6),
            r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))


def hold(c, key, frames, until_change_from):
    k = getattr(c, 'KEY_' + key)
    c.set_keys(k)
    for _ in range(frames):
        c.run_frame()
        if here(c) != until_change_from:
            break
    c.clear_keys(k)
    for _ in range(20):
        c.run_frame()
    return here(c)


for label, room, dx, dy, into, out in TRIPS:
    c = boot(ROM)
    poison_here(c)
    warp(c, HF, room, dx, dy + 48)
    if here(c) != (HF, room):
        print(f'{label}: could not stage ({here(c)})')
        continue
    inside = hold(c, into, 240, (HF, room))
    if inside == (HF, room):
        print(f'{label}: never entered')
        continue
    back = hold(c, out, 300, inside)
    if back == inside:
        print(f'{label}: in {inside}, but could NOT get back out')
        continue
    # And the important part: having landed back in the field, does the box
    # grab them again while they stand still?
    for _ in range(150):
        c.run_frame()
    settled = here(c)
    verdict = 'OK' if settled == back else f'BOUNCED to {settled}'
    print(f'{label}: field -> {inside} -> {back} at {pos(c)}  {verdict}')
