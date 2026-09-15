"""Pick a content spot for each Mt Crenel room the survey named.

A ? room's event is placed at one fixed room-local coordinate, and a bad one
is the difference between a fight and a wave nobody can clear: the spot has
to be inside the walkable component the player ARRIVES in, and far enough
from the arrival tile that the event does not deal itself onto the doorstep.
So: warp in at the survey's own coordinate, flood the collision from where
the player lands, and take the tile that maximises distance from the arrival
subject to eight-way clearance.
"""
import sys, os
sys.path.insert(0, os.path.abspath('tools/quickstart'))
from emu import boot, warp, here, coll_at, room_dims, PLAYER, r16
import parse_tables as P

ROOMS = [
    ('AREA_CAVE_OF_FLAMES', 'ROOM_CAVE_OF_FLAMES_ENTRANCE', 136, 168),
    ('AREA_MELARIS_MINE', 'ROOM_MELARIS_MINE_MAIN', 159, 290),
    ('AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_EXIT_TO_MINES', 184, 152),
    ('AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_PILLAR_CAVE', 56, 78),
    ('AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_BLOCK_PUSHING', 568, 200),
    ('AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_GRIP_RING', 120, 120),
    ('AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_TO_GRAYBLADE', 120, 240),
    ('AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_HERMIT', 120, 120),
    ('AREA_CRENEL_CAVES', 'ROOM_CRENEL_CAVES_HINT_SCRUB', 120, 120),
    ('AREA_CRENEL_DIG_CAVE', 'ROOM_CRENEL_DIG_CAVE_0', 56, 325),
    ('AREA_DOJOS', 'ROOM_DOJOS_GRAYBLADE', 120, 160),
    ('AREA_CRENEL_MINISH_PATHS', 'ROOM_CRENEL_MINISH_PATHS_SPRING_WATER', 128, 792),
    ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_CENTER', 504, 120),
    ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_TOP', 240, 151),
    ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_WALL_CLIMB', 160, 377),
    ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_ENTRANCE', 861, 54),
    ('AREA_MT_CRENEL', 'ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE', 101, 271),
]


def open_at(c, tx, ty, w, h):
    if tx < 0 or ty < 0 or tx >= w or ty >= h:
        return False
    return coll_at(c, tx, ty) == 0


def survey(an, rn, ax, ay):
    a, r = P.AREAS[an], P.ROOMS[rn]
    c = boot('tmc.gba')
    warp(c, a, r, ax, ay)
    if here(c) != (a, r):
        del c
        return '%-42s did not land' % rn
    w, h = room_dims(c)
    tw, th = w // 16, h // 16
    px = r16(c, PLAYER + 0x2e) - r16(c, 0x03000bf0 + 6)
    py = r16(c, PLAYER + 0x32) - r16(c, 0x03000bf0 + 8)
    start = (px // 16, py // 16)
    if not open_at(c, start[0], start[1], tw, th):
        # the player can stand on a tile the collision map calls solid at its
        # centre (stairs, ledges); seed from the nearest open neighbour
        found = None
        for d in range(1, 5):
            for dx in range(-d, d + 1):
                for dy in range(-d, d + 1):
                    if open_at(c, start[0] + dx, start[1] + dy, tw, th):
                        found = (start[0] + dx, start[1] + dy)
                        break
                if found:
                    break
            if found:
                break
        if not found:
            del c
            return '%-42s no open tile near the arrival (%d,%d)' % (rn, px, py)
        start = found
    seen, stack, comp = {start}, [start], []
    while stack:
        q = stack.pop()
        comp.append(q)
        for nb in ((q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)):
            if nb not in seen and open_at(c, nb[0], nb[1], tw, th):
                seen.add(nb)
                stack.append(nb)
    # Not the farthest tile - that is always a corner, and a corner is a bad
    # anchor for a wave that rings outward from it. Among the tiles that are
    # 3x3-clear AND at least four tiles off the arrival (the door keep-clear
    # the spawner already enforces is two, four for a ball-and-chain), take
    # the one nearest the component's centre of mass.
    cand = [(tx, ty) for (tx, ty) in comp
            if all(open_at(c, tx + dx, ty + dy, tw, th)
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    far = [q for q in cand if abs(q[0] - start[0]) + abs(q[1] - start[1]) >= 4]
    pool = far or cand
    best, bestd = None, -1
    if pool:
        cx = sum(q[0] for q in comp) / float(len(comp))
        cy = sum(q[1] for q in comp) / float(len(comp))
        best = min(pool, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2)
        bestd = abs(best[0] - start[0]) + abs(best[1] - start[1])
    del c
    if best is None:
        return '%-42s %3d tiles, NO 3x3-clear spot' % (rn, len(comp))
    return ('%-42s room %3dx%-3d  component %4d  spot (%d,%d) = px (%d,%d), %d tiles from the door'
            % (rn, tw, th, len(comp), best[0], best[1], best[0] * 16 + 8, best[1] * 16 + 8, bestd))


for an, rn, ax, ay in ROOMS:
    print(survey(an, rn, ax, ay))
    sys.stdout.flush()
