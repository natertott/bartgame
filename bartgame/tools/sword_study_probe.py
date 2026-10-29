"""Verify opt-in sword studies against their exact frozen GBA ROM in mGBA.

Real button swings use a disclosed local physical-floor fixture, never gallery
art. Ordinary debug-spawned beetles retain their native HP; AI/position/flags
are isolated for one-update inclusive-boundary tests. No HP, damage, enemy-death
or reward flags are injected. Hardware body/weapon bytes identify the prepared
snapshot actually uploaded, rather than assuming that current logic is already
on screen. Source masks define inclusive AABBs, not per-pixel collision.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import probe as P
import critical_path as C
import bloom_probe as B
import wood_probe as W

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'art'))
import sword_studies as S

FACES=('n','e','s','w')
FIELDS=('state','age','phase','active','x0','y0','x1','y1','cam_x','cam_y',
        'foot_x','foot_y','z','facing','body_frame','fx_frame')


def digest(data):return hashlib.sha256(data).hexdigest()


def signed(value,bits=16):return value-(1<<bits) if value&(1<<(bits-1)) else value


def pack(image):
    """Independent GBA4bpp packing of a native indexed32x32 source image."""
    data=bytearray()
    for ty in range(0,32,8):
        for tx in range(0,32,8):
            for y in range(8):
                for x in range(0,8,2):
                    data.append(image.getpixel((tx+x,ty+y)) |
                                image.getpixel((tx+x+1,ty+y))<<4)
    return bytes(data)


class Study:
    def __init__(self,args):
        self.args=args;P.ROM=str(Path(args.rom).resolve())
        self.defs=B.configure(args);self.coverage=json.loads(Path(args.coverage).read_text())
        self.meta=self.coverage['sword_study'];self.variant=self.meta['id']
        self.profile=S.profile(self.variant);self.geom=self.meta['geometry']
        self.phases=self.meta['age_phase'];self.active=self.meta['age_active']
        self.total=len(self.phases);self.checks=[];self.traces=[];self.contacts=[];self.forward_contacts=[]
        self.rom_sha=digest(Path(P.ROM).read_bytes())
        self.c=B.boot(P.ROM,int(args.seed,0));B.floor_fixture(self.c,self.defs)
        self.a=P.sym('gActors');self.pl=P.sym('gPl')
        self.snapshot_at=P.sym('gSwordStudyRender')
        self.sequence_at=P.sym('gSwordStudyRenderSequence')
        self.action_tile=P.r16(self.c,B.static_symbol('sActionTile'))&65535
        self.body_meta=B.sheet_metadata(self.c,self.defs['SHEET_HERO'])
        self.fx_meta=B.sheet_metadata(self.c,self.defs['SHEET_BLOOMFX'])
        self.body_blobs={i:B.bytes_at(self.c,self.body_meta['source']+i*512,512)
                         for i in range(self.defs['SHEET_HERO_FRAMES'])}
        self.fx_blobs={i:B.bytes_at(self.c,self.fx_meta['source']+i*512,512)
                       for i in range(self.defs['SHEET_BLOOMFX_FRAMES'])}

    def check(self,label,ok,detail=None):
        row={'name':label,'passed':bool(ok)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not ok:print('FAIL',label,detail,flush=True)
        return bool(ok)

    def snapshot(self):
        values=[signed(P.r16(self.c,self.snapshot_at+i*2)&65535) for i in range(16)]
        return {**dict(zip(FIELDS,values)),
                'sequence':P.r32(self.c,self.sequence_at),
                'logic':P.r32(self.c,P.sym('gGame')+8)}

    def reset(self,facing):
        B.reset_player(self.c,facing=facing)
        P.run(self.c,8)

    def start(self):
        self.c.set_keys(P.key(self.c,'B'))
        for _ in range(12):
            P.run(self.c,1)
            if P.r8(self.c,self.a+2)==2:break
        self.c.clear_keys(P.key(self.c,'B'))
        assert P.r8(self.c,self.a+2)==2,'real sword button was not sampled'
        assert P.r8(self.c,self.a+4)==0,'input frame did not start at age0'

    def advance_to(self,age):
        for _ in range(self.total*3):
            state=P.r8(self.c,self.a+2);now=P.r8(self.c,self.a+4)
            if state==2 and now==age:return
            assert state==2 and now<age,('attack advanced past requested age',age,state,now)
            P.run(self.c,1)
        raise AssertionError(('attack did not advance',age))

    def tables_and_art(self):
        c=self.c
        self.check('opt-in profile ID agrees across header, coverage and painter',
                   self.defs['BLOOM_SWING_STUDY']==self.variant and self.profile=={k:self.meta[k] for k in self.profile})
        self.check('eight-phase clock duration agrees with metadata',
                   self.total==sum(self.profile['durations'])==self.defs['BLOOM_SWING_FRAMES'])
        self.check('ROM age phase lookup matches metadata',
                   list(B.bytes_at(c,P.sym('bloom_swing_age_phase'),self.total))==self.phases)
        self.check('ROM damage gate lookup matches metadata',
                   list(B.bytes_at(c,P.sym('bloom_swing_age_active'),self.total))==self.active)
        self.check('single contiguous damage interval with harmless first/last poses',
                   self.active[0]==self.active[-1]==0 and
                   [i for i,v in enumerate(self.active) if v]==list(range(self.active.index(1),self.total-self.active[::-1].index(1))))
        self.check('body and weapon stay legal32x32 hardware objects',
                   all(m['frame_tiles']==16 and m['width']==m['height']==32 and m['shape']==0 and m['size']==2
                       for m in (self.body_meta,self.fx_meta)))
        self.check('study appends frames without replacing original identifiers',
                   self.meta['body_frame_base']==101 and self.meta['fx_frame_base']==47 and
                   self.defs['SHEET_HERO_FRAMES']==133 and self.defs['SHEET_BLOOMFX_FRAMES']==79)
        self.check('one streamed effect slot fits current dynamic OBJ budget',
                   B.fixed_tiles(c,self.defs)['minimum_free']<=self.action_tile and self.action_tile+16<=876)
        art_metrics=[]
        for facing,face in enumerate(FACES):
            bodies=[];heads=[];roots=[]
            for phase in range(8):
                body=S.body_frame(self.variant,face,phase);fx=S.fx_frame(self.variant,face,phase)
                mask=S.damage_mask(self.variant,face,phase);origin=self.geom['origins'][facing][phase]
                bounds=self.geom['bounds'][facing][phase];box=mask.getbbox()
                body_frame=self.meta['body_frame_base']+facing*8+phase
                fx_frame=self.meta['fx_frame_base']+facing*8+phase
                label=face+' phase'+str(phase)
                self.check(label+' packed body is exact native source',self.body_blobs[body_frame]==pack(body))
                self.check(label+' packed sword is exact native source',self.fx_blobs[fx_frame]==pack(fx))
                self.check(label+' ROM origin is source origin',
                           [signed(v,8) for v in B.bytes_at(c,P.sym('bloom_swing_origin')+(facing*8+phase)*2,2)]==origin)
                self.check(label+' ROM inclusive bounds are source bounds',
                           [signed(v,8) for v in B.bytes_at(c,P.sym('bloom_swing_hit')+(facing*8+phase)*4,4)]==bounds)
                if self.profile['active_flags'][phase]:
                    got=[origin[0]+box[0],origin[1]+box[1],origin[0]+box[2]-1,origin[1]+box[3]-1] if box else None
                    self.check(label+' damaging mask exactly defines inclusive bounds',got==bounds)
                    self.check(label+' no invisible damaging pixels',
                               all(not mask.getpixel((x,y)) or fx.getpixel((x,y)) for y in range(32) for x in range(32)))
                    if face=='n':
                        self.check(label+' far-side sword avoids opaque flower pixels',
                                   all(not fx.getpixel((x,y)) or not(0<=x+origin[0]+16<32 and 0<=y+origin[1]+32<25) or
                                       not body.getpixel((x+origin[0]+16,y+origin[1]+32))
                                       for y in range(32) for x in range(32)))
                else:self.check(label+' inactive pose has no damaging mask',box is None)
                bodies.append(body.tobytes());heads.append(body.crop((4,7,28,24)).tobytes());roots.append(body.crop((5,24,28,32)).tobytes())
            art_metrics.append({'facing':face,'distinct_bodies':len(set(bodies)),
                                'distinct_flower_regions':len(set(heads)),'distinct_root_regions':len(set(roots))})
            self.check(face+' changes body, flower and roots across swing',
                       len(set(bodies))>=4 and len(set(heads))>=3 and len(set(roots))>=3,art_metrics[-1])
        return art_metrics

    def timing_and_hardware(self):
        c=self.c
        for facing,face in enumerate(FACES):
            self.reset(facing);history=[self.snapshot()];trace=[];logic_seen={};matched=0
            c.set_keys(P.key(c,'B'))
            for video in range(self.total+8):
                c.run_frame()
                if video==0:c.clear_keys(P.key(c,'B'))
                now=self.snapshot();history.append(now)
                if now['state']==2:
                    age=now['age'];logic_seen[age]=now
                    self.check(face+f' age{age} body/FX/damage share generated pose',
                               now['phase']==self.phases[age] and now['active']==self.active[age] and
                               now['body_frame']==self.meta['body_frame_base']+facing*8+self.phases[age] and
                               now['fx_frame']==self.meta['fx_frame_base']+facing*8+self.phases[age])
                    if now['active']:
                        box=self.geom['bounds'][facing][now['phase']]
                        expected=[now['foot_x']+box[0],now['foot_y']-now['z']+box[1],
                                  now['foot_x']+box[2],now['foot_y']-now['z']+box[3]]
                        self.check(face+f' age{age} snapshot carries actual world damage box',
                                   [now[k] for k in ('x0','y0','x1','y1')]==expected)
                hero=B.hero_oam(c);effect=B.effect(c,self.action_tile)
                body_blob=B.bytes_at(c,0x06010000,512)
                fx_blob=B.bytes_at(c,0x06010000+self.action_tile*32,512)
                # Prefer prior prepared snapshots: on-screen data is normally
                # one upload behind. Matching both source blobs resolves pose
                # boundaries independently; repeated ages within one pose are
                # deliberately not claimed distinguishable by pixels alone.
                candidates=list(reversed(history[:-1][-4:]))+[now]
                display=next((s for s in candidates if hero is not None and
                              body_blob==self.body_blobs.get(s['body_frame']) and
                              ((s['state']==2 and effect is not None and fx_blob==self.fx_blobs.get(s['fx_frame'])) or
                               (s['state']!=2 and effect is None))),None)
                self.check(face+f' video{video} identifies coherent hardware body/FX snapshot',display is not None)
                if display and display['state']==2:
                    matched+=1;phase=display['phase'];origin=self.geom['origins'][facing][phase]
                    self.check(face+f' video{video} authored body is not mirrored',not hero['flip'])
                    self.check(face+f' video{video} blade is anchored to same pose',
                               (effect['x'],effect['y'])==(display['foot_x']+origin[0]-display['cam_x'],
                               display['foot_y']-display['z']+origin[1]-display['cam_y']))
                    self.check(face+f' video{video} blade depth agrees with native masking',effect['index']<hero['index'])
                trace.append({'video':video,'logical':now,'display':display,
                              'hardware_hero':hero,'hardware_effect':effect})
            self.check(face+' all logical ages are observed once in one button swing',
                       sorted(logic_seen)==list(range(self.total)),sorted(logic_seen))
            self.check(face+' complete attack reaches hardware and recovers',matched>=self.total-1 and P.r8(c,self.a+2)==0)
            shown=Counter(row['display']['phase'] for row in trace
                          if row['display'] and row['display']['state']==2)
            observed=[shown[phase] for phase in range(8)]
            self.check(face+' actual hardware pose holds equal authored tick durations',
                       observed==self.profile['durations'],observed)
            self.traces.append({'facing':face,'frames':trace})

    def spawn_frozen(self):
        index=W.spawn_enemy(self.c,0,100,100)
        at=self.a+index*64
        # Retain the ordinary constructor's HP and HB_SMALL. Only harmless
        # hittability and zero-speed knockback isolate contact from AI.
        P.w8(self.c,at+31,2);P.w8(self.c,at+29,200);P.w16(self.c,at+32,0)
        P.w8(self.c,at+28,0)
        assert P.r8(self.c,at+34)==2,'ordinary beetle no longer uses HB_SMALL'
        hp=P.actor(self.c,index)['hp'];assert hp>0
        return index,at,hp

    def target_at(self,at,x,y):
        P.w16(self.c,at+8,0);P.w16(self.c,at+10,x)
        P.w16(self.c,at+12,0);P.w16(self.c,at+14,y)

    def single_update(self):
        before=P.r32(self.c,P.sym('gGame')+8)
        for _ in range(8):
            P.run(self.c,1)
            if P.r32(self.c,P.sym('gGame')+8)!=before:return
        raise AssertionError('game did not advance an update')

    def boundary_contacts(self):
        for facing,face in enumerate(FACES):
            for phase,active in enumerate(self.profile['active_flags']):
                if not active:continue
                age=self.phases.index(phase);bounds=self.geom['bounds'][facing][phase]
                for edge,(dx,dy),(ox,oy) in B.boundary_targets(facing,bounds):
                    for outside in (False,True):
                        self.reset(facing);index,at,hp=self.spawn_frozen()
                        self.start();self.advance_to(age-1)
                        x=256+dx+(ox if outside else 0);y=230+dy+(oy if outside else 0)
                        self.target_at(at,x,y);self.single_update()
                        state=B.live(self.c);after=P.actor(self.c,index)
                        hit=after['kind']!=2 or after['hp']<hp
                        label=face+f' phase{phase} {edge} '+('one pixel outside misses' if outside else 'inclusive edge hits')
                        self.check(label,hit==(not outside) and state['timer']==age and state['phase']==phase and bool(state['active']),
                                   {'age':state['timer'],'target':[x,y],'before_hp':hp,'after_kind':after['kind'],'after_hp':after['hp']})
                        self.contacts.append({'facing':face,'phase':phase,'age':age,'edge':edge,'outside':outside,
                                              'target':[x,y],'hit':hit,'native_hp_before':hp,'native_hp_after':after['hp']})

    def forward_contact_sanity(self):
        """A complete ordinary swing must reach a nearby threat straight ahead.

        Offsets place the native enemy hurt-box centre24px in front of
        Bloom's hurt-box centre. The differing foot offsets account for
        their actual vertical hitbox anchors, not a new invisible reach.
        """
        offsets=((0,-29),(24,-5),(0,19),(-24,-5))
        def actor_box(index):
            at=self.a+index*64;hb=P.r8(self.c,at+34)
            hp=P.sym('gHitboxes')+hb*4
            ox=signed(P.r8(self.c,hp),8);oy=signed(P.r8(self.c,hp+1),8)
            hw=P.r8(self.c,hp+2);hh=P.r8(self.c,hp+3)
            actor=P.actor(self.c,index);x=actor['x']+ox;y=actor['y']+oy
            return (x-hw,y-hh,x+hw-1,y+hh-1)
        for facing,(face,(dx,dy)) in enumerate(zip(FACES,offsets)):
            self.reset(facing);index,at,hp=self.spawn_frozen()
            target=(256+dx,230+dy);self.target_at(at,*target)
            hero=actor_box(0);enemy=actor_box(index)
            separate=(hero[2]<enemy[0] or enemy[2]<hero[0] or
                      hero[3]<enemy[1] or enemy[3]<hero[1])
            self.check(face+' forward sanity target is outside body contact',separate,
                       {'hero_box':hero,'target_box':enemy})
            self.start();trace=[];first_hit=None
            for _ in range(self.total*3):
                state=B.live(self.c);target_actor=P.actor(self.c,index)
                hit=target_actor['kind']!=2 or target_actor['hp']<hp
                trace.append({'state':state,'target_kind':target_actor['kind'],
                              'target_hp':target_actor['hp'],'hit':hit})
                if hit and first_hit is None:first_hit=state.copy()
                if state['state']!=2:break
                self.single_update()
            landed=first_hit is not None and first_hit['state']==2 and bool(first_hit['active'])
            self.check(face+' complete swing hits native beetle24px straight ahead during live pose',
                       landed,{'target':target,'first_hit':first_hit,'native_hp_before':hp})
            self.forward_contacts.append({'facing':face,'target_foot':list(target),
                                          'hero_box':list(hero),'target_box':list(enemy),
                                          'native_hp_before':hp,'first_hit':first_hit,
                                          'passed':landed and separate,'trace':trace})

    def harmless_poses(self):
        for facing,face in enumerate(FACES):
            first_live=self.phases[self.active.index(1)]
            bounds=self.geom['bounds'][facing][first_live]
            dx=(bounds[0]+bounds[2])//2;dy=(bounds[1]+bounds[3])//2+6
            for phase,active in enumerate(self.profile['active_flags']):
                if active:continue
                age=self.phases.index(phase)
                self.reset(facing);index,at,hp=self.spawn_frozen()
                if age:
                    self.start();self.advance_to(age-1);self.target_at(at,256+dx,230+dy);self.single_update()
                else:
                    self.target_at(at,256+dx,230+dy);self.start()
                state=B.live(self.c);after=P.actor(self.c,index)
                self.check(face+f' inactive phase{phase} cannot damage an in-range target',
                           state['timer']==age and not state['active'] and after['kind']==2 and after['hp']==hp,
                           {'tested_age':age,'observed':state,'native_hp_before':hp,'after_hp':after['hp']})

    def run(self):
        art=self.tables_and_art();self.timing_and_hardware();self.boundary_contacts();self.harmless_poses();self.forward_contact_sanity()
        self.check('frozen ROM remained unchanged throughout probe',digest(Path(P.ROM).read_bytes())==self.rom_sha)
        failures=[row for row in self.checks if not row['passed']]
        report={'rom_sha256':self.rom_sha,'emulator':'mGBA0.10.5','method':__doc__.strip(),
                'profile':self.profile,'passed':len(self.checks)-len(failures),'total':len(self.checks),
                'checks':self.checks,'failures':failures,'body_motion_metrics':art,
                'attack_traces':self.traces,'boundary_contacts':self.contacts,
                'forward_contact_sanity':self.forward_contacts,
                'hardware_age_limit':'Repeated ages within an identical pose are visually indistinguishable; matching source body+FX bytes establishes the displayed phase, and logic traces establish exact timing.'}
        Path(self.args.out).parent.mkdir(parents=True,exist_ok=True)
        Path(self.args.out).write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT %s %d/%d'%('FAIL' if failures else 'PASS',report['passed'],report['total']))
        return int(bool(failures))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',required=True);ap.add_argument('--map',required=True)
    ap.add_argument('--assets-header',required=True);ap.add_argument('--coverage',required=True)
    ap.add_argument('--out',required=True);ap.add_argument('--seed',default='0xB4A7')
    args=ap.parse_args();return Study(args).run()


if __name__=='__main__':raise SystemExit(main())
