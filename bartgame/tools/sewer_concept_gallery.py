"""Build native asset-selection atlases and source room assemblies for the Drain.

All art begins as indexed GBA-size drawings. Enlargements use integer nearest
neighbour scaling. These source assemblies are not emulator screenshots; real
mGBA recordings are published separately by sewer_concept_review.py.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'art'))
import reboot_actors as A
import reboot_core as R
import sewer_concepts as S

BG = '#10171e'
PANEL = '#17212a'
FG = '#eee7c8'
MUTED = '#9caeb1'
GOLD = '#e8c878'
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT = ImageFont.truetype(FONT_PATH, 12)
SMALL = ImageFont.truetype(FONT_PATH, 10)
TITLE = ImageFont.truetype(FONT_PATH, 17)
CONTRACTS = json.loads((ROOT / 'art/reboot_contracts.json').read_text())
TILES = {c['name']: c for c in CONTRACTS['tiles']}
ROOM = CONTRACTS['rooms'][0]
STYLE_SHORT = {1: 'Crown of Sludge', 2: 'Crooked Brassworks',
               3: 'Moonlit Cistern', 4: 'Rotten Reliquary', 5: 'Royal Drains'}
CRITIQUES = {
    1: 'Broad masonry and weighty royal metalwork. Best for a monumental, filthy palace sewer.',
    2: 'Rounder, more crooked forms and playful fittings. Best for a cartoony market and broad frog expressions.',
    3: 'Cooler stone and quieter silhouettes, with warm fittings against dark liquid. Best for a damp night-time cistern.',
    4: 'Broken, encrusted surfaces and more accumulated grime. Best for decay; inspect floor clutter against small characters.',
    5: 'Clearer architectural edges and controlled ornament. Best for readable paths, fixtures and strong gold accents.',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def legal_palette(palette):
    assert len(palette) == 16
    for value in palette:
        assert len(value) == 7 and value.startswith('#'), value
        assert all(int(value[j:j+2], 16) % 8 == 0 for j in (1, 3, 5)), value


def check_image(image, size):
    assert image.mode == 'P' and image.size == size, (image.mode, image.size, size)
    assert set(image.tobytes()) <= set(range(16))


def rgba(image, palette):
    legal_palette(palette)
    return R.rgba(image, palette)


def paste(dst, image, xy, palette, scale=1):
    colored = rgba(image, palette)
    if scale != 1:
        colored = colored.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
    dst.alpha_composite(colored, xy)


def panel(size):
    return Image.new('RGBA', size, BG)


def save(image, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert('RGB').save(path, optimize=True)


def label(draw, xy, text, font=FONT, color=FG):
    draw.text(xy, text, font=font, fill=color)


class Gallery:
    def __init__(self, args):
        import sewer_concepts_terrain as terrain
        import sewer_concepts_npcs as npcs
        self.T, self.N = terrain, npcs
        self.out = Path(args.out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.inventory_path = Path(args.inventory)
        self.inventory = json.loads(self.inventory_path.read_text())
        self.styles = range(1, 6)
        self.records = []
        self.pages = []
        self.animation_pages = []
        self.fixture_pages = []
        self.npc_pages = []
        self.rooms = {}
        self.checks = []
        self.used = self.inventory['active_tiles']
        self.unused = self.inventory['retained_unused_named_sw_tiles']
        self.geometry = defaultdict(dict)
        for style in self.styles:
            for palette in (self.T.palette(style), self.N.peddler_palette(style), self.N.wizard_palette(style)):
                legal_palette(palette)

    def tile(self, name, frame, style):
        image = self.T.paint(name, phase=frame, recipe=S.recipe(style))
        check_image(image, (16, 16))
        return image

    def header(self, image, title, subtitle, left=200, width=174):
        d = ImageDraw.Draw(image)
        label(d, (12, 8), title, TITLE, GOLD)
        label(d, (12, 32), subtitle, SMALL, MUTED)
        for style in self.styles:
            x = left + (style - 1) * width
            label(d, (x + 3, 53), f'{style}. {STYLE_SHORT[style]}', SMALL, GOLD)
        return d

    def asset_records(self):
        for entry, status in [(t, 'active') for t in self.used] + [(t, 'unused catalogue') for t in self.unused]:
            n = entry['name']
            record = {'name': n, 'global_id': entry['id'], 'status': status,
                      'category': self.T.category(n), 'frames': entry['frames'],
                      'frame_hold_updates': entry['anim_speed'],
                      'type': entry['type'], 'coll': entry['coll'],
                      'styles': {}}
            for style in self.styles:
                images = [self.tile(n, f, style) for f in range(entry['frames'])]
                hashes = [digest(im.tobytes()) for im in images]
                self.geometry[n][style] = hashes
                record['styles'][str(style)] = {'indexed_frame_sha256': hashes,
                    'palette': self.T.palette(style), 'native_canvas': [16,16]}
            self.records.append(record)

    def tile_pages(self, entries, directory, title):
        groups = defaultdict(list)
        for entry in entries:
            groups[str(self.T.category(entry['name']))].append(entry)
        files = []
        for category, members in sorted(groups.items()):
            for start in range(0, len(members), 18):
                rows = members[start:start+18]
                slug = ''.join(c if c.isalnum() else '-' for c in category).strip('-')
                path = Path(directory) / f'{slug}-{start//18+1:02}.png'
                board = panel((1090, 78 + len(rows) * 66))
                d = self.header(board, title + ' / ' + category,
                    'Source pixels; five alternatives per ID. 16×16 tiles enlarged 3×. Animated IDs have full-frame filmstrips.')
                for row, entry in enumerate(rows):
                    y = 78 + row * 66
                    d.rectangle((8,y,1081,y+63),fill=PANEL if row%2==0 else BG)
                    label(d,(12,y+5),f"{entry['name']}  /  #{entry['id']}",FONT)
                    label(d,(12,y+26),f"{entry['type']}  coll {entry['coll']:x}  {entry['frames']}f",SMALL,MUTED)
                    for style in self.styles:
                        paste(board,self.tile(entry['name'],0,style),(247+(style-1)*174,y+7),self.T.palette(style),3)
                    rec = next(r for r in self.records if r['name']==entry['name'])
                    rec['atlas'] = str(path)
                    rec['atlas_row'] = row + 1
                save(board,self.out/path)
                files.append({'category':category,'file':str(path),'names':[e['name'] for e in rows]})
        return files

    def animations(self, entries, directory):
        files=[]
        for entry in entries:
            if entry['frames'] <= 1:
                continue
            count=entry['frames']
            board=panel((210+count*38, 70+5*58))
            d=ImageDraw.Draw(board)
            label(d,(12,8),entry['name']+' / every authored animation frame',TITLE,GOLD)
            label(d,(12,34),f'{count} frames · native16×16 →2× · frame hold {entry["anim_speed"]} updates · source artwork',SMALL,MUTED)
            for frame in range(count):
                label(d,(212+frame*38,54),str(frame),SMALL,MUTED)
            for style in self.styles:
                y=73+(style-1)*58
                label(d,(10,y+9),f'{style}. {STYLE_SHORT[style]}',SMALL,GOLD)
                for frame in range(count):
                    paste(board,self.tile(entry['name'],frame,style),(210+frame*38,y),self.T.palette(style),2)
            path=Path(directory)/(entry['name']+'.png')
            save(board,self.out/path)
            next(r for r in self.records if r['name']==entry['name'])['animation_filmstrip']=str(path)
            files.append({'name':entry['name'],'file':str(path),'frames':count})
        return files

    def world_actor(self, style, who, frame=None, face='open'):
        if who=='peddler':
            body=self.N.peddler_body(style,frame or 'rest')
            head=self.N.peddler_head(style,face)
            check_image(body,(32,32));check_image(head,(16,16))
            image=Image.new('P',(32,32),0)
            # Exact runtime order: head at foot−26, body at foot−32.
            A.stamp(image,head,(8,6));A.stamp(image,body,(0,0))
            return image,self.N.peddler_palette(style)
        image=Image.new('P',(32,32),0)
        A.stamp(image,self.N.flame(style,'w0'),(23,1))
        A.stamp(image,self.N.wizard(style,frame or 'idle'),(0,0))
        check_image(image,(32,32))
        return image,self.N.wizard_palette(style)

    def source_room(self, recipe, tick=0):
        image=panel((480,320));palette=self.T.palette(recipe['style'])
        for y,row in enumerate(ROOM['ground']):
            for x,name in enumerate(row):
                if name is not None:
                    c=TILES[name];phase=(tick//c['anim_speed'])%c['frames']
                    tile=self.T.paint(name,phase=phase,recipe=recipe)
                    paste(image,tile,(x*16,y*16),palette)
        ped,pedpal=self.world_actor(recipe['peddler'],'peddler')
        wiz,wizpal=self.world_actor(recipe['wizard'],'wizard')
        paste(image,ped,(56,62),pedpal)
        paste(image,wiz,(328,62),wizpal)
        # Bloom is the unchanged approved body, provided only as a scale reference.
        hero=A.hero_frame('idle_s')
        paste(image,hero,(184,238),R.PALETTES['hero'])
        for y,row in enumerate(ROOM['overlay']):
            for x,name in enumerate(row):
                if name is not None:
                    c=TILES[name];phase=(tick//c['anim_speed'])%c['frames']
                    paste(image,self.T.paint(name,phase=phase,recipe=recipe),(x*16,y*16),palette)
        # One foreground study sprite closes the handrail between the
        # retained posts. Its visual line leaves the physical grid intact.
        rail=self.T.rail_sprite(recipe['metal'])
        check_image(rail,(16,8))
        for x in list(range(16,224,16))+list(range(256,464,16)):
            paste(image,rail,(x,136),R.PALETTES['gold'])
        return image

    def room_maps(self):
        for number in range(1,9):
            recipe=S.recipe(number)
            image=self.source_room(recipe)
            native=f'rooms/room-{number}-native.png';enlarged=f'rooms/room-{number}-2x.png'
            save(image,self.out/native)
            save(image.resize((960,640),Image.Resampling.NEAREST),self.out/enlarged)
            self.rooms[number]={'recipe':recipe,'native':native,'enlarged':enlarged,'image':image}
        board=panel((990,3*354+40));d=ImageDraw.Draw(board)
        label(d,(12,8),'FIVE NATIVE DRAIN DIRECTIONS / source room assemblies',TITLE,GOLD)
        for i in range(5):
            x=10+(i%2)*490;y=42+(i//2)*354
            label(d,(x,y),f'{i+1}. {STYLE_SHORT[i+1]}',FONT,GOLD)
            board.alpha_composite(self.rooms[i+1]['image'],(x,y+24))
        save(board,self.out/'room-overview.png')
        mixes=panel((990,2*354+42));d=ImageDraw.Draw(mixes)
        label(d,(12,8),'MIXED COMPONENT RECIPES / same physical room',TITLE,GOLD)
        for i,number in enumerate(range(6,9)):
            x=10+(i%2)*490;y=42+(i//2)*354
            label(d,(x,y),f'{number}. {self.rooms[number]["recipe"]["name"]}',SMALL,GOLD)
            mixes.alpha_composite(self.rooms[number]['image'],(x,y+24))
        save(mixes,self.out/'mixed-overview.png')

    def npc_atlases(self):
        definitions=[('peddler_head',(16,16),self.N.peddler_head,self.N.peddler_palette),
                     ('peddler_body',(32,32),self.N.peddler_body,self.N.peddler_palette),
                     ('gatekeeper',(32,32),self.N.wizard,self.N.wizard_palette),
                     ('wisp',(8,8),self.N.flame,self.N.wizard_palette)]
        for sheet,size,painter,paletter in definitions:
            frames=next(c['frames'] for c in CONTRACTS['sheets'] if c['name']==sheet)
            scale=3 if size[0]<=16 else 2
            height=max(64,size[1]*scale+12)
            board=panel((1090,78+len(frames)*height));d=self.header(board,sheet+' / all frame IDs',
                  'Five native alternatives for each retained frame. Palette0 is transparent; enlarged with nearest neighbour.')
            for row,frame in enumerate(frames):
                y=78+row*height
                d.rectangle((8,y,1081,y+height-3),fill=PANEL if row%2==0 else BG)
                label(d,(12,y+12),frame,FONT)
                record={'sheet':sheet,'frame':frame,'native_canvas':list(size),'styles':{}}
                for style in self.styles:
                    im=painter(style,frame);check_image(im,size)
                    paste(board,im,(240+(style-1)*174,y+6),paletter(style),scale)
                    record['styles'][str(style)]={'indexed_sha256':digest(im.tobytes())}
                self.records.append(record)
            path='sprites/'+sheet+'.png';save(board,self.out/path)
            self.npc_pages.append({'sheet':sheet,'file':path,'frames':frames})
        board=panel((1090,78+2*110));d=self.header(board,'Dialogue portraits / separately drawn at48×48',
                  'These are the same frog and wizard identities as the world sprites. Portraits are not enlarged world pixels.')
        for row,who in enumerate(('peddler','gatekeeper')):
            y=78+row*110
            label(d,(12,y+20),'Frog Peddler' if who=='peddler' else 'Purple wizard',FONT)
            record={'sheet':'face','frame':who,'native_canvas':[48,48],'styles':{}}
            for style in self.styles:
                im=self.N.portrait(style,who);check_image(im,(48,48))
                pal=self.N.peddler_palette(style) if who=='peddler' else self.N.wizard_palette(style)
                paste(board,im,(225+(style-1)*174,y+4),pal,2)
                record['styles'][str(style)]={'indexed_sha256':digest(im.tobytes())}
            self.records.append(record)
        save(board,self.out/'sprites/portraits.png');self.npc_pages.append({'sheet':'portraits','file':'sprites/portraits.png','frames':['peddler','gatekeeper']})
        # Whole connected actors matter more than isolated head and torso pieces.
        board=panel((1090,78+2*142));d=self.header(board,'Five frog Peddlers and five hooded wizards',
                  'Native32×32 composites, enlarged3×. Frame names, anchors and runtime layer order are preserved.')
        for row,who in enumerate(('peddler','wizard')):
            y=84+row*142
            label(d,(12,y+25),'Billious Peddler' if who=='peddler' else 'Flame-staff wizard',FONT)
            for style in self.styles:
                im,pal=self.world_actor(style,who)
                paste(board,im,(224+(style-1)*174,y),pal,3)
        save(board,self.out/'characters.png')
        board=panel((1090,78+70));d=self.header(board,'Continuous foreground handrail / new concept sprite',
                  'Native16×8 strip, enlarged4×. Shared gold OBJ inks; joins the retained posts without changing collision.')
        label(d,(12,94),'sewerrail / rail',FONT)
        record={'sheet':'sewerrail','frame':'rail','native_canvas':[16,8],
                'new_concept_only_sprite':True,'styles':{}}
        for style in self.styles:
            im=self.T.rail_sprite(style);check_image(im,(16,8))
            paste(board,im,(234+(style-1)*174,91),R.PALETTES['gold'],4)
            record['styles'][str(style)]={'indexed_sha256':digest(im.tobytes())}
        self.records.append(record)
        save(board,self.out/'sprites/sewerrail.png')
        self.npc_pages.append({'sheet':'sewerrail (new foreground handrail)','file':'sprites/sewerrail.png','frames':['rail']})

    def fixtures(self):
        definitions=[
          ('floor','Slimy gray bricks, puddles and floor grime',(64,208,192,256)),
          ('wall','Gray retaining masonry and gold wall pipe',(0,0,128,64)),
          ('ladder','Forest ladder and unmistakable dark aperture',(128,8,176,80)),
          ('cistern','Gold wall outfall, bars, flowing fall and basin',(176,0,304,112)),
          ('market','Market, displayed wares and absentminded frog',(8,48,136,120)),
          ('wizard','Hooded purple wizard, staff flame and rug',(280,40,392,120)),
          ('bridge','Bridge linking banks across the sewage stream',(208,128,272,224)),
          ('rail','Rail separating the player from flowing sewage',(112,120,224,208)),
          ('outfall','Small gold outfall pouring into moving water',(416,104,464,184)),
          ('storage','Crates, barrel and ground filth',(392,56,464,112)),
          ('grate','Walkable floor drain with a clear barred surface',(192,216,288,264)),
          ('bottom-bank','Lower rail, dirty coping, moss and moving water',(64,248,192,320)),
        ]
        for slug,title,box in definitions:
            w,h=box[2]-box[0],box[3]-box[1]
            col=max(w*2+12,174)
            board=panel((12+col*5,82+h*2));d=ImageDraw.Draw(board)
            label(d,(12,8),title,TITLE,GOLD)
            label(d,(12,32),'Five alternatives / source room fixture crops / native art enlarged2×',SMALL,MUTED)
            for style in self.styles:
                x=6+(style-1)*col
                label(d,(x+4,53),f'{style}. {STYLE_SHORT[style]}',SMALL,GOLD)
                crop=self.rooms[style]['image'].crop(box).resize((w*2,h*2),Image.Resampling.NEAREST)
                board.alpha_composite(crop,(x+4,78))
            path='fixtures/'+slug+'.png';save(board,self.out/path)
            self.fixture_pages.append({'id':slug,'label':title,'source_crop':list(box),'file':path})

    def finalize(self):
        assert len(self.used)==370 and len(self.unused)==80
        tile_records=[r for r in self.records if 'global_id' in r]
        active_frames=sum(r['frames']*5 for r in tile_records if r['status']=='active')
        unused_frames=sum(r['frames']*5 for r in tile_records if r['status']!='active')
        assert active_frames==623*5 and unused_frames==113*5
        for style in self.styles:
            all_bytes=b''.join(self.tile(t['name'],0,style).tobytes() for t in self.used)
            self.checks.append({'style':style,'active_terrain_indexed_sha256':digest(all_bytes)})
        assert len({r['active_terrain_indexed_sha256'] for r in self.checks})==5,'Styles must change geometry, not only palettes'
        for who in ('peddler','wizard'):
            hashes={digest(self.world_actor(style,who)[0].tobytes()) for style in self.styles}
            assert len(hashes)==5,(who,'five structural alternatives required')
        sharing=Counter(len({tuple(v['indexed_frame_sha256']) for v in r['styles'].values()})
                        for r in tile_records if r['status']=='active')
        identical=[r['name'] for r in tile_records if r['status']=='active' and
                   len({tuple(v['indexed_frame_sha256']) for v in r['styles'].values()})==1]
        painter_hashes={str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in
            (ROOT/'art/sewer_concepts.py', ROOT/'art/sewer_concepts_terrain.py',
             ROOT/'art/sewer_concepts_npcs.py', ROOT/'art/reboot_contracts.json')}
        catalog={'method':__doc__.strip(),'native_screen':[240,160],'native_room':[480,320],
          'painter_source_sha256':painter_hashes,
          'source_assembly_not_emulator':True,'styles':S.STYLE_NAMES,'records':self.records,
          'tile_atlases':self.pages,'animated_tile_filmstrips':self.animation_pages,
          'npc_atlases':self.npc_pages,'fixtures':self.fixture_pages,
          'rooms':[{k:v for k,v in row.items() if k!='image'} for row in self.rooms.values()],
          'coverage':{'active_tile_ids':370,'active_frame_alternatives':active_frames,'unused_catalogue_ids':80,
                      'unused_frame_alternatives':unused_frames,'world_npc_frame_alternatives':29*5,
                      'portrait_alternatives':2*5,'new_foreground_rail_alternatives':5,
                      'unchanged_bloom':True,'ambient_glitter_in_source_assemblies':False},
          'indexed_geometry_sharing':{'number_of_distinct_sequences_to_active_id_count':dict(sorted(sharing.items())),
              'identical_indexed_sequences_in_all_five':identical,
              'meaning':'Small blank or seam pieces can retain indexed geometry across concepts; palette color may still differ. No random pixel edits were added to force five unique hashes.'},
          'geometry_checks':self.checks}
        (self.out/'catalogue.json').write_text(json.dumps(catalog,indent=2)+'\n')
        shutil.copy2(self.inventory_path,self.out/'inventory.json')
        source_inventory_md=self.inventory_path.with_name('README.md')
        if source_inventory_md.exists():shutil.copy2(source_inventory_md,self.out/'INVENTORY.md')
        self.readme(catalog)
        files={str(p.relative_to(self.out)):digest(p.read_bytes()) for p in sorted(self.out.rglob('*')) if p.is_file() and p.name!='source-manifest.json'}
        (self.out/'source-manifest.json').write_text(json.dumps({'method':'All source image pixels authored at native resolution; source assemblies are not emulator captures.','files':files},indent=2)+'\n')
        print(json.dumps({'output':str(self.out),'files':len(files),'active_frame_alternatives':active_frames,
                          'unused_frame_alternatives':unused_frames,'rooms':8,'fixture_comparisons':len(self.fixture_pages)},indent=2))

    def readme(self,catalog):
        text='''# Drain art concepts for selection

Five complete native-GBA art directions and three mixed-component rooms use
the same Drain layout. All five use gray slimy masonry, dirty ground, flowing
sewage, bright gold fittings, a clear forest ladder, railings and a bridge.
The Billious Peddler is a cartoon frog; the old wizard wears a purple hood and
carries a flame-tipped staff. Bloom, the shared UI and the existing ambient
glitter are preserved.

**The images on this page are source asset comparisons and room assemblies,
not mGBA screenshots.** Every drawing starts at its final GBA pixel size and
uses legal4bpp inks and RGB555 colors; zooms use integer nearest-neighbour.
The whole room is480×320 world pixels, larger than the240×160 GBA viewport.
Source room maps show the full layout for comparison and omit the runtime
ambient glitter emitter. Actual game recordings should be judged separately.

[Complete current asset inventory](INVENTORY.md) · [Machine-readable inventory](inventory.json) ·
[Every alternative and frame hash](catalogue.json)

## Five complete directions

![Five whole-room source assemblies](room-overview.png)

| Option | Direction | Art tradeoff | Full room |
| --- | --- | --- | --- |
'''
        for style in self.styles:
            text+=f'| **{style}** | **{STYLE_SHORT[style]}** | {CRITIQUES[style]} | [Native480×320](rooms/room-{style}-native.png) · [2×zoom](rooms/room-{style}-2x.png) |\n'
        text+='''
## Choose parts independently

You can ask for a complete option, or mix choices such as **floor3 + brass1 +
market2 + frog5 + wizard3**. The following comparisons keep the same crop and
placement in each of the five columns. Large fixtures span several16px tiles;
they are shown assembled before the exhaustive individual tile catalogue.

![Five frog and wizard concepts](characters.png)

'''
        for fixture in self.fixture_pages:
            text+=f"- [{fixture['label']}]({fixture['file']})\n"
        text+='''
## Mixed rooms

These demonstrate component combinations without moving walls, the bridge,
the ladder, the counter or the NPC anchors. Palette roles are consistent, so
metal, water, floors and props can mix while sharing one legal Drain bank.

![Three mixed-component source rooms](mixed-overview.png)

| Mix | Palette base | Floor | Masonry | Water | Goldwork | Bridge | Market | Frog | Wizard | Full room |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
'''
        for number in range(6,9):
            r=S.recipe(number)
            text+=f"| {number}. {r['name']} | {r['style']} | {r['floor']} | {r['masonry']} | {r['water']} | {r['metal']} | {r['bridge']} | {r['market']} | {r['peddler']} | {r['wizard']} | [Native](rooms/room-{number}-native.png) · [2×](rooms/room-{number}-2x.png) |\n"
        text+='''
## Every NPC sprite frame and portrait

The head/body split keeps the frog's existing breathing, blinking, looking,
coin and hand animations. The wizard's existing frame IDs remain stable; its
separate four-frame flame now belongs at the staff tip. Portraits are authored
independently at48×48 and match their world identities.

A new16×8foreground sprite supplies a continuous handrail between the retained
north-bank posts. It has five geometry choices, uses the common gold OBJ bank
and leaves the room's physical grid and glitter metadata untouched.

'''
        for row in self.npc_pages:
            text+=f"- [{row['sheet']}: all {len(row['frames'])} frame choices]({row['file']})\n"
        text+='''
## Every active Drain metatile

All370 used metatile identifiers have five alternatives below. These include
350ground IDs and20foreground IDs, across600ground and57foreground placements.
Their38animated IDs retain their frame counts and timing contracts, for623
distinct authored tile frames per option. Atlas rows show phase0; every other
animation frame appears in the filmstrip appendix. IDs, collisions, dimensions,
interactions and room placement remain unchanged.

'''
        for row in self.pages:
            text+=f"- [{row['category']} / {row['names'][0]}–{row['names'][-1]}]({row['file']})\n"
        sharing=catalog['indexed_geometry_sharing']
        count=len(sharing['identical_indexed_sequences_in_all_five'])
        text+=f'''\n{count} small active pieces retain the same indexed geometry in all five
options; some are blank or common seam fragments, with material colors supplied
by each option's palette. Other pieces can share geometry between a subset of
the options. The catalogue records the exact frame hashes and sharing counts.
Pixel differences were not added merely to manufacture five unique hashes.\n'''
        text+='\n## Every active animated tile frame\n\n'
        for row in self.animation_pages:
            if row['name'].startswith('swh_'):
                text+=f"- [{row['name']}: all {row['frames']} frames ×five options]({row['file']})\n"
        text+='''
## Retained unused sewer catalogue

These80 `sw_` identifiers are retained vocabulary, not room placements or
additional objects in the current Drain. They also receive five alternatives
for reference; their113frame drawings are listed separately to avoid implying
that these tiles appear in the current room.

'''
        for row in self.unused_pages:
            text+=f"- [{row['category']} / {row['names'][0]}–{row['names'][-1]}]({row['file']})\n"
        text+='\nUnused-catalogue animation filmstrips:\n\n'
        for row in self.animation_pages:
            if not row['name'].startswith('swh_'):
                text+=f"- [{row['name']}: all {row['frames']} frames ×five options]({row['file']})\n"
        text+='''
## Scope and critique limits

These are choices for feedback. A complete option has not been selected for
the released game. Shared HUD, shop chrome, font, inventory, conditional item
effects, Bloom and runtime glitter are catalogued as preserved common assets;
they do not receive five Drain-only redesigns that would make them inconsistent
with the forest. There are no authored Drain enemy, chest or switch spawns.

Each complete direction changes indexed geometry as well as palette; the two
new NPCs also have five distinct composite geometries. A full native room map
is useful for composition, but cannot replace motion and occlusion review in
the real240×160 viewport. Inspect flowing water, the staff flame, NPC poses,
the bridge landings and rail separation in the actual recordings before choosing.
'''
        fixes={'legal4bpp':'legal 4bpp','is480':'is 480','the240':'the 240','Native480':'Native 480',
               '2×zoom':'2× zoom','floor3':'floor 3','brass1':'brass 1','market2':'market 2','frog5':'frog 5',
               'wizard3':'wizard 3','several16px':'several 16px','at48':'at 48','All370':'All 370',
               '350ground':'350 ground','and20foreground':'and 20 foreground','across600ground':'across 600 ground',
               'and57foreground':'and 57 foreground','Their38animated':'Their 38 animated','for623':'for 623',
               'phase0':'phase 0','×five':'× five','These80':'These 80','their113frame':'their 113 frame',
               'real240':'real 240','new16×8foreground':'new 16×8 foreground'}
        for old,new in fixes.items():text=text.replace(old,new)
        (self.out/'README.md').write_text(text)

    def run(self):
        self.asset_records()
        self.pages=self.tile_pages(self.used,'tiles','Active Drain metatiles')
        self.unused_pages=self.tile_pages(self.unused,'unused-tiles','Unused retained sewer vocabulary')
        self.animation_pages=self.animations(self.used,'animation-frames')+self.animations(self.unused,'unused-animation-frames')
        self.room_maps();self.npc_atlases();self.fixtures();self.finalize()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True)
    ap.add_argument('--inventory',default='/workspace/setup/sewer-concepts/inventory/inventory.json')
    Gallery(ap.parse_args()).run()


if __name__=='__main__':
    main()
