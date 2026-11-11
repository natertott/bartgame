#!/usr/bin/env python3
"""Actual mGBA input review; only disclosed loadout/navigation fixtures."""
from pathlib import Path
import sys,json,hashlib,subprocess,re
sys.path.insert(0,str(Path(__file__).resolve().parent));import probe as P,critical_path as C,bloom_probe as B
from types import SimpleNamespace
from sewer_concept_audit import NativeRom
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
bundle=Path(args.bundle).resolve();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
P.ROM=str(bundle/'bartgame.gba');P.MAP=str(bundle/'bartgame.map');P._syms=None
D=B.configure(SimpleNamespace(map=P.MAP,assets_header=str(bundle/'assets.h')))
checks=[];fixtures=[];views=[]
native=NativeRom(bundle);meta,pixels=native.sheet('handoff_mechanisms')
nm=subprocess.check_output(['arm-none-eabi-nm','-n',str(bundle/'bartgame.elf')],text=True)
symbols={name:int(address,16) for address,name in re.findall(r'^([0-9a-f]{8})\s+\w\s+(\S+)\s*$',nm,re.M)}
def slots(c,label):
 count=P.r8(c,symbols['sObj']+8);rows=[]
 for i in range(count):
  at=symbols['sObjects']+22*i;tile=P.r16(c,at+8)&65535;kind=P.r8(c,at+12);frame=P.r8(c,at+14);pending=P.r8(c,at+15)
  expected=pixels[frame*512:(frame+1)*512];actual=bytes(P.r8(c,0x6010000+tile*32+j) for j in range(512)) if tile else b''
  rows.append(dict(index=i,type=kind,frame=frame,tile=tile,pending=pending,uploaded=actual==expected))
 check(label+' allocates every native object slot',count>0 and all(r['tile'] for r in rows),rows)
 check(label+' streams exact native pixels',all(r['pending'] or r['uploaded'] for r in rows),rows)
 views.append(dict(label=label,hero=P.actor(c,0),hp=P.r16(c,P.sym('gPl')),slots=rows))
site_at=B.static_symbol('sHandoffSite')
def current_site(c):return P.r8(c,site_at)
def w32(c,a,n):P.w16(c,a,n&65535);P.w16(c,a+2,(n>>16)&65535)
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail));print('PASS' if ok else 'FAIL',name,detail if not ok else '',flush=True)
def nav(c,x,y,face=0):
 a=P.sym('gActors');w32(c,a+8,x<<16);w32(c,a+12,y<<16);P.w8(c,a+7,face);P.w8(c,a+6,face*8);fixtures.append(dict(kind='navigation only',x=x,y=y,face=face));P.run(c,5)
def wait(c,n=1000):
 for i in range(n):
  if P.r8(c,P.sym('gTbActive')):P.press(c,'A',2,6)
  elif C.gstate(c)==1:break
  else:P.run(c,2)
 P.run(c,12)
def shot(c,name):P.snap(c,str(out/(name+'.png')))
def enter(c,site):
 if C.area(c)==4:
  nav(c,16*16+8,23*16+4);P.run(c,100);wait(c)
 # Always return through the existing Drain entrance, not transitionstatewrites.
 if C.area(c)!=0:
  P.w8(c,P.sym('gPl')+10,18);P.run(c,30);P.press(c,'B',2,120);wait(c)
 nav(c,17*16+8,6*16+34);P.press(c,'A',2,100);wait(c)
 check('enter annex hub through realdoor',C.area(c)==4 and current_site(c)==0,dict(area=C.area(c),cell=C.cell(c),site=current_site(c)))
 nav(c,17*16+8,14*16+22);P.press(c,'A',2,10)
 for i in range(site-1):P.press(c,'DOWN',3,7)
 P.press(c,'A',2,100);wait(c)
 check('Challenge desk opens actual course '+str(site),C.area(c)==4 and current_site(c)==site,dict(area=C.area(c),cell=C.cell(c),site=current_site(c)))
 slots(c,'course '+str(site)+' entry');shot(c,'course-'+str(site)+'-entry')
c=P.boot(rom=P.ROM,seed=0xb4a7);C.dismiss(c)
for i in range(4):P.press(c,'A',2,12)
C.dismiss(c);P.run(c,40)
pl=P.sym('gPl');li=P.sym('gLegacyInventory')
for i in range(16):P.w8(c,li+i,255)
P.w8(c,pl+8,127);P.w8(c,pl+36,31);P.w8(c,pl+9,1);P.w8(c,pl+10,0);P.w8(c,pl+11,5);P.w8(c,pl+35,40);P.w8(c,pl+7,20)
P.w16(c,li+32,4095);P.w8(c,li+46,4)
fixtures.append(dict(kind='loadout ownership/ammo/skills/swordlevel only',all118=True))
for site in (28,29,30,31):
 enter(c,site)
 for x,y,name in ((120,100,'nw'),(380,110,'ne'),(120,270,'sw'),(380,270,'se')):
  nav(c,x,y);P.run(c,85);slots(c,'course '+str(site)+' '+name);shot(c,'course-'+str(site)+'-'+name)
 (out/'progress.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures),indent=2))
(out/'report.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,views=views,rom_sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),notes='Actual mGBA input and live actors. Only loadout and navigation fixtures, no geometry/HP/AI/completion/state/timer writes.'),indent=2))
