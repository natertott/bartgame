#!/usr/bin/env python3
"""Exercise title appearance controls and all nine native combinations in mGBA.

No preference/menu state variable is written. Initial blank/corrupt SRAM,
inventory, seed and safe NPC positions are declared fixtures. Menus, dialogue
and shops are opened through ordinary buttons. Source framebuffer pixels are
saved unchanged. The final save/migration test uses the existing independent
save_probe's declared serialized legacy-save fixtures.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw, ImageFont
import probe as P
import bloom_probe as B
import critical_path as C
from sewer_concept_review import position

SRAM=0x0E000000
PREFS=SRAM+0x7F00
NAMES=('Winebound Folio','Mossbound Fieldbook','Ivory Reliquary')
PALETTES=('Wine','Moss','Ivory')

def bytes_at(c,addr,n):return bytes(P.r8(c,addr+i) for i in range(n))
def digest(data):return hashlib.sha256(data).hexdigest()

class Review:
    def __init__(self,args):
        self.args=args;self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=True)
        P.ROM=str(Path(args.rom).resolve())
        self.defs=B.configure(SimpleNamespace(map=args.map,assets_header=args.assets_header))
        self.checks=[];self.captures=[];self.reference_hud=None
    def check(self,name,condition,detail=None):
        row={'name':name,'passed':bool(condition)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not condition:raise AssertionError(row)
    def val(self,name):return P.r8(self.c,P.sym(name))
    def blank_boot(self):
        self.c=P.boot(rom=P.ROM,frames=0,start=False)
        for base in (SRAM,PREFS):
            for i in range(12):P.w8(self.c,base+i,0)
        P.run(self.c,80)
        self.check('blank boot has default preferences',self.val('gAppearanceStyle')==0 and self.val('gAppearancePalette')==0)
    def capture(self,name,note):
        P.run(self.c,4)
        p=self.out/(name+'.png');P.snap(self.c,str(p))
        im=Image.open(p)
        self.check(name+' native dimensions',im.size==(240,160))
        self.captures.append({'name':name,'image':p.name,'sha256':digest(p.read_bytes()),'note':note,'style':self.val('gAppearanceStyle'),'palette':self.val('gAppearancePalette'),'game_state':self.val('gGame')})
    def open_options(self,with_save=False):
        for _ in range(2 if with_save else 1):P.press(self.c,'DOWN',2,6)
        P.press(self.c,'A',2,12)
        self.check('Options opens through title choice',self.val('gTitleOptions')==1)
    def set_pair(self,style,palette):
        for _ in range(style):P.press(self.c,'RIGHT',2,6)
        P.press(self.c,'DOWN',2,6)
        for _ in range(palette):P.press(self.c,'RIGHT',2,6)
        self.check('actual style/color selectors match',self.val('gAppearanceStyle')==style and self.val('gAppearancePalette')==palette)
    def active_palette(self,palette):
        expected=bytes_at(self.c,P.sym('appearance_palettes')+palette*32,32)
        self.check('chosen native menu palette is loaded',bytes_at(self.c,P.sym('gPalBg')+13*32,32)==expected)
    def hud_data(self):
        pixels=[];c=self.c
        for y in range(12):
            for x in range(240):
                entry=P.r16(c,0x0600B800+((y//8)*32+x//8)*2)&65535
                if not entry&1023:continue
                xx=7-x%8 if entry&0x400 else x%8;yy=7-y%8 if entry&0x800 else y%8
                value=P.r8(c,0x06008000+(entry&1023)*32+yy*4+xx//2)>>((xx&1)*4)&15
                if value:pixels.append((x,y,P.r16(c,P.sym('gPalBg')+((entry>>12)*16+value)*2)&65535))
        return {'paint':digest(json.dumps(pixels).encode()),'hud_palette':digest(bytes_at(c,P.sym('gPalBg')+15*32,32)),
                'minimap_palette':digest(bytes_at(c,P.sym('gPalObj')+15*32,32)),
                'minimap_tiles':digest(bytes_at(c,0x06010000+1008*32,128))}
    def start(self):
        P.w16(self.c,P.sym('gSeedOverride'),0xB4A7)
        P.w16(self.c,P.sym('gSeedOverride')+2,0)
        P.press(self.c,'START',2,100)
        for _ in range(1200):
            if self.val('gGame')==1:break
            P.run(self.c,1)
        self.check('New Game opens actual Drain',self.val('gGame')==1 and C.area(self.c)==0)
        P.run(self.c,100)
    def inventory(self):
        pl=P.sym('gPl')
        for off,value in ((0,52),(2,80),(4,999)):P.w16(self.c,pl+off,value)
        for off,value in ((6,255),(7,30),(8,127),(35,50),(36,31)):P.w8(self.c,pl+off,value)
        for i,value in enumerate((2,1,6)):P.w8(self.c,pl+9+i,value)
        P.run(self.c,10)
    def nine_combinations(self):
        for style in range(3):
            for palette in range(3):
                prefix=f'style-{style+1}-palette-{palette+1}'
                self.blank_boot()
                if not style and not palette:self.capture('title-no-save','Actual title exposes New Game and Options without a run save.')
                before=bytes_at(self.c,SRAM,1024)
                self.open_options();self.set_pair(style,palette);self.active_palette(palette)
                current=bytes_at(self.c,P.sym('appearance_ui_tiles')+style*self.defs['UI_TILE_COUNT']*32,self.defs['UI_TILE_COUNT']*32)
                self.check('chosen native kit loaded for preview',bytes_at(self.c,0x06008000+5*32,len(current))==current)
                marker_size=self.defs['APPEARANCE_MARK_COUNT']*32
                self.check('chosen native continuation/picker shapes are resident',
                           bytes_at(self.c,0x06010000+936*32,marker_size)==bytes_at(self.c,P.sym('appearance_mark_tiles')+style*marker_size,marker_size))
                self.check('pointer colors follow menu instead of HUD palette',
                           bytes_at(self.c,P.sym('gPalObj')+8*32,32)==bytes_at(self.c,P.sym('appearance_palettes')+palette*32,32))
                self.capture(prefix+'-options','Actual title controls select independent shape and colors; live native dialogue sample.')
                P.press(self.c,'B',2,8)
                self.check('B completes Options and returns title',self.val('gTitleOptions')==0)
                self.check('Options does not write the run save',bytes_at(self.c,SRAM,1024)==before)
                prefs=bytes_at(self.c,PREFS,12)
                self.check('independent preferences written',prefs[4:8]==bytes((1,style,palette,0)))
                self.c.reset();P.run(self.c,80)
                self.check('preferences survive actual reset',self.val('gAppearanceStyle')==style and self.val('gAppearancePalette')==palette)
                self.start();self.active_palette(palette)
                self.capture(prefix+'-intro','Real opening dialogue after New Game, with saved appearance preferences.')
                self.check('New Game preserves preferences record',bytes_at(self.c,PREFS,12)==prefs)
                C.dismiss(self.c);self.inventory()
                hud=self.hud_data()
                if self.reference_hud is None:self.reference_hud=hud
                self.check('Winebound HUD stays exact across appearance choices',hud==self.reference_hud,hud)
                self.capture(prefix+'-hud','Maximum inventory/ammunition fixture; actual fixed Winebound HUD and minimap.')
                P.press(self.c,'START',2,16)
                self.check('Start opens item layout',self.val('gGame')==4)
                self.active_palette(palette)
                # The page's native top-left corner is composed over NAVY;
                # header text starts at x7, so columns0..6 remain exact kit
                # evidence without relying on an unexported EWRAM cache.
                corner=self.defs['UI_PANEL_TL']*32;corner_matches=True
                for y in range(8):
                    source=int.from_bytes(current[corner+y*4:corner+y*4+4],'little');expected=0
                    for x in range(7):expected|=((source>>(x*4)&15) or self.defs['UI_INK_NAVY'])<<(x*4)
                    corner_matches &= (P.r32(self.c,0x06000000+y*4)&0x0FFFFFFF)==expected
                self.check('menu renderer uses selected native shape corner',corner_matches)
                self.capture(prefix+'-items','Real Start opens selected Workbench; full carried-tool fixture.')
                P.press(self.c,'START',2,16)
                position(self.c,(344,118),0);P.hold(self.c,'UP',1);P.press(self.c,'A',2,100)
                self.check('real Wizard dialogue is active',self.val('gTbActive')==1)
                self.check('chosen pointer palette restored after inventory',bytes_at(self.c,P.sym('gPalObj')+8*32,32)==bytes_at(self.c,P.sym('appearance_palettes')+palette*32,32))
                self.capture(prefix+'-dialogue','Position fixture; ordinary Up/A talks to the real wizard, including name and portrait.')
                C.dismiss(self.c);position(self.c,(72,112),0);P.hold(self.c,'UP',1);P.press(self.c,'A',2,60)
                self.check('real market opened',P.r8(self.c,B.static_symbol('sShopActive'))==1)
                self.check('market uses selected pointer palette',bytes_at(self.c,P.sym('gPalObj')+8*32,32)==bytes_at(self.c,P.sym('appearance_palettes')+palette*32,32))
                self.capture(prefix+'-shop','Position/gilt fixture; ordinary Up/A opens the real merchant shop.')
                self.active_palette(palette)
                print('PAIR PASS',style,palette,flush=True)
    def corruption(self):
        self.blank_boot();self.open_options();self.set_pair(2,1);P.press(self.c,'A',2,6)
        raw=bytearray(bytes_at(self.c,PREFS,12));raw[6]^=1
        for i,v in enumerate(raw):P.w8(self.c,PREFS+i,v)
        self.c.reset();P.run(self.c,80)
        self.check('corrupt settings fall back safely',self.val('gAppearanceStyle')==0 and self.val('gAppearancePalette')==0)
    def persistence_with_run(self):
        import save_probe as S
        self.blank_boot();self.open_options();self.set_pair(1,2);P.press(self.c,'A',2,6)
        original=bytes_at(self.c,PREFS,12)
        self.c.reset();P.run(self.c,80);self.start()
        version,run=S.save_on_death(self.c)
        self.check('normal death/save keeps existing v2 format',version==2)
        self.check('run save leaves preference bytes untouched',bytes_at(self.c,PREFS,12)==original)
        self.c.reset();P.run(self.c,80)
        self.capture('title-with-save','Actual title after the normal death/save path; Continue, New Game and Options.')
        self.open_options(with_save=True)
        self.check('saved appearance remains selected with Continue present',self.val('gAppearanceStyle')==1 and self.val('gAppearancePalette')==2)
        P.press(self.c,'RIGHT',2,6);P.press(self.c,'DOWN',2,6);P.press(self.c,'LEFT',2,6);P.press(self.c,'B',2,8)
        newer=bytes_at(self.c,PREFS,12)
        self.check('changing preferences preserves a valid run record exactly',bytes_at(self.c,SRAM,len(run))==run)
        P.press(self.c,'UP',2,6);P.press(self.c,'UP',2,6);P.press(self.c,'A',2,100);C.dismiss(self.c)
        self.check('Continue loads actual saved seed',P.r32(self.c,P.sym('gWorld'))==0xB4A7)
        self.check('Continue keeps chosen appearance',self.val('gAppearanceStyle')==2 and self.val('gAppearancePalette')==1)
        self.c.reset();P.run(self.c,80)
        P.w16(self.c,P.sym('gSeedOverride'),0xCAFE);P.w16(self.c,P.sym('gSeedOverride')+2,0)
        P.press(self.c,'DOWN',2,6);P.press(self.c,'START',2,100)
        for _ in range(1200):
            if self.val('gGame')==1:break
            P.run(self.c,1)
        C.dismiss(self.c)
        self.check('New Game remains a distinct title choice with a save',P.r32(self.c,P.sym('gWorld'))==0xCAFE)
        self.check('New Game with an old run preserves preferences',bytes_at(self.c,PREFS,12)==newer)
    def finish(self):
        result={'method':__doc__.strip(),'rom_sha256':digest(Path(P.ROM).read_bytes()),'captures':self.captures,'checks':self.checks,
                'passed':sum(r['passed'] for r in self.checks),'total':len(self.checks),'fixed_hud':self.reference_hud}
        (self.out/'appearance-review.json').write_text(json.dumps(result,indent=2)+'\n')
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
        for screen in ('options','items','dialogue','shop','hud'):
            board=Image.new('RGB',(720,552),'#101820');d=ImageDraw.Draw(board);d.fontmode='1'
            for style in range(3):
                for palette in range(3):
                    x=palette*240;y=style*184
                    d.text((x+4,y+4),NAMES[style]+' / '+PALETTES[palette],font=font,fill='#e8c878')
                    board.paste(Image.open(self.out/f'style-{style+1}-palette-{palette+1}-{screen}.png'),(x,y+24))
            board.save(self.out/f'nine-{screen}.png')
        print('RESULT',result['passed'],'/',result['total'],'captures',len(self.captures),flush=True)
        return result['passed']==result['total']

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',required=True);p.add_argument('--map',required=True);p.add_argument('--assets-header',required=True);p.add_argument('--out',required=True)
    r=Review(p.parse_args());r.nine_combinations();r.corruption();r.persistence_with_run();return 0 if r.finish() else 1
if __name__=='__main__':raise SystemExit(main())
