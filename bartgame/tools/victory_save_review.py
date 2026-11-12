#!/usr/bin/env python3
"""Verify win-to-new-run lifecycle in the actual normal ROM under mGBA.

The Heart keeps its real40HP, AI, flags and timers; sword inputs and Grail
pickup produce victory. Disclosed fixtures position/heal/protect the player,
use the existing room-transition request, seed generation and inject private
serialized SRAM records for compatibility/profile cases. A separate death-save
counterprobe sets player death state/timer, never an enemy's. Native PNGs are
untouched framebuffers. No save file outside these private cores is opened.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import traceback
from types import SimpleNamespace

import mgba.core
import mgba.image
import probe as P
import bloom_probe as B
import critical_path as C
import save_probe as S
from arcade_journal_review import profile, preferences
from regional_native_support import compile_abi

SHA=lambda b:hashlib.sha256(b).hexdigest()
SRAM=0x0E000000
PROFILE=0x7EC0
PREFS=0x7F00
GOAL=4+25*13+1


def read(c,at,n):return bytes(c.memory.u8[at+i] for i in range(n))
def write(c,at,data):
    for i,b in enumerate(data):P.w8(c,at+i,b)
def w32(c,at,value):
    P.w16(c,at,value&65535);P.w16(c,at+2,value>>16)


class Review:
    def __init__(self,args):
        self.bundle=Path(args.bundle).resolve();self.out=Path(args.out).resolve();self.out.mkdir(parents=True,exist_ok=True)
        P.ROM=str(self.bundle/'bartgame.gba')
        self.defs=B.configure(SimpleNamespace(map=str(self.bundle/'bartgame.map'),assets_header=str(self.bundle/'assets.h')))
        C.mt=lambda name:self.defs['MT_'+name]
        self.rows=[];self.media=[];self.history=[];self.contexts=[]
        try:self.opening_pending=P.sym('gStartingDraft')
        except KeyError:self.opening_pending=None
        self.abi=compile_abi(self.bundle,self.out/'abi') if self.opening_pending else None
        self.begin_base=None
        self.fixtures=[
            'Independent in-memory32768-byte SRAM starts erased; valid journal/appearance records are explicit profile fixtures, not earned catalogue coverage.',
            'Ordinary death/save counterprobes set only player PS_DEAD/dead_timer; normal save serialization and title/Continue run in the ROM.',
            'Compatibility inputs alter serialized version/checksum and goal or non-goal cleared flags; no enemy or terrain is edited.',
            'The real fight bypasses maze travel with the existing transition request, supplies player health/invulnerability and positions only the player. Enemy original40HP, AI, state, flags and timers remain live.',
            'Actual B sword inputs kill the Heart, and touching its actual spawned Grail triggers GS_WIN. Native captures remain untouched.',
            'New-run starting inventory is observed before the first opening gift; three default gifts are then selected by actual A inputs. Draft data is read using ARM ABI offsets compiled from the pinned source headers.'
        ]

    def check(self,name,ok,detail=None):
        self.rows.append(dict(name=name,passed=bool(ok),detail=detail));print(('PASS ' if ok else 'FAIL ')+name,flush=True)
        return bool(ok)

    def run(self,c,n=1,keys=(),heal=False):
        c.clear_keys(*range(10));c.set_keys(*(P.key(c,k) for k in keys))
        for _ in range(n):
            if heal:P.w16(c,P.sym('gPl'),80)
            c.run_frame()
        c.clear_keys(*range(10))

    def press(self,c,key,hold=2,release=8,heal=False):
        self.run(c,hold,(key,),heal);self.run(c,release,heal=heal)

    def fresh(self,records=None):
        c=mgba.core.load_path(P.ROM);c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
        write(c,SRAM,b'\xff'*32768)
        for at,data in (records or {}).items():write(c,SRAM+at,data)
        self.run(c,45)
        return c

    def has_continue(self,c):return P.r8(c,B.static_symbol('sTitleHasSave'))!=0

    def begin(self,c,seed):
        w32(c,P.sym('gSeedOverride'),seed);self.press(c,'START',2,4)
        ready=None;self.begin_base=None
        for _ in range(2400):
            pending=self.opening_pending and P.r8(c,self.opening_pending)
            if pending and C.gstate(c)==1 and self.begin_base is None:
                self.begin_base=self.inventory(c)
                self.contexts.append(dict(kind='observed new-run inventory before any gift input',seed=seed,inventory=self.begin_base))
            if P.r8(c,P.sym('gTbActive')) or pending:self.press(c,'A',2,6)
            else:self.run(c,4)
            if C.gstate(c)==1 and P.r8(c,P.sym('gActors'))==1 and not P.r8(c,P.sym('gTbActive')) and not (self.opening_pending and P.r8(c,self.opening_pending)):
                now=P.r32(c,P.sym('gGame')+8)
                if ready is None:ready=now
                if now-ready>=3:return
            else:ready=None
        raise AssertionError('title selection did not settle into live Drain')

    def masks(self,c):return [P.r32(c,P.sym('gJournalItems')),P.r16(c,P.sym('gJournalEnemies'))&65535]

    def shot(self,c,name):
        p=self.out/(name+'.png');P.snap(c,str(p));self.media.append(dict(file=p.name,sha256=SHA(p.read_bytes()),kind='untouched native240x160 mGBA framebuffer'))

    def death_record(self,c):
        C.dismiss(c,1000)
        P.w8(c,P.sym('gActors')+2,7);P.w8(c,P.sym('gPl')+24,121)
        self.run(c,8)
        return S.record(c)[1]

    def inventory(self,c):
        pl=P.sym('gPl')
        return dict(hp=P.r16(c,pl),max_hp=P.r16(c,pl+2),gilt=P.r16(c,pl+4),keys=P.r8(c,pl+6),bombs=P.r8(c,pl+7),items=P.r8(c,pl+8),arrows=P.r8(c,pl+35),items2=P.r8(c,pl+36))

    def new_run_checks(self,c,seed,label):
        world=C.world(c);pl=P.sym('gPl');w=P.sym('gWorld')
        self.check(label+' uses new seed',P.r32(c,w)==seed,hex(P.r32(c,w)))
        self.check(label+' returns to ordinary Drain',C.area(c)==0 and C.gstate(c)==1)
        self.check(label+' Heart is alive and all gates/loot reset',all(P.r8(c,w+4+i*13+4)==0 and P.r8(c,w+4+i*13+11)&0xfe==0 for i in range(25)),world['goal'])
        inventory=self.begin_base if self.opening_pending else self.inventory(c)
        self.check(label+' restores starting inventory before opening gifts',inventory==dict(hp=24,max_hp=24,gilt=0,keys=0,bombs=0,items=65,arrows=0,items2=2),dict(pre_gift=inventory,after_real_gifts=self.inventory(c)))
        if self.opening_pending:
            h=P.sym('gHandoffState');a=self.abi
            self.check(label+' finishes all three new opening rounds through actual inputs',P.r8(c,h+a['handoff_draft_round'])==3 and P.r8(c,h+a['handoff_draft_state'])==a['enum_draft_done'] and not P.r8(c,self.opening_pending))
        self.check(label+' resets run counters',P.r16(c,P.sym('gGame')+12)==0 and P.r16(c,P.sym('gGame')+14)==0)

    def fixture_record(self,raw,version=2,clear_goal=False,clear_other=False):
        data=bytearray(raw);struct.pack_into('<H',data,4,version);goal=data[8+GOAL]
        if clear_goal:data[8+4+goal*13+11]|=0x20
        if clear_other:data[8+4+((goal+1)%25)*13+11]|=0x20
        struct.pack_into('<I',data,len(data)-4,S.checksum(data[:-4]))
        return bytes(data)

    def compatibility(self):
        initial={PROFILE:profile((1<<4)|(1<<8),1<<7,8),PREFS:preferences(2,1)}
        c=self.fresh(initial);self.begin(c,0xb4a7)
        pl=P.sym('gPl');P.w16(c,pl+4,37);P.w8(c,pl+6,2);P.w8(c,pl+7,5);P.w8(c,pl+8,67)
        base=self.death_record(c);self.base=base;self.profile_after_save=read(c,SRAM+PROFILE,76)
        self.check('ordinary unfinished death produces valid version2 record',struct.unpack_from('<H',base,4)[0]==2)
        (self.out/'unfinished-v2.bin').write_bytes(base)
        for version in (1,2):
            for finished in (False,True):
                raw=self.fixture_record(base,version,clear_goal=finished)
                fresh=self.fresh({0:raw,PROFILE:self.profile_after_save})
                label='v%d %s'%(version,'completed' if finished else 'unfinished')
                self.check(label+' title eligibility',self.has_continue(fresh)==(not finished))
                self.check(label+' preserves profile/settings while examining save',read(fresh,SRAM+PROFILE,76)==self.profile_after_save)
                self.begin(fresh,0xc0de+version)
                if finished:self.new_run_checks(fresh,0xc0de+version,label)
                else:
                    self.check(label+' Continue retains seed/inventory',P.r32(fresh,P.sym('gWorld'))==0xb4a7 and P.r16(fresh,pl+4)==37 and P.r8(fresh,pl+6)==2 and P.r8(fresh,pl+7)==5)
                    self.check(label+' continued Heart remains available',not P.r8(fresh,P.sym('gWorld')+4+C.world(fresh)['goal']*13+11)&0x20)
        non_goal=self.fixture_record(base,clear_other=True)
        c=self.fresh({0:non_goal,PROFILE:self.profile_after_save});self.check('cleared non-goal cell does not retire active run',self.has_continue(c))
        self.begin(c,0xfade)
        goal=C.world(c)['goal'];self.check('non-goal cleared marker survives ordinary Continue',P.r32(c,P.sym('gWorld'))==0xb4a7 and P.r8(c,P.sym('gWorld')+4+((goal+1)%25)*13+11)&0x20)
        # The title cached an active checkpoint. Replacing only its private
        # serialized input proves save_load also defends the Continue path.
        c=self.fresh({0:base,PROFILE:self.profile_after_save});assert self.has_continue(c)
        write(c,SRAM,self.fixture_record(base,clear_goal=True));self.begin(c,0xbeef)
        self.check('Continue rechecks a checkpoint retired after title draw',P.r32(c,P.sym('gWorld'))!=0xb4a7 and not P.r8(c,P.sym('gWorld')+4+C.world(c)['goal']*13+11)&0x20 and (self.begin_base['gilt']==0 if self.opening_pending else P.r16(c,pl+4)==0))
        # Separate live completed-state serialization counterprobe: no combat
        # claim here. Death must not recreate a resumable spent world.
        c=self.fresh({0:base,PROFILE:self.profile_after_save});self.begin(c,0)
        at=P.sym('gWorld')+4+C.world(c)['goal']*13+11;P.w8(c,at,P.r8(c,at)|0x20)
        before=read(c,SRAM+PROFILE,76);P.w8(c,P.sym('gActors')+2,7);P.w8(c,pl+24,121);self.run(c,8)
        self.check('death cannot serialize a cleared-goal checkpoint',P.r32(c,SRAM)!=S.MAGIC)
        self.check('completed-state death guard preserves profile/settings',read(c,SRAM+PROFILE,76)==before)

    def warp_goal(self,c):
        goal=C.world(c)['goal']
        for name,value in [('sNextArea',1),('sNextCell',goal),('sNextSide',2),('sTransPhase',0)]:P.w8(c,B.static_symbol(name),value)
        P.w8(c,P.sym('gGame'),2)
        for _ in range(2400):
            self.run(c,heal=True)
            if C.gstate(c)==1 and C.area(c)==1 and C.cell(c)==goal:break
        else:raise AssertionError('goal transition did not settle')
        self.run(c,30,heal=True)

    def actual_victory(self):
        c=self.fresh({0:self.base,PROFILE:self.profile_after_save});self.check('real victory begins from a resumable checkpoint',self.has_continue(c));self.begin(c,0)
        self.warp_goal(c);hero=P.sym('gActors');pl=P.sym('gPl')
        for attempt in range(80):
            e=C.find_actor(c,2,5)
            if not e:break
            self.history.append(dict(attempt=attempt,hp=e['hp'],state=e['state'],x=e['x'],y=e['y']))
            P.w16(c,pl,80);P.w16(c,pl+2,80);P.w8(c,hero+28,255)
            if e['hp']>0:
                # Player-only coordinate fixture. Do not alter enemy motion,
                # HP, AI phase, vulnerability, direction or clock.
                w32(c,hero+8,e['x']<<16);w32(c,hero+12,(e['y']+24)<<16)
                P.w16(c,pl+14,e['x']);P.w16(c,pl+16,e['y']+24)
                P.w8(c,hero+7,0);P.w8(c,hero+6,0)
                self.press(c,'B',2,28,heal=True)
            else:self.run(c,10,heal=True)
        self.run(c,150,heal=True)
        self.check('original40HP Heart dies to actual sword inputs',bool(self.history) and self.history[0]['hp']==40 and C.find_actor(c,2,5) is None,self.history)
        grail=C.find_actor(c,4,6);self.check('real boss death spawns Grail',grail is not None or C.gstate(c)==6)
        self.check('goal cleared by real boss death',P.r8(c,P.sym('gWorld')+4+C.world(c)['goal']*13+11)&0x20)
        if grail:
            self.shot(c,'01-grail-before-win')
            w32(c,hero+8,grail['x']<<16);w32(c,hero+12,(grail['y']+2)<<16)
            P.w16(c,pl+14,grail['x']);P.w16(c,pl+16,grail['y']+2)
        for _ in range(120):
            self.run(c,heal=True)
            if C.gstate(c)==6:break
        self.check('touching actual Grail wins',C.gstate(c)==6)
        victory_stats=[P.r16(c,pl+4),P.r16(c,P.sym('gGame')+12),P.r16(c,P.sym('gGame')+14)]
        self.check('win immediately retires prior checkpoint',P.r32(c,SRAM)!=S.MAGIC)
        self.check('win learns real Heart and Grail discoveries',self.masks(c)[0]&(1<<22) and self.masks(c)[1]&(1<<5),self.masks(c))
        self.check('win preserves appearance preference values',P.r8(c,P.sym('gAppearanceStyle'))==2 and P.r8(c,P.sym('gAppearancePalette'))==1)
        won_sram=read(c,SRAM,32768);won_masks=self.masks(c);tail=won_sram[PROFILE:PREFS+12]
        self.run(c,220);self.shot(c,'02-victory-summary')
        self.check('victory screen retains run statistics',victory_stats==[P.r16(c,pl+4),P.r16(c,P.sym('gGame')+12),P.r16(c,P.sym('gGame')+14)],victory_stats)
        self.press(c,'START',2,45)
        self.check('same-session home screen no longer offers Continue',C.gstate(c)==0 and not self.has_continue(c))
        self.shot(c,'03-home-after-win')
        self.check('returning home keeps journal/settings',self.masks(c)==won_masks and read(c,SRAM+PROFILE,76)==tail)
        self.begin(c,0xc0ffee);self.new_run_checks(c,0xc0ffee,'same-session next play')
        self.check('next run retains discoveries/settings',self.masks(c)==won_masks and read(c,SRAM+PROFILE,76)==tail)
        self.shot(c,'04-fresh-run')
        cold=self.fresh({0:won_sram});self.check('cold restart after victory has no Continue',not self.has_continue(cold))
        self.check('cold restart recovers journal/preferences',self.masks(cold)==won_masks and read(cold,SRAM+PROFILE,76)==tail)
        self.shot(cold,'05-cold-home-after-win');self.begin(cold,0xd00d);self.new_run_checks(cold,0xd00d,'cold-restart next play')
        self.check('cold new run retains profile and preferences',self.masks(cold)==won_masks and P.r8(cold,P.sym('gAppearanceStyle'))==2 and P.r8(cold,P.sym('gAppearancePalette'))==1)
        (self.out/'post-victory-private-sram.bin').write_bytes(won_sram)

    def all(self):
        error=None
        try:self.compatibility();self.actual_victory()
        except Exception:
            error=traceback.format_exc();print(error,flush=True);self.check('review completes',False,error)
        report=dict(method=__doc__,source_commit=(self.bundle/'source-commit.txt').read_text().strip(),rom_sha256=SHA((self.bundle/'bartgame.gba').read_bytes()),tool_sha256=SHA(Path(__file__).read_bytes()),
                    fixtures=self.fixtures,opening_observations=self.contexts,checks=self.rows,passed=sum(r['passed'] for r in self.rows),total=len(self.rows),fight=self.history,media=self.media,error=error)
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('RESULT',report['passed'],'/',report['total'],flush=True)
        return int(error is not None or report['passed']!=report['total'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True);p.add_argument('--out',required=True)
    return Review(p.parse_args()).all()


if __name__=='__main__':raise SystemExit(main())
