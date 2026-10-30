"""Capture the final Drain and five UI studies from actual mGBA framebuffers.

The ROM generates its terrain and rooms normally. Seed, inventory, safe player
position and navigation transitions are disclosed fixtures. No image, UI canvas,
pose or animation phase is assigned by this tool. Menus, dialogue, purchases,
chests and death/return are driven through the game's real controls/events.
Native PNGs are unchanged240x160 output. GIF/MP4 are review conveniences.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont
import probe as P
import critical_path as C
import lift_probe as L
import bloom_probe as B
import bloom_review as BR
import art_reboot_review as AR
from bloom_suite_gallery import write_gif
from sewer_concept_review import gif_durations, position, safe

FPS = 16777216 / 280896
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
VIEWS = (
    ('drain-market', (72,115), 0, 192),
    ('drain-ladder', (152,80), 0, 128),
    ('drain-cistern', (240,118), 0, 192),
    ('drain-wizard', (344,118), 0, 192),
    ('drain-left-outlet', (88,140), 3, 192),
    ('drain-bridge', (240,174), 0, 128),
    ('drain-storage', (424,118), 0, 96),
    ('drain-left-wall', (40,224), 3, 96),
    ('drain-right-wall', (440,224), 1, 96),
    ('drain-lower-bank', (240,254), 2, 96),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hud_alpha(c):
    """Actual nonzero BG0/HUD OBJ pixels; transparent pixels are not counted."""
    points=set(); cb=0x06008000; sb=0x0600B800
    for ty in range(20):
        for tx in range(30):
            entry=P.r16(c,sb+(ty*32+tx)*2)&65535; tile=entry&1023
            if not tile:continue
            for y in range(8):
                for x in range(8):
                    xx=7-x if entry&0x400 else x; yy=7-y if entry&0x800 else y
                    value=P.r8(c,cb+tile*32+yy*4+xx//2)
                    if value>>((xx&1)*4)&15:points.add((tx*8+x,ty*8+y))
    for o in B.oam(c):
        if o['priority']:continue
        # HUD icon source allocation; other priority-zero objects (portraits,
        # rewards) do not belong to ordinary-play HUD coverage.
        if not (876<=o['tile']<936 or 1008<=o['tile']<1024):continue
        sizes=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
        if o['shape']>=3:continue
        width,height=sizes[o['shape']][o['size']]
        for y in range(height):
            for x in range(width):
                wx,wy=o['x']+x,o['y']+y
                if not (0<=wx<240 and 0<=wy<160):continue
                xx=width-1-x if o.get('flip',False) else x
                tile=o['tile']+(y//8)*(width//8)+xx//8
                value=P.r8(c,0x06010000+tile*32+(y%8)*4+(xx%8)//2)
                if value>>((xx&1)*4)&15:points.add((wx,wy))
    # Base HUD and conditional ammunition fit the same12px top region;
    # the16px maze is isolated in the lower-right corner.
    allowed=lambda x,y:y<12 or (222<=x<238 and 142<=y<158)
    return {'pixels':len(points),'min_y':min((y for x,y in points),default=None),
            'max_y':max((y for x,y in points),default=None),
            'below_12':sum(y>=12 for x,y in points),
            'outside_allowed_regions':sum(not allowed(x,y) for x,y in points),
            'minimap_pixels':sum(222<=x<238 and 142<=y<158 for x,y in points),
            'central_top_pixels':sum(116<=x<148 and y<12 for x,y in points),
            'top_12_coverage':len({(x,y) for x,y in points if y<12})/(240*12)}


def hud_payload(c):
    return digest(B.bytes_at(c,0x06008000,12288)+B.bytes_at(c,0x0600B800,2048)+
                  B.bytes_at(c,0x06010000+876*32,60*32))


class Review:
    def __init__(self,args):
        self.args=args; self.frozen=Path(args.frozen); self.out=Path(args.out)
        self.out.mkdir(parents=True,exist_ok=True)
        P.ROM=str(self.frozen/'bartgame.gba')
        self.defs=B.configure(SimpleNamespace(map=str(self.frozen/'bartgame.map'),
                                             assets_header=str(self.frozen/'assets.h')))
        C.mt=lambda name:self.defs['MT_'+name]
        self.ui=self.defs.get('BART_UI_VARIANT',self.defs.get('BART_UI_PROFILE',-1))
        self.sha=digest((self.frozen/'bartgame.gba').read_bytes())
        self.rows=[];self.checks=[];self.c=None
        self.check('final Drain profile selected',self.defs.get('BART_SEWER_VARIANT')==9)
        self.check('valid UI profile',0<=self.ui<=5,self.ui)

    def check(self,name,condition,detail=None):
        row={'name':name,'passed':bool(condition)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not condition:print('FAIL',name,detail,flush=True)

    def boot(self,title=False,seed=0xB4A7):
        self.c=P.boot(rom=P.ROM,seed=seed,start=not title)
        if not title:C.dismiss(self.c)
        return self.c

    def inventory(self,maximal=True):
        c=self.c;pl=P.sym('gPl')
        for off,val in [(0,52 if maximal else 4),(2,80 if maximal else 24),(4,999 if maximal else 0)]:P.w16(c,pl+off,val)
        for off,val in [(6,255),(7,30),(8,127),(35,50),(36,31)]:P.w8(c,pl+off,val)
        for i,eq in enumerate((2,1,6) if maximal else (0,0,0)):P.w8(c,pl+9+i,eq)
        P.run(c,4)

    def focus(self,point,facing=0):
        assert safe(self.c,*point),('unsafe standing fixture',point)
        position(self.c,point,facing)

    def forest(self,stage):
        self.boot();world=C.world(self.c);P.enter_forest(self.c);C.dismiss(self.c)
        candidates=sorted(range(25),key=lambda i:abs(world['cells'][i]['stage']-stage))
        for cell in candidates:
            desc=world['cells'][cell]
            L.warp(self.c,cell,next(i for i,g in enumerate(desc['gate']) if g))
            C.dismiss(self.c);C.clear_enemies(self.c)
            point=BR.natural_spot(self.c,0,0)
            if point:
                self.focus(point)
                return world,cell
        raise AssertionError('no safe natural room for HUD stage '+str(stage))

    def cave(self):
        for seed in (11,0xB4A7,6,7):
            self.boot(seed=seed);world=C.world(self.c);P.enter_forest(self.c)
            for cell in range(25):
                packed=AR.actual_mystery(self.c,cell)
                if not packed or packed>>6:continue
                if AR.enter_natural(self.c,world,cell):
                    C.dismiss(self.c);C.clear_enemies(self.c)
                    point=BR.natural_spot(self.c,0,0)
                    if point:self.focus(point);return
        raise AssertionError('no entered natural cave for HUD contrast')

    def state(self):
        c=self.c;pl=P.sym('gPl');actor=P.sym('gActors')
        try:shop=P.r8(c,B.static_symbol('sShopActive'))
        except KeyError:shop=0
        return {'frame':P.r32(c,P.sym('gFrame')),'updates':P.r32(c,P.sym('gGame')+8),
                'game_state':C.gstate(c),'area':C.area(c),'cell':C.cell(c),
                'hero_state':P.r8(c,actor+2),'position':list(P.player_pos(c)),
                'camera':[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],
                'hp':P.r16(c,pl),'hp_max':P.r16(c,pl+2),'gilt':P.r16(c,pl+4)&65535,
                'equip':[P.r8(c,pl+9+i) for i in range(3)],
                'textbox':P.r8(c,P.sym('gTbActive')),'shop':shop,
                'oam':P.r8(c,P.sym('gOamCount'))}

    def record(self,name,total=48,events=None,note='',expect=None,hud=False,motion=False):
        c=self.c;events=events or {}; images=[];trace=[]
        directory=self.out/name;directory.mkdir(exist_ok=True)
        raw=self.out/'all-frames'/name;raw.mkdir(parents=True,exist_ok=True)
        start_frame=P.r32(c,P.sym('gFrame'));start_update=P.r32(c,P.sym('gGame')+8)
        alpha=hud_alpha(c) if hud else None
        for tick in range(total):
            c.clear_keys(*range(10))
            keys=events.get(tick,[])
            if keys:c.set_keys(*(P.key(c,k) for k in keys))
            c.run_frame();im=c.bg_video.to_pil().convert('RGB').copy()
            im.save(raw/f'frame-{tick:03}.png');images.append(im);trace.append(self.state())
        c.clear_keys(*range(10))
        selected=sorted({0,total//4,total//2,total*3//4,total-1})
        for tick in selected:images[tick].save(directory/f'frame-{tick:03}.png')
        pick=total//2
        if name=='reward-chest':pick=total-1
        if name=='death-return':
            first=next((i for i,r in enumerate(trace) if r['textbox'] and r['area']==0),total-1)
            pick=min(total-1,first+48)
        images[pick].save(self.out/(name+'.png'))
        metadata=None;video=None
        if motion:
            metadata=write_gif([im.resize((480,320),Image.Resampling.NEAREST) for im in images[::2]],
                               gif_durations(total),self.out/(name+'.gif'))
            if not self.args.no_video:
                video=name+'.mp4'
                subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(raw/'frame-%03d.png'),
                    '-vf','scale=720:480:flags=neighbor','-an','-c:v','libx264','-threads','1','-crf','17',
                    '-pix_fmt','yuv420p','-movflags','+faststart',str(self.out/video)],check=True)
        film=Image.new('RGB',(960,4*178+22),'#101820');draw=ImageDraw.Draw(film)
        draw.fontmode='1';draw.text((6,4),name+' / actual mGBA chronology',font=FONT,fill='#f0d898')
        for i in range(16):
            tick=round(i*(total-1)/15);x=(i%4)*240;y=22+(i//4)*178
            film.paste(images[tick],(x,y));draw.text((x+4,y+162),f'video {tick}',font=FONT,fill='#e0dcc0')
        film.save(self.out/(name+'-filmstrip.png'))
        passed=True if expect is None else bool(expect(trace))
        self.check(name+' expected game presentation',passed)
        self.check(name+' OAM budget',max(r['oam'] for r in trace)<=128)
        if hud:
            self.check(name+' HUD alpha stays in compact authorized regions',alpha['pixels']>0 and alpha['outside_allowed_regions']==0,alpha)
            self.check(name+' center remains transparent',alpha['central_top_pixels']==0,alpha)
            self.check(name+' ordinary idle keeps pace with VBlank',
                       trace[-1]['updates']-start_update==total and trace[-1]['frame']-start_frame==total,
                       {'updates':trace[-1]['updates']-start_update,'vblanks':trace[-1]['frame']-start_frame,'recorded':total})
        row={'name':name,'image':name+'.png','filmstrip':name+'-filmstrip.png',
             'native_frames':[f'{name}/frame-{i:03}.png' for i in selected],
             'video':video,'gif':name+'.gif' if motion else None,'gif_metadata':metadata,
             'frames':total,'fps':FPS,'note':note,'events':events,'hud_alpha':alpha,
             'expected':passed,'trace':trace,'all_frames':str(Path('all-frames')/name)}
        if hud:row['minimap_vram_sha256']=digest(B.bytes_at(c,0x06010000+1008*32,16*32))
        self.rows.append(row);self.save();print('CAPTURE',name,'PASS' if passed else 'FAIL',flush=True)

    def sewer(self):
        for name,point,facing,frames in VIEWS:
            self.boot();self.focus(point,facing)
            self.record(name,frames,note='Final native Drain; only safe position/facing fixtures, ordinary idle.',
                        expect=lambda t:all(r['area']==0 and r['game_state']==1 for r in t),hud=True,motion=True)
        # Walk on the existing hall route; no terrain or camera assignment.
        self.boot();self.focus((152,118),1)
        self.record('drain-walk',128,{i:['RIGHT'] for i in range(8,92)},
                    'Ordinary walk with settled start fixture; shows rail, floor and HUD together.',
                    expect=lambda t:any(r['position']!=t[0]['position'] for r in t),motion=True)

    def hud(self):
        self.boot();self.focus((152,80));self.inventory(True)
        self.record('hud-sewer-max',64,note='Inventory fixture:10 hearts,6.5filled,gilt999,three assigned items.',hud=True,motion=True)
        before=hud_payload(self.c);pl=P.sym('gPl')
        P.w8(self.c,pl+6,0)
        P.run(self.c,4)
        self.check('hidden keys do not alter HUD payload',hud_payload(self.c)==before)
        ammo_payloads=[]
        for value in (0,9,99,255):
            P.w8(self.c,pl+7,value);P.w8(self.c,pl+35,value);P.run(self.c,4)
            ammo_payloads.append(hud_payload(self.c))
            self.record('hud-ammo-'+str(value),32,note=f'Equipped seeds/bow with both ammunition counts{value}; explicit resource fixture.',hud=True)
        self.check('four equipped ammunition values produce distinct actual HUD pixels',len(set(ammo_payloads))==4,ammo_payloads)
        for i,eq in enumerate((3,4,5)):P.w8(self.c,pl+9+i,eq)
        P.run(self.c,4);before=hud_payload(self.c)
        P.w8(self.c,pl+7,1);P.w8(self.c,pl+35,1);P.run(self.c,4)
        self.check('unequipped ammunition does not alter HUD payload',hud_payload(self.c)==before)
        self.record('hud-non-ammo-equipment',32,note='Lamp/cape/shield equipped; ammunition exists but is hidden.',hud=True)
        self.inventory(False)
        self.record('hud-empty-low',48,note='Half-heart,empty equipment,gilt0 fixture.',hud=True)
        maps=[]
        for stage,label in ((0,'healthy'),(3,'blighted')):
            world,cell=self.forest(stage);self.inventory(True)
            self.record('hud-'+label,64,note=f'Natural forest stage{world["cells"][cell]["stage"]},cell{cell}; full HUD inventory fixture.',hud=True,motion=True)
            self.check('hud-'+label+' actual minimap is visible',self.rows[-1]['hud_alpha']['minimap_pixels']>0)
            maps.append({'cell':cell,'vram':self.rows[-1]['minimap_vram_sha256']})
        self.check('minimap reflects distinct naturally generated current rooms',
                   maps[0]['cell']!=maps[1]['cell'] and maps[0]['vram']!=maps[1]['vram'],maps)
        self.cave();self.inventory(True)
        self.record('hud-cave',64,note='Entered a naturally generated cave through its real entrance; inventory fixture.',hud=True,motion=True)

    def interfaces(self):
        self.boot();self.focus((344,118));P.hold(self.c,'UP',1)
        self.record('dialogue-wizard',160,{8:['A'],9:['A']},'Ordinary A talk, including natural type-on animation.',
                    expect=lambda t:any(r['textbox'] for r in t),motion=True)
        P.press(self.c,'A',2,2)
        self.record('dialogue-wizard-page2',96,note='Ordinary A advances a real paginated wizard message.',
                    expect=lambda t:any(r['textbox'] for r in t),motion=True)
        C.dismiss(self.c);self.focus((72,112));P.w16(self.c,P.sym('gPl')+4,123)
        P.w8(self.c,P.sym('gPl')+36,1);P.hold(self.c,'UP',1)
        self.record('shop',80,{8:['A'],9:['A']},'Ordinary A opens market; gilt123 and bow ownership expose all three actual wares.',
                    expect=lambda t:any(r['shop'] for r in t),motion=True)
        P.press(self.c,'DOWN',2,6)
        self.record('shop-selected',32,note='Ordinary Down selects second ware.',expect=lambda t:all(r['shop'] for r in t))
        P.press(self.c,'UP',2,6)
        self.record('shop-purchase-response',128,{8:['A'],9:['A']},'Ordinary A buys first ware; actual merchant response.',
                    expect=lambda t:any(r['textbox'] for r in t),motion=True)
        C.dismiss(self.c)
        self.focus((72,112));P.w16(self.c,P.sym('gPl')+4,0);P.hold(self.c,'UP',1);P.press(self.c,'A',2,32)
        self.record('shop-unaffordable',32,note='Actual zero-gilt shop cost states; no pixel or screen fixture.',expect=lambda t:all(r['shop'] for r in t))
        P.press(self.c,'B',2,16);C.dismiss(self.c)
        self.forest(0);self.inventory(True);P.press(self.c,'START',2,12)
        self.record('menu-items',32,note='Start opens actual inventory.',expect=lambda t:all(r['game_state']==4 for r in t))
        old=P.r8(self.c,P.sym('gPl')+9);P.press(self.c,'RIGHT',2,4);P.press(self.c,'A',2,8)
        self.record('menu-equipped',32,note='Right/A assigns a menu item using real controls.',expect=lambda t:all(r['game_state']==4 for r in t))
        P.press(self.c,'R',2,12)
        self.record('menu-key-items',32,note='R turns to actual key-item page.',expect=lambda t:all(r['game_state']==4 for r in t))
        P.press(self.c,'R',2,40)
        self.record('menu-map',32,note='R opens actual generated map with Map/Astrolabe inventory fixture.',expect=lambda t:all(r['game_state']==4 for r in t))
        P.press(self.c,'A',2,20)
        self.record('menu-map-zoom',32,note='A opens actual chamber map.',expect=lambda t:all(r['game_state']==4 for r in t))
        P.press(self.c,'B',2,10);P.press(self.c,'START',2,12)
        self.record('hud-after-equip',48,note='Menu closed normally after equipment assignment.',hud=True,
                    expect=lambda t:all(r['game_state']==1 for r in t))

    def events(self):
        self.boot(title=True);P.run(self.c,60)
        self.record('title-start',96,note='Real title and Press Start; original title painting preserved.',expect=lambda t:all(r['game_state']==0 for r in t),motion=True)
        self.boot();world=C.world(self.c);P.enter_forest(self.c);C.dismiss(self.c)
        bow=next(i for i,d in enumerate(world['cells']) if d['role']==4 and d['arg']==6)
        L.warp(self.c,bow,next(i for i,g in enumerate(world['cells'][bow]['gate']) if g));C.clear_enemies(self.c)
        found=L.find_tile(self.c,'CHEST');assert found,'natural bow chest'
        _,_,tile,key=found;self.focus((tile[0]*16+8,tile[1]*16+14),('UP','RIGHT','DOWN','LEFT').index(key))
        self.record('reward-chest',144,{i:[key] for i in range(8,32)},
                    'Real movement opens the naturally placed Thorn Bow chest; reward and item-get rendered by the game.',
                    expect=lambda t:any(r['hero_state']==6 for r in t),motion=True)
        C.dismiss(self.c)
        self.boot();world=C.world(self.c);P.enter_forest(self.c);C.dismiss(self.c)
        enemy=None
        for cell,desc in enumerate(world['cells']):
            L.warp(self.c,cell,next(i for i,g in enumerate(desc['gate']) if g))
            enemy=next((P.actor(self.c,i) for i in range(1,96) if P.actor(self.c,i)['kind']==2 and P.actor(self.c,i)['type']==0),None)
            if enemy:break
        assert enemy,'natural contact enemy'
        C.teleport(self.c,enemy['x'],enemy['y']+5);P.w16(self.c,P.sym('gPl'),2);P.w8(self.c,P.sym('gActors')+28,0)
        self.record('death-return',360,note='Natural enemy contact; injuredHP and position fixtures. Actual death/save/Drain-return/Bloom dialogue.',
                    expect=lambda t:any(r['hero_state']==7 for r in t) and t[-1]['area']==0,motion=True)
        self.c.reset();P.run(self.c,80)
        self.record('title-continue',96,note='Reset after actual death-created save; real Continue/New Game choices.',
                    expect=lambda t:all(r['game_state']==0 for r in t),motion=True)
        P.press(self.c,'DOWN',2,8)
        self.record('title-new-game-selected',32,note='Ordinary Down changes real title selection.',expect=lambda t:all(r['game_state']==0 for r in t))
        # The final panel is reached through the real Heart fight and Grail
        # collection. Navigation/healing/inventory are disclosed fixtures;
        # neither the boss HP nor game completion state is assigned.
        self.boot();world=C.world(self.c);P.enter_forest(self.c);C.dismiss(self.c)
        goal=world['goal'];desc=world['cells'][goal]
        L.warp(self.c,goal,next(i for i,g in enumerate(desc['gate']) if g));C.dismiss(self.c)
        pl=P.sym('gPl');P.w8(self.c,pl+8,127)
        for i,eq in enumerate((0,1,5)):P.w8(self.c,pl+9+i,eq)
        C.S=str(self.out/'ending-steps');Path(C.S).mkdir(exist_ok=True)
        C.boss_fight(self.c)
        self.record('victory',64,note='Actual Heart sword fight and Grail collection; navigation, healing and inventory are fixtures.',
                    expect=lambda t:all(r['game_state']==6 for r in t),motion=True)

    def save(self):
        report={'method':__doc__.strip(),'rom_sha256':self.sha,'ui_variant':self.ui,
                'emulator':'mGBA 0.10.5','native_screen':[240,160],'seed':'0xb4a7 (cave may use documented alternate)',
                'captures':self.rows,'capture_count':len(self.rows),'checks':self.checks,
                'passed':sum(r['passed'] for r in self.checks),'total':len(self.checks),
                'failures':[r for r in self.checks if not r['passed']],
                'limits':'Natural room navigation uses transition fixtures; no UI canvas/image/pose assignment. Authored complete art coverage and gameplay visual captures are separate evidence. No generic yes/no screen exists; actual shop/title choices are captured.'}
        (self.out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')

    def run(self):
        for group in self.args.groups.split(','):
            getattr(self,group)()
        self.save();print('RESULT',sum(r['passed'] for r in self.checks),'/',len(self.checks),'captures',len(self.rows),flush=True)
        return int(any(not r['passed'] for r in self.checks))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--groups',default='sewer,hud,interfaces,events')
    parser.add_argument('--no-video',action='store_true')
    return Review(parser.parse_args()).run()


if __name__=='__main__':raise SystemExit(main())
