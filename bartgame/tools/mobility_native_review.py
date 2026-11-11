#!/usr/bin/env python3
"""ActualmGBA input proof. Disclosed fixtures: private SRAM, seed, player
navigation position, matchedred half and2HP for realfall/death. Never writes
gates, completions, fusionflags, AI, terrain, palettes, OAM/VRAM or pixels.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
import mgba.core,mgba.image
import probe as P
from arcade_journal_review import profile,preferences,fnv
SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--bundle',required=True);a.add_argument('--out',required=True);a.add_argument('--catalogue',action='store_true');a=a.parse_args();bundle=Path(a.bundle);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 P.ROM=str(bundle/'bartgame.gba');P.MAP=str(bundle/'bartgame.map');P._syms=None;fields={};private={}
 with (bundle/'bartgame.elf').open('rb') as f:
  elf=ELFFile(f)
  private={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols() if s.name in ('sHandoffSite','sHandoffKind')}
  for cu in elf.get_dwarf_info().iter_CUs():
   for d in cu.iter_DIEs():
    n=d.attributes.get('DW_AT_name')
    if d.tag=='DW_TAG_typedef' and n and n.value.decode() in ('HandoffState','LegacyInventory','PlayerState') and n.value.decode() not in fields:
     r=d.get_DIE_from_attribute('DW_AT_type');fields[n.value.decode()]={x.attributes['DW_AT_name'].value.decode():x.attributes['DW_AT_data_member_location'].value for x in r.iter_children() if x.tag=='DW_TAG_member'}
   if len(fields)==3:break
 checks=[];fixtures=[];media=[];trace={}
 def at(t,k):return P.sym({'PlayerState':'gPl','HandoffState':'gHandoffState','LegacyInventory':'gLegacyInventory'}[t])+fields[t][k]
 def raw(c,p,n):return bytes(P.r8(c,p+i) for i in range(n))
 def w32(c,p,v):P.w16(c,p,v&65535);P.w16(c,p+2,v>>16)
 def status(c):return dict(gs=P.r8(c,P.sym('gGame')),area=P.r8(c,P.sym('gGame')+1),cell=P.r8(c,P.sym('gGame')+2),site=P.r8(c,private['sHandoffSite']),text=P.r8(c,P.sym('gTbActive')),mode=P.r8(c,P.sym('gMobilityMode')),layer=P.r8(c,P.sym('gMobilityLayer')),actor=P.actor(c,0))
 def check(n,v,detail=None):
  checks.append(dict(name=n,passed=bool(v),detail=detail));print('PASS' if v else 'FAIL',n,detail,flush=True)
  if not v:raise AssertionError(n)
 def shot(c,n):P.snap(c,str(out/(n+'.png')));media.append(n+'.png')
 def tp(c,x,y):w32(c,P.sym('gActors')+8,x<<16);w32(c,P.sym('gActors')+12,y<<16);fixtures.append(dict(kind='navigation position',x=x,y=y))
 def settle(c,area=None,cell=None):
  for _ in range(2400):
   if status(c)['text']:P.press(c,'A',2,5)
   else:P.run(c,3)
   s=status(c)
   if s['gs']==1 and not s['text'] and (area is None or s['area']==area) and (cell is None or (s['site'] if s['area']==4 else s['cell'])==cell):P.run(c,25);return
  raise RuntimeError(('settle',status(c),area,cell))
 def fresh(sram,start=False):
  c=mgba.core.load_path(P.ROM);c.bg_video=mgba.image.Image(240,160);c.set_video_buffer(c.bg_video);c.reset()
  for i,b in enumerate(sram):P.w8(c,0xe000000+i,b)
  P.run(c,45)
  if start:w32(c,P.sym('gSeedOverride'),0xb4a7);P.press(c,'START',2,4);settle(c,0)
  return c
 def drive(c,key,n,name=None):
  frames=[];rows=[];c.clear_keys(*range(10));c.set_keys(P.key(c,key))
  for i in range(n):
   c.run_frame();rows.append(status(c))
   if name and i%4==0:frames.append(c.bg_video.to_pil().convert('RGB').copy())
  c.clear_keys(*range(10));P.run(c,2)
  if name:frames[0].save(out/(name+'.gif'),save_all=True,append_images=frames[1:],duration=67,loop=0,optimize=False);media.append(name+'.gif');trace[name]=rows
  return rows
 def hub(c):tp(c,280,130);P.run(c,4);P.press(c,'A',2,5);settle(c,4,0)
 def choose(c,x,y,i,area=None,cell=None):
  tp(c,x*16+8,y*16+14);P.run(c,4);P.press(c,'A',2,4)
  for _ in range(i):P.press(c,'DOWN',2,3)
  P.press(c,'A',2,5)
  if area is not None:settle(c,area,cell)
 def course(c):
  choose(c,17,14,26,4,27);shot(c,'course')
  # Arrival is on the lower end ramp; leave that elevation with actual input
  # before any later navigation fixture moves us into another component.
  drive(c,'DOWN',8)
 try:
  sram=bytearray([255])*32768;old=profile(0xA50102,0x101,8);pref=preferences(2,1);sram[0x7ec0:0x7ee0]=old;sram[0x7f00:0x7f0c]=pref;fixtures.append(dict(kind='private serialized JRN1+appearance',items='0xA50102',enemies='0x101',earned=False))
  c=fresh(sram);check('native JRN1 migration preserves discoveries',P.r32(c,P.sym('gJournalItems'))==0xA50102 and (P.r16(c,P.sym('gJournalEnemies'))&65535)==0x101)
  check('native JRN2 published independently',P.r32(c,0xe007e40)==0x324e524a)
  check('migration preserves original records/settings',raw(c,0xe007ec0,32)==old and raw(c,0xe007f00,12)==pref)
  w32(c,P.sym('gSeedOverride'),0xb4a7);P.press(c,'START',2,4);settle(c,0);hub(c);course(c);check('real menu enters court',status(c)['site']==27,status(c))
  tp(c,72,343);P.run(c,25)
  oldeq=raw(c,at('PlayerState','equip'),3);olditems2=P.r8(c,at('PlayerState','items2'));oldowned=P.r32(c,at('LegacyInventory','owned'))
  P.w8(c,at('PlayerState','equip')+1,7);P.w8(c,at('PlayerState','equip')+2,16);P.w8(c,at('PlayerState','items2'),olditems2|2);w32(c,at('LegacyInventory','owned'),oldowned|(1<<21))
  gear_fixture=dict(kind='temporary transportation gear interference loadout',B='DrainCap',L='PegasusBoots',restored=False);fixtures.append(gear_fixture)
  P.press(c,'A',2,2);check('A boards realcart',status(c)['mode']==1,status(c));r=drive(c,'B',10,'cart-draincap-guard')
  check('DrainCap cannot overwrite cart state',all(x['mode']==1 and x['actor']['state']==0 for x in r),status(c))
  r=drive(c,'L',30,'cart');check('Boots cannot steal cart movement',all(x['mode']==1 and x['actor']['state']==0 for x in r),status(c));P.press(c,'A',2,2)
  for i in range(500):
   c.run_frame()
   if not status(c)['mode']:break
  check('A dismounts at safe stop',i<500 and status(c)['actor']['state']==0 and not P.r8(c,at('PlayerState','input_lock')),status(c));shot(c,'cart-stop')
  for index,b in enumerate(oldeq):P.w8(c,at('PlayerState','equip')+index,b)
  P.w8(c,at('PlayerState','items2'),olditems2);w32(c,at('LegacyInventory','owned'),oldowned);gear_fixture['restored']=True
  tp(c,88,110);P.run(c,25);P.press(c,'R',2,1);check('R launches parachute',status(c)['mode']==2,status(c));drive(c,'LEFT',40,'parachute');drive(c,'RIGHT',25)
  for i in range(250):
   c.run_frame()
   if not status(c)['mode']:break
  check('steered parachute lands lower shelf',i<250 and status(c)['actor']['y']==190 and status(c)['actor']['z']==0,status(c));shot(c,'parachute-land')
  tp(c,248,350);P.run(c,4);r=drive(c,'UP',200,'bridge-over');check('end ramp selects raised bridge',any(x['layer']==1 for x in r),status(c));check('raised route avoids waterfall',all(x['actor']['state']!=4 for x in r));drive(c,'UP',50);check('north bank exitsupperplane',status(c)['layer']==0,status(c))
  # Underlying water must not alter swimming speed or steal A gear input
  # when a real raised floor supports Flippers-owning feet.
  flipword=at('LegacyInventory','owned')+8;oldflip=P.r32(c,flipword);oldeqa=P.r8(c,at('PlayerState','equip'));oldarrows=P.r8(c,at('PlayerState','arrows'));olditems2=P.r8(c,at('PlayerState','items2'))
  support_fixture=dict(kind='temporary Flippers+bow gear control',restored=False);fixtures.append(support_fixture)
  w32(c,flipword,oldflip|(1<<6));P.w8(c,at('PlayerState','equip'),6);P.w8(c,at('PlayerState','items2'),olditems2|1);P.w8(c,at('PlayerState','arrows'),2)
  tp(c,248,110);P.run(c,3);r=drive(c,'DOWN',60,'bridge-flippers');check('Flippers retain drydeck walking speed',status(c)['layer']==1 and status(c)['actor']['y']>=180 and all(x['actor']['state']!=4 for x in r),status(c))
  body=status(c)['actor'];ground=P.r16(c,P.sym('gRoom')+2+(((body['y']-1)//16)*32+body['x']//16)*2)&65535
  waterid=int(__import__('re').search(r'^#define MT_LH_MOB_WATER (\d+)',(bundle/'assets.h').read_text(),__import__('re').M)[1]);check('gear control stands on deck above actualwater',ground==waterid and status(c)['layer']==1,dict(ground=ground,waterid=waterid,body=body))
  P.press(c,'A',2,5);check('deck A uses equippedbow instead of diving',P.r8(c,at('PlayerState','arrows'))==1,dict(arrows=P.r8(c,at('PlayerState','arrows')),state=status(c)))
  drive(c,'UP',100);check('Flipperdeck walk exits upper plane',status(c)['layer']==0,status(c))
  tp(c,168,174);P.run(c,4);check('Flippers support real lowerwater swimming',status(c)['layer']==0 and status(c)['actor']['state']==0,status(c))
  ammo_before=P.r8(c,at('PlayerState','arrows'));check('lowerwater divecontrol starts with readygear',P.r8(c,at('PlayerState','item_cooldown'))==0)
  P.press(c,'A',2,5);check('actual lowerwater A dives instead of firingbow',P.r8(c,at('PlayerState','arrows'))==ammo_before and status(c)['actor']['state']==0,dict(arrows=P.r8(c,at('PlayerState','arrows')),state=status(c)));shot(c,'lower-water-dive');P.run(c,100)
  P.w8(c,at('PlayerState','equip'),oldeqa);P.w8(c,at('PlayerState','items2'),olditems2);P.w8(c,at('PlayerState','arrows'),oldarrows);w32(c,flipword,oldflip);support_fixture['restored']=True
  tp(c,168,174);r=drive(c,'RIGHT',10,'lower-water-control');check('unsupported lowerwater still drowns',any(x['actor']['state']==4 for x in r),status(c));P.run(c,45)
  tp(c,120,238);P.run(c,5);r=drive(c,'RIGHT',190,'bridge-under');check('lower bank passes under bridge',all(x['layer']==0 for x in r),status(c));shot(c,'underpass')
  tp(c,248,350);drive(c,'DOWN',24);settle(c,4,0)
  shape=P.r8(c,at('HandoffState','fuser_shape')+2);P.w8(c,at('HandoffState','kinstone_shapes')+6+shape,1);P.w16(c,at('LegacyInventory','kinstones')+4,1);fixtures.append(dict(kind='one matching redhalf ingredient',shape=shape,earned=False));choose(c,22,8,2);settle(c,4,0)
  check('real fusion consumes ingredient',P.r8(c,at('HandoffState','fusion_flags'))&4 and P.r8(c,at('HandoffState','kinstone_shapes')+6+shape)==0)
  course(c);tp(c,424,206);drive(c,'UP',90,'red-fusion');check('physical bridge reaches island',status(c)['actor']['y']<128,status(c))
  before=P.r16(c,at('PlayerState','gilt'))&65535;tp(c,424,110);P.run(c,4);P.press(c,'A',2,5);settle(c,4,27);after=P.r16(c,at('PlayerState','gilt'))&65535;check('cache grants100gilt',after-before==100);shot(c,'cache-claimed');P.press(c,'A',2,5);settle(c,4,27);check('cache is onceonly',(P.r16(c,at('PlayerState','gilt'))&65535)==after)
  P.w16(c,at('PlayerState','hp'),2);fixtures.append(dict(kind='2HP before genuine pitfall/death'));tp(c,360,174);P.run(c,5);drive(c,'RIGHT',22)
  for i in range(1200):
   c.run_frame()
   if status(c)['area']==0 and status(c)['gs']==1:break
  check('genuine hazard death saves base+extension',i<1200 and P.r32(c,0xe000000)==0x54524142,status(c))
  saved=raw(c,0xe000000,32768);(out/'private-checkpoint.sav').write_bytes(saved);check('independent extension+meta published',any(struct.unpack_from('<I',saved,o)[0]==0x58455243 for o in (0x4000,0x5000)) and any(struct.unpack_from('<I',saved,o)[0]==0x50485242 for o in (0x7d00,0x7d80)))
  cold=fresh(saved);P.press(cold,'START',2,4);settle(cold,0);check('coldContinue restores gilt+fusion',(P.r16(cold,at('PlayerState','gilt'))&65535)==after and P.r8(cold,at('HandoffState','fusion_flags'))&4);check('coldContinue retains cache completion',P.r8(cold,at('HandoffState','completed')+3)&8);check('coldContinue retains old discoveries',P.r32(cold,P.sym('gJournalItems'))&0xA50102==0xA50102 and P.r16(cold,P.sym('gJournalEnemies'))&0x101==0x101);check('appearance retained',raw(cold,0xe007f00,12)==pref);shot(cold,'cold-continue')
  if a.catalogue:
   # An explicit complete catalogue fixture proves native high-index artwork
   # and scrolling without claiming those memories were earned this session.
   known=bytearray([255])*32768
   data=struct.pack('<IHHI',0x324e524a,2,64,77)+((1<<146)-1).to_bytes(20,'little')+((1<<84)-1).to_bytes(12,'little')+bytes(16)
   known[0x7e40:0x7e80]=data+struct.pack('<I',fnv(data));known[0x7f00:0x7f0c]=pref
   fixtures.append(dict(kind='complete JRN2 catalogue UI fixture',items=146,enemies=84,earned=False))
   cat=fresh(known,start=True);cx=P.r16(cat,P.sym('gCabinetX'));cy=P.r16(cat,P.sym('gCabinetY'));tp(cat,cx,cy+20);P.run(cat,3);drive(cat,'UP',2);P.press(cat,'A',2,4)
   check('cabinet opens actualcomplete catalogue',status(cat)['gs']==7,status(cat))
   for _ in range(25):P.press(cat,'RIGHT',2,3)
   check('catalogue reaches appended goldhalf146',P.r8(cat,P.sym('gArcadePreviewFrame'))==121)
   shot(cat,'gold-half-index');P.press(cat,'A',2,3);shot(cat,'gold-half-notes');P.press(cat,'B',2,3);P.press(cat,'R',2,4)
   for _ in range(14):P.press(cat,'RIGHT',2,3)
   check('catalogue reaches enemy84withnativebossframe',P.r8(cat,P.sym('gArcadeCursor'))==83 and P.r8(cat,P.sym('gArcadePreviewFrame'))==2 and (P.r16(cat,P.sym('gArcadePreviewTiles'))&65535)>0)
   shot(cat,'peak-boss-index');P.press(cat,'A',2,3);shot(cat,'peak-boss-notes');P.press(cat,'B',2,3);P.press(cat,'B',2,3);check('catalogue returns to liveDrain',status(cat)['gs']==1 and status(cat)['area']==0)

 finally:
  (out/'report.json').write_text(json.dumps(dict(passed=sys.exc_info()[0] is None and all(x['passed'] for x in checks),error=str(sys.exc_info()[1]) if sys.exc_info()[1] else None,checks=checks,fixtures=fixtures,media=media,traces=trace,rom_sha256=SHA((bundle/'bartgame.gba').read_bytes()),tool_sha256=SHA(Path(__file__).read_bytes()),method=__doc__),indent=2)+'\n')
if __name__=='__main__':main()
