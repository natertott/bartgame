#!/usr/bin/env python3
"""Use actual controls on live mechanism objects; no action/HP/AI fixtures."""
from pathlib import Path
import json
source=Path(__file__).with_name('handoff_objects_native.py').read_text()
exec(compile(source.split('for site in (28,29,30,31):')[0],str(Path(__file__).with_name('handoff_objects_native.py')),'exec'))
enter(c,28)
def mechanism(t):
 for i in range(P.r8(c,symbols['sObj']+8)):
  a=symbols['sObjects']+i*22
  if P.r8(c,a+12)==t:return a
 raise AssertionError(t)
def xy(at):return (P.r16(c,at),P.r16(c,at+2))
a=mechanism(0);x,y=xy(a);nav(c,x,y+18,0);P.hold(c,['R','UP'],1);P.run(c,40);check('R+direction pushes actual statue exactly one tile',xy(a)==(x,y-16),dict(before=[x,y],after=xy(a),hero=P.actor(c,0)));shot(c,'statue-push')
for t in (7,8):
 a=mechanism(t);x,y=xy(a);nav(c,x,y+18,0);P.press(c,'R',2,10);check('real R operates lever '+str(t),P.r8(c,a+13)==1,dict(type=t,state=P.r8(c,a+13)));shot(c,'lever-'+str(t))
a=mechanism(9);x,y=xy(a);nav(c,x,y+18,0);P.press(c,'A',1,25);check('actual sword cut activates hit lever',P.r8(c,a+13)==1,dict(type=9,state=P.r8(c,a+13)));shot(c,'hit-lever')
# The course prize comes from normal completion, not a completion fixture.
state=P.sym('gHandoffState');check('three real lever actions announce completion',P.r8(c,symbols['sObj']+28)==1,dict(goal_bits=P.r8(c,symbols['sObj']+11)));wait(c);shot(c,'completed-court')

enter(c,31)
def set_b(eq):
 P.w8(c,pl+10,eq);fixtures.append(dict(kind='equipped loadout only',B=eq));P.run(c,30)
set_b(3);a=mechanism(32);x,y=xy(a);nav(c,x,y+18,0);P.press(c,'B',1,30);check('real Lantern ignites light switch',P.r8(c,a+13)==1);shot(c,'lantern-light-switch')
set_b(6);a=mechanism(33);x,y=xy(a);nav(c,x,y+34,0);P.press(c,'B',1,25);check('original Bow arrow activates eye switch',P.r8(c,a+13)==1);shot(c,'bow-eye-switch')
set_b(14);a=mechanism(26);x,y=xy(a);nav(c,x,y+32,0);P.press(c,'B',1,20);check('real Pacci projectile flips pottery',P.r8(c,a+13)==1);shot(c,'pacci-flipped-pot')
set_b(13);a=mechanism(27);x,y=xy(a);nav(c,x,y+26,0);P.hold(c,'B',20);P.run(c,2)
loads=[i for i in range(1,96) if P.r8(c,P.sym('gActors')+i*64)==6 and P.r8(c,P.sym('gActors')+i*64+1)==20]
check('real Gust suction captures and releases a thrown load',P.r8(c,a+13)==1 and bool(loads),dict(loads=loads));shot(c,'gust-load-release')
set_b(19);a=mechanism(36);x,y=xy(a);nav(c,x,y+18,0)
P.w8(c,li+42,0x26);fixtures.append(dict(kind='bottle contents only',contents='ordinary water'));P.press(c,'B',1,28);check('ordinary water does not melt large ice',P.r8(c,a+13)==0)
P.w8(c,li+42,0x27);fixtures.append(dict(kind='bottle contents only',contents='mineral water'));P.press(c,'B',1,28);check('real mineral-water pour melts large ice',P.r8(c,a+13)==1 and P.r8(c,a+16)==0);shot(c,'mineral-water-melt')
set_b(12);a=mechanism(34);x,y=xy(a);nav(c,x,y+100,0);P.hold(c,'B',12);r=mechanism(41);check('raised Mirror Shield reflects real ray into receiver',P.r8(c,r+13)==1);shot(c,'mirror-reflected-ray')
(out/'report.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,views=views,rom_sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),notes=__doc__),indent=2))
