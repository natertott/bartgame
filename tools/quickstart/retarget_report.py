"""Every transition this mode changes, next to what vanilla does there.

The user, after finding two rooms that "transport you somewhere weird":
"Please provide the list of every retargeted transition and its vanilla
destination." This is that list, generated rather than written, so it
cannot drift from src/data/transitions.c.

Method: resolve the file's #ifdef QUICKSTART blocks twice - once as the
build sees them, once as vanilla - parse both into exit lists, and report
every list whose rows differ. Each row is classed as:

  BLOCKED    vanilla has a row here, this build has none
  ADDED      this build has a row vanilla does not
  RETARGETED same slot, different destination room
  MOVED      same destination room, different landing coordinates

MOVED is the class worth knowing about: it is the one that looks like a
bug in play (you take a door and arrive somewhere odd) while looking like
nothing in a diff of destinations.

Usage: python3 tools/quickstart/retarget_report.py [--md]
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SRC = os.path.join(ROOT, 'src/data/transitions.c')


def resolve(defined):
    out, stack = [], []
    for l in open(SRC).read().split('\n'):
        t = l.strip()
        if t.startswith('#ifdef QUICKSTART'):
            stack.append(defined)
            continue
        if t.startswith('#ifndef QUICKSTART'):
            stack.append(not defined)
            continue
        if t.startswith('#else') and stack:
            stack[-1] = not stack[-1]
            continue
        if t.startswith('#endif') and stack:
            stack.pop()
            continue
        if all(stack):
            out.append(l)
    return '\n'.join(out)


def lists(text):
    d = {}
    for m in re.finditer(r'const Transition (gExitList_\w+)\[\]\s*=\s*\{(.*?)\n\};', text, re.S):
        body = re.sub(r'//[^\n]*', '', m.group(2))
        rows = []
        for r in re.finditer(r'\{\s*(WARP_TYPE_\w+)\s*,([^{}]*?)\}', body):
            f = [x.strip() for x in r.group(2).split(',')]
            # startX, startY, endX, endY, shape, destArea, destRoom, ...
            if len(f) < 7:
                continue
            rows.append({'warp': r.group(1), 'sx': f[0], 'sy': f[1], 'ex': f[2], 'ey': f[3],
                         'shape': f[4], 'area': f[5], 'room': f[6]})
        d.setdefault(m.group(1), []).append(rows)
    return {k: v[-1] for k, v in d.items()}


def key(r):
    return (r['warp'], r['sx'], r['sy'], r['shape'])


def main():
    md = '--md' in sys.argv
    qs, van = lists(resolve(True)), lists(resolve(False))
    findings = []
    for name in sorted(set(qs) | set(van)):
        a, b = qs.get(name, []), van.get(name, [])
        if a == b:
            continue
        bk = {key(r): r for r in b}
        ak = {key(r): r for r in a}
        for k in sorted(set(bk) | set(ak), key=str):
            x, y = ak.get(k), bk.get(k)
            if x == y:
                continue
            if y and not x:
                findings.append((name, 'BLOCKED', k, '%s/%s @ %s,%s' % (y['area'], y['room'], y['ex'], y['ey']), '-'))
            elif x and not y:
                findings.append((name, 'ADDED', k, '-', '%s/%s @ %s,%s' % (x['area'], x['room'], x['ex'], x['ey'])))
            elif x['room'] != y['room'] or x['area'] != y['area']:
                findings.append((name, 'RETARGETED', k, '%s/%s' % (y['area'], y['room']), '%s/%s' % (x['area'], x['room'])))
            else:
                findings.append((name, 'MOVED', k, '%s/%s @ %s,%s' % (y['area'], y['room'], y['ex'], y['ey']),
                                 '%s/%s @ %s,%s' % (x['area'], x['room'], x['ex'], x['ey'])))
    order = {'MOVED': 0, 'RETARGETED': 1, 'BLOCKED': 2, 'ADDED': 3}
    findings.sort(key=lambda f: (order[f[1]], f[0]))
    if md:
        print('| class | exit list | door (warp, x, y) | vanilla | this build |')
        print('|---|---|---|---|---|')
        for name, cls, k, v, q in findings:
            print('| %s | `%s` | %s %s,%s | %s | %s |' % (cls, name.replace('gExitList_', ''),
                                                          k[0].replace('WARP_TYPE_', ''), k[1], k[2], v, q))
    else:
        for cls in ('MOVED', 'RETARGETED', 'BLOCKED', 'ADDED'):
            rows = [f for f in findings if f[1] == cls]
            print('\n=== %s (%d) ===' % (cls, len(rows)))
            for name, _c, k, v, q in rows:
                print('  %-46s %s %s,%s' % (name.replace('gExitList_', ''), k[0].replace('WARP_TYPE_', ''), k[1], k[2]))
                print('       vanilla: %s' % v)
                print('       ours   : %s' % q)
    print('\n%d differing row(s) across %d exit list(s)' %
          (len(findings), len({f[0] for f in findings})))
    return 0


if __name__ == '__main__':
    sys.exit(main())
