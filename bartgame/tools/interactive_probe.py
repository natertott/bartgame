"""Verify readable interactive scenery and its real gameplay in mGBA.

Generated field chests, mystery doors, switches and rewards use actual inputs.
Inventory/location and mystery descriptors are test fixtures; no screenshot
from this probe is presented as generated gameplay evidence. Hardware OAM,
OBJ VRAM and BG maps verify the display, rather than trusting renderer tags.
"""
import argparse
import hashlib
import json
from pathlib import Path

import probe as P
import critical_path as C
import lift_probe as L
import myst_probe as M
import bloom_probe as B
import surface_probe as S

checks=[]


def check(name,ok,detail=None):
    row={'name':name,'passed':bool(ok)}
    if detail is not None:row['detail']=detail
    checks.append(row)
    print(('PASS' if ok else 'FAIL'),name,'' if detail is None else detail,flush=True)


def memory(c,address,size):return B.bytes_at(c,address,size)


def sheet(c,index):
    at=P.sym('sheets')+index*12
    return {'source':P.r32(c,at),'count':P.r16(c,at+4)&65535,
            'tiles':P.r8(c,at+6),'shape':P.r8(c,at+7),'size':P.r8(c,at+8),
            'pal':P.r8(c,at+9),'width':P.r8(c,at+10),'height':P.r8(c,at+11)}


def bounds(points):
    if not points:return None
    xs,ys=zip(*points);return [min(xs),min(ys),max(xs)+1,max(ys)+1]


def dimensions(box):return [box[2]-box[0],box[3]-box[1]] if box else [0,0]


def sprite(c,defs,name,frame):
    sh=sheet(c,defs['SHEET_'+name]);blob=memory(c,sh['source']+frame*sh['tiles']*32,sh['tiles']*32)
    return sh,blob,bounds(B.pixels(blob,sh['width'],sh['height']))


def resident(c,name,sh,blob,label):
    tile=P.r16(c,B.static_symbol(name))&65535
    check(label+' has a valid resident frame',0<tile and tile+sh['tiles']<=876,tile)
    match=[e for e in B.oam(c) if e['tile']==tile and e['shape']==sh['shape'] and e['size']==sh['size']]
    check(label+' is drawn exactly once in hardware OAM',len(match)==1,match)
    if tile:
        check(label+' actual OBJ VRAM matches the intended art',memory(c,0x06010000+tile*32,len(blob))==blob)
    return match[0] if len(match)==1 else None


def resources(c):
    p=P.sym('gPl')
    return {'hp_max':P.r16(c,p+2),'gilt':P.r16(c,p+4),'keys':P.r8(c,p+6),
            'bombs':P.r8(c,p+7),'items':P.r8(c,p+8),'pieces':P.r8(c,p+30),
            'arrows':P.r8(c,p+35),'items2':P.r8(c,p+36)}


def focus(c,x,y):
    C.clear_enemies(c);C.heal(c);c.clear_keys(*range(10))
    P.w8(c,P.sym('gActors')+35,0)
    C.teleport(c,x*16+8,(y+1)*16+14)
    # A test teleport can move the camera its full224px range. Give normal
    # easing enough time to settle before judging HUD overlap or clipping.
    P.run(c,96)


def chest_display(c,defs,tier,opened,x,y,label):
    frame=defs['F_INTERACTIVECHEST_'+('WOODEN','BRASS','RELIC')[tier]+'_'+('OPEN' if opened else 'CLOSED')]
    sh,blob,box=sprite(c,defs,'INTERACTIVECHEST',frame)
    check(label+' painted chest is larger than one tile',all(v>16 for v in dimensions(box)),box)
    part=resident(c,'sChestTile',sh,blob,label)
    if part:
        hero=next((e for e in B.oam(c) if e['tile']==0 and e['shape']==1 and e['size']==3),None)
        if hero:
            check(label+' chest stays behind the approaching player',part['index']>hero['index'],{'chest':part['index'],'hero':hero['index']})
        wx=part['x']+P.r16(c,P.sym('gCamX'));wy=part['y']+P.r16(c,P.sym('gCamY'))
        check(label+' visible chest is centered on its physical interaction',abs((wx+16)-(x*16+8))<=1,{'sprite_top_left':[wx,wy],'logical_tile':[x,y]})
    check(label+' old small chest is absent from BG1',S.entry(c,24,x,y)==(0,0,0,0),S.entry(c,24,x,y))
    return box


