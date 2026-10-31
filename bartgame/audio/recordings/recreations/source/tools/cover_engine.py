#!/usr/bin/env python3
"""Build instrumental game covers from symbolic automatic transcription.

This module never mixes decoded source samples into synthesized output. Source
audio is read only by analyze_drums(); notes come from a separately recorded
Basic Pitch run. Native note/transient timestamps are not put on a new grid.
The results are automatic instrumental approximations, not verified scores.
"""
from __future__ import annotations
import argparse
import bisect
from collections import Counter
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

import numpy as np
from scipy import ndimage, signal
from scipy.io import wavfile

HERE=Path(__file__).resolve().parent
SAMPLER=Path('/workspace/work/round2/sampler.py')
PALETTES={
    1: dict(melody=81,counter=5,harmony=90,bass=38,kit=25,
            name='soft saw / FM keys / polysynth / synth bass'),
    2: dict(melody=81,counter=5,harmony=89,bass=38,kit=24,
            name='synth lead / FM keys / warm pad / synth bass'),
    3: dict(melody=5,counter=98,harmony=90,bass=38,kit=25,
            name='FM keys / crystal plucks / polysynth / synth bass'),
    4: dict(melody=81,counter=107,harmony=50,bass=39,kit=24,
            name='saw lead / koto / synth strings / synth bass'),
    5: dict(melody=4,counter=27,harmony=90,bass=38,kit=25,
            name='electric piano / clean guitar / polysynth / synth bass'),
    6: dict(melody=27,counter=7,harmony=48,bass=33,kit=0,
            name='clean guitar / clavinet / strings / fingered bass'),
    7: dict(melody=4,counter=98,harmony=89,bass=38,kit=24,
            name='electric piano / crystal plucks / warm pad / synth bass'),
    8: dict(melody=62,counter=5,harmony=90,bass=39,kit=25,
            name='synth brass / FM keys / polysynth / synth bass'),
}

def _decode_mono(path,sample_rate=22050):
    completed=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le',
        '-acodec','pcm_f32le','-ac','1','-ar',str(sample_rate),'-'],
        check=True,stdout=subprocess.PIPE)
    return np.frombuffer(completed.stdout,dtype='<f4').copy()

def _robust_peaks(values,times,min_gap,scale=1.15,quantile=.68):
    """Adaptive local threshold; timing stays on the 9.98ms analysis lattice."""
    values=np.asarray(values,dtype=np.float64)
    dt=float(np.median(np.diff(times)))
    background=ndimage.median_filter(values,size=max(3,int(.6/dt)|1),mode='nearest')
    deviation=ndimage.median_filter(np.abs(values-background),size=max(3,int(.6/dt)|1),mode='nearest')
    floor=float(np.quantile(values,quantile))
    threshold=np.maximum(background+scale*np.maximum(deviation,1e-10),floor)
    peaks,props=signal.find_peaks(values,height=threshold,
        distance=max(1,round(min_gap/dt)),prominence=max(1e-9,float(np.std(values))*.15))
    ref=max(1e-9,float(np.quantile(values[peaks],.92))) if len(peaks) else 1
    return [(int(p),float(np.clip(values[p]/ref,.05,1.3))) for p in peaks]

