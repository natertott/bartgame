"""Review interactive scenery in actual, naturally generated mGBA rooms.

Fixtures choose seed, room, inventory, safe position/facing and clear unrelated
actors. No terrain, chest reward, mystery descriptor, pose or animation frame
is injected. Entrances are used with ordinary inputs. Native PNGs are exact
240x160 framebuffers; GIFs sample every two video frames and enlarge 2x.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import probe as P
import critical_path as C
import lift_probe as L
import myst_probe as M
import blight_review as B
import bloom_probe as BP
import bloom_review as BR

SEED=0xB4A7
KEYS=('UP','RIGHT','DOWN','LEFT')
STATES=('normal','roll','attack','hurt','fall','jump','itemget','dead','talk','frozen','lift','carry','swallowed')


def plan():
    cases=[]
    def add(name,seed,cell,feature,**kw):cases.append(dict(name=name,seed=hex(seed),cell=cell,feature=feature,**kw))
    # Natural field loot: wood, brass and relic designs, against living and deep decay.
    for n,s,c in [('forest-wood-chest',6,16),('blight-wood-chest',9,15),
                  ('forest-brass-chest',7,10),('blight-brass-chest',7,18),
                  ('forest-relic-chest',SEED,21),('blight-relic-chest',6,19)]:
        add(n,s,c,'chest',action='chest',frames=112)
    # Every architectural style, including bright and heavily corrupted surroundings.
    for n,s,c in [('forest-cave-door',SEED,11),('mixed-cave-door',SEED,0),
                  ('forest-hollow-door',6,0),('blight-hollow-door',6,24),
                  ('forest-thicket-door',SEED,7),('blight-thicket-door',7,14)]:
        add(n,s,c,'mouth_',action='enter',frames=124)
    for n,s,c in [('small-hollow-chest',6,3),('medium-cave-chest',11,17),
                  ('large-thicket-chest',6,17)]:
        add(n,s,c,'chest',interior=True,action='chest',frames=112)
    for n,s,c in [('cave-floor-switch',SEED,11),('hollow-floor-switch',6,0),
                  ('thicket-floor-switch',6,12)]:
        add(n,s,c,'myst_switch',interior=True,action='switch',frames=88)
    add('thicket-censer',SEED,13,'torch',interior=True,action='torch',frames=96)
    add('cave-pot',SEED,12,'myst_pot',interior=True,frames=64)
    add('cave-spring',SEED,3,'myst_spring',interior=True,frames=64)
    for n,s,c in [('cave-exit',11,17),('hollow-exit',6,3),('thicket-exit',6,17)]:
        add(n,s,c,'exit',interior=True,action='leave',frames=124)
    for n,s,c,kind in [('forest-bomb-wall',0xDEADBEEF,15,1),('blight-bomb-wall',6,4,1),
                        ('forest-cobweb',6,0,2),('blight-cobweb',6,24,2),
                        ('forest-cape-hole',SEED,16,3),('blight-cape-hole',6,9,3)]:
        add(n,s,c,'pocket',action=('bomb','lamp','cape')[kind-1],frames=220 if kind==1 else 96)
    add('forest-locked-door',SEED,24,'door_locked',frames=64)
    add('blight-locked-door',7,14,'door_locked',frames=64)
    add('forest-shrine',0xDEADBEEF,5,'statue',action='shrine',frames=96)
    add('forest-relic-pedestal',SEED,23,'mossy_stone',frames=64)
    for feature,cell in [('bush',16),('rock_small',16),('thorn',11)]:
        add('forest-'+feature,SEED,cell,feature,frames=64)
    add('thicket-boulder',7,17,'boulder',interior=True,frames=64)
    add('drain-control',SEED,None,'control',frames=64)
    add('drain-exit',SEED,None,'drain_exit',frames=64)
    return cases


class Review:
    def __init__(self,args):
        self.args=args;P.MAP=args.map;P._syms=None
        self.defs=BP.definitions(args.assets_header);self.names={v:k[3:].lower() for k,v in self.defs.items() if k.startswith('MT_')}
        self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=True);self.rows=[];self.missing=[]
        self.old=json.loads(Path(args.match).read_text()) if args.match else None
        existing=self.out/'capture.json'
        if args.only and existing.exists():
            prior=json.loads(existing.read_text());assert prior['rom_sha256']==hashlib.sha256(Path(args.rom).read_bytes()).hexdigest()
            self.rows=[r for r in prior['captures'] if r['name'] not in args.only.split(',')]
            valid_names={r['name'] for r in plan()}
            self.missing=[r for r in prior['missing'] if r['name'] in valid_names and r['name'] not in args.only.split(',')]
        self.c=None

    def grid(self):
        c=self.c;R=P.sym('gRoom');w,h=P.r8(c,R),P.r8(c,R+1);out={}
        for y in range(h):
            for x in range(w):
                at=y*32+x;g=P.r16(c,R+2+at*2)&65535;o=P.r16(c,R+2050+at*2)&65535
                out[x,y]=(self.names.get(g,'none'),self.names.get(o,'none'),g,o)
        return w,h,out

    def find(self,prefix,exact=False):
        _,_,g=self.grid()
        return [(p,ns) for p,ns in g.items() if any((n==prefix if exact else n.startswith(prefix)) for n in ns[:2])]

    def clear(self):
        c=self.c;C.clear_enemies(c);actors=P.sym('gActors')
        for i in range(1,96):
            at=actors+i*64
            if P.r8(c,at)==7 and P.r8(c,at+1)==6:P.w8(c,at,0)

    def warp(self,cell):
        L.warp(self.c,cell,next(i for i,g in enumerate(self.world['cells'][cell]['gate']) if g));self.clear()

    def enter_natural(self,cell):
        c=self.c;m=P.r8(c,P.sym('gWorld')+M.MYST_OFF+cell)
        assert m,(cell,'has no generated mystery')
        self.warp(cell);found=self.find('mouth_');assert len(found)==1,found
        (mx,my),_=found[0];C.teleport(c,mx*16+8,(my+1)*16+14)
        for _ in range(40):
            P.hold(c,'UP',2)
            if C.area(c)==2:break
        assert C.wait_play(c,2),(cell,'failed to enter natural mouth')
        self.clear()
        return {'packed':m,'kind':M.KINDS[m&15],'size':(m>>4)&3,'style':(m>>6)&3}

    def boot(self,row):
        c=P.boot(rom=self.args.rom,seed=int(row['seed'],0));self.c=c;C.dismiss(c);self.world=C.world(c)
        if row['cell'] is not None:
            P.enter_forest(c)
            if row.get('interior'):self.mystery=self.enter_natural(row['cell'])
            else:self.warp(row['cell']);self.mystery=None
        else:self.mystery=None
        self.clear();C.heal(c)

    def safe(self,px,py):
        c=self.c;R=P.sym('gRoom');w,h=P.r8(c,R),P.r8(c,R+1)
        if px<8 or py<14 or px>=w*16-8 or py>=h*16:return False
        for y in range(py-12,py,4):
            for x in range(px-6,px+6,4):
                if P.r8(c,R+4098+(y//8)*64+x//8):return False
        mt=P.r16(c,R+2+((py-6)//16*32+px//16)*2)&65535
        return P.r8(c,P.sym('metatile_type')+mt)==0

    def settle(self,point,facing=0):
        c=self.c;C.teleport(c,*point);a=P.sym('gActors');P.w8(c,a+7,facing);P.w8(c,a+6,facing*8)
        for _ in range(96):self.clear();C.heal(c);c.run_frame()
        P.w16(c,P.sym('gFrame'),0);P.w16(c,P.sym('gFrame')+2,0)
        for _ in range(64):self.clear();C.heal(c);c.run_frame()

    def target(self,row):
        c=self.c;feature=row['feature'];w,h,g=self.grid()
        if feature=='control':return (12,16),[200,270],0,{}
        if feature=='drain_exit':return (9,2),[152,92],0,{}
        if feature=='pocket':
            S=P.sym('gSpots');kind=P.r8(c,S+57);assert kind,(row,'no pocket')
            target=(P.r8(c,S+55),P.r8(c,S+56));loot=(P.r8(c,S+44),P.r8(c,S+45))
            dx=(loot[0]>target[0])-(loot[0]<target[0]);dy=(loot[1]>target[1])-(loot[1]<target[1])
            face=1 if dx>0 else 3 if dx<0 else 2 if dy>0 else 0
            return target,[(target[0]-dx)*16+8,(target[1]-dy)*16+12],face,{'pocket_kind':kind,'loot':loot,'direction':KEYS[face]}
        if row.get('action')=='leave':
            target=(w//2-1,h-1);return target,[w*8,(h-2)*16-4],2,{}
        matches=self.find(feature,exact=not feature.endswith('_'))
        if feature=='chest' and row.get('interior'):matches=[(p,n) for p,n in g.items() if n[1]=='myst_chest']
        if not matches:return None
        if feature=='chest':matches=[v for v in matches if v[1][0]=='chest' or v[1][1]=='myst_chest' or v[1][0].endswith('_floor_chest')] or matches
        if feature=='chest' and row.get('interior'):
            matches=[(p,n) for p,n in g.items() if n[1]=='myst_chest']
        # Stand to the south on the real approach, keeping the target above Bloom.
        candidates=[]
        for (tx,ty),ns in matches:
            for dy in [36,32,40,44,28,48,52,24,-12,-20,-28,-36]:
                for dx in [0,-16,16,-32,32]:
                    px,py=tx*16+8+dx,ty*16+dy
                    if not self.safe(px,py):continue
                    cx=max(0,min(w*16-240,px-120));cy=max(0,min(h*16-160,py-104))
                    top=ty*16-(32 if feature=='mouth_' else 4)
                    visible=0<=tx*16-cx<=224 and 30<=top-cy and ty*16+16-cy<=160
                    if not visible:continue
                    score=abs(dx)*2+abs(dy-(30 if feature=='mouth_' else 40))
                    candidates.append((score,(tx,ty),[px,py],ns))
        if not candidates:return None
        _,target,point,ns=min(candidates,key=lambda v:v[0])
        return target,point,0,{'target_names':ns[:2]}

    def snapshot_state(self,target):
        c=self.c;a=P.sym('gActors');R=P.sym('gRoom');at=target[1]*32+target[0]
        return {'state':P.r8(c,a+2),'state_name':STATES[P.r8(c,a+2)],'position':list(P.player_pos(c)),
                'z_q16':P.r32(c,a+16),'hp':P.r16(c,P.sym('gPl')),'area':C.area(c),'game_state':C.gstate(c),
                'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],
                'target_ground':self.names.get(P.r16(c,R+2+at*2)&65535,'none'),
                'target_overlay':self.names.get(P.r16(c,R+2050+at*2)&65535,'none')}

    def record(self,row):
        self.boot(row);chosen=self.target(row)
        if not chosen:self.missing.append(row);print('MISSING',row,flush=True);self.save();return
        target,point,face,extra=chosen;c=self.c;action=row.get('action');events={}
        if action=='chest':
            point=[target[0]*16+8,target[1]*16+46]
            if not self.safe(*point):point=[target[0]*16+8,target[1]*16+30]
            events={8:[('UP',True)],36:[('UP',False)]}
        elif action=='enter':
            point=[target[0]*16+8,target[1]*16+42]
            if not self.safe(*point):point=[target[0]*16+8,target[1]*16+30]
            events={8:[('UP',True)],55:[('UP',False)]}
        elif action=='leave':events={8:[('DOWN',True)],56:[('DOWN',False)]}
        elif action=='shrine':
            target=(target[0],target[1]+1);point=[target[0]*16+8,target[1]*16+44]
            events={8:[('UP',True)],36:[('UP',False)]}
        elif action=='switch':
            point=[target[0]*16+40,target[1]*16+12];face=3;key='LEFT'
            if not self.safe(*point):point=[target[0]*16-24,target[1]*16+12];face=1;key='RIGHT'
            if not self.safe(*point):point=[target[0]*16+8,target[1]*16+32];face=0;key='UP'
            events={8:[(key,True)],34:[(key,False)]}
        elif action=='torch':
            point=[target[0]*16+8,target[1]*16+46];C.equip_b(c,C.EQ_LAMP)
            P.w8(c,P.sym('gPl')+8,P.r8(c,P.sym('gPl')+8)|4)
            events={8:[('UP',True)],25:[('UP',False),('A',True)],27:[('A',False)]}
        elif action in ('bomb','lamp','cape'):
            pl=P.sym('gPl');kind=extra['pocket_kind'];P.w8(c,pl+8,P.r8(c,pl+8)|{1:2,2:4,3:8}[kind]);P.w8(c,pl+7,10)
            C.equip_b(c,{1:C.EQ_BOMBS,2:C.EQ_LAMP,3:C.EQ_CLOAK}[kind]);key=extra['direction']
            if action=='cape':events={8:[(key,True)],11:[('A',True)],13:[('A',False)],36:[(key,False)]}
            else:
                events={8:[(key,True)],13:[(key,False),('A',True)],15:[('A',False)]}
                if action=='bomb':
                    back=KEYS[(face+2)%4];events[17]=[(back,True)];events[47]=[(back,False)]
        self.settle(point,face)
        if action=='shrine':P.w16(c,P.sym('gPl'),8)
        contract=B.contract(c);initial=self.snapshot_state(target);frames=[];trace=[];held=set();total=row.get('frames',64)
        for tick in range(total):
            for key,down in events.get(tick,[]):
                if down:held.add(key)
                else:held.discard(key)
            c.clear_keys(*range(10))
            if held:c.set_keys(*(P.key(c,k) for k in sorted(held)))
            if action!='shrine':C.heal(c)
            c.run_frame();frames.append(c.bg_video.to_pil().convert('RGB').copy());trace.append(self.snapshot_state(target))
        c.clear_keys(*range(10));name=row['name'];folder=self.out/name;folder.mkdir(exist_ok=True)
        selected=sorted(set([0,7,12,20,32,48,64,80,total-1]+[i for i in range(1,total) if (trace[i]['state'],trace[i]['area'],trace[i]['target_ground'],trace[i]['target_overlay'])!=(trace[i-1]['state'],trace[i-1]['area'],trace[i-1]['target_ground'],trace[i-1]['target_overlay'])]))
        selected=[i for i in selected if i<total]
        for i in selected:frames[i].save(folder/f'frame-{i:03}.png')
        gif=BR.make_gif(frames,self.out/f'{name}.gif')
        frames[0].save(self.out/f'{name}.png');self.filmstrip(name,frames,trace)
        checks=[]
        def check(n,v):checks.append({'name':n,'passed':bool(v)})
        if action=='chest':check('actual chest opens',any(t['state_name']=='itemget' for t in trace) or trace[-1]['target_ground']!=initial['target_ground'])
        elif action=='enter':check('actual generated entrance reaches interior',any(t['area']==2 for t in trace))
        elif action=='leave':check('actual interior exit returns to forest',any(t['area']==1 for t in trace))
        elif action=='shrine':
            check('injured Bloom receives shrine healing',initial['hp']==8 and any(t['hp']==P.r16(c,P.sym('gPl')+2) for t in trace))
            check('actual shrine trigger becomes spent',trace[-1]['target_ground']!=initial['target_ground'])
        elif action=='switch':check('actual floor plate becomes pressed',any(t['target_overlay']=='myst_switch_down' for t in trace))
        elif action=='torch':check('actual candle lights censer',any(t['target_ground']=='torch_lit' for t in trace))
        elif action in ('bomb','lamp'):check('actual item clears pocket barrier',trace[-1]['target_ground']!=initial['target_ground'])
        elif action=='cape':
            check('real cape jump gains height',any(t['z_q16']>8*65536 and t['state_name']=='jump' for t in trace))
            check('cape crosses without falling',not any(t['state_name']=='fall' for t in trace))
        result={**row,**extra,'stage':None if row['cell'] is None else self.world['cells'][row['cell']]['stage'],
                'mystery':self.mystery,'target':list(target),'position':point,'facing':face,'initial':initial,'physical_contract':contract,
                'video_frames':total,'inputs':{str(t):v for t,v in events.items()},'gif':gif,'native_frames':[f'{name}/frame-{i:03}.png' for i in selected],
                'image':name+'.png','filmstrip':name+'-frames.png','trace':trace,'checks':checks}
        if self.old:
            old=next(r for r in self.old['captures'] if r['name']==name)
            result['matched_case']={'same_seed':old['seed']==row['seed'],'same_cell':old['cell']==row['cell'],'same_target':old['target']==list(target),'same_position':old['position']==point,
                                     'same_initial_camera':old['initial']['camera']==initial['camera'],'same_physical_contract':old['physical_contract']==contract}
        self.rows.append(result);self.save();print('CAPTURE',name,'seed',row['seed'],'cell',row['cell'],'target',target,'checks',checks,flush=True)

    def filmstrip(self,name,frames,trace):
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
        out=Image.new('RGB',(960,4*182+24),'#101820');d=ImageDraw.Draw(out);d.text((8,6),name+' / actual full mGBA frames / chronological sampling',font=font,fill='#ece5c8')
        for n in range(16):
            tick=round(n*(len(frames)-1)/15);x=n%4*240;y=24+n//4*182;out.paste(frames[tick],(x,y));t=trace[tick]
            d.text((x+4,y+162),f'{tick:03} {t["state_name"]} area{t["area"]} {t["target_ground"][:20]}',font=font,fill='#ece5c8')
        out.save(self.out/f'{name}-frames.png')

    def save(self):
        checks=[v for r in self.rows for v in r['checks']]
        report={'rom_sha256':hashlib.sha256(Path(self.args.rom).read_bytes()).hexdigest(),'emulator':'mGBA 0.10.5','method':__doc__.strip(),'captures':self.rows,'count':len(self.rows),'missing':self.missing,'activation_checks':{'passed':sum(v['passed'] for v in checks),'total':len(checks)},'fixture_version':1}
        (self.out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out');ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP);ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'));ap.add_argument('--match');ap.add_argument('--only');args=ap.parse_args();review=Review(args)
    for row in plan():
        if args.only and row['name'] not in args.only.split(','):continue
        review.record(row)
    report=json.loads((Path(args.out)/'capture.json').read_text());checks=report['activation_checks'];print('RESULT',checks,'missing',len(review.missing),flush=True)
    return int(bool(review.missing) or checks['passed']!=checks['total'])


if __name__=='__main__':raise SystemExit(main())
