#!/usr/bin/env python3
"""Actual mGBA HUD review; fixtures affect inventory/navigation, never pixels.

A bundle contains bartgame.gba, bartgame.map, assets.h and source-commit.txt.
Only screenshot crops/contact sheets and a decoded HUD-plane diagnostic are
made after capture. Native PNGs are unchanged 240x160 mGBA framebuffers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import traceback

from PIL import Image, ImageDraw

import probe as P
import critical_path as C
import bloom_probe as B
from sewer_concept_audit import NativeRom

SHA = lambda data: hashlib.sha256(data).hexdigest()
SIZES = (((8,8),(16,16),(32,32),(64,64)),
         ((16,8),(32,8),(32,16),(64,32)),
         ((8,16),(8,32),(16,32),(32,64)))


def read(core, at, count):
    head=bytearray()
    while count and at&3:
        head.append(P.r8(core,at));at+=1;count-=1
    words=count//4
    if words:head.extend(struct.pack('<%dI'%words,*(core.memory.u32[at+i*4] for i in range(words))))
    at+=words*4;count-=words*4
    head.extend(P.r8(core,at+i) for i in range(count))
    return bytes(head)


def rgb(value):
    return tuple(((value>>shift)&31)*255//31 for shift in (0,5,10))


def hardware_hud(core):
    """Decode native BG0 and priority-zero OBJ into RGB555; -1 is clear.

    This is an explicitly labelled inspection layer, never a replacement
    framebuffer. Only ordinary un-affined 4bpp sprites are valid for this HUD.
    """
    pixels = [-1]*(240*160)
    control = P.r16(core,0x04000008)&65535
    charbase = 0x06000000+((control>>2)&3)*16384
    mapbase = 0x06000000+((control>>8)&31)*2048
    palette = struct.unpack('<256H',read(core,0x05000000,512))
    atlas = read(core,charbase,32768)
    entries = struct.unpack('<1024H',read(core,mapbase,2048))
    for ty in range(20):
        for tx in range(30):
            entry = entries[ty*32+tx]
            tile, pal = entry&1023, entry>>12
            if not tile:
                continue
            for y in range(8):
                sy = 7-y if entry&0x800 else y
                for x in range(8):
                    sx = 7-x if entry&0x400 else x
                    ink = (atlas[tile*32+sy*4+sx//2]>>((sx&1)*4))&15
                    if ink:
                        pixels[(ty*8+y)*240+tx*8+x] = palette[pal*16+ink]
    # Later OBJ entries are lower priority; resolve the same order as GBA.
    obj = read(core,0x06010000,32768)
    opal = struct.unpack('<256H',read(core,0x05000200,512))
    oam = []
    for i in range(128):
        a0,a1,a2 = struct.unpack('<3H',read(core,0x07000000+i*8,6))
        if a0&0x300==0x200 or (a2>>10)&3 or a0>>14==3:
            continue
        if a0&0x100 or a0&0x2000:
            raise AssertionError('HUD affine/8bpp sprite requires explicit decoder')
        w,h=SIZES[a0>>14][a1>>14]
        ox,oy = a1&511,a0&255
        if ox>=256:ox-=512
        if oy>=160:oy-=256
        if ox+w<=0 or ox>=240 or oy+h<=0 or oy>=160:
            continue
        oam.append(dict(index=i,x=ox,y=oy,width=w,height=h,tile=a2&1023,palette=a2>>12))
    for entry in reversed(oam):
        i=entry['index'];a0,a1,a2=struct.unpack('<3H',read(core,0x07000000+i*8,6))
        w,h,ox,oy=entry['width'],entry['height'],entry['x'],entry['y']
        for y in range(h):
            for x in range(w):
                px,py=ox+x,oy+y
                if not(0<=px<240 and 0<=py<160):continue
                sx=w-1-x if a1&0x1000 else x
                sy=h-1-y if a1&0x2000 else y
                tile=(a2&1023)+(sy//8)*(w//8)+sx//8
                ink=(obj[tile*32+(sy%8)*4+(sx%8)//2]>>((sx&1)*4))&15
                if ink:pixels[py*240+px]=opal[(a2>>12)*16+ink]
    return pixels,oam


def crop_pixels(pixels, box):
    x0,y0,x1,y1=box
    return tuple(pixels[y*240+x] for y in range(y0,y1) for x in range(x0,x1))


def bounds(pixels, box=(0,0,240,160)):
    x0,y0,x1,y1=box
    pts=[(x,y) for y in range(y0,y1) for x in range(x0,x1) if pixels[y*240+x]>=0]
    return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1] if pts else None


class Review:
    def __init__(self,args):
        self.args=args;self.bundle=Path(args.bundle).resolve();self.out=Path(args.out).resolve()
        self.out.mkdir(parents=True,exist_ok=True)
        self.rom=NativeRom(self.bundle)
        P.MAP=str(self.bundle/'bartgame.map');P._syms=None
        C.mt=lambda name:self.rom.defs['MT_'+name]
        self.rows=[];self.media=[];self.frames=[];self.scenes=[];self.hardware=[]
        self.state_snapshots=[]
        self.button_boxes=json.loads(args.button_boxes)
        self.fixtures=[
            'Pinned seed0xb4a7 through the ordinary title Start path.',
            'Resource/equipment fixtures exercise all inventory icons, ten hearts, full16-bit gilt and byte ammunition extremes; those values are not claimed as a naturally earned inventory.',
            'Developer navigation positions Bloom or requests the existing room transition, without modifying terrain, tile art, palette, framebuffer, enemies HP or earned rewards.',
            'Enemy removal isolates HUD readability. The original real rooms and simulation are otherwise retained.',
            'A minimap all-visited fixture reveals every cell for blink/readability checks; natural entry screenshots retain ordinary exploration state.',
            'Actual A/B/L controls drive item use/button feedback; no HUD variables, input globals, animation clocks or game frames are written.',
        ]

    def check(self,name,passed,detail=None):
        row=dict(name=name,passed=bool(passed))
        if detail is not None:row['detail']=detail
        self.rows.append(row)
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)

    def boot(self,start=True):
        return P.boot(rom=str(self.bundle/'bartgame.gba'),seed=self.args.seed,start=start)

    def shot(self,core,name,hud=True):
        path=self.out/(name+'.png');P.snap(core,str(path))
        self.media.append(dict(file=path.name,sha256=SHA(path.read_bytes()),size=[240,160],kind='untouched actual mGBA framebuffer'))
        if hud:
            px,oam=hardware_hud(core)
            mp=next((e for e in oam if e['tile']==1008),None)
            top=bounds(px,(0,0,240,64))
            self.hardware.append(dict(file=path.name,gFrame=P.r32(core,P.sym('gFrame')),top_bounds=top,minimap=mp,oam=oam,
                top_ink_count=sum(p>=0 for p in px[:240*32]),open_center_clear=all(px[y*240+x]<0 for y in range(24) for x in range(116,140))))
            self.check(name+' top HUD stays within24px',top is not None and top[3]<=24,top)
            self.check(name+' leaves north-center opening',self.hardware[-1]['open_center_clear'])
            self.source_icons(core,name,oam)
            self.counter_glyphs(core,name,px)
            if name=='09-healthy-forest':self.fog_check(core,px,oam)
            if name=='11-mystery' and self.args.phase=='after':self.parent_map_check(core,px,oam)
        return path

    def source_icons(self,core,label,oam):
        metadata,data=self.rom.sheet('huditems')
        frames={1:'SWORD',2:'BOMBS',3:'LAMP',4:'CLOAK',5:'SHIELD',6:'BOW',7:'HUBCAP'}
        for slot in range(3):
            eq=P.r8(core,P.sym('gPl')+9+slot)
            obj=next((e for e in oam if e['tile']==876+slot*16),None)
            if not eq:
                self.check(label+' empty slot%d has no item OBJ'%slot,obj is None)
                continue
            name=frames[eq]
            if eq==5 and P.r8(core,P.sym('gPl')+36)&16:name='SHIELD_UPGRADED'
            frame=self.rom.defs['F_ICON32_'+name]
            size=metadata['frame_tiles']*32
            self.check(label+' slot%d uses exact native%s icon'%(slot,name),
                obj is not None and read(core,0x06010000+(876+slot*16)*32,size)==data[frame*size:(frame+1)*size])
            if obj is not None:
                expected=P.r8(core,P.sym('huditems_frame_pal')+frame)
                self.check(label+' slot%d uses correct item palette'%slot,obj['palette']==expected)

    def counter_glyphs(self,core,label,pixels):
        digits=((7,5,5,5,7),(2,6,2,2,7),(7,1,7,4,7),(7,1,7,1,7),
                (5,5,7,1,1),(7,4,7,1,7),(7,4,7,5,7),(7,1,1,1,1),
                (7,5,7,5,7),(7,5,7,1,7))
        ink=P.r16(core,0x05000000+self.rom.defs['PAL_SLOT_HUD']*32+9*2)&65535
        def matches(x,y,value):
            chars=str(value)
            return all((pixels[(y+dy)*240+x+i*4+dx]==ink)==bool(digits[int(ch)][dy]&(4>>dx))
                       for i,ch in enumerate(chars) for dy in range(5) for dx in range(3))
        self.check(label+' actual gilt glyphs match full resource value',matches(94,3,P.r16(core,P.sym('gPl')+4)&65535))
        if self.args.phase!='after':return
        for slot in range(3):
            eq=P.r8(core,P.sym('gPl')+9+slot)
            x=149+30*slot
            if eq in (2,6):
                count=P.r8(core,P.sym('gPl')+(7 if eq==2 else 35))
                self.check(label+' slot%d actual ammo glyphs match%d'%(slot,count),matches(x,14,count))
            else:
                self.check(label+' slot%d has no unrelated ammo label'%slot,
                           all(pixels[y*240+xx]!=ink for y in range(14,19) for xx in range(x,x+11)))

    def fog_check(self,core,pixels,oam):
        mp=next(e for e in oam if e['tile']==1008)
        pitch=4 if mp['width']==32 else 3
        inset=2 if pitch==4 else 1
        extent=3 if pitch==4 else 2
        ink=P.r16(core,0x05000200+self.rom.defs['PAL_OBJ_UIKIT']*32+self.rom.defs['UI_INK_RAISED']*2)&65535
        unseen=[]
        for i in range(25):
            flags=P.r8(core,P.sym('gWorld')+4+i*13+11)
            if flags&1 or i==C.cell(core):continue
            cx=mp['x']+inset+pitch*(i%5);cy=mp['y']+inset+pitch*(i//5)
            unseen.append((i,all(pixels[(cy+y)*240+cx+x]==ink for y in range(extent) for x in range(extent))))
        self.check('natural entry minimap keeps unvisited rooms undisclosed',len(unseen)>0 and all(ok for _,ok in unseen),unseen)

    def parent_map_check(self,core,pixels,oam):
        mp=next((e for e in oam if e['tile']==1008),None)
        parent=C.cell(core);entry=self.world['entry']
        gold=P.r16(core,0x05000200+self.rom.defs['PAL_OBJ_UIKIT']*32+self.rom.defs['UI_INK_GOLD']*2)&65535
        def center(cell):
            return pixels[(mp['y']+3+4*(cell//5))*240+mp['x']+3+4*(cell%5)] if mp else -1
        values=dict(parent_cell=parent,entry_cell=entry,parent_center_rgb555=center(parent),entry_center_rgb555=center(entry),marker_gold_rgb555=gold)
        self.check('mystery minimap locates player in actual parent room',
                   C.area(core)==2 and parent!=entry and center(parent)==gold and center(entry)!=gold,values)

    def wait(self,core,pred,n=1200):
        for _ in range(n):
            if pred():return True
            P.run(core,1)
        return False

    def warp(self,core,area,cell,side=0):
        C.dismiss(core)
        for name,value in (('sNextArea',area),('sNextCell',cell),('sNextSide',side),('sTransPhase',0)):
            P.w8(core,B.static_symbol(name),value)
        P.w8(core,P.sym('gGame'),2)
        self.check('requested transition settles area%d cell%d'%(area,cell),self.wait(core,lambda:C.gstate(core)==1 and C.area(core)==area and (area==0 or C.cell(core)==cell)))
        C.dismiss(core);C.clear_enemies(core);P.run(core,30)

    def setup_inventory(self,core,equipment=(1,5,2),hp=80,gilt=65535,bombs=99,arrows=99):
        pl=P.sym('gPl')
        P.w16(core,pl, hp);P.w16(core,pl+2,80);P.w16(core,pl+4,gilt)
        P.w8(core,pl+7,bombs);P.w8(core,pl+8,0x7f);P.w8(core,pl+35,arrows);P.w8(core,pl+36,0x0f)
        for i,e in enumerate(equipment):P.w8(core,pl+9+i,e)
        P.run(core,30)

    def intro(self):
        core=self.boot(start=False)
        P.w16(core,P.sym('gSeedOverride'),self.args.seed&65535)
        P.w16(core,P.sym('gSeedOverride')+2,self.args.seed>>16)
        P.press(core,'START',2,90)
        self.check('ordinary opening text is active',self.wait(core,lambda:P.r8(core,P.sym('gTbActive'))!=0))
        P.run(core,150)
        self.shot(core,'13-unnamed-opening-dialogue',hud=False)
        _,oam=hardware_hud(core)
        if self.args.phase=='after':self.check('unnamed dialogue suppresses map over continuation arrow',not any(e['tile']==1008 for e in oam))
        C.dismiss(core);P.run(core,30)
        self.check('opening dialogue closes back to gameplay',C.gstate(core)==1 and not P.r8(core,P.sym('gTbActive')))
        self.shot(core,'14-after-unnamed-dialogue')

    def dialogue_shop(self,core):
        C.teleport(core,21*16+8,7*16+4);P.hold(core,'UP',6);P.press(core,'A',2,100)
        self.check('actual wizard conversation opens named dialogue',P.r8(core,P.sym('gTbActive'))!=0)
        self.shot(core,'15-named-wizard-dialogue',hud=False)
        _,oam=hardware_hud(core)
        if self.args.phase=='after':self.check('named dialogue suppresses map over continuation arrow',not any(e['tile']==1008 for e in oam))
        C.dismiss(core,frames=1000);P.run(core,30)
        self.check('wizard dialogue closes back to gameplay',not P.r8(core,P.sym('gTbActive')))
        self.shot(core,'16-after-wizard-dialogue')
        C.teleport(core,4*16+8,7*16+6);P.hold(core,'UP',8);P.press(core,'A',3,60)
        self.check('actual frog market opens',P.r8(core,B.static_symbol('sShopActive'))!=0)
        self.shot(core,'17-frog-market',hud=False)
        P.press(core,'B',3,48);C.dismiss(core);P.run(core,30)
        self.check('frog market returns to gameplay',not P.r8(core,B.static_symbol('sShopActive')) and not P.r8(core,P.sym('gTbActive')))
        self.shot(core,'18-after-market')

    def title(self):
        core=self.boot(start=False)
        self.check('ordinary boot reaches native title',C.gstate(core)==0)
        self.shot(core,'01-title',hud=False)
        P.press(core,'DOWN',2,6);P.press(core,'A',2,50)
        self.check('real title Options opens',P.r8(core,P.sym('gTitleOptions'))!=0)
        self.shot(core,'02-options',hud=False)
        P.press(core,'RIGHT',2,8);P.press(core,'DOWN',2,8);P.press(core,'RIGHT',2,8)
        P.press(core,'B',2,30)
        self.check('Options returns to native title',P.r8(core,P.sym('gTitleOptions'))==0 and C.gstate(core)==0)

    def world_snapshot(self,core,label):
        data={'room':SHA(read(core,P.sym('gRoom'),10242)),
              'bg1':SHA(read(core,0x0600C000,8192)),
              'bg2':SHA(read(core,0x0600E000,8192)),
              'bg3':SHA(read(core,0x06006000,8192)),
              'world':SHA(read(core,P.sym('gWorld'),329))}
        self.state_snapshots.append(dict(label=label,area=C.area(core),cell=C.cell(core),hashes=data))
        return data

    def menus(self,core):
        before=self.world_snapshot(core,'before item/map/zoom menu')
        P.press(core,'START',2,90)
        self.check('Start opens item menu',C.gstate(core)==4 and P.r8(core,P.sym('gMenuStudyPage'))==0)
        self.shot(core,'20-items',hud=False)
        P.press(core,'R',2,65)
        self.check('R reaches key menu',P.r8(core,P.sym('gMenuStudyPage'))==1)
        self.shot(core,'21-key-items',hud=False)
        P.press(core,'R',2,90)
        self.check('R reaches overview map',P.r8(core,P.sym('gMenuStudyPage'))==2)
        self.shot(core,'22-map',hud=False)
        P.press(core,'A',2,90)
        self.check('A reaches room zoom',P.r8(core,P.sym('gMenuStudyZoom'))==1)
        self.shot(core,'23-map-zoom',hud=False)
        P.press(core,'B',2,80);P.press(core,'START',2,50)
        self.check('Start returns to gameplay',C.gstate(core)==1)
        after=self.world_snapshot(core,'after item/map/zoom menu')
        for key,value in before.items():self.check('menu restores '+key,after[key]==value)
        self.shot(core,'24-after-menu')

    def scene(self,core,name):
        self.setup_inventory(core,(2,5,6),hp=68)
        path=self.shot(core,name)
        self.scenes.append(path)

    def contexts(self):
        core=self.boot();C.dismiss(core);C.clear_enemies(core)
        self.check('ordinary Start enters Drain',C.gstate(core)==1 and C.area(core)==0)
        C.teleport(core,200,156);P.run(core,30)
        self.scene(core,'03-drain')
        self.setup_inventory(core,(3,4,7),gilt=999)
        self.shot(core,'04-lantern-cape-hubcap')
        self.setup_inventory(core,(1,5,0),hp=4,gilt=0)
        self.shot(core,'05-sword-shield-halfheart')
        self.setup_inventory(core,(2,6,5),bombs=0,arrows=0)
        self.shot(core,'06-zero-ammunition')
        self.setup_inventory(core,(2,6,1),bombs=255,arrows=255)
        self.shot(core,'07-byte-ammunition-extremes')
        self.setup_inventory(core,(0,0,0),hp=4)
        # Preserve a non-dead body while exercising empty hearts.
        P.w16(core,P.sym('gPl'),4);P.run(core,30)
        self.shot(core,'08-empty-equipment')
        self.setup_inventory(core,(1,5,2),hp=80)
        P.enter_forest(core);C.dismiss(core);C.clear_enemies(core);P.run(core,30)
        self.world=C.world(core)
        self.check('real Drain ladder enters forest entry',C.area(core)==1 and C.cell(core)==self.world['entry'])
        self.scene(core,'09-healthy-forest')
        self.menus(core)
        # The selected seeded cell4 is naturally deep (stage4), not recolored.
        deep=max(range(25),key=lambda i:self.world['cells'][i]['stage'])
        side=next(i for i,g in enumerate(self.world['cells'][deep]['gate']) if g)
        self.warp(core,1,deep,side)
        self.check('deep scene uses natural high-blight cell',self.world['cells'][deep]['stage']>=3,dict(cell=deep,stage=self.world['cells'][deep]['stage']))
        self.scene(core,'10-deep-forest')
        self.motion(core)
        self.buttons(core)
        self.walk_timing(core)
        # Real mystery from one of the existing mandatory key-item trials.
        target=self.world['key_cell'][0]
        side=next(i for i,g in enumerate(self.world['cells'][target]['gate']) if g)
        self.warp(core,1,target,side)
        self.check('real mystery mouth enters generated interior',C.enter_trial(core))
        C.dismiss(core);C.clear_enemies(core);P.run(core,30)
        self.scene(core,'11-mystery')
        self.warp(core,0,0)
        self.scene(core,'12-drain-return')
        self.dialogue_shop(core)

    def motion(self,core):
        self.setup_inventory(core,(1,5,2),hp=80,gilt=999,bombs=9)
        # Reveal-only fixture for a readable5x5 grid.
        for i in range(25):
            at=P.sym('gWorld')+4+i*13+11
            P.w8(core,at,P.r8(core,at)|1)
        # Force only a normal entry reload through the existing transition.
        side=next(i for i,g in enumerate(self.world['cells'][C.cell(core)]['gate']) if g)
        self.warp(core,1,C.cell(core),side)
        folder=self.out/'motion-native';folder.mkdir(exist_ok=True)
        frames=[];rows=[];maps=[]
        for i in range(180):
            P.run(core,1)
            px,oam=hardware_hud(core)
            mp=next(e for e in oam if e['tile']==1008)
            visible=bounds(px,(mp['x'],mp['y'],min(240,mp['x']+mp['width']),min(160,mp['y']+mp['height'])))
            box=visible
            piece=crop_pixels(px,box)
            maps.append(piece)
            path=folder/('%03d.png'%i);P.snap(core,str(path))
            frames.append(Image.open(path).convert('RGB'))
            rows.append(dict(frame=i,gFrame=P.r32(core,P.sym('gFrame')),run_frames=P.r32(core,P.sym('gGame')+8),file=str(path.relative_to(self.out)),sha256=SHA(path.read_bytes()),minimap=mp,visible_bounds=visible,minimap_sha256=SHA(struct.pack('<%dh'%len(piece),*piece)),top_sha256=SHA(struct.pack('<%dh'%(240*24),*px[:240*24]))))
        self.frames.extend(rows)
        idle_deltas=self.logic_deltas(rows)
        if self.args.phase=='after':self.check('180-frame idle sample keeps near-baseline logic cadence',idle_deltas.get('0',0)<=4 and all(int(k)<=1 for k in idle_deltas),idle_deltas)
        # Compare native room faces rather than border animation. The current
        # marker alone should blink; all other revealed rooms remain steady.
        current=C.cell(core)
        pitch=4 if rows[0]['minimap']['width']==32 else 3
        inset=2 if pitch==4 else 1
        extent=3 if pitch==4 else 2
        cells_by_frame=[]
        for image in maps:
            # maps is the tightly cropped visible marker plane (16 or24px).
            mw=rows[0]['visible_bounds'][2]-rows[0]['visible_bounds'][0]
            cells=[]
            for cell in range(25):
                cx=inset+pitch*(cell%5);cy=inset+pitch*(cell//5)
                cells.append(tuple(image[(cy+y)*mw+cx+x] for y in range(extent) for x in range(extent)))
            cells_by_frame.append(cells)
        cell_uniques=[len({v[i] for v in cells_by_frame}) for i in range(25)]
        if self.args.phase=='after':
            self.check('current room alone has two visible blink phases',cell_uniques[current]==2,dict(cell=current,unique=cell_uniques))
            self.check('non-current room faces do not flash with border',all(n==1 for i,n in enumerate(cell_uniques) if i!=current),cell_uniques)
            self.check('current marker stays distinct in both phases',all(row[current] not in [x for i,x in enumerate(row) if i!=current] for row in cells_by_frame))
        unique_map=len(set(r['minimap_sha256'] for r in rows));unique_top=len(set(r['top_sha256'] for r in rows))
        self.check('180 actual HUD simulation frames captured',len(rows)==180)
        self.check('native minimap hardware allocation valid',all(r['minimap']['tile']+r['minimap']['width']*r['minimap']['height']//64<=1024 for r in rows))
        if self.args.phase=='after':
            self.check('minimap width grows about25percent',20<=rows[0]['visible_bounds'][2]-rows[0]['visible_bounds'][0]<=26,rows[0]['visible_bounds'])
            self.check('minimap animates in actual hardware pixels',unique_map>=2,unique_map)
            self.check('gold top border shimmer animates in actual hardware pixels',unique_top>=2,unique_top)
        sampled=frames[::6]
        sampled[0].save(self.out/'hud-shimmer-and-map.gif',save_all=True,append_images=sampled[1:],duration=100,loop=0,optimize=False)
        contact=Image.new('RGB',(480,320),(0,0,0))
        for i,index in enumerate((0,32,64,96)):contact.paste(frames[index],((i%2)*240,(i//2)*160))
        contact.save(self.out/'motion-contact.png')
        self.motion_summary=dict(native_frame_count=180,emulator_frames_per_second=262144/4389,gif_sample_step=6,gif_duration_ms=100,unique_minimap=unique_map,unique_top=unique_top,room_face_unique_states=cell_uniques,idle_logic_delta_histogram=self.logic_deltas(rows),first_map=rows[0]['minimap'],first_visible_bounds=rows[0]['visible_bounds'])

    def buttons(self,core):
        self.setup_inventory(core,(5,5,5),hp=80,gilt=999)
        # All three fixture slots share a shield, isolating press identity.
        # Buttons still invoke the actual player use routine.
        records=[]
        for slot,key in enumerate(('A','B','L')):
            core.clear_keys(*range(10));P.run(core,30)
            neutral,_=hardware_hud(core)
            self.shot(core,'button-'+key+'-released')
            core.set_keys(P.key(core,key));P.run(core,4)
            pressed,_=hardware_hud(core)
            self.shot(core,'button-'+key+'-held')
            held=P.r16(core,P.sym('gKeysHeld'))&65535
            self.check(key+' physical input reaches real key scanner',bool(held&(1<<P.key(core,key))),held)
            changes=[]
            for box in self.button_boxes:
                a,b=crop_pixels(neutral,box),crop_pixels(pressed,box)
                changes.append(sum(x!=y for x,y in zip(a,b)))
            core.clear_keys(P.key(core,key));P.run(core,2)
            short_release,_=hardware_hud(core)
            if self.args.phase=='after':
                box=self.button_boxes[slot]
                self.check(key+' release keeps brief readable afterglow',crop_pixels(short_release,box)==crop_pixels(pressed,box))
            P.run(core,38)
            released,_=hardware_hud(core)
            records.append(dict(key=key,slot=slot,held_bits=held,changed_pixels_by_box=changes,
                released_hashes=[SHA(struct.pack('<%dh'%len(crop_pixels(released,b)),*crop_pixels(released,b))) for b in self.button_boxes]))
            if self.args.phase=='after':
                self.check(key+' illuminates its associated button label',changes[slot]>=3,changes)
                # Border glints may move outside these label-only boxes.
                self.check(key+' leaves other button labels unchanged',all(changes[i]==0 for i in range(3) if i!=slot),changes)
        self.button_summary=records

    @staticmethod
    def logic_deltas(rows):
        result={}
        for before,after in zip(rows,rows[1:]):
            delta=after['run_frames']-before['run_frames']
            result[str(delta)]=result.get(str(delta),0)+1
        return result

    def walk_timing(self,core):
        # Find a genuine open feet strip in the existing room; never inject a
        # replacement floor or turn off collision for a performance sample.
        room=P.sym('gRoom');w=P.r8(core,room);h=P.r8(core,room+1)
        col=read(core,room+4098,4096)
        best=(0,0,0)
        for y in range(24,h*16-8,4):
            start=None
            for x in range(8,w*16-8,2):
                clear=not any(col[(yy//8)*64+xx//8] for yy in (y-8,y-1) for xx in (x-5,x+4))
                if clear and start is None:start=x
                if not clear and start is not None:
                    if x-start>best[0]:best=(x-start,start,y)
                    start=None
            if start is not None and w*16-8-start>best[0]:best=(w*16-8-start,start,y)
        self.check('walk timing uses a natural open feet strip',best[0]>=48,best)
        _,x,y=best
        C.teleport(core,x+8,y);P.run(core,30)
        records=[];start=P.player_pos(core)
        for i in range(144):
            key='RIGHT' if (i//36)%2==0 else 'LEFT'
            core.set_keys(P.key(core,key));P.run(core,1)
            records.append(dict(frame=i,key=key,gFrame=P.r32(core,P.sym('gFrame')),run_frames=P.r32(core,P.sym('gGame')+8),position=list(P.player_pos(core))))
        core.clear_keys(*range(10));P.run(core,30)
        moved=max(r['position'][0] for r in records)-min(r['position'][0] for r in records)
        self.check('real directional input moves Bloom during timing sample',moved>=12,moved)
        walk_deltas=self.logic_deltas(records)
        if self.args.phase=='after':self.check('144-frame actual walking keeps near-baseline logic cadence',walk_deltas.get('0',0)<=4 and all(int(k)<=1 for k in walk_deltas),walk_deltas)
        self.walk_summary=dict(frames=144,fixture_strip=best,positions_span=moved,logic_delta_histogram=self.logic_deltas(records),records=records)

    def presentation(self):
        if self.scenes:
            sheet=Image.new('RGB',(480,320),(16,16,24))
            for i,path in enumerate(self.scenes[:4]):sheet.paste(Image.open(path),((i%2)*240,(i//2)*160))
            sheet.save(self.out/'contexts-actual-native.png')
        paths=[self.out/name for name in ('03-drain.png','04-lantern-cape-hubcap.png','05-sword-shield-halfheart.png','06-zero-ammunition.png','07-byte-ammunition-extremes.png','08-empty-equipment.png','09-healthy-forest.png','10-deep-forest.png','11-mystery.png','12-drain-return.png') if (self.out/name).exists()]
        bands=Image.new('RGB',(960,len(paths)*100),(16,16,24))
        for i,path in enumerate(paths):bands.paste(Image.open(path).crop((0,0,240,24)).resize((960,96),Image.Resampling.NEAREST),(0,i*100))
        bands.save(self.out/'top-hud-inspection-4x.png')

    def run(self):
        error=None
        try:self.title();self.intro();self.contexts()
        except Exception:
            error=traceback.format_exc();print(error,flush=True)
            self.check('capture completes without exception',False,error)
        self.presentation()
        report=dict(phase=self.args.phase,source_commit=(self.bundle/'source-commit.txt').read_text().strip(),
            rom_sha256=SHA(self.rom.rom),emulator='mGBA0.10.5',native_size=[240,160],
            method='Real simulation and hardware HUD decoding. Native PNGs unchanged; inspection sheets use integer nearest-neighbor crops only.',
            fixtures=self.fixtures,passed=sum(r['passed'] for r in self.rows),total=len(self.rows),checks=self.rows,
            media=self.media,hardware=self.hardware,state_snapshots=self.state_snapshots,
            motion=getattr(self,'motion_summary',None),motion_frames=self.frames,buttons=getattr(self,'button_summary',None),walking_timing=getattr(self,'walk_summary',None),
            button_boxes=self.button_boxes,error=error,complete=error is None,
            tool_sha256=SHA(Path(__file__).read_bytes()))
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('%d/%d; complete=%s'%(report['passed'],report['total'],report['complete']),flush=True)
        return 0 if report['passed']==report['total'] and error is None else 1


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--phase',choices=('before','after'),required=True)
    ap.add_argument('--seed',type=lambda s:int(s,0),default=0xB4A7)
    ap.add_argument('--button-boxes',default='[[151,4,156,11],[181,4,186,11],[211,4,216,11]]')
    args=ap.parse_args()
    return Review(args).run()


if __name__=='__main__':raise SystemExit(main())