def analyze_drums(source_path,duration_seconds=None):
    """Read full source transient timing and return fresh GM drum-note events.

    HPSS median masks suppress stable pitched content before low/mid/high
    positive spectral flux is measured. These are heuristic drum candidates:
    consonants, plucks and bass attacks can still be misclassified. No rhythm
    is filled in or moved to a tempo grid, and no audio samples are retained.
    """
    sr=22050;hop=220;nfft=1024
    y=_decode_mono(source_path,sr)
    duration=len(y)/sr if duration_seconds is None else float(duration_seconds)
    freq,times,z=signal.stft(y,fs=sr,nperseg=nfft,noverlap=nfft-hop,
        nfft=nfft,boundary='zeros',padded=False)
    mag=np.abs(z).astype(np.float32)
    del z,y
    harmonic=ndimage.median_filter(mag,size=(1,31),mode='nearest')
    percussive=ndimage.median_filter(mag,size=(17,1),mode='nearest')
    mask=percussive**2/(percussive**2+harmonic**2+1e-12)
    p=mag*mask
    del mag,harmonic,percussive,mask
    # Log compression prevents a single loud kick from setting all thresholds.
    flux=np.maximum(0,np.diff(np.log1p(p*120),axis=1,prepend=np.zeros((len(freq),1),np.float32)))
    def band(lo,hi):
        selected=(freq>=lo)&(freq<hi)
        return np.mean(flux[selected],axis=0)
    low=band(32,180);mid=band(180,2600);high=band(4200,10500)
    proposals=[]
    for label,values,gap,scale,qt in [('kick',low,.12,1.25,.68),
        ('snare',mid+.28*high,.15,1.65,.78),('hat',high,.052,1.15,.67)]:
        for index,strength in _robust_peaks(values,times,gap,scale,qt):
            b=float(times[index])
            if b>=duration:continue
            proposals.append((b,label,index,strength))
    events=[]
    # Fixed measured-time events; all sound is supplied by a GM drum preset.
    for sec,label,i,strength in proposals:
        # Full-mix vocal/pluck attacks otherwise produce many false snare hits.
        # Keep a conservative, independently documented candidate subset.
        if strength<dict(kick=.42,snare=.57,hat=.35)[label]:continue
        if label=='kick':
            pitch=36;length=.10;velocity=.48+.38*min(1,strength)
        elif label=='snare':
            # Bass-dominated peaks without substantial high-band attack are
            # more likely another pitched/low transient than a snare.
            if low[i]>mid[i]*3 and high[i]<np.median(high):continue
            pitch=39 if high[i]>mid[i]*.55 else 38
            length=.12;velocity=.34+.35*min(1,strength)
        else:
            # Bright attacks that also carry a strong snare band are represented
            # by the snare candidate, avoiding systematic clap+hat doubling.
            if mid[i]>high[i]*2.8:continue
            # Longer high-frequency tails suggest an open hat, never a copied tail.
            j=min(p.shape[1],i+7)
            decay=float(np.mean(p[freq>=4200,i+1:j])) if j>i+1 else 0
            attack=float(np.mean(p[freq>=4200,i]))
            pitch=46 if decay>attack*.45 and strength>.65 else 42
            length=.13 if pitch==46 else .055
            velocity=.25+.30*min(1,strength)
        events.append(dict(start=round(sec,6),end=round(min(duration,sec+length),6),
            pitch=pitch,amplitude=round(velocity,5),class_name=label,
            detector_salience=round(strength,4)))
    events.sort(key=lambda e:(e['start'],e['pitch']))
    metadata=dict(detector_version=2,method='HPSS-masked log spectral-flux bands; no quantization or beat filling',
        source_sample_rate=sr,fft_samples=nfft,hop_samples=hop,
        time_resolution_seconds=hop/sr,counts=dict(Counter(e['class_name'] for e in events)),
        thresholds='adaptive local median/MAD plus source-band quantile',
        minimum_relative_peak_salience=dict(kick=.42,snare=.57,hat=.35),
        confidence='heuristic attack candidates, not verified source/stem drum transcription',
        limitations=['Pitched plucks, vocal consonants or bass attacks may produce false drum candidates.',
                     'Quiet or overlapping percussion may be missed; no exact kit separation is claimed.'])
    return events,metadata

def _normalize_notes(document,duration):
    result=[];excluded=Counter();folds=0
    for token,n in enumerate(document.get('notes',[])):
        try:
            start=float(n.get('start',n.get('start_time')))
            end=float(n.get('end',n.get('end_time')))
            pitch=int(round(n['pitch']));amplitude=float(n.get('amplitude',n.get('confidence',.4)))
        except (TypeError,ValueError,KeyError):
            excluded['malformed']+=1;continue
        if not all(math.isfinite(x) for x in (start,end,amplitude)):
            excluded['nonfinite']+=1;continue
        if end-start<.055 or amplitude<.16 or pitch<21 or pitch>100:
            excluded['short_low_salience_or_out_of_range']+=1;continue
        start=max(0,start);end=min(duration,end)
        if end<=start:
            excluded['outside_source_duration']+=1;continue
        # Direct Sound PCM has no PSG pitch floor. Preserve credible raw deep
        # sub fundamentals (including21..27), rather than rewriting their octave.
        # Source01's independent YIN pilot supports its B0/C1 register.
        source_pitch=pitch
        result.append(dict(start=start,end=end,original_start=start,original_end=end,
            pitch=pitch,source_pitch=source_pitch,
            amplitude=amplitude,token=token,stem=n.get('stem','full_mix'),
            pitch_bends=n.get('pitch_bends',[])))
    return sorted(result,key=lambda n:(n['start'],n['pitch'])),dict(excluded),folds

