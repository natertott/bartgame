#!/usr/bin/env python3
"""Independently verify world preservation and native UI bytes for layout studies.

The final-room baseline already has its independently decoded1,554 native
frames. Every new ROM must retain its exact resolved world data. New UI ink,
frame/marker/cursor data is decoded from actual4bpp bytes against native source;
this script never imports the asset builder or its packing/dedup functions.
"""
import argparse,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
from sewer_concept_audit import NativeRom,decode_8x8,decode_sprite
ROOT=Path(__file__).resolve().parents[1]
UI_SHEETS={'uimarks','cursor','huditems'}
UI_ARRAYS={'ui_tiles','hud_tiles','huditems_frame_pal'}
BG_SKINS={'ui','menu','map','hud'}
OBJ_SKINS={'ui','uikit'}
SHA=lambda b:hashlib.sha256(b).hexdigest()

def source(ui):
    # Clean process: art modules intentionally cache the chosen skin at import.
    code='import drain_ui_audit; drain_ui_audit.source_export('+str(ui)+')'
    env={**os.environ,'BART_UI':str(ui),'BART_SEWER':'9','BART_MENU':'0'}
    return json.loads(subprocess.check_output([sys.executable,'-c',code],cwd=ROOT/'tools',env=env,text=True))

class Audit:
    def __init__(self,args):self.args=args;self.base=NativeRom(args.baseline);self.rows=[];self.details=[];self.sources={}
    def check(self,v,g,n,ok,detail=None):
        row={'variant':v,'group':g,'name':n,'passed':bool(ok)}
        if detail is not None:row['detail']=detail
        self.rows.append(row)
        if not ok:print('FAIL',v,g,n,detail,flush=True)
    def equal(self,v,g,n,a,b):self.check(v,g,n,a==b,None if a==b else {'before':SHA(a),'after':SHA(b),'before_bytes':len(a),'after_bytes':len(b)})
    def snapshot(self):
        return {str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in sorted((ROOT/'art').glob('*')) if p.suffix in ('.py','.json')}
    def world(self,v,rom):
        before=self.base
        self.check(v,'identifiers','all final picture IDs exact',rom.tile_ids==before.tile_ids)
        self.check(v,'identifiers','all sheet IDs exact',rom.sheet_ids==before.sheet_ids)
        for area in ('forest','myst','sewer'):
            a,b=before.tileset(area),rom.tileset(area)
            for key in ('tile_count','palette_count'):self.check(v,'world',area+'.'+key,a[key]==b[key],b[key])
            for key in ('tiles','map','palettes'):self.equal(v,'world',area+'.'+key,a[key],b[key])
            self.check(v,'world',area+' exact animation data/clocks',a['animations']==b['animations'])
            self.check(v,'budget',area+' resident <=1024',b['tile_count']<=1024,b['tile_count'])
        for name in before.sheet_ids:
            a,pix=before.sheet(name);b,other=rom.sheet(name)
            self.check(v,'sheet_contract',name,a==b)
            if name not in UI_SHEETS:self.equal(v,'world_sprite',name,pix,other)
        skip={'tilesets','sheets','pal_bg','pal_obj','room_defs'}|UI_ARRAYS
        for name in before.sections:
            if name in skip or name.startswith(('sheet_','tileset_','tile_anim')):continue
            self.check(v,'scalar',name+' exists',name in rom.sections)
            if name in rom.sections:self.equal(v,'scalar',name,before.array(name),rom.array(name))
        # RoomDef contains relocated pointers; compare its physical header and
        # exact resolved array targets rather than pointer-address bytes.
        self.check(v,'room_descriptor','room count exact',before.defs['ROOM_COUNT']==rom.defs['ROOM_COUNT'])
        contract=json.loads((ROOT/'art/reboot_contracts.json').read_text())['rooms']
        for i,record in enumerate(contract):
            a=struct.unpack('<BB2xIIIB3x',before.array('room_defs')[i*20:(i+1)*20])
            b=struct.unpack('<BB2xIIIB3x',rom.array('room_defs')[i*20:(i+1)*20])
            self.check(v,'room_descriptor',record['name']+' dimensions/object count',(a[0],a[1],a[5])==(b[0],b[1],b[5]))
            for index,field in ((2,'ground'),(3,'overlay'),(4,'objects')):
                symbol='room_'+record['name']+'_'+field
                self.check(v,'room_descriptor',symbol+' resolves exact source array',b[index]==rom.symbols.get(symbol,0))
        for array,prefix,allowed in [('pal_bg','PAL_BG_',BG_SKINS),('pal_obj','PAL_OBJ_',OBJ_SKINS)]:
            count=before.defs['PAL_BG_COUNT' if array=='pal_bg' else 'PAL_OBJ_COUNT'];ex={before.defs[prefix+n.upper()] for n in allowed}
            for bank in range(count):
                if bank not in ex:self.equal(v,'world_palette',array+str(bank),before.array(array)[32*bank:32*bank+32],rom.array(array)[32*bank:32*bank+32])
    def ui(self,v,rom,expected):
        for bank,array in [('kit','ui_tiles'),('hud','hud_tiles')]:
            raw=rom.array(array);self.check(v,'native_ui',bank+' tile count',len(raw)==len(expected[bank])*32)
            for i,(name,pixels) in enumerate(expected[bank].items()):self.equal(v,'native_ui',bank+'.'+name,bytes.fromhex(pixels),bytes(decode_8x8(raw[i*32:i*32+32])))
        for name in UI_SHEETS:
            row=expected['sheets'][name];meta,raw=rom.sheet(name);stride=meta['frame_tiles']*32
            self.check(v,'native_ui',name+' source canvas',meta['width']==row['w'] and meta['height']==row['h'])
            self.check(v,'native_ui',name+' frame count',meta['tile_count']==row['frame_count']*meta['frame_tiles'])
            self.check(v,'native_ui',name+' primary palette slot',meta['pal']==rom.defs['PAL_OBJ_'+row['pal'].upper()])
            if row.get('frame_pal'):
                pal_slots=bytes(rom.defs['PAL_OBJ_'+row['frame_pal'][k].upper()] for k in row['frame_ids'])
                self.equal(v,'native_ui',name+' per-frame palette slots',pal_slots,rom.array(name+'_frame_pal'))
            for frame,pixels in row['frames'].items():
                index=rom.defs['F_'+name.upper()+'_'+frame.upper()]
                self.equal(v,'native_ui',name+'.'+frame,bytes.fromhex(pixels),decode_sprite(raw[index*stride:(index+1)*stride],row['w'],row['h']))
        for group,array,prefix in [('bg_palettes','pal_bg','PAL_BG_'),('obj_palettes','pal_obj','PAL_OBJ_')]:
            for name,colors in expected[group].items():
                bank=rom.defs[prefix+name.upper()]
                self.equal(v,'native_palette',group+'.'+name,struct.pack('<16H',*colors),rom.array(array)[bank*32:bank*32+32])
        self.equal(v,'font','native widths',bytes(expected['font_widths']),rom.array('vwf_w'))
        self.equal(v,'font','native glyph rows',bytes(expected['font_bits']),rom.array('vwf_bits'))
    def run(self):
        snapshot=self.snapshot();builds=json.loads((Path(self.args.work)/'builds.json').read_text())
        for build in builds:
            v=build['variant'];rom=NativeRom(Path(self.args.work)/f'v{v}');freeze=json.loads((rom.directory/'freeze.json').read_text());ui=freeze['ui'];layout=freeze.get('menu',0)
            self.check(v,'provenance','ROM exact freeze hash',SHA(rom.rom)==freeze['rom_sha256'])
            self.check(v,'provenance','every native source input unchanged',all(freeze['source_file_sha256'].get(k)==d for k,d in snapshot.items()))
            code=freeze.get('code_file_sha256',{})
            self.check(v,'provenance','code inputs recorded',bool(code))
            for name,digest in code.items():
                current=(ROOT/name).read_bytes()
                self.check(v,'code_provenance',name+' current hash',SHA(current)==digest)
                committed=subprocess.check_output(['git','show',freeze['source_commit']+':bartgame/'+name],cwd=ROOT)
                self.check(v,'code_provenance',name+' equals frozen git source',current==committed)
            self.check(v,'profile','UI profile',rom.defs['BART_UI_VARIANT']==ui,ui)
            self.check(v,'profile','menu layout profile',rom.defs.get('BART_MENU_VARIANT',0)==layout,layout)
            self.check(v,'profile','final Drain unchanged',rom.defs['BART_SEWER_VARIANT']==9)
            self.world(v,rom)
            if ui not in self.sources:self.sources[ui]=source(ui)
            self.ui(v,rom,self.sources[ui])
            rows=[r for r in self.rows if r['variant']==v]
            self.details.append({'variant':v,'ui':ui,'menu':layout,'rom_sha256':SHA(rom.rom),'checks':len(rows),'passed':sum(r['passed'] for r in rows)})
            print('VARIANT',v,sum(r['passed'] for r in rows),'/',len(rows),flush=True)
        # The previous six native skins are archival design choices. Compare the
        # current painter outputs to independently decoded old frozen ROMs.
        oldroot=Path(self.args.old_skins)
        for ui in range(6):
            if ui not in self.sources:self.sources[ui]=source(ui)
            self.ui('old-'+str(ui),NativeRom(oldroot/f'v{ui}'),self.sources[ui])
        self.check(-1,'provenance','source snapshot remained unchanged throughout audit',snapshot==self.snapshot())
        report={'method':__doc__,'baseline_sha256':SHA(self.base.rom),'source_file_sha256':snapshot,'variants':self.details,'passed':sum(r['passed'] for r in self.rows),'total':len(self.rows),'failures':[r for r in self.rows if not r['passed']],'checks':self.rows,'limits':'This proves native art preservation/encoding and profile identity, not visual taste or runtime usability. Actual input/capture regressions are in the separate review.'}
        out=Path(self.args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');out.with_name('audit-summary.json').write_text(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True);return int(bool(report['failures']))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',default='/workspace/setup/ui-layout-studies');p.add_argument('--baseline',default='/workspace/setup/drain-ui-final/v0');p.add_argument('--old-skins',default='/workspace/setup/drain-ui-final');p.add_argument('--out',default='/workspace/setup/ui-layout-studies/audit.json');a=p.parse_args();return Audit(a).run()
if __name__=='__main__':raise SystemExit(main())
