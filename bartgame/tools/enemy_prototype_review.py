#!/usr/bin/env python3
"""Record optional enemy prototypes through actual mGBA inputs and ordinary AI.

The lab's own request API selects a case and clears unrelated actors. Navigation,
safe actor positions, player facing, inventory and player healing are disclosed
fixtures. This tool never assigns enemy HP, facing, flags, state, timer, pose or
animation clocks, and never writes room geometry, palettes, VRAM or framebuffers.
Native PNGs are untouched emulator output. Filmstrip labels are outside them.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageSequence
import probe as P
import bloom_probe as B
import critical_path as C
import lift_probe as L
from sewer_concept_audit import NativeRom
from sewer_concept_review import safe, gif_durations
from bloom_suite_gallery import write_gif

ROOT = Path(__file__).resolve().parent.parent
SHA = lambda data: hashlib.sha256(data).hexdigest()
NAMES = ('gilt-leech', 'root-maw', 'reliquary-snout', 'mixed')
KEYS = ('UP', 'RIGHT', 'DOWN', 'LEFT')
DXY = ((0, -1), (1, 0), (0, 1), (-1, 0))


def signed(value, bits):
    return value - (1 << bits) if value >= 1 << (bits - 1) else value


def symbols(bundle):
    result = subprocess.check_output(['arm-none-eabi-nm', '-n', str(bundle/'bartgame.elf')], text=True)
    return {name: int(address, 16) for address, name in
            re.findall(r'^([\da-fA-F]{8})\s+\w\s+(\S+)\s*$', result, re.M)}


class Review:
    def __init__(self, args):
        self.args = args
        self.bundle, self.out = Path(args.bundle).resolve(), Path(args.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.native = NativeRom(self.bundle)
        self.symbols = symbols(self.bundle)
        self.defs = B.configure(SimpleNamespace(map=str(self.bundle/'bartgame.map'),
                                              assets_header=str(self.bundle/'assets.h')))
        C.mt = lambda name: self.defs['MT_'+name]
        assert self.defs.get('BART_ENEMY_LAB') == 1, 'requires the explicitly optional lab ROM'
        self.c, self.rows, self.checks, self.media = None, [], [], []
        self.trace, self.images, self.events, self.label = [], [], [], None
        self.fixtures = []

    def check(self, name, passed, detail=None):
        row = dict(name=name, passed=bool(passed))
        if detail is not None:
            row['detail'] = detail
        self.checks.append(row)
        print(('PASS ' if passed else 'FAIL ')+name, flush=True)
        return bool(passed)

    def actor(self, index):
        c, at = self.c, P.sym('gActors')+index*64
        return dict(index=index, kind=P.r8(c, at), type=P.r8(c, at+1),
                    state=P.r8(c, at+2), timer=P.r8(c, at+4), timer2=P.r8(c, at+5),
                    direction=P.r8(c, at+6), facing=P.r8(c, at+7),
                    x_q16=signed(P.r32(c, at+8), 32), y_q16=signed(P.r32(c, at+12), 32),
                    x=signed(P.r32(c, at+8), 32)/65536,
                    y=signed(P.r32(c, at+12), 32)/65536,
                    hp=signed(P.r16(c, at+26)&65535, 16), iframes=P.r8(c, at+28),
                    knockback=P.r8(c, at+29), flags=P.r8(c, at+31), collision=P.r8(c, at+35),
                    sheet=P.r8(c, at+36), frame=P.r8(c, at+37),
                    tile=P.r16(c, at+44)&65535, palette=P.r8(c, at+46),
                    damage=P.r8(c, at+47), v=list(B.bytes_at(c, at+48, 6)))

    def enemies(self):
        return [self.actor(i) for i in range(1, 96)
                if P.r8(self.c, P.sym('gActors')+i*64) == 2]

    def target(self, kind):
        return next((a for a in self.enemies() if a['type'] == kind), None)

    def state(self):
        c = self.c
        return dict(frame=P.r32(c, P.sym('gFrame')),
                    updates=P.r32(c, P.sym('gGame')+8), game_state=C.gstate(c),
                    area=C.area(c), cell=C.cell(c), case=P.r8(c, P.sym('gEnemyPrototypeCase')),
                    hero=self.actor(0), player_hp=P.r16(c, P.sym('gPl')),
                    sword_active=P.r8(c, P.sym('gPl')+21),
                    arrows=P.r8(c, P.sym('gPl')+35), bombs=P.r8(c, P.sym('gPl')+7),
                    enemies=self.enemies(),
                    projectiles=[self.actor(i) for i in range(1, 96)
                                 if P.r8(c, P.sym('gActors')+i*64) == 3],
                    effects=sum(P.r8(c, P.sym('gActors')+i*64) == 7 for i in range(1, 96)),
                    next_tile=P.r16(c, self.symbols['sNextTile'])&65535,
                    prototype_events=[P.r16(c,P.sym('gEnemyPrototypeEvents')+i*2)&65535 for i in range(7)],
                    camera=[signed(P.r16(c, P.sym('gCamX'))&65535,16),
                            signed(P.r16(c, P.sym('gCamY'))&65535,16)],
                    oam_count=P.r8(c,P.sym('gOamCount')))

    def begin(self, label):
        assert self.label is None
        self.label, self.trace, self.images, self.events = label, [], [], []
        self.start_fixtures = len(self.fixtures)

    def run(self, frames=1, keys=(), heal=True):
        self.c.clear_keys(*range(10))
        self.c.set_keys(*(P.key(self.c,k) for k in keys))
        if self.label:
            self.events.append(dict(tick=len(self.trace), frames=frames, held=list(keys)))
        for _ in range(frames):
            if heal:
                P.w16(self.c, P.sym('gPl'), 80)
            self.c.run_frame()
            if self.label:
                tick=len(self.trace)
                self.trace.append(self.state())
                if tick % self.args.sample == 0:
                    self.images.append((tick,self.c.bg_video.to_pil().convert('RGB').copy()))
        self.c.clear_keys(*range(10))

    def finish(self, note):
        folder=self.out/self.label
        folder.mkdir(exist_ok=True)
        for tick,img in self.images:
            path=folder/('native-%04d.png'%tick)
            img.save(path)
            self.media.append(dict(file=str(path.relative_to(self.out)),sha256=SHA(path.read_bytes()),
                                   kind='untouched native240x160 mGBA framebuffer'))
        frames=[image for _,image in self.images]
        # Every frame has a separate palette if the combined scene exceeds256.
        gif=folder/'motion.gif'
        durations=gif_durations(len(self.trace),self.args.sample)
        meta=write_gif(frames,durations,gif)
        self.media.append(dict(file=str(gif.relative_to(self.out)),sha256=SHA(gif.read_bytes()),
                               kind='native mGBA samples; no compositing',metadata=meta))
        decoded=[]
        with Image.open(gif) as source:
            for image in ImageSequence.Iterator(source):
                decoded.append((image.convert('RGB').tobytes(),image.info.get('duration',0)))
        expected=[]
        for frame,duration in zip(frames,durations):
            raw=frame.tobytes()
            if expected and expected[-1][0]==raw:
                expected[-1]=(raw,expected[-1][1]+duration)
            else:
                expected.append((raw,duration))
        self.check(self.label+' GIF exact native pixels and timing',decoded==expected,
                   dict(meta,decoded_frames=len(decoded)))
        sheet=Image.new('RGB',(720,3*182),(13,15,23))
        draw=ImageDraw.Draw(sheet)
        for i in range(9):
            tick,img=self.images[round(i*(len(self.images)-1)/8)]
            x,y=(i%3)*240,(i//3)*182
            sheet.paste(img,(x,y))
            draw.text((x+4,y+163),self.label+' @'+str(tick),fill=(240,225,176))
        sheet.save(folder/'filmstrip.png')
        row=dict(name=self.label,note=note,frames=len(self.trace),inputs=self.events,
                 fixtures=self.fixtures[self.start_fixtures:],trace=self.trace,
                 gif=str(gif.relative_to(self.out)),native_frames=len(frames))
        self.rows.append(row)
        self.label=None
        self.save()
        return row

    def position(self,index,point,facing=None):
        x,y=map(int,point)
        assert safe(self.c,x,y),('unsafe position fixture',index,point)
        at=P.sym('gActors')+index*64
        # Coordinates only. Enemy state/facing/HP/timers remain untouched.
        for off,value in ((8,x),(12,y)):
            P.w16(self.c,at+off,0)
            P.w16(self.c,at+off+2,value)
        if index==0:
            pl=P.sym('gPl')
            P.w16(self.c,pl+14,x);P.w16(self.c,pl+16,y)
            if facing is not None:
                P.w8(self.c,at+7,facing);P.w8(self.c,at+6,facing*8)
        self.fixtures.append(dict(tick=len(self.trace) if self.label else None,
                                  action='safe position',actor=index,point=[x,y],player_facing=facing))

    def enter(self,case=0,background='healthy'):
        self.c=P.boot(rom=str(self.bundle/'bartgame.gba'),seed=0xB4A7)
        C.dismiss(self.c,1000)
        self.settle_case(0)
        world=C.world(self.c)
        if background=='sewer':
            for name,value in (('sNextArea',0),('sNextCell',0),('sNextSide',0),('sTransPhase',0)):
                P.w8(self.c,self.symbols[name],value)
            P.w8(self.c,P.sym('gGame'),2)
            P.run(self.c,90)
        elif background=='deep':
            cell=max(range(25),key=lambda i:world['cells'][i]['stage'])
            L.warp(self.c,cell,next(i for i,g in enumerate(world['cells'][cell]['gate']) if g))
        P.w8(self.c,P.sym('gEnemyPrototypeRequest'),case+1)
        self.settle_case(case)
        C.dismiss(self.c,1000)
        self.check('lab case%d selected in real %s'%(case+1,background),
                   P.r8(self.c,P.sym('gEnemyPrototypeCase'))==case and C.gstate(self.c)==1,
                   dict(area=C.area(self.c),cell=C.cell(self.c)))
        self.fixtures.append(dict(action='lab request/navigation',case=case,background=background,
                                  seed='0xb4a7',area=C.area(self.c),cell=C.cell(self.c)))

    def settle_case(self,case):
        """Fixture setup scans may span video frames; record only finished AI."""
        first=None
        expected=3 if case==3 else 1
        for tick in range(2400):
            ready=(P.r8(self.c,P.sym('gEnemyPrototypeCase'))==case and
                   P.r8(self.c,P.sym('gEnemyPrototypeRequest'))==0 and
                   P.r8(self.c,P.sym('gEnemyPrototypeSpawned'))==expected and
                   len(self.enemies())==expected and C.gstate(self.c)==1)
            updates=P.r32(self.c,P.sym('gGame')+8)
            if ready:
                if first is None:first=updates
                if updates-first>=3:return
            else:first=None
            self.run()
        raise AssertionError(('lab case did not finish setup',case,self.state()))

    def lane(self,minimum=112):
        """Longest real dry-floor horizontal run; no replacement terrain."""
        room=P.sym('gRoom')
        w,h=P.r8(self.c,room)*16,P.r8(self.c,room+1)*16
        best=[]
        for y in range(48,h-24,8):
            run=[]
            for x in range(32,w-24,4):
                if safe(self.c,x,y):run.append((x,y))
                else:
                    if len(run)>len(best):best=run
                    run=[]
            if len(run)>len(best):best=run
        assert best and best[-1][0]-best[0][0]>=minimum,('no actual dry-floor lane',best)
        return best[0],best[-1]

    def near(self,enemy,front=True,distance=22):
        f=enemy['facing'];dx,dy=DXY[f]
        if not front:dx,dy=-dx,-dy
        point=(round(enemy['x'])+dx*distance,round(enemy['y'])+dy*distance)
        if not safe(self.c,*point):return False
        self.position(0,point,(f+2)%4 if front else f)
        return True

    def wait(self,predicate,limit=600):
        for _ in range(limit):
            if predicate():return True
            self.run()
        return False

    def idle(self,case,background='healthy',frames=320):
        self.enter(case,background)
        self.begin(NAMES[case]+'-'+background)
        self.run(frames)
        row=self.finish('Live optional prototype AI on unchanged real room terrain. Player HP replenishment is a survival fixture; no enemy behavior/HP writes.')
        deltas=Counter(b['updates']-a['updates'] for a,b in zip(row['trace'],row['trace'][1:]))
        self.check(row['name']+' uninterrupted native logic cadence',deltas=={1:frames-1},dict(deltas))
        self.check(row['name']+' world allocation remains below reserved HUD',
                   all(0<r['next_tile']<=876 for r in row['trace']),
                   max(r['next_tile'] for r in row['trace']))
        for name in ('proto_rope','proto_leever','proto_helmasaur'):
            sid=self.native.sheet_ids[name]
            meta,payload=self.native.sheet(name)
            actors=[a for r in row['trace'] for a in r['enemies'] if a['sheet']==sid]
            if actors:
                self.check(row['name']+' '+name+' genuine allocated tiles/palette',
                           all(a['tile']>0 and a['tile']+meta['tile_count']<=876 and
                               a['palette']==meta['pal'] for a in actors),
                           dict(tile=actors[0]['tile'],metadata=meta))
                live=next((a for a in self.enemies() if a['sheet']==sid),None)
                if live:
                    actual=B.bytes_at(self.c,0x06010000+live['tile']*32,len(payload))
                    self.check(row['name']+' '+name+' VRAM matches actual ROM sheet',actual==payload,
                               dict(rom_sha256=SHA(payload),vram_sha256=SHA(actual)))
        return row

    def rope(self):
        self.enter(0)
        enemy=self.target(6)
        left,right=self.lane()
        # A real wall-edge run makes the ordinary charge stop observable.
        x,y=right
        # Let the ordinary camera reach this part of the room before the
        # encounter starts. Otherwise a cross-room fixture hides the charge.
        self.position(0,(x-8,y),3)
        self.run(96)
        self.check('Rope completes pre-existing state before line fixture',
                   self.wait(lambda:self.target(6)['state']==0 and not self.target(6)['knockback'],180))
        self.begin('gilt-leech-charge-and-wall')
        self.position(enemy['index'],(x-40,y))
        self.position(0,(x-8,y),3)
        encounter_start=len(self.trace)
        self.check('Rope acquires cardinal line',self.wait(lambda:self.target(6)['state']==1,80))
        tell=self.target(6)
        self.check('Rope begins full30-update tell',tell['timer']==30,tell)
        self.check('Rope ordinary tell reaches charge',self.wait(lambda:self.target(6)['state']==2,40))
        attack=self.target(6)
        locked=attack['direction']
        side=next(((round(attack['x']),y+dy) for dy in (32,-32,24,-24)
                   if safe(self.c,round(attack['x']),y+dy)),None)
        self.check('Rope has real perpendicular dodge footing',side is not None,side)
        if side:self.position(0,side,0)
        self.check('Rope charge ends in ordinary recovery',self.wait(lambda:self.target(6)['state']==3,44))
        recover=self.target(6)
        self.run(16)
        row=self.finish('Native30-update tell, fixed-heading1.625px/update charge and wall stop. Initial enemy/player coordinates and the perpendicular player dodge are fixtures on unchanged dry floor. Enemy HP/state/facing/timer are never assigned.')
        attacks=[a for r in row['trace'][encounter_start:] for a in r['enemies'] if a['type']==6 and a['state']==2]
        self.check('Rope charge direction remains locked after player dodge',bool(attacks) and all(a['direction']==locked for a in attacks),locked)
        self.check('Rope collision stops charge before36-frame timeout',recover['timer']==36 and len(attacks)<36,
                   dict(attack_frames=len(attacks),recovery=recover))
        self.check('Rope actual charge speed is1.625',any((b['x']-a['x'])**2+(b['y']-a['y'])**2==1.625**2
                   for a,b in zip(attacks,attacks[1:])))

    def maw(self):
        self.enter(1)
        self.begin('root-maw-buried-and-sword')
        enemy=self.target(7)
        self.check('Maw starts buried and unhittable',enemy['state']==4 and not enemy['flags']&10,enemy)
        self.check('Buried Maw has ordinary sword approach',self.near(enemy,True))
        hp=enemy['hp']
        self.run(2,('B',));self.run(22)
        self.check('Actual sword leaves buried Maw HP unchanged',self.target(7)['hp']==hp,
                   dict(before=hp,after=self.target(7)['hp']))
        self.check('Maw reaches emergence through ordinary countdown',self.wait(lambda:self.target(7)['state']==5,400))
        emerge=self.target(7);hero=self.actor(0)
        self.check('Maw telegraph is24updates and safe40px away',emerge['timer']==24 and
                   (emerge['x']-hero['x'])**2+(emerge['y']-hero['y'])**2>=1600 and
                   safe(self.c,round(emerge['x']),round(emerge['y'])),dict(enemy=emerge,hero=hero))
        self.check('Maw surfaces through ordinary tell',self.wait(lambda:self.target(7)['state']==6,30))
        exposed=self.target(7)
        self.check('Surface enables hit/contact for180updates',exposed['timer']==180 and exposed['flags']&10==10,exposed)
        approach=self.near(exposed,True)
        self.check('Exposed Maw has actual sword approach',approach)
        if approach:
            hp=exposed['hp']
            self.run(2,('B',));self.run(26)
            self.check('Actual surface sword removes2HP',self.target(7) and self.target(7)['hp']==hp-2,
                       dict(before=hp,after=self.target(7)))
        self.wait(lambda:self.target(7)['state']==4,360)
        buried=self.target(7)
        self.check('Maw retreats and returns below for240updates',buried['state']==4 and buried['timer']==240 and not buried['flags']&10,buried)
        self.finish('Real B sword inputs before/after natural24-frame emergence, then ordinary exposed/retreat/buried loop. Player positioning/healing only; no enemyHP/state/clock writes.')

    def armor(self):
        self.enter(2)
        self.begin('reliquary-snout-front-and-rear')
        self.check('Snout reaches locked tell naturally',self.wait(lambda:self.target(8)['state']==1,100))
        enemy=self.target(8)
        # Repositioning the actor is disclosed; its locked orientation/state stays.
        left,right=self.lane()
        midpoint=((left[0]+right[0])//2,left[1])
        self.position(enemy['index'],midpoint)
        self.check('Snout has safe front approach',self.near(self.target(8),True))
        hp=self.target(8)['hp'];events=self.state()['prototype_events'][2]
        self.run(2,('B',));self.run(23)
        front=self.target(8)
        self.check('Actual front sword clang preserves HP',front and front['hp']==hp and
                   self.state()['prototype_events'][2]>events,dict(before=hp,after=front))
        # Still inside the60-frame non-steering windup, get behind naturally locked armor.
        self.check('Snout has safe rear approach',self.near(front,False))
        self.run(2,('B',));self.run(24)
        rear=self.target(8)
        self.check('Actual rear sword removes2HP',rear and rear['hp']==hp-2,dict(before=hp,after=rear))
        self.finish('Real B sword on front armor, then rear during its natural60-update locked tell. Actor/player position fixtures do not change facing, HP, timers, flags or AI state. Clang is diagnosed by the game event plus unchangedHP.')

    def arrow_point(self,enemy,front):
        facing=enemy['facing']
        direction=(facing+2)%4 if front else facing
        dx,dy=DXY[direction]
        # Account for the real bow hand origin and HB_ARROW's14px vertical offset.
        ox=(5,9,3,-9)[direction]
        oy=(-4,2,7,2)[direction]-14
        point=(round(enemy['x']-dx*32-ox),round(enemy['y']-8-dy*32-oy))
        if not safe(self.c,*point):return False
        self.position(0,point,direction)
        return True

    def arrows(self):
        self.enter(2)
        self.begin('reliquary-snout-arrow-defense')
        self.wait(lambda:self.target(8)['state']==1,100)
        enemy=self.target(8)
        left,right=self.lane();self.position(enemy['index'],((left[0]+right[0])//2,left[1]))
        P.w8(self.c,P.sym('gPl')+9,6)
        self.fixtures.append(dict(action='inventory equip',button='A',item='owned bow'))
        enemy=self.target(8);hp=enemy['hp'];events=self.state()['prototype_events'][2]
        front=self.arrow_point(enemy,True)
        self.check('Snout has safe front bow lane',front)
        if front:
            self.run(2,('A',));self.run(18)
            self.check('Actual front arrow clang preserves HP',self.target(8)['hp']==hp and
                       self.state()['prototype_events'][2]>events,self.target(8))
        rear=self.arrow_point(self.target(8),False)
        self.check('Snout has safe rear bow lane',rear)
        if rear:
            self.run(2,('A',));self.run(18)
            self.check('Actual rear arrow removes2HP',self.target(8)['hp']==hp-2,self.target(8))
        row=self.finish('Actual A bow shots from front/rear during the natural locked tell. Shot origins account for ordinary authored hand and collision offsets. No enemyHP/state/facing/timer writes.')
        self.check('Snout bow evidence contains actual2damage arrow',
                   any(a['type']==3 and a['damage']==2 for r in row['trace'] for a in r['projectiles']))

    def bomb(self,buried):
        self.enter(1)
        self.begin('root-maw-bomb-'+('buried' if buried else 'exposed'))
        if buried:
            self.wait(lambda:self.target(7)['state']==6 and self.target(7)['timer']<=96,420)
        # This is a damage-interface counterprobe: the actual bomb runs its full
        # fuse, then a coordinate-only target fixture puts the naturally timed
        # enemy in the real blast. It does not purport to show an ordinary fight.
        left,right=self.lane();point=((left[0]+right[0])//2,left[1])
        self.position(0,point,1)
        before=P.r8(self.c,P.sym('gPl')+7)
        self.run(2,('A',))
        def live_bomb():
            return next((self.actor(i) for i in range(1,96)
                         if P.r8(self.c,P.sym('gActors')+i*64)==6 and
                         P.r8(self.c,P.sym('gActors')+i*64+1)==5),None)
        bomb=live_bomb()
        self.check('Actual bomb input consumes one blightseed',bomb is not None and
                   P.r8(self.c,P.sym('gPl')+7)==before-1)
        if bomb:
            escape=next(((round(bomb['x'])+dx,round(bomb['y'])+dy)
                         for dx,dy in ((-64,0),(64,0),(0,64),(0,-64),(-48,0),(48,0))
                         if safe(self.c,round(bomb['x'])+dx,round(bomb['y'])+dy)),None)
            if escape:self.position(0,escape,0)
            self.wait(lambda:live_bomb() is None or live_bomb()['timer2']>=149,180)
            enemy=self.target(7);bomb=live_bomb()
            phase=4 if buried else 6
            self.check('Natural phase at bomb fuse149 is intended phase',enemy['state']==phase,enemy)
            if bomb:
                self.position(enemy['index'],(round(bomb['x']),round(bomb['y'])))
                hp=enemy['hp'];self.run(12)
                after=self.target(7)
                self.check('Real bomb rejects buried target' if buried else 'Real8damage bomb kills6HP exposed target',
                           after is not None and after['hp']==hp if buried else after is None,
                           dict(before=hp,after=after))
        self.finish('Damage-interface counterprobe: actual A bomb input and its full150-update fuse; target coordinates alone are placed into the blast on update149. Natural buried/exposed phase and HP are never assigned. This fixture verifies phase damage rules, not unassisted combat positioning.')

    def contact(self):
        self.enter(0)
        self.begin('gilt-leech-contact-iframes')
        enemy=self.target(6)
        hp=P.r16(self.c,P.sym('gPl'))
        # Repeated overlap is intentional isolation of the player damage gate.
        for _ in range(22):
            enemy=self.target(6)
            self.position(0,(round(enemy['x']),round(enemy['y'])),0)
            self.run(1,heal=False)
        row=self.finish('Repeated coordinate-only player overlap fixture, no healing during22updates, verifies contact damage and ordinary invulnerability. Neither actor HP nor AI clock is assigned.')
        health=[r['player_hp'] for r in row['trace']]
        self.check('Contact deals2HP once during22-frame invulnerability window',
                   min(health)==hp-2 and health[-1]==hp-2,dict(before=hp,health=health))

    def menus(self):
        self.enter(3)
        self.begin('mixed-tools-menus')
        initial=P.r16(self.c,self.symbols['sNextTile'])&65535
        self.run(2,('START',));self.run(14)
        self.check('Start opens real item menu',C.gstate(self.c)==4)
        for label,keys in (('keys',('R',)),('overview',('R',)),('zoom',('A',))):
            self.run(2,keys);self.run(12)
            self.check('actual '+label+' page remains open',C.gstate(self.c)==4)
        self.run(2,('B',));self.run(8);self.run(2,('START',));self.run(24)
        self.check('menu closes back to live mixed encounter',C.gstate(self.c)==1 and len(self.enemies())==3)
        pl=P.sym('gPl');P.w8(self.c,pl+9,6)
        self.fixtures.append(dict(action='inventory equip',button='A',item='owned bow'))
        before=P.r8(self.c,pl+35)
        self.run(2,('A',));self.run(24)
        self.check('real bow input consumes one arrow',P.r8(self.c,pl+35)==before-1)
        row=self.finish('Actual Start/R/R/A/B/Start navigation and real A bow input. Full lab inventory and button assignment are fixtures.')
        self.check('mixed menus/bow never invade HUD tile banks',all(r['next_tile']<=876 for r in row['trace']))
        self.check('bow has real projectile sheet allocation',any(r['projectiles'] for r in row['trace']))
        arrows=[a for r in row['trace'] for a in r['projectiles'] if a['type']==3]
        arrow_meta,_=self.native.sheet('arrow')
        self.check('bow after menus uses genuine arrow tiles and material palette',bool(arrows) and
                   all(a['sheet']==self.native.sheet_ids['arrow'] and a['tile']>0 and
                       a['tile']+arrow_meta['tile_count']<=876 and a['palette']==arrow_meta['pal'] for a in arrows),
                   dict(arrow_metadata=arrow_meta,actors=arrows[:2]))
        expected={self.native.sheet_ids[name]:self.native.sheet(name)[0]
                  for name in ('proto_rope','proto_leever','proto_helmasaur')}
        self.check('all three mixed actors retain real allocated sheets after menus',
                   len(self.enemies())==3 and all(a['sheet'] in expected and a['tile']>0 and
                   a['tile']+expected[a['sheet']]['tile_count']<=876 and a['palette']==expected[a['sheet']]['pal']
                   for a in self.enemies()),self.enemies())
        return initial

    def save(self):
        source=self.bundle/'source-commit.txt'
        report=dict(emulator='mGBA 0.10.5',method=__doc__.strip(),
                    bundle=str(self.bundle),rom_sha256=SHA((self.bundle/'bartgame.gba').read_bytes()),
                    tool_sha256=SHA(Path(__file__).read_bytes()),
                    source_commit=source.read_text().strip() if source.exists() else 'unavailable',
                    checks=self.checks,scenarios=self.rows,media=self.media,all_fixtures=self.fixtures)
        (self.out/'review.json').write_text(json.dumps(report,indent=2)+'\n')

    def run_all(self):
        jobs=[('rope',self.rope),('maw',self.maw),('armor',self.armor),('arrows',self.arrows),
              ('bombs-buried',lambda:self.bomb(True)),('bombs-exposed',lambda:self.bomb(False)),
              ('contact',self.contact)]
        jobs += [('idle-'+NAMES[case],lambda case=case:self.idle(case,frames=self.args.frames))
                 for case in range(4)]
        jobs.append(('menus',self.menus))
        if self.args.backgrounds:
            jobs += [('background-'+background,lambda background=background:self.idle(3,background,160))
                     for background in ('sewer','deep')]
        for name,job in jobs:
            if self.args.only and not any(name.startswith(part) for part in self.args.only.split(',')):
                continue
            try:
                job()
            except Exception as error:
                self.check(name+' scenario completed',False,dict(error=type(error).__name__,message=str(error)))
                if self.label and self.images:
                    self.finish('SCENARIO INCOMPLETE: '+repr(error))
                else:
                    self.label=None
                self.save()
        self.save()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--frames',type=int,default=360)
    parser.add_argument('--sample',type=int,default=4)
    parser.add_argument('--backgrounds',action='store_true')
    parser.add_argument('--only',help='comma-separated scenario prefixes for private pilots')
    args=parser.parse_args()
    review=Review(args)
    review.run_all()
    raise SystemExit(any(not check['passed'] for check in review.checks))


if __name__=='__main__':main()
