#!/usr/bin/env python3
"""Real mGBA annex review. Native inputs perform all awards and pushes.
Only an explicit fresh-save/seed and player-navigation fixtures are injected.
Copies ROM/map to --out/bundle so real user saves cannot be overwritten.
"""
from pathlib import Path
import sys,re,json,struct,hashlib,argparse,shutil,tempfile,subprocess
GAME=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(GAME/'tools'));import probe as P
import mgba.core,mgba.image
arg=argparse.ArgumentParser();arg.add_argument('--bundle',type=Path);arg.add_argument('--out',type=Path,default=Path('/tmp/handoff-native-review'));arg.add_argument('--seed',type=lambda n:int(n,0),default=0xB4A7);arg.add_argument('--suite',choices=['services','quests','contract','meta'],default='services');args=arg.parse_args()
O=args.out;O.mkdir(parents=True,exist_ok=True);B=O/'bundle';B.mkdir(exist_ok=True)
rom=(args.bundle/'bartgame.gba') if args.bundle else GAME/'bartgame.gba'
mapfile=(args.bundle/'bartgame.map') if args.bundle else GAME/'build/bartgame.map'
for source,target in ((rom,B/'bartgame.gba'),(mapfile,B/'bartgame.map')):
 if source.resolve()!=target.resolve():shutil.copyfile(source,target)
P.ROM=str(B/'bartgame.gba');P.MAP=str(B/'bartgame.map');P._syms=None
# Derive extension field offsets from the C ABI used by the reviewed source.
fields=['draft','draft_round','draft_state','memory_known','memory_code','completed','quest','contract_step','contract_kind','contract_state','contract_target','contract_item']
code='#include <stdio.h>\n#include <stddef.h>\n#include "handoff_events.h"\nint main(void){'+''.join('printf("%%zu ",offsetof(HandoffState,%s));'%f for f in fields)+'return 0;}'
with tempfile.TemporaryDirectory(prefix='handoff-abi-') as temporary:
 cfile=Path(temporary)/'abi.c';binary=Path(temporary)/'abi';cfile.write_text(code)
 subprocess.run(['gcc','-Wno-attributes','-I'+str(GAME/'src'),'-I'+str(GAME/'build/gen'),str(cfile),'-o',str(binary)],check=True,capture_output=True)
 offsets=dict(zip(fields,map(int,subprocess.check_output([str(binary)],text=True).split())))

maptext=Path(P.MAP).read_text();checks=[];fixtures=[]
def static(n,file):
 q=re.search(r'\.(?:bss|rodata)\.'+re.escape(n)+r'\s+0x([0-9a-f]+)\s+0x[0-9a-f]+\s+build/'+file+r'\.o',maptext)
 if not q and n in ('s','m'):
  section='runtime' if n=='s' else 'menu'
  q=re.search(r'\.ewram_bss\.handoff_'+section+r'\s+0x([0-9a-f]+)',maptext)
 if not q:raise KeyError((n,file))
 return int(q[1],16)
S=static('s','handoff_events');M=static('m','handoff_events');H=P.sym('gHandoffState')
def ck(n,ok,d=None):checks.append(dict(name=n,passed=bool(ok),detail=d));print('PASS' if ok else 'FAIL',n,d,flush=True)
def w32(a,n):P.w16(c,a,n&65535);P.w16(c,a+2,n>>16)
def raw(a,n):return bytes(P.r8(c,a+i) for i in range(n))
def tp(x,y,face=0):
 a=P.sym('gActors');w32(a+8,x<<16);w32(a+12,y<<16);P.w8(c,a+7,face);fixtures.append(dict(kind='player position and facing only',x=x,y=y,facing=face))
def text():return P.r8(c,P.sym('gTbActive'))
def dismiss():
 for i in range(150):
  if not text():break
  P.press(c,'A',2,6)