def _mono_bass(notes,bass_f0=None):
    """Resolve overlapping low-note candidates at their original boundaries.

    The winning active candidate favors note activation and a true bass register.
    This avoids simultaneously sounding model harmonic/octave bass duplicates.
    The subset/resolution is documented, not passed off as the original bass stem.
    """
    if not notes:return [],0,dict(f0_validated_intervals=0,total_active_intervals=0)
    boundaries=sorted({t for n in notes for t in (n['start'],n['end'])})
    resolved=[];active={};changes={};validated=0;intervals=0
    def actual_pitch(n,t):
        bends=n.get('pitch_bends')
        if isinstance(bends,(list,tuple)) and bends:
            index=(t-n['original_start'])/max(1e-6,n['original_end']-n['original_start'])*len(bends)
            return n['pitch']+float(np.interp(index,np.arange(len(bends)),bends))/3
        return n['pitch']
    for n in notes:
        changes.setdefault(n['start'],[]).append((True,n))
        changes.setdefault(n['end'],[]).append((False,n))
    for i,t in enumerate(boundaries[:-1]):
        for is_on,n in sorted(changes[t],key=lambda pair:pair[0]):
            if is_on:active[n['token']]=n
            else:active.pop(n['token'],None)
        end=boundaries[i+1]
        if not active or end-t<1e-7:continue
        intervals+=1
        reference=None
        if bass_f0 is not None:
            midpoint=(t+end)*.5;ts=bass_f0['time_seconds']
            index=int(np.clip(np.searchsorted(ts,midpoint),0,len(ts)-1))
            if (bool(bass_f0['valid'][index]) and float(bass_f0['periodicity'][index])>=.78):
                f0=float(bass_f0['midi_float'][index])
                if min(abs(actual_pitch(n,midpoint)-f0) for n in active.values())<.85:
                    reference=f0;validated+=1
        if reference is None:
            n=max(active.values(),key=lambda n:n['amplitude']-.012*max(0,n['pitch']-43))
        else:
            n=max(active.values(),key=lambda n:n['amplitude']*.55-.24*min(6,abs(actual_pitch(n,(t+end)*.5)-reference)))
        if resolved and resolved[-1]['token']==n['token'] and abs(resolved[-1]['end']-t)<1e-7:
            resolved[-1]['end']=end
        else:resolved.append(dict(n,start=t,end=end))
    return ([n for n in resolved if n['end']-n['start']>=.04],
        len(notes)-len({n['token'] for n in resolved}),
        dict(f0_validated_intervals=validated,total_active_intervals=intervals,
             rule='Independent low-band YIN breaks ties only when valid periodic F0 matches an existing note+bend within0.85semitones; no notes or times generated.'))

def _foreground_tokens(notes):
    """Weighted nonoverlapping foreground; all other notes remain in the score.

    Dense HPSS/full-mix note candidates are not instrument stems. Selecting one
    foreground avoids turning every staggered chord tone into a loud lead while
    retaining the remaining original-time candidates as counter/harmony parts.
    This is role assignment, not a claim to have recovered the original lead.
    """
    candidates=sorted((n for n in notes if 55<=n['pitch']<=94),key=lambda n:n['end'])
    ends=[n['end'] for n in candidates];best=[0.0];take=[];prior=[]
    for i,n in enumerate(candidates):
        j=bisect.bisect_right(ends,n['start']+1e-7,hi=i)
        duration=n['end']-n['start']
        register=.45+.55*math.exp(-((n['pitch']-75)/23)**2)
        weight=n['amplitude']*math.sqrt(duration)*register*(1.25 if n['stem']=='vocals' else 1)
        selected=weight+best[j]
        take.append(selected>best[-1]);prior.append(j)
        best.append(max(best[-1],selected))
    result=set();i=len(candidates)
    while i:
        if take[i-1]:result.add(candidates[i-1]['token']);i=prior[i-1]
        else:i-=1
    return result

