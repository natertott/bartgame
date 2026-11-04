#!/usr/bin/env python3
"""Independent art, gameplay-scope and actual-ROM regression qualification.

Performance is measured by the separate natural/stress survey. These tests
exercise gameplay, UI and save contracts; they do not claim an unassisted run.
No game or art source is changed by this tool.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import struct

from sewer_concept_audit import NativeRom

GAME=Path(__file__).resolve().parents[1]
REPO=GAME.parent
BASELINE='11b872e9897320398fa02344cef1418733c04e9a'
SHA=lambda data:hashlib.sha256(data).hexdigest()
POINTERS={'sheets','tilesets','room_defs','tile_anims_forest','tile_anims_sewer','tile_anims_myst'}
ALLOWED_SOURCE={'actor.c','ambient.c','enemy.c','forest_trees.c','forest_trees.h',
                'game.c','main.c','objects.c','player.c','react.c','react.h','room.c','room.h',
                'text.c','performance.c','performance.h'}


def logical_source(text):
    """An explicit placement attribute changes memory, never body tokens."""
    return text.replace('IWRAM_CODE ','')


def preview_source(text):
    """Permit only the explicit restored-room cache invalidation."""
    return text.replace('#include "react.h"\n','').replace(
        '    gRoomRevision++;gRoomTorchesDirty=1; /* invalidate restored-room query caches */\n','')


def menu_source(text):
    """Reverse the two exact, separately tested presentation-only rewrites."""
    return text.replace('''    int b,f,t,y,i;
    const u32* tiles;
    if(sStudyKitReady)return;
    /* Appearance changes run on the main thread, outside this build. Read
       the selected immutable kit once rather than once for every tile row. */
    tiles=(const u32*)ui_current_tiles();''','''    int b,f,t,y,i;
    if(sStudyKitReady)return;''').replace(
        'const u32* src=tiles+t*8;','const u32* src=(const u32*)ui_current_tiles()+t*8;').replace(
        'u32 start=gFrame;int i,x,y,n,count_at=0;','u32 start=gFrame;int i,n,count_at=0;').replace('''    /* Preserve the exact600 entries and their order without two software
       divisions per tile on ARM7TDMI. The unused right/bottom cells stay clear. */
    for(y=0,i=0;y<20;y++)for(x=0;x<30;x++,i++)gBg3[y*32+x]=i|(UI_PAL<<12);''',
        '    for(i=0;i<MS_TILES;i++)gBg3[(i/30)*32+i%30]=i|(UI_PAL<<12);')


class Regression:
    def __init__(self,args):
        self.args=args;self.out=Path(args.out).resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.before=Path(args.before).resolve();self.after=Path(args.after).resolve()
        self.a=NativeRom(self.before);self.b=NativeRom(self.after)
        self.checks=[];self.suites=[]

    def check(self,name,passed,detail=None):
        row=dict(name=name,passed=bool(passed))
        if detail is not None:row['detail']=detail
        self.checks.append(row);print(('PASS ' if passed else 'FAIL ')+name,flush=True)

    def baseline_file(self,path):
        return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=REPO)

    def scope(self):
        # Read every retained authored source recursively, including metadata.
        files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE,'bartgame/art'],cwd=REPO,text=True).splitlines()
        for name in files:self.check('authored source exact '+name,SHA((REPO/name).read_bytes())==SHA(self.baseline_file(name)))
        sources=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE,'bartgame/src'],cwd=REPO,text=True).splitlines()
        for name in sources:
            if Path(name).name not in ALLOWED_SOURCE:
                if Path(name).name=='actor.h':
                    self.check('protected actor declarations exact except IWRAM placement',
                               logical_source((REPO/name).read_text())==logical_source(self.baseline_file(name).decode()))
                elif Path(name).name=='roomgen.c':
                    self.check('room generation exact except explicit preview cache invalidation',
                               preview_source((REPO/name).read_text())==preview_source(self.baseline_file(name).decode()))
                elif Path(name).name=='menu.c':
                    self.check('menu exact except two tested pure presentation rewrites',
                               menu_source((REPO/name).read_text())==menu_source(self.baseline_file(name).decode()))
                else:self.check('protected gameplay source exact '+name,(REPO/name).read_bytes()==self.baseline_file(name))
        # The optimized rendering code is below these logical behavior regions.
        for file,delimiter in [('enemy.c','static void knight_draw_sword'),
                               ('player.c','static void prepare_canopy_visibility'),
                               ('actor.c','void actor_draw'),
                               ('objects.c','void objects_draw_hand')]:
            before=self.baseline_file('bartgame/src/'+file).decode().split(delimiter)[0]
            after=(GAME/'src'/file).read_text().split(delimiter)[0]
            self.check('unchanged logical behavior prefix '+file,logical_source(before)==logical_source(after))
        self.check('all generated numeric IDs/contracts exact',self.a.defs==self.b.defs)
        self.check('all authored array families retained',set(self.a.sections)==set(self.b.sections))
        for name in sorted(set(self.a.sections)&set(self.b.sections)-POINTERS):
            self.check('linked native payload exact '+name,self.a.array(name)==self.b.array(name))
        self.check('all36 sprite sheet IDs retained',self.a.sheet_ids==self.b.sheet_ids)
        for name in sorted(self.a.sheet_ids):self.check('resolved native sheet exact '+name,self.a.sheet(name)==self.b.sheet(name))
        for name in ('sewer','forest','myst'):
            self.check('resolved full terrain/animation set exact '+name,self.a.tileset(name)==self.b.tileset(name))
        self.check('production ROM excludes development cycle-profiler data',
                   'gPerfSequence' not in self.b.symbols and 'gPerfCycles' not in self.b.symbols)

    def external(self,name,command,report=None,expected=None):
        log=self.out/(name+'.log')
        with log.open('w') as f:
            run=subprocess.run(command,cwd=GAME,stdout=f,stderr=subprocess.STDOUT,text=True)
        row=dict(name=name,returncode=run.returncode,log=log.name)
        self.check(name+' command succeeds',run.returncode==0)
        if report:
            path=Path(report)
            self.check(name+' report exists',path.exists())
            if path.exists():
                data=json.loads(path.read_text());row.update(report=str(path.relative_to(self.out)),report_sha256=SHA(path.read_bytes()),passed=data.get('passed'),total=data.get('total'))
                self.check(name+' all reported checks pass',data.get('passed')==data.get('total') and not data.get('error') and not data.get('failures'),dict(passed=data.get('passed'),total=data.get('total')))
                self.check(name+' uses exact qualified ROM',data['rom_sha256']==SHA(self.b.rom))
                if expected:self.check(name+' expected test coverage',data['total']>=expected,data['total'])
        else:
            text=log.read_text();found=re.search(r'RESULT\s+(PASS|FAIL)\s+(\d+)\s*/\s*(\d+)',text)
            self.check(name+' final status/count passes',bool(found) and found[1]=='PASS' and found[2]==found[3] and not re.search(r'^FAIL\b',text,re.M))
            if found:row.update(passed=int(found[2]),total=int(found[3]))
        self.suites.append(row)

    def run_existing(self,name,args):
        # Adapt original probe CLI defaults to this immutable bundle. Explicit
        # legacy ROM args, when present, still pass through unchanged.
        shim='''import sys,runpy
from pathlib import Path
sys.path.insert(0,'tools')
import probe as P
P.ROM=sys.argv[1];P.MAP=sys.argv[2];P._syms=None
old=P.boot
def boot(*args,**kw):
    if not args and 'rom' not in kw:kw['rom']=P.ROM
    return old(*args,**kw)
P.boot=boot
script=sys.argv[3];sys.argv=[script]+sys.argv[4:]
runpy.run_path(script,run_name='__main__')
'''
        command=[sys.executable,'-c',shim,str(self.after/'bartgame.gba'),str(self.after/'bartgame.map'),'tools/'+name+'.py']+args
        self.external(name,command)

    def isolated_views(self):
        """Actual PPU comparisons at explicit, matching semantic state.

        The existing review hook freezes the clock/camera and suppresses HUD.
        Nonplayer actors are removed to isolate tree/water/glitter/body depth.
        No VRAM, palette, rendered pixel or tile/collision bytes are written.
        """
        import probe as P
        import critical_path as C
        import bloom_probe as B
        import lift_probe as L

        def read(c,at,n):return bytes(P.r8(c,at+i) for i in range(n))
        def write32(c,at,value):P.w16(c,at,value&65535);P.w16(c,at+2,value>>16)
        cases=(('healthy',0xB4A7,16),('mixed',0xB4A7,0),('pond',0xB4A7,15),('deep',6,4))
        cameras=((0,0),(136,112),(272,224));clocks=(256,288)
        images={};metadata={};positions={};guarded=0;native_rows=[]
        for phase,bundle,rom in (('before',self.before,self.a),('after',self.after,self.b)):
            P.MAP=str(bundle/'bartgame.map');P._syms=None
            C.mt=lambda name:rom.defs['MT_'+name]
            for name,seed,cell in cases:
                c=P.boot(rom=str(bundle/'bartgame.gba'),seed=seed);C.dismiss(c,1000)
                P.enter_forest(c);C.dismiss(c,1000)
                world=C.world(c);L.warp(c,cell,next(i for i,v in enumerate(world['cells'][cell]['gate']) if v))
                C.dismiss(c,1000)
                room=P.sym('gRoom');raw=read(c,room,10242)
                if phase=='before':metadata[name]=SHA(raw)
                else:self.check(name+' isolated room semantic geometry exact',SHA(raw)==metadata[name])
                # Isolate actors, never their pictures or existing floor art.
                for i in range(1,96):P.w8(c,P.sym('gActors')+i*64,0)
                P.w8(c,P.sym('gTbActive'),0)
                actor=P.sym('gActors');pl=P.sym('gPl')
                for off in (2,3,4,5,28,29,31):P.w8(c,actor+off,0)
                P.w8(c,actor+6,16);P.w8(c,actor+7,2)
                for off in (16,18,20,22,24):P.w16(c,actor+off,0)
                for off in (9,10,11,18,19,20,21,22,23,24,25,26,28,29,31,32,33,34):P.w8(c,pl+off,0)
                for key in ('sWalkTimer','sUseItem','sUseTimer','sUseLength'):P.w8(c,B.static_symbol(key),0)
                write32(c,P.sym('gGame')+8,720)
                P.w8(c,P.sym('gForestReviewEnabled'),1)
                atlas=read(c,0x06000000,32768);mapping=read(c,0x0600C000,8192)
                solid=raw[4098:8194]
                def ink(wx,wy):
                    if not(0<=wx<512 and 0<=wy<384):return 0
                    tx,ty=wx//8,wy//8
                    at=(ty//32)*4096+(tx//32)*2048+((ty%32)*32+tx%32)*2
                    e=struct.unpack_from('<H',mapping,at)[0];x,y=wx&7,wy&7
                    if e&0x400:x=7-x
                    if e&0x800:y=7-y
                    return atlas[(e&1023)*32+y*4+x//2]>>((x&1)*4)&15
                for camera in cameras:
                    key=(name,camera)
                    if phase=='before':
                        spots=[]
                        for y in range(2,raw[1]-2):
                            for x in range(2,raw[0]-2):
                                px,py=x*16+8,y*16+14
                                if not(camera[0]+16<=px<camera[0]+224 and camera[1]+32<=py<camera[1]+152):continue
                                if any(solid[(yy>>3)*64+(xx>>3)] for xx,yy in ((px-5,py-8),(px+4,py-8),(px-5,py-1),(px+4,py-1))):continue
                                mt=struct.unpack_from('<H',raw,2+(y*32+x)*2)[0]
                                if mt==65535 or P.r8(c,P.sym('metatile_type')+mt)!=rom.defs['TT_FLOOR']:continue
                                cover=sum(bool(ink(xx,yy)) for yy in range(py-24,py-3,2) for xx in range(px-8,px+8,2))
                                distance=abs(px-camera[0]-120)+abs(py-camera[1]-96)
                                spots.append((-bool(cover),-cover,distance,px,py))
                        if not spots:
                            # A dense corner can contain no playable floor at
                            # all. Keep Bloom on real floor even when it lies
                            # outside that particular terrain camera view.
                            for y in range(2,raw[1]-2):
                                for x in range(2,raw[0]-2):
                                    px,py=x*16+8,y*16+14
                                    if any(solid[(yy>>3)*64+(xx>>3)] for xx,yy in ((px-5,py-8),(px+4,py-8),(px-5,py-1),(px+4,py-1))):continue
                                    mt=struct.unpack_from('<H',raw,2+(y*32+x)*2)[0]
                                    if mt==65535 or P.r8(c,P.sym('metatile_type')+mt)!=rom.defs['TT_FLOOR']:continue
                                    distance=abs(px-camera[0]-120)+abs(py-camera[1]-96)
                                    spots.append((0,0,distance,px,py))
                        assert spots,(name,camera,'no actual safe floor anywhere')
                        *_,px,py=min(spots);positions[key]=(px,py)
                    px,py=positions[key]
                    write32(c,actor+8,px<<16);write32(c,actor+12,py<<16)
                    P.w16(c,pl+14,px);P.w16(c,pl+16,py)
                    for clock in clocks:
                        P.w16(c,P.sym('gForestReviewCamera'),camera[0]);P.w16(c,P.sym('gForestReviewCamera')+2,camera[1])
                        write32(c,P.sym('gForestReviewClock'),clock)
                        for _ in range(6):write32(c,P.sym('gFrame'),clock-1);P.run(c,1)
                        image=c.bg_video.to_pil().convert('RGB').copy()
                        folder=self.out/'isolated-native'/phase;folder.mkdir(parents=True,exist_ok=True)
                        file=folder/('%s-%03d-%03d-%03d.png'%(name,*camera,clock));image.save(file)
                        row=dict(phase=phase,room=name,seed=hex(seed),cell=cell,camera=camera,clock=clock,
                                 player=(px,py),file=str(file.relative_to(self.out)),sha256=SHA(file.read_bytes()),
                                 RGB_sha256=SHA(image.tobytes()),guard=[P.r16(c,P.sym('gForestV3Visibility')+i*2)&65535 for i in range(12)])
                        native_rows.append(row);guarded+=bool(row['guard'][0])
                        index=(name,camera,clock)
                        if phase=='before':images[index]=image.tobytes()
                        else:self.check('%s native camera%d,%d clock%d exact'%(name,*camera,clock),images[index]==image.tobytes())
        self.check('isolated native comparison includes canopy visibility guard',guarded>0,guarded)
        (self.out/'isolated-native.json').write_text(json.dumps(dict(
            method='Actual frozen-camera PPU views, actor/clock/pose isolation fixtures. No VRAM, palette, framebuffer or terrain injection.',
            cases=native_rows),indent=2)+'\n')

    def run(self):
        self.scope()
        if not self.args.scope_only:
            self.isolated_views()
            hud=self.out/'hud';runtime=self.out/'runtime'
            self.external('hud',[sys.executable,'tools/hud_gilt_review.py','--bundle',str(self.after),'--out',str(hud),'--phase','after'],hud/'report.json',290)
            self.external('runtime',[sys.executable,'tools/forest_cohesion_runtime.py','--bundle',str(self.after),'--out',str(runtime)],runtime/'report.json',80)
            for name,args in [('save_probe',[]),('quest_probe',['--seed','0xB4A7']),
                              ('pocket_probe',['--seed','0xB4A7']),('revisit_probe',[])]:
                self.run_existing(name,args)
        report=dict(method=__doc__,baseline_commit=BASELINE,
                    source_commit=(self.after/'source-commit.txt').read_text().strip(),
                    before_rom_sha256=SHA(self.a.rom),rom_sha256=SHA(self.b.rom),
                    tool_sha256=SHA(Path(__file__).read_bytes()),
                    passed=sum(row['passed'] for row in self.checks),total=len(self.checks),
                    checks=self.checks,suites=self.suites,
                    scope_only=self.args.scope_only)
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True)
        return int(report['passed']!=report['total'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',required=True);ap.add_argument('--after',required=True)
    ap.add_argument('--out',required=True);ap.add_argument('--scope-only',action='store_true')
    return Regression(ap.parse_args()).run()

if __name__=='__main__':raise SystemExit(main())
