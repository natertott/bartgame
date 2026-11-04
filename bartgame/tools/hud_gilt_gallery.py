#!/usr/bin/env python3
"""Publish the reviewed native HUD, item source catalog and exact playable ROM.

This tool never renders game scenes or alters a captured framebuffer. All
boards are literal native images/crops and integer-nearest inspection views.
Source-only paintings are cataloged separately from actual mGBA evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageSequence

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parent
TOOL_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
BG, GOLD, DIM = '#101820', '#f8e0a0', '#b0c0b8'
FONT = ImageFont.load_default()
CONTEXTS = (
    ('03-drain.png', 'Drain'),
    ('09-healthy-forest.png', 'Healthy forest'),
    ('10-deep-forest.png', 'Deep blight'),
    ('11-mystery.png', 'Mystery interior'),
)
DETAILS = (
    ('03-drain.png', 'Bomb / shield / bow'),
    ('04-lantern-cape-hubcap.png', 'Lantern / cape / Drain Cap'),
    ('05-sword-shield-halfheart.png', 'Sword / shield / half heart'),
    ('06-zero-ammunition.png', 'Empty ammunition'),
    ('07-byte-ammunition-extremes.png', '255 ammunition / 65,535 gilt'),
    ('08-empty-equipment.png', 'Empty equipment slots'),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rgb_sha(image):
    return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n')


def safe(root, relative):
    path = (root/relative).resolve()
    assert path.is_relative_to(root.resolve()), ('Unsafe relative path', relative)
    return path


class Gallery:
    def __init__(self, args):
        self.args = args
        self.out = Path(args.out).resolve()
        self.bundle = Path(args.bundle).resolve()
        self.before = Path(args.before).resolve()
        self.after = Path(args.after).resolve()
        self.items = Path(args.items).resolve()
        self.qa, self.panels = [], []
        self.source = (self.bundle/'source-commit.txt').read_text().strip()
        assert re.fullmatch(r'[a-f0-9]{40}', self.source), self.source
        self.rom = self.bundle/'bartgame.gba'
        self.release = REPO/'downloads'/('hud-gilt-'+self.source[:7])
        self.out.mkdir(parents=True, exist_ok=True)

    def check(self, name, passed, detail=None):
        row = dict(name=name, passed=bool(passed))
        if detail is not None:
            row['detail'] = detail
        self.qa.append(row)
        assert passed, (name, detail)

    def copy(self, src, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        self.check('exact copy '+str(dst.relative_to(REPO)), sha(src)==sha(dst))

    def reports(self):
        self.reports = {}
        for phase, root in (('before', self.before), ('after', self.after)):
            report = json.loads((root/'report.json').read_text())
            self.check(phase+' capture completed', report['complete'] and report.get('error') is None)
            self.check(phase+' all capture checks passed', report['passed']==report['total'])
            self.reports[phase] = report
            target = self.out/'actual'/phase
            for row in report['media']+report.get('motion_frames', []):
                path = safe(root, row['file'])
                self.check(phase+' capture hash '+row['file'], sha(path)==row['sha256'])
                with Image.open(path) as im:
                    self.check(phase+' native framebuffer '+row['file'], im.size==(240, 160))
                self.copy(path, safe(target, row['file']))
            for name in ('hud-shimmer-and-map.gif', 'motion-contact.png',
                         'contexts-actual-native.png', 'top-hud-inspection-4x.png'):
                path = root/name
                if path.exists():
                    self.copy(path, target/name)
            self.copy(root/'report.json', self.out/'validation'/(phase+'-capture.json'))
            motion = report.get('motion')
            if motion:
                gif = Image.open(target/'hud-shimmer-and-map.gif')
                step = motion['gif_sample_step']
                sample = 0
                for i, frame in enumerate(ImageSequence.Iterator(gif)):
                    duration=frame.info['duration']
                    hold=motion['gif_duration_ms']
                    self.check(phase+' GIF duration '+str(i),duration>=hold and duration%hold==0)
                    # GIF encoders may join identical adjacent samples. Check
                    # every represented hold against its literal raw frame.
                    for _ in range(duration//hold):
                        native = Image.open(target/'motion-native'/('%03d.png'%(sample*step)))
                        self.check(phase+' exact GIF sample '+str(sample),rgb_sha(frame)==rgb_sha(native))
                        sample += 1
                self.check(phase+' GIF sample count', sample==len(report['motion_frames'][::step]))
        after = self.reports['after']
        self.check('after report frozen game source', after['source_commit']==self.source)
        self.check('after report exact released ROM', after['rom_sha256']==sha(self.rom))

    def panel(self, board, src, at, box=None, scale=1):
        image = Image.open(src).convert('RGB')
        if box:
            image = image.crop(box)
        if scale!=1:
            image = image.resize((image.width*scale, image.height*scale), Image.Resampling.NEAREST)
        board.paste(image, at)
        self.panels.append(dict(source=str(Path(src).relative_to(self.out)),
            rectangle=[at[0],at[1],at[0]+image.width,at[1]+image.height],
            crop=list(box) if box else None, scale=scale, RGB_sha256=rgb_sha(image)))

    def board_save(self, image, name):
        path = self.out/name
        image.save(path)
        back = Image.open(path).convert('RGB')
        records = self.panels
        self.panels = []
        for i, row in enumerate(records):
            self.check(name+' literal panel '+str(i), rgb_sha(back.crop(row['rectangle']))==row['RGB_sha256'])
        return dict(file=name, sha256=sha(path), panels=records)

    def boards(self):
        self.boards = []
        image = Image.new('RGB', (496, 60+len(CONTEXTS)*184), BG)
        draw = ImageDraw.Draw(image)
        draw.text((8,8), 'ACTUAL mGBA / native240x160 views, no retouching', font=FONT, fill=GOLD)
        draw.text((8,28), 'Previous compact HUD', font=FONT, fill=DIM)
        draw.text((256,28), 'Gleaming gilt HUD', font=FONT, fill=DIM)
        for i, (name, label) in enumerate(CONTEXTS):
            y = 54+i*184
            draw.text((8,y), label, font=FONT, fill=GOLD)
            self.panel(image,self.out/'actual'/'before'/name,(8,y+16))
            self.panel(image,self.out/'actual'/'after'/name,(256,y+16))
        self.boards.append(self.board_save(image,'before-after-actual.png'))

        image = Image.new('RGB', (496, 56+len(DETAILS)*60), BG)
        draw = ImageDraw.Draw(image)
        draw.text((8,8), 'ACTUAL HUD CROPS / 1x native pixels', font=FONT, fill=GOLD)
        draw.text((8,27), 'Previous / new. Counters are disclosed inventory fixtures.',font=FONT,fill=DIM)
        for i, (name,label) in enumerate(DETAILS):
            y = 52+i*60
            draw.text((8,y), label,font=FONT,fill=GOLD)
            self.panel(image,self.out/'actual'/'before'/name,(8,y+17),(0,0,240,24))
            self.panel(image,self.out/'actual'/'after'/name,(256,y+17),(0,0,240,24))
        self.boards.append(self.board_save(image,'equipment-actual.png'))

        image = Image.new('RGB', (496, 46+3*76), BG)
        draw = ImageDraw.Draw(image)
        draw.text((8,8), 'ACTUAL BUTTON FEEDBACK / 2x nearest inspection',font=FONT,fill=GOLD)
        draw.text((8,24), 'Released then held; physical A, B and L inputs.',font=FONT,fill=DIM)
        for i,key in enumerate(('A','B','L')):
            y = 46+i*76
            draw.text((8,y), key,font=FONT,fill=GOLD)
            for j,state in enumerate(('released','held')):
                self.panel(image,self.out/'actual'/'after'/('button-'+key+'-'+state+'.png'),
                           (8+j*248,y+17),(144,0,240,20),scale=2)
        self.boards.append(self.board_save(image,'button-feedback-actual.png'))
        dump(self.out/'boards.json',dict(method='Literal framebuffer/crop placement; nearest-only integer inspection.',boards=self.boards))

    def sources(self):
        catalog = json.loads((self.items/'manifest.json').read_text())
        root = self.out/'source'
        root.mkdir(parents=True,exist_ok=True)
        rows = []
        for row in catalog['frames']:
            mode,name = row['sheet'],row['frame']
            indexed = safe(self.items,row['indexed'])
            rgba = safe(self.items,row['rgba'])
            self.check('source manifest indexed hash '+mode+'/'+name,sha(indexed)==row['indexed_sha256'])
            self.check('source manifest RGBA hash '+mode+'/'+name,sha(rgba)==row['rgba_sha256'])
            with Image.open(indexed) as im:
                self.check('native indexed source '+mode+'/'+name, im.mode=='P' and list(im.size)==row['canvas'])
                inks=set(im.get_flattened_data())
                self.check('4bpp source '+mode+'/'+name, max(inks)<16 and min(inks)>=0)
                self.check('binary transparent source '+mode+'/'+name, im.info.get('transparency')==0)
                palette=im.getpalette()[:48]
                self.check('RGB555 author inks '+mode+'/'+name, all(n%8==0 for n in palette))
                self.check('documented author palette '+mode+'/'+name,
                           palette==[n for color in row['palette_rgb555'] for n in color])
                source_rgb=im.convert('RGBA')
                preview=Image.open(rgba).convert('RGBA')
                self.check('matching indexed and RGBA source '+mode+'/'+name,source_rgb.tobytes()==preview.tobytes())
            for path in (indexed,rgba):
                self.copy(path,root/'native'/path.name)
            rows.append({**row,'indexed_file':'native/'+indexed.name,'indexed_sha256':sha(indexed),
                         'RGBA_file':'native/'+rgba.name,'RGBA_sha256':sha(rgba)})
        self.copy(self.items/'representative'/'items-source.png',root/'items-source.png')
        self.copy(self.items/'manifest.json',root/'author-manifest.json')
        dump(root/'manifest.json',{'source_commit':self.source,'kind':'Native source paintings, not emulator captures.',
            'frames':rows,'author_color_note':'RGB555 source values retain their literal multiples-of-eight author colors; actual GBA screenshots show emulator display expansion.',
            'method':catalog['method']})
        self.source_rows=rows
        (root/'README.md').write_text('# Native item source catalog\n\n'
            'These are source paintings, separate from the [actual mGBA review](../README.md). '
            'HUD16, menu32 and compact-world16 canvases are independently drawn at final resolution. '
            'The board includes native pixels and2x nearest inspection views. '
            'Indexed PNGs retain4bpp indices, literal RGB555 author inks and transparent index0.\n\n'
            '![Native source item families](items-source.png)\n\n'
            '[Every indexed/RGBA asset and material record](manifest.json).\n')

    def validation(self):
        folder = self.out/'validation'
        for name in ('assets.h','bartgame.map','freeze.json','source-commit.txt'):
            path=self.bundle/name
            if path.exists():self.copy(path,folder/'frozen'/name)
        coverage=next((self.bundle/name for name in ('coverage.json','art-reboot-coverage.json') if (self.bundle/name).exists()),None)
        if coverage:self.copy(coverage,folder/'frozen'/'coverage.json')
        if self.args.audit:
            path=Path(self.args.audit).resolve()
            data=json.loads(path.read_text())
            self.check('independent audit all passed',data['passed']==data['total'])
            self.copy(path,folder/'audit.json')
            self.audit=data
        else:self.audit=None
        freeze=self.bundle/'freeze.json'
        if freeze.exists():
            self.freeze=json.loads(freeze.read_text())
            source_hashes=self.freeze.get('source_file_sha256',self.freeze.get('inputs',{}))
            self.check('freeze includes game/art input hashes',bool(source_hashes))
            if self.freeze.get('source_commit'):
                self.check('freeze source matches report source',self.freeze['source_commit']==self.source)
            self.check('release is not a pilot bundle','pilot' not in self.freeze.get('status','').lower())
            for name,expected in source_hashes.items():
                self.check('source unchanged since freeze '+name,sha(safe(GAME,name))==expected)
        else:self.freeze=None

    def release_files(self):
        self.release.mkdir(parents=True,exist_ok=True)
        stem='hud-gilt-'+self.source[:7]
        rom_name=stem+'.gba'
        self.copy(self.rom,self.release/rom_name)
        note=('BARTGAME — Gleaming gilt HUD\n\n'
            'Original standalone GBA game; no commercial base ROM required.\n'
            'Game/art source: '+self.source+'\n'
            'Selected build: BART_HUD1 / BART_FOREST32 / BART_UI6 / BART_MENU1 / BART_ENEMY11 / BART_SEWER9 / BART_SWING3\n'
            'ROM SHA256: '+sha(self.rom)+'\n\n'
            'A/B/L use assigned tools; Start opens/closes the bag; R changes bag page.\n'
            'Larger native item icons and button medallions, physical press feedback,\n'
            'gold border glints and a larger blinking-current-room minimap.\n'
            'Existing controls, save format, Bloom, enemies and environment paintings retained.\n')
        (self.release/'README.txt').write_text(note)
        sums=sha(self.release/rom_name)+'  '+rom_name+'\n'
        (self.release/'SHA256SUMS').write_text(sums)
        archive=self.release/(stem+'.zip')
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in (rom_name,'README.txt','SHA256SUMS'):
                info=zipfile.ZipInfo(name,date_time=(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644<<16
                z.writestr(info,(self.release/name).read_bytes())
        with zipfile.ZipFile(archive) as z:
            self.check('ZIP exact frozen playable ROM',hashlib.sha256(z.read(rom_name)).hexdigest()==sha(self.rom))
            self.check('ZIP documented checksum',z.read('SHA256SUMS').decode()==sums)
        self.release_record=dict(directory=str(self.release.relative_to(REPO)),rom=rom_name,
            rom_sha256=sha(self.rom),rom_bytes=self.rom.stat().st_size,zip=archive.name,
            zip_sha256=sha(archive),zip_bytes=archive.stat().st_size)
        prefix='https://raw.githubusercontent.com/natertott/bartgame/'+self.args.branch+'/'+str(self.release.relative_to(REPO))+'/'
        (self.release/'README.md').write_text('# Gleaming gilt HUD — playable ROM\n\n'
            '[Download ROM]('+prefix+rom_name+') · [Download ZIP]('+prefix+archive.name+')\n\n'
            '[Actual mGBA images and animation](../../art-review/hud-gilt/README.md).\n\n'
            'Game/art source `'+self.source+'`. Ordinary `make` builds the selected interface; '
            '`make BART_HUD=0` restores the previous compact HUD/item paintings.\n\n'
            '| File | Bytes | SHA256 |\n| --- | ---: | --- |\n'
            '| '+rom_name+' | '+str(self.rom.stat().st_size)+' | `'+sha(self.rom)+'` |\n'
            '| '+archive.name+' | '+str(archive.stat().st_size)+' | `'+sha(archive)+'` |\n')

    def readme(self):
        after,before=self.reports['after'],self.reports['before']
        audit_line=(' Independent source/scope/budget audit: **%d/%d**.'%(self.audit['passed'],self.audit['total'])) if self.audit else ''
        release_rel=os.path.relpath(self.release,self.out)
        lines=['# Gleaming gilt HUD and native item redraw','',
            'Larger item silhouettes and A/B/L medallions sit in local gold frames. '
            'Physical button presses brighten the corresponding badge. The minimap has a '
            'larger5×5 room grid, a gleaming gold border and a blinking current-room marker. '
            'Hearts, gilt and conditional ammunition remain the only other HUD fields. '
            'The center stays open; ground pickups retain their compact world scale.','',
            '[Download the playable ROM/ZIP]('+release_rel+'/README.md) · '
            '[All native item source art](source/README.md) · '
            '[Validation/provenance](validation/README.md)','',
            '## Actual mGBA scenes','',
            'Every game view below comes from a real run of the frozen ROM in mGBA0.10.5. '
            'Native PNGs remain240×160 and unretouched. The boards only place literal views '
            'or crops beside labels. Inventory, navigation and enemy-isolation fixtures are '
            'disclosed in the capture reports; these are readability tests, not an unassisted playthrough.','',
            '![Previous and new HUD in four real backgrounds](before-after-actual.png)','',
            '![Native equipment and counter crops](equipment-actual.png)','',
            '## Motion and button feedback','',
            '![Actual gold glints and map blinking](actual/after/hud-shimmer-and-map.gif)','',
            'The animation samples every sixth frame from180 actual simulation frames. '
            'Its100ms viewing holds are approximately the native59.73Hz playback rate; '
            'all raw frames and recorded game clocks remain in the [capture report](validation/after-capture.json). '
            'No HUD animation clocks or framebuffer pixels were injected.','',
            '![Released and physically held button badges](button-feedback-actual.png)','',
            '## Menus, dialogue and restoration','',
            '[Native item menu](actual/after/20-items.png) · '
            '[Key items](actual/after/21-key-items.png) · '
            '[Overview map](actual/after/22-map.png) · '
            '[Room zoom](actual/after/23-map-zoom.png) · '
            '[Return to gameplay](actual/after/24-after-menu.png).','',
            '[Opening dialogue](actual/after/13-unnamed-opening-dialogue.png) · '
            '[Wizard dialogue](actual/after/15-named-wizard-dialogue.png) · '
            '[Frog market](actual/after/17-frog-market.png).','',
            'Menu/dialogue frame and color options remain independent of the gameplay HUD. '
            'The minimap temporarily hides during dialogue to leave the text and continuation cue clear.','',
            '## Verification','',
            'Final capture: **%d/%d**; previous capture: **%d/%d**.'%(after['passed'],after['total'],before['passed'],before['total'])+audit_line,
            ' Source `'+self.source+'`; ROM SHA256 `'+sha(self.rom)+'`. '
            'The [source catalog](source/README.md) is explicitly separate from emulator evidence.','']
        (self.out/'README.md').write_text('\n'.join(lines))
        (self.out/'validation'/'README.md').write_text('# HUD verification and provenance\n\n'
            '[Final actual capture](after-capture.json) and [previous actual capture](before-capture.json) '
            'record the ROM/source/tool hashes, disclosed fixtures, native media hashes, hardware HUD/OAM '
            'readback, physical input feedback and saved world snapshots around menus.\n\n'
            +('[Independent audit](audit.json) checks scope, source/hardware constraints and historical restoration.\n\n' if self.audit else '')
            +'[Publication QA](publication-qa.json) checks exact file copies, native framebuffer sizes, literal '
            'comparison/crop panels, exact GIF samples, native source indexing/palettes, ZIP ROM identity '
            'and all local Markdown links. [Frozen build records](frozen/) retain header/map/source identity.\n')

    def links(self):
        for root in (self.out,self.release):
            for path in root.rglob('*.md'):
                for match in re.finditer(r'(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                    href=(match.group(1) or match.group(2)).split('#')[0]
                    if not href or re.match(r'[a-z]+://',href):continue
                    self.check('local link '+str(path.relative_to(REPO))+' -> '+href,(path.parent/href).exists())

    def finish(self):
        self.links()
        report=dict(passed=sum(r['passed'] for r in self.qa),total=len(self.qa),checks=self.qa,
            source_commit=self.source,rom_sha256=sha(self.rom),gallery_tool_sha256=TOOL_SHA)
        dump(self.out/'validation'/'publication-qa.json',report)
        files=[]
        for root in (self.out,self.release):
            for path in sorted(root.rglob('*')):
                if path.is_file() and path.name!='publication-manifest.json':
                    files.append(dict(file=str(path.relative_to(REPO)),bytes=path.stat().st_size,sha256=sha(path)))
        dump(self.out/'publication-manifest.json',dict(source_commit=self.source,
            baseline_source=self.reports['before']['source_commit'],rom_sha256=sha(self.rom),
            gallery_tool_sha256=TOOL_SHA,release=self.release_record,
            before_checks=[self.reports['before']['passed'],self.reports['before']['total']],
            after_checks=[self.reports['after']['passed'],self.reports['after']['total']],
            audit_checks=[self.audit['passed'],self.audit['total']] if self.audit else None,
            publication_checks=[report['passed'],report['total']],files=files,
            self_manifest_excluded=True))
        print(json.dumps(dict(gallery=str(self.out),release=str(self.release),source=self.source,
                              publication_checks=[report['passed'],report['total']],files=len(files))))

    def run(self):
        self.reports()
        self.validation()
        self.boards()
        self.sources()
        self.release_files()
        self.readme()
        self.finish()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',required=True)
    parser.add_argument('--after',required=True)
    parser.add_argument('--bundle',required=True)
    parser.add_argument('--items',required=True)
    parser.add_argument('--audit')
    parser.add_argument('--out',default=str(REPO/'art-review'/'hud-gilt'))
    parser.add_argument('--branch',default='hud-gilt-polish')
    Gallery(parser.parse_args()).run()


if __name__=='__main__':
    main()