def build_score(note_document,source,drum_events=None,drum_metadata=None,bass_note_document=None,bass_f0=None):
    duration=float(source['duration_seconds']);sid=int(source['id'])
    notes,excluded,folds=_normalize_notes(note_document,duration)
    palette=PALETTES[sid]
    def spec(program,pan,volume,drum=False):
        return dict(program=program,pan=pan,volume=volume,drum=drum)
    parts=dict(melody=spec(palette['melody'],-.06,.80),
        counter=spec(palette['counter'],.24,.58),
        harmony=spec(palette['harmony'],-.22,.44),
        bass=spec(palette['bass'],0,.91),drums=spec(palette['kit'],0,.70,True))
    bass_source=notes;extra_bass_metadata=None
    if bass_note_document is not None:
        bass_source,bass_excluded,bass_folds=_normalize_notes(bass_note_document,duration)
        # Independent model tokens need a stable separate namespace.
        for n in bass_source:n['token']+=1000000
        extra_bass_metadata=dict(transcription=bass_note_document.get('transcription',{}),
            excluded_note_reasons=bass_excluded,deep_candidates_octave_folded=bass_folds,
            role='Only the low-register monophonic bass is taken from this separate band-limited pass; no blind note union.')
    events=[];bass,masked_bass,bass_f0_report=_mono_bass(
        [n for n in bass_source if n['pitch']<=51 and n['stem']!='vocals'],bass_f0=bass_f0)
    melodic=[n for n in notes if n['pitch']>51 or n['stem']=='vocals']
    for n in bass:
        velocity=float(np.clip(.33+n['amplitude']*.86,.31,.94))
        events.append(dict(voice='bass',beat=n['start']*2,duration=(n['end']-n['start'])*2,
            pitch=n['pitch'],velocity=velocity,source_note_token=n['token'],
            source_pitch=n['source_pitch'],raw_pitch_bends=n['pitch_bends'],
            bend_source_start=n['original_start'],bend_source_end=n['original_end']))
    # Preserve every retained nonbass note onset/end; role allocation alone is
    # heuristic. Full mix cannot tell which line was a vocal or actual instrument.
    foreground=_foreground_tokens(melodic)
    for n in melodic:
        if n['token'] in foreground:voice='melody'
        elif n['end']-n['start']>.50:voice='harmony'
        else:voice='counter'
        velocity=float(np.clip(.26+n['amplitude']*.95,.25,.91))
        events.append(dict(voice=voice,beat=n['start']*2,duration=(n['end']-n['start'])*2,
            pitch=n['pitch'],velocity=velocity,source_note_token=n['token'],
            source_pitch=n['source_pitch'],source_stem=n['stem'],raw_pitch_bends=n['pitch_bends']))
    for n in drum_events or []:
        if n['end']>n['start']:
            events.append(dict(voice='drums',beat=n['start']*2,duration=(n['end']-n['start'])*2,
                pitch=n['pitch'],velocity=n['amplitude'],detector_salience=n.get('detector_salience'),
                detected_class=n.get('class_name')))
    events.sort(key=lambda e:(e['beat'],e['voice'],e['pitch']))
    score=dict(id=sid,code=f'R{sid:02}',title=source['display_title']+' — automatic game-instrument cover',
        slug=source['slug']+'-instrumental-cover',bpm=120,beats=duration*2,
        duration_seconds=duration,loop_start_beat=0,parts=parts,events=events,
        render_gain=.28,source_file_name=source['file_name'],source_sha256=source['source_sha256'],
        description='Native-time symbolic automatic transcription revoiced with game/GM instruments; no source samples or vocals in synthesis.',
        analysis=dict(palette=palette['name'],raw_note_count=len(note_document.get('notes',[])),
            retained_note_candidates=len(notes),rendered_pitched_events=sum(e['voice']!='drums' for e in events),
            excluded_note_reasons=excluded,bass_candidates_masked_by_monophonic_resolution=masked_bass,
            deep_bass_candidates_octave_folded=folds,
            part_counts=dict(Counter(e['voice'] for e in events)),
            source_transcription=note_document.get('transcription',{}),drum_analysis=drum_metadata or {},
            separate_bass_pass=extra_bass_metadata,
            bass_f0_candidate_validation=bass_f0_report,
            engine_revision='symbolic-cover-v4-raw-sub-f0-tiebreak',
            foreground_role_assignment='Weighted nonoverlapping native-time note path; other retained pitches remain in counter/harmony voices.',
            timing='Native model/transient timestamps retained without tempo grid or source trimming; bpm120 is an export timebase only.',
            uncertainty=['Automatic transcription of a dense full mix is not a complete or exact transcription.',
                'Vocal, bass, chord and percussion source attribution is uncertain unless explicit stem labels were supplied.',
                'Raw deep bass pitches are retained without octave folding; unresolved model octave errors remain possible. Overlapping candidates are resolved to one active note.',
                'Raw Basic Pitch bend bins drive only the resolved monophonic bass; other GM voices use equal-tempered note centers.',
                'No ground-truth score or human listening validation is available.']))
    return score

