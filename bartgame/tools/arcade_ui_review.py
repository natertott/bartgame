#!/usr/bin/env python3
"""Record every journal note under nine native appearance combinations in mGBA.

Valid private SRAM profile records unlock the entire catalogue solely to inspect
its UI. These are disclosed catalogue fixtures, not earned discoveries. Ordinary
A/B/L/R/D-pad controls open and browse the real cabinet. Terrain, enemy state,
VRAM, palettes, OAM and framebuffers are never assigned. Contact sheets append
labels outside untouched native240x160 framebuffers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from types import SimpleNamespace

from PIL import Image,ImageDraw
import probe as P
import critical_path as C
import bloom_probe as B
from arcade_journal_review import Review,profile,preferences,bytes_at

SHA=lambda b:hashlib.sha256(b).hexdigest()
STYLES=('Winebound','Mossbound','Ivory')
PALETTES=('Wine','Moss','Ivory')


class UIReview:
    def __init__(self,args):
        self.args=args;self.out=Path(args.out).resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.r=Review(SimpleNamespace(bundle=args.bundle,out=str(self.out/'helper'),suites=''))
        self.native=self.r.native;self.rows=[];self.media=[];self.scenes=[];self.context=None
        self.entries=[]
        for name,count in [('sItems',24),('sEnemies',9)]:
            match=re.search(r'^ \.rodata\.'+name+r'\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+\S*journal\.o$',self.native.linker,re.M)
            assert match,name
            at=int(match[1],16);assert int(match[2],16)==count*16
            data=[]
            for i in range(count):
                n,d,s,f,p,hp,touch=struct.unpack('<II5B3x',self.native.read(at+i*16,16))
                data.append(dict(name=self.string(n),description=self.string(d),sheet=s,frame=f,palette=p,hp=hp,touch=touch))
            self.entries.append(data)
        self.widths=self.native.array('vwf_w');self.first=self.native.defs['VWF_FIRST'];self.space=self.native.defs['VWF_SPACE']

    def string(self,at):
        out=bytearray()
        while len(out)<2048:
            b=self.native.read(at+len(out),1)[0]
            if not b:return out.decode('ascii')
            out.append(b)
        raise AssertionError('unterminated source text')

    def check(self,name,ok,detail=None):
        self.rows.append(dict(name=name,passed=bool(ok),context=self.context,detail=detail))
        if not ok:print('FAIL '+name,detail,flush=True)

    def snap(self,c,folder,name):
        folder.mkdir(parents=True,exist_ok=True);path=folder/(name+'.png');P.snap(c,str(path))
        self.media.append(dict(file=str(path.relative_to(self.out)),sha256=SHA(path.read_bytes()),size=[240,160],kind='untouched actual mGBA framebuffer'))
        return path

    def word_lines(self,s,width):
        lines=[]
        while s:
            i=px=brk=0
            while i<len(s):
                a=self.space if s[i]==' ' else self.widths[ord(s[i])-self.first]+1
                if s[i]==' ':brk=i
                if px+a-1>width and s[i]!=' ':break
                px+=a;i+=1
            if i<len(s):i=brk if brk else max(1,i)
            lines.append(s[:i]);s=s[i:].lstrip(' ')
        return lines

    def source_checks(self):
        for page,entries in enumerate(self.entries):
            for i,e in enumerate(entries):
                lines=self.word_lines(e['description'],136)
                self.check('source%d/%02d full notes fit native width/height'%(page,i),len(lines)<=(5 if page else 7),dict(lines=lines))
                if not page:
                    for sheet,table in [('SHEET_ITEMS','items_frame_pal'),('SHEET_PICK32','pick32_frame_pal')]:
                        if e['sheet']==self.native.defs[sheet]:
                            expected=self.native.array(table)[e['frame']]
                            self.check('source0/%02d uses actual world material palette'%i,e['palette']==expected,dict(expected=expected,actual=e['palette']))

    def actual_preview(self,c,page,index):
        st=self.r.arcade(c);e=self.entries[page][index]
        sid=st['PreviewSheet'];name=next(name for name,value in self.native.sheet_ids.items() if value==sid)
        meta,data=self.native.sheet(name);size=meta['frame_tiles']*32
        if sid==self.native.defs['SHEET_ICON32']:
            data=self.native.array('icon32_exact_tiles');pal=self.native.array('icon32_exact_pal')[e['frame']*32:(e['frame']+1)*32]
        else:pal=self.native.array('pal_obj')[e['palette']*32:(e['palette']+1)*32]
        pixels=data[e['frame']*size:(e['frame']+1)*size]
        actual=bytes_at(c,0x06010000+944*32,size);actualpal=bytes_at(c,0x05000200+6*32,32)
        self.check('actual%d/%02d native source frame and palette'%(page,index),
                   st['Detail']==1 and st['Cursor']==index and st['Seen']==1 and sid==e['sheet'] and
                   st['PreviewFrame']==e['frame'] and actual==pixels and actualpal==pal,
                   dict(state=st,pixel_sha256=SHA(actual),palette_sha256=SHA(actualpal)))
        obj=[o for o in B.oam(c) if o['tile']==944]
        self.check('actual%d/%02d preview separated from notes/header'%(page,index),
                   len(obj)==1 and obj[0]['pal']==6 and obj[0]['x']==48-meta['width']//2 and
                   obj[0]['y']==84-meta['height']//2 and obj[0]['x']>=16 and
                   obj[0]['x']+meta['width']<=80 and obj[0]['y']>=40 and obj[0]['y']+meta['height']<=128,obj)
        return st

    def catalogue(self):
        fullitems=(1<<24)-1;fullenemies=(1<<9)-1
        for style in range(3):
            for palette in range(3):
                self.context=dict(style=style,palette=palette)
                folder=self.out/('style%d-palette%d'%(style,palette))
                c=self.r.fresh(sram={0x7ec0:profile(fullitems,fullenemies,2),0x7f00:preferences(style,palette)})
                before_pixels=bytes_at(c,0x06010000+944*32,1024);before_pal=bytes_at(c,self.r.at('gPalObj')+6*32,32)
                self.r.cabinet(c)
                allocated=P.r16(c,self.r.at('sNextTile'))&65535
                self.check('style%d/palette%d actual preferences honored'%(style,palette),P.r8(c,self.r.at('gAppearanceStyle'))==style and P.r8(c,self.r.at('gAppearancePalette'))==palette)
                for page,count in [(0,24),(1,9)]:
                    if self.r.arcade(c)['Page']!=page:self.r.press(c,'R')
                    self.snap(c,folder,'page%d-index'%page)
                    if not self.r.arcade(c)['Detail']:self.r.press(c,'A')
                    for i in range(count):
                        current=self.r.arcade(c)['Cursor']
                        key='DOWN' if current<i else 'UP'
                        for _ in range(abs(i-current)):self.r.press(c,key)
                        self.r.run(c,4)
                        st=self.actual_preview(c,page,i)
                        file=self.snap(c,folder,'page%d-entry%02d'%(page,i))
                        self.scenes.append(dict(style=style,palette=palette,page=page,index=i,name=self.entries[page][i]['name'],file=str(file.relative_to(self.out)),state=st))
                    self.r.press(c,'B')
                self.check('style%d/palette%d catalogue allocates no world tiles'%(style,palette),(P.r16(c,self.r.at('sNextTile'))&65535)==allocated)
                self.r.press(c,'START');self.r.run(c,8)
                self.check('style%d/palette%d borrowed face window and palette restored'%(style,palette),
                           C.gstate(c)==1 and bytes_at(c,0x06010000+944*32,1024)==before_pixels and
                           bytes_at(c,self.r.at('gPalObj')+6*32,32)==before_pal)
                self.snap(c,folder,'return-to-drain')
                print('captured',STYLES[style],PALETTES[palette],flush=True)

    def sheet(self,name,rows,columns):
        width=columns*240;height=((len(rows)+columns-1)//columns)*180
        result=Image.new('RGB',(width,height),(12,17,25));draw=ImageDraw.Draw(result);draw.fontmode='1'
        for i,row in enumerate(rows):
            x=i%columns*240;y=i//columns*180
            result.paste(Image.open(self.out/row['file']).convert('RGB'),(x,y))
            draw.text((x+5,y+164),row['label'],fill=(243,227,174))
        file=self.out/(name+'.png');result.save(file)
        self.media.append(dict(file=file.name,sha256=SHA(file.read_bytes()),kind='native framebuffer contact sheet; labels occupy separate20px rows'))

    def finish(self):
        for page,name,cols in [(0,'all-items-winebound-native',4),(1,'all-enemies-winebound-native',3)]:
            selected=[dict(s,label='%02d %s'%(s['index'],s['name'])) for s in self.scenes if s['style']==s['palette']==0 and s['page']==page]
            self.sheet(name,selected,cols)
        selected=[dict(s,label=STYLES[s['style']]+' / '+PALETTES[s['palette']]) for s in self.scenes if s['page']==1 and s['index']==8]
        self.sheet('nine-appearance-combinations-native',selected,3)
        report=dict(method=__doc__,rom_sha256=SHA(self.native.rom),source_commit=(Path(self.args.bundle)/'source-commit.txt').read_text().strip(),
                    tool_sha256=SHA(Path(__file__).read_bytes()),helper_sha256=SHA(Path(__file__).with_name('arcade_journal_review.py').read_bytes()),
                    fixtures=['Private valid serialized journal profiles unlock24items/9enemies for catalogue coverage only. These are not claimed as earned discoveries.',
                              'Private valid serialized appearance records select all3frame constructions×3palettes before ordinary startup.',
                              'Player coordinate/facing placement on actual accessible cabinet approach; ordinary Up/A interaction opens real journal.',
                              'Every selection uses ordinary L/R/A/B/D-pad controls. No UI cursor, geometry, enemy state, palette, VRAM, OAM or framebuffer writes.'],
                    entries=self.entries,scenes=self.scenes,checks=self.rows,passed=sum(r['passed'] for r in self.rows),total=len(self.rows),media=self.media)
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True)
        return int(report['passed']!=report['total'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True);p.add_argument('--out',required=True)
    args=p.parse_args();r=UIReview(args);r.source_checks();r.catalogue();return r.finish()


if __name__=='__main__':raise SystemExit(main())
