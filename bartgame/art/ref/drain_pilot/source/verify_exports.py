#!/usr/bin/env python3
"""Independently reconstruct the delivered pilot scene from exported GBA bytes."""
import json,struct
from pathlib import Path
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent.parent
layout=json.loads((root/'layout.json').read_text())
char=(root/'gba/drain_bg_4bpp.chr').read_bytes()
assert len(char)%32==0
bankraw=(root/'gba/drain_bg_palettes.pal').read_bytes()
def rgb(c):
 r=c&31;g=(c>>5)&31;b=(c>>10)&31
 return [int(round(x*255/31)) for x in (r,g,b)]
pals=np.array([rgb(struct.unpack_from('<H',bankraw,i*2)[0]) for i in range(len(bankraw)//2)],dtype='uint8').reshape(13,16,3)

def unpack8(buf):
 vals=[]
 for b in buf:vals.extend((b&15,(b>>4)&15))
 return np.array(vals,dtype='uint8').reshape(8,8)

def reconstruct(name,opaque):
 raw=(root/'gba'/name).read_bytes()
 words=np.frombuffer(raw,dtype='<u2').reshape(32,32)
 res=np.zeros((160,240,4),dtype='uint8')
 for yy in range(20):
  for xx in range(30):
   entry=int(words[yy,xx]);idx=entry&1023;bank=(entry>>12)&15
   block=unpack8(char[idx*32:(idx+1)*32])
   dst=res[yy*8:yy*8+8,xx*8:xx*8+8]
   dst[:,:,:3]=pals[bank][block]
   dst[:,:,3]=255 if opaque else np.where(block>0,255,0).astype('uint8')
 return Image.fromarray(res,'RGBA')

ground=reconstruct('drain_bg2_ground.map',True)
overlay=reconstruct('drain_bg1_overlay.map',False)
for name,im in [('ground',ground),('overlay',overlay)]:
 expected=np.array(Image.open(root/'assets/bg'/f'{name}_240x160.png').convert('RGBA'))
 assert np.array_equal(np.array(im),expected),f'{name}: hardware readback pixel mismatch'
 im.save(root/'previews'/f'{name}_HARDWARE_RECONSTRUCTED.png')

# Verify OBJ bytes reconstruct sprite alpha and RGB (no game engine assumed).
objraw=(root/'gba/drain_obj_palettes.pal').read_bytes()
objpals=np.array([rgb(struct.unpack_from('<H',objraw,i*2)[0]) for i in range(256)],dtype='uint8').reshape(16,16,3)
objs=[]
for sp in layout['sprite_placement']:
 name=sp['name'];w,h=sp['size'];bank=sp['palette_bank_obj']
 data=(root/'gba'/f'obj_{name}_4bpp.bin').read_bytes()
 tilecnt=(w//8)*(h//8)
 assert len(data)==tilecnt*32
 canvas=np.zeros((h,w,4),dtype='uint8')
 i=0
 for y in range(0,h,8):
  for x in range(0,w,8):
   pix=unpack8(data[i*32:(i+1)*32]);i+=1
   canvas[y:y+8,x:x+8,:3]=objpals[bank][pix]
   canvas[y:y+8,x:x+8,3]=np.where(pix>0,255,0)
 ref=np.array(Image.open(root/'assets/sprites'/f'{name}_idle.png').convert('RGBA'))
 assert np.array_equal(canvas,ref),f'{name}: OBJ binary readback mismatch'
 objs.append((Image.fromarray(canvas,'RGBA'),int(sp['x']),int(sp['y'])))

master=ground.copy()
for im,x,y in objs:master.alpha_composite(im,(x,y))
master.alpha_composite(overlay)
actual=np.array(master.convert('RGB'))
expected=np.array(Image.open(root/'master_240x160.png').convert('RGB'))
assert np.array_equal(actual,expected)
master.convert('RGB').save(root/'previews'/'master_HARDWARE_RECONSTRUCTED_240x160.png')
print('PASS: independently decoded BG1, BG2, OBJ and exact master RGB: 0 mismatched pixels of 38400')
