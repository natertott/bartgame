"""Original annex mechanisms, native32px canvases with16/24px silhouettes.

Broad stone/bronze masses share the existing material palette. Verb marks
(keyhole, eye, handle, flame, grate) use the brightest compact clusters.
These added pictures never replace a current tile or sprite.
"""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
import reboot_core as R

TYPES=('statue','grave','furniture','big_door','boss_door','light_door','metal_door',
 'pull_lever','push_lever','hit_lever','big_lever','float','lava','lily','fan',
 'whirlwind','steam','bar','chain','hidden_ladder','beanstalk','warp','trap',
 'rotating_trap','bridge','weather','pacci_pot','gust_load','torch','target',
 'switch','pull_rock','light_switch','eye_switch','light_ray','jar_portal','big_ice','frozen_flower','barrel_web','ladder_down','dest_hole','light_receiver')
DIGITS='0123456789abcdef'
def rows(im):return [''.join(DIGITS[im.getpixel((x,y))] for x in range(im.width)) for y in range(im.height)]
def paint(kind,state):
 im=Image.new('P',(32,32),0);d=ImageDraw.Draw(im)
 # Small subdued contact shadows make grounded props read as part of a room.
 if kind not in ('whirlwind','steam','bar','chain'):d.ellipse((4,25,28,30),fill=2)
 if kind in ('statue','grave','pull_rock'):
  d.rectangle((5,23,26,28),fill=1);d.rectangle((6,23,25,26),fill=5);d.line((7,23,24,23),fill=8)
  if kind=='statue':
   d.polygon([(11,5),(20,5),(23,12),(21,17),(23,23),(8,23),(10,16),(8,12)],fill=1)
   d.polygon([(12,6),(19,6),(21,12),(18,16),(20,21),(11,21),(13,16),(10,12)],fill=5)
   d.line((12,7,18,7),fill=8);d.line((14,9,14,13),fill=3);d.line((19,12,18,17),fill=3)
   d.rectangle((12,18,18,20),fill=12)
  elif kind=='grave':
   d.rectangle((13,3,18,22),fill=1);d.rectangle((7,8,24,14),fill=1)
   d.rectangle((14,4,17,21),fill=5);d.rectangle((8,9,23,13),fill=5);d.line((9,9,22,9),fill=8)
   d.point((15,7),fill=7);d.line((11,24,15,21),fill=4)
  else:
   d.polygon([(7,12),(16,7),(25,14),(26,21),(20,25),(9,24),(5,19)],fill=1)
   d.polygon([(8,13),(16,9),(23,15),(23,20),(19,23),(10,22),(7,18)],fill=5)
   d.line((10,13,15,11,19,13),fill=8);d.line((15,15,17,19,14,21),fill=3)
 elif kind=='furniture':
  d.rectangle((5,10,26,26),fill=1);d.rectangle((7,11,24,22),fill=11)
  d.rectangle((8,12,23,14),fill=13);d.rectangle((8,16,23,20),fill=9)
  d.line((10,24,10,29),fill=9,width=3);d.line((22,24,22,29),fill=9,width=3)
  d.rectangle((14,17,17,19),fill=14)
 elif kind.endswith('_door'):
  d.pieslice((1,0,30,26),180,360,fill=1);d.rectangle((1,13,30,29),fill=1)
  d.pieslice((3,2,28,26),180,360,fill=5);d.rectangle((3,13,28,28),fill=5)
  d.line((5,5,10,2,21,2,26,6),fill=8);d.line((3,14,7,14),fill=8);d.line((24,14,28,14),fill=8)
  d.pieslice((7,7,24,25),180,360,fill=1);d.rectangle((7,16,24,28),fill=1)
  if not state:
   d.rectangle((8,15,23,27),fill=10 if kind=='big_door' else 3)
   d.line((8,16,23,16),fill=14 if kind=='big_door' else 6)
   if kind=='big_door':
    d.ellipse((12,15,19,22),fill=1);d.polygon([(14,20),(17,20),(19,26),(12,26)],fill=1)
    d.line((12,16,12,19),fill=15)
   elif kind=='metal_door':
    for x in (10,15,20):d.line((x,12,x,27),fill=7,width=2)
   elif kind=='light_door':
    d.line((15,14,15,24),fill=13);d.line((11,19,20,19),fill=13);d.point((15,18),fill=15)
   else:
    d.polygon([(11,17),(14,15),(16,17),(19,15),(22,18),(16,24)],fill=12);d.line((16,17,16,23),fill=1)
 elif 'lever' in kind:
  d.rectangle((8,22,24,28),fill=1);d.rectangle((10,23,22,26),fill=5);d.line((10,23,22,23),fill=8)
  x=22 if state else 10;y=10 if kind!='big_lever' else 6
  d.line((16,24,x,y),fill=1,width=5);d.line((16,22,x,y),fill=11,width=3)
  d.ellipse((x-4,y-3,x+4,y+3),fill=1);d.ellipse((x-3,y-2,x+3,y+2),fill=14)
  if kind=='hit_lever':d.line((6,15,9,12),fill=15);d.point((5,12),fill=14)
  if kind=='push_lever':d.polygon([(25,20),(28,17),(28,23)],fill=14)
  if kind=='pull_lever':d.polygon([(4,20),(7,17),(7,23)],fill=14)
 elif kind in ('float','lava','lily','bridge'):
  if kind=='bridge' and not state:
   for x in (3,26):d.rectangle((x,18,x+2,28),fill=10)
  elif kind=='lily':
   d.ellipse((1,15,30,29),fill=1);d.ellipse((3,16,28,27),fill=5);d.pieslice((3,16,28,27),280,335,fill=0)
   d.line((7,20,15,23,24,19),fill=8)
  else:
   d.polygon([(1,18),(28,14),(31,23),(4,29)],fill=1)
   for y in (18,22,26):d.line((4,y,27,y-3),fill=12 if kind!='lava' else 6,width=3)
   d.line((6,16,8,27),fill=9);d.line((24,14,26,24),fill=9)
   if state:d.line((2,30,9,30),fill=7);d.line((22,28,30,28),fill=7)
 elif kind=='fan':
  d.rectangle((10,22,22,28),fill=3);d.ellipse((3,4,29,26),fill=1);d.ellipse((5,6,27,24),fill=5)
  d.ellipse((13,12,19,18),fill=14)
  points=[[(15,14),(6,8),(11,5),(17,11)],[(18,14),(25,7),(28,12),(21,17)],[(17,18),(20,25),(14,26),(12,19)]]
  for p in points:d.polygon(p,fill=7)
  for y in (9,14,19):d.line((5,y,26,y),fill=2)
  if state:d.line((10,1,19,1),fill=7)
 elif kind in ('whirlwind','steam'):
  if kind=='steam':d.ellipse((7,24,24,30),fill=1);d.ellipse((9,25,22,28),fill=5)
  for i,y in enumerate((6,12,18,24)):
   x=5+(i+state)%3*2;w=22-i*3
   d.arc((x,y,x+w,y+5),180,360,fill=8 if kind=='steam' else 7,width=2);d.line((x+3,y,x+w-3,y),fill=6)
 elif kind in ('bar','chain'):
  d.ellipse((10,14,22,26),fill=1);d.ellipse((12,16,20,24),fill=12 if kind=='chain' else 5)
  if kind=='chain':d.polygon([(15,16),(16,10),(20,16),(25,18),(21,21),(20,26),(16,23),(11,24)],fill=14);d.point((16,18),fill=15)
  else:d.line((10,18,22,22),fill=8,width=2);d.line((12,24,20,15),fill=7)
 elif kind=='hidden_ladder':
  if not state:
   d.rectangle((5,22,26,28),fill=3);d.line((6,22,25,22),fill=7);d.line((10,24,14,23),fill=2)
  else:
   d.rectangle((6,11,25,29),fill=1)
   for x in (9,22):d.line((x,12,x,28),fill=11,width=2)
   for y in (14,19,24,28):d.line((10,y,21,y),fill=14)
 elif kind=='beanstalk':
  top=2 if state else 19
  d.line((16,29,16,top),fill=1,width=5);d.line((15,28,15,top+1),fill=11,width=2)
  for y in range(top+3,28,6):
   d.polygon([(15,y+3),(6,y),(5,y-4),(12,y-3)],fill=12);d.polygon([(17,y),(25,y-3),(28,y-1),(21,y+3)],fill=10)
 elif kind=='warp':
  d.ellipse((1,13,30,30),fill=1);d.ellipse((3,15,28,28),fill=12);d.ellipse((6,17,25,26),fill=13)
  d.arc((7,17,24,25),15+state*80,300+state*80,fill=14,width=2);d.point((15,20),fill=15)
 elif kind in ('trap','rotating_trap'):
  d.rectangle((2,14,29,29),fill=1)
  if not state:
   for y in (15,20,25):d.rectangle((3,y,28,y+3),fill=11);d.line((4,y,27,y),fill=14)
   if kind=='rotating_trap':d.ellipse((13,19,19,25),fill=5)
  else:d.rectangle((4,17,27,27),fill=1);d.line((3,15,28,15),fill=6)
 elif kind=='weather':
  d.line((16,28,16,5),fill=1,width=4);d.line((15,27,15,6),fill=11)
  d.line((5,10,26,10),fill=14,width=2);d.polygon([(23,5),(30,10),(23,15)],fill=12)
  d.ellipse((11,2,20,9),fill=8);d.point((18,4),fill=1)
  if state:d.line((3,18,9,18),fill=7);d.line((23,23,29,23),fill=7)
 elif kind=='pacci_pot':
  b=(7,12,25,28) if not state else (7,19,25,28)
  d.ellipse(b,fill=1);d.ellipse((b[0]+2,b[1]+1,b[2]-2,b[3]-2),fill=11)
  if not state:d.rectangle((9,11,23,15),fill=1);d.line((10,11,22,11),fill=14);d.line((12,18,12,23),fill=14)
  else:d.line((9,27,23,27),fill=3);d.line((11,20,21,20),fill=14)
 elif kind=='gust_load':
  d.polygon([(8,21),(14,16),(23,18),(25,26),(17,29),(7,27)],fill=1)
  d.polygon([(10,21),(15,18),(21,20),(22,25),(17,27),(10,25)],fill=5);d.line((12,21,16,20,19,22),fill=8)
 elif kind in ('torch','light_switch'):
  d.rectangle((11,14,21,28),fill=1);d.rectangle((12,15,19,25),fill=10);d.line((13,15,13,24),fill=14)
  d.rectangle((9,12,23,16),fill=1);d.line((10,13,22,13),fill=14)
  if state:d.polygon([(11,10),(13,4),(16,1),(18,6),(23,8),(21,13),(15,15)],fill=12);d.polygon([(14,10),(16,6),(19,11),(16,13)],fill=15)
 elif kind in ('target','switch','eye_switch'):
  d.polygon([(3,19),(7,14),(25,14),(29,19),(27,28),(5,28)],fill=1)
  d.polygon([(5,19),(8,16),(23,16),(27,19),(25,25),(7,25)],fill=13 if not state else 5)
  d.line((7,17,23,17),fill=15 if not state else 8)
  if kind=='eye_switch':d.ellipse((9,18,23,24),fill=8);d.rectangle((14,18,17,24),fill=1)
  elif kind=='target':d.line((16,18,16,24),fill=15);d.line((12,21,20,21),fill=15)
  else:d.rectangle((11,19,21,23),fill=14 if not state else 6)
 if kind=='light_ray':
  d.rectangle((5,14,27,27),fill=1);d.rectangle((7,15,25,24),fill=10)
  d.ellipse((10,6,22,20),fill=1);d.ellipse((12,8,20,18),fill=14);d.ellipse((14,10,18,16),fill=15)
  d.line((16,17,16,31),fill=15,width=2)
 elif kind=='light_receiver':
  d.ellipse((5,5,27,27),fill=1);d.ellipse((7,7,25,25),fill=10)
  d.ellipse((10,10,22,22),fill=15 if state else 3);d.line((12,12,19,12),fill=8)
 elif kind=='jar_portal':
  d.ellipse((5,11,27,29),fill=1);d.ellipse((7,12,25,27),fill=11)
  d.rectangle((8,8,24,14),fill=1);d.line((9,9,23,9),fill=14);d.ellipse((11,10,21,14),fill=1)
  d.arc((10,18,23,26),170,330,fill=14);d.point((16,21),fill=15)
 elif kind=='big_ice':
  if not state:
   d.polygon([(2,8),(8,1),(25,2),(31,8),(29,28),(9,31),(0,24)],fill=1)
   d.polygon([(4,9),(9,3),(24,4),(28,9),(26,26),(9,28),(3,23)],fill=6)
   d.line((5,10,11,5,23,5),fill=8,width=2);d.line((9,24,23,10),fill=7,width=2);d.line((17,23,25,15),fill=8)
  else:d.ellipse((3,24,28,30),fill=6);d.line((7,25,16,25),fill=8)
 elif kind=='frozen_flower':
  d.line((16,28,16,13),fill=11,width=2);d.line((15,23,8,19),fill=12);d.line((17,21,24,18),fill=12)
  for x,y in ((10,9),(19,9),(10,17),(19,17)):d.ellipse((x-4,y-4,x+4,y+4),fill=7 if not state else 13)
  d.ellipse((12,10,21,19),fill=8 if not state else 15)
  if not state:d.polygon([(6,6),(24,4),(28,22),(7,26)],outline=8)
 elif kind=='barrel_web':
  d.ellipse((5,8,27,29),fill=1);d.ellipse((7,9,25,27),fill=11)
  d.rectangle((8,11,24,14),fill=3);d.rectangle((8,23,24,26),fill=3)
  d.line((11,15,11,22),fill=9);d.line((21,15,21,22),fill=9)
  if not state:
   for end in ((5,7),(26,7),(6,28),(27,29),(3,18),(29,18)):d.line((16,18,*end),fill=8)
   d.polygon([(8,12),(22,12),(24,23),(8,25)],outline=7)
  else:d.ellipse((11,15,23,26),fill=1)
 elif kind in ('ladder_down','dest_hole'):
  d.ellipse((2,13,30,30),fill=1);d.arc((3,13,29,29),180,360,fill=6,width=2)
  for x in (10,23):d.line((x,15,x,29),fill=11,width=2)
  for y in (17,22,27):d.line((11,y,22,y),fill=14)
  if kind=='ladder_down':d.polygon([(13,4),(19,4),(19,7),(23,7),(16,13),(9,7),(13,7)],fill=14)
  else:d.line((7,14,10,11),fill=15);d.line((23,12,27,14),fill=15)
 return im

