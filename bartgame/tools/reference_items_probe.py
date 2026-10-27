"""Review the imported reference items in the actual ROM under mGBA.

python tools/reference_items_probe.py OUT [--rom ROM --map MAP --assets-header H]
Use --capture-only for a matched older ROM before the reference imports.

PNGs are unmodified240x160 framebuffers. Full inventory, debug positioning,
cleared actors, shield-upgrade ownership and the ground pickup display are
explicit render fixtures. Tool poses and the earned reward run from actual
button actions. No animation pose or frame is assigned.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from PIL import Image
import probe as P
import critical_path as C
import lift_probe as L
import myst_probe as M
import bloom_probe as B
import bloom_review as R
import wood_probe as W

FACES=('n','e','s','w')
EQUIP_ICONS={1:'SWORD',2:'BOMBS',3:'LAMP',4:'CLOAK',5:'SHIELD',6:'BOW',7:'HUBCAP'}
ITEM_PAGE=('SWORD','SHIELD','BOMBS','LAMP','CLOAK','BOW','HUBCAP')
KEY_PAGE=('HEART_PIECE','KEY','GAUNTLET','RELIC','MAP','ASTROLABE')
PICKUPS=('HEART','GILT','BOMB_PICKUP','GILT_BIG','KEY','RELIC','GRAIL','ARROW1','ARROW5','ARROW10')
checks=[]


def definitions(path):
    return {k:int(v,0) for k,v in re.findall(r'^#define\s+(\w+)\s+(0x[0-9a-fA-F]+|\d+)\b',Path(path).read_text(),re.M)}


def check(name,ok,detail=''):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})
    print(('PASS' if ok else 'FAIL'),name,detail,flush=True)


def data(c,at,n):return bytes(P.r8(c,at+i) for i in range(n))


def sh(c,defs,name):
    at=P.sym('sheets')+defs['SHEET_'+name]*12
    return {'source':P.r32(c,at),'tiles':P.r16(c,at+4)&65535,'frame_tiles':P.r8(c,at+6),
            'pal':P.r8(c,at+9),'w':P.r8(c,at+10),'h':P.r8(c,at+11)}


def bank(c,table,frame):return P.r8(c,P.sym(table)+frame)


def object_at(c,x=None,y=None,tile=None,size=None):
    return next((o for o in B.oam(c) if (x is None or o['x']==x) and
                 (y is None or o['y']==y) and (tile is None or o['tile']==tile) and
                 (size is None or o['size']==size)),None)


def material_check(c,obj,table,frame,label):
    want=bank(c,table,frame)
    check(label+' uses its material bank',obj is not None and obj['pal']==want,str(obj))
    if obj:
        actual=data(c,0x05000200+obj['pal']*32,32)
        expected=data(c,P.sym('pal_obj')+want*32,32)
        check(label+' material palette is resident',actual==expected)


def sprite_check(c,defs,sheet,frame,obj,label,table=None,exact=False):
    info=sh(c,defs,sheet)
    check(label+' has an actual OAM sprite',obj is not None,str(obj))
    if obj is None:return
    n=info['frame_tiles']*32
    source=P.sym('icon32_exact_tiles')+frame*n if exact else info['source']+frame*n
    check(label+' pixels match source ROM frame',data(c,0x06010000+obj['tile']*32,n)==data(c,source,n))
    if exact:
        expected=data(c,P.sym('icon32_exact_pal')+frame*32,32)
        check(label+' exact icon palette matches',data(c,0x05000200+obj['pal']*32,32)==expected)
        check(label+' exact palette uses menu slots',0<=obj['pal']<8,str(obj['pal']))
    elif table:material_check(c,obj,table,frame,label)


def hud_checks(c,defs,equipment,label,upgrade=False):
    for slot,eq in enumerate(equipment):
        if not eq:continue
        name='SHIELD_UPGRADED' if eq==5 and upgrade else EQUIP_ICONS[eq]
        frame=defs['F_ICON32_'+name]
        obj=object_at(c,x=112+slot*32,y=0,tile=876+slot*16,size=2)
        sprite_check(c,defs,'ICON32',frame,obj,f'{label} HUD slot{slot}','icon32_frame_pal')


def menu_checks(c,defs,names,label,upgrade=False):
    for i,name in enumerate(names):
        if name=='SHIELD' and upgrade:name='SHIELD_UPGRADED'
        frame=defs['F_ICON32_'+name]
        obj=object_at(c,x=16+(i%4)*40,y=24+(i//4)*40,size=2)
        sprite_check(c,defs,'ICON32',frame,obj,f'{label} {name}',exact=True)
    # The description repeats the selected icon and must reuse valid data.
    frame=defs['F_ICON32_'+names[0]]
    obj=object_at(c,x=16,y=112,size=2)
    sprite_check(c,defs,'ICON32',frame,obj,label+' description',exact=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out');ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--seed',default='0xB4A7');ap.add_argument('--capture-only',action='store_true')
    args=ap.parse_args();P.MAP=args.map;P._syms=None;defs=definitions(args.assets_header)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);seed=int(args.seed,0)
    digest=hashlib.sha256(Path(args.rom).read_bytes()).hexdigest();shots=[]
    c=P.boot(rom=args.rom,seed=seed);C.dismiss(c);pl=P.sym('gPl')
    def snap(name,context):
        P.snap(c,str(out/(name+'.png')));shots.append({'file':name+'.png','context':context})
    def bag(upgrade=False):
        P.w8(c,pl+8,0x7f);P.w8(c,pl+36,0x0f|(0x10 if upgrade else 0));P.w8(c,pl+6,2)
        P.w8(c,pl+7,7);P.w8(c,pl+35,12)
    bag()
    groups=(('hud-sword-shield',(1,5,0)),('hud-bomb-lantern-cape',(2,3,4)),('hud-bow-cap',(6,7,5)))
    for name,equipment in groups:
        for i,eq in enumerate(equipment):P.w8(c,pl+9+i,eq)
        P.run(c,12);snap(name,'full-inventory HUD render fixture in the actual Drain')
        if not args.capture_only:hud_checks(c,defs,equipment,name)
    world_palette=data(c,P.sym('gPalObj'),512)
    P.press(c,'START',3,48);check('Start opens the real inventory',C.gstate(c)==4)
    snap('inventory-items','real items page; full ownership render fixture')
    if not args.capture_only:menu_checks(c,defs,ITEM_PAGE,'items page')
    def turn_page(want):
        # A map redraw can span several video frames before input is read.
        # Wait for its completion before sending another short button pulse.
        for _ in range(4):
            P.run(c,96);P.press(c,'R',3,96)
            if P.r8(c,L.ssym('sPage'))==want:return True
        return False
    for cycle in range(3):
        check('R opens key items page'+str(cycle),turn_page(1))
        if cycle==0:snap('inventory-key-items','real key-items page; full ownership render fixture')
        if not args.capture_only:menu_checks(c,defs,KEY_PAGE,'key page'+str(cycle))
        check('R opens map page'+str(cycle),turn_page(2))
        check('R returns to items page'+str(cycle),turn_page(0))
        if not args.capture_only:menu_checks(c,defs,ITEM_PAGE,'returned items'+str(cycle))
    P.press(c,'START',3,32);check('inventory closes to live Drain',C.gstate(c)==1)
    P.run(c,12)
    if not args.capture_only:
        hud_checks(c,defs,groups[-1][1],'HUD after exact-palette menu')
        # The keeper's last two orb colours animate during live Drain play.
        # All remaining bytes must survive the menu's borrowed palettes.
        restored=data(c,P.sym('gPalObj'),512)
        dynamic={14*32+i for i in range(28,32)}
        check('menu restores all non-animated world palette bytes',
              all(a==b for i,(a,b) in enumerate(zip(restored,world_palette)) if i not in dynamic))
    # The actual merchant draws the same imported16px assets as equipped tools.
    C.teleport(c,4*16+8,7*16+6);P.hold(c,'UP',8);P.press(c,'A',3,40)
    shop=P.r8(c,L.ssym('sShopActive'))
    check('the actual Peddler shop opens',shop==1)
    if shop:
        snap('shop-items','actual Peddler shop with imported heart, bomb and arrow-bundle sprites')
        if not args.capture_only:
            for i,name in enumerate(('HEART','BOMBS','ARROW10')):
                frame=defs['F_ITEMS_'+name];obj=object_at(c,x=27,y=(9+i*3)*8,size=1)
                sprite_check(c,defs,'ITEMS',frame,obj,'shop '+name,'items_frame_pal')
        P.press(c,'B',3,48)
    C.dismiss(c);P.enter_forest(c);C.dismiss(c);world=C.world(c)
    spot=R.natural_spot(c,0,0);assert spot,'no natural clearing for item review'
    def place(facing=0,equipment=(0,5,0),upgrade=False):
        B.reset_player(c,*spot,facing=facing,equipment=equipment);bag(upgrade);P.run(c,96)
    # Display all ten pickup types using real pickup actors on unchanged floor.
    place(equipment=(0,1,5));A=P.sym('gActors');pick=sh(c,defs,'PICK32');base=P.r16(c,L.ssym('sPickTile'))&65535
    records=[]
    for i,name in enumerate(PICKUPS):
        frame=defs['F_PICK32_'+name];x=spot[0]+((i%5)-2)*32;y=spot[1]+(-32 if i<5 else 32)
        slot=i+1;W.put_actor(c,slot,4,i,x,y,2,timer=1);at=A+slot*64
        P.w8(c,at+36,defs['SHEET_PICK32']);P.w8(c,at+37,frame);P.w8(c,at+42,pick['w']);P.w8(c,at+43,pick['h'])
        P.w16(c,at+44,base);P.w8(c,at+46,bank(c,'pick32_frame_pal',frame) if not args.capture_only else pick['pal'])
        P.w8(c,at+50,1) # persistent display fixture
        records.append((slot,name,frame))
    P.run(c,4);snap('ground-pickups','explicit ten-pickup actor render fixture on actual generated forest ground; no terrain or animation pose changes')
    if not args.capture_only:
        for slot,name,frame in records:
            at=A+slot*64;sx=P.actor(c,slot)['x']-16-P.r16(c,P.sym('gCamX'));sy=P.actor(c,slot)['y']-32-P.r16(c,P.sym('gCamY'))
            obj=object_at(c,x=sx,y=sy,tile=base+frame*pick['frame_tiles'],size=2)
            sprite_check(c,defs,'PICK32',frame,obj,'ground '+name,'pick32_frame_pal')
    # Real input-driven actions. Upgrade ownership is explicitly a render fixture.
    for upgraded in (False,True):
        for facing,d in enumerate(FACES):
            place(facing=facing,upgrade=upgraded);c.set_keys(P.key(c,'B'));P.run(c,6)
            snap(('shield-green-' if upgraded else 'shield-wood-')+d,
                 ('green upgrade ownership render fixture' if upgraded else 'starting wooden shield')+'; real held shield input')
            if not args.capture_only:
                view=2 if facing==0 else 0 if facing==2 else 1
                frame=view+(3 if upgraded else 0)
                obj=object_at(c,tile=44,size=1)
                sprite_check(c,defs,'SHIELD',frame,obj,('green ' if upgraded else 'wood ')+d,'shield_frame_pal')
                hud_checks(c,defs,(0,5,0),('green ' if upgraded else 'wood ')+d,upgrade=upgraded)
            c.clear_keys(P.key(c,'B'))
    P.run(c,12);P.press(c,'START',3,48)
    check('upgraded shield fixture opens the real inventory',C.gstate(c)==4)
    snap('inventory-items-green-shield','actual inventory with explicit green shield-upgrade ownership render fixture')
    if not args.capture_only:menu_checks(c,defs,ITEM_PAGE,'green shield items page',upgrade=True)
    P.press(c,'START',3,32)
    for name,eq,facing,age in (('use-bow',6,1,4),('use-lantern',3,0,4),('use-cape',4,1,12),('plant-bomb-hand',2,2,3)):
        place(facing=facing,equipment=(0,eq,0));c.set_keys(P.key(c,'B'));P.run(c,1);c.clear_keys(P.key(c,'B'));P.run(c,age)
        snap(name,'actual button-triggered '+name+' on natural generated forest ground')
        if not args.capture_only and name!='plant-bomb-hand':
            # One extra video frame flushes the newly selected streamed frame.
            P.run(c,1)
            frame=P.r16(c,L.ssym('sLastActionFrame'))&65535
            tile=P.r16(c,L.ssym('sActionTile'))&65535
            sprite_check(c,defs,'BLOOMFX',frame,object_at(c,tile=tile,size=2),name+' held source','bloomfx_frame_pal')
        if name=='plant-bomb-hand':
            P.run(c,10);snap('plant-bomb-ground','same real bomb after its hand-to-ground release')
            if not args.capture_only:
                slot=next((i for i in range(1,96) if P.actor(c,i)['kind']==6 and P.actor(c,i)['type']==5),None)
                check('bomb button creates a real planted object',slot is not None)
                if slot is not None:
                    at=A+slot*64;info=sh(c,defs,'ITEMS');frame=P.r8(c,at+37);tile=(P.r16(c,at+44)&65535)+frame*info['frame_tiles']
                    sprite_check(c,defs,'ITEMS',frame,object_at(c,tile=tile,size=1),'real planted bomb','items_frame_pal')
                    P.run(c,64);snap('plant-bomb-lit','same real planted bomb during the warning part of its fuse')
                    frame=P.r8(c,at+37);tile=(P.r16(c,at+44)&65535)+frame*info['frame_tiles']
                    sprite_check(c,defs,'ITEMS',frame,object_at(c,tile=tile,size=1),'real bomb warning','items_frame_pal')
    # Earn a generated trial reward normally, without assigning its get pose.
    c=P.boot(rom=args.rom,seed=seed);C.dismiss(c);pl=P.sym('gPl');world=C.world(c);P.enter_forest(c)
    cell=world['key_cell'][0];L.warp(c,cell,next(i for i,g in enumerate(world['cells'][cell]['gate']) if g))
    check('actual plate trial completes',C.earn_trial(c,claim=False))
    chest=M.tiles_of(c,lambda m:m['type']=='CHEST');assert chest
    tx,ty=chest[0];C.teleport(c,tx*16+8,(ty+1)*16+14);c.set_keys(P.key(c,'UP'))
    for _ in range(60):
        c.run_frame()
        if P.actor(c,0)['state']==6:break
    c.clear_keys(P.key(c,'UP'));check('earned chest enters item-get',P.actor(c,0)['state']==6)
    P.run(c,12);snap('earned-blightseeds','actual generated plate trial reward; earned, not a pose fixture')
    if not args.capture_only:
        frame=defs['F_ICON32_BOMBS'];x=P.actor(c,0)['x']-16-P.r16(c,P.sym('gCamX'))
        obj=next((o for o in B.oam(c) if o['x']==x and o['shape']==0 and o['size']==2 and 56<=o['tile']<876),None)
        sprite_check(c,defs,'ICON32',frame,obj,'earned item-get','icon32_frame_pal')
    check('ROM stayed fixed during review',hashlib.sha256(Path(args.rom).read_bytes()).hexdigest()==digest)
    for record in shots:
        with Image.open(out/record['file']) as im:assert im.size==(240,160)
    report={'rom_sha256':digest,'seed':hex(seed),'emulator':'mGBA 0.10.5','capture_only':args.capture_only,
            'method':'Unmodified native240x160 mGBA framebuffers. Explicit full-inventory, upgraded-shield ownership and ground-actor display fixtures; real tool button inputs; Blightseeds earned from the generated plate trial.',
            'passed':sum(c['passed'] for c in checks),'total':len(checks),'checks':checks,'captures':shots}
    (out/'reference-items.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d; %d native captures'%('PASS' if report['passed']==report['total'] else 'FAIL',report['passed'],report['total'],len(shots)),flush=True)
    return int(report['passed']!=report['total'])


if __name__=='__main__':raise SystemExit(main())
