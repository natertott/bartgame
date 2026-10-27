"""Capture Bloom's complete implemented action suite from real mGBA runs.

python tools/bloom_suite_review.py OUT --rom ROM --map MAP --assets-header HEADER

Fixtures choose inventory, facing, position, and clear unrelated actors.
Every displayed action is triggered by ordinary input on actual generated
terrain. No terrain, action state, pose, or animation frame is injected.
Native PNGs preserve framebuffers; GIFs enlarge whole frames 2x. Filmstrips
crop around the live player for frame-by-frame inspection, without repainting.
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
import wood_probe as W
import bloom_probe as B
import bloom_review as R

KEYS=('UP','RIGHT','DOWN','LEFT')
STATES=('normal','roll','attack','hurt','fall','jump','itemget','dead','talk','frozen','lift','carry','swallowed')
ACTIONS=(('idle',1,(),32,0,0),('walk',1,('DIR',),48,34,48),
         ('roll',1,('DIR','R'),48,1,68),('sword',1,('B',),40,1,0),
         ('shield-wood',5,('B',),48,28,0),('shield-green',5,('B',),48,28,0),
         ('shield-walk',5,('B','DIR'),64,40,48),
         ('bow',6,('B',),44,1,0),('lamp',3,('B',),48,1,0),
         ('bomb',2,('B',),64,1,0),('cape',4,('B',),56,1,48))


def signed(c,at):
    v=P.r32(c,at)
    return v-(1<<32) if v>=1<<31 else v


class Suite:
    def __init__(self,args):
        self.args=args;self.defs=B.configure(args);self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=True)
        self.seed=int(args.seed,0);self.rows=[];self.missing=[];self.c=None;self.background=None
        self.old=json.loads(Path(args.match).read_text()) if args.match else None
        self.cache={n:B.static_symbol(n) for n in ('sLastFrame','sLastActionFrame','sLastShieldFrame','sUseTimer','sWalkTimer')}
        self.frames={v:k[7:].lower() for k,v in self.defs.items() if k.startswith('F_HERO_')}

    def boot(self):
        c=P.boot(rom=self.args.rom,seed=self.seed);C.dismiss(c);B.clear_actors(c)
        return c

    def enter(self,background):
        self.c=self.boot();self.background=background;self.cell=None
        if background=='drain':return
        c=self.c;self.world=C.world(c);P.enter_forest(c)
        if background=='cave':
            for cell,d in enumerate(self.world['cells']):
                if cell in (self.world['entry'],self.world['goal']):continue
                if M.enter(c,cell,'pots',2,0):self.cell=cell;B.clear_actors(c);return
            raise AssertionError('could not enter actual generated cave')
        choices=[i for i,d in enumerate(self.world['cells']) if (d['stage']<2 if background=='forest' else d['stage']>=3)]
        self.cell=choices[0] if background=='forest' else next((i for i in choices if i!=self.world['goal']),choices[0])
        self.warp(self.cell)

    def warp(self,cell):
        L.warp(self.c,cell,next(i for i,g in enumerate(self.world['cells'][cell]['gate']) if g));self.cell=cell;B.clear_actors(self.c)

    def spot(self,facing,travel):
        point=R.natural_spot(self.c,facing,travel)
        if point:return point
        if self.background in ('forest','blight'):
            for cell,d in enumerate(self.world['cells']):
                if (self.background=='forest' and d['stage']>=2) or (self.background=='blight' and d['stage']<3):continue
                self.warp(cell);point=R.natural_spot(self.c,facing,travel)
                if point:return point
        raise AssertionError((self.background,'no natural safe action lane',facing,travel))

    def reset(self,point,facing,equipment=1,upgraded=False):
        c=self.c;B.reset_player(c,*point,facing=facing,equipment=(0,equipment,0))
        # Reset's full inventory intentionally omits the aesthetic shield bit.
        P.w8(c,P.sym('gPl')+36,0x0f|(0x10 if upgraded else 0));P.run(c,64)

    def trace(self):
        c=self.c;a=P.sym('gActors');pl=P.sym('gPl');s=P.r8(c,a+2)
        frame=P.r8(c,self.cache['sLastFrame'])
        oam=B.oam(c);objects=[]
        for i in range(1,96):
            at=a+i*64;kind=P.r8(c,at)
            if kind in (3,6):objects.append({'slot':i,'kind':kind,'type':P.r8(c,at+1),
                'position':[signed(c,at+8)>>16,signed(c,at+12)>>16],
                'z_q16':signed(c,at+16),'timer':P.r8(c,at+4)})
        return {'state':s,'state_name':STATES[s] if s<len(STATES) else str(s),'sub':P.r8(c,a+3),
                'timer':P.r8(c,a+4),'facing':P.r8(c,a+7),'position':list(P.player_pos(c)),
                'z_q16':signed(c,a+16),'zvel_q16':signed(c,a+20),'hero_frame':frame,
                'hero_frame_name':self.frames.get(frame,str(frame)),'effect_frame':P.r16(c,self.cache['sLastActionFrame'])&65535,
                'shield_frame':P.r8(c,self.cache['sLastShieldFrame']),'use_timer':P.r8(c,self.cache['sUseTimer']),
                'walk_timer':P.r8(c,self.cache['sWalkTimer']),'sword_active':P.r8(c,pl+21),
                'sword_phase':P.r8(c,pl+22),'carry':P.r8(c,pl+33),'shield_up':P.r8(c,pl+34),
                'hp':P.r16(c,pl),'lamp_timer':P.r8(c,pl+23),'items2':P.r8(c,pl+36),
                'objects':objects,'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],
                'game_state':P.r8(c,P.sym('gGame')),'area':C.area(c),'cell':C.cell(c),
                'oam':[v for v in oam if v['pal']<13 and v['y']>28 and v['shape'] in (0,1)]}

    def record(self,name,facing,total,events,point=None,note=None):
        c=self.c;directory=self.out/name;directory.mkdir(exist_ok=True);frames=[];traces=[]
        initial={'background':self.background,'cell':self.cell,'position':list(point or P.player_pos(c)),
                 'facing':B.FACES[facing],'area':C.area(c)}
        held=set()
        for tick in range(total):
            if tick in events:
                for key,down in events[tick]:
                    if down:held.add(key)
                    else:held.discard(key)
                c.clear_keys(*range(10))
                if held:c.set_keys(*(P.key(c,key) for key in sorted(held)))
            c.run_frame();frames.append(c.bg_video.to_pil().convert('RGB').copy());traces.append(self.trace())
        c.clear_keys(*range(10))
        selected=sorted(set([0,7,8,10,12,16,20,24,28,32,total-1]+[i for i in range(1,total) if traces[i]['state']!=traces[i-1]['state'] or traces[i]['hero_frame']!=traces[i-1]['hero_frame']]))
        # Save useful frame changes, capped to keep the review repository compact.
        selected=[i for i in selected if i<total]
        if len(selected)>24:selected=selected[:20]+selected[-4:]
        for tick in selected:frames[tick].save(directory/f'frame-{tick:03d}.png')
        gif=R.make_gif(frames,self.out/(name+'.gif'))
        self.filmstrip(name,frames,traces)
        row={'name':name,**initial,'video_frames':total,'inputs':{str(k):v for k,v in events.items()},
             'gif':gif,'native_frames':[f'{name}/frame-{i:03d}.png' for i in selected],
             'filmstrip':name+'-frames.png','states':sorted(set(t['state_name'] for t in traces)),
             'poses':sorted(set(t['hero_frame_name'] for t in traces)),'trace':traces}
        expected=None
        if '-roll-' in name:expected='roll'
        elif '-sword-' in name:expected='attack'
        elif '-cape-' in name:expected='jump'
        elif name.startswith('lift-carry-throw-'):expected='carry'
        elif name in ('forest-drowning','forest-pit-fall'):expected='fall'
        validations=[]
        def valid(label,ok):
            validations.append({'name':label,'passed':bool(ok)})
            assert ok,(name,label,row['states'],row['poses'])
        if expected:valid('expected action state '+expected,expected in row['states'])
        if '-roll-' in name:valid('roll has at least four actual tumble poses',sum(p.startswith('roll_') for p in row['poses'])>=4)
        if '-shield-' in name:
            valid('shield raised from held item button',any(t['shield_up'] for t in traces))
            if '-green-' in name:valid('green shield upgrade flag is enabled',all(t['items2']&0x10 for t in traces))
            else:valid('wooden shield upgrade flag is disabled',all(not(t['items2']&0x10) for t in traces))
        if '-walk-' in name or '-roll-' in name:valid('directional action actually travels',max(abs(t['position'][0]-initial['position'][0])+abs(t['position'][1]-initial['position'][1]) for t in traces)>=8)
        if '-bow-' in name:valid('real arrow projectile emitted',any(o['kind']==3 and o['type']==3 for t in traces for o in t['objects']))
        if '-bomb-' in name:valid('real armed bomb object emitted',any(o['kind']==6 and o['type']==5 for t in traces for o in t['objects']))
        if '-lamp-' in name:valid('real lamp interaction window entered',any(t['lamp_timer'] for t in traces))
        if '-cape-' in name:valid('cape visibly gains height',max(t['z_q16'] for t in traces)>=8*65536)
        if name.startswith('lift-carry-throw-'):
            valid('real carried load present',any(t['carry'] for t in traces))
            valid('real thrown load actor released',any(o['kind']==6 and o['type']==20 for t in traces for o in t['objects']))
            if name.endswith('sword-drop'):valid('sword interrupts carry after releasing load','attack' in row['states'])
        if 'drowning' in name:valid('water fall subtype is active',any(t['state']==4 and t['sub']==1 for t in traces))
        if 'pit-fall' in name:valid('pit fall subtype is active',any(t['state']==4 and t['sub']==0 for t in traces))
        if name.endswith('ledge-jump'):valid('actual ledge-drop jump entered',any(t['state']==5 and t['sub']==1 for t in traces))
        if 'hurt-' in name:valid('actual contact hurt state entered','hurt' in row['states'])
        if name.endswith('-death'):valid('actual death state entered','dead' in row['states'])
        if name.endswith('item-get-bow'):valid('actual chest invokes item-get state','itemget' in row['states'])
        if name.endswith('cap-return-drop-in'):
            valid('cap invokes actual swallow state','swallowed' in row['states'])
            valid('cap returns through ceiling drop',any(t['area']==0 and t['state']==5 and t['sub']==2 and t['z_q16']>32*65536 for t in traces))
        if name.endswith('forest-transition'):valid('ordinary exit reaches forest',any(t['area']==1 for t in traces))
        row['validations']=validations
        if note:row['fixture_note']=note
        if self.old:
            prior=next((r for r in self.old['captures'] if r['name']==name),None)
            if prior:
                for field in ('background','cell','position','facing','area','inputs','video_frames'):
                    assert row[field]==prior[field],(name,field,row[field],prior[field])
                fields=('state','sub','timer','position','z_q16','zvel_q16','sword_active','sword_phase','carry','shield_up','hp','game_state','area')
                different=[{'tick':tick,'fields':[k for k in fields if a[k]!=b[k]]}
                           for tick,(a,b) in enumerate(zip(row['trace'],prior['trace']))
                           if any(a[k]!=b[k] for k in fields)]
                row['gameplay_comparison']={'matched_fixture':True,'identical_frames':len(traces)-len(different),'different_frames':different}
        self.rows.append(row);self.save();print('CAPTURE',name,row['states'],row['poses'],flush=True)

    def filmstrip(self,name,frames,traces):
        count=16;ticks=sorted(set(round(i*(len(frames)-1)/(count-1)) for i in range(count)))
        w,h=172,198;sheet=Image.new('RGB',(w*4,40+h*4),'#101820');draw=ImageDraw.Draw(sheet)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
        draw.text((8,8),name+' / actual mGBA crops / temporal sampling',font=font,fill='#eee9d7')
        for k,tick in enumerate(ticks):
            t=traces[tick];x,y=t['position'];cx,cy=t['camera'];sx,sy=x-cx,y-cy
            crop=frames[tick].crop((sx-40,sy-66,sx+40,sy+14)).resize((160,160),Image.Resampling.NEAREST)
            x0=(k%4)*w+6;y0=40+(k//4)*h;sheet.paste(crop,(x0,y0))
            draw.text((x0,y0+162),f'{tick:03d} {t["state_name"]} t{t["timer"]} z{t["z_q16"]/65536:.1f}',font=font,fill='#eee9d7')
            draw.text((x0,y0+176),t['hero_frame_name'],font=font,fill='#9eafba')
        sheet.save(self.out/(name+'-frames.png'))

    def save(self):
        report={'rom_sha256':hashlib.sha256(Path(self.args.rom).read_bytes()).hexdigest(),'seed':hex(self.seed),'fixture_version':3,
                'emulator':'mGBA 0.10.5','method':'Real button actions on natural generated terrain. Inventory/position/facing and cleared unrelated actors are fixtures. No terrain or action pose/frame injection. Full native PNGs; GIFs enlarge whole frames 2x/sample30fps; filmstrips crop live player positions.',
                'implemented_states':list(STATES),'not_implemented':['swimming','running/sprint'],
                'activation_checks':{'passed':sum(v['passed'] for r in self.rows for v in r.get('validations',[])),
                                     'total':sum(len(r.get('validations',[])) for r in self.rows)},
                'captures':self.rows,'missing':self.missing}
        seen={t['hero_frame'] for r in self.rows for t in r['trace'] if t['game_state']==1 and t['hero_frame'] in self.frames}
        report['pose_coverage']={'seen':[self.frames[i] for i in sorted(seen)],
                                 'not_seen':[self.frames[i] for i in sorted(set(self.frames)-seen)]}
        (self.out/'suite.json').write_text(json.dumps(report,indent=2)+'\n')

    def actions(self,background):
        self.enter(background)
        if background=='drain':plan=[(a,f) for a in ACTIONS for f in range(4)]
        else:
            wanted=[('sword',0),('sword',1),('shield-wood',0),('shield-wood',2),('cape',0),('cape',1),('lamp',0),('bow',0),('bomb',0)]
            plan=[(next(a for a in ACTIONS if a[0]==name),f) for name,f in wanted]
        for (action,eq,keys,total,held,travel),f in plan:
            name=background+'-'+action+'-'+B.FACES[f]
            prior=next((r for r in self.old['captures'] if r['name']==name),None) if self.old else None
            if prior:
                if self.background in ('forest','blight') and self.cell!=prior['cell']:self.warp(prior['cell'])
                point=prior['position']
            else:point=self.spot(f,travel)
            self.reset(point,f,eq,action=='shield-green')
            actual=[KEYS[f] if key=='DIR' else key for key in keys]
            events={8:[(key,True) for key in actual],8+held:[(key,False) for key in actual]}
            self.record(name,f,total,events,point)

    def find_lift(self,name,facing=None):
        for cell,d in enumerate(self.world['cells']):
            self.warp(cell);found=self.lift_target(name,facing)
            if found:return found
        return None

    def lift_target(self,name,facing=None):
        if facing is None:return L.find_tile(self.c,name)
        _,_,g=C.room_tiles(self.c);want=C.mt(name)
        dx,dy=((0,-1),(1,0),(0,1),(-1,0))[facing]
        for (x,y),v in g.items():
            if v!=want:continue
            at=(x-dx,y-dy);near=g.get(at)
            if near is not None and P.r8(self.c,P.sym('metatile_type')+near)==0:
                return x,y,at,KEYS[facing]
        return None

    def specials(self):
        self.enter('forest')
        lift_plan=[('bush','BUSH',None),('rock','ROCK_SMALL',None),('boulder','BOULDER',None),('pot','CAVE_FLOOR_LIFT',None)]
        lift_plan += [('bush-'+B.FACES[f],'BUSH',f) for f in range(4)]
        lift_plan += [('bush-sword-drop','BUSH',0)]
        for label,mt,want_facing in lift_plan:
            self.enter('forest')
            if label in ('pot','boulder'):
                kind='pots' if label=='pot' else 'boulders'
                for cell,d in enumerate(self.world['cells']):
                    if cell not in (self.world['entry'],self.world['goal']) and M.enter(self.c,cell,kind,2,0):self.cell=cell;break
                B.clear_actors(self.c);self.background='cave'
                found=self.lift_target(mt,want_facing)
            else:found=self.find_lift(mt,want_facing)
            if not found:self.missing.append(label+' natural lift target');continue
            _,_,tile,key=found;f=KEYS.index(key);point=(tile[0]*16+8,tile[1]*16+14)
            self.reset(point,f)
            release='B' if label.endswith('sword-drop') else 'R'
            events={8:[('R',True)],9:[('R',False)],24:[(KEYS[(f+1)%4],True)],
                    35:[(KEYS[(f+1)%4],False),(KEYS[(f+3)%4],True)],46:[(KEYS[(f+3)%4],False)],
                    52:[(release,True)],53:[(release,False)]}
            self.record('lift-carry-throw-'+label,f,100,events,point,'Natural '+label+' lifted with R, carried out and back to show both walking poses, then released with '+release+'.')
        # Water is entered by walking off a natural bank; there is no swim state.
        self.enter('forest');found=None
        import guard_probe as G
        for cell,d in enumerate(self.world['cells']):
            self.warp(cell);found=G.water_edge(self.c)
            if found:break
        if found:
            tx,ty=found;point=((tx-1)*16+6,ty*16+12);self.reset(point,1)
            self.record('forest-drowning',1,88,{8:[('RIGHT',True)],30:[('RIGHT',False)]},point)
        else:self.missing.append('natural water bank')
        # A real chasm gate supplies the hole; walk into it without jumping.
        self.enter('forest')
        chasm=next(((i,s) for i,d in enumerate(self.world['cells']) for s,g in enumerate(d['gate']) if g==6),None)
        if chasm:
            cell,side=chasm;self.warp(cell);x,y,key=C.door_inside(side);point=(x,y);f=KEYS.index(key);self.reset(point,f)
            self.record('forest-pit-fall',f,90,{8:[(key,True)],30:[(key,False)]},point)
        else:self.missing.append('natural chasm gate')
        # Natural ledge, approach from its permitted side and keep walking.
        self.enter('forest');found=None
        for cell,d in enumerate(self.world['cells']):
            self.warp(cell);w,h,g=C.room_tiles(self.c)
            for (x,y),mt in g.items():
                typ=P.r8(self.c,P.sym('metatile_type')+mt)
                if typ not in (4,5,6,7):continue
                f=typ-4;dx,dy=((0,-1),(1,0),(0,1),(-1,0))[f]
                if g.get((x-dx,y-dy)) is not None and P.r8(self.c,P.sym('metatile_type')+g[x-dx,y-dy])==0:
                    found=(x,y,f,dx,dy);break
            if found:break
        if found:
            x,y,f,dx,dy=found;point=((x-dx)*16+8,(y-dy)*16+12);self.reset(point,f)
            self.record('forest-ledge-jump',f,84,{8:[(KEYS[f],True)],46:[(KEYS[f],False)]},point)
        else:self.missing.append('natural ledge')
        # Hurt/death are caused by an actual, spawned enemy's collision.
        for fatal,f in [(False,f) for f in range(4)]+[(True,2)]:
            self.enter('forest');point=self.spot(f,0);self.reset(point,f)
            if fatal:P.w16(self.c,P.sym('gPl'),2)
            i=W.spawn_enemy(self.c,0,point[0],point[1]-8);at=P.sym('gActors')+i*64
            P.w8(self.c,at+29,0);P.w16(self.c,at+32,0)
            self.record('forest-'+('death' if fatal else 'hurt-'+B.FACES[f]),f,100 if fatal else 48,{},point,'Enemy spawn/position fixture; ordinary contact damage triggers the actual action.')
        # Cap entry, swallow, transition and ceiling drop occur from item input.
        self.enter('forest');point=self.spot(2,0);self.reset(point,2,7)
        self.record('forest-cap-return-drop-in',2,200,{8:[('B',True)],9:[('B',False)]},point)
        # The bow chest invokes the game's genuine item-get presentation.
        self.enter('forest');cell=next((i for i,d in enumerate(self.world['cells']) if d['role']==4 and d['arg']==6),None)
        if cell is not None:
            self.warp(cell);found=L.find_tile(self.c,'CHEST')
            if found:
                _,_,tile,key=found;point=(tile[0]*16+8,tile[1]*16+14);f=KEYS.index(key);self.reset(point,f)
                self.record('forest-item-get-bow',f,125,{8:[(key,True)],26:[(key,False)],80:[('A',True)],81:[('A',False)]},point)
            else:self.missing.append('bow chest accessible front')
        else:self.missing.append('bow chest role')
        # Ordinary room exit: walk through the Drain's actual forest entrance.
        self.enter('drain');ex,ey=P.hall_exit(self.c);point=(ex*16+8,(ey+2)*16+10);self.reset(point,0)
        self.record('drain-forest-transition',0,200,{8:[('UP',True)],68:[('UP',False)]},point)
        self.save()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out')
    ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--seed',default='0xB4A7');ap.add_argument('--groups',default='drain,forest,blight,cave,special')
    ap.add_argument('--match');args=ap.parse_args();suite=Suite(args)
    for group in args.groups.split(','):
        if group=='special':suite.specials()
        else:suite.actions(group)
    suite.save();print('PASS:',len(suite.rows),'genuine action clips; missing:',suite.missing,flush=True)


if __name__=='__main__':main()