def _vlq(n):
    n=max(0,int(n));b=[n&127];n>>=7
    while n:b.insert(0,0x80|(n&127));n>>=7
    return bytes(b)

def write_midi(score,path):
    """Dependency-free SMF1, ~0.52ms tick resolution at an export bpm120."""
    ppqn=960;tracks=[]
    def track(events):
        # Preserve controller/RPN ordering at equal timestamps. Sorting by raw
        # message bytes would put Data Entry before RPN selection and silently
        # leave a DAW at its default two-semitone pitchwheel range.
        def priority(message):
            status=message[0]&0xf0
            return 0 if status==0x80 else (2 if status==0x90 else 1)
        events=[event for _,event in sorted(enumerate(events),
            key=lambda item:(item[1][0],priority(item[1][1]),item[0]))]
        data=bytearray();last=0
        for t,msg in events:data.extend(_vlq(t-last)+msg);last=t
        end=round(score['beats']*ppqn)
        data.extend(_vlq(max(0,end-last))+b'\xff\x2f\x00')
        return b'MTrk'+struct.pack('>I',len(data))+data
    title=score['title'].encode('utf8')[:120]
    tracks.append(track([(0,b'\xff\x03'+_vlq(len(title))+title),
                         (0,b'\xff\x51\x03\x07\xa1\x20')]))
    channels=iter([0,1,2,3,4,5,6,7,8,10,11,12,13,14,15])
    for voice,spec in score['parts'].items():
        ch=9 if spec.get('drum') else next(channels)
        name=voice.encode();ev=[(0,b'\xff\x03'+_vlq(len(name))+name),
            (0,bytes([0xc0|ch,int(spec['program'])])),
            (0,bytes([0xb0|ch,7,round(spec['volume']*127)])),
            (0,bytes([0xb0|ch,10,round((spec['pan']+1)*63.5)]))]
        if voice=='bass':
            for cc,value in [(101,0),(100,0),(6,12),(38,0),(101,127),(100,127)]:
                ev.append((0,bytes([0xb0|ch,cc,value])))
        for e in score['events']:
            if e['voice']!=voice:continue
            st=round(e['beat']*ppqn);en=max(st+1,round((e['beat']+e['duration'])*ppqn))
            ev.append((st,bytes([0x90|ch,e['pitch'],max(1,round(e['velocity']*127))])))
            ev.append((en,bytes([0x80|ch,e['pitch'],0])))
            if voice=='bass':
                raw=e.get('raw_pitch_bends',[])
                if isinstance(raw,(list,tuple)) and raw:
                    values=np.asarray(raw,dtype=float)
                    source_start=e.get('bend_source_start',e['beat']*.5)
                    source_end=e.get('bend_source_end',(e['beat']+e['duration'])*.5)
                    original_times=np.linspace(source_start,source_end,len(values),endpoint=False)
                    times=np.arange(e['beat']*.5,(e['beat']+e['duration'])*.5,.02)
                    for t,b in zip(times,np.interp(times,original_times,values)):
                        val=int(np.clip(round(8192+float(b)/3/12*8192),0,16383))
                        ev.append((round(t*2*ppqn),bytes([0xe0|ch,val&127,(val>>7)&127])))
                else:ev.append((st,bytes([0xe0|ch,0,64])))
        tracks.append(track(ev))
    Path(path).write_bytes(b'MThd'+struct.pack('>IHHH',6,1,len(tracks),ppqn)+b''.join(tracks))

