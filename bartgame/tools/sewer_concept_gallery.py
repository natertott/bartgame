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

from PIL import Image, ImageDraw, ImageFont, ImageOps

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
STYLE_SHORT = S.STYLE_NAMES
CRITIQUES = {
    1: 'Heavy gray ashlar, amber fittings and worn wood. Inspect the floor joints, falling sheet and ladder arrow at native size.',
    2: 'Crooked brick and patched market construction. Check that wear changes the form without obscuring its purpose.',
    3: 'Floodworn flags and quieter wet planes. Check current direction, water impact and separation from the banks.',
    4: 'Crumbling vault masonry and dilapidated timber. Compare deliberate damage against the still-readable travel plane.',
    5: 'Silted cloister stone and restrained gilt. Check the sacred corner against attached grime and exposed plumbing.',
}
FIXTURES = (
    ('floor','Slimy gray bricks, puddles and floor grime',(64,208,192,256)),
    ('wall','Gray retaining masonry and gold wall pipe',(0,0,128,64)),
    ('ladder','Forest ladder and unmistakable dark aperture',(128,8,176,80)),
    ('cistern','Barred sewer mouth, falling water and impact basin',(176,0,304,112)),
    ('market','Market, displayed wares and absentminded frog',(8,48,136,120)),
    ('wizard','Hooded purple wizard, staff flame and rug',(280,40,392,120)),
    ('bridge','Bridge linking banks across the sewage stream',(208,128,272,224)),
    ('rail','Rail separating the player from flowing sewage',(112,120,224,208)),
    ('outfall','Open brass waste pipe pouring into the stream',(416,104,480,184)),
    ('storage','Exposed wooden crate lids, barrel and ground filth',(392,56,464,112)),
    ('grate','Walkable floor drain with a clear barred surface',(192,216,288,264)),
    ('bottom-bank','Lower rail, dirty coping, moss and moving water',(64,248,192,320)),
)
REFERENCE_CRITERIA = (
    ('Silhouette and negative space', 'S2 pp.3–8; S3 p.2; S4 p.18',
     'Read the frog eye/jaw mass and the wizard hood/staff before texture. Keep deliberate gaps and one primary identity detail.'),
    ('Native-size economy', 'S2 pp.4–6; S4 pp.9–14 and p.7 embedded chart; S5 pp.2–7',
     'Judge the real 1× footprint. Use a few strong masses and two or three values per material; a sixteen-ink bank is a ceiling.'),
    ('Controlled line cadence', 'S1 pp.1–2; S6 pp.7–12',
     'Clean accidental kinks and inconsistent pixel runs; preserve intentional chipped or organic shape breaks.'),
    ('Directional volume and material', 'S1 pp.4–5; S6 pp.15–24',
     'Upper-left light and contact shadows describe planes. Matte stone/cloth and glossy brass/slime need different highlight widths; avoid nested pillow bands.'),
    ('Value and hue hierarchy', 'S1 pp.2–3; S3 pp.2–5',
     'Use separated values, cooler shadows and warmer light. Keep the travel plane quieter than characters, ladder and gold focal fittings.'),
    ('Selective edge treatment', 'S1 pp.4–5; S3 p.3; S4 pp.18–19; S6 pp.11–12',
     'Keep moving silhouettes crisp. Existing-ink internal anti-aliasing can refine a curve; filtered blur and transparency fringes do not belong in game art.'),
    ('Texture with a purpose', 'S1 p.3; S3 p.4; S6 pp.16–20',
     'Use material-shaped clusters and accumulation. Sparse intentional dithering may serve roughness; blanket checker noise and equally strong floor grids do not.'),
    ('Stable identity in motion', 'S2 pp.6–8; S4 p.17',
     'Keep feet planted, preserve identifying shapes and inspect complete frame families. Source boards must be followed by actual idle, flame and flow recordings.'),
)


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
        self.before = Path(args.before).resolve() if getattr(args, 'before', None) else None
        if self.before:
            assert self.before.is_dir(), ('Missing previous source gallery', str(self.before))
            assert self.before != self.out.resolve() and self.before not in self.out.resolve().parents and self.out.resolve() not in self.before.parents, 'The previous gallery must remain immutable and outside the output tree'
        self.before_hashes = {}
        self.review_pages = []
        self.comparison_pages = []
        self.painter_paths = tuple(sorted((ROOT/'art').glob('sewer*.py'))) + (ROOT/'art/reboot_contracts.json',)
        self.painter_snapshot = {str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in self.painter_paths}
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
            for palette in (self.T.palette(style), self.N.peddler_palette(self.npc_style(style,'peddler')),
                            self.N.wizard_palette(self.npc_style(style,'wizard'))):
                legal_palette(palette)

    @staticmethod
    def npc_style(option, who):
        """Resolve a room option to its explicitly selected character painter."""
        return S.recipe(option)['peddler' if who in ('peddler','peddler_head','peddler_body') else 'wizard']

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
            # The appended breathing body is selected with the existing
            # one-pixel head bob; source rest/breathe views use that same join.
            A.stamp(image,head,(8,7 if frame=='breathe' else 6));A.stamp(image,body,(0,0))
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
            frames=list(next(c['frames'] for c in CONTRACTS['sheets'] if c['name']==sheet))
            if sheet=='peddler_body':frames.append('breathe')
            scale=3 if size[0]<=16 else 2
            height=max(64,size[1]*scale+12)
            board=panel((1090,78+len(frames)*height));d=self.header(board,sheet+' / all frame IDs',
                  'Native character selected by each room recipe. Palette 0 is transparent; enlarged with nearest neighbour.')
            for row,frame in enumerate(frames):
                y=78+row*height
                d.rectangle((8,y,1081,y+height-3),fill=PANEL if row%2==0 else BG)
                label(d,(12,y+12),frame+' (new in v2)' if sheet=='peddler_body' and frame=='breathe' else frame,FONT)
                record={'sheet':sheet,'frame':frame,'native_canvas':list(size),'styles':{}}
                if sheet=='peddler_body' and frame=='breathe':record['new_in_revision']=2
                for style in self.styles:
                    actor_style=self.npc_style(style,sheet)
                    im=painter(actor_style,frame);check_image(im,size)
                    paste(board,im,(240+(style-1)*174,y+6),paletter(actor_style),scale)
                    record['styles'][str(style)]={'actor_style':actor_style,'indexed_sha256':digest(im.tobytes())}
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
                actor_style=self.npc_style(style,who)
                im=self.N.portrait(actor_style,who);check_image(im,(48,48))
                pal=self.N.peddler_palette(actor_style) if who=='peddler' else self.N.wizard_palette(actor_style)
                paste(board,im,(225+(style-1)*174,y+4),pal,2)
                record['styles'][str(style)]={'actor_style':actor_style,'indexed_sha256':digest(im.tobytes())}
            self.records.append(record)
        save(board,self.out/'sprites/portraits.png');self.npc_pages.append({'sheet':'portraits','file':'sprites/portraits.png','frames':['peddler','gatekeeper']})
        # Whole connected actors matter more than isolated head and torso pieces.
        board=panel((1090,78+2*142));d=self.header(board,'Frog and wizard variations / preferred identities guide all five',
                  'Native 32×32 composites, enlarged 3×. Based on v2 frog #1 and wizard #5; anchors and runtime order stay fixed.')
        for row,who in enumerate(('peddler','wizard')):
            y=84+row*142
            label(d,(12,y+25),'Billious Peddler' if who=='peddler' else 'Flame-staff wizard',FONT)
            for style in self.styles:
                im,pal=self.world_actor(self.npc_style(style,who),who)
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
        for slug,title,box in FIXTURES:
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

    def previous_room(self, style):
        relative=f'rooms/room-{style}-native.png'
        path=self.before/relative
        assert path.is_file(), ('Previous room assembly missing', str(path))
        self.before_hashes[relative]=digest(path.read_bytes())
        manifest=self.before/'source-manifest.json'
        if manifest.is_file():
            expected=json.loads(manifest.read_text())['files'].get(relative)
            assert expected==self.before_hashes[relative], ('Previous room differs from its source manifest', relative)
        with Image.open(path) as image:
            assert image.size==(480,320), ('Previous room has a different native footprint', str(path), image.size)
            return image.convert('RGBA')

    def water_motion(self):
        """Review connected liquid features at 1× without posing an emulator."""
        from bloom_suite_gallery import write_gif
        frames=[]
        crops=(('cistern / falling sheet',(176,0,304,112),(8,61)),
               ('stream / bridge',(192,136,288,208),(8,195)),
               ('open waste pipe',(432,112,480,184),(111,195)))
        for tick in range(0,128,4):
            board=panel((850,280));d=ImageDraw.Draw(board)
            d.fontmode='1'
            label(d,(8,5),'WATER AT NATIVE SCALE / source animation, not emulator footage',FONT,GOLD)
            label(d,(8,22),'Unfiltered native pixels. Cistern, horizontal stream and open pipe share the same room clock.',SMALL,MUTED)
            for style in self.styles:
                x=(style-1)*170
                label(d,(x+8,41),f'{style}. {STYLE_SHORT[style]}',SMALL,GOLD)
                room=self.source_room(S.recipe(style),tick=tick)
                for title,box,(dx,dy) in crops:
                    if box[0]==192:label(d,(x+8,179),'stream          waste pipe',SMALL,MUTED)
                    board.alpha_composite(room.crop(box),(x+dx,dy))
            frames.append(board.convert('RGB'))
        fps=16777216/280896
        durations=[round(min(128,t+4)/fps*100)*10-round(t/fps*100)*10 for t in range(0,128,4)]
        info=write_gif(frames,durations,self.out/'water-motion-native.gif')
        assert info['exact_palette'], 'Source water comparison must preserve every color'
        self.review_pages.append({'kind':'native connected-water source motion','file':'water-motion-native.gif',
                                  'source_not_emulator':True,'sample_updates':list(range(0,128,4)),**info})

    def value_image(self, image):
        # Review diagnostic only: never feed converted pixels into the game.
        return ImageOps.grayscale(image.convert('RGB')).convert('RGBA')

    def review_diagnostics(self):
        """Expose value grouping and silhouette; make no automatic taste score."""
        overview=panel((990,3*354+40));d=ImageDraw.Draw(overview)
        label(d,(12,8),'VALUE GROUPING / grayscale source diagnostics, not game art',TITLE,GOLD)
        for number in range(1,9):
            native=self.value_image(self.rooms[number]['image'])
            path=f'diagnostics/room-{number}-value-native.png'
            large=f'diagnostics/room-{number}-value-2x.png'
            save(native,self.out/path)
            save(native.resize((960,640),Image.Resampling.NEAREST),self.out/large)
            self.review_pages.append({'kind':'room value','recipe':number,'native':path,'enlarged':large})
            if number<=5:
                x=10+(number-1)%2*490;y=42+(number-1)//2*354
                label(d,(x,y),f'{number}. {STYLE_SHORT[number]}',FONT,GOLD)
                overview.alpha_composite(native,(x,y+24))
        save(overview,self.out/'diagnostics/room-value-overview.png')
        self.review_pages.append({'kind':'room value overview','file':'diagnostics/room-value-overview.png'})

        # At actual scale each cell contains the same native32px character in
        # color, value-only and a solid mask. The enlarged sheet repeats those
        # identical pixels, not a more detailed redraw.
        native_board=panel((1090,78+2*92));d=self.header(native_board,
            'CHARACTER READS AT 1× / color · value · silhouette',
            'Diagnostic views of the exact same native 32×32 composite. Do not judge only the enlargement.')
        zoom_board=panel((990,82+5*146));zd=ImageDraw.Draw(zoom_board)
        label(zd,(12,8),'CHARACTER SHAPES AT 3× / nearest-neighbour diagnostic enlargement',TITLE,GOLD)
        label(zd,(12,34),'Frog: color / value / silhouette                         Wizard: color / value / silhouette',FONT,MUTED)
        for row,who in enumerate(('peddler','wizard')):
            y=84+row*92
            label(d,(12,y+20),'Frog Peddler' if who=='peddler' else 'Purple wizard',FONT)
            for style in self.styles:
                indexed,pal=self.world_actor(self.npc_style(style,who),who)
                color=rgba(indexed,pal)
                mask=color.getchannel('A')
                value=self.value_image(color)
                value.putalpha(mask)
                silhouette=Image.new('RGBA',indexed.size,'#eee7c8')
                silhouette.putalpha(mask)
                images=(color,value,silhouette)
                x=224+(style-1)*174
                for k,image in enumerate(images):
                    native_board.alpha_composite(image,(x+k*48,y+16))
                zy=82+(style-1)*146
                if row==0:label(zd,(12,zy+35),f'{style}. {STYLE_SHORT[style]}',FONT,GOLD)
                zx=208+row*378
                for k,image in enumerate(images):
                    zoom_board.alpha_composite(image.resize((96,96),Image.Resampling.NEAREST),(zx+k*116,zy+8))
                if style==1:
                    for k,name in enumerate(('color','value','shape')):label(d,(224+k*48,71),name,SMALL,MUTED)
        save(native_board,self.out/'diagnostics/character-reads-1x.png')
        save(zoom_board,self.out/'diagnostics/character-reads-3x.png')
        self.review_pages.extend([
            {'kind':'native character shape/value','file':'diagnostics/character-reads-1x.png'},
            {'kind':'enlarged character shape/value','file':'diagnostics/character-reads-3x.png'},
        ])

        idle=panel((1090,78+112));idraw=self.header(idle,
            'FROG IDLE JOINS / rest and new breathing pose',
            'Native 1× pair above, nearest-neighbour 2× pair below. Head bob and torso compress; the feet stay planted.')
        for style in self.styles:
            for k,frame in enumerate(('rest','breathe')):
                indexed,pal=self.world_actor(self.npc_style(style,'peddler'),'peddler',frame)
                x=226+(style-1)*174+k*68
                paste(idle,indexed,(x,82),pal)
                paste(idle,indexed,(x,120),pal,2)
                label(idraw,(x,70),'rest' if k==0 else 'breathe',SMALL,MUTED)
        save(idle,self.out/'diagnostics/frog-idle-joins.png')
        self.review_pages.append({'kind':'rest and breathing join','file':'diagnostics/frog-idle-joins.png'})

    def before_after(self):
        if not self.before:return
        overview=panel((990,5*354+44));d=ImageDraw.Draw(overview)
        label(d,(12,8),'PREVIOUS / REVISED / native source assemblies, same physical room',TITLE,GOLD)
        value_overview=panel(overview.size);vd=ImageDraw.Draw(value_overview)
        label(vd,(12,8),'PREVIOUS / REVISED VALUE GROUPING / grayscale diagnostics',TITLE,GOLD)
        previous={style:self.previous_room(style) for style in self.styles}
        for style in self.styles:
            old=previous[style];new=self.rooms[style]['image']
            board=panel((984,366));bd=ImageDraw.Draw(board)
            label(bd,(12,8),f'{style}. {STYLE_SHORT[style]} / v2 and feedback-led v3 source assets',TITLE,GOLD)
            label(bd,(12,32),f'Previous v2 option {style}',FONT,MUTED);label(bd,(502,32),'Revised v3',FONT,GOLD)
            board.alpha_composite(old,(8,46));board.alpha_composite(new,(498,46))
            path=f'before-after/room-{style}-1x.png'
            large=f'before-after/room-{style}-2x.png'
            save(board,self.out/path)
            save(board.resize((1968,732),Image.Resampling.NEAREST),self.out/large)
            value=board.copy();value.paste(self.value_image(old),(8,46));value.paste(self.value_image(new),(498,46))
            value_path=f'before-after/room-{style}-value-1x.png'
            save(value,self.out/value_path)
            y=44+(style-1)*354
            label(d,(10,y),f'Previous v2 option {style}',FONT,MUTED)
            label(d,(500,y),'Revised',FONT,GOLD)
            overview.alpha_composite(old,(10,y+24));overview.alpha_composite(new,(500,y+24))
            label(vd,(10,y),f'Previous v2 option {style}',FONT,MUTED)
            label(vd,(500,y),'Revised',FONT,GOLD)
            value_overview.alpha_composite(self.value_image(old),(10,y+24))
            value_overview.alpha_composite(self.value_image(new),(500,y+24))
            self.comparison_pages.append({'kind':'whole room','style':style,'native':path,'enlarged':large,'value':value_path})
        save(overview,self.out/'before-after/room-overview.png')
        save(value_overview,self.out/'before-after/room-value-overview.png')

        for slug,title,box in FIXTURES:
            w,h=box[2]-box[0],box[3]-box[1];col=max(w*2+12,174)
            board=panel((12+col*5,100+2*(h*2+30)));bd=ImageDraw.Draw(board)
            label(bd,(12,8),title+' / previous above, revised below',TITLE,GOLD)
            label(bd,(12,32),'Matched native source crops enlarged 2×; compare form, plane and focal contrast before texture.',SMALL,MUTED)
            for style in self.styles:
                x=6+(style-1)*col
                label(bd,(x+4,54),f'{style}. {STYLE_SHORT[style]}',SMALL,GOLD)
                for row,image in enumerate((previous[style],self.rooms[style]['image'])):
                    y=80+row*(h*2+30)
                    label(bd,(x+4,y-15),'Previous' if row==0 else 'Revised',SMALL,MUTED)
                    board.alpha_composite(image.crop(box).resize((w*2,h*2),Image.Resampling.NEAREST),(x+4,y))
            path=f'before-after/fixture-{slug}.png';save(board,self.out/path)
            self.comparison_pages.append({'kind':'fixture','id':slug,'label':title,'source_crop':list(box),'file':path})

    def finalize(self):
        assert len(self.used)==370 and len(self.unused)==80
        tile_records=[r for r in self.records if 'global_id' in r]
        active_frames=sum(r['frames']*5 for r in tile_records if r['status']=='active')
        unused_frames=sum(r['frames']*5 for r in tile_records if r['status']!='active')
        assert active_frames==623*5 and unused_frames==113*5
        world_npc_frames=sum(len(row['frames']) for row in self.npc_pages
                             if row['sheet'] in ('peddler_head','peddler_body','gatekeeper','wisp'))
        assert world_npc_frames==30, 'v2 retains29 keeper frames and appends one breathing body pose'
        for style in self.styles:
            all_bytes=b''.join(self.tile(t['name'],0,style).tobytes() for t in self.used)
            self.checks.append({'style':style,'active_terrain_indexed_sha256':digest(all_bytes)})
        assert len({r['active_terrain_indexed_sha256'] for r in self.checks})==5,'Styles must change geometry, not only palettes'
        for who in ('peddler','wizard'):
            hashes={digest(self.world_actor(self.npc_style(style,who),who)[0].tobytes()) for style in self.styles}
            assert len(hashes)==5,(who,'five structural alternatives required')
        sharing=Counter(len({tuple(v['indexed_frame_sha256']) for v in r['styles'].values()})
                        for r in tile_records if r['status']=='active')
        identical=[r['name'] for r in tile_records if r['status']=='active' and
                   len({tuple(v['indexed_frame_sha256']) for v in r['styles'].values()})==1]
        painter_hashes={str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in self.painter_paths}
        assert painter_hashes==self.painter_snapshot, 'Painter sources changed during gallery generation; rerun after freezing the art'
        if self.before:
            assert all(digest((self.before/name).read_bytes())==value for name,value in self.before_hashes.items()), 'Previous source gallery changed during comparison'
        catalog={'method':__doc__.strip(),'native_screen':[240,160],'native_room':[480,320],
          'painter_source_sha256':painter_hashes,
          'source_assembly_not_emulator':True,'styles':S.STYLE_NAMES,'records':self.records,
          'tile_atlases':self.pages,'animated_tile_filmstrips':self.animation_pages,
          'npc_atlases':self.npc_pages,'fixtures':self.fixture_pages,
          'review_diagnostics':self.review_pages,'before_after_comparisons':self.comparison_pages,
          'before_source_room_sha256':self.before_hashes,
          'reference_review':{'criteria':[{'topic':topic,'pdf_pages':pages,'review_question':question} for topic,pages,question in REFERENCE_CRITERIA],
              'sources':{'S1':'Richard Janes','S2':'the-pixel.art character design','S3':'Alain Galvan',
                         'S4':'Adafruit / John Park','S5':'Thomas Palef','S6':'Livresquare / CLIP STUDIO TIPS'},
              'meaning':'Page citations refer to supplied PDFs. These are review criteria and GBA adaptations, not automatic taste scores or claims that a source prescribed these exact sewer designs.'},
          'rooms':[{k:v for k,v in row.items() if k!='image'} for row in self.rooms.values()],
          'coverage':{'active_tile_ids':370,'active_frame_alternatives':active_frames,'unused_catalogue_ids':80,
                      'unused_frame_alternatives':unused_frames,'world_npc_frame_alternatives':world_npc_frames*5,
                      'retained_world_npc_frame_alternatives':29*5,'new_breathing_frame_alternatives':5,
                      'portrait_alternatives':2*5,'new_foreground_rail_alternatives':5,
                      'unchanged_bloom':True,'ambient_glitter_in_source_assemblies':False},
          'indexed_geometry_sharing':{'number_of_distinct_sequences_to_active_id_count':dict(sorted(sharing.items())),
              'identical_indexed_sequences_in_all_five':identical,
              'meaning':'Small blank or seam pieces can retain indexed geometry across concepts; palette color may still differ. No random pixel edits were added to force five unique hashes.'},
          'geometry_checks':self.checks}
        (self.out/'catalogue.json').write_text(json.dumps(catalog,indent=2)+'\n')
        shutil.copy2(self.inventory_path,self.out/'inventory.json')
        source_inventory_md=self.inventory_path.with_name('README.md')
        if source_inventory_md.exists():
            inventory_text=source_inventory_md.read_text()
            current_note='''
> Current study additions: the physical tile/room inventory below is inherited
> unchanged from the released source contract. The concept builds retain the
> appended `peddler_body.breathe` ID 14 from v2, giving **15 frog body frames and
> 30 world keeper/flame frames** in total. Portraits have a separately authored
> 48×48 drawing inside the retained padded sheet. The complete current artwork,
> selected recipe styles and frame hashes are in [catalogue.json](catalogue.json).
> Historical source bounds identify feature envelopes, not a requirement to
> preserve old pixel silhouettes.

'''
            inventory_text=inventory_text.replace('# Drain visual inventory\n','# Drain visual inventory\n\n'+current_note,1)
            (self.out/'INVENTORY.md').write_text(inventory_text)
        self.readme(catalog)
        files={str(p.relative_to(self.out)):digest(p.read_bytes()) for p in sorted(self.out.rglob('*')) if p.is_file() and p.name!='source-manifest.json'}
        (self.out/'source-manifest.json').write_text(json.dumps({'method':'All source image pixels authored at native resolution; source assemblies are not emulator captures.','files':files},indent=2)+'\n')
        print(json.dumps({'output':str(self.out),'files':len(files),'active_frame_alternatives':active_frames,
                          'unused_frame_alternatives':unused_frames,'rooms':8,'fixture_comparisons':len(self.fixture_pages)},indent=2))

    def readme(self,catalog):
        text='''# Drain art concepts v3: feedback-led redraw

Five complete native-GBA art directions and three mixed-component rooms use
the same Drain layout. All five use gray slimy masonry, dirty ground, flowing
sewage, bright gold fittings, a clear forest ladder, railings and a bridge.
The Billious Peddler is a cartoon frog; the old wizard wears a purple hood and
carries a flame-tipped staff. Bloom, the shared UI and the existing ambient
glitter are preserved.

These five new treatments respond to the second-pass feedback. Frog variations
build on the preferred v2 #1 frog, and wizard variations build on v2 #5's
pointed purple hood. The later instruction to continue exploring both actors
is represented by five related alternatives, rather than identical copies.

| Family | Feedback carried into this pass |
| --- | --- |
| Floors | Every previous floor rejected: new gray brick/flag bonds with quieter, purposeful joints. |
| Walls | #4 closest: damaged connected masonry and coherent damp deposits. |
| Ladder | #1 closest; all arrows illegible: a separate dark sign and a plain high-contrast up arrow. |
| Cistern | Keep the broad arch language of #1/#4; replace root-like streams with falling sheets and visible water impact. |
| Market | #1/#2 closest, none approved: new cloth-and-wood stalls and readable wares. |
| Wizard corner | #1/#2/#5 atmosphere with #4's dilapidation. |
| Bridge | #4 closest: worn serviceable timber spanning the actual channel. |
| Rail | #1/#2 structure plus #4's grime and decay. |
| Gold outfall | Make its purpose visible: an open waste-pipe mouth and a pour into the stream. |
| Storage | #1/#2 construction; remove the ambiguous blob so wooden lids and barrel surfaces read. |
| Floor grate | #4's worn barred opening. |
| Floor bank | Dirty coping and a clear water boundary, drawing from #1/#2/#4. |

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
coin and hand animations. The retained fifteenth body frame, `breathe`, compresses the
upper body with the one-pixel head bob while keeping the feet planted. The
fourteen original body IDs retain their ordering. The wizard's frame IDs remain stable; its
separate four-frame flame now belongs at the staff tip. Portraits are authored
independently at48×48 and match their world identities.

A study-only16×8foreground sprite supplies a continuous handrail between the retained
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
declared frame drawings per option. Atlas rows show phase0; every other
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
## PDF-led review of this revision

The six supplied reference PDFs guide the revised forms, materials and review
workflow. Their page-specific notes, adaptations and adoption decisions live
in the shared [reference register](../../../bartgame/docs/art-reboot/REFERENCE_REGISTER.md),
[art bible](../../../bartgame/docs/art-reboot/ART_BIBLE.md) and
[direction log](../../../bartgame/docs/art-reboot/ART_DIRECTION_LOG.md).
The [reference-application matrix](../../../bartgame/docs/art-reboot/REFERENCE_APPLICATION.md)
connects adopted rules to source pages, explicit GBA adaptations and this pass.

These diagnostics expose the same native source pixels at different review
views. **Grayscale and silhouette sheets are inspection tools, not replacement
game art or emulator screenshots.** Native 1× views are the primary readability
test; enlargements use integer nearest-neighbour scaling.

- [Whole-room value grouping](diagnostics/room-value-overview.png)
- [NPC color, value and silhouette at native size](diagnostics/character-reads-1x.png)
- [The same NPC pixels enlarged 3×](diagnostics/character-reads-3x.png)
- [Rest/breathe joins at native size and 2×](diagnostics/frog-idle-joins.png)
- [Connected water at native scale: source animation](water-motion-native.gif)

| Topic | Supplied PDF pages | Review question / GBA application |
| --- | --- | --- |
'''
        for topic,pages,question in REFERENCE_CRITERIA:
            text+=f'| {topic} | {pages} | {question} |\n'
        text+='''
S1 is Richard Janes; S2 is the-pixel.art character design; S3 is Alain Galvan;
S4 is Adafruit/John Park; S5 is Thomas Palef; S6 is Livresquare/CLIP STUDIO TIPS.
Page numbers refer to the actual supplied print PDFs, not website sections.
The register distinguishes read text from illustrations unavailable in a print.
No reference images or Nintendo pixels are used as game assets.

For this GBA pipeline, optional large-canvas sketch reduction, blur, unrestricted
colors and posterization are translated into native blockouts, controlled
indexed-palette correction and deliberate pixel edits. Internal hand-placed
edge treatment is distinct from automatic filtering. The diagnostic questions
do not manufacture an art-quality score or automatically approve a treatment.

'''
        if self.before:
            text+='''
## Previous and revised source art

Every pair uses the same world coordinates and unchanged room footprint.
The left column is the previously published source assembly; the right column
is this revision. The old input images are read only and recorded by hash.
These comparisons demonstrate iteration; they do not replace actual-run
animation and occlusion checks.

![Five previous/revised native room pairs](before-after/room-overview.png)

[Previous/revised value grouping](before-after/room-value-overview.png)

'''
            for row in self.comparison_pages:
                if row['kind']=='whole room':
                    text+=f"- [{row['style']}. {STYLE_SHORT[row['style']]}: native pair]({row['native']}) · [2× pair]({row['enlarged']}) · [Value pair]({row['value']})\n"
                else:
                    text+=f"- [{row['label']}: all five previous/revised fixture pairs]({row['file']})\n"
            text+='\n'
        text+='''
## Scope and critique limits

These are choices for feedback. A complete option has not been selected for
the released game. Shared HUD, shop chrome, font, inventory, conditional item
effects, Bloom and runtime glitter are catalogued as preserved common assets;
they do not receive five Drain-only redesigns that would make them inconsistent
with the forest. There are no authored Drain enemy, chest or switch spawns.

Each complete direction changes indexed geometry as well as palette; both
NPC families also have five distinct composite geometries. A full native room map
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
               'real240':'real 240','new16×8foreground':'new 16×8 foreground',
               'study-only16×8foreground':'study-only 16×8 foreground'}
        for old,new in fixes.items():text=text.replace(old,new)
        shortcuts='[PDF-led review and native diagnostics](#pdf-led-review-of-this-revision)'
        if self.before:shortcuts+=' · [Previous/revised comparisons](#previous-and-revised-source-art)'
        text=text.replace('[Every alternative and frame hash](catalogue.json)',
                          '[Every alternative and frame hash](catalogue.json)\n\n'+shortcuts,1)
        (self.out/'README.md').write_text(text)

    def run(self):
        self.asset_records()
        self.pages=self.tile_pages(self.used,'tiles','Active Drain metatiles')
        self.unused_pages=self.tile_pages(self.unused,'unused-tiles','Unused retained sewer vocabulary')
        self.animation_pages=self.animations(self.used,'animation-frames')+self.animations(self.unused,'unused-animation-frames')
        self.room_maps();self.npc_atlases();self.fixtures();self.water_motion()
        self.review_diagnostics();self.before_after();self.finalize()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True)
    ap.add_argument('--inventory',default='/workspace/setup/sewer-concepts/inventory/inventory.json')
    ap.add_argument('--before',help='Read-only prior source gallery for matched native before/after room and fixture comparisons')
    Gallery(ap.parse_args()).run()


if __name__=='__main__':
    main()
