"""Check Bloom's complete action presentation in the real mGBA ROM.

Actions use real buttons and interactions. A local, explicitly physical floor
fixture isolates rendering checks from maze hazards; its screenshots are not
published as gameplay. Hardware OAM/VRAM, real state transitions and world
coordinates are inspected, allowing for the normal one-frame VBlank upload.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import probe as P
import critical_path as C
import lift_probe as L
import wood_probe as W
import bloom_probe as B

FACES=('n','e','s','w')
KEYS=('UP','RIGHT','DOWN','LEFT')
checks=[]


def check(name,ok,detail=None):
    row={'name':name,'passed':bool(ok)}
    if detail is not None:row['detail']=detail
    checks.append(row)
    print(('PASS' if ok else 'FAIL'),name,detail if detail is not None else '',flush=True)


def signed(c,at):
    v=P.r32(c,at)
    return v-(1<<32) if v>=1<<31 else v


def snapshot(c):
    a=P.sym('gActors');pl=P.sym('gPl')
    return {'state':P.r8(c,a+2),'sub':P.r8(c,a+3),'timer':P.r8(c,a+4),
            'facing':P.r8(c,a+7),'position':list(P.player_pos(c)),
            'z':signed(c,a+16),'zvel':signed(c,a+20),
            'pose':P.r8(c,B.static_symbol('sLastFrame')),
            'carry':P.r8(c,pl+33),'hp':P.r16(c,pl),
            'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))]}


def hold(c,*keys):
    c.clear_keys(*range(10))
    if keys:c.set_keys(*(P.key(c,k) for k in keys))


def reset(c,defs,facing=0,eq=1):
    B.floor_fixture(c,defs)
    B.reset_player(c,256,230,facing,equipment=(0,eq,0))
    P.w8(c,B.static_symbol('sUseTimer'),0)
    P.run(c,64)


def entry(c,tile,shape=None,size=None):
    return next((e for e in B.oam(c) if e['tile']==tile and
                 (shape is None or e['shape']==shape) and
                 (size is None or e['size']==size)),None)


def hero(c):return entry(c,0,1,3)


def visible_beyond_hero(c,part,w,h):
    """Count real nontransparent tool pixels not hidden by Bloom's alpha."""
    body=hero(c)
    if body is None or part is None:return 0
    bloom=set(B.pixels(B.bytes_at(c,0x06010000,1024),64,32))
    if body['flip']:bloom={(63-x,y) for x,y in bloom}
    pixels=B.pixels(B.bytes_at(c,0x06010000+part['tile']*32,w*h//2),w,h)
    if part['flip']:pixels=[(w-1-x,y) for x,y in pixels]
    return sum((part['x']+x-body['x'],part['y']+y-body['y']) not in bloom for x,y in pixels)


def actor_entry(c,kind,type_):
    for i in range(1,96):
        a=P.sym('gActors')+i*64
        if P.r8(c,a)!=kind or P.r8(c,a+1)!=type_:continue
        sheet=P.r8(c,a+36);frame=P.r8(c,a+37)
        frame_tiles=P.r8(c,P.sym('sheets')+sheet*12+6)
        tile=(P.r16(c,a+44)&65535)+frame*frame_tiles
        return entry(c,tile),i
    return None,None


def world_anchor(c,e):
    return [e['x']+P.r16(c,P.sym('gCamX')),e['y']+P.r16(c,P.sym('gCamY'))]


def tile_set(c,x,y,mt):
    room=P.sym('gRoom');at=y*32+x
    P.w16(c,room+2+at*2,mt);P.w16(c,room+2050+at*2,65535)
    P.w16(c,room+8194+at*2,defs_global['MT_MOSS0'])
    mask=P.r8(c,P.sym('metatile_coll')+mt)
    for dy in range(2):
        for dx in range(2):
            P.w8(c,room+4098+(y*2+dy)*64+x*2+dx,(mask>>(3-dy*2-dx))&1)


def depth_and_guard(c,defs):
    action=P.r16(c,B.static_symbol('sActionTile'))&65535
    hero_sheet=P.sym('sheets')+defs['SHEET_HERO']*12
    source=P.r32(c,hero_sheet);frame_bytes=P.r8(c,hero_sheet+6)*32
    for f,d in enumerate(FACES):
        for upgraded in (False,True):
            reset(c,defs,f,5)
            P.w8(c,P.sym('gPl')+36,0x0f|(0x10 if upgraded else 0))
            hold(c,'B');P.run(c,6)
            h,s=hero(c),entry(c,44,0,1)
            check(d+' shield '+('green' if upgraded else 'wood')+' is present',h is not None and s is not None)
            if h and s:
                check(d+' shield has facing-correct depth',s['index']>h['index'] if f==0 else s['index']<h['index'],{'hero':h,'shield':s})
                if f==0:
                    x,y=world_anchor(c,s);px,py=P.player_pos(c)
                    check('north shield stays beside the raised hands',-18<=x-px<=6 and -30<=y-py<=-20,[x-px,y-py])
                    visible=visible_beyond_hero(c,s,16,16)
                    check('north shield retains a readable visible rim behind Bloom',visible>=32,{'visible_opaque_pixels':visible})
            hold(c)
        reset(c,defs,f,5);hold(c,'B',KEYS[(f+1)%4]);poses=set();frames_ok=True;facings=[]
        previous=snapshot(c)
        for _ in range(62):
            c.run_frame();now=snapshot(c);poses.add(now['pose']);facings.append(now['facing'])
            if previous['state']==0 and previous['pose'] in poses:
                got=B.bytes_at(c,0x06010000,frame_bytes)
                want=B.bytes_at(c,source+previous['pose']*frame_bytes,frame_bytes)
                frames_ok &= got==want
            previous=now
        body='E' if f==3 else d.upper()
        expected={defs['F_HERO_GUARD_'+body],defs['F_HERO_GUARD_'+body+'1'],defs['F_HERO_GUARD_'+body+'2']}
        check(d+' guarded movement has alternating leg poses',expected<=poses,sorted(poses))
        check(d+' guard strafe retains shield facing',all(v==f for v in facings))
        check(d+' guarded poses reach actual OBJ VRAM',frames_ok)
        hold(c)
        for name,eq in (('bow',6),('lamp',3),('sword',1)):
            reset(c,defs,f,eq);hold(c,'B');c.run_frame();hold(c);P.run(c,3)
            h,e=hero(c),entry(c,action,0,2)
            check(d+' '+name+' effect is present',h is not None and e is not None)
            if h and e:
                far=f==0 and name!='sword'
                check(d+' '+name+' has facing-correct depth',e['index']>h['index'] if far else e['index']<h['index'],{'hero':h['index'],'effect':e['index']})
                if f==0 and name=='bow':
                    visible=visible_beyond_hero(c,e,32,32)
                    check('north bow retains visible limbs beyond the blossom',visible>=16,{'visible_opaque_pixels':visible})
            if name=='bow':
                arrow,_=actor_entry(c,3,3)
                check(d+' released arrow is drawn once at the hand',arrow is not None)
                if h and arrow:check(d+' released arrow retains hand-side depth',arrow['index']>h['index'] if f==0 else arrow['index']<h['index'])
        reset(c,defs,f,2);hold(c,'B');c.run_frame();hold(c);P.run(c,2)
        h=hero(c);bomb,_=actor_entry(c,6,5)
        check(d+' planted bomb is the real visible object',h is not None and bomb is not None)
        if h and bomb:check(d+' held bomb uses facing-correct depth',bomb['index']>h['index'] if f==0 else bomb['index']<h['index'])


def jumps(c,defs):
    shadow=P.r16(c,B.static_symbol('sShadowTile'))&65535
    check('ground shadow uses the small resident allocation',shadow>0 and shadow+2<=876,shadow)
    rows=[]
    for f,d in enumerate(FACES):
        reset(c,defs,f,4);hold(c,'B');trace=[];anchors=[];depth=[]
        previous=snapshot(c)
        for tick in range(42):
            c.run_frame()
            if tick==0:hold(c)
            now=snapshot(c);trace.append(now)
            if previous['state']==5 and previous['z']>65536:
                h=hero(c);s=entry(c,shadow,1,0)
                check(d+' airborne ground shadow exists at tick '+str(tick),h is not None and s is not None)
                if h and s:
                    # Hardware entries correspond to the previous prepared frame.
                    x=s['x']+previous['camera'][0];y=s['y']+previous['camera'][1]
                    anchors.append((x-previous['position'][0],y-previous['position'][1]))
                    depth.append(s['index']>h['index'])
                    action=P.r16(c,B.static_symbol('sActionTile'))&65535;e=entry(c,action,0,2)
                    if e:check(d+' cape has facing-correct depth at tick '+str(tick),e['index']<h['index'] if f==0 else e['index']>h['index'])
            previous=now
        poses={t['pose'] for t in trace if t['state']==5}
        body='E' if f==3 else d.upper()
        expected={defs['F_HERO_CAPE_'+body+str(i)] for i in (1,2,3)}
        check(d+' jump shows takeoff, flight and landing poses',expected<=poses,sorted(poses))
        check(d+' shadow stays at ground feet while Bloom rises',bool(anchors) and all(a==(-8,-5) for a in anchors),anchors)
        check(d+' shadow stays behind the airborne body',bool(depth) and all(depth))
        check(d+' cape returns to grounded normal state',trace[-1]['state']==0 and trace[-1]['z']==0)
        check(d+' cape retains its original flight duration',32<=sum(t['state']==5 for t in trace)<=35,sum(t['state']==5 for t in trace))
        rows.append({'direction':d,'trace':trace})
    return rows


def lifts(c,defs):
    rows=[]
    for f,d in enumerate(FACES):
        reset(c,defs,f,1);px,py=P.player_pos(c)
        qx,qy=px,py-6
        if f==0:qy-=11
        elif f==1:qx+=11
        elif f==2:qy+=11
        else:qx-=11
        tile_set(c,qx//16,qy//16,defs['MT_BUSH'])
        hold(c,'R');trace=[]
        for tick in range(18):
            c.run_frame()
            if tick==0:hold(c)
            trace.append(snapshot(c))
        check(d+' R lifts the actual local bush',any(t['state']==10 for t in trace) and trace[-1]['state']==11 and trace[-1]['carry']==1)
        check(d+' lift lasts twelve updates',sum(t['state']==10 for t in trace)==12,sum(t['state']==10 for t in trace))
        body='E' if f==3 else d.upper()
        expected={defs['F_HERO_LIFT_'+body+str(i)] for i in range(3)}
        check(d+' lift has bend, raise and settle poses',expected<={t['pose'] for t in trace},sorted({t['pose'] for t in trace}))
        lift_tile=P.r16(c,B.static_symbol('sLiftTile'))&65535
        obj=entry(c,lift_tile,0,1);h=hero(c)
        check(d+' carried object remains visible',obj is not None)
        if obj and h:
            check(d+' carried object has facing-correct depth',obj['index']>h['index'] if f==0 else obj['index']<h['index'])
            x,y=world_anchor(c,obj);check(d+' overhead load anchor aligns with throw origin',(x-px,y-py)==(-8,-40),[x-px,y-py])
        last_anchor=world_anchor(c,obj) if obj else None
        hold(c,'R');release=[]
        for tick in range(8):
            c.run_frame()
            if tick==0:hold(c)
            release.append(snapshot(c))
            e=entry(c,lift_tile,0,1)
            if tick==1 and e and last_anchor:
                point=world_anchor(c,e);distance=max(abs(point[k]-last_anchor[k]) for k in range(2))
                check(d+' throw releases continuously from the hands',distance<=7,{'carried':last_anchor,'released':point,'max_delta':distance})
                h=hero(c)
                if h:check(d+' thrown object retains hand-side depth while overlapping Bloom',e['index']>h['index'] if f==0 else e['index']<h['index'])
            if tick==1:
                thrown,slot=actor_entry(c,6,20)
                check(d+' R creates the actual moving thrown actor',slot is not None)
                if slot is not None:
                    a=P.sym('gActors')+slot*64
                    check(d+' thrown physics retains speed and airborne launch',P.r16(c,a+24)==640 and signed(c,a+16)>24*65536)
        check(d+' throw clears the carried state',release[-1]['state']==0 and release[-1]['carry']==0)
        rows.append({'direction':d,'lift_trace':trace,'release_trace':release})
    return rows


def ledge_and_dropin(c,defs):
    rows=[]
    for f,mt,ty in ((0,'MT_LEDGE_N',13),(2,'MT_LEDGE_S',15)):
        reset(c,defs,f,1)
        # A real ledge spans a bank. A lone 16px pillar is intentionally
        # bypassed by normal corner assistance before six push updates.
        for tx in (15,16,17):tile_set(c,tx,ty,defs[mt])
        hold(c,KEYS[f]);trace=[]
        for _ in range(58):c.run_frame();trace.append(snapshot(c))
        hold(c);air=[t for t in trace if t['state']==5 and t['sub']==1]
        expected={defs['F_HERO_CAPE_'+FACES[f].upper()+str(i)] for i in (1,2,3)}
        check(FACES[f]+' ledge is jumped by pushing against its physical edge',bool(air))
        check(FACES[f]+' ledge drop has takeoff, airborne and landing bodies',expected<={t['pose'] for t in air},sorted({t['pose'] for t in air}))
        check(FACES[f]+' ledge drop finishes grounded',trace[-1]['state']==0 and trace[-1]['z']==0)
        rows.append({'kind':'ledge-'+FACES[f],'trace':trace})
    reset(c,defs,2,7);hold(c,'B');trace=[]
    for tick in range(260):
        c.run_frame()
        if tick==0:hold(c)
        trace.append(snapshot(c))
    dropping=[t for t in trace if t['state']==5 and t['sub']==2]
    expected={defs['F_HERO_CAPE_S'+str(i)] for i in (1,2,3)}
    check('Drain Cap input triggers swallowing',any(t['state']==12 for t in trace))
    check('return transition triggers the real ceiling drop',bool(dropping))
    check('ceiling drop uses a landing progression',expected<={t['pose'] for t in dropping},sorted({t['pose'] for t in dropping}))
    check('return drop ends on its feet',trace[-1]['state']==0 and trace[-1]['z']==0)
    rows.append({'kind':'cap-return-dropin','trace':trace})
    return rows


def mechanical_traces(rom,map_,header):
    defs=B.configure(SimpleNamespace(map=map_,assets_header=header))
    c=B.boot(rom);rows=[]
    plan=(('walk',1,48,48),('sword',1,40,1),('roll',1,40,1),('cape',4,45,1),('guard-walk',5,62,62))
    for f,d in enumerate(FACES):
        for name,eq,total,held in plan:
            reset(c,defs,f,eq)
            keys=(KEYS[f],) if name=='walk' else (KEYS[f],'R') if name=='roll' else (KEYS[(f+1)%4],'B') if name=='guard-walk' else ('B',)
            hold(c,*keys);trace=[]
            for tick in range(total):
                c.run_frame()
                if tick+1==held:hold(c)
                t=snapshot(c);t.pop('pose');t.pop('camera')
                t['sword_active']=P.r8(c,P.sym('gPl')+21)
                t['sword_phase']=P.r8(c,P.sym('gPl')+22)
                trace.append(t)
            hold(c);rows.append({'action':name+'-'+d,'trace':trace})
    return rows


def hazards_and_death(c,defs):
    rows=[]
    for label,mt,sub in (('water','MT_WATER',1),('pit','MT_PIT',0)):
        reset(c,defs,1,1);tile_set(c,17,14,defs[mt]);hold(c,'RIGHT');trace=[];entered=False
        for _ in range(80):
            c.run_frame();now=snapshot(c);trace.append(now)
            if now['state']==4:entered=True;hold(c)
        falling=[t for t in trace if t['state']==4]
        check(label+' is entered by walking into a real physical tile',entered)
        check(label+' selects the proper fall variant',bool(falling) and all(t['sub']==sub for t in falling))
        check(label+' retains its 36-update fall duration',len(falling)==36,len(falling))
        prefix='DROWN_' if sub else 'FALL_';expected={defs['F_HERO_'+prefix+str(i)] for i in (1,2,3)}
        check(label+' shows all three sinking poses',expected<={t['pose'] for t in falling})
        check(label+' restores the safe position and charges one heart quarter',trace[-1]['state']==0 and trace[-1]['z']==0 and trace[-1]['hp']==22,trace[-1])
        rows.append({'hazard':label,'trace':trace})
    reset(c,defs,2,1);P.w16(c,P.sym('gPl'),2)
    px,py=P.player_pos(c);W.spawn_enemy(c,0,px,py-8);trace=[]
    for _ in range(110):c.run_frame();trace.append(snapshot(c))
    dead=[t for t in trace if t['state']==7]
    expected={defs['F_HERO_DEAD_'+str(i)] for i in range(3)}
    check('actual enemy contact triggers death',len(dead)>80 and dead[-1]['hp']==0)
    check('death progresses through three collapse poses',expected<={t['pose'] for t in dead})
    check('death settles instead of returning to the standing hurt pose',len(dead)>40 and all(t['pose']==defs['F_HERO_DEAD_2'] for t in dead[-40:]))
    rows.append({'hazard':'death','trace':trace})
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--before-rom',default='/workspace/setup/bloom-suite-before/bartgame.gba')
    ap.add_argument('--before-map',default='/workspace/setup/bloom-suite-before/bartgame.map')
    ap.add_argument('--before-header',default='/workspace/setup/bloom-suite-before/assets.h')
    ap.add_argument('--skip-before',action='store_true',help='omit the frozen-ROM physical trace comparison')
    ap.add_argument('--out',default='/workspace/setup/bloom-suite-probe.json')
    args=ap.parse_args();defs=B.configure(args)
    global defs_global;defs_global=defs
    c=B.boot(args.rom);depth_and_guard(c,defs);jump_rows=jumps(c,defs);lift_rows=lifts(c,defs);hazard_rows=hazards_and_death(c,defs)
    # Return transitions reload all static sprite allocations, so do these
    # after the per-area allocation checks and before independent ROM boots.
    c=B.boot(args.rom);ledge_rows=ledge_and_dropin(c,defs)
    comparisons=[]
    if not args.skip_before:
        old=mechanical_traces(args.before_rom,args.before_map,args.before_header)
        new=mechanical_traces(args.rom,args.map,args.assets_header)
        for a,b in zip(old,new):
            differences=[{'tick':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(a['trace'],b['trace'])) if x!=y]
            check(a['action']+' physical action trace matches the frozen ROM',not differences,differences[:3])
            comparisons.append({'action':a['action'],'frames':len(b['trace']),'unchanged':not differences,'differences':differences})
    report={'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),
            'emulator':'mGBA 0.10.5','method':__doc__.strip(),
            'passed':sum(r['passed'] for r in checks),'total':len(checks),'checks':checks,
            'jump_traces':jump_rows,'lift_traces':lift_rows,'hazard_traces':hazard_rows,
            'ledge_dropin_traces':ledge_rows,'mechanical_comparison':comparisons}
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d'%('PASS' if all(r['passed'] for r in checks) else 'FAIL',report['passed'],report['total']))
    return int(not all(r['passed'] for r in checks))


if __name__=='__main__':raise SystemExit(main())
