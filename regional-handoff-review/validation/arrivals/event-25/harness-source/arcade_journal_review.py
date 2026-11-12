#!/usr/bin/env python3
"""Qualify the production enemy/music/arcade ROM through actual mGBA execution.

Native framebuffers are untouched. Navigation, player positions/facing, health,
inventory, private serialized SRAM profiles and the existing developer enemy
spawn request are disclosed fixtures. Enemy HP, AI state, timers, poses and
facing are never assigned. Terrain, palettes, OAM and VRAM are never written.
Catalogue-coverage fixtures are separate from tests of genuine discovery.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import traceback
from types import SimpleNamespace

from PIL import Image, ImageSequence
import mgba.core
import mgba.image
import probe as P
import bloom_probe as B
import critical_path as C
from sewer_concept_audit import NativeRom
from sewer_concept_review import safe, gif_durations
from bloom_suite_gallery import write_gif

SHA=lambda b:hashlib.sha256(b).hexdigest()
SRAM=0x0e000000
PROFILE=0x7ec0
PREFS=0x7f00
JI_COUNT=24
EN_COUNT=9
KEYS=('UP','RIGHT','DOWN','LEFT')
DXY=((0,-1),(1,0),(0,1),(-1,0))


def signed(x,bits=16):
    return x-(1<<bits) if x&(1<<(bits-1)) else x


def bytes_at(c,at,n):
    return bytes(c.memory.u8[at+i] for i in range(n))


def w32(c,at,value):
    P.w16(c,at,value&65535);P.w16(c,at+2,(value>>16)&65535)


def fnv(data):
    value=2166136261
    for b in data:value=((value^b)*16777619)&0xffffffff
    return value


def profile(items,enemies,generation=1):
    data=struct.pack('<IHHIIHHII',0x314e524a,1,32,generation,items,enemies,0,0,0)
    return data+struct.pack('<I',fnv(data))


def preferences(style,palette):
    data=struct.pack('<IBBBB',0x4f545242,1,style,palette,0)
    return data+struct.pack('<I',fnv(data))


class Review:
    def __init__(self,args):
        self.args=args;self.bundle=Path(args.bundle).resolve();self.out=Path(args.out).resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        self.native=NativeRom(self.bundle)
        self.defs=B.configure(SimpleNamespace(map=str(self.bundle/'bartgame.map'),assets_header=str(self.bundle/'assets.h')))
        P.ROM=str(self.bundle/'bartgame.gba')
        self.original_boot=P.boot
        P.boot=lambda **kwargs:self.original_boot(**dict({'rom':P.ROM},**kwargs))
        C.mt=lambda name:self.defs['MT_'+name]
        output=subprocess.check_output(['arm-none-eabi-nm','-n',str(self.bundle/'bartgame.elf')],text=True)
        self.syms={name:int(at,16) for at,name in re.findall(r'^([0-9a-fA-F]{8})\s+\w\s+(\S+)\s*$',output,re.M)}
        self.checks=[];self.media=[];self.census=[];self.motion=[];self.fixtures=[];self.errors=[]
        self.rom_sha=SHA(self.native.rom);self.sram_evidence=None;self.cabinet_snapshot=None
        self.check('ordinary production build',self.defs.get('BART_ENEMY_LAB')==0)

    def at(self,name):
        return self.syms[name]

    def check(self,name,passed,detail=None):
        self.checks.append(dict(name=name,passed=bool(passed),detail=detail))
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)
        return bool(passed)

    def fresh(self,start=True,sram=None,seed=0xb4a7):
        c=mgba.core.load_path(P.ROM);c.bg_video=mgba.image.Image(240,160)
        c.set_video_buffer(c.bg_video);c.reset()
        # This is an isolated in-memory emulator SRAM fixture, not a disk save.
        for i in range(32768):P.w8(c,SRAM+i,0xff)
        if sram:
            for offset,data in sram.items():
                for i,b in enumerate(data):P.w8(c,SRAM+offset+i,b)
        P.run(c,45)
        if start:
            w32(c,self.at('gSeedOverride'),seed);P.press(c,'START',2,4)
            ready=None
            for _ in range(2200):
                if P.r8(c,self.at('gTbActive')):P.press(c,'A',2,6)
                else:P.run(c,4)
                if C.gstate(c)==1 and P.r8(c,self.at('gActors'))==1 and not P.r8(c,self.at('gTbActive')):
                    now=P.r32(c,self.at('gGame')+8)
                    if ready is None:ready=now
                    if now-ready>=3:break
                else:ready=None
            else:raise AssertionError('new run did not finish real introduction')
        return c

    def run(self,c,n=1,keys=(),heal=False,record=None):
        c.clear_keys(*range(10));c.set_keys(*(P.key(c,k) for k in keys))
        for _ in range(n):
            if heal:P.w16(c,self.at('gPl'),80)
            c.run_frame()
            if record is not None:record.append(c.bg_video.to_pil().convert('RGB').copy())
        c.clear_keys(*range(10))

    def press(self,c,key,n=2,release=6,record=None):
        self.run(c,n,(key,),record=record);self.run(c,release,record=record)

    def wait(self,c,pred,limit=1200,heal=False,record=None):
        for _ in range(limit):
            if pred():return True
            self.run(c,heal=heal,record=record)
        return bool(pred())

    def shot(self,c,name):
        path=self.out/(name+'.png');P.snap(c,str(path))
        self.media.append(dict(file=path.name,sha256=SHA(path.read_bytes()),size=[240,160],kind='untouched native mGBA framebuffer'))

    def clip(self,name,frames,step=4):
        folder=self.out/name;folder.mkdir(exist_ok=True)
        sampled=frames[::step]
        for tick,img in enumerate(sampled):
            file=folder/('native-%04d.png'%(tick*step));img.save(file)
        gif=folder/'motion.gif';durations=gif_durations(len(frames),step)
        meta=write_gif(sampled,durations,gif)
        decoded=[]
        for img in ImageSequence.Iterator(Image.open(gif)):
            decoded.append((img.convert('RGB').copy(),img.info.get('duration',0)))
        i=t=0;exact=True
        for img,d in decoded:
            while d and i<len(sampled):
                exact &= img.tobytes()==sampled[i].tobytes()
                take=min(d,durations[i]-t);t+=take;d-=take
                if t==durations[i]:i+=1;t=0
        self.check(name+' GIF keeps exact native pixels/timing',exact and i==len(sampled))
        self.media.append(dict(file=str(gif.relative_to(self.out)),sha256=SHA(gif.read_bytes()),kind='actual native mGBA sampled playback',**meta))

    def masks(self,c):
        return (P.r32(c,self.at('gJournalItems')),P.r16(c,self.at('gJournalEnemies'))&65535)

    def actor(self,c,i):
        at=self.at('gActors')+i*64
        return dict(index=i,kind=P.r8(c,at),type=P.r8(c,at+1),state=P.r8(c,at+2),sub=P.r8(c,at+3),timer=P.r8(c,at+4),
                    timer2=P.r8(c,at+5),direction=P.r8(c,at+6),facing=P.r8(c,at+7),
                    x=signed(P.r32(c,at+8),32)/65536,y=signed(P.r32(c,at+12),32)/65536,
                    hp=signed(P.r16(c,at+26)&65535),iframes=P.r8(c,at+28),kb=P.r8(c,at+29),flags=P.r8(c,at+31),
                    sheet=P.r8(c,at+36),frame=P.r8(c,at+37),tile=P.r16(c,at+44)&65535,palette=P.r8(c,at+46))

    def enemies(self,c):
        return [self.actor(c,i) for i in range(1,96) if P.r8(c,self.at('gActors')+i*64)==2]

    def position(self,c,i,x,y,facing=None):
        at=self.at('gActors')+i*64
        w32(c,at+8,round(x*65536));w32(c,at+12,round(y*65536))
        if i==0:
            P.w16(c,self.at('gPl')+14,int(x));P.w16(c,self.at('gPl')+16,int(y))
            if facing is not None:P.w8(c,at+7,facing);P.w8(c,at+6,facing*8)
        self.fixtures.append(dict(action='coordinate-only actor position',actor=i,position=[x,y],player_facing=facing))

    def warp(self,c,area,cell=0,side=0):
        C.dismiss(c,1200)
        for name,v in [('sNextArea',area),('sNextCell',cell),('sNextSide',side),('sTransPhase',0)]:P.w8(c,self.at(name),v)
        P.w8(c,self.at('gGame'),2)
        assert self.wait(c,lambda:C.gstate(c)==1 and C.area(c)==area and (area!=1 or C.cell(c)==cell),1800,heal=True),'room navigation did not complete'
        C.dismiss(c,1000);self.run(c,6,heal=True)
        self.fixtures.append(dict(action='existing room transition request',area=area,cell=cell,side=side))

    def cabinet(self,c,walk=True,record=None):
        assert C.area(c)==0 and P.r8(c,self.at('gCabinetActive')),'cabinet absent from real Drain'
        x=signed(P.r16(c,self.at('gCabinetX'))&65535);y=signed(P.r16(c,self.at('gCabinetY'))&65535)
        self.position(c,0,x,y+30,0);self.run(c,80)
        if walk:self.run(c,6,('UP',),record=record)
        self.run(c,24,record=record)
        self.cabinet_snapshot=self.world_preservation(c)
        self.press(c,'A',record=record)
        assert self.wait(c,lambda:C.gstate(c)==7,120,record=record),'ordinary A interaction did not open arcade'
        self.run(c,8,record=record)

    def world_preservation(self,c):
        return dict(terrain=SHA(bytes_at(c,self.at('gRoom')+2,4096)),
                    collision=SHA(bytes_at(c,self.at('gRoom')+4098,4096)),
                    preview_reserve=SHA(bytes_at(c,0x06010000+944*32,1024)),
                    portrait_palette=SHA(bytes_at(c,0x05000200+6*32,32)),
                    bg3_control=P.r16(c,0x0400000e)&65535,
                    bg3_scroll=bytes_at(c,self.at('gBgScroll')+12,4).hex())

    def arcade(self,c):
        return {n:P.r8(c,self.at('gArcade'+n)) for n in ['Page','Cursor','Top','Detail','Seen','PreviewTiles','PreviewFrame','PreviewSheet','PreviewSourcePalette']}

    def journal(self):
        c=self.fresh();initial=self.masks(c)
        self.check('new game records only starting tools and no unseen enemies',initial==(1|2|(1<<8),0),initial)
        before=bytes_at(c,SRAM+PROFILE,64)
        self.run(c,120)
        self.check('idle does not rewrite journal profile',bytes_at(c,SRAM+PROFILE,64)==before)
        self.shot(c,'01-drain-before-cabinet')
        frames=[];self.cabinet(c,record=frames)
        self.check('walking up and pressing A opens cabinet',C.gstate(c)==7)
        self.check('cabinet starts at known Sword entry',self.arcade(c)['Page']==0 and self.arcade(c)['Cursor']==0 and self.arcade(c)['Seen']==1,self.arcade(c))
        self.shot(c,'02-journal-known-sword')
        actor_before=bytes_at(c,self.at('gActors'),96*64)
        logic=P.r32(c,self.at('gGame')+8);video=P.r32(c,self.at('gFrame'))
        self.run(c,90,record=frames)
        self.check('journal freezes actors and world run clock',bytes_at(c,self.at('gActors'),96*64)==actor_before and P.r32(c,self.at('gGame')+8)==logic)
        self.check('journal continues video timing',P.r32(c,self.at('gFrame'))-video>=90)
        self.press(c,'DOWN',record=frames);self.press(c,'DOWN',record=frames)
        self.check('unseen upgraded shield is masked with no preview',self.arcade(c)['Cursor']==2 and not self.arcade(c)['Seen'] and self.arcade(c)['PreviewTiles']==0,self.arcade(c))
        self.shot(c,'03-journal-unknown-item')
        self.press(c,'A',record=frames)
        self.check('unknown detail remains unknown',self.arcade(c)['Detail']==1 and not self.arcade(c)['Seen'] and not self.arcade(c)['PreviewTiles'],self.arcade(c))
        self.press(c,'B',record=frames);self.check('B returns notes to browser',self.arcade(c)['Detail']==0)
        self.press(c,'R',record=frames)
        self.check('R selects enemy catalogue',self.arcade(c)['Page']==1)
        self.check('unencountered enemy does not reveal sprite',not self.arcade(c)['Seen'] and not self.arcade(c)['PreviewTiles'])
        self.shot(c,'04-journal-unknown-enemy')
        self.press(c,'L',record=frames);self.press(c,'UP',record=frames);self.press(c,'UP',record=frames);self.press(c,'A',record=frames)
        self.check('known entry has readable full notes mode',self.arcade(c)['Detail']==1 and self.arcade(c)['Seen']==1,self.arcade(c))
        self.shot(c,'05-journal-known-notes')
        self.press(c,'START',record=frames)
        self.check('Start exits notes to unchanged live Drain',C.gstate(c)==1 and C.area(c)==0)
        self.check('leaving journal restores terrain collision preview VRAM palette and BG3',self.world_preservation(c)==self.cabinet_snapshot,dict(before=self.cabinet_snapshot,after=self.world_preservation(c)))
        self.run(c,16,record=frames);self.shot(c,'06-drain-after-journal')
        self.clip('cabinet-and-journal',frames)
        self.check('viewing journal invents no discoveries',self.masks(c)==initial,self.masks(c))
        self.sram_evidence=bytes_at(c,SRAM,32768)

    def discovery_profiles(self):
        # Valid serialized profile inputs exercise decoder/recovery and full
        # catalogue UI. These masks are not claimed as earned exploration.
        items=(1<<JI_COUNT)-1;enemies=(1<<EN_COUNT)-1
        current=profile(items,enemies,8);older=profile(3,1,7)
        c=self.fresh(start=False,sram={PROFILE:older+current,PREFS:preferences(2,1)})
        self.check('newest complete discovery generation restored',self.masks(c)==(items,enemies),self.masks(c))
        self.check('journal profile preserves independent appearance preferences',P.r8(c,self.at('gAppearanceStyle'))==2 and P.r8(c,self.at('gAppearancePalette'))==1)
        bad=bytearray(current);bad[17]^=1
        d=self.fresh(start=False,sram={PROFILE:older+bad,PREFS:preferences(1,2)})
        self.check('torn/corrupt newest generation falls back to older',self.masks(d)==(3,1),self.masks(d))
        bad2=bytearray(older);bad2[28]^=1
        e=self.fresh(start=False,sram={PROFILE:bad2+bad})
        self.check('two corrupt discovery records fail closed',self.masks(e)==(0,0),self.masks(e))
        self.fixtures.append(dict(action='private serialized profile',purpose='decoder and catalogue coverage',all_items=items,all_enemies=enemies))
        c=self.fresh(sram={PROFILE:older+current,PREFS:preferences(2,1)})
        self.cabinet(c);self.shot(c,'07-ivory-shape-moss-palette')
        visited=[]
        for tab,count in [(0,JI_COUNT),(1,EN_COUNT)]:
            if self.arcade(c)['Page']!=tab:self.press(c,'R')
            for idx in range(count):
                # Opening a tab restores that tab's own selection; rewind with
                # ordinary controls, never by assigning the UI's cursor.
                cursor=self.arcade(c)['Cursor']
                for _ in range((idx-cursor)%count):self.press(c,'DOWN')
                self.run(c,4)
                st=self.arcade(c);visited.append(st)
                self.check(('item' if not tab else 'enemy')+'%02d seen native preview'%idx,st['Cursor']==idx and st['Seen'] and st['PreviewTiles']>0,st)
                sid=st['PreviewSheet'];frame=st['PreviewFrame']
                sheetname=next(name for name,i in self.native.sheet_ids.items() if i==sid)
                meta,payload=self.native.sheet(sheetname);size=meta['frame_tiles']*32
                self.check(('item' if not tab else 'enemy')+'%02d preview uses exact native pixels'%idx,bytes_at(c,0x06010000+944*32,size)==payload[frame*size:(frame+1)*size])
                expected_pal=bytes_at(c,self.at('pal_obj')+st['PreviewSourcePalette']*32,32)
                self.check(('item' if not tab else 'enemy')+'%02d preview uses native material palette'%idx,bytes_at(c,0x05000200+6*32,32)==expected_pal)
                if idx in (0,count-1):self.shot(c,('08-items' if not tab else '09-enemies')+'-%02d'%idx)
        self.press(c,'B');self.run(c,6)
        self.check('all catalogue entries browse without out-of-range UI',len(visited)==JI_COUNT+EN_COUNT and C.gstate(c)==1)
        before_mask=self.masks(c);before_prefs=bytes_at(c,SRAM+PREFS,12)
        # Exercise actual death/save; only the player's death state/timer are
        # fixtures. Enemy state and loot flags are never fabricated.
        P.w8(c,self.at('gActors')+2,7);P.w8(c,self.at('gPl')+24,121);self.run(c,10)
        self.check('actual run save preserves discovery masks',self.masks(c)==before_mask)
        self.check('actual run save leaves appearance record exact',bytes_at(c,SRAM+PREFS,12)==before_prefs)
        ram=bytes_at(c,SRAM,32768)
        fresh=self.fresh(start=False,sram={0:ram})
        self.check('discoveries survive emulator reboot',self.masks(fresh)==before_mask)
        self.press(fresh,'START');self.wait(fresh,lambda:C.gstate(fresh)==1,1500);C.dismiss(fresh,1000)
        self.check('Continue retains run and discovered catalogue',C.area(fresh)==0 and self.masks(fresh)==before_mask)
        self.sram_evidence=ram
        newrun=self.fresh(start=False,sram={0:ram})
        self.press(newrun,'DOWN');self.press(newrun,'START')
        self.wait(newrun,lambda:C.gstate(newrun)==1,1500);C.dismiss(newrun,1000)
        self.check('New Game erases only run progress and keeps collection',C.area(newrun)==0 and self.masks(newrun)==before_mask and P.r16(newrun,self.at('gPl')+2)==24)
        self.check('New Game keeps independent appearance settings',P.r8(newrun,self.at('gAppearanceStyle'))==2 and P.r8(newrun,self.at('gAppearancePalette'))==1)
        for style,palette in ((0,0),(1,2),(2,1)):
            styled=self.fresh(sram={PROFILE:older+current,PREFS:preferences(style,palette)})
            self.cabinet(styled)
            expected=self.native.array('appearance_palettes')[palette*32:(palette+1)*32]
            self.check('journal style%d uses independently selected palette%d'%(style,palette),P.r8(styled,self.at('gAppearanceStyle'))==style and bytes_at(styled,0x05000000+self.defs['PAL_SLOT_MENU']*32,32)==expected)
            self.shot(styled,'style-%d-palette-%d'%(style,palette))
            self.press(styled,'B');self.run(styled,8)
            self.check('journal style%d restores native world reserve'%style,self.world_preservation(styled)==self.cabinet_snapshot)

    def stream_before(self,c):
        result=[]
        if 'sStream' not in self.syms:return result
        base=self.at('sStream');count=P.r8(c,self.at('sStreamCount'))
        for i in range(count):
            tile=P.r16(c,base+i*4)&65535;owner=P.r8(c,base+i*4+2);frame=P.r8(c,base+i*4+3)
            if owner and frame!=255:
                a=self.actor(c,owner)
                if a['kind']==2 and a['type']>=6:result.append((a['type'],a['sheet'],tile,frame&127))
        return result

    def stream_check(self,c,expected):
        matches=[]
        for typ,sid,tile,frame in expected:
            name=next(name for name,i in self.native.sheet_ids.items() if i==sid)
            meta,payload=self.native.sheet(name);size=meta['frame_tiles']*32
            actual=bytes_at(c,0x06010000+tile*32,size)
            matches.append((typ,frame,actual==payload[frame*size:(frame+1)*size]))
        return matches

    def natural(self):
        c=self.fresh();P.w16(c,self.at('gPl')+2,80)
        world=C.world(c);counts=Counter();poses={6:set(),7:set(),8:set()};seen_vram=Counter();all_exact=True
        for cell in range(25):
            self.warp(c,1,cell)
            original=self.enemies(c);counts.update(a['type'] for a in original)
            target=next((a for a in original if a['type']>=6),None)
            if target:
                # Keep generated AI/HP/terrain. A nearby real safe floor places
                # the encounter in view through ordinary camera easing.
                points=[(target['x']+dx,target['y']+dy) for dx,dy in ((0,40),(40,0),(-40,0),(0,-40),(0,24))]
                point=next((p for p in points if safe(c,round(p[0]),round(p[1]))),None)
                if point:self.position(c,0,*map(round,point),0)
                self.run(c,75,heal=True)
            start=P.r32(c,self.at('gGame')+8);frames=[];deltas=[];alloc=[];states=[]
            for tick in range(120):
                expected=self.stream_before(c);before=P.r32(c,self.at('gGame')+8)
                self.run(c,heal=True,record=frames if target and cell%3==0 else None)
                deltas.append(P.r32(c,self.at('gGame')+8)-before)
                alloc.append(P.r16(c,self.at('sNextTile'))&65535)
                for typ,frame,ok in self.stream_check(c,expected):
                    seen_vram[typ]+=1;poses[typ].add(frame);all_exact &= ok
                states.extend((a['type'],a['state']) for a in self.enemies(c) if a['type']>=6)
            row=dict(cell=cell,stage=world['cells'][cell]['stage'],roster=dict(Counter(a['type'] for a in original)),updates=P.r32(c,self.at('gGame')+8)-start,video_frames=120,deltas=dict(Counter(deltas)),peak_world_tile=max(alloc),states=sorted(set(states)))
            self.census.append(row)
            if frames:self.clip('natural-cell-%02d'%cell,frames)
        self.check('all three new enemies occur in natural generated rosters',all(counts[t]>0 for t in (6,7,8)),dict(counts))
        self.check('all three production streams have genuine native ROM pixels',all(seen_vram[t]>=10 for t in (6,7,8)) and all_exact,dict(samples=dict(seen_vram),poses={str(k):sorted(v) for k,v in poses.items()}))
        self.check('all25 natural-room samples stay within world OBJ budget',len(self.census)==25 and all(r['peak_world_tile']<=876 for r in self.census),max(r['peak_world_tile'] for r in self.census))
        self.check('all25 natural-room samples retain sampled full logic cadence',all(r['updates']==r['video_frames'] and r['deltas']=={1:120} for r in self.census),[(r['cell'],r['updates'],r['deltas']) for r in self.census])
        self.check('naturally submitted new enemy bodies become discoveries',all(self.masks(c)[1]&(1<<t) for t in (6,7,8)),self.masks(c))
        earned=self.masks(c);ram=bytes_at(c,SRAM,32768)
        returned=self.fresh(sram={0:ram})
        self.check('genuinely encountered enemy discoveries persist into a new run',self.masks(returned)==earned,dict(before=earned,after=self.masks(returned)))
        self.cabinet(returned);self.press(returned,'R');self.shot(returned,'10-earned-enemy-journal')
        self.motion.append(dict(natural_roster_counts=dict(counts),stream_samples=dict(seen_vram),poses={str(k):sorted(v) for k,v in poses.items()}))

    def music(self):
        if 'gOriginalMusicBgm' not in self.syms:
            self.check('original soundtrack diagnostics available',False);return
        c=self.fresh(start=False)
        self.run(c,8)
        def audio():
            return {name:P.r32(c,self.at('gOriginalMusic'+name)) if name in ('Samples','Loops','DmaOffset') else P.r16(c,self.at('gOriginalMusic'+name))&65535 for name in ('Bgm','Track','Samples','Loops','DmaOffset')}
        title=audio();self.check('title plays original Dawn Overture',title['Bgm']==4 and title['Track']==26,title)
        before=title['Samples'];first_video=P.r32(c,self.at('gFrame'));self.run(c,120);after=audio();video_delta=P.r32(c,self.at('gFrame'))-first_video
        observed=after['Samples']-before;expected_samples=video_delta*280896/512
        self.check('original audio advances through real sample clock',after['Samples']>before,dict(before=title,after=after))
        w32(c,self.at('gSeedOverride'),0xb4a7);self.press(c,'START');self.wait(c,lambda:C.gstate(c)==1,1600);C.dismiss(c,1200);self.run(c,12)
        sewer=audio();self.check('Drain plays original Undertow Circuit',sewer['Bgm']==1 and sewer['Track']==1,sewer)
        self.warp(c,1,C.world(c)['entry']);self.run(c,10)
        forest=audio();self.check('forest plays original Verdant Afterimage',forest['Bgm']==2 and forest['Track']==2,forest)
        before=forest['Samples'];self.press(c,'B');self.run(c,14)
        after=audio();self.check('real sword sound leaves original music running',after['Bgm']==2 and after['Samples']>before,after)
        self.check('FIFO music actual sample clock is32768Hz',abs(observed-expected_samples)<16,dict(samples=observed,expected=expected_samples,video_frames=video_delta))
        self.check('FIFO music timers0and1 have native audio/cascade control',(P.r16(c,0x04000102)&0x0087)==0x0080 and (P.r16(c,0x04000106)&0x0087)==0x0084)
        self.check('FIFO music DMA1 is enabled',(P.r16(c,0x040000c6)&0x8000)!=0)
        self.motion.append(dict(original_music=dict(title=title,sewer=sewer,forest=forest,after_sword=after)))

    def save(self):
        # Existing comprehensive v1/v2 migration helper runs against this exact
        # ROM/map. Its serialization fixtures and checks are documented there.
        import contextlib,io,save_probe
        output=io.StringIO();old=sys.argv
        try:
            sys.argv=['save_probe']
            with contextlib.redirect_stdout(output):save_probe.main()
            self.check('legacyv1/v2 run migration suite passes',True,output.getvalue())
        except Exception:
            self.check('legacyv1/v2 run migration suite passes',False,traceback.format_exc())
        finally:sys.argv=old
        (self.out/'save-migration.txt').write_text(output.getvalue())

    def write(self):
        source=(self.bundle/'source-commit.txt').read_text().strip() if (self.bundle/'source-commit.txt').exists() else 'unfrozen'
        report=dict(method=__doc__,emulator='mGBA0.10.5',source_commit=source,rom_sha256=self.rom_sha,tool_sha256=SHA(Path(__file__).read_bytes()),
                    checks=self.checks,passed=sum(c['passed'] for c in self.checks),total=len(self.checks),media=self.media,
                    fixtures=self.fixtures,natural_census=self.census,motion=self.motion,errors=self.errors)
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        return report

    def execute(self):
        for name in self.args.suites.split(','):
            try:getattr(self,name)()
            except Exception:
                self.errors.append(dict(suite=name,error=traceback.format_exc()));self.check(name+' scenario completes',False,traceback.format_exc())
            self.write()
        r=self.write();print('RESULT',r['passed'],'/',r['total'],flush=True)
        return int(r['passed']!=r['total'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--suites',default='journal,discovery_profiles,natural,music,save')
    return Review(parser.parse_args()).execute()


if __name__=='__main__':raise SystemExit(main())
