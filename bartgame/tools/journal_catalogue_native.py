#!/usr/bin/env python3
"""Read every visible item/enemy entry through real mGBA cabinet controls.
Complete JRN2 knowledge is an explicit private UI fixture, not earned discovery.
Native preview bytes/palettes are checked against the frozen ROM's source;
no terrain, video memory, AI, stats, cursor, journal RAM or completion is set.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
import mgba.core,mgba.image
import probe as P
from arcade_journal_review import fnv,preferences
SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bundle',required=True);ap.add_argument('--out',required=True);ap.add_argument('--raw-list',action='store_true',help='Reproduce pre-filter integration4 control');a=ap.parse_args();bundle=Path(a.bundle);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 P.ROM=str(bundle/'bartgame.gba');P.MAP=str(bundle/'bartgame.map');P._syms=None;checks=[];rows=[];media=[]
 linker=(bundle/'bartgame.map').read_text()
 static={}
 for label in ('sItems','sEnemies'):
  found=re.search(r'^ \.rodata\.'+label+r'\s+0x([0-9a-f]+)\s+0x[0-9a-f]+\s+\S*journal\.o$',linker,re.M)
  if not found:raise RuntimeError('native journal metadata unavailable: '+label)
  static[label]=int(found[1],16)
 defs={k:int(v,0) for k,v in re.findall(r'^#define\s+(\w+)\s+(0x[\da-fA-F]+|\d+)\b',(bundle/'assets.h').read_text(),re.M)}
 def raw(c,at,n):return bytes(P.r8(c,at+i) for i in range(n))
 def w32(c,at,v):P.w16(c,at,v&65535);P.w16(c,at+2,v>>16)
 def check(n,ok,detail=None):checks.append(dict(name=n,passed=bool(ok),detail=detail))
 def shot(c,n):f=out/(n+'.png');P.snap(c,str(f));media.append(dict(file=f.name,sha256=SHA(f.read_bytes())))
 c=mgba.core.load_path(P.ROM);c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset();sram=bytearray([255])*32768
 data=struct.pack('<IHHI',0x324e524a,2,64,77)+((1<<146)-1).to_bytes(20,'little')+((1<<84)-1).to_bytes(12,'little')+bytes(16)
 sram[0x7e40:0x7e80]=data+struct.pack('<I',fnv(data));sram[0x7f00:0x7f0c]=preferences(2,1)
 for i,b in enumerate(sram):P.w8(c,0xe000000+i,b)
 P.run(c,45);w32(c,P.sym('gSeedOverride'),0xb4a7);P.press(c,'START',2,4)
 for _ in range(2200):
  if P.r8(c,P.sym('gTbActive')):P.press(c,'A',2,5)
  else:P.run(c,3)
  if P.r8(c,P.sym('gGame'))==1 and P.r8(c,P.sym('gGame')+1)==0 and not P.r8(c,P.sym('gTbActive')):break
 P.run(c,30);cx=P.r16(c,P.sym('gCabinetX'));cy=P.r16(c,P.sym('gCabinetY'));w32(c,P.sym('gActors')+8,cx<<16);w32(c,P.sym('gActors')+12,(cy+20)<<16);P.hold(c,'UP',2);P.press(c,'A',2,5)
 check('real cabinet opens known catalogue',P.r8(c,P.sym('gGame'))==7)
 room_before=raw(c,P.sym('gRoom'),10242);actors_before=raw(c,P.sym('gActors'),96*64)
 # LegacyItemDef is a native32bit two-pointer/6byte record, padded to16;
 # flags are byte12. Read the exact frozen ROM, not the live source tree.
 visible=list(range(146)) if a.raw_list else list(range(24))+[24+i for i in range(118) if not(P.r8(c,P.sym('gLegacyItemDefs')+i*16+12)&2)]+list(range(142,146))
 for page,listing in ((0,visible),(1,list(range(84)))):
  total=len(listing)
  if page:P.press(c,'R',2,5)
  for index,rawid in enumerate(listing):
   cursor=P.r8(c,P.sym('gArcadeCursor'));sheet=P.r8(c,P.sym('gArcadePreviewSheet'));frame=P.r8(c,P.sym('gArcadePreviewFrame'));pal=P.r8(c,P.sym('gArcadePreviewSourcePalette'));tiles=P.r16(c,P.sym('gArcadePreviewTiles'))&65535
   if (not page and rawid<24) or (page and rawid<9):
    meta=static['sEnemies' if page else 'sItems']+rawid*16
    expected=(P.r8(c,meta+8),P.r8(c,meta+9),P.r8(c,meta+10))
   elif not page:
    expected_sheet=defs['SHEET_HANDOFF_ITEMS'];expected_frame=P.r8(c,P.sym('gLegacyItemDefs')+(rawid-24)*16+13) if rawid<142 else 118+rawid-142
    expected=(expected_sheet,expected_frame,P.r8(c,P.sym('sheets')+expected_sheet*12+9))
   else:
    expected_sheet=P.r8(c,P.sym('gLegacyEnemyDefs')+(rawid-9)*24)
    expected=(expected_sheet,2,P.r8(c,P.sym('sheets')+expected_sheet*12+9))
   okay=cursor==index and P.r8(c,P.sym('gArcadeSeen')) and 0<tiles<=32 and sheet<defs['SHEET_COUNT'] and (sheet,frame,pal)==expected
   native=raw(c,0x6010000+944*32,tiles*32)
   if sheet==defs['SHEET_ICON32']:src=P.sym('icon32_exact_tiles')+frame*tiles*32;ps=P.sym('icon32_exact_pal')+frame*32
   else:src=P.r32(c,P.sym('sheets')+sheet*12)+frame*tiles*32;ps=P.sym('pal_obj')+pal*32
   okay=okay and native==raw(c,src,tiles*32) and raw(c,0x5000200+6*32,32)==raw(c,ps,32)
   check(('enemy' if page else 'item')+' nativepreview%d'%rawid,okay,dict(cursor=cursor,raw_id=rawid,sheet=sheet,frame=frame,palette=pal,tiles=tiles,expected=expected))
   rows.append(dict(page=page,index=index,raw_id=rawid,sheet=sheet,frame=frame,palette=pal,tiles=tiles,sha256=SHA(native)))
   if (not page and rawid in (0,24,42,83,117,141,142,143,144,145)) or (page and rawid in (0,9,28,29,41,64,65,66,67,79,80,81,82,83)):
    shot(c,('enemy' if page else 'item')+'-%03d-index'%rawid);P.press(c,'A',2,4);shot(c,('enemy' if page else 'item')+'-%03d-notes'%rawid);P.press(c,'B',2,4)
   if index<total-1:P.press(c,'DOWN',2,4)
 check('catalogue freezes actual actor state',raw(c,P.sym('gActors'),96*64)==actors_before)
 check('catalogue preserves actual terrain',raw(c,P.sym('gRoom'),10242)==room_before)
 P.press(c,'B',2,4);check('cabinet returns to live Drain',P.r8(c,P.sym('gGame'))==1 and P.r8(c,P.sym('gGame')+1)==0);shot(c,'return-drain')
 report=dict(passed=all(x['passed'] for x in checks),method=__doc__,checks=checks,entries=rows,media=media,fixture=dict(raw_items=146,visible_items=len(visible),visible_raw_ids=visible,enemies=84,raw_list_control=a.raw_list,private_valid_JRN2=True,earned=False,navigation='player position/facing toward actual cabinet only'),rom_sha256=SHA((bundle/'bartgame.gba').read_bytes()),tool_sha256=SHA(Path(__file__).read_bytes()))
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(dict(passed=report['passed'],checks=len(checks),failed=[x for x in checks if not x['passed']]),flush=True)
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
