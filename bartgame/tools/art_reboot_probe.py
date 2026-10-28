"""Verify complete native art ownership and its actual GBA presentation.

Packed ROM comparisons distinguish geometric redraws from palette-only edits.
Runtime checks read real OAM/OBJ VRAM after ordinary inputs. A disclosed local
floor fixture isolates direction/anchor checks; it is never gallery evidence.
"""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import struct

from art_reboot_inventory import alpha_bounds
from blight_scope_probe import Rom, digest

ROOT=Path(__file__).resolve().parent.parent
BASE=Path('/workspace/setup/art-reboot-before')
OWNERS={'reboot_terrain','reboot_actors','reboot_items','reboot_ui'}
OLD_ART_IMPORTS={'pack','pack_tiles','tiles_style','tile_art','wood_art','env_pack',
                 'forest_art','forest_sprites','healthy_reference','blight_reference',
                 'blight_reference_source','reference_assets','reference_items','clean_items',
                 'bloom_animations','bloom_fx','bloom_loads','interactive_props','interactive_tiles',
                 'sw_hall','sw_cut','sw_drain','sw_paint','sw_props'}
SHAPES={(8,8),(16,16),(32,32),(64,64),(16,8),(32,8),(32,16),(64,32),
        (8,16),(8,32),(16,32),(32,64)}
OAM_DIMS={0:((8,8),(16,16),(32,32),(64,64)),
          1:((16,8),(32,8),(32,16),(64,32)),
          2:((8,16),(8,32),(16,32),(32,64))}
# Explicit art-direction exceptions: these simple glyphs/rules were freshly
# authored in the native generators, but retain the same irreducible geometry.
# Do not hide them inside a broad "all pixels changed" claim.
SHARED_LETTER_PRIMITIVES=set('cnorsuvxz')
SHARED_UI_PRIMITIVES={'UI_SLOT_L','UI_ROW_L','UI_BUB_JOIN','UI_RULE'}
checks=[]


def check(group,name,ok,detail=None):
    row={'group':group,'name':name,'passed':bool(ok)}
    if detail is not None:row['detail']=detail
    checks.append(row)
    if not ok:print('FAIL',group,name,detail,flush=True)