def site():return P.r8(c,S+34)
def status():return dict(area=P.r8(c,P.sym('gGame')+1),state=P.r8(c,P.sym('gGame')),site=site(),menu=P.r8(c,M+14),actor=P.actor(c,0),text=text(),gilt=P.r16(c,P.sym('gPl')+4)&65535)
def shot(n):P.snap(c,str(O/(n+'.png')))
def settle(area=4,limit=1000):
 for i in range(limit):
  if text():dismiss()
  if P.r8(c,P.sym('gGame'))==1 and P.r8(c,P.sym('gGame')+1)==area and not text():return True
  P.run(c,2)
 return False
def enter():
 tp(17*16+8,6*16+34);P.run(c,2);P.press(c,'A',2,4);assert settle(4);assert site()==0

def desk(i):
 xy=[(7,8),(12,8),(17,8),(22,8),(7,14),(12,14),(17,14),(22,14)][i]
 tp(xy[0]*16+8,xy[1]*16+14);P.run(c,3);P.press(c,'A',4,8)
 return P.r8(c,M+14)
def move_menu(index):
 for i in range(index):P.press(c,'DOWN',3,5)
def challenge(kind):
 assert desk(6)==7,status();move_menu(kind-1);P.press(c,'A',4,8)
 for i in range(1000):
  if text():dismiss()
  if site()==kind and P.r8(c,P.sym('gGame'))==1:return
  P.run(c,2)
 raise AssertionError(('not entered',kind,status()))
def leave():
 dismiss();tp(16*16+8,21*16+14);P.run(c,2);P.hold(c,'DOWN',28)
 for i in range(1000):
  if text():dismiss()
  if P.r8(c,P.sym('gGame'))==1 and ((P.r8(c,P.sym('gGame')+1)==4 and site()==0) or P.r8(c,P.sym('gGame')+1)==0):break
  P.run(c,2)
 if P.r8(c,P.sym('gGame')+1)==0:enter()
 assert site()==0,status()
def done(id):return bool(P.r8(c,H+offsets['completed']+(id>>3))&(1<<(id&7)))
c=mgba.core.load_path(P.ROM);c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
for i in range(32768):P.w8(c,0xe000000+i,255)
P.run(c,45);w32(P.sym('gSeedOverride'),args.seed);P.press(c,'START',2,4)
assert settle(0);enter();ck('actual Drain interaction enters annex',site()==0,status());shot('annex')
ck('draft opens actual modal',desk(0)==1,status());shot('draft-first')
choices=[]
for rnd in range(3):
 P.run(c,5)
 row=[P.r16(c,H+offsets['draft']+i*2)&65535 for i in range(3)];choices.append(row)
 choice=row.index(0x59) if 0x59 in row else 0
 move_menu(choice);P.press(c,'A',4,8)
 if text():dismiss()
ck('three-round draft choices are granted',P.r8(c,H+offsets['draft_state'])==2 and P.r8(c,H+offsets['draft_round'])==3,dict(choices=choices,status=status()));dismiss();shot('draft-complete')
# Rupee200 selected from the real second-round draft funds actual transaction.
old=P.r16(c,P.sym('gPl')+4)&65535
ck('draft supplied transaction funds',old>=50,old)
if old>=50:
 ck('inn actual menu',desk(1)==2,status());P.press(c,'A',4,8);shot('inn-fading');P.run(c,170);dismiss();ck('inn charges50 and returns from frozen sleep',P.r16(c,P.sym('gPl')+4)==old-50 and P.actor(c,0)['state']==0,status());shot('inn-rested')
