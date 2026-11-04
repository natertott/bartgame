#!/usr/bin/env python3
"""Actual mGBA integration checks for cohesive procedural forest profile32.

Navigation and inventory fixtures are explicit. Controls still operate the
real menu, forest entrance, required trials and item gates. This is a focused
runtime check, not a claim to have played a run without developer positioning.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import traceback

import probe as P
import bloom_probe as B
import critical_path as C
from sewer_concept_audit import NativeRom

SHA = lambda data: hashlib.sha256(data).hexdigest()


def read(core, address, count):
    return bytes(P.r8(core, address+i) for i in range(count))


class Runtime:
    def __init__(self, args):
        self.args = args
        self.bundle = Path(args.bundle).resolve()
        self.out = Path(args.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.rom = NativeRom(self.bundle)
        self.rows = []
        self.media = []
        self.snapshots = []
        self.fixtures = [
            'Pinned run seed via gSeedOverride before normal title Start.',
            'Forest ladder approach uses developer positioning, then real Up input.',
            'Enemy removal isolates menu and gate geometry; it does not test combat pressure.',
            'Room-switch checks use the game transition request, not tile or framebuffer injection.',
            'Critical-path helper positions Bloom between rooms and before trial enemies, heals him, and equips owned items; trial completion and item rewards are earned through actual game logic.',
            'The combat fixture chooses an enemy with an existing safe approach before a blocked first actor; it never changes enemy HP, event flags or rewards.',
        ]
        self.boot_original = P.boot
        P.MAP = str(self.bundle/'bartgame.map')
        P._syms = None
        P.boot = lambda **kw: self.boot_original(rom=str(self.bundle/'bartgame.gba'), **kw)
        C.mt = lambda name: self.rom.defs['MT_'+name]
        P.hall_exit = self.hall_exit
        self.check('forest cohesion profile32 is loaded', self.rom.defs['BART_FOREST_VARIANT'] == 32)

    def check(self, name, passed, detail=None):
        self.rows.append(dict(name=name, passed=bool(passed), **({'detail':detail} if detail is not None else {})))
        print(('PASS ' if passed else 'FAIL ')+name, flush=True)

    def shot(self, core, name):
        path = self.out/(name+'.png')
        P.snap(core, str(path))
        self.media.append(dict(file=path.name, sha256=SHA(path.read_bytes()), native_size=[240,160], kind='untouched mGBA framebuffer'))

    def wait(self, core, pred, maximum=1200):
        for _ in range(maximum):
            if pred():
                return True
            P.run(core, 1)
        return False

    def hall_exit(self, core):
        _, _, grid = C.room_tiles(core)
        for point, mt in grid.items():
            if mt != 65535 and P.r8(core, P.sym('metatile_type')+mt) == self.rom.defs['TT_EXIT']:
                return point
        raise AssertionError('Drain entrance tile absent')

    def registers(self, core):
        return {'display':P.r16(core,0x04000000)&65535,
                'bg1':P.r16(core,0x0400000A)&65535,
                'bg2':P.r16(core,0x0400000C)&65535,
                'bg3':P.r16(core,0x0400000E)&65535}

    def static_atlas(self, core, area='forest'):
        ts = self.rom.tileset(area)
        data = bytearray(read(core, 0x06000000, ts['tile_count']*32))
        # Animation is allowed to advance. The test compares every other
        # resident byte, including the exact static approved tree atlas.
        for animation in ts['animations']:
            start = animation['base']*32
            data[start:start+128] = bytes(128)
        return SHA(data)

    def world_snapshot(self, core, label):
        roots = P.sym('gForestTreeRoots')
        count = P.r16(core, P.sym('gForestTreeStats')+2)&65535
        values = {
            'bg1':SHA(read(core,0x0600C000,8192)),
            'bg2':SHA(read(core,0x0600E000,8192)),
            'bg3':SHA(read(core,0x06006000,8192)),
            'static_atlas':self.static_atlas(core),
            'collision':SHA(read(core,P.sym('gRoom')+4098,4096)),
            'root_owners':SHA(read(core,roots,2048)),
            'placements':SHA(read(core,P.sym('gForestTrees'),count*8)),
            'tree_palette':SHA(read(core,0x05000000+self.rom.defs['FOREST_TREE_PALETTE_SLOT']*32,32)),
            'motif_metadata':SHA(read(core,P.sym('gForestCohesionInfo'),32)),
        }
        row = dict(label=label, values=values, count=count, registers=self.registers(core),
                   motif=list(struct.unpack('<16H',read(core,P.sym('gForestCohesionInfo'),32))),
                   area=C.area(core), cell=C.cell(core), frame=P.r32(core,P.sym('gFrame')))
        self.snapshots.append(row)
        return row

    def assert_world_layers(self, core, name):
        regs = self.registers(core)
        self.check(name+' uses all three world layers', regs['display']&0x0E00 == 0x0E00, regs)
        self.check(name+' reserves BG3screen12 charbase0 size64',
                   ((regs['bg3']>>8)&31)==12 and ((regs['bg3']>>2)&3)==0 and ((regs['bg3']>>14)&3)==3, regs)
        self.check(name+' keeps floor behind tree bases', regs['bg2']&3 > regs['bg3']&3 and regs['bg3']&3 > regs['bg1']&3, regs)

    def assert_nonforest(self, core, name):
        regs = self.registers(core)
        self.check(name+' does not enable forest BG3 roots', not(regs['display']&0x0800), regs)
        self.check(name+' restores the ordinary menu BG3screen22', ((regs['bg3']>>8)&31)==22 and ((regs['bg3']>>14)&3)==0, regs)

    def warp(self, core, area, cell, side=0):
        C.dismiss(core)
        for name, value in (('sNextArea',area),('sNextCell',cell),('sNextSide',side),('sTransPhase',0)):
            P.w8(core,B.static_symbol(name),value)
        P.w8(core,P.sym('gGame'),2)
        self.check('transition request settles in area%d cell%d'%(area,cell),
                   self.wait(core,lambda:C.gstate(core)==1 and C.area(core)==area and (area==0 or C.cell(core)==cell)))
        C.dismiss(core)
        P.run(core,8)

    def title(self):
        core = P.boot(start=False)
        self.check('ordinary boot reaches native title bitmap', C.gstate(core)==0 and self.registers(core)['display']&7==3)
        self.shot(core,'01-title')
        P.press(core,'DOWN',2,6)
        P.press(core,'A',2,40)
        self.check('title Options opens through real input', P.r8(core,P.sym('gTitleOptions'))!=0)
        self.shot(core,'02-title-options')
        P.press(core,'RIGHT',2,8)
        P.press(core,'DOWN',2,8)
        P.press(core,'RIGHT',2,8)
        P.press(core,'B',2,20)
        self.check('Options returns to title without forest layer',
                   P.r8(core,P.sym('gTitleOptions'))==0 and self.registers(core)['display']&7==3 and not(self.registers(core)['display']&0x0800))

    def menus_and_switches(self):
        core = P.boot(seed=self.args.seed)
        C.dismiss(core)
        self.check('normal Start begins in the Drain', C.gstate(core)==1 and C.area(core)==0)
        self.assert_nonforest(core,'Drain boot')
        self.shot(core,'03-drain')
        self.world = C.world(core)
        P.enter_forest(core)
        C.dismiss(core)
        C.clear_enemies(core)
        self.check('real ladder input enters generated entry room', C.area(core)==1 and C.cell(core)==self.world['entry'])
        self.assert_world_layers(core,'entry forest')
        self.shot(core,'04-forest-before-menu')
        before = self.world_snapshot(core,'before menu')
        P.press(core,'START',2,90)
        self.check('Start opens item page', C.gstate(core)==4 and P.r8(core,P.sym('gMenuStudyPage'))==0)
        regs = self.registers(core)
        self.check('item menu owns BG3screen22 size32 charbase0', ((regs['bg3']>>8)&31)==22 and ((regs['bg3']>>14)&3)==0 and ((regs['bg3']>>2)&3)==0, regs)
        self.shot(core,'05-items')
        P.press(core,'R',2,65)
        self.check('R opens key-item page', P.r8(core,P.sym('gMenuStudyPage'))==1)
        self.shot(core,'06-key-items')
        P.press(core,'R',2,100)
        self.check('R opens region map', P.r8(core,P.sym('gMenuStudyPage'))==2)
        self.shot(core,'07-region-map')
        P.press(core,'A',2,100)
        self.check('A opens room zoom map', P.r8(core,P.sym('gMenuStudyZoom'))==1)
        self.shot(core,'08-room-map')
        P.press(core,'B',2,100)
        self.check('B returns to overview map', P.r8(core,P.sym('gMenuStudyZoom'))==0)
        P.press(core,'START',2,50)
        self.check('Start returns to normal world', C.gstate(core)==1)
        C.clear_enemies(core)
        after = self.world_snapshot(core,'after item/key/map/zoom menu')
        self.assert_world_layers(core,'returned forest')
        for field, value in before['values'].items():
            self.check('menu restores exact '+field, after['values'][field]==value,
                       {'before':value,'after':after['values'][field]})
        self.shot(core,'09-forest-after-menu')
        self.cut_cache(core)
        # Select an existing generated mystery rather than forcing a new event.
        import myst_probe as M
        candidates = [i for i in range(25) if P.r8(core,P.sym('gWorld')+M.MYST_OFF+i)]
        target = candidates[0]
        side = next(i for i,g in enumerate(self.world['cells'][target]['gate']) if g)
        self.warp(core,1,target,side)
        self.check('existing mystery mouth enters its generated interior', C.enter_trial(core))
        self.assert_nonforest(core,'mystery interior')
        self.shot(core,'10-mystery-interior')
        # Some trials close their normal exit during the challenge. Returning
        # via the existing transition request isolates graphics handoff.
        self.warp(core,1,target,side)
        self.assert_world_layers(core,'forest after mystery')
        self.shot(core,'11-forest-after-mystery')
        self.warp(core,0,0,0)
        self.assert_nonforest(core,'Drain return')
        self.shot(core,'12-drain-return')
        P.enter_forest(core)
        self.assert_world_layers(core,'forest re-entry')
        self.shot(core,'13-forest-reentry')

    def cut_cache(self, core):
        """Cut a real generated bush, then test the same live-room cache."""
        def clear_feet(x,y):
            w,h=P.r8(core,P.sym('gRoom')),P.r8(core,P.sym('gRoom')+1)
            if not (6<=x<w*16-6 and 8<=y<h*16):return False
            return not any(P.r8(core,P.sym('gRoom')+4098+(yy//8)*64+xx//8)
                           for yy in range(y-8,y) for xx in range(x-5,x+5))
        candidates=[]
        search=[C.cell(core)]+[cell for cell in range(25) if cell!=C.cell(core)]
        for cell in search:
            if cell!=C.cell(core):
                side=next(i for i,g in enumerate(self.world['cells'][cell]['gate']) if g)
                self.warp(core,1,cell,side)
            C.clear_enemies(core)
            _,_,grid=C.room_tiles(core)
            roots=read(core,P.sym('gForestTreeRoots'),2048)
            for (tx,ty),mt in grid.items():
                if mt!=self.rom.defs['MT_BUSH']:continue
                # Facing is established with real directional input. Each
                # standing position uses Bloom's actual10x8 feet footprint.
                choices=((tx*16+8,(ty+1)*16+12,'UP'),
                         ((tx-1)*16+8,ty*16+12,'RIGHT'),
                         ((tx+1)*16+8,ty*16+12,'LEFT'),
                         (tx*16+8,(ty-1)*16+14,'DOWN'))
                near=any(struct.unpack_from('<H',roots,(yy*32+xx)*2)[0]
                         for yy in range(max(0,ty-2),min(24,ty+3))
                         for xx in range(max(0,tx-2),min(32,tx+3)))
                for x,y,key in choices:
                    if clear_feet(x,y):candidates.append((not near,tx,ty,x,y,key))
            if candidates:break
        self.check('generated room contains a safely approachable cuttable bush',bool(candidates))
        if not candidates:return
        _,tx,ty,x,y,key=min(candidates)
        before=self.world_snapshot(core,'before ordinary sword bush cut')
        def collision_cell():
            at=P.sym('gRoom')+4098+(ty*2)*64+tx*2
            return bytes(P.r8(core,at+dy*64+dx) for dy in range(2) for dx in range(2))
        previous_collision=collision_cell()
        C.teleport(core,x,y)
        P.hold(core,key,1)
        for _ in range(3):
            P.press(core,'B',2,24)
            _,_,grid=C.room_tiles(core)
            if grid[(tx,ty)]!=self.rom.defs['MT_BUSH']:break
        _,_,grid=C.room_tiles(core)
        self.check('ordinary sword input cuts the generated bush',grid[(tx,ty)]!=self.rom.defs['MT_BUSH'],
                   {'cell':C.cell(core),'tile':[tx,ty],'near_tree':not min(candidates)[0]})
        self.check('bush cut updates the real collision grid',any(previous_collision) and collision_cell()==bytes(4))
        cut=self.world_snapshot(core,'after sword cut before menu')
        for field in ('placements','root_owners','bg3'):
            self.check('room_change preserves planted tree '+field,before['values'][field]==cut['values'][field])
        self.shot(core,'14-bush-cut-before-menu')
        P.press(core,'START',2,90)
        self.check('post-cut item menu opens',C.gstate(core)==4)
        P.press(core,'START',2,50)
        self.check('post-cut item menu closes',C.gstate(core)==1)
        after=self.world_snapshot(core,'after sword cut and same-room menu redraw')
        for field in cut['values']:
            self.check('same-room cache restores cut-room '+field,cut['values'][field]==after['values'][field])
        _,_,grid=C.room_tiles(core)
        self.check('cut floor and open collision survive menu redraw',grid[(tx,ty)]!=self.rom.defs['MT_BUSH'] and collision_cell()==bytes(4))
        self.shot(core,'15-bush-cut-after-menu')

    def critical(self):
        original = C.check
        original_find = C.find_actor
        def attackable_actor(core, kind, typ=None):
            # The older probe always chose actor1, then waited if its three
            # approach spots were blocked by another monster. A reachable
            # add can remain elsewhere indefinitely. Choose a target with
            # one existing safe approach first; damage and event completion
            # still use the real sword and unmodified enemy HP.
            if kind==2 and typ is None:
                for index in range(1,96):
                    actor=P.actor(core,index)
                    if actor['kind']==kind and C.trial_attack_position(core,actor,0) is not None:
                        return actor
            return original_find(core,kind,typ)
        def check(name, passed, detail=''):
            original(name,passed,detail)
            self.check('critical path: '+name,passed,detail)
        C.check = check
        C.find_actor = attackable_actor
        C.res = []
        C.S = str(self.out)
        oldargv = sys.argv
        sys.argv = ['critical_path.py','--seed',hex(self.args.seed)]
        try:
            result = C.main()
            self.check('all actual required trials/item gates reach the Heart room',result==0 and bool(C.res) and all(C.res),
                       {'passed':sum(C.res),'total':len(C.res)})
        finally:
            C.check = original
            C.find_actor = original_find
            sys.argv = oldargv
        for path in sorted(self.out.glob('cp*.png')):
            self.media.append(dict(file=path.name,sha256=SHA(path.read_bytes()),native_size=[240,160],kind='untouched mGBA critical-path framebuffer'))

    def run(self):
        error = None
        try:
            self.title()
            self.menus_and_switches()
            if not self.args.skip_critical:
                self.critical()
        except Exception:
            error = traceback.format_exc()
            self.check('runtime harness completes',False,error)
        source = Path(__file__)
        report = dict(kind='actual mGBA runtime integration verification',
                      source_commit=json.loads((self.bundle/'freeze.json').read_text()).get('source_commit') if (self.bundle/'freeze.json').exists() else 'unfrozen pilot',
                      rom_sha256=SHA(self.rom.rom),tool_sha256=SHA(source.read_bytes()),seed=self.args.seed,
                      fixtures=self.fixtures,checks=self.rows,passed=sum(r['passed'] for r in self.rows),
                      total=len(self.rows),failures=[r for r in self.rows if not r['passed']],
                      snapshots=self.snapshots,media=self.media,error=error)
        (self.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('RESULT',report['passed'],'/',report['total'],flush=True)
        return 1 if report['failures'] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True)
    parser.add_argument('--out',required=True)
    parser.add_argument('--seed',type=lambda value:int(value,0),default=0xB4A7)
    parser.add_argument('--skip-critical',action='store_true')
    return Runtime(parser.parse_args()).run()


if __name__ == '__main__':
    raise SystemExit(main())
