"""Exercise Bloom's sprite budget and icon cache in the actual mGBA ROM.

All 25 forest cells across three seeds, required and optional mysteries,
menus, shop, bow and return-mouth allocations are exercised. Selected rooms
also repeatedly change inventory pages and compare the hardware OAM/VRAM
icons and per-icon palettes against their exact ROM frames, including the
selected description. Borrowed actor palettes must be restored on closing.
Debug navigation, full inventory and cleared enemies isolate rendering.

    python tools/bloom_budget.py --out /tmp/bloom-budget.json
"""
import sys,json,hashlib,re,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import probe as P, critical_path as C, lift_probe as L, myst_probe as M
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',default='/tmp/bloom-budget.json')
ap.add_argument('--seeds',nargs='+',default=['0xB4A7','0xDEADBEEF','7'])
args=ap.parse_args()
rows=[];fail=[];checks=[]
rom_hash=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest()
header=Path(P.ROOT,'build/gen/assets.h').read_text()
def define(name):return int(re.search(r'^#define '+name+r' (\d+)$',header,re.M)[1])
ITEMS=[define('F_ICON32_'+n) for n in ('SWORD','SHIELD','BOMBS','LAMP','CLOAK','BOW','HUBCAP')]
KEYS=[define('F_ICON32_'+n) for n in ('HEART_PIECE','KEY','GAUNTLET','RELIC','MAP','ASTROLABE')]

def check(seed,context,ok,detail=''):
    r={'seed':hex(seed),'context':context,'ok':bool(ok),'detail':detail}
    checks.append(r)
    if not ok:fail.append(r)
    print(('PASS' if ok else 'FAIL'),hex(seed),context,detail,flush=True)

def memory(c,at,size):return bytes(c.memory.u8[at+i] for i in range(size))

def sheet(c,index):
    at=P.sym('sheets')+index*12
    return P.r32(c,at),P.r16(c,at+4)&65535,P.r8(c,at+6)

def markers(c,seed,label):
    for name,index in (('sMarksTile',define('SHEET_MARKS')),('sDotsTile',define('SHEET_DOTS'))):
        tile=P.r16(c,adr[name])&65535
        source,count,_=sheet(c,index)
        cache=P.r16(c,L.ssym('sSheetTile')+index*2)&65535
        ok=tile>0 and tile==cache and tile+count<=876 and memory(c,0x06010000+tile*32,count*32)==memory(c,source,count*32)
        check(seed,label+' '+name+' VRAM identity',ok,'tile %d canonical %d'%(tile,cache))

