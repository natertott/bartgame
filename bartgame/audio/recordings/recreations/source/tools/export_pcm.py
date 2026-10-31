#!/usr/bin/env python3
"""Faithful source performance -> synchronized GBA PCM, without time stretching."""
from pathlib import Path
import json,subprocess,numpy as np,hashlib,math,argparse,os
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parent
FPS=16777216/280896

def export_planes(audio,source,code,rate,kind,extra=None):
    destination=ROOT/'assets'/code
    (destination/'src').mkdir(parents=True,exist_ok=True)
    seconds=source['duration_seconds'];frames=math.ceil(seconds*FPS)
    timeline_samples=math.ceil(frames*rate/FPS)
    audio=np.asarray(audio,dtype=np.float64)
    source_samples=round(seconds*rate)
    if len(audio)<source_samples:audio=np.pad(audio,((0,source_samples-len(audio)),(0,0)))
    audio=audio[:source_samples]
    if not np.isfinite(audio).all():raise ValueError('Nonfinite PCM')
    # Full triangular dither prevents low-level tones sticking at 8-bit steps.
    rng=np.random.default_rng(81000+source['id']+(100 if kind=='instrument' else 0))
    dither=rng.random(audio.shape)-rng.random(audio.shape)
    pcm=np.rint(audio*127+dither).clip(-127,127).astype(np.int8)
    # True digital source silence remains zero rather than becoming dither noise.
    silence_threshold=1e-10 if kind=='original_mix' else 1e-4
    pcm[np.max(np.abs(audio),axis=1)<silence_threshold]=0
    assert timeline_samples>=len(pcm)
    n=timeline_samples+8192;n+=(16-n%16)%16
    hashes=[]
    for channel,name in enumerate(('left','right')):
        plane=np.zeros(n,dtype=np.int8);plane[:len(pcm)]=pcm[:,channel]
        path=destination/f'pcm_{name}.bin';path.write_bytes(plane.tobytes())
        hashes.append(hashlib.sha256(plane.tobytes()).hexdigest())
    reload=65536-round(16777216/rate)
    bias=0x4200 if rate==65536 else 0x0200
    title=code+' - '+source['display_title'].replace('—','-').replace('–','-')
    c='#include "soundtrack_data.h"\nextern const signed char pcmL[],pcmR[];\nconst SoundtrackSong gSoundtrackSongs[2]={{0},{pcmL,pcmR,0,0,%d,0,0,0,%s,0x%04X,0x%04X}};\n'%(frames,json.dumps(title),reload,bias)
    (destination/'src/soundtrack_data.c').write_text(c)
    (destination/'src/soundtrack_pcm.s').write_text('.section .rodata.music,"a"\n.balign16\n.global pcmL\npcmL:\n.incbin "pcm_left.bin"\n.balign16\n.global pcmR\npcmR:\n.incbin "pcm_right.bin"\n'.replace('.balign16','.balign 16'))
    metadata={'source_id':source['id'],'id':1,'code':code,'kind':kind,'title':source['display_title'],'slug':source['slug'],'file_name':source['file_name'],'source_sha256':source['source_sha256'],'seconds':seconds,'total_frames':frames,'rate':rate,'timer_reload':reload,'sound_bias':bias,'channels':2,'bits':8,'source_samples_per_channel':source_samples,'stored_samples_per_channel':n,'pcm_bytes':2*n,'pcm_sha256':hashes,'asset_directory':str(destination),'quantization':'signed8-bit, nearest step with full TPDF dither; digital silence kept zero','no_source_trimming':True,'no_time_stretch':True,'extra':extra or {}}
    (destination/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--native',action='store_true');ap.add_argument('--covers',action='store_true');ap.add_argument('--ids',nargs='+',type=int);a=ap.parse_args()
    sources=json.loads((ROOT/'source_manifest.json').read_text())['sources']
    if a.native:
        cache=ROOT/'native_cache';cache.mkdir(exist_ok=True);entries=[];maxpeak=0
        for s in sources:
            rate=32768 if s['id']==3 else 65536
            path=cache/f"{s['id']:02d}_{rate}.npy"
            if path.is_file():audio=np.load(path,mmap_mode='r')
            else:
                command=['ffmpeg','-v','error','-i',s['source_path'],'-af',f'aresample={rate}:resampler=soxr:precision=28','-ac','2','-f','f32le','-']
                raw=subprocess.check_output(command);audio=np.frombuffer(raw,dtype='<f4').reshape(-1,2);np.save(path,audio)
            peak=float(np.max(np.abs(audio)));maxpeak=max(maxpeak,peak);entries.append((s,rate,path,peak))
            print('Decoded',s['id'],s['display_title'],len(audio),'peak',peak,flush=True)
        # A common gain preserves relative source loudness and avoids clipping any mix.
        gain=min(1,.92/maxpeak)
        native=[]
        for s,rate,path,peak in entries:
            audio=np.load(path,mmap_mode='r')*gain
            meta=export_planes(audio,s,f"R{s['id']:02d}",rate,'original_mix',{'common_gain':gain,'source_decoded_peak':peak,'source_performance_and_vocals':True,'rate_limit_note':'Full track retained; 65,536Hz stereo exceeds32MiB for this source, so synchronized32,768Hz is used.' if rate==32768 else None})
            assert meta['pcm_bytes']+65536<=33554432
            native.append(meta);print('Exported',meta['code'],meta['pcm_bytes'],rate,flush=True)
        (ROOT/'native_manifest.json').write_text(json.dumps({'common_gain':gain,'songs':native},indent=2)+'\n')
    if a.covers:
        mp=ROOT/'instrument_manifest.json'
        by_id={s['source_id']:s for s in json.loads(mp.read_text())['songs']} if mp.exists() else {}
        for s in sources:
            if a.ids and s['id'] not in a.ids:continue
            path=ROOT/'covers'/f"{s['id']:02d}_{s['slug']}.npy"
            audio=np.load(path,mmap_mode='r');rmeta=json.loads(path.with_suffix('.render.json').read_text());sr=rmeta.get('sample_rate',32768)
            if sr!=32768:audio=resample_poly(audio,32768,sr,axis=0)
            # The symbolic renderer already applies its documented linear headroom.
            # Preserve its dynamics and synth tone; no extra saturation or time edits.
            meta=export_planes(audio,s,f"I{s['id']:02d}",32768,'instrument',{'automatic_transcription':True,'source_waveform_in_render':False,'render_metadata':rmeta,'common_mix_gain':1.0,'quiet_tail_gate_threshold':1e-4})
            by_id[s['id']]=meta;print('Exported',meta['code'],meta['pcm_bytes'],flush=True)
        mp.write_text(json.dumps({'songs':sorted(by_id.values(),key=lambda s:s['source_id'])},indent=2)+'\n')
if __name__=='__main__':main()
