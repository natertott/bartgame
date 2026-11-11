#!/usr/bin/env python3
"""Play the actual Cream tool trials, graph gates and peak in mGBA.

Hero navigation/facing/standing and the selected new-run seed are disclosed
fixtures. Every trial completion, earned tool, equipment change, gate reaction,
climb/fall/cave transition and enemy HP change comes from real game input.
No inventory grant, player health, enemy state/health, completion, terrain,
VRAM, palette or framebuffer is assigned. This is a mechanic proof using
navigation fixtures, not an unassisted playthrough.

Use --stop-after-long-drop --seed 5 or --seed 1432 to qualify the3/4-row falls.
"""
from pathlib import Path
import sys,ctypes as C,json,hashlib,struct,argparse,atexit
import probe as P,cream_graph_review as G
import mgba.core,mgba.image
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True);parser.add_argument('--out',required=True);parser.add_argument('--seed',type=lambda x:int(x,0),default=0xb4a7);parser.add_argument('--stop-after-long-drop',action='store_true');parser.add_argument('--panoramas',action='store_true');args=parser.parse_args()
out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True);bundle=Path(args.bundle).resolve()
P.ROM=str(bundle/'bartgame.gba');P.MAP=str(bundle/'bartgame.map');P._syms=None
checks=[];fixtures=[];review_complete=False;fatal_errors=[];harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def w32(c,addr,n):P.w16(c,addr,n&65535);P.w16(c,addr+2,(n>>16)&65535)
def raw(c,addr,size):return bytes(P.r8(c,addr+i) for i in range(size))
def world(c):return G.World.from_buffer_copy(raw(c,P.sym('gCreamWorld'),C.sizeof(G.World)))
def status(c):return dict(state=P.r8(c,P.sym('gGame')),area=P.r8(c,P.sym('gGame')+1),cell=P.r8(c,P.sym('gGame')+2),node=P.r8(c,P.sym('gCreamNode')),actor=P.actor(c,0),text=P.r8(c,P.sym('gTbActive')))
def shot(c,name):P.snap(c,str(out/(name+'.png')))
def tp(c,x,y):
 a=P.sym('gActors');w32(c,a+8,x<<16);w32(c,a+12,y<<16);w32(c,a+16,0);P.w8(c,a+2,0);fixtures.append(dict(kind='hero position/standing/facing navigation',x=x,y=y,frame=P.r32(c,P.sym('gGame')+8),area=P.r8(c,P.sym('gGame')+1),cell=P.r8(c,P.sym('gGame')+2)))
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail));print('PASS' if ok else 'FAIL',name,flush=True)
c=mgba.core.load_path(P.ROM);c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
for i in range(32768):P.w8(c,0x0e000000+i,255)
P.run(c,45);w32(c,P.sym('gSeedOverride'),args.seed);P.press(c,'START',2,4)
for i in range(2200):
 if P.r8(c,P.sym('gTbActive')):P.press(c,'A',2,6)
 else:P.run(c,4)
 if P.r8(c,P.sym('gGame'))==1 and P.r8(c,P.sym('gActors'))==1 and not P.r8(c,P.sym('gTbActive')):break
check('real new run boots',status(c)['area']==0,status(c));shot(c,'sewer')
tp(c,28*16+8,6*16+34);P.run(c,3);P.press(c,'A',2,6)
for i in range(1200):
 if P.r8(c,P.sym('gTbActive')):P.press(c,'A',2,6)
 else:P.run(c,3)
 if P.r8(c,P.sym('gGame'))==1 and P.r8(c,P.sym('gGame')+1)==3 and not P.r8(c,P.sym('gTbActive')):break
