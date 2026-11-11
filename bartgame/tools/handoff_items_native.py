#!/usr/bin/env python3
"""Actual mGBA input review; only disclosed loadout/navigation fixtures."""
from pathlib import Path
import sys,re,json,struct,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent));import probe as P,critical_path as C,bloom_probe as B
from types import SimpleNamespace
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
bundle=Path(args.bundle).resolve();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
P.ROM=str(bundle/'bartgame.gba');P.MAP=str(bundle/'bartgame.map');P._syms=None
D=B.configure(SimpleNamespace(map=P.MAP,assets_header=str(bundle/'assets.h')))
checks=[];frames={};fixtures=[]
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail));print('PASS' if ok else 'FAIL',name,detail,flush=True)
def w32(c,a,n):P.w16(c,a,n&65535);P.w16(c,a+2,(n>>16)&65535)
def raw(c,a,n):return bytes(P.r8(c,a+i) for i in range(n))
def shot(c,name):P.snap(c,str(out/(name+'.png')))
def equip(c,eq):
 pl=P.sym('gPl');P.w8(c,pl+9,1);P.w8(c,pl+10,eq);P.w8(c,pl+11,0)
 fixtures.append(dict(kind='loadout equipment only',B=eq));P.run(c,40)
def nav(c,x=200,y=270,face=1):
 a=P.sym('gActors');w32(c,a+8,x<<16);w32(c,a+12,y<<16);P.w8(c,a+7,face);P.w8(c,a+6,face*8)
 fixtures.append(dict(kind='navigation position/facing only',x=x,y=y,face=face));P.run(c,5)
def actors(c,kind=None,typ=None):
 return [dict(i=i,**P.actor(c,i),v=list(raw(c,P.sym('gActors')+64*i+48,6))) for i in range(1,96) if (kind is None or P.r8(c,P.sym('gActors')+i*64)==kind) and (typ is None or P.r8(c,P.sym('gActors')+i*64+1)==typ)]
c=P.boot(rom=P.ROM,seed=0xb4a7);C.dismiss(c)
for i in range(4):P.press(c,'A',2,12)
C.dismiss(c);P.run(c,40)
check('real fresh run in sewer',C.area(c)==0,dict(actor=P.actor(c,0),state=C.gstate(c)))
# Disclosed ownership/ammunition fixture. No HP, enemy, room, action, completion,
# animationclock or timer fields are assigned by this review.
li=P.sym('gLegacyInventory');pl=P.sym('gPl')
for i in range(16):P.w8(c,li+i,255)
P.w8(c,pl+8,0x7f);P.w8(c,pl+36,0x1f);P.w8(c,pl+35,40);P.w8(c,pl+7,20)
fixtures.append(dict(kind='loadout ownership and ammunition only',all118=True,arrows=40,bombs=20))
for name,eq,kind,damage in [('boomerang',10,0,0),('magic-boomerang',11,1,0),('pacci',14,2,2),('fire-rod',17,3,4),('light-arrow',9,4,4)]:
 equip(c,eq);nav(c);before=P.r8(c,pl+35);P.hold(c,'B',1);P.run(c,2)
 got=[a for a in actors(c,6,23) if a['v'][0]==kind]
 check(name+' input spawns explicit tool actor',len(got)==1,got)
 if got:check(name+' damage matches tool',P.r8(c,P.sym('gActors')+got[0]['i']*64+47)==damage,got)
 shot(c,name);P.run(c,180)
 if eq==9:check('Light Arrow consumes one arrow',P.r8(c,pl+35)==before-1)
equip(c,13);nav(c);P.hold(c,'B',122);P.run(c,2);got=[a for a in actors(c,6,23) if a['v'][0]==6];check('Gust medium charge releases gust',bool(got),got);shot(c,'gust-release');P.run(c,160)
equip(c,16)
r=P.sym('gRoom');good=None
for yy in range(160,340,8):
 for xx in range(64,340,8):
  if all(P.r8(c,r+4098+(y//8)*64+x//8)==0 for y in range(yy-12,yy+5,4) for x in range(xx-8,xx+100,4)):
   good=(xx,yy);break
 if good:break
assert good,'no native boots lane'
nav(c,*good);start=P.player_pos(c);c.set_keys(P.key(c,'B'));xs=[]
for i in range(25):c.run_frame();xs.append(P.player_pos(c)[0])
c.clear_keys(*range(10));P.run(c,5);check('Boots windup then 3px dash',xs[-1]-xs[-2]==3,dict(start=start,x=xs));shot(c,'boots')
equip(c,4);nav(c);P.hold(c,'B',8);a=P.actor(c,0);check('Cape takes actual jump state and height',a['state']==5 and a['z']>0,a);shot(c,'cape');P.run(c,90)
equip(c,15);nav(c);P.hold(c,'B',18);check('Mitts keeps standard movement state',P.actor(c,0)['state']==0,P.actor(c,0));shot(c,'mitts');P.run(c,60)
# Cure actual blast damage, then prove automatic bottled-fairy rescue using
# real bomb impacts rather than writing a low HP fixture.
P.w8(c,li+42,0x24);fixtures.append(dict(kind='bottle1 contents loadout',value='Red Potion'));equip(c,2);nav(c);hp0=P.r16(c,pl);P.press(c,'B',1,60);hp1=P.r16(c,pl);check('native impact self damage occurs',hp1==hp0-4,dict(before=hp0,after=hp1));equip(c,19);P.press(c,'B',1,40);check('Red Potion cures real damage and empties bottle',P.r16(c,pl)==hp0 and P.r8(c,li+42)==0,dict(hp=P.r16(c,pl),bottle=P.r8(c,li+42)))
P.w8(c,li+42,0x28);fixtures.append(dict(kind='bottle1 contents loadout',value='Fairy'));equip(c,2)
for i in range(6):
 nav(c);P.press(c,'B',1,65)
 if not P.r8(c,li+42):break
check('Bottled Fairy automatically rescues real lethal blast',P.r8(c,li+42)==0 and P.r16(c,pl)>0,dict(hp=P.r16(c,pl),state=P.actor(c,0)['state']));shot(c,'fairy-rescue')
(out/'report.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,rom_sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),notes='Only loadout and navigation fixtures. No HP/AI/action/completion/geometry/framebuffer writes.'),indent=2))
print('RESULT',sum(x['passed'] for x in checks),'/',len(checks))