def field_chests(c,defs,world):
    cases=(('wooden money chest',lambda d:d['role']==4 and d['arg']==0,0,'gilt'),
           ('brass map chest',lambda d:d['role']==4 and d['arg']==7,1,'map'),
           ('relic bow chest',lambda d:d['role']==4 and d['arg']==6,2,'bow'),
           ('relic small-key chest',lambda d:d['role']==10,2,'key'))
    rows=[]
    for label,predicate,tier,reward in cases:
        cell=next((i for i,d in enumerate(world['cells']) if predicate(d)),None)
        check(label+' exists in the generated seed',cell is not None)
        if cell is None:continue
        side=next(i for i,g in enumerate(world['cells'][cell]['gate']) if g)
        L.warp(c,cell,side);C.clear_enemies(c)
        positions=M.tiles_of(c,lambda m:m['type']=='CHEST')
        check(label+' keeps a real unopened chest interaction',len(positions)==1,positions)
        if not positions:continue
        x,y=positions[0];focus(c,x,y)
        old=resources(c);base=S.under(c,x,y)
        chest_display(c,defs,tier,False,x,y,label+' closed')
        check(label+' preserves its underlying floor',S.entry(c,28,x,y)==S.expected(c,base))
        check(label+' opens by walking into its front',C.open_chest(c))
        C.dismiss(c);focus(c,x,y);new=resources(c)
        expected=(new['gilt']==old['gilt']+30 if reward=='gilt' else
                  bool(new['items2']&4) if reward=='map' else
                  bool(new['items2']&1) and new['arrows']==20 if reward=='bow' else
                  new['keys']==old['keys']+1)
        check(label+' pays its original reward',expected,{'before':old,'after':new})
        chest_display(c,defs,tier,True,x,y,label+' opened')
        check(label+' open state retains the exact substrate',S.under(c,x,y)==base and S.entry(c,28,x,y)==S.expected(c,base))
        L.warp(c,cell,side);C.dismiss(c);focus(c,x,y)
        check(label+' remains opened after revisiting',C.tt_at(c,x,y)==defs['MT_CHEST_OPEN'])
        chest_display(c,defs,tier,True,x,y,label+' revisited')
        P.hold(c,'UP',20);C.dismiss(c)
        check(label+' cannot grant its reward twice',resources(c)==new,{'expected':new,'actual':resources(c)})
        rows.append({'cell':cell,'tier':tier,'reward':reward,'position':[x,y]})
    return rows


def entry_display(c,defs,style,label,closed=False):
    frame=defs['F_INTERACTIVEENTRY_'+('CAVE','HOLLOW','THICKET')[style]+('_CLOSED' if closed else '')]
    sh,blob,box=sprite(c,defs,'INTERACTIVEENTRY',frame)
    hero,hero_blob,hero_box=sprite(c,defs,'HERO',defs['F_HERO_IDLE_N'])
    dims=dimensions(box);bloom=dimensions(hero_box)
    check(label+' doorway is wider and taller than Bloom',dims[0]>bloom[0] and dims[1]>bloom[1],{'entry':box,'bloom':hero_box})
    return resident(c,'sEntryTile',sh,blob,label)


def mysteries(c,defs,world):
    cell=next(i for i,d in enumerate(world['cells']) if d['role'] not in (1,2,3,7))
    rows=[]
    for style,name in enumerate(('cave','hollow','thicket')):
        # Descriptor/size is an explicit fixture. Entry itself is the actual
        # generated mouth, and both directions use ordinary player input.
        check(name+' enters through its generated door',M.enter(c,cell,'chest',style,style))
        C.clear_enemies(c);P.run(c,3)
        entry_display(c,defs,style,name+' inner exit')
        positions=M.tiles_of(c,lambda m:m['type']=='CHEST')
        check(name+' has the expected sized reward chest',len(positions)==1,positions)
        if positions:
            x,y=positions[0];focus(c,x,y)
            chest_display(c,defs,style,False,x,y,name+' reward')
            old=resources(c)
            check(name+' chest opens normally',M.open_chest(c));C.dismiss(c);focus(c,x,y)
            new=resources(c)
            paid=new['gilt']==old['gilt']+10 if style==0 else new['pieces']==old['pieces']+1 if style==1 else new['keys']==old['keys']+1 and new['gilt']==old['gilt']+20
            check(name+' chest tier matches its unchanged reward',paid,{'before':old,'after':new})
            chest_display(c,defs,style,True,x,y,name+' claimed reward')
        check(name+' enlarged inner door exits to the forest',M.leave(c)==1 and C.cell(c)==cell)
        C.clear_enemies(c);P.run(c,4)
        entry_display(c,defs,style,name+' outer mouth')
        check(name+' returning through the larger mouth still works',C.enter_trial(c))
        check(name+' claimed reward stays claimed on return',not M.tiles_of(c,lambda m:m['type']=='CHEST'))
        if positions:
            focus(c,x,y);chest_display(c,defs,style,True,x,y,name+' persisted reward')
            check(name+' revisiting does not duplicate resources',resources(c)==new)
        check(name+' exit remains usable on revisit',M.leave(c)==1)
        rows.append({'cell':cell,'style':name,'size':style})
    return rows