# Inspect/solve template and axis maze through ordinary A pushes only.
for kind in (10,11,22):
 challenge(kind);shot('board-%d-before'%kind)
 idx=P.r16(c,P.sym('gHandoffPuzzleIndex'))&65535;base=static('sPuzzlePool','handoff_events')+idx*52;p=struct.unpack('<II3B3B6B32B',raw(base,52));blocks=list(p[2:5]);moves=p[14:14+p[13]]
 # layout: walls0 goals1 blocks2..4 axes5..7 player8 entry9 goal10 kind11 min12 length13
 for encoded in moves:
  which,d=divmod(encoded,4);cell=blocks[which];dx=(0,1,0,-1)[d];dy=(-1,0,1,0)[d];back=(cell%5-dx,cell//5-dy)
  tp((7+back[0])*16+8,(8+back[1])*16+14,d);P.run(c,2);P.press(c,'A',4,8);blocks[which]=(cell//5+dy)*5+cell%5+dx
 ck('actual C puzzle completed by native pushes kind%d'%kind,done(kind),dict(index=idx,witness=list(moves),pushes=P.r16(c,P.sym('gHandoffPushes'))&65535,blocks=list(raw(P.sym('gHandoffBoardBlocks'),3))));shot('board-%d-solved'%kind);leave()
# Memory learn/recall genuine sequence storage, no completion writes.
challenge(7);P.run(c,400);code=list(raw(H+offsets['memory_code'],4));ck('Learn chamber teaches seeded code',P.r8(c,H+offsets['memory_known'])==1,code);shot('memory-learn');leave();challenge(8)
for p in code:
 tp(16*16+8,14*16+14);P.run(c,3);tp((9+p*4)*16+8,10*16+14);P.run(c,3)
ck('Recall completes by entering real plates',done(8),code);shot('memory-recall');leave()
challenge(9);theme=P.r8(c,S+46)
for p in ((0,2) if theme==1 else (0,1,2,3)):
 tp(16*16+8,14*16+14);P.run(c,3);tp((9+p*4)*16+8,10*16+14);P.run(c,3)
ck('Floor switch puzzle responds to actual feet',done(9),dict(theme=theme));shot('plates');leave()
# A real R lift exposes overlay-only pot bug if present; no false success.
challenge(16);tp(7*16+8,7*16+14+16,0);P.run(c,2);P.press(c,'R',2,12)
ck('Pot quest pot can actually be lifted',P.r8(c,P.sym('gPl')+33)==4 or P.actor(c,0)['state'] in (10,11),status());shot('pot-lift')

Q=H+offsets['quest']
# Find the hidden seeded pot with real R lifts and throws.
for i in range(6):
 if P.r8(c,Q+1)==3:break
 if P.r8(c,P.sym('gPl')+33):P.press(c,'R',4,50)
 if i==0:continue
 tx,ty=7+(i%3)*8,7+(i//3)*8;tp(tx*16+8,ty*16+30,0);P.run(c,3);P.press(c,'R',4,20)
ck('Pot quest finds its actual seeded pot',P.r8(c,Q+1)==3,dict(quest=list(raw(Q,20)),status=status()))
if P.r8(c,P.sym('gPl')+33):P.press(c,'R',4,50)
shot('pot-complete')
(O/'report.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,layout=offsets,rom_sha256=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest(),note='Fresh private SRAM; seed fixture; player position/facing navigation only. Native R lifts/throws, A interactions, and proof-witness pushes. No enemy, HP or completion edits.'),indent=2))
print('REPORT',sum(x['passed'] for x in checks),len(checks),flush=True)
if not all(x['passed'] for x in checks):raise SystemExit(1)

if args.suite=='quests':
 Q=H+offsets['quest']
 leave();challenge(18);mode=P.r8(c,Q+8)
 x=P.r16(c,Q+20);y=P.r16(c,Q+22)
 if mode==0:tp(23*16+16,8*16+14);P.run(c,50)
 elif mode==1:tp(x,y+20,0);P.run(c,3);P.press(c,'B',4,40)
 else:
  P.w8(c,P.sym('gPl')+9,15);fixtures.append(dict(kind='assign actually drafted Mole Mitts to A; sword remains on B'))
  tp(x,y+16,0);P.run(c,3);P.hold(c,'A',20);P.run(c,4)
 ck('Final Scavenger uses actual hidden predicate/tool',P.r8(c,Q+1)==3,dict(mode=mode,hidden_x=x,hidden_y=y,status=status()));shot('scavenger');leave()
 challenge(19);tp(28*16+8,20*16+14);P.run(c,3);P.hold(c,'UP',190);P.hold(c,'LEFT',40)
 ck('Final Stealth solved with continuous native walking',P.r8(c,Q+1)==3,dict(status=status(),quest=list(raw(Q,20))));shot('stealth');leave()
 # Full real carry test, reusing reviewed input-only helper bodies.
 challenge(20);Q=H+offsets['quest']
 
 def carry_pick():
  x=P.r16(c,Q+20);y=P.r16(c,Q+22);tp(x,y);P.run(c,3);P.press(c,'A',4,22)
  return P.actor(c,0)['state']==11
 
 def fight(limit=1100):
  for t in range(limit):
   foes=[P.actor(c,i) for i in range(1,96) if P.actor(c,i)['kind']==2]
   if not foes:return True
   a=P.actor(c,0);e=foes[0]
   if a['state'] in (0,2):
    tp(e['x'],e['y']+24,0)
    if a['state']==0:P.press(c,'B',3,2)
    else:P.run(c,5)
   else:P.run(c,5)
   if P.r8(c,Q+1)!=2:return False
  return False
 
 carry_pick();ck('Full carry contract picks up actual cargo',P.r8(c,Q+12)==1,status())
 tp(16*16,13*16);P.run(c,5);ck('Carry crossing triggers first live ambush',P.r8(c,Q+11)==1 and any(P.actor(c,i)['kind']==2 for i in range(1,96)),list(raw(Q,20)));shot('carry-ambush1')
 P.press(c,'B',4,45);ck('First carry ambush cleared by sword attacks',fight(),dict(hp=P.r16(c,P.sym('gPl')),quest=list(raw(Q,20))));P.run(c,25)
 ck('Cargo recovered after first ambush',carry_pick(),dict(status=status(),quest=list(raw(Q,28))))
 tp(19*16,8*16);P.run(c,5);ck('Carry crossing triggers second live ambush',P.r8(c,Q+11)==2 and any(P.actor(c,i)['kind']==2 for i in range(1,96)),list(raw(Q,20)));shot('carry-ambush2')
 P.press(c,'B',4,45);ck('Second carry ambush cleared by sword attacks',fight(),dict(hp=P.r16(c,P.sym('gPl')),quest=list(raw(Q,20))));P.run(c,25)
 ck('Cargo recovered after second ambush',carry_pick(),dict(status=status(),quest=list(raw(Q,28))))
 tp(P.r16(c,Q+24),P.r16(c,Q+26));P.run(c,3);P.press(c,'A',4,8);dismiss();ck('Full carry quest delivery completes through A while carrying',P.r8(c,Q+1)==3 and done(20),dict(status=status(),quest=list(raw(Q,28))));shot('carry-delivered')
 
 leave();challenge(17);hp=P.r16(c,P.sym('gPl'))
 for i in range(1800):
  if P.r8(c,Q+1)!=2:break
  foes=[P.actor(c,j) for j in range(1,96) if P.actor(c,j)['kind']==2]
  if not foes:P.run(c,2);continue
  e=foes[0];a=P.actor(c,0)
  if a['state'] in (0,2):
   tp(e['x'],e['y']+24,0)
   if a['state']==0:P.press(c,'B',3,2)
   else:P.run(c,5)
  else:P.run(c,5)
 ck('Final Hunt quota fulfilled by real sword kills',P.r8(c,Q+1)==3,dict(hp_before=hp,hp_after=P.r16(c,P.sym('gPl')),quest=list(raw(Q,20))));shot('hunt');P.run(c,30);leave()
 challenge(21);ck('Final Courier holds actual parcel',P.r8(c,Q+12)==1 and P.r8(c,Q+1)==2,list(raw(Q,20)));leave()
 tp(16*16+8,21*16+14);P.run(c,2);P.hold(c,'DOWN',28);assert settle(0);P.enter_forest(c);fixtures.append(dict(kind='P.enter_forest navigation to actual sewer exit; safe floor relocation; real UP input'));dismiss();P.run(c,5)
 rx=P.r16(c,S+30);ry=P.r16(c,S+32);ck('Final Courier has reachable real recipient',rx>=0 and ry>=0,dict(x=rx,y=ry,status=status()))
 if rx>=0:tp(rx,ry);P.run(c,2);P.press(c,'A',4,8);dismiss();ck('Final Courier completes via actual A delivery',P.r8(c,Q+1)==3,dict(status=status(),quest=list(raw(Q,20))));shot('courier')
 (O/'all-seven-quests.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,rom_sha256=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest(),note='All seven quest families tested in native final5. Real attacks, cargo mechanics and timers. Fresh SRAM/seed/player position/facing only; one control assignment for already drafted Mitts. No HP/enemy/completion/quest state writes.'),indent=2))
 print('ALL_SEVEN',sum(x['passed'] for x in checks),len(checks),flush=True)

if args.suite=='contract':
 leave();desk(7);P.press(c,'A',4,8);dismiss();desk(7);move_menu(1);P.press(c,'A',4,8)
 for i in range(600):
  if text():dismiss()
  if P.r8(c,P.sym('gGame'))==1 and site()!=0:break
  P.run(c,3)
 ck('Contract uses dedicated fresh event instance',site()==128,dict(status=status(),step=P.r8(c,H+offsets['contract_step']),target=P.r8(c,H+offsets['contract_target'])))
 shot('contract-first')
 
 
 def stepnum():return P.r8(c,H+offsets['contract_step'])
 def solve_board():
  idx=P.r16(c,P.sym('gHandoffPuzzleIndex'))&65535;data=struct.unpack('<II3B3B6B32B',raw(static('sPuzzlePool','handoff_events')+idx*52,52));blocks=list(data[2:5])
  for move in data[14:14+data[13]]:
   i,d=divmod(move,4);cell=blocks[i];dx=(0,1,0,-1)[d];dy=(-1,0,1,0)[d];tp((7+cell%5-dx)*16+8,(8+cell//5-dy)*16+14,d);P.run(c,3);P.press(c,'A',4,8);blocks[i]=(cell//5+dy)*5+cell%5+dx
 
 def travel_contract():
  leave();desk(7);move_menu(1);P.press(c,'A',4,8)
  for i in range(700):
   if text():dismiss()
   if P.r8(c,P.sym('gGame'))==1 and site()!=0:return
   P.run(c,3)
 
 def kill_until(fn,limit=2000):
  for i in range(limit):
   if fn():return True
   foes=[P.actor(c,j) for j in range(1,96) if P.actor(c,j)['kind']==2]
   if not foes:P.run(c,3);continue
   a=P.actor(c,0);e=foes[0]
   if a['state'] in (0,2):
    tp(e['x'],e['y']+24,0)
    if a['state']==0:P.press(c,'B',3,2)
    else:P.run(c,5)
   else:P.run(c,5)
   if P.r8(c,P.sym('gGame')+1)!=4:return False
  return False
 
 def claim():
  for i in range(80):
   if P.actor(c,0)['state']==0:break
   P.run(c,3)
  tp(16*16+8,11*16+14+18,0);P.run(c,3);P.press(c,'A',4,12);dismiss()
 
 target=P.r8(c,H+offsets['contract_target'])
 if target==10:solve_board()
 else:
  for i in range(6):
   if stepnum()>0:break
   tx,ty=7+i%3*8,7+i//3*8;tp(tx*16+8,ty*16+30,0);P.run(c,3);P.press(c,'R',4,20);P.press(c,'R',4,50)
 ck('Contract first actual event advances seal and awards Earth',stepnum()==1,dict(step=stepnum(),target=target,status=status()));claim();shot('contract-seal1')
 travel_contract();ck('Contract second instance entered',site()==129,status());before=P.r16(c,P.sym('gPl'));ok=kill_until(lambda:stepnum()>1)
 ck('Contract real wave/quest combat advances Fire seal',ok,dict(step=stepnum(),hp_before=before,hp_after=P.r16(c,P.sym('gPl')),status=status()));claim();shot('contract-seal2')
 if stepnum()==2:
  wanted=P.r16(c,H+offsets['contract_item'])&65535;travel_contract();ck('Contract item instance entered with16bit target',site()==130,dict(target=wanted,status=status()));ok=kill_until(lambda:done(130));claim()
  ck('Contract guaranteed requested item advances Water seal',ok and stepnum()==3,dict(target=wanted,step=stepnum(),status=status()));shot('contract-seal3')
 else:ck('Item already fulfilled by real bonus reward',stepnum()==3,status())
 if stepnum()==3:
  # A real fairy well refill before a long boss, with no HP writes.
  leave();challenge(6);tp(16*16+8,11*16+14);P.run(c,3);P.press(c,'A',4,12);dismiss();leave();desk(7);move_menu(1);P.press(c,'A',4,8)
  for i in range(700):
   if text():dismiss()
   if P.r8(c,P.sym('gGame'))==1 and site()==131:break
   P.run(c,3)
  ck('Contract boss instance entered',site()==131,status());hp=P.r16(c,P.sym('gPl'));ok=kill_until(lambda:stepnum()==4,5000)
  ck('Contract real boss completes Wind/four-seal reward',ok and P.r8(c,H+offsets['contract_state'])==2,dict(step=stepnum(),hp_before=hp,hp_after=P.r16(c,P.sym('gPl')),status=status()));shot('contract-complete')
 (O/'contract-full.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,rom_sha256=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest(),note='Native four-seal contract; actual swordkills andfairywellheal. Navigationfixturesonly; no enemy, HP, completion/counters/state edits.'),indent=2))
 print('FULL_CONTRACT',sum(x['passed'] for x in checks),len(checks),flush=True)

if args.suite=='meta':
 leave();desk(4);move_menu(1);P.press(c,'A',4,8);dismiss();ck('Entitlement mode enables through real trophy choice',P.r8(c,H+12)==1,status())
 desk(4);move_menu(2);P.press(c,'A',4,8);ck('Difficulty picker opens',P.r8(c,M+14)==9,status());move_menu(3);P.press(c,'A',4,8);dismiss();ck('Real mode/difficulty choice sets3',P.r8(c,H+10)==3 and P.r8(c,H+12)==1,status())
 before=list(raw(H,16));flags=raw(H+offsets['completed'],32);gilt=P.r16(c,P.sym('gPl')+4);shot('preference-saved')
 c.reset();P.run(c,60);ck('Profile preferences restored after reset',P.r8(c,H+10)==3 and P.r8(c,H+12)==1,dict(before=before,after=list(raw(H,16))))
 P.press(c,'START',4,8);assert settle(0);dismiss();ck('Run checkpoint and profile resume together',raw(H+offsets['completed'],32)==flags and P.r8(c,H+offsets['draft_state'])==2 and P.r16(c,P.sym('gPl')+4)==gilt,dict(status=status(),profile=list(raw(H,16))));shot('preference-resumed')
 (O/'meta-powercycle.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,rom_sha256=hashlib.sha256(Path(P.ROM).read_bytes()).hexdigest(),note='Actual trophy/difficulty choices trigger game save. Emulator reset, real Continue, run flags/inventory restored. No SRAM fixture after initial fresh clear.'),indent=2))
 print('META_POWER',sum(x['passed'] for x in checks),len(checks),flush=True)

if not all(result['passed'] for result in checks):
 raise SystemExit(1)
