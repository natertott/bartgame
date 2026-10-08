"""Where the CPU goes in a room: sample the program counter every N
instructions over F frames and attribute each sample to a function
(game.o's statics rebased onto the link, plus the map's globals).

    python3 tools/quickstart/pc_profile.py SITE <site> <KIND> [--frames 30] [--every 97]
    python3 tools/quickstart/pc_profile.py REGION <row> [--frames 30]
"""
import os, sys, subprocess, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario as S
import callrom as C
args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
FRAMES = int(args[args.index('--frames') + 1]) if '--frames' in args else 30
EVERY = int(args[args.index('--every') + 1]) if '--every' in args else 97

def symbols():
    base = C._game_text_base()
    syms = []
    for line in subprocess.run(['arm-none-eabi-nm', 'build/USA/src/game.o'], capture_output=True, text=True).stdout.split('\n'):
        p = line.split()
        if len(p) == 3 and p[1] in ('t', 'T'):
            syms.append((int(p[0], 16) + base, 'game:' + p[2]))
    for line in open('build/USA/tmc.map'):
        p = line.split()
        if len(p) == 2 and p[0].startswith('0x08') and not p[1].startswith('.'):
            try:
                syms.append((int(p[0], 16), p[1]))
            except ValueError:
                pass
    syms.sort()
    return syms

def profile(c, frames=FRAMES, every=EVERY):
    syms = symbols(); addrs = [a for a, _ in syms]
    hits = collections.Counter(); total = 0
    cpu = c.cpu._native
    for _ in range(frames):
        start = c.frame_counter
        n = 0
        while c.frame_counter == start:
            c.step()
            n += 1
            if n % every == 0:
                pc = cpu.gprs[15] & 0xFFFFFFFF
                i = bisect.bisect_right(addrs, pc) - 1
                name = syms[i][1] if i >= 0 and pc >= 0x08000000 else ('IWRAM/BIOS %#x' % (pc & 0xFFFF0000))
                hits[name] += 1; total += 1
    return hits, total

if __name__ == '__main__':
    mode = args[0]
    if mode == 'SITE':
        c = S.boot(ROM, S.KINDS['SITE'], int(args[1]), S.EVENTS.index(args[2]), 0, kit=2, diff=3, frames=300)
    else:
        c = S.boot(ROM, S.KINDS['REGION'], int(args[1]), 0, kit=2, diff=3, frames=300)
    hits, total = profile(c)
    for name, n in hits.most_common(30):
        print('%6.1f%%  %s' % (100.0 * n / total, name))