def picture(c,seed,label,frames,cursor):
    entries={}
    for i in range(128):
        at=0x07000000+i*8;a0=P.r16(c,at)&65535;a1=P.r16(c,at+2)&65535;a2=P.r16(c,at+4)&65535
        if (a0&0x0300)==0x0200:continue
        if a0>>14==0 and a1>>14==2:
            entries[(a1&511,a0&255)]=(a2&1023,a2>>12)
    source=P.sym('icon32_exact_tiles')
    palettes=P.sym('icon32_exact_pal')
    expected=[(16+(i%4)*40,24+(i//4)*40,f) for i,f in enumerate(frames)]+[(16,112,frames[cursor])]
    for x,y,frame in expected:
        entry=entries.get((x,y))
        tile,pal=entry if entry is not None else (None,None)
        pixels_ok=tile is not None and memory(c,0x06010000+tile*32,512)==memory(c,source+frame*512,512)
        palette_ok=pal is not None and 0<=pal<8 and memory(c,0x05000200+pal*32,32)==memory(c,palettes+frame*32,32)
        detail='frame %d tile %s palette %s'%(frame,tile,pal)
        check(seed,label+' icon (%d,%d)'%(x,y),pixels_ok,detail)
        check(seed,label+' exact palette (%d,%d)'%(x,y),palette_ok,detail)

def repeat_pages(c,seed,label):
    # Old and new icon frames are intentionally mixed on repeated page
    # changes. Compare final GPU bytes, not the cache implementation's tags.
    for round_ in range(4):
        picture(c,seed,label+' repeat%d items'%round_,ITEMS,0)
        P.press(c,'RIGHT',2,4);picture(c,seed,label+' repeat%d selected item'%round_,ITEMS,1)
        P.press(c,'R',2,6);picture(c,seed,label+' repeat%d keys'%round_,KEYS,0)
        P.press(c,'RIGHT',2,4);picture(c,seed,label+' repeat%d selected key'%round_,KEYS,1)
        P.press(c,'R',2,6);markers(c,seed,label+' repeat%d map'%round_)
        P.press(c,'R',2,6)

adr={n:L.ssym(n) for n in ['sNextTile','sActionTile','sIconTile','sMarksTile','sDotsTile','sArrowTile','sMouthTile']}

def rec(c,seed,context,required=()):
    v={n:P.r16(c,a)&65535 for n,a in adr.items()}
    ok=0<v['sActionTile'] and v['sActionTile']+16<=876 and v['sNextTile']<=876 and all(v[n]>0 for n in required)
    r={'seed':hex(seed),'context':context,'ok':ok,**v}
    rows.append(r)
    check(seed,context,ok,v)
    return r

def inventory(c):
    pl=P.sym('gPl');P.w8(c,pl+8,127);P.w8(c,pl+36,15);P.w8(c,pl+35,20);P.w8(c,pl+7,9)

def menus(c,seed,label,identity=False):
    C.dismiss(c);C.heal(c);C.clear_enemies(c)
    # Menu icons borrow slots0..7, while the Drain keeper's animated orb
    # uses slot14. Compare both CPU colours and the actual GPU palette.
    world_palette=memory(c,P.sym('gPalObj'),8*32)
    P.press(c,'START',2,8)
    if C.gstate(c)!=4:
        check(seed,label+' menu opens',False,'state %d'%C.gstate(c));return
    r=rec(c,seed,label+' items',('sIconTile','sMarksTile','sDotsTile'))
    if identity:repeat_pages(c,seed,label)
    P.press(c,'R',2,6);P.press(c,'R',2,6);rec(c,seed,label+' map');markers(c,seed,label+' map')
    # Building the full map can span video frames. Wait until its work is
    # complete before sending the close pulse, then verify the actual state.
    P.run(c,24)
    for _ in range(3):
        if C.gstate(c)!=4:break
        P.press(c,'START',2,16)
    check(seed,label+' menu closes',C.gstate(c)==1,'state %d'%C.gstate(c))
    restored=memory(c,P.sym('gPalObj'),8*32)==world_palette and memory(c,0x05000200,8*32)==world_palette
    check(seed,label+' borrowed palettes restored',restored)

def extras(c,seed,label):
    C.heal(c);C.clear_enemies(c)
    C.equip_b(c,6);P.w8(c,P.sym('gPl')+25,0);P.press(c,'A',2,4);r=rec(c,seed,label+' bow',('sArrowTile',))
    P.run(c,20);C.equip_b(c,7);P.w8(c,P.sym('gPl')+25,0);P.press(c,'A',2,4);r=rec(c,seed,label+' mouth',('sMouthTile',))

for seed in map(lambda s:int(s,0),args.seeds):
    c=P.boot(seed=seed);C.dismiss(c);inventory(c);rec(c,seed,'drain')
    menus(c,seed,'drain')
    C.teleport(c,4*16+8,7*16+6);P.hold(c,'UP',8);P.press(c,'A',2,30);rec(c,seed,'drain shop');check(seed,'shop opens',P.r8(c,L.ssym('sShopActive')) and P.r8(c,L.ssym('sShopCount'))==3)
    for _ in range(3):P.press(c,'B',2,20)
    C.dismiss(c)
    w=C.world(c)
    for cell,d in enumerate(w['cells']):
        L.warp(c,cell,next(i for i,g in enumerate(d['gate']) if g));inventory(c)
        rec(c,seed,'forest '+str(cell));menus(c,seed,'forest '+str(cell),identity=(seed==0xB4A7 and cell in (2,3)) or (seed==7 and cell in (9,w['goal'])));extras(c,seed,'forest '+str(cell))
        # Interrupt the cap before its return transition; next room's normal
        # transition resets all sprite allocations as it does in gameplay.
    for trial,cell in enumerate(w['key_cell']):
        L.warp(c,cell,next(i for i,g in enumerate(w['cells'][cell]['gate']) if g))
        assert C.enter_trial(c),'trial entry failed'
        inventory(c);rec(c,seed,'required trial '+str(trial));menus(c,seed,'required trial '+str(trial));extras(c,seed,'required trial '+str(trial))
    cell=next(i for i,d in enumerate(w['cells']) if i not in (w['entry'],w['goal']) and d['role'] not in (1,2,3,7))
    for kind in ('pots','chest','npc','fairy','waves','survive','miniboss','switches','torches','boulders'):
        # This is a controlled room variant, entered through a real mouth.
        ok=M.enter(c,cell,kind,2,2)
        if not ok:
            check(seed,kind+' optional variant entry',False);continue
        inventory(c);rec(c,seed,'optional '+kind);menus(c,seed,'optional '+kind);extras(c,seed,'optional '+kind)
check(0,'ROM remained unchanged during sweep',hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest()==rom_hash)
report={'rom_sha256':rom_hash,'emulator':'mGBA 0.10.5','limit':876,'maximum_next_tile':max(r['sNextTile'] for r in rows),'headroom_tiles':876-max(r['sNextTile'] for r in rows),'contexts':len(rows),'passed':sum(r['ok'] for r in checks),'total':len(checks),'failures':fail,'rows':rows,'checks':checks,'method':'Actual ROM transitions, full inventory fixture, cleared enemies after allocation; repeated menu pages compare hardware OAM/VRAM icons and per-icon palettes against exact ROM frame bytes. Slots0..7 must match their live world colours again after closing.'}
Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
print('RESULT %s %d/%d, %d contexts, maximum %d/%d tiles'%('PASS' if not fail else 'FAIL',report['passed'],report['total'],len(rows),report['maximum_next_tile'],876),flush=True)
sys.exit(bool(fail))
