#!/usr/bin/env python3
"""Qualify original music through real mGBA gameplay contexts and audio output.

Navigation requests, player health restoration and the existing sword-assisted
boss fight are disclosed fixtures. Music state, clocks, PCM, sound registers,
DMA and frame counters are never assigned. Captures are unprocessed emulator
16-bit stereo output. The source comparison uses the actual imported ROM PCM,
not synthesis of a replacement melody. Full physical-frame samples establish
sample-clock and loop behavior even while normal logic/modal menus are busy.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import traceback
import wave

import numpy as np
import mgba.core
import mgba.image
import mgba.log
from mgba._pylib import ffi
import probe as P
import critical_path as C
import bloom_probe as B
import lift_probe as L

SHA=lambda x:hashlib.sha256(x).hexdigest()
ROLES={1:'sewer',2:'forest',3:'boss',4:'title',5:'win'}


class Review:
    def __init__(self,args):
        self.args=args;self.bundle=Path(args.bundle).resolve();self.out=Path(args.out).resolve();self.out.mkdir(parents=True,exist_ok=True)
        P.MAP=str(self.bundle/'bartgame.map');P._syms=None
        self.rom=(self.bundle/'bartgame.gba').read_bytes();self.rows=[];self.scenarios=[];self.fixtures=[
            'Seed0xb4a7 pinned before ordinary title Start; new emulator SRAM for this tool only.',
            'Forest/goal navigation uses existing transition request fields, bypassing travel/gates but retaining real generation, actors and music selection.',
            'Full-loop forest/boss recordings use the real pause menu to keep combat still; the menu input IRQ chains the audio heartbeat.',
            'Player health/invulnerability restoration and coordinate-only positioning accompany real sword inputs to obtain the Grail; enemy HP/state/timers remain live.',
            'No audio state, sample clock, source pointer, sound register, DMA register or framebuffer is injected. WAVs are raw mGBA output; PCM comparison resampling is diagnostic only.'
        ]
        self.manifest=json.loads((Path(__file__).resolve().parent.parent/'audio/original/manifest.json').read_text())
        self.tracks={t['bgm_id']:t for t in self.manifest['tracks']}
        self.buf=ffi.new('short[8192]')
        self.core=mgba.core.load_path(str(self.bundle/'bartgame.gba'));self.core.bg_video=mgba.image.Image(240,160);self.core.set_video_buffer(self.core.bg_video)
        self.core.set_audio_buffer_size(4096);self.audio=self.core.get_audio_channels();self.audio.set_rate(44100);self.core.reset()
        self.step(30)

    def check(self,name,ok,detail=None):
        self.rows.append(dict(name=name,passed=bool(ok),detail=detail));print(('PASS ' if ok else 'FAIL ')+name,flush=True)

    def diag(self):
        c=self.core
        return dict(bgm=P.r16(c,P.sym('gOriginalMusicBgm'))&65535,track=P.r16(c,P.sym('gOriginalMusicTrack'))&65535,
                    samples=P.r32(c,P.sym('gOriginalMusicSamples')),loops=P.r32(c,P.sym('gOriginalMusicLoops')),
                    dma_offset=P.r32(c,P.sym('gOriginalMusicDmaOffset')),frame=P.r32(c,P.sym('gFrame')),
                    game_state=C.gstate(c),run_frames=P.r32(c,P.sym('gGame')+8))

    def drain(self):
        data=bytearray()
        while self.audio.available:
            n=self.audio.read_into(self.buf,min(self.audio.available,4096));data.extend(ffi.buffer(self.buf,n*4))
        return data

    def step(self,n=1,keys=(),heal=False):
        self.core.clear_keys(*range(10));self.core.set_keys(*(P.key(self.core,k) for k in keys))
        for _ in range(n):
            if heal:P.w16(self.core,P.sym('gPl'),80)
            self.core.run_frame();self.drain()
        self.core.clear_keys(*range(10))

    def press(self,key,hold=2,release=12):
        self.step(hold,(key,),True);self.step(release,heal=True)

    def descriptor(self,bgm):
        c=self.core;at=P.sym('gOriginalSongs')+bgm*24
        return dict(pcm=P.r32(c,at),samples=P.r32(c,at+4),loop_sample=P.r32(c,at+8),
                    total_frames=P.r16(c,at+12)&65535,loop_frame=P.r16(c,at+14)&65535,source_id=P.r16(c,at+16)&65535)

    def asset_checks(self):
        for bgm,t in self.tracks.items():
            d=self.descriptor(bgm);off=d['pcm']-0x08000000;data=self.rom[off:off+t['pcm_bytes']]
            self.check(t['role']+' original track descriptor',d['samples']==t['sample_count'] and d['loop_sample']==t['loop_sample'] and d['source_id']==t['source_id'],d)
            self.check(t['role']+' complete ROM PCM matches source-import hash',SHA(data)==t['pcm_sha256'],SHA(data))
            n=d['samples'];loop=d['loop_sample'];tail=len(data)-n
            self.check(t['role']+' musical FIFO guard and ROM bounds',tail>=8192 and data[n:]==data[loop:loop+tail] and off+len(data)<=len(self.rom),tail)

    def start_game(self):
        c=self.core;P.w16(c,P.sym('gSeedOverride'),0xB4A7);P.w16(c,P.sym('gSeedOverride')+2,0)
        self.step(2,('START',));trace=[]
        for _ in range(2400):
            a=self.diag();self.step(1);b=self.diag();trace.append((a,b))
            if b['bgm']==1 and C.area(c)==0 and C.gstate(c)==1:break
        else:raise AssertionError('normal New Game did not reach Drain')
        busy=[(a,b) for a,b in trace if a['bgm']==b['bgm']==4 and a['run_frames']==b['run_frames'] and b['frame']>a['frame']]
        self.check('physical music sample clock survives busy New Game generation',bool(busy) and all(b['samples']>a['samples'] or b['loops']>a['loops'] for a,b in busy),dict(video_frames=len(trace),busy_intervals=len(busy)))
        try:pending=P.sym('gStartingDraft')
        except KeyError:pending=None
        for _ in range(600):
            if not P.r8(c,P.sym('gTbActive')) and not (pending and P.r8(c,pending)):break
            self.press('A',2,6)
        else:raise AssertionError('opening text/gift draft did not finish through actual input')
        self.step(120)
        self.check('real opening gift inputs finish before audio/SFX qualification',not P.r8(c,P.sym('gTbActive')) and not (pending and P.r8(c,pending)))

    def warp(self,cell):
        c=self.core
        if C.gstate(c)==4:self.press('START',2,20)
        for name,value in [('sNextArea',1),('sNextCell',cell),('sNextSide',2),('sTransPhase',0)]:P.w8(c,B.static_symbol(name),value)
        P.w8(c,P.sym('gGame'),2)
        for _ in range(2400):
            self.step(1,heal=True)
            if C.gstate(c)==1 and C.area(c)==1 and C.cell(c)==cell:break
        else:raise AssertionError('generated forest transition did not settle')
        self.step(30,heal=True)

    def menu(self):
        if C.gstate(self.core)!=4:self.press('START',2,20)
        self.check('real pause menu opens for clean music observation',C.gstate(self.core)==4)
        self.step(120,heal=True)
        self.check('period0 menu SFX ends while original music continues',P.r16(self.core,0x04000062)&0xF000==0 and self.diag()['bgm'] in (2,3),hex(P.r16(self.core,0x04000062)))

    @staticmethod
    def pcm_resample(data,rate=44100):
        raw=subprocess.check_output(['ffmpeg','-v','error','-f','s8','-ar','32768','-ac','1','-i','pipe:0','-ar',str(rate),'-f','f32le','pipe:1'],input=data)
        return np.frombuffer(raw,dtype='<f4')

    def correlate(self,observed,source):
        # Source is deliberately longer on both sides. Resolve lag at1/10 rate,
        # then inspect each original sample around that candidate.
        source=np.asarray(source,dtype='f8');observed=np.asarray(observed,dtype='f8');observed=observed-observed.mean()
        if len(source)<len(observed)+100:return dict(correlation=0,error='short expected source')
        subsource=source[::10];subobs=observed[::10]
        coarse=int(np.argmax(np.correlate(subsource,subobs,mode='valid')))*10
        best=(-2,None,None)
        for at in range(max(0,coarse-12),min(len(source)-len(observed)+1,coarse+13)):
            expected=source[at:at+len(observed)];expected=expected-expected.mean()
            den=float(np.sqrt(np.dot(expected,expected)*np.dot(observed,observed)))
            corr=float(np.dot(expected,observed)/den) if den else 0
            if corr>best[0]:best=(corr,at,float(np.sqrt(np.mean(expected*expected))))
        return dict(correlation=best[0],source_offset_44100=best[1],source_rms=best[2],observed_rms=float(np.sqrt(np.mean(observed*observed))))

    @staticmethod
    def wav(file,data):
        with wave.open(str(file),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(44100);f.writeframes(data)

    def capture(self,bgm):
        c=self.core;t=self.tracks[bgm];role=t['role'];d=self.descriptor(bgm)
        self.step(90,heal=True);self.audio.clear();initial=self.diag();base_loops=initial['loops'];frames=[];audio=bytearray();boundary=None;after_loop=0;maxdelta=0;errors=[]
        self.check(role+' natural game context selects original catalog track',initial['bgm']==bgm and initial['track']==t['source_id'],initial)
        if initial['bgm']!=bgm:raise AssertionError('wrong music context; do not qualify unrelated track')
        for i in range(t['source_first_pass_frames']+600):
            old=self.diag();c.run_frame();new=self.diag();start=len(audio)//4;audio.extend(self.drain())
            delta=new['samples']-old['samples']
            if new['loops']!=old['loops']:
                delta=new['samples']-d['loop_sample']+d['samples']-old['samples'];boundary=dict(frame=i,audio_sample=start,previous=old,current=new)
            maxdelta=max(maxdelta,delta)
            if not 530<=delta<=565:errors.append(dict(frame=i,delta=delta,old=old,new=new))
            if i%60==0 or new['loops']!=old['loops']:frames.append(dict(video_index=i,**new))
            if new['loops']>base_loops:
                after_loop+=1
                if after_loop>=180:break
        self.check(role+' actual Timer1 samples advance at32768Hz through every physical frame',not errors,dict(frames=i+1,max_sample_delta=maxdelta,bad_intervals=errors[:5]))
        end=self.diag();self.check(role+' real loop observed without clock injection',end['loops']>base_loops,boundary)
        self.check(role+' loop DMA points inside the correct original ROM stream',0<=end['dma_offset']<d['samples'] and end['dma_offset']>=d['loop_sample'],end)
        self.check(role+' DMA and hardware sample clocks remain enabled',P.r16(c,0x04000102)==0x80 and P.r16(c,0x04000106)==0x84 and P.r32(c,0x040000C4)&0x80000000,dict(timer0=P.r16(c,0x04000102),timer1=P.r16(c,0x04000106),dma1=hex(P.r32(c,0x040000C4))))
        samples=np.frombuffer(audio,dtype='<i2').reshape(-1,2);preview=samples[:44100*12]
        self.wav(self.out/(role+'-preview.wav'),preview.tobytes())
        rms=float(np.sqrt(np.mean(preview.astype('f8')**2)));peak=int(np.max(np.abs(preview.astype('i4'))))
        self.check(role+' actual audio is non-silent and unclipped',rms>100 and peak<32767,dict(rms16=rms,peak16=peak))
        self.check(role+' original mono mix routes equally to both speakers',np.array_equal(preview[:,0],preview[:,1]))
        pcm=self.rom[d['pcm']-0x08000000:d['pcm']-0x08000000+d['samples']]
        start=max(0,initial['samples']-8192);stop=min(len(pcm),initial['samples']+32768*12+8192)
        expected=self.pcm_resample(pcm[start:stop]);corr=self.correlate(preview.mean(axis=1)/32768,expected)
        self.check(role+' actual waveform matches imported original ROM PCM',corr['correlation']>0.94,corr)
        loopcorr=None
        if boundary:
            center=boundary['audio_sample'];a=max(0,center-44100);b=min(len(samples),center+44100)
            loop_audio=samples[a:b];self.wav(self.out/(role+'-loop.wav'),loop_audio.tobytes())
            pre=pcm[max(0,d['samples']-32768-8192):d['samples']]
            post=pcm[d['loop_sample']:d['loop_sample']+32768+8192]
            loopcorr=self.correlate(loop_audio.mean(axis=1)/32768,self.pcm_resample(pre+post))
            self.check(role+' audible loop follows musical continuation without silent guard',loopcorr['correlation']>0.90,loopcorr)
        P.snap(c,str(self.out/(role+'-context.png')))
        self.scenarios.append(dict(role=role,source_track=t['source_id'],source_title=t['title'],initial=initial,final=end,video_frames=i+1,audio_samples=len(samples),sampled_trace=frames,boundary=boundary,waveform=corr,loop_waveform=loopcorr,
                                   preview_sha256=SHA((self.out/(role+'-preview.wav')).read_bytes()),loop_sha256=SHA((self.out/(role+'-loop.wav')).read_bytes()) if boundary else None))
        self.save()

    def sfx(self):
        if C.gstate(self.core)==4:self.press('START',2,20)
        before=self.diag();self.step(2,('B',),True);pulse=[]
        # Step-and-cut emits its audible swish at its actual active pose,
        # rather than on the input frame. Observe the complete anticipation.
        for _ in range(16):
            self.step(1,heal=True);pulse.append(P.r16(self.core,0x04000062))
        after=self.diag()
        self.check('real sword input produces pulse1 SFX without restarting original music',after['bgm']==1 and after['samples']>before['samples'] and after['dma_offset']==before['dma_offset'] and any(v&0xF000 for v in pulse),dict(before=before,after=after,pulse1=[hex(v) for v in pulse]))
        self.step(60)

    def victory(self):
        if C.gstate(self.core)==4:self.press('START',2,20)
        c=self.core;pl=P.sym('gPl');hero=P.sym('gActors');history=[]
        # Coordinate-only positioning keeps the real blade near the moving
        # Heart. Its original40 HP, AI, height and vulnerability remain live.
        for attempt in range(80):
            e=C.find_actor(c,2,5)
            if not e:break
            history.append(e['hp']);P.w16(c,pl,80);P.w16(c,pl+2,80)
            P.w8(c,hero+28,255) # player invulnerability fixture prevents cancelled swings
            if e['hp']>0:
                C.teleport(c,e['x'],e['y']+24)
                P.w8(c,hero+7,0);P.w8(c,hero+6,0)
                self.press('B',2,28)
            else:self.step(10,heal=True)
        self.step(150,heal=True)
        self.check('Heart retains original40 HP and dies to actual sword hits',bool(history) and history[0]==40 and C.find_actor(c,2,5) is None,history)
        grail=C.find_actor(c,4,6)
        self.check('real Heart death drops its Grail',grail is not None or C.gstate(c)==6,grail)
        if grail:C.teleport(c,grail['x'],grail['y']+2)
        self.step(220,heal=True);self.audio.clear()
        self.check('actual sword victory and Grail trigger original victory music',C.gstate(c)==6 and self.diag()['bgm']==5)
        self.step(120)

    def save(self,error=None):
        report=dict(method=__doc__,emulator='mGBA0.10.5',rom_sha256=SHA(self.rom),source_commit=(self.bundle/'source-commit.txt').read_text().strip(),
                    tool_sha256=SHA(Path(__file__).read_bytes()),manifest_sha256=SHA((Path(__file__).resolve().parent.parent/'audio/original/manifest.json').read_bytes()),
                    fixtures=self.fixtures,checks=self.rows,passed=sum(r['passed'] for r in self.rows),total=len(self.rows),scenarios=self.scenarios,error=error,
                    media=[dict(file=p.name,sha256=SHA(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(self.out.iterdir()) if p.suffix in ('.wav','.png')])
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        return report

    def run(self):
        try:
            self.asset_checks();self.capture(4);self.start_game();self.sfx();self.capture(1)
            w=C.world(self.core);self.warp(w['entry']);self.menu();self.capture(2)
            self.warp(w['goal']);self.menu();self.capture(3)
            self.victory();self.capture(5)
        except Exception:
            error=traceback.format_exc();print(error,flush=True);self.check('audio qualification completes',False,error);self.save(error);return 1
        r=self.save();print('RESULT',r['passed'],'/',r['total'],flush=True);return int(r['passed']!=r['total'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True);p.add_argument('--out',required=True)
    return Review(p.parse_args()).run()


if __name__=='__main__':mgba.log.silence();raise SystemExit(main())
