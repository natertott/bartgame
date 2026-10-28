"""Capture the complete reboot from actual mGBA runs, never source mockups.

Seeds, room navigation, inventory, facing/position and cleared unrelated actors
are fixtures. Generated terrain and mystery descriptors are not modified.
Ordinary inputs animate Bloom, use entrances/items, open menus and finish the
Heart fight. Exact240x160 frames accompany nearest-neighbour2x GIFs.
Controlled ordinary enemy-contact fixtures are labelled in action reports.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont
import probe as P
import critical_path as C
import lift_probe as L
import myst_probe as M
import bloom_probe as B
import bloom_review as BR
import bloom_suite_review as BS
import interactive_review as IR

STATES=BS.STATES
STYLES=('cave','hollow','thicket')


def actual_mystery(c,cell):
    return P.r8(c,P.sym('gWorld')+M.MYST_OFF+cell)


def enter_natural(c,world,cell,clear=True):
    packed=actual_mystery(c,cell)
    if not packed:return False
    L.warp(c,cell,next(i for i,g in enumerate(world['cells'][cell]['gate']) if g))
    if clear:C.clear_enemies(c)
    _,_,grid=C.room_tiles(c)
    mouths=[(x,y) for (x,y),mt in grid.items() if mt in {
        C.mt('MOUTH_CAVE'),C.mt('MOUTH_HOLLOW'),C.mt('MOUTH_THICKET')}]
    if len(mouths)!=1:return False
    x,y=mouths[0];C.teleport(c,x*16+8,(y+1)*16+14)
    for _ in range(40):
        P.hold(c,'UP',2)
        if C.area(c)==2:break
    return C.wait_play(c,2)


class NativeSuite(BS.Suite):
    """Reuse the real-input suite, replacing its old mystery test fixture."""
    def enter(self,background):
        if background!='cave':return super().enter(background)
        self.c=self.boot();self.background='cave';self.world=C.world(self.c)
        P.enter_forest(self.c)
        candidates=[cell for cell in range(25) if (actual_mystery(self.c,cell)>>6)==0
                    and ((actual_mystery(self.c,cell)>>4)&3)>=1
                    and (actual_mystery(self.c,cell)&15) in (1,2,3,4)]
        for cell in candidates:
            if enter_natural(self.c,self.world,cell):
                self.cell=cell;B.clear_actors(self.c);return
        raise AssertionError('seed %s has no natural medium/large quiet cave'%hex(self.seed))

    def record(self,*args,**kwargs):
        # The compact body intentionally samples its new feet centre. Give
        # the real south chasm approach a few extra walking updates instead of
        # ending one pixel before that centre reaches the hole.
        if args and args[0]=='forest-pit-fall' and len(args)>3:
            values=list(args);events={tick:list(keys) for tick,keys in values[3].items()}
            if 30 in events:events[36]=events.pop(30)
            values[3]=events;args=tuple(values)
        original=self.background;packed=None
        if C.area(self.c)==2:
            packed=actual_mystery(self.c,self.cell)
            self.background=STYLES[packed>>6]
        before=len(self.rows)
        super().record(*args,**kwargs)
        self.background=original
        if len(self.rows)>before:
            self.rows[-1]['seed']=hex(self.seed)
            self.rows[-1]['natural_mystery']=packed
            self.save()

    def natural_lift(self,label,seed,cell,tile_name,facing=None):
        self.seed=seed;self.enter('forest')
        if label in ('pot','boulder'):
            if not enter_natural(self.c,self.world,cell):
                self.missing.append(label+' actual generated entrance');return
            self.cell=cell;self.background=STYLES[actual_mystery(self.c,cell)>>6]
            B.clear_actors(self.c);found=self.lift_target(tile_name,facing)
        else:
            self.warp(cell);found=self.lift_target(tile_name,facing)
            if not found:found=self.find_lift(tile_name,facing)
        if not found:self.missing.append(label+' actual lift approach');return
        _,_,at,key=found;f=BS.KEYS.index(key);point=(at[0]*16+8,at[1]*16+14)
        self.reset(point,f)
        events={8:[('R',True)],9:[('R',False)],24:[(BS.KEYS[(f+1)%4],True)],
                35:[(BS.KEYS[(f+1)%4],False),(BS.KEYS[(f+3)%4],True)],
                46:[(BS.KEYS[(f+3)%4],False)],52:[('R',True)],53:[('R',False)]}
        self.record('lift-carry-throw-'+label,f,100,events,point,
                    'Real lift/turn/throw on naturally generated terrain; inventory and positioning are fixtures.')


class Review:
    def __init__(self,args):
        self.args=args;P.ROM=args.rom;self.defs=B.configure(args)
        self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=True)
        self.rows=[];self.failures=[];self.c=None;self.seed=int(args.seed,0)
        prior=self.out/'review.json'
        if getattr(args,'resume',False) and prior.exists():
            report=json.loads(prior.read_text())
            assert report['rom_sha256']==hashlib.sha256(Path(args.rom).read_bytes()).hexdigest()
            self.rows=report['captures'];self.failures=report['failures']
        self.pose=B.static_symbol('sLastFrame')

    def boot(self,seed=None,title=False):
        self.seed=self.seed if seed is None else seed
        self.c=P.boot(rom=self.args.rom,seed=self.seed,start=not title)
        if not title:C.dismiss(self.c)
        return self.c

    def safe(self,px,py):
        c=self.c;room=P.sym('gRoom');w=P.r8(c,room);h=P.r8(c,room+1)
        if not (8<=px<w*16-8 and 12<=py<h*16):return False
        for y in (py-8,py-4,py-1):
            for x in (px-5,px,px+4):
                if P.r8(c,room+4098+(y//8)*64+x//8):return False
        mt=P.r16(c,room+2+(((py-4)//16)*32+px//16)*2)&65535
        return P.r8(c,P.sym('metatile_type')+mt)==0

    def focus(self,point,clear=True):
        if clear:C.clear_enemies(self.c)
        C.teleport(self.c,*point)
        for _ in range(96):C.heal(self.c);self.c.run_frame()

    def state(self):
        c=self.c;s=P.r8(c,P.sym('gActors')+2)
        return {'game_state':C.gstate(c),'area':C.area(c),'cell':C.cell(c),
                'state':s,'state_name':STATES[s] if s<len(STATES) else str(s),
                'hero_pose':P.r8(c,self.pose),'position':list(P.player_pos(c)),
                'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],
                'hp':P.r16(c,P.sym('gPl')),'oam_count':P.r8(c,P.sym('gOamCount'))}

    def record(self,name,frames=64,events=None,note='',expect=None,heal=True):
        c=self.c;events=events or {};images=[];trace=[];held=set();directory=self.out/name;directory.mkdir(exist_ok=True)
        for tick in range(frames):
            for key,down in events.get(tick,[]):
                if down:held.add(key)
                else:held.discard(key)
            c.clear_keys(*range(10))
            if held:c.set_keys(*(P.key(c,k) for k in held))
            if heal:C.heal(c)
            c.run_frame();images.append(c.bg_video.to_pil().convert('RGB').copy());trace.append(self.state())
        c.clear_keys(*range(10));selected=sorted({0,frames//4,frames//2,frames*3//4,frames-1})
        for tick in selected:images[tick].save(directory/f'frame-{tick:03}.png')
        images[0].save(self.out/(name+'.png'))
        gif=BR.make_gif(images,self.out/(name+'.gif'))
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
        sheet=Image.new('RGB',(960,4*178+22),'#101820');d=ImageDraw.Draw(sheet);d.text((6,4),name+' / actual mGBA frames / chronological',font=font,fill='#e8e0c0')
        for i in range(16):
            tick=round(i*(frames-1)/15);x=i%4*240;y=22+i//4*178;sheet.paste(images[tick],(x,y))
            d.text((x+4,y+162),f'{tick:03} {trace[tick]["state_name"]} area{trace[tick]["area"]}',font=font,fill='#e8e0c0')
        sheet.save(self.out/(name+'-frames.png'))
        passed=True if expect is None else bool(expect(trace))
        if not passed:self.failures.append(name)
        row={'name':name,'seed':hex(self.seed),'video_frames':frames,'inputs':events,'note':note,
             'initial':trace[0],'passed':passed,'image':name+'.png','gif':gif,
             'native_frames':[f'{name}/frame-{tick:03}.png' for tick in selected],
             'filmstrip':name+'-frames.png','trace':trace}
        self.rows.append(row);self.save();print('CAPTURE',name,'PASS' if passed else 'FAIL',flush=True)

    def save(self):
        report={'rom_sha256':hashlib.sha256(Path(self.args.rom).read_bytes()).hexdigest(),
                'method':__doc__.strip(),'emulator':'mGBA 0.10.5','captures':self.rows,
                'count':len(self.rows),'failures':self.failures}
        (self.out/'review.json').write_text(json.dumps(report,indent=2)+'\n')

    def scenes(self):
        self.boot(title=True);P.run(self.c,60);self.record('title-screen',96)
        self.boot();
        for name,point in [('drain-ladder',(152,92)),('drain-lower-hall',(200,270)),('drain-keepers',(328,126))]:
            self.focus(point);self.record(name,note='Actual painted Drain room; position and settled camera are fixtures.')
        world=C.world(self.c);P.enter_forest(self.c)
        for cell,desc in enumerate(world['cells']):
            L.warp(self.c,cell,next(i for i,g in enumerate(desc['gate']) if g));C.clear_enemies(self.c)
            point=BR.natural_spot(self.c,2,0)
            if point is None:
                side=next(i for i,g in enumerate(desc['gate']) if g);point=C.door_inside(side)[:2]
            self.focus(point)
            self.record(f'forest-cell-{cell:02}-stage{desc["stage"]}',note='Generated room; cleared unrelated enemies and safe standing point are fixtures.')
        # All three mystery materials are selected from actual descriptors.
        seen=set()
        for seed in (0xB4A7,6,7,11):
            self.boot(seed);world=C.world(self.c);P.enter_forest(self.c)
            for cell in range(25):
                packed=actual_mystery(self.c,cell)
                if not packed or packed>>6 in seen:continue
                if not enter_natural(self.c,world,cell):continue
                C.clear_enemies(self.c);point=BR.natural_spot(self.c,2,0)
                if point:self.focus(point)
                style=packed>>6;self.record('interior-'+STYLES[style],note=f'Entered naturally generated kind{packed&15}, size{(packed>>4)&3}, cell{cell}; no descriptor injection.')
                seen.add(style)
            if len(seen)==3:break
        if len(seen)!=3:self.failures.append('all three naturally generated interior styles')
        self.save()

    def interfaces(self):
        self.boot(0xB4A7);c=self.c;pl=P.sym('gPl');P.w16(c,pl+4,123)
        self.focus((344,116));P.hold(c,'UP',6);P.press(c,'A',2,90)
        self.record('dialogue-gatekeeper',48,note='Actual talk input.',expect=lambda _:P.r8(c,B.static_symbol('sTbFace'))==2)
        C.dismiss(c);self.focus((72,118));P.hold(c,'UP',6);P.press(c,'A',2,30)
        self.record('shop-peddler',48,note='Actual shop input; gilt is an inventory fixture.',expect=lambda _:P.r8(c,B.static_symbol('sShopActive'))==1)
        P.press(c,'A',2,90);self.record('dialogue-peddler',48,note='Actual purchase response.');C.dismiss(c)
        P.w8(c,pl+8,0x7f);P.w8(c,pl+36,0x1f);P.w8(c,pl+7,30);P.w8(c,pl+35,40);P.w8(c,pl+6,3)
        P.enter_forest(c);P.press(c,'START',2,12);self.record('menu-bag',48,expect=lambda _:C.gstate(c)==3)
        P.press(c,'R',2,12);self.record('menu-key-items',48,expect=lambda _:C.gstate(c)==3)
        P.press(c,'R',2,20);self.record('menu-map-overview',48,expect=lambda _:C.gstate(c)==3)
        P.press(c,'A',2,20);self.record('menu-map-zoom',48,expect=lambda _:C.gstate(c)==3)
        P.press(c,'B',2,10);P.press(c,'START',2,12)
        # Ordinary quest dialogue uses the real NPC placement and A input.
        world=C.world(c)
        for role,name,portrait in ((5,'hermit',3),(6,'nun',4),(7,'gardener',5)):
            cell=next((i for i,d in enumerate(world['cells']) if d['role']==role),None)
            if cell is None:self.failures.append(name+' actual NPC role');continue
            L.warp(c,cell,next(i for i,g in enumerate(world['cells'][cell]['gate']) if g));C.clear_enemies(c)
            x,y=P.r8(c,P.sym('gSpots')+27),P.r8(c,P.sym('gSpots')+28)
            self.focus((x*16+8,(y+1)*16+14));P.hold(c,'UP',6);P.press(c,'A',2,90)
            self.record('dialogue-'+name,48,note='Actual generated quest NPC and talk input.',expect=lambda _,p=portrait:P.r8(c,B.static_symbol('sTbFace'))==p)
            C.dismiss(c)

    def actors(self):
        seen=set()
        for seed in (0xB4A7,6,7):
            self.boot(seed);world=C.world(self.c);P.enter_forest(self.c)
            for cell,desc in enumerate(world['cells']):
                L.warp(self.c,cell,next(i for i,g in enumerate(desc['gate']) if g))
                candidates=[(i,P.actor(self.c,i)) for i in range(1,96) if P.actor(self.c,i)['kind']==2]
                for index,actor in candidates:
                    kind=actor['type']
                    if kind>=5 or kind in seen:continue
                    px,py=actor['x'],actor['y'];point=next(((px+dx,py+dy) for dx,dy in ((0,48),(48,0),(-48,0),(0,-40),(32,32),(-32,32)) if self.safe(px+dx,py+dy)),None)
                    if point is None:continue
                    for other,_ in candidates:
                        if other!=index:P.w8(self.c,P.sym('gActors')+other*64,0)
                    self.focus(point,clear=False)
                    names=('beetle','bat','spitter','slime','knight')
                    self.record('enemy-'+names[kind],96,note='Target enemy is naturally spawned; unrelated enemies cleared, player positioned and healed.')
                    seen.add(kind);break
            if len(seen)==5:break
        if len(seen)!=5:self.failures.append('all five naturally generated common enemy types')
        self.save()

    def ending(self):
        self.boot(0xB4A7);c=self.c;world=C.world(c);P.enter_forest(c);goal=world['goal']
        L.warp(c,goal,next(i for i,g in enumerate(world['cells'][goal]['gate']) if g));C.heal(c)
        self.record('heart-boss',80,note='Naturally spawned final boss in generated goal room; navigation/healing fixtures.')
        pl=P.sym('gPl');P.w8(c,pl+8,0x7f);P.w8(c,pl+9,0);P.w8(c,pl+10,1);P.w8(c,pl+11,5)
        C.S=str(self.out/'ending-steps');Path(C.S).mkdir(exist_ok=True)
        C.boss_fight(c)
        self.record('victory-screen',64,note='Actual sword fight and Grail collection reached the completion screen; healing/inventory fixture.',expect=lambda _:C.gstate(c)==6)

    def death_return(self):
        self.boot(0xB4A7);c=self.c;world=C.world(c);P.enter_forest(c)
        found=None
        for cell,desc in enumerate(world['cells']):
            L.warp(c,cell,next(i for i,g in enumerate(desc['gate']) if g))
            found=next((P.actor(c,i) for i in range(1,96) if P.actor(c,i)['kind']==2 and P.actor(c,i)['type']==0),None)
            if found:break
        if found is None:self.failures.append('natural contact enemy for death return');return
        C.teleport(c,found['x'],found['y']+5);P.w16(c,P.sym('gPl'),2)
        P.w8(c,P.sym('gActors')+28,0)
        self.record('bloom-death-and-return',320,heal=False,
                    note='Actual contact with a naturally spawned beetle; injured2HP and position are fixtures. The game performs death, return and Bloom dialogue.',
                    expect=lambda trace:any(r['state_name']=='dead' for r in trace) and trace[-1]['area']==0)


def actions(args,out):
    rows=[]
    wanted=set(args.action_groups.split(','))
    for background in ('drain','forest','blight','cave'):
        folder=out/background;ns=SimpleNamespace(rom=args.rom,map=args.map,assets_header=args.assets_header,
            out=str(folder),seed='11' if background=='cave' else args.seed,only=None,match=None)
        if background in wanted:
            suite=NativeSuite(ns);suite.actions(background);suite.save()
        if (folder/'suite.json').exists():
            report=json.loads((folder/'suite.json').read_text())
            rows.append({'group':background,'report':str(folder.relative_to(out)/'suite.json'),'captures':len(report['captures']),'missing':report['missing']})
    if 'special' not in wanted:
        if (out/'special/suite.json').exists():
            report=json.loads((out/'special/suite.json').read_text());rows.append({'group':'special','report':'special/suite.json','captures':len(report['captures']),'missing':report['missing']})
        return rows
    ns=SimpleNamespace(rom=args.rom,map=args.map,assets_header=args.assets_header,out=str(out/'special'),seed=args.seed,only=None,match=None)
    suite=NativeSuite(ns)
    for label,seed,cell,name in [('bush',0xB4A7,16,'BUSH'),('rock',0xB4A7,16,'ROCK_SMALL'),('pot',0xB4A7,12,'CAVE_FLOOR_LIFT'),('boulder',7,17,'BOULDER')]:
        suite.natural_lift(label,seed,cell,name)
    # The remaining inherited specials run through real inputs. Replace its
    # old descriptor test helper with a strict natural-mystery selector.
    original=M.enter
    def natural_only(c,cell,kind,size,style):
        packed=actual_mystery(c,cell)
        if not packed or (packed&15)!=M.KINDS.index(kind):return False
        return enter_natural(c,C.world(c),cell)
    M.enter=natural_only
    try:
        # Supplemental source suite covers drowning, pit/ledge, hurt/death,
        # cap return, item-get and the actual Drain exit. Any absent natural
        # lift context is covered by the four explicit natural cases above.
        suite.seed=int(args.seed,0);suite.specials()
    finally:M.enter=original
    unique={row['name']:row for row in suite.rows};suite.rows=list(unique.values())
    observed=set(unique)
    suite.missing=[name for name in suite.missing if not any(
        name.startswith(label+' natural lift target') and 'lift-carry-throw-'+label in observed for label in ('pot','boulder','bush','rock'))]
    suite.save();rows.append({'group':'special','report':'special/suite.json','captures':len(suite.rows),'missing':suite.missing})
    (out/'index.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),'groups':rows},indent=2)+'\n')
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out')
    ap.add_argument('--rom',default=P.ROM);ap.add_argument('--map',default=P.MAP)
    ap.add_argument('--assets-header',default=str(Path(P.ROOT)/'build/gen/assets.h'))
    ap.add_argument('--seed',default='0xB4A7')
    ap.add_argument('--groups',default='scenes,interface,actors,actions,interactive,ending,death')
    ap.add_argument('--action-groups',default='drain,forest,blight,cave,special')
    ap.add_argument('--resume',action='store_true',help='retain prior exact-ROM screen captures while adding selected groups')
    args=ap.parse_args();base=Path(args.out);base.mkdir(parents=True,exist_ok=True);groups=args.groups.split(',')
    review=Review(SimpleNamespace(**{**vars(args),'out':str(base/'screens')}))
    for group,method in (('scenes',review.scenes),('interface',review.interfaces),('actors',review.actors),('ending',review.ending),('death',review.death_return)):
        if group in groups:method()
    action_rows=actions(args,base/'actions') if 'actions' in groups else []
    if 'interactive' in groups:
        native=IR.Review(SimpleNamespace(rom=args.rom,map=args.map,assets_header=args.assets_header,
            out=str(base/'interactive'),match=None,only=None))
        for row in IR.plan():native.record(row)
        if native.missing:review.failures.extend(row['name'] for row in native.missing)
    review.save()
    result={'rom_sha256':hashlib.sha256(Path(args.rom).read_bytes()).hexdigest(),'method':__doc__.strip(),
            'groups':groups,'screens':len(review.rows),'screen_report':'screens/review.json',
            'actions':action_rows,'failures':review.failures}
    for row in action_rows:result['failures'].extend(row['missing'])
    (base/'index.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',len(review.rows),'real-run screen clips;',sum(r['captures'] for r in action_rows),'action clips; failures:',result['failures'],flush=True)
    return int(bool(result['failures']))


if __name__=='__main__':raise SystemExit(main())
