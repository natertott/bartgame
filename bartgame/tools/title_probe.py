"""Check the real Mode3 title and its transitions in mGBA.

python tools/title_probe.py --out /workspace/art-review/title

All PNGs are unmodified native240x160 framebuffers. The save fixture goes
through the normal death/save path; the win fixture collects a placed Grail.
No title art, title pose or framebuffer is injected by this probe.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np
from PIL import Image
import probe as P
import critical_path as C
import lift_probe as L
import save_probe as S
import wood_probe as W

WIDTH,HEIGHT=240,160
VRAM=0x06000000
IO=0x04000000
OAM=0x07000000
checks=[]


def check(name,ok,detail=''):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})
    print(('PASS' if ok else 'FAIL'),name,detail,flush=True)


def u16(c,addr):return P.r16(c,addr)&65535


def memory(c,addr,size):return bytes(P.r8(c,addr+i) for i in range(size))


def definitions(path):
    return {name:int(value,0) for name,value in re.findall(
        r'^#define\s+(\w+)\s+(0x[0-9a-fA-F]+|\d+)\b',Path(path).read_text(),re.M)}


def source(c,rom,name,size):
    offset=P.sym(name)-0x08000000
    return rom[offset:offset+size]


def picture(raw,replicate=True):
    pixels=np.frombuffer(raw,dtype='<u2').reshape(HEIGHT,WIDTH)
    channels=np.stack((pixels&31,(pixels>>5)&31,(pixels>>10)&31),axis=-1)
    channels=(channels<<3)|(channels>>2) if replicate else channels<<3
    return Image.fromarray(channels.astype('uint8'))


def visible_objects(c):
    sizes=(((8,8),(16,16),(32,32),(64,64)),
           ((16,8),(32,8),(32,16),(64,32)),
           ((8,16),(8,32),(16,32),(32,64)))
    result=[]
    for i in range(128):
        at=OAM+i*8;a0=u16(c,at);a1=u16(c,at+2);a2=u16(c,at+4)
        if a0&0x0300==0x0200:continue
        shape=a0>>14;size=a1>>14
        if shape==3:continue
        w,h=sizes[shape][size];x=a1&511;y=a0&255
        if x>=256:x-=512
        if y>=160:y-=256
        if x>=WIDTH or x+w<=0 or y>=HEIGHT or y+h<=0:continue
        result.append({'index':i,'x':x,'y':y,'w':w,'h':h,'tile':a2&1023})
    return result


def frame(c):return c.bg_video.to_pil().convert('RGB')


def settled_title(c,expected,frames=180):
    # Match the actual framebuffer as well as OAM: the emulator returns at
    # VBlank, so the new shadow-OAM state may precede its displayed frame.
    for _ in range(frames):
        c.run_frame()
        if C.gstate(c)==0 and P.r8(c,P.sym('gFadeLevel'))==0:
            shown=frame(c).tobytes()
            for mode,image in expected.items():
                if shown==image.tobytes():return mode
    return None


def wait_prompt(c,frames=100):
    for _ in range(frames):
        c.run_frame()
        if P.r8(c,P.sym('gFadeLevel'))==0 and visible_objects(c):
            P.run(c,2)
            if visible_objects(c):return True
    return False


def bitmap_checks(c,raw,label):
    check(label+' uses Mode3 and BG2',u16(c,IO)&0x0F07==0x0403,hex(u16(c,IO)))
    # BG2 affine registers are write-only on the GBA (debug reads return
    # open bus). Exact framebuffer comparison verifies the effective
    # identity transform rather than asserting unsupported readbacks.
    check(label+' VRAM equals every source RGB555 word',memory(c,VRAM,len(raw))==raw)
    objects=visible_objects(c)
    check(label+' bitmap-safe OBJ allocations',all(o['tile']>=512 for o in objects),str(objects))
    check(label+' keeps name and baked subtitle unobscured',all(o['y']>=120 for o in objects),str(objects))


def masked_frame_check(c,expected,label):
    got=np.asarray(frame(c));want=np.asarray(expected)
    # Save-choice text and the cursor animate within this lower-water band.
    # All image pixels above it and along both sides must remain source art.
    mask=np.ones((HEIGHT,WIDTH),dtype=bool);mask[120:152,64:160]=False
    same=np.all(got==want,axis=-1)
    check(label+' framebuffer preserves unobscured reference',bool(same[mask].all()),
          str(int((~same&mask).sum()))+' differing pixels')


def start(c,seed=None):
    if seed is not None:
        P.w16(c,P.sym('gSeedOverride'),seed&65535)
        P.w16(c,P.sym('gSeedOverride')+2,seed>>16)
    P.press(c,'START',3,70)
    for _ in range(1800):
        if C.gstate(c)!=0:break
        c.run_frame()
    C.dismiss(c);P.run(c,32)
    return C.gstate(c)==1


def world_checks(c,rom,defs,label):
    check(label+' returns to Mode0',u16(c,IO)&7==0,hex(u16(c,IO)))
    check(label+' restores world display layers',u16(c,IO)&0x0700==0x0700)
    count=defs['HUD_TILE_COUNT'];base=defs['HUD_TILE_BASE']
    check(label+' restores HUD atlas',memory(c,VRAM+0x8000+base*32,count*32)==source(c,rom,'hud_tiles',count*32))
    ui_base=base+count;ui_count=defs['UI_TILE_COUNT']
    check(label+' restores UI frame atlas',memory(c,VRAM+0x8000+ui_base*32,ui_count*32)==source(c,rom,'ui_tiles',ui_count*32))
    got=memory(c,0x05000200,512);want=source(c,rom,'pal_obj',512)
    dynamic=set(range(defs['PAL_OBJ_PORTRAIT']*16,(defs['PAL_OBJ_PORTRAIT']+1)*16))
    # The Drain keeper animates two palette entries in her glowing orb.
    glow=defs['PAL_OBJ_GATEKEEPER']*16+defs['ORB_GLOW_INDEX']
    dynamic.update((glow,glow+1))
    fixed=[i for i in range(256) if i not in dynamic]
    check(label+' restores fixed OBJ colours',all(got[i*2:i*2+2]==want[i*2:i*2+2] for i in fixed),
          'dialogue portraits and the keeper orb have dynamic colours')
    # BLDY is also write-only; BLDCNT's readable mode bits determine
    # whether the title's brightness effect remains enabled.
    check(label+' disables title brightness fade',u16(c,IO+0x50)&0x00C0==0,hex(u16(c,IO+0x50)))
    hero=P.sym('sheets')+defs['SHEET_HERO']*12
    hw,hh=P.r8(c,hero+10),P.r8(c,hero+11)
    check(label+' has visible native32px Bloom canvas',hw==hh==32 and any(o['tile']==0 and o['w']==hw and o['h']==hh for o in visible_objects(c)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',default=P.ROM);parser.add_argument('--map',default=P.MAP)
    parser.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    parser.add_argument('--out',default='/workspace/setup/title-review-after')
    args=parser.parse_args();P.MAP=args.map;P._syms=None
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rom=Path(args.rom).read_bytes();defs=definitions(args.assets_header);shots=[]
    def snap(c,name,context):
        P.snap(c,str(out/(name+'.png')));shots.append({'file':name+'.png','context':context})
    c=P.boot(rom=args.rom,start=False,frames=48)
    raw=source(c,rom,'title_bitmap',WIDTH*HEIGHT*2)
    check('title asset is complete RGB555 bitmap',len(raw)==76800 and defs['TITLE_WIDTH']==WIDTH and defs['TITLE_HEIGHT']==HEIGHT)
    check('native title uses at most48 shared RGB555 inks',len(set(np.frombuffer(raw,dtype='<u2')))<=48,str(len(set(np.frombuffer(raw,dtype='<u2')))))
    choices={'replicated':picture(raw,True),'shifted':picture(raw,False)}
    conversion=settled_title(c,choices)
    check('unobscured framebuffer equals entire native title',conversion is not None,str(conversion))
    expected=choices[conversion or 'replicated'];bitmap_checks(c,raw,'fresh title')
    snap(c,'title-clean','actual fresh title during prompt-off blink; no image or pose injection')
    check('fresh title shows blinking prompt',wait_prompt(c))
    bitmap_checks(c,raw,'title prompt');snap(c,'title-press-start','actual fresh title with the Press Start OBJ')
    check('Start begins a new run',start(c,0xB4A7))
    check('new run wakes in Drain',C.area(c)==0)
    check('new run respects selected seed',P.r32(c,P.sym('gWorld'))==0xB4A7)
    world_checks(c,rom,defs,'new run');snap(c,'new-game-drain','actual world after leaving full-colour title')
    P.enter_forest(c);C.dismiss(c);P.run(c,32)
    check('forest transition remains playable',C.gstate(c)==1 and C.area(c)==1)
    world_checks(c,rom,defs,'forest');snap(c,'forest-after-title','actual generated forest after leaving title')
    P.press(c,'START',3,64)
    check('pause opens after title transition',C.gstate(c)==4)
    snap(c,'pause-after-title','actual pause page after full-colour title and forest transition')
    P.press(c,'R',3,24);P.press(c,'R',3,48)
    check('map remains Mode0 after title',C.gstate(c)==4 and u16(c,IO)&7==0)
    P.press(c,'START',3,48)
    check('pause closes to live forest',C.gstate(c)==1)
    pl=P.sym('gPl');P.w16(c,pl+4,37);P.w8(c,pl+6,2);P.w8(c,pl+7,5)
    version,saved=S.save_on_death(c);world=C.world(c);items=P.r8(c,pl+8)
    check('save fixture uses real death/save record',version==2 and len(saved)>500)
    c.reset();P.run(c,80)
    check('saved title recognises record',P.r8(c,L.ssym('sTitleHasSave'))==1)
    check('saved title defaults to Continue',P.r8(c,L.ssym('sTitleCursor'))==0)
    bitmap_checks(c,raw,'saved title');masked_frame_check(c,expected,'saved title')
    snap(c,'title-continue','actual saved-run title with Continue selected')
    P.press(c,'DOWN',3,24)
    check('Down selects New Game',P.r8(c,L.ssym('sTitleCursor'))==1)
    snap(c,'title-new-game','actual saved-run title with New Game selected')
    P.press(c,'UP',3,24)
    check('Up returns selection to Continue',P.r8(c,L.ssym('sTitleCursor'))==0)
    check('Continue enters the saved run',start(c))
    check('Continue keeps saved inventory',P.r16(c,pl+4)==37 and P.r8(c,pl+6)==2 and P.r8(c,pl+7)==5 and P.r8(c,pl+8)==items)
    continued=C.world(c)
    check('Continue keeps saved maze',continued==world)
    check('Continue wakes in Drain',C.area(c)==0)
    world_checks(c,rom,defs,'continued run');snap(c,'continue-drain','actual saved run after Continue')
    c.reset();P.run(c,80);P.press(c,'DOWN',3,24)
    check('New Game selection survives redraw',P.r8(c,L.ssym('sTitleCursor'))==1)
    check('New Game starts from saved title',start(c,0xCC55))
    check('New Game clears old inventory/resources',P.r16(c,pl+4)==0 and P.r8(c,pl+6)==0 and P.r8(c,pl+7)==0)
    check('New Game selects a new maze seed',P.r32(c,P.sym('gWorld'))==0xCC55)
    world_checks(c,rom,defs,'fresh run after save')
    # Trigger the real Grail pickup/win path, without requiring a boss run.
    a=P.sym('gActors');slot=next(i for i in range(1,96) if P.r8(c,a+i*64)==0)
    x,y=P.player_pos(c);W.put_actor(c,slot,4,6,x,y,2,timer=10)
    at=a+slot*64;P.w8(c,at+36,defs['SHEET_PICK32']);P.w8(c,at+37,defs['F_PICK32_GRAIL'])
    pick=P.sym('sheets')+defs['SHEET_PICK32']*12
    P.w8(c,at+42,P.r8(c,pick+10));P.w8(c,at+43,P.r8(c,pick+11));P.w16(c,at+44,P.r16(c,L.ssym('sPickTile')))
    P.w8(c,at+46,P.r8(c,P.sym('pick32_frame_pal')+defs['F_PICK32_GRAIL']));P.run(c,4)
    check('Grail fixture enters real win path',C.gstate(c)==6)
    P.run(c,140);P.press(c,'START',3,80)
    check('win screen returns to title',C.gstate(c)==0)
    bitmap_checks(c,raw,'returned title');masked_frame_check(c,expected,'returned title')
    snap(c,'title-after-win','actual return to title through the win screen Start action')
    check('returned title Continue remains usable',start(c))
    world_checks(c,rom,defs,'second title round trip')
    for capture in shots:
        with Image.open(out/capture['file']) as im:assert im.size==(WIDTH,HEIGHT)
    report={'rom_sha256':hashlib.sha256(rom).hexdigest(),'title_bitmap_sha256':hashlib.sha256(raw).hexdigest(),
            'emulator':'mGBA 0.10.5','rgb555_framebuffer_expansion':conversion,
            'method':'Native unmodified240x160 framebuffers. Title and choices use real controls; fixture inventory is saved via death, and the win-return fixture collects a placed Grail.',
            'passed':sum(c['passed'] for c in checks),'total':len(checks),'checks':checks,'captures':shots}
    (out/'title.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d'%('PASS' if report['passed']==report['total'] else 'FAIL',report['passed'],report['total']))
    return int(report['passed']!=report['total'])


if __name__=='__main__':raise SystemExit(main())