def palette(kind):return 'blight' if kind=='warp' else 'iron'
def build_sheets():
 frames={};pals={}
 for kind in TYPES:
  for phase in (0,1):
   name=kind+('_active' if phase else '_idle');frames[name]=rows(paint(kind,phase));pals[name]=palette(kind)
 rain=Image.new('P',(8,8),0);rd=ImageDraw.Draw(rain);rd.line((5,0,2,5),fill=7);rd.point((2,5),fill=8)
 leaf=Image.new('P',(8,8),0);ld=ImageDraw.Draw(leaf);ld.polygon([(0,3),(3,1),(6,2),(5,5),(2,6)],fill=10);ld.line((1,4,5,2),fill=14)
 return [dict(name='handoff_mechanisms',w=32,h=32,pal='iron',frames=frames,frame_pal=pals),
         dict(name='handoff_weather',w=8,h=8,pal='iron',frames={'rain':rows(rain),'wind_leaf':rows(leaf),'ray': ['000ff000']*8})]

def write_review(destination):
 dst=Path(destination);dst.mkdir(parents=True,exist_ok=True);font=ImageFont.load_default()
 out=Image.new('RGB',(640,780),'#181820');d=ImageDraw.Draw(out);d.text((6,4),'ADDITIVE MECHANISM SOURCE ART | native32px, no old art changed',fill='#f8e8c0',font=font)
 for i,kind in enumerate(TYPES):
  x=8+(i%5)*126;y=24+(i//5)*82
  for p in (0,1):
   im=paint(kind,p);pal=R.PALETTES['blight' if palette(kind)=='blight' else 'stone'];im.putpalette([v for c in pal for v in R.rgb(c)]+[0]*720)
   out.paste(im.convert('RGB'),(x+p*42,y))
  d.text((x,y+36),kind,fill='#d8d0b0',font=font)
 out.save(dst/'mechanisms-source.png');(dst/'mechanisms-manifest.json').write_text(json.dumps({'types':TYPES,'native_canvas':[32,32],'poses':['idle','active'],'existing_art_changed':False},indent=2)+'\n')
if __name__=='__main__':
 import sys
 write_review(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/handoff-objects/source')
