#!/usr/bin/env python3
"""Publish measured mGBA throughput, exact native evidence and a production ROM.

Graphs describe measurements; they are not game artwork. Complete raw survey
JSON is compressed losslessly with its original hash recorded. Native views,
GIF samples and independent regression/host reports are preserved separately.
Instrumented profiling ROMs are never copied to a release.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageSequence

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parent
HZ = 262144 / 4389
TOOL_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
SUITES = ('broad', 'throughput', 'steady')
SELECTED = (('broad', 'forest-0000b4a7-cell10', 'Natural forest: seed0xB4A7 / room10'),
            ('throughput', 'stress-knights-24', 'Synthetic24 Confessors / no player offense'))
BG, FG, DIM = '#101820', '#f8e0a0', '#b0c0b8'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n')


def rgb_sha(image):
    return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


def safe(root, relative):
    path = (root/relative).resolve()
    assert path.is_relative_to(root.resolve()), ('unsafe relative file', relative)
    return path


def rates(rows):
    eligible = sum(r['eligible_gameplay_frames'] for r in rows)
    updates = sum(r['eligible_gameplay_updates'] for r in rows)
    return dict(cases=len(rows), eligible_frames=eligible, updates=updates,
                updates_per_second=HZ*updates/eligible if eligible else None,
                ratio=updates/eligible if eligible else None,
                missed=sum(r['missed_gameplay_updates'] for r in rows),
                longest_repeat=max((r['longest_repeat'] for r in rows), default=0))


class Publisher:
    def __init__(self, args):
        self.args = args
        self.before, self.after = Path(args.before).resolve(), Path(args.after).resolve()
        self.bundle = Path(args.bundle).resolve()
        self.out = Path(args.out).resolve()
        self.reg_root = Path(args.regression).resolve()
        self.source = (self.bundle/'source-commit.txt').read_text().strip()
        assert re.fullmatch(r'[a-f0-9]{40}', self.source), 'unfrozen source identity'
        self.release = REPO/'downloads'/('performance-'+self.source[:7])
        self.rom = self.bundle/'bartgame.gba'
        self.qa, self.raw_records, self.host_records = [], [], []
        self.surveys, self.selected, self.profiles = {}, [], {}
        self.out.mkdir(parents=True, exist_ok=True)

    def check(self, name, ok, detail=None):
        row = dict(name=name, passed=bool(ok))
        if detail is not None:
            row['detail'] = detail
        self.qa.append(row)
        assert ok, (name, detail)

    def copy(self, src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        self.check('exact copy '+str(dst.relative_to(REPO)), sha(src)==sha(dst))

    def compressed(self, src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        raw = src.read_bytes()
        with dst.open('wb') as f:
            with gzip.GzipFile(fileobj=f, mode='wb', filename='', mtime=0, compresslevel=9) as g:
                g.write(raw)
        self.check('lossless complete raw report '+str(dst.relative_to(self.out)), gzip.decompress(dst.read_bytes())==raw)
        return dict(file=str(dst.relative_to(self.out)), sha256=sha(dst), bytes=dst.stat().st_size,
                    original_sha256=sha(src), original_bytes=len(raw))

    def freeze(self):
        path = self.bundle/'freeze.json'
        data = json.loads(path.read_text())
        self.check('production freeze identifies source', data.get('source_commit')==self.source)
        self.check('production freeze identifies ROM', data.get('rom_sha256')==sha(self.rom))
        self.check('not a private pilot', 'pilot' not in data.get('status', '').lower())
        inputs = data.get('inputs', data.get('source_file_sha256', {}))
        self.check('frozen input hashes exist', bool(inputs))
        for name, expected in inputs.items():
            self.check('frozen source unchanged '+name, sha(safe(GAME, name))==expected)
        elf = self.bundle/'bartgame.elf'
        self.check('production ELF exists', elf.exists())
        symbols = subprocess.check_output(['arm-none-eabi-nm', '--defined-only', str(elf)], text=True)
        self.check('released ELF excludes profiling counters and timer routines',
                   not any(re.search(r'\b'+name+r'\s*$', symbols, re.M) for name in
                           ('gPerfCycles', 'gPerfWorking', 'gPerfSequence', 'perf_clock', 'perf_frame_begin', 'perf_frame_end')))
        for name in ('freeze.json', 'source-commit.txt', 'assets.h', 'bartgame.map', 'coverage.json'):
            if (self.bundle/name).exists():
                self.copy(self.bundle/name, self.out/'validation'/'frozen'/name)

    def reports(self):
        before_rom = sha(self.before/'bundle'/'bartgame.gba')
        before_source = (self.before/'bundle'/'source-commit.txt').read_text().strip()
        for phase, root, source, rom in (('before', self.before, before_source, before_rom),
                                        ('after', self.after, self.source, sha(self.rom))):
            self.surveys[phase] = {}
            for suite in SUITES:
                path = root/suite/'report.json'
                data = json.loads(path.read_text())
                self.check(phase+'/'+suite+' survey complete', data['complete'] and not data.get('errors'))
                self.check(phase+'/'+suite+' integrity checks pass', data['passed']==data['total'])
                self.check(phase+'/'+suite+' frozen production identity', data['source_commit']==source and data['rom_sha256']==rom)
                self.surveys[phase][suite] = data
                self.raw_records.append({'phase':phase, 'suite':suite,
                    **self.compressed(path, self.out/'measurements'/(phase+'-'+suite+'.json.gz'))})
                names = [r['name'] for r in data['scenarios']]
                self.check(phase+'/'+suite+' unique case names', len(names)==len(set(names)))
                for row in data['scenarios']:
                    samples = [s for s in row['samples'] if s['expected_play']]
                    eligible, updates = len(samples), sum(s['logic_delta'] for s in samples)
                    missed = sum(s['logic_delta']==0 for s in samples)
                    self.check(phase+'/'+suite+'/'+row['name']+' metrics match raw samples',
                               eligible==row['eligible_gameplay_frames'] and updates==row['eligible_gameplay_updates']
                               and missed==row['missed_gameplay_updates'])
        for suite in SUITES:
            a, b = self.surveys['before'][suite], self.surveys['after'][suite]
            self.check(suite+' identical case set', {r['name'] for r in a['scenarios']}=={r['name'] for r in b['scenarios']})
            self.check(suite+' identical survey tool', a['tool_sha256']==b['tool_sha256'])
            self.check(suite+' same sample/warmup lengths', a['configured_frames']==b['configured_frames'] and a['warmup_frames']==b['warmup_frames'])
            self.check(suite+' references exact previous report', b['reference_report_sha256']==sha(self.before/suite/'report.json'))
        self.before_source, self.before_rom = before_source, before_rom

    def summaries(self):
        paired, groups = [], {}
        for suite in SUITES:
            old = {r['name']:r for r in self.surveys['before'][suite]['scenarios']}
            new = {r['name']:r for r in self.surveys['after'][suite]['scenarios']}
            for name, a in old.items():
                b = new[name]
                row = dict(suite=suite, name=name, kind=a['kind'], seed=a['seed'],
                           requested_enemies=a['metadata'].get('requested_enemies'),
                           reference_match=b.get('reference_match'))
                for phase, item in (('before', a), ('after', b)):
                    row[phase] = dict(rates([item]), initial_enemies=item['initial']['roster']['enemies'],
                        ending_enemies=item['ending']['roster']['enemies'], oam_peak=item['oam_peak'],
                        fixture_point=item['metadata'].get('fixture_point'), camera=item['initial']['camera'])
                paired.append(row)
            for kind in sorted({r['kind'] for r in old.values()}):
                groups[suite+'/'+kind] = {phase:rates([r for r in data[suite]['scenarios'] if r['kind']==kind])
                                         for phase, data in self.surveys.items()}
        self.summary = dict(native_refresh_hz=HZ,
            metric='Eligible gameplay logic updates per video frame multiplied by native GBA refresh; not host wall-clock speed.',
            before_source=self.before_source, after_source=self.source, before_rom_sha256=self.before_rom,
            after_rom_sha256=sha(self.rom), groups=groups, cases=paired,
            survey_integrity_counts={phase:{s:[d['passed'],d['total']] for s,d in data.items()} for phase,data in self.surveys.items()},
            integrity_note='Integrity checks establish workload/capture validity; they are not frame-rate pass/fail thresholds.')
        dump(self.out/'measurements'/'summary.json', self.summary)
        columns = ['suite','name','kind','seed','requested_enemies']
        metrics = ['updates_per_second','eligible_frames','updates','missed','longest_repeat','initial_enemies','ending_enemies','oam_peak']
        columns += [phase+'_'+key for phase in ('before','after') for key in metrics]
        with (self.out/'measurements'/'cases.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
            for row in paired:
                flat={k:row[k] for k in columns[:5]}
                for phase in ('before','after'):
                    flat.update({phase+'_'+key:row[phase][key] for key in metrics})
                writer.writerow(flat)
        self.case_pairs={(r['suite'],r['name']):r for r in paired}

    def native(self):
        board = Image.new('RGB',(496,48+len(SELECTED)*188),BG)
        draw = ImageDraw.Draw(board)
        draw.text((8,8),'ACTUAL mGBA / native pixels / previous and optimized',fill=FG)
        draw.text((8,26),'Scenes retain live simulation; equal video age is not equal game age.',fill=DIM)
        panels = []
        for index,(suite,name,label) in enumerate(SELECTED):
            y = 48+index*188
            draw.text((8,y),label,fill=FG)
            record = dict(suite=suite,name=name,label=label,phases={})
            for j,(phase,root) in enumerate((('before',self.before),('after',self.after))):
                report = self.surveys[phase][suite]
                clip=next(c for c in report['clips'] if c['name']==name)
                target=self.out/'actual'/phase/name
                self.check(phase+'/'+name+' GIF recorded hash',sha(root/suite/clip['gif'])==clip['gif_sha256'])
                self.copy(root/suite/clip['gif'],target/'motion.gif')
                for i,row in enumerate(clip['frames']):
                    source=safe(root/suite,row['file'])
                    self.check(phase+'/'+name+' native frame hash '+str(i),sha(source)==row['sha256'])
                    with Image.open(source) as im:self.check(phase+'/'+name+' native size '+str(i),im.size==(240,160))
                    self.copy(source,target/'frames'/('%03d.png'%i))
                sample=0
                for i,frame in enumerate(ImageSequence.Iterator(Image.open(target/'motion.gif'))):
                    duration=frame.info['duration'];hold=clip['duration_ms']
                    self.check(phase+'/'+name+' GIF holds '+str(i),duration>=hold and duration%hold==0)
                    for _ in range(duration//hold):
                        raw=Image.open(target/'frames'/('%03d.png'%(sample*clip['sample_step'])))
                        self.check(phase+'/'+name+' exact sampled RGB '+str(sample),rgb_sha(frame)==rgb_sha(raw));sample+=1
                self.check(phase+'/'+name+' complete GIF schedule',sample==len(clip['frames'][::clip['sample_step']]))
                self.copy(target/'frames'/'000.png',target/'native.png')
                image=Image.open(target/'native.png').convert('RGB');at=(8+j*248,y+18);board.paste(image,at)
                panels.append(dict(file=str((target/'native.png').relative_to(self.out)),rectangle=[at[0],at[1],at[0]+240,at[1]+160],RGB_sha256=rgb_sha(image)))
                record['phases'][phase]=dict(gif=str((target/'motion.gif').relative_to(self.out)),
                    raw_frames=len(clip['frames']),sample_step=clip['sample_step'],duration_ms=clip['duration_ms'],frames=clip['frames'])
            self.selected.append(record)
        path=self.out/'actual-before-after.png';board.save(path)
        reopened=Image.open(path)
        for i,p in enumerate(panels):self.check('literal actual comparison panel '+str(i),rgb_sha(reopened.crop(p['rectangle']))==p['RGB_sha256'])
        dump(self.out/'actual'/'manifest.json',dict(kind='Untouched native mGBA framebuffers and exact sampled GIFs; no interpolation or repainting.',cases=self.selected,board_panels=panels))

    def regressions(self):
        path=self.reg_root/'report.json';report=json.loads(path.read_text())
        self.check('independent regression checks pass',report['passed']==report['total'])
        self.check('independent regression is exact released source/ROM',report['source_commit']==self.source and report['rom_sha256']==sha(self.rom))
        self.check('regression uses exact previous ROM',report['before_rom_sha256']==self.before_rom)
        target=self.out/'validation'/'regression'
        self.copy(path,target/'report.json')
        for suite in report.get('suites',[]):
            self.check('underlying regression suite '+suite['name'],suite['returncode']==0 and suite['passed']==suite['total'])
            for key in ('report','log'):
                if suite.get(key):
                    source=safe(self.reg_root,suite[key])
                    if key=='report' and suite.get('report_sha256'):
                        self.check('suite report hash '+suite['name'],sha(source)==suite['report_sha256'])
                    self.copy(source,safe(target,suite[key]))
        native=json.loads((self.reg_root/'isolated-native.json').read_text())
        self.copy(self.reg_root/'isolated-native.json',target/'isolated-native.json')
        comparisons={}
        for row in native['cases']:
            source=safe(self.reg_root,row['file'])
            self.check('isolated native frame hash '+row['file'],sha(source)==row['sha256'])
            im=Image.open(source)
            self.check('isolated native RGB '+row['file'],im.size==(240,160) and rgb_sha(im)==row['RGB_sha256'])
            self.copy(source,safe(target,row['file']))
            key=(row['room'],row['seed'],row['cell'],tuple(row['camera']),row['clock'])
            comparisons.setdefault(key,{})[row['phase']]=row
        for key,pair in comparisons.items():
            self.check('fixed-logic identical actual RGB '+str(key),set(pair)=={'before','after'} and pair['before']['RGB_sha256']==pair['after']['RGB_sha256'])
        self.regression=report;self.native_pairs=len(comparisons)
        for spec in self.args.host:
            name,location=spec.split('=',1)
            assert re.fullmatch(r'[a-z0-9_-]+',name),name
            source=Path(location).resolve();data=json.loads(source.read_text())
            passed=data.get('passed')
            self.check('host algorithm report '+name,passed is True if isinstance(passed,bool) else isinstance(passed,int) and passed==data.get('total'))
            self.copy(source,self.out/'validation'/'host'/(name+'.json'))
            self.host_records.append(dict(name=name,file='validation/host/'+name+'.json',sha256=sha(source),
                method=data.get('method'),passed=data.get('passed'),total=data.get('total'),
                counts={key:data[key] for key in ('cases','counts','glitter_cases','map_cases','number_cases','animation','torches') if key in data}))

    def profile_data(self):
        if not self.args.profile_before and not self.args.profile_after:return
        assert self.args.profile_before and self.args.profile_after,'provide both instrumented profile roots'
        roots={'before':Path(self.args.profile_before).resolve(),'after':Path(self.args.profile_after).resolve()}
        for phase,root in roots.items():
            self.profiles[phase]={}
            for name in ('natural-b4a7-cell10.json','knights24.json'):
                path=root/name;data=json.loads(path.read_text())
                self.check(phase+' profiler explicitly instrumented '+name,data['instrumented'] is True)
                self.check(phase+' profiler is not production ROM '+name,data['rom_sha256'] not in (self.before_rom,sha(self.rom)))
                self.copy(path,self.out/'measurements'/'instrumented'/phase/name)
                self.profiles[phase][name]=data

    def graphs(self):
        os.environ.setdefault('MPLCONFIGDIR','/tmp/bartgame-performance-matplotlib')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        plt.rcParams.update({'font.size':10,'figure.dpi':150,'savefig.dpi':150,'axes.spines.top':False,'axes.spines.right':False})
        folder=self.out/'graphs';folder.mkdir(exist_ok=True)
        seeds=self.surveys['before']['broad']['seeds']
        fig,axes=plt.subplots(len(seeds),2,figsize=(9,3.5*len(seeds)),layout='constrained',squeeze=False)
        for i,seed in enumerate(seeds):
            for j,phase in enumerate(('before','after')):
                items=[r for r in self.surveys[phase]['broad']['scenarios'] if r['kind']=='natural' and r['seed']==seed]
                values=np.full((5,5),np.nan)
                for r in items:
                    cell=r['initial']['cell'];values[cell//5,cell%5]=r['update_ratio']*HZ
                self.check(phase+' heatmap covers25 rooms '+seed,len(items)==25 and np.isfinite(values).all())
                ax=axes[i,j];im=ax.imshow(values,vmin=0,vmax=HZ,cmap='viridis')
                ax.set_title(('Previous' if phase=='before' else 'Optimized')+' / seed'+seed)
                ax.set_xticks(range(5));ax.set_yticks(range(5));ax.set_xlabel('Room column');ax.set_ylabel('Room row')
                for y in range(5):
                    for x in range(5):ax.text(x,y,'%d: %.1f'%(y*5+x,values[y,x]),ha='center',va='center',fontsize=8,color='white' if values[y,x]<40 else '#101820')
        fig.colorbar(im,ax=axes.ravel().tolist(),label='Eligible gameplay updates per second (native limit59.73)')
        fig.suptitle('Natural forest room throughput / measured mGBA production ROMs')
        fig.savefig(folder/'natural-room-throughput.png',metadata={'Description':'Measurement figure; not game artwork.'});plt.close(fig)

        fig,axes=plt.subplots(1,2,figsize=(11,4.8),layout='constrained',sharey=True)
        families=sorted({r['metadata']['enemy_family'] for r in self.surveys['before']['throughput']['scenarios']})
        for ax,phase in zip(axes,('before','after')):
            for family in families:
                rows=sorted((r for r in self.surveys[phase]['throughput']['scenarios'] if r['metadata']['enemy_family']==family),key=lambda r:r['metadata']['requested_enemies'])
                ax.plot([r['metadata']['requested_enemies'] for r in rows],[r['update_ratio']*HZ for r in rows],marker='o',label=family)
            ax.axhline(HZ,color='#606060',linestyle=':',linewidth=1);ax.set_ylim(0,63);ax.set_xticks([4,8,12,16,24]);ax.set_xlabel('Requested enemies (synthetic fixtures)')
            ax.set_title('Previous' if phase=='before' else 'Optimized');ax.grid(axis='y',alpha=.2)
        axes[0].set_ylabel('Eligible gameplay updates per second');axes[1].legend(loc='lower left',fontsize=8)
        fig.suptitle('Live enemy AI, no player offense / actual initial and final counts in CSV')
        fig.savefig(folder/'synthetic-throughput.png');plt.close(fig)

        fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
        for ax,(suite,name,label) in zip(axes,SELECTED):
            for phase,color in (('before','#a04040'),('after','#207060')):
                row=next(r for r in self.surveys[phase][suite]['scenarios'] if r['name']==name)
                cumulative=np.cumsum([s['logic_delta'] if s['expected_play'] else 0 for s in row['samples']])
                ax.plot((np.arange(len(cumulative))+1)/HZ,cumulative,label=phase,color=color)
            ax.set_title(label,fontsize=10);ax.set_xlabel('Video time (seconds)');ax.set_ylabel('Completed eligible game updates');ax.legend();ax.grid(alpha=.2)
        fig.suptitle('Actual game-age traces / repeated video frames remain in the measurement')
        fig.savefig(folder/'selected-timing.png');plt.close(fig)
        if self.profiles:
            keys=('total','tile_animation','camera_dark','glitter','player_draw','enemies_draw','hud')
            labels=('Total (overlaps below)','Tile animation','Camera / unlit torches','Both glitter passes','Bloom draw / visibility','Enemy draw / depth','HUD')
            fig,axes=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
            for ax,name in zip(axes,('natural-b4a7-cell10.json','knights24.json')):
                for i,phase in enumerate(('before','after')):
                    data=self.profiles[phase][name]['summary']
                    values=[(data['glitter_front']['mean']+data['glitter_back']['mean'] if key=='glitter' else data[key]['mean'])/1000 for key in keys]
                    ax.barh(np.arange(len(keys))+(i-.5)*.34,values,height=.32,label=phase,color=('#a04040','#207060')[i])
                ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis();ax.set_xlabel('Mean instrumented CPU cycles (thousands)');ax.legend();ax.grid(axis='x',alpha=.2)
                ax.axvline(280.896,color='#505050',linestyle=':',label='one video frame');ax.set_title(name.removesuffix('.json'))
            fig.suptitle('Development-only timer profiles / different instrumented ROMs, not release FPS')
            fig.savefig(folder/'instrumented-phases.png');plt.close(fig)
        self.graph_files=sorted(str(p.relative_to(self.out)) for p in folder.glob('*.png'))

    def release_files(self):
        self.release.mkdir(parents=True,exist_ok=True)
        stem='performance-'+self.source[:7];romname=stem+'.gba'
        self.copy(self.rom,self.release/romname)
        text=('BARTGAME performance build\n\nOriginal standalone GBA game; no commercial base ROM required.\n'
              'Source: '+self.source+'\nROM SHA256: '+sha(self.rom)+'\n'
              'Production PROFILE=0; no profiling timer code or counters.\n'
              'Selected native artwork, enemy counts/AI, action clocks and game rules retained.\n'
              'A/B/L use assigned tools; Start opens/closes bag; R changes bag page.\n')
        (self.release/'README.txt').write_text(text)
        checksum=sha(self.rom)+'  '+romname+'\n';(self.release/'SHA256SUMS').write_text(checksum)
        archive=self.release/(stem+'.zip')
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in (romname,'README.txt','SHA256SUMS'):
                info=zipfile.ZipInfo(name,(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                z.writestr(info,(self.release/name).read_bytes())
        with zipfile.ZipFile(archive) as z:
            self.check('ZIP exact production ROM',hashlib.sha256(z.read(romname)).hexdigest()==sha(self.rom))
            self.check('ZIP checksum matches',z.read('SHA256SUMS').decode()==checksum)
        self.release_record=dict(directory=str(self.release.relative_to(REPO)),rom=romname,rom_sha256=sha(self.rom),rom_bytes=self.rom.stat().st_size,
                                 zip=archive.name,zip_sha256=sha(archive),zip_bytes=archive.stat().st_size)
        prefix='https://raw.githubusercontent.com/natertott/bartgame/'+self.args.branch+'/'+str(self.release.relative_to(REPO))+'/'
        (self.release/'README.md').write_text('# BARTGAME performance build\n\n'
            '[Download ROM]('+prefix+romname+') · [Download ZIP]('+prefix+archive.name+')\n\n'
            '[Actual measurements and recordings](../../performance-review/README.md).\n\n'
            'Game source `'+self.source+'`; normal `make` selects `PROFILE=0`. '
            'The timer-instrumented diagnosis ROM is not included.\n\n'
            '| File | Bytes | SHA256 |\n| --- | ---: | --- |\n'
            '| '+romname+' | '+str(self.rom.stat().st_size)+' | `'+sha(self.rom)+'` |\n'
            '| '+archive.name+' | '+str(archive.stat().st_size)+' | `'+sha(archive)+'` |\n')

    def documents(self):
        groups=self.summary['groups'];lines=['# Measured performance improvements','',
            'The optimized build removes repeated renderer/terrain work while retaining the selected native '
            'artwork, glitter, enemy AI/populations and action rules. The production ROM is measured in actual '
            'mGBA runs; separate development-only timer profiles explain CPU cost.','',
            '[Download the production ROM/ZIP]('+os.path.relpath(self.release,self.out)+'/README.md) · '
            '[Complete measurements](measurements/README.md) · [Regression evidence](validation/README.md)','',
            '## Actual production throughput','',
            '“Updates/s” means completed eligible game updates per video frame multiplied by the native '
            'GBA refresh rate59.7275Hz. It is not the emulator host machine’s speed. Paused menus, named '
            'dialogue, shops and room transitions are excluded from gameplay throughput and recorded separately.','',
            '| Matched workload | Cases | Previous updates/s | Optimized updates/s | Missed updates, previous → optimized |',
            '| --- | ---: | ---: | ---: | ---: |']
        for key,label in (('broad/natural','Natural forest rooms, three seeds'),('broad/drain','Drain'),('broad/interior','Generated mystery interiors'),
                          ('broad/actions','Real item/action contexts'),('broad/stress','Synthetic enemies, combat inputs'),('throughput/stress-throughput','Synthetic enemies, no player offense'),('steady/natural','Room10 after120 ordinary warmup frames')):
            a,b=groups[key]['before'],groups[key]['after']
            lines.append('| '+label+' | '+str(a['cases'])+' | %.2f | %.2f | %d → %d |'%(a['updates_per_second'],b['updates_per_second'],a['missed'],b['missed']))
        lines += ['', 'These are weighted rates from the sampled eligible frames. Each ordinary workload lasts180 '
            'video frames; the finite corpus does not establish a universal60FPS bound for every future room, '
            'enemy/effect combination or area. Faster runs advance more actual simulation in the same video '
            'time. Planned player floor positions match the reference; camera and live enemy states are not forced '
            'to manufacture an identical screenshot. Per-case initial/final rosters and match flags are retained.','',
            '![Measured natural room heatmap](graphs/natural-room-throughput.png)','',
            '![Synthetic no-offense throughput](graphs/synthetic-throughput.png)','',
            '## Native recordings','',
            '![Actual previous and optimized scenes](actual-before-after.png)','']
        for suite,name,label in SELECTED:
            pair=self.case_pairs[(suite,name)];a,b=pair['before'],pair['after']
            lines += ['**'+label+':** %.2f → %.2f updates/s; missed%d → %d. '%(a['updates_per_second'],b['updates_per_second'],a['missed'],b['missed'])
                      +'Actual enemies start/end: previous%d/%d, optimized%d/%d.'%(a['initial_enemies'],a['ending_enemies'],b['initial_enemies'],b['ending_enemies']), '',
                '| Previous | Optimized |','| --- | --- |',
                '| ![Previous actual run](actual/before/'+name+'/motion.gif) | ![Optimized actual run](actual/after/'+name+'/motion.gif) |','']
        lines += ['Each GIF samples every sixth raw native frame with100ms viewing holds, approximately real '
            'native playback. Repeated video frames remain repeated. All180 original frames per selected run '
            'and their video/game ages are available in the [native manifest](actual/manifest.json). '
            'No pixels, AI timers, enemy HP or simulation clocks are replaced for these recordings. Health '
            'restoration, full inventory, developer navigation and explicitly replaced stress rosters are disclosed fixtures.','',
            '![Actual game-age traces](graphs/selected-timing.png)','',
            '## What consumed the frame budget','',
            'Room-dependent work included repeated full-room unlit-torch searches, software division in tile '
            'animation scheduling, repeated tree-depth/visibility queries, room-wide glitter scans and object '
            'overlap tests on unrelated actor slots. Equivalent cached/indexed queries, packed native-row tests '
            'and earlier exact viewport/kind rejection remove that repeated work. No animation frame, glitter '
            'site, enemy update or monster is removed to achieve the measured result.','']
        if self.profiles:
            lines += ['![Separate instrumented CPU diagnosis](graphs/instrumented-phases.png)','',
                'These timer measurements use separate instrumented development ROMs and include profiling '
                'overhead. The total overlaps the displayed child phases; do not add the bars. Timer-ROM '
                'samples support diagnosis, while the production reports above establish experienced throughput. '
                'Only the uninstrumented production ROM is downloadable.','']
        lines += ['## Preserved behavior and visual output','',
            'The independent frozen-source regression passes **%d/%d** and retains **%d matched actual RGB views**. '%(self.regression['passed'],self.regression['total'],self.native_pairs)
            +'Separate host differential reports compare actual C routines for actor/object painting, native '
            'visibility, glitter/HUD, torch invalidation and animation/DMA scheduling. Their fixture counts '
            'have different units and are not added to the regression count.','',
            'The original authored art and resolved native payloads are unchanged. Fixed-logic native comparisons '
            'separately establish visual equivalence; the throughput recordings deliberately do not claim '
            'identical game state at equal video age. See [all raw reports and limits](validation/README.md).','',
            'Production source `'+self.source+'`; ROM SHA256 `'+sha(self.rom)+'`.','']
        (self.out/'README.md').write_text('\n'.join(lines))
        rawlinks=['- ['+r['phase']+' '+r['suite']+' / complete raw JSON.gz]('+Path(r['file']).name+') — original SHA256 `'+r['original_sha256']+'`.' for r in self.raw_records]
        menus={phase:[r for r in reports['broad']['transitions'] if r.get('kind')=='menu'] for phase,reports in self.surveys.items()}
        menurows=['| Target | Previous video frames | Optimized video frames |','| --- | ---: | ---: |']
        old={r['target']:r for r in menus['before']};new={r['target']:r for r in menus['after']}
        for target,a in old.items():menurows.append('| '+target+' | '+str(a['video_frames'])+' | '+str(new[target]['video_frames'])+' |')
        text=['# Complete performance measurements','',
            '[Summary JSON](summary.json) and [all paired case metrics CSV](cases.csv) expose every measured case. '
            'The following lossless gzip files retain the original complete pretty-printed JSON, every raw '
            'video/game-age sample, initial/periodic/final rosters, fixtures, transition records and integrity checks. '
            'Decompressed byte hashes are recorded in the [index](index.json).','',*rawlinks,'',
            '## Observed menu input-to-state latency','',*menurows,'',
            'These are observed video-frame counts under the fixed real-input script, including its minimum '
            'three-frame detection schedule. They are not idle gameplay FPS. Cold page drawing, room '
            'generation/fades and modal states remain separate records in the broad report.','',
            'Graphs are scientific measurement artifacts generated with Matplotlib. They are not screenshots '
            'or new game artwork. All rates derive from eligible logic updates divided by eligible video '
            'frames, multiplied by262144/4389Hz.','']
        (self.out/'measurements'/'README.md').write_text('\n'.join(text))
        hostlinks=['- ['+r['name']+'](host/'+r['name']+'.json): its original schema, counts and source hashes.' for r in self.host_records]
        (self.out/'validation'/'README.md').write_text('# Performance regression and provenance\n\n'
            '[Independent frozen-ROM regression](regression/report.json) includes authored/resolved-art scope, '
            'gameplay/UI/save suites and24 matched native RGB views. Underlying suite reports/logs are '
            'preserved with their original counts; they are not additional disjoint tests to sum. '
            '[Native comparison manifest](regression/isolated-native.json) records all48 before/after '
            'untouched240×160 views and their hashes.\n\n'
            +'\n'.join(hostlinks)+'\n\n'
            'Host differential checks establish equivalent routines under their disclosed fixtures. They do '
            'not measure GBA speed, exhaust every possible game state or replace production timing. '
            '[Frozen build records](frozen/) pin production source, inputs and linked symbols. '
            '[Publication QA](publication-qa.json) verifies lossless reports, exact native/GIF/crop pixels, '
            'release identity and local links.\n')
        dump(self.out/'measurements'/'index.json',dict(raw=self.raw_records,graphs=self.graph_files,
            host_reports=self.host_records,source_commit=self.source,rom_sha256=sha(self.rom),gallery_tool_sha256=TOOL_SHA,
            instrumented_note='Only JSON CPU profiles are published. Development-only profiling binaries are excluded from downloads.'))

    def finish(self):
        # The QA report links to itself. Reserve its destination before the
        # link scan, then overwrite it with the completed substantive report.
        qa_path=self.out/'validation'/'publication-qa.json'
        if not qa_path.exists():dump(qa_path,{'status':'pending complete publication checks'})
        for root in (self.out,self.release):
            for path in root.rglob('*.md'):
                for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                    href=match.group(1).split('#')[0]
                    if not href or re.match(r'[a-z]+://',href):continue
                    self.check('local link '+str(path.relative_to(REPO))+' -> '+href,(path.parent/href).exists())
        dump(qa_path,dict(passed=sum(r['passed'] for r in self.qa),total=len(self.qa),checks=self.qa,
            source_commit=self.source,rom_sha256=sha(self.rom),tool_sha256=TOOL_SHA))
        files=[]
        for root in (self.out,self.release):
            for path in sorted(root.rglob('*')):
                if path.is_file() and path.name!='publication-manifest.json':
                    files.append(dict(file=str(path.relative_to(REPO)),bytes=path.stat().st_size,sha256=sha(path)))
        manifest=dict(source_commit=self.source,before_source=self.before_source,rom_sha256=sha(self.rom),
            tool_sha256=TOOL_SHA,release=self.release_record,regression_checks=[self.regression['passed'],self.regression['total']],
            native_RGB_pairs=self.native_pairs,publication_checks=[len(self.qa),len(self.qa)],files=files,self_manifest_excluded=True)
        dump(self.out/'publication-manifest.json',manifest)
        print(json.dumps(dict(source=self.source,release=self.release_record,files=len(files),
            total_bytes=sum(r['bytes'] for r in files),publication_checks=[len(self.qa),len(self.qa)],
            manifest_sha256=sha(self.out/'publication-manifest.json'))))

    def run(self):
        self.freeze();self.reports();self.summaries();self.native();self.regressions()
        self.profile_data();self.graphs();self.release_files();self.documents();self.finish()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--before',required=True);ap.add_argument('--after',required=True)
    ap.add_argument('--bundle',required=True);ap.add_argument('--regression',required=True)
    ap.add_argument('--host',action='append',default=[],metavar='NAME=REPORT')
    ap.add_argument('--profile-before');ap.add_argument('--profile-after')
    ap.add_argument('--out',default=str(REPO/'performance-review'))
    ap.add_argument('--branch',default='performance-optimization')
    Publisher(ap.parse_args()).run()


if __name__=='__main__':main()
