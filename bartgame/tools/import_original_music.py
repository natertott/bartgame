#!/usr/bin/env python3
"""Import the game's original native GBA recordings, without recomposition.

The original composer/player sources for these thirty pieces were not committed
on forest-art. The lossless mGBA recordings and exact first-pass/loop metadata
were. This importer checks out only five specified blobs into a temporary
folder, resamples their mono native mix to the hardware's synchronous32768Hz
clock, and quantizes signed8-bit ROM streams. No MP3 or unrelated uploaded-song
recreation is used. Normal builds consume the checked-in streams without ffmpeg.

Run from bartgame/: python3 tools/import_original_music.py
Requires the pinned forest-art commit locally, ffmpeg and numpy for re-import.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np

REVISION='cad41afcc9041b0a346fe052aba54f2caa19043a'
RATE=32768
GUARD=8192
# Stable existing BGM IDs: silence,sewer,forest,boss,title,win.
MAPPING=((1,'sewer',1),(2,'forest',2),(3,'boss',3),(4,'title',26),(5,'win',25))
SHA=lambda data:hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--revision',default=REVISION)
    p.add_argument('--out',default='audio/original')
    args=p.parse_args()
    game=Path(__file__).resolve().parent.parent;repo=game.parent
    out=(game/args.out).resolve();(out/'pcm').mkdir(parents=True,exist_ok=True)
    def blob(path):return subprocess.check_output(['git','show',args.revision+':'+path],cwd=repo)
    manifest_path='bartgame/audio/recordings/soundtrack_manifest.json'
    original_bytes=blob(manifest_path);original=json.loads(original_bytes)
    (out/'source-catalogue.json').write_bytes(original_bytes)
    checksum_bytes=blob('bartgame/audio/recordings/SHA256SUMS')
    (out/'source-SHA256SUMS.txt').write_bytes(checksum_bytes)
    expected_hashes={line.split('  ',1)[1]:line.split('  ',1)[0] for line in checksum_bytes.decode().splitlines()}
    (out/'source-captures').mkdir(exist_ok=True)
    tracks={s['id']:s for s in original['songs']}
    records=[]
    with tempfile.TemporaryDirectory(prefix='bartgame-original-music-') as tmp:
        for bgm,role,number in MAPPING:
            track=tracks[number];source_path='bartgame/audio/recordings/flac/%02d_%s.flac'%(number,track['slug'])
            source=blob(source_path)
            assert SHA(source)==expected_hashes['flac/'+Path(source_path).name],source_path
            provenance_path='bartgame/audio/recordings/provenance/%02d_%s.capture.json'%(number,track['slug'])
            provenance=blob(provenance_path);capture=json.loads(provenance)
            assert capture['song_id']==number and capture['observed_loop_count']>=1,provenance_path
            (out/'source-captures'/Path(provenance_path).name).write_bytes(provenance)
            file=Path(tmp)/Path(source_path).name;file.write_bytes(source)
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(file),'-ac','1','-af',
                'aresample=32768:filter_size=64:phase_shift=10:exact_rational=1',
                '-ar',str(RATE),'-f','f32le','pipe:1'])
            samples=np.frombuffer(raw,dtype='<f4')
            count=(track['total_frames']*4389+7)//8 # ceil(frame *280896/512)
            loop=(track['loop_frame']*4389+4)//8
            loop &= ~3 # DMA source is word-aligned; error is at most3 samples.
            assert len(samples)>count+RATE,source_path
            active=samples[:count]
            pcm=np.clip(np.rint(active*128),-128,127).astype('i1').tobytes()
            padding=(-len(pcm))&15
            # Playback may cross a boundary before the next VBlank. Append the
            # actual next loop samples so this safe prefetch interval is musical.
            payload=pcm+pcm[loop:loop+padding+GUARD]
            filename=role+'.pcm';(out/'pcm'/filename).write_bytes(payload)
            reconstruction=np.frombuffer(pcm,dtype='i1').astype('f4')/128
            mse=float(np.mean((active-reconstruction)**2))
            rec=dict(bgm_id=bgm,role=role,source_id=number,title=track['title'],
                source_revision=args.revision,source_path=source_path,source_blob_sha256=SHA(source),
                source_capture_path=provenance_path,source_capture_sha256=SHA(provenance),
                original_player_rom_sha256=capture['rom_sha256'],
                source_expected_flac_sha256=expected_hashes['flac/'+Path(source_path).name],
                source_manifest_path=manifest_path,source_manifest_sha256=SHA(original_bytes),
                source_first_pass_frames=track['total_frames'],source_loop_frame=track['loop_frame'],
                sample_rate=RATE,sample_count=count,loop_sample=loop,guard_samples=GUARD,guard_content='loop continuation, not silence',
                alignment_padding=padding,pcm_file='pcm/'+filename,pcm_bytes=len(payload),
                pcm_sha256=SHA(payload),active_pcm_sha256=SHA(pcm),
                source_peak=float(np.max(np.abs(active))),quantization_mse=mse,
                max_quantization_error=float(np.max(np.abs(active-reconstruction))),
                loop_source_alignment_error_samples=loop-track['loop_frame']*4389/8,
                method='Lossless native mGBA first pass; ffmpeg polyphase resample32768Hz; nearest signed8-bit, unity gain; no recomposition, mixer or runtime decoder.')
            records.append(rec);print(role,number,track['title'],len(payload),flush=True)
    output=dict(schema=1,source_revision=args.revision,source_catalogue_songs=30,
                source_catalogue_kind='Original BARTGAME soundtrack; not later uploaded-song recreations',
                sample_format='signed8-bit mono',sample_rate=RATE,timer0_reload='0xFE00',
                sound_bias='0x0200',dma_channel=1,fifo='A, routed to both speakers',
                loop_clock='Timer1 cascades Timer0 sample clocks; VBlank heartbeat checks actual sample count',
                tracks=records)
    (out/'manifest.json').write_text(json.dumps(output,indent=2)+'\n')

    # Re-import updates descriptors and assembler with the same source data;
    # no manual sample lengths can drift from the generated payloads.
    c=['/* Imported native original music; see audio/original/manifest.json. */',
       '#include "original_music_data.h"','']
    asm=['/* Signed8-bit mono ROM streams, no runtime decoder or sample buffers. */',
         '.section .rodata.original_music_pcm,"a",%progbits','.balign 16']
    for t in records:
        role=t['role'];name='gOriginalPcm_'+role
        c.append('extern const s8 %s[];'%name)
        asm+=['.global '+name,name+':',
              '.incbin "audio/original/pcm/%s.pcm"'%role,'.balign 16']
    c+=['','const OriginalSong gOriginalSongs[BGM_COUNT] = {',
        '    [BGM_NONE] = { 0, 0, 0, 0, 0, 0, "Silence" },']
    for t in records:
        c.append('    [BGM_%s] = { gOriginalPcm_%s, %du, %du, %d, %d, %d, "%s" },'%(
            t['role'].upper(),t['role'],t['sample_count'],t['loop_sample'],
            t['source_first_pass_frames'],t['source_loop_frame'],t['source_id'],t['title']))
    c+=['};','']
    (game/'src/original_music_data.c').write_text('\n'.join(c))
    (game/'src/original_music_pcm.s').write_text('\n'.join(asm)+'\n')


if __name__=='__main__':main()