def trial_exits(c,defs,world):
    cell=next(i for i,d in enumerate(world['cells']) if d['role'] not in (1,2,3,7))
    for style,name in enumerate(('cave','hollow','thicket')):
        check(name+' battle chamber enters through the mouth',M.enter(c,cell,'waves',2,style))
        C.clear_enemies(c);P.run(c,3)
        # The player begins immediately inside the bottom exit, so the GPU
        # check examines the actual visible gate, not a distant hidden OBJ.
        entry_display(c,defs,style,name+' shut trial door',closed=True)
        check(name+' shut trial has no active exit trigger',not M.tiles_of(c,lambda m:m['type']=='MYST'))
        width,height,_=M.grid(c)
        C.teleport(c,(width//2)*16,(height-2)*16+10)
        P.hold(c,'DOWN',24)
        check(name+' closed door physically prevents leaving',C.area(c)==2 and C.gstate(c)==1)
        # Clearing unrelated combat actors is a test fixture; existing
        # combat probes verify the battles. Here all wave-completion logic,
        # reward creation and the closed-to-open drawing execute normally.
        for _ in range(5):C.clear_enemies(c);P.run(c,70)
        check(name+' won trial restores both real exit tiles',len(M.tiles_of(c,lambda m:m['type']=='MYST'))==2)
        C.teleport(c,(width//2)*16,(height-2)*16+10);P.run(c,4)
        entry_display(c,defs,style,name+' opened trial door')
        check(name+' opened trial door permits leaving',M.leave(c)==1)


def shrine(args,defs):
    c=P.boot(args.rom,seed=0xDEADBEEF);C.dismiss(c);world=C.world(c);P.enter_forest(c)
    cell=next(i for i,d in enumerate(world['cells']) if d['role']==9 and i==5)
    side=next(i for i,g in enumerate(world['cells'][cell]['gate']) if g)
    L.warp(c,cell,side);C.clear_enemies(c)
    spots=P.sym('gSpots');x=P.r8(c,spots+42);y=P.r8(c,spots+43)+1
    check('natural shrine has the explicit unused interaction plate',C.tt_at(c,x,y)==defs['MT_SHRINE_PLATE'],{'seed':'0xdeadbeef','cell':cell,'plate':[x,y]})
    focus(c,x,y)
    check('shrine plate is actually drawn above the forest floor',S.entry(c,24,x,y)==S.expected(c,defs['MT_SHRINE_PLATE']))
    p=P.sym('gPl');flag=P.sym('gWorld')+4+cell*13+11
    P.w16(c,p,6);c.set_keys(P.key(c,'UP'))
    for _ in range(40):
        c.run_frame()
        if P.r8(c,flag)&0x80:break
    c.clear_keys(*range(10));C.dismiss(c)
    check('walking onto the shrine plate heals the injured player',P.r16(c,p)==P.r16(c,p+2))
    check('shrine use records its one-use flag',bool(P.r8(c,flag)&0x80))
    check('used shrine replaces its bright plate with the spent stone',C.tt_at(c,x,y)==defs['MT_MOSSY_STONE'])
    L.warp(c,cell,side);C.clear_enemies(c)
    x=P.r8(c,spots+42);y=P.r8(c,spots+43)+1
    check('spent shrine stays spent after revisiting',C.tt_at(c,x,y)==defs['MT_MOSSY_STONE'] and bool(P.r8(c,flag)&0x80))
    C.teleport(c,x*16+8,y*16+12);P.w16(c,p,6);P.run(c,24)
    check('revisiting a spent shrine grants no second heal',P.r16(c,p)==6)
    return {'seed':'0xdeadbeef','cell':cell,'plate':[x,y]}


def entrance_visibility(args,defs):
    rows=[]
    for seed in (0xB4A7,0xDEADBEEF,7):
        c=P.boot(args.rom,seed=seed);C.dismiss(c);world=C.world(c);P.enter_forest(c)
        for cell,data in enumerate(world['cells']):
            packed=P.r8(c,P.sym('gWorld')+M.MYST_OFF+cell)
            if not packed:continue
            L.warp(c,cell,next(i for i,g in enumerate(data['gate']) if g));C.clear_enemies(c)
            mouths=M.tiles_of(c,lambda m:m['name'].startswith('mouth_'))
            label=hex(seed)+' cell'+str(cell)+' doorway approach'
            check(label+' contains exactly one physical mouth',len(mouths)==1,mouths)
            if len(mouths)!=1:continue
            x,y=mouths[0];check(label+' keeps the arch below the HUD edge',y>=4,[x,y])
            focus(c,x,y);style=(packed>>6)&3
            sh,blob,box=sprite(c,defs,'INTERACTIVEENTRY',style)
            tile=P.r16(c,B.static_symbol('sEntryTile'))&65535
            parts=[e for e in B.oam(c) if e['tile']==tile and e['shape']==sh['shape'] and e['size']==sh['size']]
            check(label+' is present in actual hardware OAM',len(parts)==1,parts)
            if parts:
                e=parts[0];visible=[e['x']+box[0],e['y']+box[1],e['x']+box[2],e['y']+box[3]]
                check(label+' complete painted silhouette is visible outside the HUD',visible[0]>=0 and visible[1]>=32 and visible[2]<=240 and visible[3]<=160,visible)
                check(label+' hardware pixels match this entrance style',memory(c,0x06010000+tile*32,len(blob))==blob)
                rows.append({'seed':hex(seed),'cell':cell,'style':style,'mouth':[x,y],'screen_bounds':visible})
    check('door approach visibility covers all three styles',{r['style'] for r in rows}=={0,1,2})
    return rows


def bg_pixels(c,x,y):
    """Decode the actual BG1 map and character data to RGBA-like RGB555."""
    return tile_pixels(c,S.entry(c,24,x,y))


def tile_pixels(c,entries):
    out=[]
    for py in range(16):
        row=[]
        for px in range(16):
            e=entries[(py//8)*2+px//8];tx=px%8;ty=py%8
            if e&0x400:tx=7-tx
            if e&0x800:ty=7-ty
            byte=P.r8(c,0x06000000+(e&1023)*32+ty*4+tx//2)
            index=(byte>>(4*(tx&1)))&15
            color=P.r16(c,0x05000000+((e>>12)*16+index)*2)&65535
            row.append((index,color))
        out.append(row)
    return out


def materials(c,defs,world):
    cell=world['entry'];side=next(i for i,g in enumerate(world['cells'][cell]['gate']) if g)
    L.warp(c,cell,side)
    def art(name):
        at=P.sym('metatile_map_forest')+defs['MT_'+name]*8
        return tile_pixels(c,tuple(P.r16(c,at+i*2)&65535 for i in range(4)))
    def lum(color):return ((color&31)*2+((color>>5)&31)*3+((color>>10)&31))/6
    for name in ('PIT','FOREST_BLIGHT_PIT'):
        pixels=art(name)
        center=[lum(pixels[y][x][1]) for y in range(4,12) for x in range(3,13)]
        rim=[lum(pixels[y][x][1]) for y in (0,1,14,15) for x in range(16)]
        check(name+' retains a deep quiet cavity',sum(v<=4 for v in center)>=64,{'dark_pixels':sum(v<=4 for v in center),'sample_pixels':len(center)})
        check(name+' rim visibly separates the drop from its floor',sum(rim)/len(rim)>sum(center)/len(center)+3,{'center_mean':sum(center)/len(center),'rim_mean':sum(rim)/len(rim)})
        check(name+' remains an actual falling hazard',P.r8(c,P.sym('metatile_type')+defs['MT_'+name])==defs['TT_PIT'])
    web=art('WEB');bright=sum(lum(color)>=15 for row in web for _,color in row)
    check('cobweb has broad pale silk against the dark opening',bright>=45,bright)
    crack=art('CRACK');tones={color for row in crack for _,color in row}
    check('bombable wall retains a readable stone and fracture range',max(map(lum,tones))-min(map(lum,tones))>=12)
    for name,behavior in (('CRACK','CRACK'),('WEB','WEB'),('DOOR_LOCKED','DOOR'),('TORCH','TORCH'),('TORCH_LIT','TORCH_LIT')):
        mt=defs['MT_'+name]
        check(name+' retains its correct item interaction',P.r8(c,P.sym('metatile_type')+mt)==defs['TT_'+behavior])
        check(name+' keeps its physical barrier',P.r8(c,P.sym('metatile_coll')+mt)!=0)


def switches(c,defs,world):
    cell=next(i for i,d in enumerate(world['cells']) if d['role'] not in (1,2,3,7))
    check('switch chamber enters normally',M.enter(c,cell,'switches',1,2))
    plates=M.tiles_of(c,lambda m:m['name']=='myst_switch',1)
    check('medium switch task contains four full plates',len(plates)==4,plates)
    for i,(x,y) in enumerate(plates):
        before=bg_pixels(c,x,y)
        b=bounds([(px,py) for py,row in enumerate(before) for px,(ink,_) in enumerate(row) if ink])
        check('switch %d fills the complete tile'%i,b==[0,0,16,16],b)
        C.heal(c);C.clear_enemies(c);C.teleport(c,x*16+8,y*16+12);P.run(c,8)
        after=bg_pixels(c,x,y)
        check('switch %d responds to a real footstep'%i,M.grid(c,1)[2][(x,y)]==defs['MT_MYST_SWITCH_DOWN'])
        changed=sum(a!=b for ra,rb in zip(before,after) for a,b in zip(ra,rb))
        check('switch %d pressed state is visibly distinct'%i,changed>=24,changed)
        check('switch %d remains walkable'%i,P.r8(c,P.sym('metatile_coll')+C.tt_at(c,x,y))==0)
    P.run(c,20)
    check('all four real plate steps earn one chest',len(M.tiles_of(c,lambda m:m['type']=='CHEST'))==1)
    old=resources(c);check('earned switch chest opens normally',M.open_chest(c));C.dismiss(c)
    check('switch reward remains a piece of heart',resources(c)['pieces']==old['pieces']+1)
    check('solved switch room can be left',M.leave(c)==1)
    check('solved switch room can be reentered',C.enter_trial(c))
    check('solved plates remain inactive after returning',not M.tiles_of(c,lambda m:m['name']=='myst_switch',1) and bool(P.r8(c,P.sym('gWorld')+M.FLAGS_OFF+cell)&1))
    check('solved plates do not grant a second closed chest',not M.tiles_of(c,lambda m:m['type']=='CHEST'))
    M.leave(c)


def packed_contracts(c,args,defs):
    before_header=Path(args.before_header);before_map=Path(args.before_map);before_rom=Path(args.before_rom)
    if not all(p.exists() for p in (before_header,before_map,before_rom)):
        return {'skipped':'provide all three --before-* paths for packed contract comparison'}
    olddefs=B.definitions(before_header);blob=before_rom.read_bytes();symbols={}
    import re
    for line in before_map.read_text().splitlines():
        m=re.match(r'\s+0x([0-9a-f]{8,16})\s+(\w+)\s*$',line)
        if m:symbols[m.group(2)]=int(m.group(1),16)
    ids=[(name,index) for name,index in olddefs.items() if name.startswith('MT_') and name not in ('MT_NONE','MT_COUNT')]
    changed=[name for name,index in ids if defs.get(name)!=index]
    check('all existing metatiles retain their logical ids',not changed,{'metatiles':len(ids),'changed':changed})
    n=max(i for _,i in ids)+1
    for table in ('metatile_type','metatile_coll','metatile_prop'):
        old=blob[symbols[table]-0x08000000:symbols[table]-0x08000000+n]
        new=memory(c,P.sym(table),n)
        check(table+' preserves every existing physical contract',old==new,{'metatiles':n})
    return {'baseline_rom_sha256':hashlib.sha256(blob).hexdigest(),'metatiles':n}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--before-rom',default='/workspace/setup/interactive-before/bartgame.gba')
    ap.add_argument('--before-map',default='/workspace/setup/interactive-before/bartgame.map')
    ap.add_argument('--before-header',default='/workspace/setup/interactive-before/assets.h')
    ap.add_argument('--out',default='/tmp/interactive-probe.json')
    args=ap.parse_args();defs=B.configure(args)
    c=P.boot(args.rom);C.dismiss(c);world=C.world(c);P.enter_forest(c)
    contracts=packed_contracts(c,args,defs)
    fields=field_chests(c,defs,world);rooms=mysteries(c,defs,world);switches(c,defs,world)
    trial_exits(c,defs,world);materials(c,defs,world);shrine_row=shrine(args,defs)
    entrances=entrance_visibility(args,defs)
    report={'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),
            'emulator':'mGBA 0.10.5','method':__doc__.strip(),
            'passed':sum(r['passed'] for r in checks),'total':len(checks),'checks':checks,
            'field_chests':fields,'mystery_rooms':rooms,'shrine':shrine_row,
            'entrance_visibility':entrances,'retained_contracts':contracts}
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d'%('PASS' if report['passed']==report['total'] else 'FAIL',report['passed'],report['total']))
    return int(report['passed']!=report['total'])


if __name__=='__main__':raise SystemExit(main())
