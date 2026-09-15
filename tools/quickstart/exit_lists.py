"""Every room's exit list, read from src/data/transitions.c as the build sees it.

This is the QUICKSTART view: the file is full of

    #ifdef QUICKSTART
    const Transition gExitList_Foo[] = { ...our rows... };
    #else
    const Transition gExitList_Foo[] = { ...vanilla rows... };
    #endif

so the conditionals have to be resolved on the raw text BEFORE anything is
parsed, or a sweep sees two definitions of the same list and silently keeps
the wrong one. A tool that reports on vanilla rows we deleted is worse than
no tool - it reports doors that do not exist in the ROM we ship.

Exposes:
    LISTS[list_name]  -> [(warp, sx, sy, ex, ey, shape, destArea, destRoom)]
    BY_ROOM[room]     -> the same rows, keyed by the room they belong to
    OWNER[room]       -> the AREA_* name that room lives in
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = open(os.path.join(ROOT, 'src', 'data', 'transitions.c')).read()


def _resolve(text, defined=('QUICKSTART',)):
    """Keep only the lines a compile with QUICKSTART defined would keep."""
    out = []
    stack = []  # each entry: (this_branch_live, any_branch_taken, parent_live)
    for line in text.split('\n'):
        s = line.strip()
        m = re.match(r'#\s*(ifdef|ifndef|if|else|elif|endif)\b\s*(.*)', s)
        if m:
            kind, rest = m.group(1), m.group(2).strip()
            parent = stack[-1][0] if stack else True
            if kind in ('ifdef', 'ifndef', 'if'):
                if kind == 'ifdef':
                    live = rest in defined
                elif kind == 'ifndef':
                    live = rest not in defined
                else:
                    # `#if defined(X)` and friends; anything else stays live so
                    # an unknown condition never silently deletes rows.
                    dm = re.match(r'defined\s*\(?\s*(\w+)\s*\)?$', rest)
                    live = (dm.group(1) in defined) if dm else True
                stack.append([live and parent, live, parent])
            elif kind == 'else':
                if stack:
                    e = stack[-1]
                    e[0] = (not e[1]) and e[2]
            elif kind == 'elif':
                if stack:
                    e = stack[-1]
                    e[0] = False  # only used alongside conditions we don't model
            else:
                if stack:
                    stack.pop()
            continue
        if all(e[0] for e in stack):
            out.append(line)
    return '\n'.join(out)


SRC = _resolve(RAW)
SRC = re.sub(r'/\*.*?\*/', '', SRC, flags=re.S)
SRC = re.sub(r'//[^\n]*', '', SRC)

ROW = re.compile(
    r'\{\s*(WARP_TYPE_\w+)\s*,\s*(-?(?:0x)?[0-9a-fA-F]+)\s*,\s*(-?(?:0x)?[0-9a-fA-F]+)\s*,'
    r'\s*(-?(?:0x)?[0-9a-fA-F]+)\s*,\s*(-?(?:0x)?[0-9a-fA-F]+)\s*,\s*(\w+)\s*,'
    r'\s*(AREA_\w+)\s*,\s*(ROOM_\w+)')


def _num(tok):
    return int(tok, 16) if tok.lower().startswith(('0x', '-0x')) else int(tok)


LISTS = {}
for m in re.finditer(r'const Transition (gExitList_\w+)\[\]\s*=\s*\{(.*?)\n\};', SRC, re.S):
    LISTS[m.group(1)] = [(w, _num(a), _num(b), _num(c), _num(d), sh, ar, rm)
                         for w, a, b, c, d, sh, ar, rm in ROW.findall(m.group(2))]

# gExitLists[] carries the area each per-area table belongs to as a comment,
# which _resolve() has not stripped yet - read it from the raw text.
_AREA_OF_TABLE = {}
_m = re.search(r'const Transition\* const\* const gExitLists\[\]\s*=\s*\{(.*?)\n\};', RAW, re.S)
if _m:
    for area, table in re.findall(r'/\*(AREA_\w+)\*/\s*(gExitLists_\w+)', _m.group(1)):
        _AREA_OF_TABLE.setdefault(table, area)

BY_ROOM = {}
OWNER = {}
for m in re.finditer(r'const Transition\* const (gExitLists_\w+)\[\]\s*=\s*\{(.*?)\n\};', SRC, re.S):
    table, body = m.group(1), m.group(2)
    area = _AREA_OF_TABLE.get(table)
    for room, listname in re.findall(r'\[(ROOM_\w+)\]\s*=\s*(gExitList_\w+)', body):
        BY_ROOM[room] = LISTS.get(listname, [])
        if area:
            OWNER[room] = area


def area_doors(room):
    """(destArea, destRoom) for every WARP_TYPE_AREA door this room owns."""
    return [(r[6], r[7]) for r in BY_ROOM.get(room, []) if r[0] == 'WARP_TYPE_AREA']


if __name__ == '__main__':
    print(f'{len(LISTS)} exit lists, {len(BY_ROOM)} rooms wired')
    for r in ('ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD', 'ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH'):
        print(f'\n{r}  ({OWNER.get(r)})')
        for row in BY_ROOM.get(r, []):
            print('   ', row)