def inks(data,width,height):
    result=bytearray(width*height)
    for y in range(height):
        for x in range(width):
            at=((y//8)*(width//8)+x//8)*32+(y%8)*4+(x%8)//2
            result[y*width+x]=(data[at]>>(4*(x&1)))&15
    return bytes(result)


def tile_inks(rom,set_,name):
    entries=rom.unpack('<4H',set_['mapping']+rom.metatiles[name]*8)
    if not any(entries):return None
    animation=set_['animations'].get(entries[0]&1023)
    frames=animation[0] if animation else 1
    result=[]
    for frame in range(frames):
        pixels=bytearray(256)
        for q,entry in enumerate(entries):
            data=(rom.read(animation[2]+frame*128+q*32,32) if animation else
                  rom.read(set_['tiles']+(entry&1023)*32,32))
            for y in range(8):
                for x in range(8):
                    tx=7-x if entry&1024 else x;ty=7-y if entry&2048 else y
                    value=(data[ty*4+tx//2]>>(4*(tx&1)))&15
                    pixels[((q//2)*8+y)*16+(q%2)*8+x]=value
        result.append(bytes(pixels))
    return result


def frame(rom,name,index):
    meta,data=rom.sheet(name)
    size=meta[1]*32
    return meta,data[index*size:(index+1)*size]


def primitive(data,width,height):
    # Blank source images and uniform void/fill primitives are mathematical
    # fields rather than figurative art. All owners must still declare them.
    return len(set(inks(data,width,height)))<=1


def static_checks(args,old,new):
    contract=json.loads(Path(args.contracts).read_text())
    coverage=json.loads(Path(args.coverage).read_text())
    details={'unchanged_primitive_frames':[],'unchanged_primitive_tiles':[],
             'changed_tiles':{},'frame_counts':{},'areas':{},'source_modules':[]}
    check('coverage','contract baseline matches frozen ROM',contract['baseline_rom_sha256']==digest(old.data))
    expected={t['name'].upper():t['id'] for t in contract['tiles']}
    check('contracts','all original metatile names and identifiers',old.metatiles==new.metatiles==expected)
    tile_owners={row['name']:row for row in coverage.get('tiles',[])}
    check('coverage','every metatile has exactly one native owner',
          len(tile_owners)==len(coverage.get('tiles',[]))==len(expected) and
          set(tile_owners)=={t['name'] for t in contract['tiles']})
    for tile in contract['tiles']:
        name=tile['name'];index=tile['id'];owner=tile_owners.get(name,{})
        check('coverage','tile '+name,owner.get('owner')=='reboot_terrain' and owner.get('frames')==tile['frames'])
        for field in ('type','coll','prop'):
            check('contracts',name+' '+field,old.read(old.symbols['metatile_'+field]+index,1)==
                  new.read(new.symbols['metatile_'+field]+index,1))
    for area in ('forest','sewer','myst'):
        before,after=old.tileset(area),new.tileset(area);changed=[];retained=[]
        check('hardware',area+' background subtile budget',after['tile_count']<=1024,after['tile_count'])
        check('hardware',area+' material palette budget',after['palette_count']<=12,after['palette_count'])
        for name in expected:
            old_frames=tile_inks(old,before,name);new_frames=tile_inks(new,after,name)
            if old_frames is None and new_frames is None:continue
            if old_frames==new_frames:
                uniform=bool(new_frames) and all(len(set(f))<=1 for f in new_frames)
                check('pixel_redraw',area+' '+name+' indexed drawing changed',uniform,
                      'explicit uniform fill/void exception' if uniform else 'unchanged indexed drawing')
                (details['unchanged_primitive_tiles'] if uniform else retained).append(area+':'+name.lower())
            else:
                check('pixel_redraw',area+' '+name+' indexed drawing changed',True)
                changed.append(name.lower())
        details['changed_tiles'][area]=changed
        details['areas'][area]={'subtiles':after['tile_count'],'palette_banks':after['palette_count'],
                                'animated_metatiles':len(after['animations']),
                                'changed_drawings':len(changed),'unexpected_unchanged':retained}
    expected_frames={(sheet['name'],name) for sheet in contract['sheets'] for name in sheet['frames']}
    owners=coverage.get('sprites',[])
    owned={(r['sheet'],r['frame']):r for r in owners}
    check('coverage','all sprite frame owners are unique',len(owned)==len(owners))
    check('coverage','every original sprite frame has an owner',expected_frames<=set(owned))
    check('coverage','new HUD and glitter families are explicitly owned',
          {name for name,_ in set(owned)-expected_frames}=={'huditems','glitter'})
    for sheet in contract['sheets']:
        name=sheet['name'];meta,data=new.sheet(name);width,height=meta[-2:]
        check('hardware',name+' valid native OBJ shape',(width,height) in SHAPES,[width,height])
        check('hardware',name+' four-bit tile layout',meta[1]==width*height//64)
        details['frame_counts'][name]=len(sheet['frames'])
        for index,fname in enumerate(sheet['frames']):
            key=(name,fname);row=owned.get(key,{})
            check('coverage',name+'.'+fname,row.get('owner') in OWNERS and row.get('canvas')==[width,height])
            macro='F_'+name.upper()+'_'+fname.upper()
            check('contracts',macro,new.defs.get(macro)==old.defs.get(macro)==index)
            before,before_data=frame(old,name,index);_,after_data=frame(new,name,index)
            if before_data==after_data and before[-2:]==meta[-2:]:
                allowed=primitive(after_data,width,height)
                check('pixel_redraw',name+'.'+fname+' native pixels changed',allowed,
                      'explicit transparent/uniform primitive exception' if allowed else 'same packed pixels')
                if allowed:details['unchanged_primitive_frames'].append(name+'.'+fname)
            else:check('pixel_redraw',name+'.'+fname+' native pixels changed',True)
    for name in ('huditems','glitter'):
        meta,_=new.sheet(name);wanted=(16,16) if name=='huditems' else (8,8)
        check('native_scale',name+' exact native canvas',meta[-2:]==wanted,list(meta[-2:]))
        check('coverage',name+' all appended frames owned',
              sum(s==name for s,f in owned)==new.defs['SHEET_'+name.upper()+'_FRAMES'])
    hero,_=new.sheet('hero')
    check('native_scale','Bloom uses a 32x32 canvas and 16 resident tiles',hero[-2:]==(32,32) and hero[1]==16)
    for facing in ('S','N','E'):
        index=new.defs['F_HERO_IDLE_'+facing];meta,data=frame(new,'hero',index)
        box=alpha_bounds(data,*meta[-2:]);size=[box[2]-box[0],box[3]-box[1]] if box else [0,0]
        check('native_scale','Bloom idle '+facing+' is compact',12<=size[0]<=16 and 20<=size[1]<=24,{'bounds':box,'visible_size':size})
    pickup_meta,pickup_data=new.sheet('pick32')
    check('native_scale','world pickups use 16x16 hardware canvas',pickup_meta[-2:]==(16,16))
    for i in range(new.defs['SHEET_PICK32_FRAMES']):
        raw=pickup_data[i*pickup_meta[1]*32:(i+1)*pickup_meta[1]*32]
        box=alpha_bounds(raw,*pickup_meta[-2:]);size=[box[2]-box[0],box[3]-box[1]] if box else [0,0]
        check('native_scale','world pickup '+str(i)+' fits one tile',bool(box) and max(size)<=16 and 4<=min(size),size)
    check('native_scale','inventory illustrations remain separately authored 32px',new.sheet('icon32')[0][-2:]==(32,32))
    exact_exceptions=[]
    for index in range(new.defs['SHEET_ICON32_FRAMES']):
        a=old.read(old.symbols['icon32_exact_tiles']+index*512,512)
        b=new.read(new.symbols['icon32_exact_tiles']+index*512,512)
        same=a==b;allowed=same and primitive(b,32,32)
        check('pixel_redraw','exact menu illustration '+str(index)+' native drawing changed',not same or allowed,
              'explicit transparent none illustration' if allowed else None)
        if allowed:exact_exceptions.append(index)
    details['unchanged_exact_menu_primitives']=exact_exceptions
    check('native_scale','portrait illustrations have six native frames',new.defs['SHEET_FACE_FRAMES']==6)
    glitter=new.named('metatile_glitter',len(expected))
    check('glitter','multiple native materials explicitly support glitter',sum(bool(v) for v in glitter)>=8,sum(bool(v) for v in glitter))
    interfaces={row['family']:row for row in coverage.get('interface',[])}
    required={'ui_kit':new.defs['UI_TILE_COUNT'],'hud':new.defs['HUD_TILE_COUNT'],
              'font':97,'portraits':6}
    for family,count in required.items():
        row=interfaces.get(family,{})
        check('coverage','complete '+family+' native redesign',row.get('owner')=='reboot_ui' and len(row.get('elements',[]))==count,count)
    check('contracts','all 51 UI and four HUD tile contracts retained',new.defs['UI_TILE_COUNT']==51 and new.defs['HUD_TILE_COUNT']==4)
    check('contracts','all 97 native font characters retained',new.defs['VWF_COUNT']==97 and new.defs['VWF_HEIGHT']==9)
    # Shared punctuation primitives are legitimate; report them rather than
    # pretending a dot was redesigned merely because its palette changed.
    glyph_exceptions=[];shared_letters=[];changed_letters=0
    for i in range(97):
        a=old.read(old.symbols['vwf_bits']+i*9,9);b=new.read(new.symbols['vwf_bits']+i*9,9)
        if a==b:
            ch=chr(i+32);shared=ch in SHARED_LETTER_PRIMITIVES;allowed=not ch.isalnum() or shared
            check('font_redraw','glyph '+repr(ch),allowed,
                  'explicit shared five-pixel letter primitive' if shared else 'shared punctuation/space/symbol primitive' if allowed else 'unchanged letter/number')
            if shared:shared_letters.append(ch)
            elif allowed:glyph_exceptions.append(i+32)
        else:changed_letters+=1;check('font_redraw','glyph '+repr(chr(i+32)),True)
    details['font']={'changed_glyphs':changed_letters,'shared_letter_primitives':shared_letters,
                     'shared_punctuation_space_or_symbol':glyph_exceptions}
    details['shared_ui_primitives']=[]
    for name in ('ui_tiles','hud_tiles'):
        count=new.defs['UI_TILE_COUNT' if name=='ui_tiles' else 'HUD_TILE_COUNT']
        before=old.named(name,count*32);after=new.named(name,count*32)
        for index in range(count):
            a,b=before[index*32:(index+1)*32],after[index*32:(index+1)*32]
            names={key for key,value in new.defs.items() if key.startswith('UI_') and value==index}
            shared=name=='ui_tiles' and bool(names&SHARED_UI_PRIMITIVES)
            same=a==b;allowed=same and (primitive(b,8,8) or shared)
            check('pixel_redraw',name+' native drawing '+str(index),not same or allowed,
                  'explicit straight edge/join/rule primitive' if allowed and shared else 'explicit uniform fill/blank exception' if allowed else None)
            if same and shared:details['shared_ui_primitives'].extend(sorted(names&SHARED_UI_PRIMITIVES))
    title=new.named('title_bitmap',240*160*2);colors=set(struct.unpack('<38400H',title))
    check('native_title','title remains 240x160 RGB555',new.defs['TITLE_BITMAP_PIXELS']==38400 and max(colors)<32768)
    check('native_title','title uses at most 48 deliberate native colours',len(colors)<=48,len(colors))
    check('pixel_redraw','title is a new native composition',title!=old.named('title_bitmap',len(title)))
    details['title']={'colors':len(colors),'sha256':digest(title),'metadata':coverage.get('title')}
    for filename in ['tiles.py','sprites.py','palettes.py','title.py','ui_kit.py','ui_font.py','faces.py','rooms.py','sw_folk.py']+[
            path.name for path in sorted((ROOT/'art').glob('reboot_*.py'))]:
        path=ROOT/'art'/filename
        if not path.exists():continue
        tree=ast.parse(path.read_text());imports=set();bad_resize=[];source_image_reads=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:imports.add(node.module.split('.')[0])
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                if node.func.attr=='resize' and any(isinstance(v,ast.Attribute) and v.attr in {'LANCZOS','BILINEAR','BICUBIC'} for v in ast.walk(node)):
                    bad_resize.append(node.lineno)
                if node.func.attr=='open' and isinstance(node.func.value,ast.Name) and node.func.value.id=='Image':source_image_reads.append(node.lineno)
        check('native_pipeline',filename+' has no old painter imports',not(imports&OLD_ART_IMPORTS),sorted(imports&OLD_ART_IMPORTS))
        check('native_pipeline',filename+' has no high-resolution input or filtered resize',not bad_resize and not source_image_reads,{'filtered_resize_lines':bad_resize,'image_read_lines':source_image_reads})
        details['source_modules'].append({'file':filename,'imports':sorted(imports)})
    core=ast.parse((ROOT/'art/reboot_core.py').read_text())
    ramp_count=0
    for node in ast.walk(core):
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and len(node.value)==7 and node.value.startswith('#'):
            try:channels=[int(node.value[k:k+2],16) for k in (1,3,5)]
            except ValueError:continue
            ramp_count+=1;check('native_palette',node.value+' is authored RGB555-aligned',all(v%8==0 for v in channels))
    check('native_palette','shared native palette vocabulary is populated',ramp_count>=16,ramp_count)
    return details


def runtime_checks(args,new):
    # Lazy imports allow pure-ROM inspection without loading mGBA.
    import probe as P
    import critical_path as C
    import bloom_probe as B
    import bloom_suite_probe as S
    P.ROM=str(Path(args.rom).resolve());P.MAP=str(Path(args.map).resolve());P._syms=None
    defs=B.definitions(args.header);c=B.boot(P.ROM)
    B.floor_fixture(c,defs)
    hurt=new.unpack('<bbBB',new.symbols['gHitboxes'])
    feet=new.unpack('<bbBB',new.symbols['gHitboxes']+4)
    check('runtime_geometry','hurt box aligns to compact 12x20 body',hurt==(0,-11,6,10),list(hurt))
    check('runtime_geometry','feet box is the deliberate 10x8 footprint',feet==(0,-4,5,4),list(feet))
    check('runtime_oam','actual Bloom sprite exists with its new shape',B.hero_oam(c) is not None)
    hero=B.sheet_metadata(c,defs['SHEET_HERO'])
    check('runtime_oam','live Bloom descriptor is 32x32 square',hero['shape']==0 and hero['size']==2 and hero['frame_tiles']==16,hero)
    shapes=[]
    for f,d in enumerate(('n','e','s','w')):
        B.reset_player(c,256,230,f,equipment=(0,5,0));P.run(c,6)
        h=B.hero_oam(c);check('runtime_oam',d+' idle body cannot be silently skipped',h is not None)
        pose=P.r8(c,B.static_symbol('sLastFrame'));live=B.bytes_at(c,0x06010000,hero['frame_tiles']*32)
        check('runtime_oam',d+' idle art is actually uploaded',live==new.read(hero['source']+pose*hero['frame_tiles']*32,len(live)))
        c.set_keys(P.key(c,'B'));P.run(c,5)
        h=B.hero_oam(c);shield_tile=B.fixed_tiles(c,defs)['shield'];sh=B.sheet_metadata(c,defs['SHEET_SHIELD'])
        part=next((o for o in B.oam(c) if o['tile']==shield_tile and o['shape']==sh['shape'] and o['size']==sh['size']),None)
        check('runtime_depth',d+' held shield is physically rendered',h is not None and part is not None)
        if h and part:
            check('runtime_depth',d+' shield belongs on the correct side of Bloom',part['index']>h['index'] if f==0 else part['index']<h['index'])
            if f==0:
                visible=S.visible_beyond_hero(c,part,sh['width'],sh['height'])
                check('runtime_depth','north shield has a visible forward rim',visible>=8,visible)
        shapes.append({'direction':d,'body':h,'shield':part})
        c.clear_keys(*range(10))
    # Reuse the already validated real contact/range implementation rather
    # than making a second implementation-shaped sword test.
    B.checks.clear();attack_c=B.boot(P.ROM);B.floor_fixture(attack_c,defs)
    _,traces=B.timing_and_render(attack_c,defs);B.boundaries(attack_c)
    for row in B.checks:check('runtime_sword',row['name'],row['passed'],row.get('detail'))
    arrow_rows=[]
    hands=((5,-17),(7,-12),(3,-9),(-8,-12))
    for f,d in enumerate(('n','e','s','w')):
        B.reset_player(c,256,230,f,equipment=(0,6,0));P.run(c,6)
        before=P.player_pos(c);c.set_keys(P.key(c,'B'));c.run_frame();c.clear_keys(*range(10))
        first=None
        for tick in range(8):
            c.run_frame()
            for i in range(1,96):
                at=P.sym('gActors')+i*64
                if P.r8(c,at)!=3 or P.r8(c,at+1)!=3:continue
                sid=P.r8(c,at+36);source_frame=P.r8(c,at+37);sh=B.sheet_metadata(c,sid)
                tile=(P.r16(c,at+44)&65535)+source_frame*sh['frame_tiles']
                shot=next((o for o in B.oam(c) if o['tile']==tile and o['shape']==sh['shape'] and o['size']==sh['size']),None)
                if shot is None:continue
                nock=(8,12) if f==0 else (8,3) if f==2 else (3,8)
                if shot['flip']:nock=(sh['width']-1-nock[0],nock[1])
                anchor=[shot['x']+nock[0]+P.r16(c,P.sym('gCamX')),
                        shot['y']+nock[1]+P.r16(c,P.sym('gCamY'))]
                want=[before[0]+hands[f][0],before[1]+hands[f][1]]
                first={'direction':d,'tick':tick,'nock_world':anchor,'hand_world':want,'oam':shot}
                check('runtime_grips',d+' first visible arrow nock meets the held bow',anchor==want,first)
                break
            if first:break
        check('runtime_grips',d+' released arrow is actually observed',first is not None)
        arrow_rows.append(first)
    # Inspect naturally spawned pocket hoards and relics. The sheet's ten
    # source frames are checked above; these prove the real spawn/draw path
    # uses that16px descriptor instead of a manually fabricated actor.
    import lift_probe as L
    c=B.boot(P.ROM);world=C.world(c);pickup_rows=[];kinds=set()
    def safe_point(px,py):
        room=P.sym('gRoom');w=P.r8(c,room);h=P.r8(c,room+1)
        if not (8<=px<w*16-8 and 12<=py<h*16):return False
        for yy in (py-8,py-4,py-1):
            for xx in (px-5,px,px+4):
                if P.r8(c,room+4098+(yy//8)*64+xx//8):return False
        mt=P.r16(c,room+2+(((py-4)//16)*32+px//16)*2)&65535
        return P.r8(c,P.sym('metatile_type')+mt) in (0,15)
    for cell,desc in enumerate(world['cells']):
        side=next(i for i,g in enumerate(desc['gate']) if g)
        L.warp(c,cell,side);C.clear_enemies(c);C.heal(c)
        for i in range(1,96):
            at=P.sym('gActors')+i*64
            if P.r8(c,at)!=4:continue
            kind=P.r8(c,at+1)
            if kind in kinds:continue
            px,py=P.r32(c,at+8)>>16,P.r32(c,at+12)>>16
            point=next(((px+dx,py+dy) for dx,dy in ((0,32),(0,48),(32,16),(-32,16),(48,0),(-48,0)) if safe_point(px+dx,py+dy)),None)
            if point is None:continue
            C.teleport(c,*point);P.run(c,96)
            if P.r8(c,at)!=4:continue
            sid=P.r8(c,at+36);source_frame=P.r8(c,at+37);sh=B.sheet_metadata(c,sid)
            tile=(P.r16(c,at+44)&65535)+source_frame*sh['frame_tiles']
            matches=[o for o in B.oam(c) if o['tile']==tile and o['shape']==sh['shape'] and o['size']==sh['size']]
            check('runtime_scale','natural pickup '+str(kind)+' uses PICK32',sid==defs['SHEET_PICK32'])
            check('runtime_scale','natural pickup '+str(kind)+' has a real16px hardware sprite',
                  sh['width']==sh['height']==16 and sh['shape']==0 and sh['size']==1 and bool(matches),matches)
            check('runtime_scale','natural pickup '+str(kind)+' actor canvas follows the sheet',P.r8(c,at+42)==P.r8(c,at+43)==16)
            kinds.add(kind);pickup_rows.append({'cell':cell,'kind':kind,'position':[px,py],'camera_fixture_player':point,'oam':matches})
        if len(kinds)>=2:break
    check('runtime_scale','multiple naturally generated pickup types are actually inspected',len(kinds)>=2,sorted(kinds))
    # Use a quiet, naturally rendered play frame for HUD-boundary inspection.
    c=B.boot(P.ROM);C.dismiss(c);P.run(c,12);entries=B.oam(c)
    # HUD objects must not spill into the first gameplay row below y24.
    hud=[];overflow=[]
    for o in entries:
        if o['tile']<876 or o['y']>=24 or o['shape'] not in OAM_DIMS:continue
        width,height=OAM_DIMS[o['shape']][o['size']]
        raw=B.bytes_at(c,0x06010000+o['tile']*32,width*height//2)
        pixels=B.pixels(raw,width,height)
        screen=[(o['x']+px,o['y']+py) for px,py in pixels if 0<=o['x']+px<240 and 0<=o['y']+py<160]
        if screen:
            hud.append({'oam':o,'bottom':max(y for x,y in screen)})
            overflow.extend((x,y) for x,y in screen if y>=24)
    check('runtime_hud','HUD icons and minimap were actually rendered',len(hud)>=2,hud)
    check('runtime_hud','native HUD alpha fits above y24 without rescaling',not overflow,{'overflow_pixels':len(overflow)})
    bg0=0x06000000+23*2048
    below=[(x,y) for y in range(3,20) for x in range(30) if P.r16(c,bg0+(y*32+x)*2)&65535]
    check('runtime_hud','no old 32px HUD row remains below the 24px band',not below,below[:12])
    next_tile=P.r16(c,B.static_symbol('sNextTile'))&65535
    check('runtime_budget','actual allocations stay below fixed HUD tiles',next_tile<=876,next_tile)
    glitter_trace=[]
    B.clear_actors(c)
    for _ in range(90):
        c.run_frame()
        glitter_trace.append({'sites':P.r16(c,P.sym('gAmbientSiteCount'))&65535,
                              'potential':P.r8(c,P.sym('gAmbientPotential')),
                              'visible':P.r8(c,P.sym('gAmbientVisible')),
                              'oam_count':P.r8(c,P.sym('gOamCount'))})
    check('runtime_glitter','real terrain supplies authored ambient sites',any(t['sites'] for t in glitter_trace))
    check('runtime_glitter','viewport sparkle population respects its explicit cap',all(t['potential']<=24 and t['visible']<=24 for t in glitter_trace))
    check('runtime_glitter','sparkle animation is actually visible',any(t['visible'] for t in glitter_trace))
    check('runtime_glitter','sparkles do not consume logical actor slots',all(P.r8(c,P.sym('gActors')+i*64)==0 for i in range(1,96)))
    check('runtime_glitter','actual OAM stays inside the hardware limit',all(t['oam_count']<=128 for t in glitter_trace))
    return {'directions':shapes,'attack_traces':traces,'first_arrow_grips':arrow_rows,'natural_pickups':pickup_rows,'hud_entries':hud,'obj_next_tile':next_tile,
            'ambient_glitter':glitter_trace,
            'fixture_note':'Direction/range/pickup checks use an isolated disclosed physical-floor/actor fixture. No such images are published as generated gameplay.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom',default=str(ROOT/'bartgame.gba'));ap.add_argument('--map',default=str(ROOT/'build/bartgame.map'))
    ap.add_argument('--header',default=str(ROOT/'build/gen/assets.h'))
    ap.add_argument('--baseline',type=Path,default=BASE)
    ap.add_argument('--coverage',default=str(ROOT/'build/gen/art-reboot-coverage.json'))
    ap.add_argument('--contracts',default=str(ROOT/'art/reboot_contracts.json'))
    ap.add_argument('--static-only',action='store_true');ap.add_argument('--out',default='/workspace/setup/art-reboot-probe.json')
    args=ap.parse_args();old=Rom(args.baseline/'bartgame.gba',args.baseline/'bartgame.map',args.baseline/'assets.h')
    new=Rom(args.rom,args.map,args.header)
    static=static_checks(args,old,new);runtime=None
    if not args.static_only:runtime=runtime_checks(args,new)
    failures=[row for row in checks if not row['passed']]
    report={'rom_sha256':digest(new.data),'before_rom_sha256':digest(old.data),'emulator':None if args.static_only else 'mGBA 0.10.5',
            'method':__doc__.strip(),'passed':len(checks)-len(failures),'total':len(checks),
            'checks':checks,'failures':failures,'static':static,'runtime':runtime}
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT %s %d/%d native-art coverage and presentation checks'%('FAIL' if failures else 'PASS',report['passed'],report['total']))
    return int(bool(failures))


if __name__=='__main__':raise SystemExit(main())