check('real sewer ascent enters Cream',status(c)['area']==3,status(c));shot(c,'cream-entry')
w=world(c);print('World',w.entry_node,'->',w.goal_node,'rewards',list(w.reward_node),flush=True)
(out/'initial.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),world=G.plain(w)),indent=2))

trace=[];active_capture=None;local_drop_proved=False
def drive(key,limit,pred):
 c.clear_keys(*range(10));c.set_keys(P.key(c,key))
 for i in range(limit):
  c.run_frame();trace.append(status(c))
  if active_capture is not None and i%2==0:active_capture.append((status(c),c.bg_video.to_pil().convert('RGB').copy()))
  if pred():break
 c.clear_keys(*range(10));P.run(c,2)
 return i+1
import collections,re,math
DEFS={n:int(v) for n,v in re.findall(r'^#define\s+(\w+)\s+(\d+)\s*$',(bundle/'assets.h').read_text(),re.M)}
def dismiss(limit=800):
 for i in range(limit):
  st=status(c)
  if st['area']==3 and st['state']==1 and not st['text'] and st['actor']['state'] not in (6,13):return True
  if st['text']:P.press(c,'A',2,6)
  else:P.run(c,2)
 return False
def gp():return P.sym('gPl')
def reward():return P.r8(c,P.sym('gCreamProgress')+32)
def owned(item):return bool(P.r32(c,P.sym('gLegacyInventory')+(item//32)*4)&(1<<(item%32)))
def equip(item,key='A'):
 P.press(c,'START',2,4);P.press(c,'SELECT',2,4)
 inv=[i for i in range(1,118) if owned(i) and not(P.r8(c,P.sym('gLegacyItemDefs')+i*16+12)&2)]
 check('earned item is present in real satchel',item in inv,dict(item=item,possessions=inv))
 if item not in inv:return False
 for _ in range(inv.index(item)):P.press(c,'RIGHT',2,3)
 P.press(c,key,2,4);shot(c,'equip-%02x'%item);P.press(c,'START',2,6)
 return True
def face(f):
 P.w8(c,P.sym('gActors')+7,f);fixtures.append(dict(kind='hero facing navigation',facing=f,frame=P.r32(c,P.sym('gGame')+8)))
def core_status():return dict(status(c),rewards=reward(),items=P.r8(c,gp()+8),hp=P.r16(c,gp()),bombs=P.r8(c,gp()+7),equip=list(raw(c,gp()+9,3)))
def review_exception(kind,value,tb):
 fatal_errors.append(str(value));sys.__excepthook__(kind,value,tb)
sys.excepthook=review_exception
def save_report():
 (out/'report.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,seed=args.seed,scope_complete=review_complete,errors=fatal_errors,harness_sha256=harness_sha256,assets_header_sha256=hashlib.sha256((bundle/'assets.h').read_bytes()).hexdigest(),final=core_status(),sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),limitations='Navigation fixtures select hero position, standing state and facing. Seed and erased in-memory SRAM are explicit start fixtures. All equipment choices and tools/rewards/combat use real input. No enemy HP/state, inventory grants, player health, completion, gates, terrain, palette, VRAM or framebuffer writes.'),indent=2))
atexit.register(save_report)
def return_from_trial():
 tp(c,16*16+8,21*16+14);P.run(c,3);drive('DOWN',100,lambda:status(c)['area']!=4);return dismiss()

def available_tokens():
 m=P.r8(c,gp()+8);return (1 if m&2 else 0)|(2 if m&4 else 0)|(4 if m&8 and owned(0x12) else 0)
def shortest(goal,tokens):
 start=P.r8(c,P.sym('gCreamNode'));q=[start];prev={start:None}
 for n in q:
  if n==goal:break
  for i in range(w.degree[n]):
   e=w.edges[n][i]
   if e.require&tokens!=e.require or e.target in prev:continue
   prev[e.target]=(n,i);q.append(e.target)
 if goal not in prev:raise AssertionError(('no admitted route',start,goal,tokens))
 path=[];n=goal
 while prev[n] is not None:
  a,i=prev[n];path.append((a,i));n=a
 return path[::-1]
def type_at(x,y):
 mt=P.r16(c,P.sym('gRoom')+2+(y*32+x)*2);return P.r8(c,P.sym('metatile_type')+mt)
def gate_open(n,i):return bool(P.r8(c,P.sym('gCreamOpenEdges')+n)&(1<<i))
def use_gate(n,i,e):
 if not e.require or gate_open(n,i) or e.require==7:return
 r=P.sym('gCreamRoom');cx=P.r8(c,r+3);t=n&1;wy=6 if t else 19;other=e.target//2
 if e.kind==1:
  left=other%5<(n//2)%5;px=40 if left else 472;py=wy*16+14;f=3 if left else 1;gx=1 if left else 30;gy=wy
 elif e.kind==4:
  px=112;py=(wy+1)*16+14;f=0;gx=6;gy=wy
 elif e.kind==2:
  gx=cx;gy=P.r8(c,r+36+cx) if other==n//2 else 2
  px=cx*16+16;py=(gy+1)*16+14;f=0
 else:
  gx=27 if e.flags&1 else 10 if t else cx;gy=min(P.r8(c,r+4+gx),P.r8(c,r+4+gx+1)) if t else 22
  px=gx*16+16;py=(gy-1)*16+14;f=2
 if e.require&2:equip(0x0f,'A')
 elif list(raw(c,gp()+9,3))[0]!=2:equip(7,'A')
 for attempt in range(3):
  tp(c,px,py);face(f);P.press(c,'A',2,35)
  if gate_open(n,i):break
 check('real tool clears generated route barrier',gate_open(n,i),dict(node=n,edge=i,require=e.require,kind=e.kind,actor=P.actor(c,0),gate_type=type_at(gx,gy)))
 if not gate_open(n,i):raise AssertionError(('gate did not clear',n,i,e.require))
 shot(c,'opened-gate-%d'%n)

def edge(n,i):
 global active_capture,review_complete,local_drop_proved
 if P.r16(c,gp())==0:raise AssertionError('hero died before route')
 e=w.edges[n][i];use_gate(n,i,e);r=P.sym('gCreamRoom');cx=P.r8(c,r+3);t=n&1;cell=n//2;target=e.target//2
 P.run(c,26)
 if e.kind==1:
  left=target%5<cell%5;tp(c,20 if left else 492,(6 if t else 19)*16+14);drive('LEFT' if left else 'RIGHT',100,lambda:P.r8(c,P.sym('gCreamNode'))==e.target and status(c)['state']==1)
 elif e.kind==2:
  if target==cell:
   yy=min(P.r8(c,r+4+cx),P.r8(c,r+4+cx+1));tp(c,(cx+1)*16+8,(yy+1)*16+7)
  else:tp(c,(cx+1)*16+8,24)
  drive('UP',250,lambda:P.r8(c,P.sym('gCreamNode'))==e.target and status(c)['state']==1)
 elif e.kind==3:
  xx=27 if e.flags&1 else 10 if t else cx;yy=min(P.r8(c,r+4+xx),P.r8(c,r+4+xx+1)) if t else 22
  tp(c,xx*16+16,yy*16+12)
  takeoff_y=P.actor(c,0)['y'];capture_local=target==cell and not local_drop_proved
  if e.flags&1 or capture_local:active_capture=[]
  drive('DOWN',600,lambda:P.r8(c,P.sym('gCreamNode'))==e.target and status(c)['state']==1)
  for tick in range(40):
   c.run_frame()
   if active_capture is not None and tick%2==0:active_capture.append((status(c),c.bg_video.to_pil().convert('RGB').copy()))
  if capture_local:
   samples=active_capture;active_capture=None;fall=[st['actor'] for st,im in samples if st['actor']['state']==5 and st['actor']['z']>0]
   check('local drop begins at the physical takeoff lip',bool(fall) and abs(fall[0]['y']-fall[0]['z']-takeoff_y)<=3,dict(takeoff_y=takeoff_y,first=fall[0] if fall else None))
   speed=[fall[k]['z']-fall[k+1]['z'] for k in range(len(fall)-1)]
   check('local drop accelerates down and lands upright',len(speed)>5 and sum(speed[-3:])>=sum(speed[:3]) and P.actor(c,0)['z']==0 and P.actor(c,0)['state']==0,dict(speed=speed,landed=P.actor(c,0)))
   images=[im for st,im in samples]
   if images:images[0].save(out/'local-drop.gif',save_all=True,append_images=images[1:],duration=33,loop=0,optimize=False)
   (out/'local-drop.json').write_text(json.dumps(dict(takeoff_y=takeoff_y,frames=[st for st,im in samples]),indent=2));local_drop_proved=True
  if e.flags&1:
   samples=active_capture;active_capture=None;span=target//5-cell//5;cells=list(dict.fromkeys(st['cell'] for st,im in samples))
   check('long drop renders every intervening actual room',cells==list(range(cell,target+1,5)),dict(span=span,cells=cells))
   check('long drop physically lands on its requested terrace',P.r8(c,P.sym('gCreamNode'))==e.target and P.actor(c,0)['z']==0 and status(c)['area']==3,dict(target=e.target,landed=core_status()))
   images=[im for st,im in samples]
   if images:images[0].save(out/('drop-%d-rooms.gif'%span),save_all=True,append_images=images[1:],duration=33,loop=0,optimize=False)
   for cc in cells:
    settled=[im for st,im in samples if st['cell']==cc]
    settled[len(settled)//2].save(out/('drop-%d-cell-%d.png'%(span,cc)))
   (out/'long-drop.json').write_text(json.dumps(dict(span=span,cells=cells,frames=[st for st,im in samples],fixtures=fixtures,checks=checks,sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest()),indent=2))
   if args.stop_after_long_drop:
    review_complete=all(row['passed'] for row in checks)
    if any(not row['passed'] for row in checks):raise SystemExit(1)
    raise SystemExit(0)
 elif e.kind==4:
  yy=6 if t else 19;tp(c,7*16,(yy+1)*16+14);drive('UP',130,lambda:P.r8(c,P.sym('gCreamNode'))==e.target and status(c)['state']==1)
 check('real graph edge reaches target',P.r8(c,P.sym('gCreamNode'))==e.target and status(c)['area']==3,dict(node=n,index=i,target=e.target,kind=e.kind,status=core_status()))
 if P.r8(c,P.sym('gCreamNode'))!=e.target:raise AssertionError('route stalled')
 dismiss();return e
def go(goal):
 for n,i in shortest(goal,available_tokens()):edge(n,i)
def mission(which):
 go(w.reward_node[which]);r=P.sym('gCreamRoom')+68+(w.reward_node[which]&1)*24+22;mx,my=P.r8(c,r),P.r8(c,r+1)
 tp(c,mx*16+8,my*16+22);P.run(c,26);P.press(c,'A',2,6)
 for _ in range(800):
  if status(c)['area']==4 and status(c)['state']==1 and not status(c)['text']:break
  if status(c)['text']:P.press(c,'A',2,6)
  else:P.run(c,3)
 check('real task%d opens'%(which+1),status(c)['area']==4,core_status());shot(c,'trial%d-enter'%(which+1))
def enemies():return [(i,P.actor(c,i)) for i in range(1,96) if P.r8(c,P.sym('gActors')+i*64)==2]
def task_done(site):return bool(P.r8(c,P.sym('gHandoffState')+89+(site>>3))&(1<<(site&7)))
def combat(kind,limit=600):
 damage=[]
 for iteration in range(limit):
  if task_done(161 if kind=='trial2-wave' else 162):break
  es=enemies()
  if not es:
   P.run(c,10)
   if not enemies():break
   continue
  i,e=es[0];hp=e['hp'];x,y=e['x'],e['y'];f=e['facing']
  if e['type']==16 and e['state']!=7:
   # The propeller has a real grounded recovery; chasing its immune flight
   # is deliberately ineffective. Stay clear until that authored window.
   tp(c,max(48,min(464,x+96 if x<256 else x-96)),y if e['state'] in (0,1) else (80 if y>192 else 320));P.run(c,8)
  elif e['type'] in (74,75,76,77):
   # Stand in range to bait the real tell, then wait beside its locked cut.
   if e['state'] not in (2,3,4):tp(c,x+30,y);P.run(c,2)
   elif e['state'] in (2,3):tp(c,x,y+45);P.run(c,4)
   else:tp(c,x-22,y);face(1);P.press(c,'B',2,22)
  else:
   tp(c,x-24,y);face(1);P.press(c,'B',2,22)
  after=P.actor(c,i)
  if after['kind']!=2 or after['hp']!=hp:damage.append(dict(iteration=iteration,type=e['type'],before=hp,after=after['hp'] if after['kind']==2 else 0))
  if status(c)['actor']['state']==7:raise AssertionError(('player died in real combat',kind,iteration,e,damage))
 check(kind+' defeated by actual attacks',task_done(161 if kind=='trial2-wave' else 162),dict(hits=damage,remaining=enemies(),status=core_status()));shot(c,kind+'-finished')
 if not task_done(161 if kind=='trial2-wave' else 162):raise AssertionError(('combat stalled',kind,enemies()))
def panorama(name):
 from PIL import Image
 folder=out/name;folder.mkdir(exist_ok=True);views=[];images={};clock=256
 before=raw(c,P.sym('gRoom'),10242);mosaic=Image.new('RGB',(512,384));xs=(0,136,272);ys=(0,112,224);xb=(0,188,324,512);yb=(0,136,248,384)
 for j,y in enumerate(ys):
  for i,x in enumerate(xs):
   P.w16(c,P.sym('gForestReviewCamera'),x);P.w16(c,P.sym('gForestReviewCamera')+2,y);w32(c,P.sym('gForestReviewClock'),clock);P.w8(c,P.sym('gForestReviewEnabled'),1)
   for _ in range(5):w32(c,P.sym('gFrame'),clock-1);P.run(c,1)
   image=c.bg_video.to_pil().convert('RGB').copy();image.save(folder/('camera-%d-%d.png'%(x,y)));images[i,j]=image
   world=[xb[i],yb[j],xb[i+1],yb[j+1]];crop=[world[0]-x,world[1]-y,world[2]-x,world[3]-y]
   mosaic.paste(image.crop(crop),world[:2]);views.append(dict(camera=[x,y],file='camera-%d-%d.png'%(x,y),source_crop=crop,world_crop=world))
 mosaic.save(folder/'full-room.png')
 exact=all(mosaic.crop(v['world_crop']).tobytes()==images[i%3,i//3].crop(v['source_crop']).tobytes() for i,v in enumerate(views))
 check(name+' mosaic copies actual native camera pixels',exact)
 check(name+' camera fixture preserves generated room/collision',before==raw(c,P.sym('gRoom'),10242))
 fixtures.append(dict(kind='camera-only HUD-free panorama',clock=clock,views=views))
 (folder/'provenance.json').write_text(json.dumps(dict(method='Nine untouched240x160 mGBA camera frames;512x384 is a literal disjoint crop mosaic, not a single GBA screen.',views=views,clock=clock,room_unchanged=before==raw(c,P.sym('gRoom'),10242),crop_copy_exact=exact,sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest()),indent=2))
 P.w8(c,P.sym('gForestReviewEnabled'),0);P.run(c,2)
# The new area must be escapable through its visible entrance without a
# return item or a death. This is an actual A interaction, not a forced area.
door=P.sym('gCreamRoom')+116;dx,dy=P.r8(c,door),P.r8(c,door+1)
tp(c,(dx+1)*16,(dy+1)*16+14);P.run(c,25);shot(c,'cream-return-stairs');P.press(c,'A',2,6)
for _ in range(800):
 if status(c)['area']==0 and status(c)['state']==1:break
 if status(c)['text']:P.press(c,'A',2,6)
 else:P.run(c,3)
P.run(c,80)
check('visible entry returns to Drain without an escape item',status(c)['area']==0 and status(c)['state']==1,status(c));shot(c,'returned-to-drain')
if status(c)['area']!=0:raise AssertionError('visible entry return failed')
tp(c,28*16+8,6*16+34);P.run(c,3);P.press(c,'A',2,6)
for _ in range(800):
 if status(c)['area']==3 and status(c)['state']==1 and not status(c)['text']:break
 if status(c)['text']:P.press(c,'A',2,6)
 else:P.run(c,3)
check('Drain ascent re-enters the same generated Cream',status(c)['area']==3 and P.r8(c,P.sym('gCreamNode'))==w.entry_node,status(c))
if args.panoramas:panorama('healthy-room')
mission(0)
# Solve whichever of the three generated four-switch rules was selected.
for plate in (0,1,2,3,0,2):
 tp(c,(9+plate*4)*16+8,10*16+14);P.run(c,4)
# No completion memory is assigned: the actual switch inputs set the result.
shot(c,'trial1-switches-finished');return_from_trial()
check('first real trial earns Blightseeds',bool(reward()&1) and owned(7) and bool(P.r8(c,gp()+8)&2),core_status());shot(c,'earned-bombs');equip(7,'A')

mission(1);combat('trial2-wave');return_from_trial();check('second real trial earns Lamp',bool(reward()&2) and bool(P.r8(c,gp()+8)&4),core_status());shot(c,'earned-lamp')
if args.panoramas:panorama('sick-room')
mission(2);combat('trial3-darknut');return_from_trial();check('third real trial earns Cape and Pacci',reward()==7 and owned(0x12) and bool(P.r8(c,gp()+8)&8),core_status());shot(c,'earned-cape-pacci')
go(w.goal_node);check('real route reaches peak with three earned gifts',status(c)['area']==3 and P.r8(c,P.sym('gCreamNode'))==w.goal_node,core_status());shot(c,'peak-real-arrival')
if args.panoramas:panorama('peak-room')
(out/'progression.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),final=core_status()),indent=2))
# The final encounter uses its real painted-head Pacci target and raised back.
equip(0x12,'A');boss_trace=[];boss_frames=[];exposed=False;mounted=False
for attack in range(180):
 es=[(i,e) for i,e in enemies() if e['type']==83]
 if not es:break
 i,e=es[0];before=e['hp']
 if e['state']!=7:
  # Lure the actual head to face north, then shoot south into that front.
  hx=e['x']+1;hy=e['y']-48
  if hy<60:tp(c,e['x'],e['y']+32);face(0);P.run(c,45);continue
  tp(c,hx,hy-20);face(2);P.run(c,32)
  e=P.actor(c,i);hx=e['x']+(6 if e['facing']==1 else -5 if e['facing']==3 else 1);hy=e['y']-48
  tp(c,hx,hy-20);face(2);P.press(c,'A',2,20)
  now=P.actor(c,i);exposed|=now['state']==7
  if now['state']==7:shot(c,'peak-pacci-exposes-core')
 else:
  tp(c,e['x'],e['y']+8);face(0);P.run(c,2);mounted|=P.actor(c,0)['z']>=12
  P.hold(c,'B',2)
  for f in range(22):
   c.run_frame()
   if f%3==0:boss_frames.append(c.bg_video.to_pil().convert('RGB').copy())
  now=P.actor(c,i)
  if now['kind']!=2 or now['hp']!=before:shot(c,'peak-core-hit-%03d'%attack)
 boss_trace.append(dict(attack=attack,before=e,after=now,player=P.actor(c,0),health=P.r16(c,gp())))
 if P.r16(c,gp())==0:break
check('Pacci genuinely opens the painted peak head',exposed)
check('Bloom genuinely mounts the exposed back',mounted)
check('peak defeated through actual Pacci and raised sword hits',not any(e['type']==83 for _,e in enemies()),dict(status=core_status(),trace=boss_trace))
P.run(c,80);shot(c,'peak-result')
if boss_frames:boss_frames[0].save(out/'peak-core-combat.gif',save_all=True,append_images=boss_frames[1:],duration=50,loop=0,optimize=False)
(out/'peak-combat.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,boss_trace=boss_trace,sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),final=core_status()),indent=2))

review_complete=all(row['passed'] for row in checks)
if not review_complete:raise SystemExit(1)
