#!/usr/bin/env python3
"""Exercise real Minish and Four Sword inputs in the authored secrets court.

Reuses the review's public boot/loadout/navigation helpers, never C state,
HP, AI, geometry or completion writes. Native PNGs are untouched mGBA output.
"""
from pathlib import Path
import json
# Shared review bootstrap before its gallery loop. It parses --bundle/--out,
# declares disclosed fixtures, boots the actual ROM and records normal input.
source=Path(__file__).with_name('handoff_objects_native.py').read_text()
exec(compile(source.split('for site in (28,29,30,31):')[0],str(Path(__file__).with_name('handoff_objects_native.py')),'exec'))
enter(c,30)
nav(c,56,312,1);P.press(c,'R',2,8);P.run(c,70);shot(c,'shrink-on-real-portal')
start=P.player_pos(c);P.hold(c,'RIGHT',64);P.run(c,20);end=P.player_pos(c)
check('Minish exits real four-pixel gap into enclosed floor',112<end[0]<144 and end[1]==312,dict(start=start,end=end,hero=P.actor(c,0)))
shot(c,'inside-minish-pocket')
# Restore the form through the actual portal, not a state fixture.
nav(c,56,312,1);P.press(c,'R',2,8)
nav(c,184,312,1);c.set_keys(P.key(c,'A'));P.run(c,45)
c.set_keys(P.key(c,'A'),P.key(c,'RIGHT'));P.run(c,94)
c.clear_keys(*range(10));P.run(c,8);shot(c,'clone-formation')
def bodies():
 at=P.sym('gOam');n=P.r16(c,P.sym('gOamCount'))
 return [i for i in range(n) if (P.r16(c,at+i*8+4)&1023)==0]
check('real charge, pad walk and release create three copies',len(bodies())==4,dict(position=P.player_pos(c),body_oam=bodies()))
P.hold(c,'UP',10);P.run(c,8);shot(c,'clone-pressure-plates')
# The primary stands aside while three copies occupy their real plate
# footprints. Read only the live mechanism state, never force completion.
rows=[]
for i in range(P.r8(c,symbols['sObj']+8)):
 at=symbols['sObjects']+22*i
 if P.r8(c,at+12) in (6,30):rows.append(dict(type=P.r8(c,at+12),x=P.r16(c,at),y=P.r16(c,at+2),state=P.r8(c,at+13),solid=P.r8(c,at+16)))
check('three real clone footprints latch their bonus gate',sum(r['type']==30 and r['state']==1 for r in rows)==3 and any(r['type']==6 and r['state']==1 and not r['solid'] for r in rows),rows)
# A real sword press uses the original current-phase FX on every copy.
P.press(c,'A',1,5);shot(c,'clone-sword-same-phase')
check('formation stays intact through ordinary sword use',len(bodies())==4,dict(body_oam=bodies(),hero=P.actor(c,0)))
(out/'report.json').write_text(json.dumps(dict(checks=checks,fixtures=fixtures,views=views,rom_sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),notes=__doc__),indent=2))
