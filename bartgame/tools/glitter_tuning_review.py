#!/usr/bin/env python3
"""Paired actual mGBA evidence for quieter decorative glitter.

Natural room layouts, tiles and palettes remain intact. Actor isolation, safe
positioning and inventory are readability fixtures. Ordinary simulation supplies
all clocks: no frame, palette, tile, OAM or framebuffer bytes are injected.
Hardware OAM determines sparkle count and period; decoded GPU strips independently
check decorative HUD cadence and the unchanged functional current-room blink.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import statistics
import struct
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageSequence
import probe as P
import bloom_probe as B
import critical_path as C
from art_reboot_review import NativeSuite
from sewer_concept_audit import NativeRom

SHA=lambda data:hashlib.sha256(data).hexdigest()


def read(c,at,n):
    return bytes(P.r8(c,at+i) for i in range(n))


def nm_symbols(bundle):
    result=subprocess.check_output(['arm-none-eabi-nm','-n',str(bundle/'bartgame.elf')],text=True)
    return {name:int(address,16) for address,name in re.findall(r'^([0-9a-fA-F]{8})\s+\w\s+(\S+)\s*$',result,re.M)}


def row_rgb(core,charbase,mapbase,y,x0,x1):
    """Read only the requested BG0 scanline pixels, not a replacement image."""
    values=[]
    for x in range(x0,x1):
        entry=P.r16(core,mapbase+((y//8)*32+x//8)*2)&65535
        xx=7-x%8 if entry&0x400 else x%8
        yy=7-y%8 if entry&0x800 else y%8
        tile=entry&1023
        ink=(P.r8(core,charbase+tile*32+yy*4+xx//2)>>((xx&1)*4))&15
        values.append(P.r16(core,0x05000000+(entry>>12)*32+ink*2)&65535 if tile and ink else -1)
    return tuple(values)


def map_ink(core,x,y):
    tile=1008+(y//8)*4+x//8
    value=P.r8(core,0x06010000+tile*32+(y%8)*4+(x%8)//2)
    return (value>>((x&1)*4))&15


def changes(values):
    indices=[i for i in range(1,len(values)) if values[i]!=values[i-1]]
    intervals=[b-a for a,b in zip(indices,indices[1:])]
    return dict(events=len(indices),indices=indices,intervals=dict(Counter(intervals)))


class Review:
    def __init__(self,args):
        self.args=args;self.bundle=Path(args.bundle).resolve();self.out=Path(args.out).resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        self.native=NativeRom(self.bundle);self.symbols=nm_symbols(self.bundle)
        self.checks=[];self.contexts=[];self.media=[]
        self.frames=args.frames;self.phase=args.phase
        self.period=64 if self.phase=='before' else 128
        self.rim_step=8 if self.phase=='before' else 16
        self.cap=24 if self.phase=='before' else 12
        P.MAP=str(self.bundle/'bartgame.map');P._syms=None

    def check(self,name,passed,detail=None):
        row=dict(name=name,passed=bool(passed))
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)

    def media_row(self,path,kind):
        row=dict(file=str(path.relative_to(self.out)),sha256=SHA(path.read_bytes()),kind=kind)
        self.media.append(row);return row

    def source_sites(self,c):
        count=P.r16(c,P.sym('gAmbientSiteCount'))&65535
        raw=read(c,self.symbols['sAmbientSites'],count*8)
        return [dict(index=i,x=x,y=y,phase=phase,foreground=fg,tx=tx,ty=ty)
                for i,(x,y,phase,fg,tx,ty) in enumerate(struct.iter_unpack('<hh4B',raw))]

    def selected_sites(self,c):
        count=P.r8(c,self.symbols['sAmbientViewCount'])
        raw=read(c,self.symbols['sAmbientView'],count*4)
        return [dict(index=site,material=material,
                     fractional=bool(fractional) if self.phase=='after' else False)
                for site,material,fractional in struct.iter_unpack('<HBB',raw)]

    def record_context(self,name):
        args=SimpleNamespace(rom=str(self.bundle/'bartgame.gba'),map=str(self.bundle/'bartgame.map'),
            assets_header=str(self.bundle/'assets.h'),out=str(self.out),seed='0xb4a7',only=None,match=None)
        suite=NativeSuite(args)
        suite.seed=11 if name=='cave' else 0xB4A7
        suite.enter(name);point=suite.spot(0,0);suite.reset(point,0,1)
        c=suite.c;pl=P.sym('gPl')
        for i,equipment in enumerate((1,5,4)):P.w8(c,pl+9+i,equipment)
        P.run(c,32)
        initial=dict(area=C.area(c),cell=C.cell(c),position=list(P.player_pos(c)),
                     camera=[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],seed=hex(suite.seed))
        sites=self.source_sites(c);selected=self.selected_sites(c)
        camera=initial['camera'];by_point={(site['x']-camera[0]-3,site['y']-camera[1]-3):site['index'] for site in sites}
        tile=P.r16(c,self.symbols['sAmbientTile'])&65535
        meta,_=self.native.sheet('glitter')
        frame_tiles=meta['frame_tiles'];sheet_tiles=meta['tile_count']
        selected_ids=[site['index'] for site in selected]
        states={i:[] for i in selected_ids};rows=[];rim=[];maprim=[];current=[];frames=[]
        folder=self.out/name;folder.mkdir(exist_ok=True)
        cb=0x06008000;mb=0x0600B800
        for tick in range(self.frames):
            c.run_frame();entries=B.oam(c)
            stars={}
            for entry in entries:
                if tile<=entry['tile']<tile+sheet_tiles:
                    key=(entry['x'],entry['y'])
                    if key in by_point:stars[by_point[key]]=(entry['tile']-tile)//frame_tiles
            for site in selected_ids:states[site].append(stars.get(site,0))
            top=row_rgb(c,cb,mb,1,83,116)+row_rgb(c,cb,mb,1,148,237)
            minimap_rim=tuple(map_ink(c,x,1) for x in range(2,22))
            here=C.cell(c) if C.area(c)!=0 else self.world_entry(c)
            ring=map_ink(c,2+(here%5)*4,2+(here//5)*4)
            rim.append(SHA(struct.pack('<%dh'%len(top),*top)))
            maprim.append(SHA(bytes(minimap_rim)));current.append(ring)
            row=dict(tick=tick,gFrame=P.r32(c,P.sym('gFrame')),logic=P.r32(c,P.sym('gGame')+8),
                     stars=stars,count=len(stars),selected_count=P.r8(c,self.symbols['sAmbientViewCount']),
                     oam_count=len(entries),hud_rim=rim[-1],map_rim=maprim[-1],current_ring=ring)
            rows.append(row)
            if tick%8==0:
                path=folder/('native-%03d.png'%tick);P.snap(c,str(path));frames.append(Image.open(path).convert('RGB'))
                self.media_row(path,'untouched native mGBA framebuffer')
        gif=folder/'motion.gif'
        frames[0].save(gif,save_all=True,append_images=frames[1:],duration=130,loop=0,optimize=False)
        self.media_row(gif,'native mGBA samples every8 frames,130ms inspection holds')
        # A screenshot sample is literal: GIF optimizer may coalesce repeated samples.
        check_frames=[]
        for image in ImageSequence.Iterator(Image.open(gif)):
            hold=image.info['duration']//130;check_frames.extend([image.convert('RGB').tobytes()]*hold)
        self.check(name+' GIF retains exact sampled native pixels',check_frames==[f.tobytes() for f in frames])
        deltas=Counter(b['logic']-a['logic'] for a,b in zip(rows,rows[1:]))
        self.check(name+' one native logic update per sampled video interval',deltas=={1:self.frames-1},dict(deltas))
        self.check(name+' selected star cap',all(r['selected_count']<=self.cap for r in rows),self.cap)
        self.check(name+' stable camera and selected scene',self.selected_sites(c)==selected and [P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))]==camera)
        self.check(name+' same real room throughout',C.area(c)==initial['area'] and C.cell(c)==initial['cell'])
        observed=[site for site,seq in states.items() if any(seq)]
        self.check(name+' contains visible native glitter',bool(observed),len(observed))
        self.check(name+' hardware star counts match decoded source states',all(r['count']<=len(selected) for r in rows))
        periods=[]
        selected_by_id={row['index']:row for row in selected}
        for site in observed:
            sequence=states[site]
            divisor=4 if selected_by_id[site]['fractional'] else 2
            self.check(name+' site%d repeats at%d video frames'%(site,self.period),sequence[:-self.period]==sequence[self.period:])
            self.check(name+' site%d is not a half-period pulse'%site,sequence[:-self.period//2]!=sequence[self.period//2:])
            self.check(name+' site%d has%dpercent bright duty'%(site,100//divisor),
                       sum(bool(v) for v in sequence)==self.frames//divisor)
            self.check(name+' site%d retains every drawn glitter stage'%site,
                       set(sequence)==set(range(sheet_tiles//frame_tiles)))
            periods.append(dict(site=site,period=self.period,fractional=selected_by_id[site]['fractional'],
                                lit_frames=sum(bool(v) for v in sequence),sequence=sequence))
        for label,values in [('HUD rim',rim),('map rim',maprim)]:
            timing=changes(values);intervals=timing['intervals']
            self.check(name+' '+label+' decorative step%d'%self.rim_step,
                       bool(intervals) and min(intervals)==self.rim_step and all(k%self.rim_step==0 for k in intervals),timing)
        blink=changes(current)
        if initial['area']!=0:
            self.check(name+' functional room blink remains32 frames',set(blink['intervals'])=={32},blink)
        row=dict(name=name,initial=initial,candidate_sites=sites,selected_sites=selected,
                 selected_count=len(selected),period=self.period,counts=dict(min=min(r['count'] for r in rows),
                 max=max(r['count'] for r in rows),mean=statistics.mean(r['count'] for r in rows)),
                 live_sites=len(observed),site_periods=periods,rim_timing=changes(rim),
                 map_rim_timing=changes(maprim),current_room_timing=blink,samples=rows,
                 gif=str(gif.relative_to(self.out)),native_sample_step=8)
        self.contexts.append(row)
        self.save(False)

    def world_entry(self,c):
        return P.r8(c,P.sym('gWorld')+4+25*13)

    def save(self,complete):
        report=dict(method=__doc__,phase=self.phase,complete=complete,
            source_commit=(self.bundle/'source-commit.txt').read_text().strip(),
            rom_sha256=SHA((self.bundle/'bartgame.gba').read_bytes()),
            tool_sha256=SHA(Path(__file__).read_bytes()),frames_per_context=self.frames,
            fixtures=['Original generated room layouts/art; seed0xb4a7, cave seed11.',
                      'Inventory, camera target and safe player position fixtures; unrelated actors isolated.',
                      'All native video/logic clocks run ordinarily; no gFrame or framebuffer injection.',
                      'Sprite-state and HUD-strip reads are GPU diagnostics, separate from screenshots.'],
            contexts=self.contexts,media=self.media,checks=self.checks,
            passed=sum(r['passed'] for r in self.checks),total=len(self.checks))
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        return report

    def run(self):
        for name in self.args.contexts.split(','):self.record_context(name)
        r=self.save(True);print('%d/%d'%(r['passed'],r['total']));return int(r['passed']!=r['total'])


def compare(before,after,out):
    a=json.loads((Path(before)/'report.json').read_text());b=json.loads((Path(after)/'report.json').read_text())
    rows=[]
    def check(name,passed,detail=None):rows.append(dict(name=name,passed=bool(passed),detail=detail))
    for phase,d in [('before',a),('after',b)]:check(phase+' capture passed',d['complete'] and d['passed']==d['total'])
    check('same immutable capture helper',a['tool_sha256']==b['tool_sha256'])
    for old,new in zip(a['contexts'],b['contexts']):
        name=old['name'];check(name+' same scene',old['initial']==new['initial'],[old['initial'],new['initial']])
        check(name+' all source candidate sites retained',old['candidate_sites']==new['candidate_sites'])
        selected=[dict(row) for row in old['selected_sites'][::2]]
        if len(old['selected_sites'])&1:selected[-1]['fractional']=True
        check(name+' exactly alternating prior view subset with fractional odd remainder',new['selected_sites']==selected)
        check(name+' selected count represents half the prior view',new['selected_count']==(old['selected_count']+1)//2,[old['selected_count'],new['selected_count']])
        check(name+' average visible glitter is exactly half',new['counts']['mean']*2==old['counts']['mean'],
              [old['counts']['mean'],new['counts']['mean']])
        check(name+' full ambient cycle doubles',new['period']==old['period']*2)
    r=dict(method='Paired real mGBA glitter density/cadence comparison.',before_rom=a['rom_sha256'],after_rom=b['rom_sha256'],
           checks=rows,passed=sum(x['passed'] for x in rows),total=len(rows))
    Path(out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return int(r['passed']!=r['total'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle');ap.add_argument('--out',required=True);ap.add_argument('--phase',choices=('before','after'))
    ap.add_argument('--frames',type=int,default=512);ap.add_argument('--contexts',default='drain,forest,blight,cave')
    ap.add_argument('--compare',nargs=2,metavar=('BEFORE','AFTER'))
    a=ap.parse_args()
    if a.compare:return compare(*a.compare,a.out)
    if not a.bundle or not a.phase:ap.error('--bundle and --phase are required for capture')
    if a.frames<256 or a.frames%128:ap.error('--frames must cover whole128-frame cycles, at least256')
    return Review(a).run()


if __name__=='__main__':raise SystemExit(main())
