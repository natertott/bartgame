"""Extract TMC's mechanics tables as data for an engine written from scratch.

The new engine does not run TMC's code, but it must play like it. These
tables are the parts of "feel" that live in data rather than in AI code:

  enemies.csv          per enemy id and form: health, speed (Q8.8 px/frame),
                       contact damage type, hitbox, collision mask, sheet
                       kind (fixed = shared by every instance, swap = one
                       slot per instance) and its slot count
  hitboxes.csv         every named hitbox: offset, half-extents, the 4 tile probe offsets
  collision_matrix.csv every non-empty hit response. Row hitType is the
                       non-player side (enemy, projectile), column hurtType
                       the player side (body 0, sword swings, arrows...).
                       org_* applies to the player side, tgt_* to the other.
                       Knockback speed is Q8.8 px/frame (already x16),
                       negative iframes mean "flash without blocking", and
                       handler != default means special code handles it
  player_animations.csv every ANIM_* in include/player.h: keyframe durations
                       and the flag cues the code reads (entity->frame)

Sources: src/enemy.c, src/data/hitbox.c (parsed), and gCollisionMtx read
from the vanilla ROM (baserom.gba, USA, 0x080B7B74, 173*34 entries of 12
bytes; index = hitType * 34 + hurtType).

    python3 tools/newgame/extract_feel.py      # writes docs/newgame/data/
"""
import csv
import os
import re
import struct

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'docs', 'newgame', 'data')


def strip_variants(src):
    """Keep the USA side of #ifdef EU / #ifdef JP blocks."""
    out, stack = [], []
    for line in src.splitlines():
        s = line.strip()
        m = re.match(r'#if(n?)def\s+(\w+)', s)
        if m:
            neg, name = m.group(1) == 'n', m.group(2)
            usa = (name not in ('EU', 'JP', 'DEMO_JP', 'DEMO_USA')) if not neg else (name in ('EU', 'JP', 'DEMO_JP', 'DEMO_USA'))
            stack.append(usa)
            continue
        if s.startswith('#else') and stack:
            stack[-1] = not stack[-1]
            continue
        if s.startswith('#endif') and stack:
            stack.pop()
            continue
        if all(stack):
            out.append(line)
    return '\n'.join(out)


def hitboxes():
    src = strip_variants(open(os.path.join(ROOT, 'src/data/hitbox.c')).read())
    hb = {}
    for m in re.finditer(r'(?:Hitbox|Hitbox3D)\s+(\w+)\s*=\s*\{([^;]*)\};', src):
        nums = [int(x, 0) for x in re.findall(r'-?(?:0x[0-9a-fA-F]+|\d+)', m.group(2))]
        hb[m.group(1)] = nums
    return hb


def enemy_ids():
    src = open(os.path.join(ROOT, 'include/enemy.h')).read()
    body = src[src.find('enum {', src.find('OCTOROK') - 200):]
    names = re.findall(r'/\*0x([0-9a-f]+)\*/\s*([A-Z_0-9]+)', body[:body.find('}')])
    return {int(i, 16): n for i, n in names}


def fixed_gfx_counts():
    """gFixedTypeGfxData: slot count is bits 24-30 of each entry."""
    src = open(os.path.join(ROOT, 'data/gfx/fixed_type_gfx_data.s')).read() if os.path.exists(
        os.path.join(ROOT, 'data/gfx/fixed_type_gfx_data.s')) else ''
    return src


ROW = re.compile(r'\{\s*(-?\w+)\s*,\s*(-?\w+)\s*,\s*\{?\s*(?:\([^)]*\))?\s*&?(\w+)\s*\}?\s*,\s*(\w+)\s*,\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}\s*,\s*(-?\w+)\s*,\s*(-?\w+)\s*,\s*(-?\w+)\s*,\s*(-?\w+)\s*\}')


def enemies(hb):
    src = strip_variants(open(os.path.join(ROOT, 'src/enemy.c')).read())
    tables = {}
    for m in re.finditer(r'const EnemyDefinition (gEnemyDefinition\w*)\[\]\s*=\s*\{(.*?)\n\};', src, re.S):
        rows = []
        for line in m.group(2).splitlines():
            line = line.strip()
            mf = re.match(r'MULTI_FORM\((\w+)\)', line)
            if mf:
                rows.append(('MULTI', mf.group(1)))
                continue
            r = ROW.search(line)
            if r:
                rows.append(('ROW', r.groups()))
            elif line.startswith('{'):
                rows.append(('BAD', line))   # holds its place; reported below
        tables[m.group(1)] = rows
    ids = enemy_ids()
    out = []

    def emit(eid, form, g):
        gfx = int(g[0], 0)
        kind = 'none' if gfx == 0 else 'common' if gfx & 0x8000 else 'swap' if gfx & 0x4000 else 'fixed'
        slots = (gfx >> 4) & 0xff if kind == 'swap' else ''
        h = hb.get(g[2], [])
        out.append({
            'id': '0x%02x' % eid, 'name': ids.get(eid, '?'), 'form': form,
            'health': int(g[8], 0), 'speed_q8_8': int(g[9], 0), 'speed_px_per_frame': '%.4g' % (int(g[9], 0) / 256),
            'damage_type': int(g[10], 0), 'collision_mask': int(g[11], 0),
            'hitbox': g[2], 'hb_off_x': h[0] if h else '', 'hb_off_y': h[1] if h else '',
            'hb_half_w': h[6] if len(h) > 7 else '', 'hb_half_h': h[7] if len(h) > 7 else '',
            'sheet': kind, 'gfx': '0x%04x' % gfx, 'swap_slots': slots, 'sprite': g[3],
            'draw_prio_collide_draw_shadow': '/'.join(g[4:8]),
        })

    for eid, row in enumerate(tables['gEnemyDefinitions']):
        if row[0] == 'BAD':
            raise SystemExit('unparsed enemy row %d: %s' % (eid, row[1]))
        if row[0] == 'MULTI':
            for form, sub in enumerate(tables.get(row[1], [])):
                if sub[0] == 'ROW':
                    emit(eid, form, sub[1])
        else:
            emit(eid, 0, row[1])
    return out


