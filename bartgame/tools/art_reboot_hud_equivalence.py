"""Compare actual packed vitals pixels before/after the HUD span optimization.

Values are disclosed display fixtures. Real title Start and pause controls
exercise normal rendering and shared text-pool restoration. The comparison
reads hardware BG0 entries, all36 displayed4bpp tiles and their live palette;
no screenshot or renderer-private pixels are substituted for GPU output.
"""
import argparse
import hashlib
import json
from pathlib import Path
import bloom_probe as B
import critical_path as C
import probe as P


def variants():
    rows=[]
    for hp in (0,1,3,4,7,8,15,16,22,23,24):rows.append((hp,24,0,0))
    for hp in (0,4,8,39,40,52,79,80):rows.append((hp,80,999,255))
    for gilt in (0,1,9,10,99,100,999,65535):rows.append((24,24,gilt,255))
    for keys in (0,1,9,10,99,255):rows.append((24,24,999,keys))
    return rows


def memory(c,address,n):return bytes(P.r8(c,address+i) for i in range(n))


def panel(c):
    # Canvas metadata locates what is mapped, not a hardcoded source address.
    canvas=B.static_symbol('sPurse');tile=P.r16(c,canvas)&65535
    tw,th=P.r8(c,canvas+2),P.r8(c,canvas+3)
    assert (tw,th)==(12,3),(tw,th)
    entries=b''.join(memory(c,0x0600B800+y*64,tw*2) for y in range(th))
    bank=int.from_bytes(entries[:2],'little')>>12
    return entries+memory(c,0x06008000+tile*32,tw*th*32)+memory(c,0x05000000+bank*32,32)


def sample(directory):
    directory=Path(directory);rom=directory/'bartgame.gba'
    P.MAP=str(directory/'bartgame.map');P._syms=None
    c=P.boot(rom=str(rom),seed=0xB4A7);C.dismiss(c);P.run(c,24)
    pl=P.sym('gPl');rows=[]
    for index,values in enumerate(variants()):
        hp,hpmax,gilt,keys=values
        for off,val in ((0,hp),(2,hpmax),(4,gilt)):P.w16(c,pl+off,val)
        P.w8(c,pl+6,keys);P.run(c,8)
        raw=panel(c);rows.append({'name':'values-%02d'%index,'values':list(values),'data':raw})
    P.press(c,'START',2,16);assert C.gstate(c)==4
    P.press(c,'R',2,16);P.press(c,'R',2,24)
    P.press(c,'START',2,24);assert C.gstate(c)==1
    rows.append({'name':'after shared pause/map text pool','values':list(variants()[-1]),'data':panel(c)})
    return hashlib.sha256(rom.read_bytes()).hexdigest(),rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',default='/workspace/setup/art-reboot-second')
    ap.add_argument('--after',required=True)
    ap.add_argument('--out',default='/workspace/setup/art-reboot-hud-equivalence.json')
    args=ap.parse_args();before_sha,before=sample(args.before);after_sha,after=sample(args.after)
    checks=[]
    for a,b in zip(before,after):
        assert a['name']==b['name'] and a['values']==b['values']
        ok=a['data']==b['data']
        checks.append({'name':a['name'],'values':a['values'],'passed':ok,
                       'bytes_compared':len(a['data']),
                       'before_sha256':hashlib.sha256(a['data']).hexdigest(),
                       'after_sha256':hashlib.sha256(b['data']).hexdigest()})
        print(('PASS' if ok else 'FAIL'),a['name'],a['values'],flush=True)
    passed=sum(c['passed'] for c in checks)
    report={'method':__doc__.strip(),'emulator':'mGBA0.10.5','before_rom_sha256':before_sha,
            'rom_sha256':after_sha,'passed':passed,'total':len(checks),'checks':checks}
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d'%('PASS' if passed==len(checks) else 'FAIL',passed,len(checks)))
    return int(passed!=len(checks))


if __name__=='__main__':raise SystemExit(main())
