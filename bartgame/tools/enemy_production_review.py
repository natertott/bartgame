#!/usr/bin/env python3
"""Real mGBA production combat, streaming and wave-boundary qualification.

Disclosed fixtures: normal title seed and transition requests; private blank
SRAM; player loadout/healing; existing gDbgSpawn path; nonplayer actor isolation
and safe coordinate-only actor positioning. Enemy HP, AI state/facing, timers,
poses and flags are never assigned. Terrain, clocks, palettes, VRAM, OAM and
framebuffers are never edited. Bomb counterprobes place target coordinates into
an ordinarily timed blast; they are not unassisted combat recordings.
"""
import argparse
from collections import Counter
import hashlib
import json
import subprocess
from pathlib import Path
import traceback

import probe as P
import critical_path as C
from arcade_journal_review import Review as Base, bytes_at, w32, signed
from sewer_concept_review import safe

SHA=lambda b:hashlib.sha256(b).hexdigest()
DXY=((0,-1),(1,0),(0,1),(-1,0))


def route_differential(out):
    """Compile the actual optimized C function against an exhaustive old formula."""
    source=Path(__file__).resolve().parent.parent/'src/enemy_prototypes.c'
    text=source.read_text();a=text.index('static bool8 reachable_dry(');b=text.index('\nstatic bool8 maw_emergence',a)
    function=text[a:b]
    harness=r'''#include <stdio.h>
#include <stdint.h>
typedef int bool8;
#define TRUE 1
#define FALSE 0
#define PX(v) ((v)>>16)
#define ABS(v) ((v)<0?-(v):(v))
#define MAX(a,b) ((a)>(b)?(a):(b))
typedef struct {int x,y;} Actor;
static Actor player={100<<16,200<<16};
static Actor* gPlayer=&player;
static int px[512],py[512],count;
static bool8 dry_footprint(int x,int y) {px[count]=x;py[count]=y;count++;return TRUE;}
'''+function+r'''
int main(void) {
    int dx,dy,i;long long vectors=0,samples=0;
    for(dx=-512;dx<=512;dx++) for(dy=-512;dy<=512;dy++) {
        int n=(MAX(ABS(dx),ABS(dy))+3)/4;
        count=0;
        if(!reachable_dry(100+dx,200+dy) || count!=n+1) return 1;
        if(px[0]!=100 || py[0]!=200) return 2;
        for(i=1;i<=n;i++) if(px[i]!=100+dx*i/n || py[i]!=200+dy*i/n) {
            fprintf(stderr,"mismatch dx%d dy%d sample%d\n",dx,dy,i);return 3;
        }
        vectors++;samples+=count;
    }
    printf("%lld %lld\n",vectors,samples);return 0;
}
'''
    folder=Path(out)/'route-host';folder.mkdir(parents=True,exist_ok=True)
    (folder/'test.c').write_text(harness)
    subprocess.run(['cc','-O2','-std=c99','-Wall','-Werror',str(folder/'test.c'),'-o',str(folder/'test')],check=True)
    values=subprocess.check_output([str(folder/'test')],text=True).split()
    result=dict(method='Actual extracted reachable_dry C, dry-footprint recorder, exhaustive comparison to original signed C division at every sample.',
        source_sha256=SHA(source.read_bytes()),function_sha256=SHA(function.encode()),harness_sha256=SHA(harness.encode()),
        vectors=int(values[0]),sample_coordinates=int(values[1]),dx_dy_range=[-512,512],zero_vector=True,passed=True)
    (Path(out)/'route-differential.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


class Review(Base):
    def __init__(self,args):
        super().__init__(args)
        self.c=None;self.scenarios=[];self.active=None;self.trace=[];self.images=[];self.performance=[]
        result=route_differential(self.out)
        self.check('exact rational route coordinates match original C division',result['passed'],result)

    def actor(self,c,i):
        a=super().actor(c,i)
        if a['kind']==2 and a['type']>=6:
            at=self.at('gActors')+i*64
            a['anchor']=[P.r16(c,at+48)&65535,P.r16(c,at+50)&65535]
            a['velocity']=[signed(P.r16(c,at+54)&65535),signed(P.r16(c,at+56)&65535)]
        return a

    def target(self,typ):
        return next((a for a in self.enemies(self.c) if a['type']==typ),None)

    def events(self):
        return [P.r16(self.c,self.at('gEnemyPrototypeEvents')+i*2)&65535 for i in range(7)]

    def pool(self):
        base=self.at('sStream');count=P.r8(self.c,self.at('sStreamCount'))
        return [dict(slot=i,tile=P.r16(self.c,base+i*4)&65535,owner=P.r8(self.c,base+i*4+2),frame=P.r8(self.c,base+i*4+3)) for i in range(count)]

    def tick(self,n=1,keys=(),heal=True):
        for _ in range(n):
            expected=self.stream_before(self.c)
            before=P.r32(self.c,self.at('gGame')+8)
            super().run(self.c,1,keys,heal=heal)
            matches=self.stream_check(self.c,expected)
            if self.active:
                self.trace.append(dict(frame=P.r32(self.c,self.at('gFrame')),updates=P.r32(self.c,self.at('gGame')+8),
                    delta=P.r32(self.c,self.at('gGame')+8)-before,state=C.gstate(self.c),area=C.area(self.c),cell=C.cell(self.c),
                    enemies=self.enemies(self.c),player_hp=P.r16(self.c,self.at('gPl')),events=self.events(),pool=self.pool(),
                    next_tile=P.r16(self.c,self.at('sNextTile'))&65535,stream_matches=matches,held=list(keys)))
                self.images.append(self.c.bg_video.to_pil().convert('RGB').copy())

    def wait_for(self,pred,limit=600):
        for _ in range(limit):
            if pred():return True
            self.tick()
        return bool(pred())

    def begin(self,name):
        self.active=name;self.trace=[];self.images=[];self.fixture_start=len(self.fixtures)

    def end(self,note,media=True):
        name=self.active
        self.scenarios.append(dict(name=name,note=note,fixtures=self.fixtures[self.fixture_start:],trace=self.trace))
        if media:self.clip(name,self.images,4)
        checks=[m for r in self.trace for m in r['stream_matches']]
        self.check(name+' exact ROM-to-VRAM streamed frame payloads',bool(checks) and all(m[2] for m in checks),dict(samples=len(checks)))
        self.check(name+' world OBJ below reserved HUD',all(0<r['next_tile']<=876 for r in self.trace),max(r['next_tile'] for r in self.trace))
        self.active=None

    def isolate(self,keep_boss=False):
        removed=[]
        for a in [self.actor(self.c,i) for i in range(1,96)]:
            if a['kind'] and not(keep_boss and a['kind']==2 and a['type']==5):
                P.w8(self.c,self.at('gActors')+a['index']*64,0);removed.append((a['index'],a['kind'],a['type']))
        self.fixtures.append(dict(action='controlled actor isolation',removed=removed,keep_real_boss=keep_boss))

    def native_dry(self,x,y):
        room=self.at('gRoom');w,h=P.r8(self.c,room)*16,P.r8(self.c,room+1)*16
        if not(24<=x<=w-24 and 32<=y<=h-16):return False
        for px,py in [(x-6,y-2),(x+6,y-2),(x-6,y-10),(x+6,y-10)]:
            mt=P.r16(self.c,room+2+((py//16)*32+px//16)*2)&65535
            if mt==65535 or P.r8(self.c,self.at('metatile_type')+mt)!=0:return False
        return not any(P.r8(self.c,room+4098+yy*64+xx) for yy in range((y-12)//8,(y-1)//8+1) for xx in range((x-7)//8,(x+6)//8+1))

    def spawn_player_point(self,count,typ):
        room=self.at('gRoom');w,h=P.r8(self.c,room)*16,P.r8(self.c,room+1)*16
        points=[]
        for y in range(104,h-24,8):
            for x in range(88,w-24,8):
                if not safe(self.c,x,y):continue
                okay=True
                for i in range(count):
                    ex=max(24,min(w-24,x-60+(i%8)*16));ey=max(40,min(h-24,y-60+(i//8)*20))
                    offsets=[(0,0)] if typ!=8 else [(0,0),(-16,0),(16,0),(0,-16),(0,16)]
                    if not all(self.native_dry(ex+dx,ey+dy) for dx,dy in offsets):okay=False;break
                if okay:points.append((abs(x-w//2)+abs(y-h//2),x,y))
        assert points,('no unchanged room patch for request',count,typ,w,h)
        _,x,y=min(points);return x,y

    def request(self,typ,count=1):
        before={a['index'] for a in self.enemies(self.c)}
        w32(self.c,self.at('gDbgSpawn'),(count<<8)|typ)
        self.fixtures.append(dict(action='existing developer spawn request',type=typ,count=count))
        first=None
        for _ in range(180):
            self.tick()
            new=[a for a in self.enemies(self.c) if a['index'] not in before]
            now=P.r32(self.c,self.at('gGame')+8)
            if not P.r32(self.c,self.at('gDbgSpawn')) and len(new)==count:
                if first is None:first=now
                if now-first>=3:return new
        raise AssertionError(('spawn request did not settle',typ,count,new))

    def enter(self,typ,count=1,myst=False):
        self.c=self.fresh();self.world=C.world(self.c)
        cell=self.world['key_cell'][1] if myst else self.world['entry']
        self.warp(self.c,2 if myst else 1,cell)
        # A live wave is established before replacing its roster, without ever
        # assigning trial phase or victory flags.
        if myst:self.wait_for(lambda:bool(self.enemies(self.c)),100)
        pl=self.at('gPl');P.w16(self.c,pl,80);P.w16(self.c,pl+2,80);P.w8(self.c,pl+7,20)
        P.w8(self.c,pl+8,0x6f);P.w8(self.c,pl+35,50);P.w8(self.c,pl+36,0x0f)
        for i,e in enumerate((2,1,5)):P.w8(self.c,pl+9+i,e)
        x,y=self.spawn_player_point(count,typ)
        self.position(self.c,0,x,y,0)
        # No live sample until the ordinary camera reaches this patch.
        self.tick(96)
        self.isolate() # preserve the first real wave through camera setup
        made=self.request(typ,count)
        self.check('controlled type%d request produces%d actual bodies'%(typ,count),len(made)==count and all(a['type']==typ for a in made),made)
        assert len(made)==count and all(a['type']==typ for a in made)

    def lane(self,minimum=100):
        room=self.at('gRoom');w,h=P.r8(self.c,room)*16,P.r8(self.c,room+1)*16;best=[]
        for y in range(48,h-24,8):
            run=[]
            for x in range(32,w-24,4):
                if self.native_dry(x,y):run.append((x,y))
                else:
                    if len(run)>len(best):best=run
                    run=[]
            if len(run)>len(best):best=run
        assert best and best[-1][0]-best[0][0]>=minimum
        return best[0],best[-1]

    def near(self,enemy,front=True,distance=22):
        f=enemy['facing'];dx,dy=DXY[f]
        if not front:dx,dy=-dx,-dy
        x,y=round(enemy['x'])+dx*distance,round(enemy['y'])+dy*distance
        if not safe(self.c,x,y):return False
        self.position(self.c,0,x,y,(f+2)%4 if front else f);return True

    def armor(self):
        self.enter(8);self.begin('snout-front-rear-production')
        self.check('Snout enters its natural locked60-update tell',self.wait_for(lambda:self.target(8)['state']==1,100))
        a=self.target(8);left,right=self.lane();self.position(self.c,a['index'],(left[0]+right[0])//2,left[1])
        self.check('front sword approach is real safe floor',self.near(self.target(8)))
        hp=self.target(8)['hp'];blocks=self.events()[2]
        self.tick(2,('B',));self.tick(23)
        self.check('actual front sword clang preserves4HP',self.target(8)['hp']==hp==4 and self.events()[2]>blocks,self.target(8))
        self.check('rear sword approach is real safe floor',self.near(self.target(8),False))
        self.tick(2,('B',));self.tick(24)
        self.check('actual rear sword removes2HP',self.target(8) and self.target(8)['hp']==hp-2,self.target(8))
        self.end('Real normal-build B sword: front blocked, rear accepted. Coordinates only are fixtures; HP, facing and AI clocks remain live.')

    def maw(self):
        self.enter(7);self.begin('maw-buried-surface-production')
        a=self.target(7);hp=a['hp'];anchor=a['anchor'];self.check('Maw begins live, buried and protected',a['state']==4 and not a['flags']&10,a)
        self.check('buried sword approach is safe',self.near(a))
        self.tick(2,('B',));self.tick(22)
        self.check('actual sword leaves buried6HP unchanged',self.target(7)['hp']==hp==6)
        self.check('Maw enters24-update harmless emergence',self.wait_for(lambda:self.target(7)['state']==5,240) and self.target(7)['timer']==24 and not self.target(7)['flags']&10,self.target(7))
        self.check('Maw naturally exposes for180updates',self.wait_for(lambda:self.target(7)['state']==6,30) and self.target(7)['timer']==180 and self.target(7)['flags']&10==10,self.target(7))
        self.check('surface sword approach is safe',self.near(self.target(7)))
        self.tick(2,('B',));self.tick(26)
        self.check('actual sword removes2 exposed HP',self.target(7)['hp']==hp-2,self.target(7))
        self.check('Maw returns to240-update buried cooldown',self.wait_for(lambda:self.target(7)['state']==4,240) and self.target(7)['timer']==240,self.target(7))
        observed=[a for r in self.trace for a in r['enemies'] if a['type']==7]
        self.check('original anchor survives actual movement and sword recoil',all(a['anchor']==anchor for a in observed) and
            any(a['kb'] for a in observed) and any(a['velocity']!=[0,0] for a in observed),anchor)
        x,y=self.fringe(anchor);self.position(self.c,0,x,y,0);before=self.events()[4]
        self.check('subsequent burrow retries genuinely obstructed origin',self.wait_for(lambda:self.target(7)['state']==5,360) and self.events()[4]>=before+2,self.events())
        second=self.target(7)
        self.check('second-cycle fallback returns to unchanged original anchor',
            [round(second['x']),round(second['y'])]==anchor and second['anchor']==anchor and second['timer']==24 and not second['flags']&10,second)
        self.end('Production live Maw phase/damage cycle and second-burrow fallback after actual exposed movement and sword recoil; coordinate/player healing fixtures only.')

    def fringe(self,anchor):
        room=self.at('gRoom');w,h=P.r8(self.c,room)*16,P.r8(self.c,room+1)*16
        points=[(abs(x-anchor[0])+abs(y-anchor[1]),x,y)
                for y in range(32,h-16,2) for x in range(24,w-24,2)
                if safe(self.c,x,y) and not self.native_dry(x,y)]
        assert points,'no actual narrow safe fringe in generated entry room'
        _,x,y=max(points);return x,y

    def fallback(self):
        self.enter(7)
        a=self.target(7);anchor=(round(a['x']),round(a['y']))
        # Player feet are narrower than the Maw dry-footprint requirement.
        # This real safe fringe defeats the strict ray origin check naturally.
        x,y=self.fringe(anchor)
        self.position(self.c,0,x,y,0)
        self.begin('maw-finite-narrow-footing')
        before=self.events()[4]
        reached=self.wait_for(lambda:self.target(7)['state']==5,210)
        a=self.target(7)
        self.check('strict-origin failures are genuinely exercised',self.events()[4]>=before+2,dict(before=before,events=self.events(),player=[x,y]))
        self.check('Maw finite fallback uses validated anchor with24harmless tell',reached and
            (round(a['x']),round(a['y']))==anchor and a['timer']==24 and not a['flags']&10,
            dict(anchor=anchor,emerged=a,video_frames=len(self.trace)))
        self.check('fallback naturally becomes hittable after warning',self.wait_for(lambda:self.target(7)['state']==6,30) and self.target(7)['flags']&10==10)
        self.end('Player-only coordinate fixture on a real walkable fringe narrower than a Maw footprint forces strict ray rejection. Original validated spawn anchor guarantees finite emergence; no terrain, enemy state/timer/HP or phase assignment.',media=False)

    def stress(self):
        for typ in (6,7,8):
            self.enter(typ,24);self.begin('sustained-type%d-24'%typ)
            self.tick(300)
            deltas=Counter(r['delta'] for r in self.trace)
            run=longest=0
            for row in self.trace:
                run=run+1 if row['delta']==0 else 0;longest=max(longest,run)
            observed=dict(type=typ,actual_bodies=24,video_frames=300,updates=sum(r['delta'] for r in self.trace),
                deltas=dict(deltas),full_cadence=deltas=={1:300},longest_repeat_run=longest,
                repeated_video_indices=[i for i,r in enumerate(self.trace) if r['delta']==0],
                scope='Synthetic24-body load exceeds normal12 spawn-marker cap. Raw isolated boundary repeats remain observations; native natural rooms have separate strict full-cadence checks.')
            self.performance.append(observed)
            self.check('type%d24-body crowd stays>=99percent without consecutive repeats'%typ,
                observed['updates']>=297 and longest<=1 and set(deltas)<=set((0,1)),observed)
            self.check('type%d all24 bodies remain alive without enemy HP edits'%typ,all(len(r['enemies'])==24 for r in self.trace))
            self.check('type%d uses no more24 recycled4-tile slots'%typ,max(len(r['pool']) for r in self.trace)<=24)
            self.end('Controlled sustained24-body request, real AI/HP and original terrain. Player HP restored for survival. No offense. First emergence/collision bursts included.',media=False)

    def mixed(self):
        self.c=self.fresh();world=C.world(self.c);self.warp(self.c,1,world['goal'])
        self.isolate(keep_boss=True)
        self.check('mixed fixture retains real spawned Heart',self.target(5) is not None)
        pl=self.at('gPl');P.w16(self.c,pl,80);P.w16(self.c,pl+2,80)
        x,y=self.spawn_player_point(1,8);self.position(self.c,0,x,y,0)
        for typ in (0,1,2,3,4,6,7,8):self.request(typ)
        self.check('all nine actual enemy families coexist',set(a['type'] for a in self.enemies(self.c))==set(range(9)))
        self.tick(80);self.begin('all-nine-mixed-production');self.tick(240)
        deltas=Counter(r['delta'] for r in self.trace)
        self.check('nine-family mixed full sampled cadence',deltas=={1:240},dict(deltas))
        self.check('nine-family fixture never loses a family',all(set(a['type'] for a in r['enemies'])==set(range(9)) for r in self.trace))
        self.end('Real goal-room Heart plus developer requests for the other eight distinct families. Existing terrain/AI/HP remain live; player healing is a survival fixture.')

    def bomb_kill_wave(self,count,initial_wait=149):
        # Place one real bomb with a full150-update fuse so the independently
        # timed initial Maws are exposed/retreating at the damage counterprobe.
        self.tick(initial_wait)
        self.check('wave has live Maws before bomb input',len(self.enemies(self.c))==count and all(a['type']==7 for a in self.enemies(self.c)))
        left,right=self.lane();point=((left[0]+right[0])//2,left[1])
        self.position(self.c,0,*point,1)
        self.tick(2,('A',))
        def bomb():return next((self.actor(self.c,i) for i in range(1,96) if P.r8(self.c,self.at('gActors')+i*64)==6 and P.r8(self.c,self.at('gActors')+i*64+1)==5),None)
        b=bomb();self.check('wave counterprobe uses an actual planted bomb',b is not None)
        assert b
        escape=next(((round(b['x'])+dx,round(b['y'])+dy) for dx,dy in ((64,0),(-64,0),(0,64),(0,-64)) if safe(self.c,round(b['x'])+dx,round(b['y'])+dy)),None)
        assert escape;self.position(self.c,0,*escape,0)
        self.wait_for(lambda:bomb() is None or bomb()['timer2']>=149,180)
        b=bomb();assert b
        self.check('every target is naturally exposed or retreating at fuse149',all(a['state'] in (6,7) and a['flags']&2 for a in self.enemies(self.c)),self.enemies(self.c))
        targets=list(self.enemies(self.c));tiles={a['tile'] for a in targets}
        for a in targets:self.position(self.c,a['index'],round(b['x']),round(b['y']))
        self.tick(12)
        self.check('actual8damage blast kills all6HP wave targets',not self.enemies(self.c),self.enemies(self.c))
        self.check('death releases every streamed slot',not any(s['owner'] for s in self.pool()),self.pool())
        return tiles

    def waves(self):
        self.enter(7,8,myst=True);self.begin('required-trial-eight-maws')
        world=C.world(self.c);cell=world['key_cell'][1]
        mystbase=4+25*13+2+3+3+3+25+1+1
        flags=self.at('gWorld')+mystbase+25+cell
        self.tick(60)
        self.check('buried live wave does not complete trial',not(P.r8(self.c,flags)&4) and len(self.enemies(self.c))==8)
        # The60-frame observation above is included in the initial cycle. The
        # bomb helper expects elapsed149 from spawn, so advance only89 more.
        self.tick(89)
        tiles=self.bomb_kill_wave(8,initial_wait=0)
        self.check('next real trial wave begins after all8 killed',self.wait_for(lambda:bool(self.enemies(self.c)),80),self.enemies(self.c))
        pool_before=len(self.pool());self.isolate()
        # Replace the second generated roster with one final live Maw through
        # the same developer request, without assigning trial/wave state.
        x,y=self.spawn_player_point(1,7);self.position(self.c,0,x,y,0);made=self.request(7)
        self.check('new wave reuses prior streamed tile',len(made)==1 and made[0]['tile'] in tiles and len(self.pool())==pool_before,made)
        self.bomb_kill_wave(1)
        self.check('final Maw death unlocks actual trial victory',self.wait_for(lambda:bool(P.r8(self.c,flags)&4),80),dict(flags=P.r8(self.c,flags),enemies=self.enemies(self.c)))
        self.end('First actual required wave replaced with8live Maws, second with1throughdeveloper requests. All kills are real full-fuse bombs; target coordinate-only overlap is disclosed. Trial phase/victory flags and enemy HP/state/timers never assigned.')

    def save_result(self):
        r=dict(method=__doc__,source_commit=(self.bundle/'source-commit.txt').read_text().strip(),rom_sha256=self.rom_sha,
            tool_sha256=SHA(Path(__file__).read_bytes()),checks=self.checks,passed=sum(x['passed'] for x in self.checks),total=len(self.checks),
            scenarios=self.scenarios,performance_observations=self.performance,media=self.media,fixtures=self.fixtures,errors=self.errors)
        (self.out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
        print('RESULT',r['passed'],'/',r['total'],flush=True)

    def all(self):
        suites=dict(armor=self.armor,maw=self.maw,fallback=self.fallback,stress=self.stress,mixed=self.mixed,waves=self.waves)
        for name in self.args.only.split(',') if self.args.only else suites:
            try:suites[name]()
            except Exception:
                error=traceback.format_exc();self.errors.append(dict(suite=name,error=error));print(error,flush=True)
                self.check(name+' completes',False,error)
                if self.active and self.trace:self.end('INCOMPLETE SCENARIO: '+error,media=False)
                self.active=None
            self.save_result()
        return int(bool(self.errors) or any(not x['passed'] for x in self.checks))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True);p.add_argument('--out',required=True);p.add_argument('--only')
    return Review(p.parse_args()).all()


if __name__=='__main__':raise SystemExit(main())