def collision_matrix():
    rom = open(os.path.join(ROOT, 'baserom.gba'), 'rb').read()
    base = 0x0B7B74
    # org = the player side (the player's body, a sword, an arrow): column
    # hurtType. tgt = the other side (an enemy, a projectile): row hitType.
    # ColSettings' tgtDamage is what the ORG loses and orgDamage what the
    # TGT loses (CollisionDefault sets each entity's `damage`, and
    # CalculateDamage subtracts the other side's), so they are renamed.
    names = ['org_knockback_speed', 'org_iframes', 'org_knockback_duration', 'damage_to_org', 'org_confused_time',
             'tgt_knockback_speed', 'tgt_iframes', 'tgt_knockback_duration', 'damage_to_tgt', 'tgt_confused_time',
             'flags']
    rows = []
    for ht in range(173):
        for hu in range(34):
            b = rom[base + (ht * 34 + hu) * 12: base + (ht * 34 + hu) * 12 + 12]
            if not any(b):
                continue
            if b[0] == 0xff:
                rows.append({'hitType': ht, 'hurtType': hu, 'handler': struct.unpack('<H', b[2:4])[0]})
                continue
            v = list(b[:11])
            v[6] = struct.unpack('b', bytes([v[6]]))[0]
            d = {'hitType': ht, 'hurtType': hu, 'handler': 'default'}
            d.update(dict(zip(names, v)))
            d['org_knockback_speed'] *= 16
            d['tgt_knockback_speed'] *= 16
            rows.append(d)
    return rows


def u32(rom, a):
    return struct.unpack('<I', rom[a & 0x1ffffff: (a & 0x1ffffff) + 4])[0]


def keyframes(rom, sprite, index):
    """Keyframes of one animation: (frame_index, duration, bitfield, flags).
    gSpritePtrs (vanilla 0x080029B4) is 16 bytes per sprite; its first word
    points at the sprite's animation pointer array. flags is what the code
    reads as entity->frame: 0x80 ANIM_DONE, low bits are per-animation cues
    (the roll's speed phases, item hit windows)."""
    anims = u32(rom, 0x080029B4 + sprite * 16)
    if not 0x08000000 <= anims < 0x09000000:
        return None
    ptr = u32(rom, anims + index * 4)
    if not 0x08000000 <= ptr < 0x09000000:
        return None
    out = []
    for k in range(96):
        a = (ptr & 0x1ffffff) + k * 4
        f, d, b1, b2 = rom[a:a + 4]
        out.append((f, d, b1, b2))
        if b2 & 0x80:
            break
    return out


def player_animations():
    rom = open(os.path.join(ROOT, 'baserom.gba'), 'rb').read()
    src = open(os.path.join(ROOT, 'include/player.h')).read()
    rows = []
    for name, val in re.findall(r'\b(ANIM_\w+)\s*=\s*(0x[0-9a-fA-F]+)', src):
        v = int(val, 16)
        sprite, index = v >> 8, v & 0xff
        kf = keyframes(rom, sprite, index)
        if not kf:
            continue
        total = sum(d for _, d, _, _ in kf if d != 255)
        cues, t = [], 0
        for f, d, b1, b2 in kf:
            if b2 & 0x7f:
                cues.append('t%d:0x%02x' % (t, b2 & 0x7f))
            t += d if d != 255 else 0
        rows.append({'name': name, 'id': '0x%03x' % v, 'sprite': sprite, 'index': index,
                     'keyframes': len(kf), 'frames_total': total,
                     'ends': 'hold' if kf[-1][1] == 255 else 'done' if kf[-1][3] & 0x80 else 'loop?',
                     'durations': ' '.join(str(d) for _, d, _, _ in kf),
                     'cues(t:flags)': ' '.join(cues)})
    return rows


def write(name, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(OUT, name), 'w', newline='') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)
    print('%-22s %5d rows' % (name, len(rows)))


def main():
    os.makedirs(OUT, exist_ok=True)
    hb = hitboxes()
    write('hitboxes.csv', [{'name': k, 'off_x': v[0], 'off_y': v[1], 'probe': ' '.join(map(str, v[2:6])),
                            'half_w': v[6] if len(v) > 6 else '', 'half_h': v[7] if len(v) > 7 else '',
                            'depth_3d': v[8] if len(v) > 8 else ''} for k, v in hb.items()])
    write('enemies.csv', enemies(hb))
    write('collision_matrix.csv', collision_matrix())
    write('player_animations.csv', player_animations())


if __name__ == '__main__':
    main()
