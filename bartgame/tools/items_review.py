"""Capture item art in the real ROM's HUD, inventory and earned reward pose.

python tools/items_review.py OUTDIR [--rom ROM --map LINKER_MAP]
Full inventory is injected for UI inspection. The bomb item-get capture is
obtained by completing the generated plate trial and opening its earned chest.
All screenshots are unmodified native mGBA framebuffers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import probe as P
import critical_path as C
import lift_probe as L
import myst_probe as M


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out');ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--seed',default='0xB4A7');args=ap.parse_args()
    P.MAP=args.map;out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    seed=int(args.seed,0);c=P.boot(rom=args.rom,seed=seed);C.dismiss(c)
    pl=P.sym('gPl');shots=[]
    def snap(name,context):
        P.snap(c,str(out/(name+'.png')));shots.append({'file':name+'.png','context':context})
    # A complete bag exercises the same UI path as normal owned items.
    P.w8(c,pl+8,0x7f);P.w8(c,pl+36,0x0f);P.w8(c,pl+6,2);P.w8(c,pl+7,7);P.w8(c,pl+35,12)
    for name,equipment in (('hud-sword-shield',(1,5,0)),('hud-bomb-candle-cape',(2,3,4)),('hud-bow-cap',(6,7,5))):
        for i,item in enumerate(equipment):P.w8(c,pl+9+i,item)
        P.run(c,12);snap(name,'full-inventory HUD render fixture')
    P.press(c,'START',2,16);assert C.gstate(c)==4
    snap('inventory-items','actual items menu with all tools owned')
    P.press(c,'R',2,16);snap('inventory-key-items','actual key-items menu with all tools owned')
    # A fresh run earns a real reward, instead of assigning a pose/frame.
    c=P.boot(rom=args.rom,seed=seed);C.dismiss(c);w=C.world(c);P.enter_forest(c)
    cell=w['key_cell'][0];L.warp(c,cell,next(i for i,g in enumerate(w['cells'][cell]['gate']) if g))
    assert C.earn_trial(c,claim=False),'plate trial did not complete'
    chest=M.tiles_of(c,lambda m:m['type']=='CHEST');assert chest
    tx,ty=chest[0];C.teleport(c,tx*16+8,(ty+1)*16+14)
    c.set_keys(P.key(c,'UP'))
    for _ in range(60):
        c.run_frame()
        if P.actor(c,0)['state']==6:break
    c.clear_keys(P.key(c,'UP'))
    assert P.actor(c,0)['state']==6,'earned chest did not begin item-get'
    P.run(c,12);snap('earned-blightseeds','bomb reward earned by stepping on trial plates and opening its chest')
    report={'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),'seed':hex(seed),
            'emulator':'mGBA 0.10.5','method':'native frames; full-inventory UI fixture plus actual earned item-get','captures':shots}
    (out/'items.json').write_text(json.dumps(report,indent=2))
    print('PASS: %d native UI and item-get captures'%len(shots))


if __name__=='__main__':main()