def render_cover(score,sample_rate=32768):
    """Synthesize symbolic events only; this function cannot open source audio."""
    import ctypes as C
    module_spec=importlib.util.spec_from_file_location('cover_gm_sampler',SAMPLER)
    sampler=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(sampler)
    parts=sampler._parts(score)
    samples=round(score['duration_seconds']*sample_rate)
    audio=np.zeros((samples,2),np.float32)
    schedule=[];bend_count=0
    for token,event in enumerate(score['events']):
        part=parts[event['voice']];ch=part['channel'];pitch=event['pitch']
        start=max(0,min(samples-1,round(event['beat']*.5*sample_rate)))
        end=max(start+1,min(samples,round((event['beat']+event['duration'])*.5*sample_rate)))
        schedule.append((end,0,token,ch,pitch,0))
        schedule.append((start,2,token,ch,pitch,max(1,round(event['velocity']*127))))
        if event['voice']=='bass':
            raw=event.get('raw_pitch_bends',[])
            if isinstance(raw,(list,tuple)) and len(raw)>0:
                bends=np.asarray(raw,dtype=float)
                if bends.size and np.isfinite(bends).all():
                    # Basic Pitch bins are 1/3 semitone; no source waveform is used.
                    source_start=event.get('bend_source_start',event['beat']*.5)
                    source_end=event.get('bend_source_end',(event['beat']+event['duration'])*.5)
                    original_times=np.linspace(source_start,source_end,len(bends),endpoint=False)
                    seg_start=event['beat']*.5;seg_end=(event['beat']+event['duration'])*.5
                    times=np.arange(seg_start,seg_end,.02)
                    for t,bend in zip(times,np.interp(times,original_times,bends)):
                        value=int(np.clip(round(8192+float(bend)/3/12*8192),0,16383))
                        schedule.append((min(end-1,round(t*sample_rate)),3,token,ch,0,value));bend_count+=1
            else:schedule.append((start,1,token,ch,0,8192))
    schedule.sort(key=lambda x:(x[0],x[1],x[2]))
    with sampler.Synth(sample_rate,gain=float(score.get('render_gain',.28)),effects=True) as synth:
        selection=sampler._select_parts(synth,parts)
        bend_fn=synth.lib.fluid_synth_pitch_bend
        bend_fn.restype=C.c_int;bend_fn.argtypes=[C.c_void_p,C.c_int,C.c_int]
        sensitivity=synth.lib.fluid_synth_pitch_wheel_sens
        sensitivity.restype=C.c_int;sensitivity.argtypes=[C.c_void_p,C.c_int,C.c_int]
        sensitivity(synth.synth,parts['bass']['channel'],12)
        cursor=0;active={}
        for when,kind,token,ch,pitch,velocity in schedule:
            if when>cursor:synth.write(audio,cursor,when);cursor=when
            if kind==0:
                if active.get((ch,pitch))==token:
                    synth.lib.fluid_synth_noteoff(synth.synth,ch,pitch);del active[ch,pitch]
            elif kind in (1,3):bend_fn(synth.synth,ch,velocity)
            else:
                if (ch,pitch) in active:synth.lib.fluid_synth_noteoff(synth.synth,ch,pitch)
                synth.lib.fluid_synth_noteon(synth.synth,ch,pitch,velocity);active[ch,pitch]=token
        if cursor<samples:synth.write(audio,cursor,samples)
        metadata=dict(soundfont=synth.path.name,fluidsynth=synth.lib.fluid_version_str().decode(),
            sample_rate=sample_rate,main_samples=samples,parts=selection,note_count=len(score['events']),
            bass_bend_automation_events=bend_count,bass_pitchbend_range_semitones=12,
            other_parts_pitchbend='equal-tempered note centers',scheduled_sample_accuracy=1,
            synth_internal_block_samples=64,gain=float(score.get('render_gain',.28)))
    audio-=np.mean(audio,axis=0,dtype=np.float64)
    peak=float(np.max(np.abs(audio),initial=0))
    rms=float(np.sqrt(np.mean(audio.astype(np.float64)**2)))
    gain=min(.91/max(peak,1e-9),.13/max(rms,1e-9))
    audio*=gain
    metadata.update(symbolic_only=True,source_audio_in_render=False,master_gain=gain,
        master_peak=float(np.max(np.abs(audio),initial=0)),
        master_rms=float(np.sqrt(np.mean(audio.astype(np.float64)**2))))
    return audio,metadata

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=HERE/'source_manifest.json')
    p.add_argument('--id',type=int,required=True)
    p.add_argument('--notes',type=Path,help='Basic Pitch JSON using native absolute seconds')
    p.add_argument('--bass-notes',type=Path,help='Optional coherent band-limited pass used only for bass, not blindly unioned')
    p.add_argument('--bass-f0',type=Path,help='Optional independent native-time low-band YIN NPZ for bass-candidate disambiguation')
    p.add_argument('--drums-json',type=Path,help='Reuse/save drum analysis JSON; extracts if absent')
    p.add_argument('--score',type=Path,required=True)
    p.add_argument('--midi',type=Path)
    p.add_argument('--render',type=Path,help='Write stereo float32 .npy synthesized from score only')
    p.add_argument('--wav',type=Path,help='Optional signed16 review WAV, pre-GBA-emulation')
    p.add_argument('--sample-rate',type=int,default=32768)
    p.add_argument('--no-drums',action='store_true')
    args=p.parse_args()
    if args.notes:
        source=next(s for s in json.loads(args.manifest.read_text())['sources'] if s['id']==args.id)
        note_document=json.loads(args.notes.read_text())
        if args.no_drums:drums,drum_meta=[],{}
        elif args.drums_json and args.drums_json.exists() and json.loads(args.drums_json.read_text()).get('analysis',{}).get('detector_version')==2:
            d=json.loads(args.drums_json.read_text());drums,drum_meta=d['events'],d['analysis']
        else:
            drums,drum_meta=analyze_drums(source['source_path'],source['duration_seconds'])
            if args.drums_json:
                args.drums_json.parent.mkdir(parents=True,exist_ok=True)
                args.drums_json.write_text(json.dumps(dict(events=drums,analysis=drum_meta),separators=(',',':'))+'\n')
        bass_document=json.loads(args.bass_notes.read_text()) if args.bass_notes else None
        bass_f0=dict(np.load(args.bass_f0)) if args.bass_f0 else None
        score=build_score(note_document,source,drums,drum_meta,bass_note_document=bass_document,bass_f0=bass_f0)
        score['analysis']['input_note_sha256']=hashlib.sha256(args.notes.read_bytes()).hexdigest()
        if args.bass_notes:score['analysis']['input_bass_note_sha256']=hashlib.sha256(args.bass_notes.read_bytes()).hexdigest()
        if args.bass_f0:score['analysis']['input_bass_f0_sha256']=hashlib.sha256(args.bass_f0.read_bytes()).hexdigest()
        score['analysis']['engine_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        args.score.parent.mkdir(parents=True,exist_ok=True)
        args.score.write_text(json.dumps(score,separators=(',',':'))+'\n')
    else:score=json.loads(args.score.read_text())
    if args.midi:write_midi(score,args.midi)
    if args.render or args.wav:
        audio,metadata=render_cover(score,args.sample_rate)
        if args.render:
            np.save(args.render,audio)
            args.render.with_suffix('.render.json').write_text(json.dumps(metadata,indent=2)+'\n')
        if args.wav:wavfile.write(args.wav,args.sample_rate,np.rint(np.clip(audio,-1,1)*32767).astype(np.int16))
    print(json.dumps(dict(id=score['id'],duration=score['duration_seconds'],events=len(score['events']),parts=score['analysis']['part_counts'])))

if __name__=='__main__':main()
