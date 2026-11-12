"""Read-only observation and input support for a frozen regional ROM.

Offsets are compiled by the ARM compiler from the bundle's pinned source
headers. They are not hand-maintained guesses about the live game ABI. This
module never writes gameplay state, inventory, completion, terrain or pixels.
Only boot's deterministic title seed is an optional explicit memory fixture.
"""
import hashlib
import inspect
import io
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tarfile

import probe as P


GAME = Path(__file__).resolve().parent.parent
REPO = GAME.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


ABI = {
    'game_size': 'sizeof(GameState)',
    'game_state': 'offsetof(GameState,state)',
    'game_area': 'offsetof(GameState,area)',
    'game_cell': 'offsetof(GameState,cell)',
    'game_seed': 'offsetof(GameState,seed)',
    'player_size': 'sizeof(PlayerState)',
    'player_hp': 'offsetof(PlayerState,hp)',
    'player_hp_max': 'offsetof(PlayerState,hp_max)',
    'player_gilt': 'offsetof(PlayerState,gilt)',
    'player_items': 'offsetof(PlayerState,items)',
    'player_items2': 'offsetof(PlayerState,items2)',
    'player_equip': 'offsetof(PlayerState,equip)',
    'player_carry': 'offsetof(PlayerState,carry)',
    'player_bombs': 'offsetof(PlayerState,bombs)',
    'handoff_size': 'sizeof(HandoffState)',
    'handoff_draft_round': 'offsetof(HandoffState,draft_round)',
    'handoff_draft_state': 'offsetof(HandoffState,draft_state)',
    'handoff_draft': 'offsetof(HandoffState,draft)',
    'handoff_entitlement': 'offsetof(HandoffState,entitlement_mode)',
    'handoff_inn_reward': 'offsetof(HandoffState,inn_reward)',
    'handoff_contract_step': 'offsetof(HandoffState,contract_step)',
    'handoff_contract_kind': 'offsetof(HandoffState,contract_kind)',
    'handoff_contract_state': 'offsetof(HandoffState,contract_state)',
    'handoff_contract_target': 'offsetof(HandoffState,contract_target)',
    'handoff_completed': 'offsetof(HandoffState,completed)',
    'handoff_won': 'offsetof(HandoffState,won)',
    'handoff_wave': 'offsetof(HandoffState,wave)',
    'handoff_remaining': 'offsetof(HandoffState,remaining)',
    'handoff_quest': 'offsetof(HandoffState,quest)',
    'quest_size': 'sizeof(HandoffQuest)',
    'quest_kind': 'offsetof(HandoffQuest,kind)',
    'quest_state': 'offsetof(HandoffQuest,state)',
    'quest_origin_area': 'offsetof(HandoffQuest,origin_area)',
    'quest_origin_cell': 'offsetof(HandoffQuest,origin_cell)',
    'quest_target_area': 'offsetof(HandoffQuest,target_area)',
    'quest_target_cell': 'offsetof(HandoffQuest,target_cell)',
    'quest_progress': 'offsetof(HandoffQuest,progress)',
    'quest_quota': 'offsetof(HandoffQuest,quota)',
    'quest_timer': 'offsetof(HandoffQuest,timer)',
    'quest_receiver_x': 'offsetof(HandoffQuest,receiver_x)',
    'quest_receiver_y': 'offsetof(HandoffQuest,receiver_y)',
    'spots_size': 'sizeof(RegionalContentSpots)',
    'spots_door': 'offsetof(RegionalContentSpots,door)',
    'spots_npc': 'offsetof(RegionalContentSpots,npc)',
    'spots_cache': 'offsetof(RegionalContentSpots,cache)',
    'spots_mechanism': 'offsetof(RegionalContentSpots,mechanism)',
    'spots_has_door': 'offsetof(RegionalContentSpots,has_door)',
    'spots_has_npc': 'offsetof(RegionalContentSpots,has_npc)',
    'spots_has_cache': 'offsetof(RegionalContentSpots,has_cache)',
    'spots_has_mechanism': 'offsetof(RegionalContentSpots,has_mechanism)',
    'spots_terrace': 'offsetof(RegionalContentSpots,terrace)',
    'discovery_size': 'sizeof(RegionalContentDiscovery)',
    'discovery_marks': 'offsetof(RegionalContentDiscovery,marks)',
    'inventory_size': 'sizeof(LegacyInventory)',
    'inventory_owned': 'offsetof(LegacyInventory,owned)',
    'inventory_skills': 'offsetof(LegacyInventory,skills)',
    'room_w': 'offsetof(Room,w)',
    'room_h': 'offsetof(Room,h)',
    'room_ground': 'offsetof(Room,ground)',
    'room_overlay': 'offsetof(Room,overlay)',
    'room_solid': 'offsetof(Room,solid)',
    'world_entry': 'offsetof(World,entry)',
    'world_goal': 'offsetof(World,goal)',
    'world_cells': 'offsetof(World,cells)',
    'cell_size': 'sizeof(Cell)',
    'cell_gate': 'offsetof(Cell,gate)',
    'cell_opened': 'offsetof(Cell,opened)',
    'cell_flags': 'offsetof(Cell,flags)',
    'cream_entry': 'offsetof(CreamWorld,entry_node)',
    'cream_goal': 'offsetof(CreamWorld,goal_node)',
    'cream_degree': 'offsetof(CreamWorld,degree)',
    'cream_edges': 'offsetof(CreamWorld,edges)',
    'cream_edge_size': 'sizeof(CreamEdge)',
    'cream_rewards': 'offsetof(CreamProgress,rewards)',
    'enum_draft_running': 'HDRAFT_RUNNING',
    'enum_draft_done': 'HDRAFT_DONE',
    'enum_play': 'GS_PLAY',
    'enum_transition': 'GS_TRANSITION',
    'enum_sewer': 'AREA_SEWER',
    'enum_forest': 'AREA_FOREST',
    'enum_cream': 'AREA_CREAM',
    'enum_handoff': 'AREA_HANDOFF',
    'enum_regional_field_base': 'RC_FIELD_BASE',
    'enum_regional_interior_base': 'RC_INTERIOR_BASE',
    'gear_marker_size': 'sizeof(GearMapMarker)',
    'gear_marker_tile_x': 'offsetof(GearMapMarker,tile_x)',
    'gear_marker_tile_y': 'offsetof(GearMapMarker,tile_y)',
    'gear_marker_ch': 'offsetof(GearMapMarker,ch)',
    'gear_marker_source_x': 'offsetof(GearMapMarker,source_x)',
    'gear_marker_source_y': 'offsetof(GearMapMarker,source_y)',
    'gear_marker_x': 'offsetof(GearMapMarker,x)',
    'gear_marker_y': 'offsetof(GearMapMarker,y)',
    'menu_marker_size': 'sizeof(MenuMapMarker)',
    'menu_marker_cell': 'offsetof(MenuMapMarker,cell)',
    'menu_marker_kind': 'offsetof(MenuMapMarker,kind)',
    'menu_marker_tile_x': 'offsetof(MenuMapMarker,tile_x)',
    'menu_marker_tile_y': 'offsetof(MenuMapMarker,tile_y)',
    'menu_marker_source_x': 'offsetof(MenuMapMarker,source_x)',
    'menu_marker_source_y': 'offsetof(MenuMapMarker,source_y)',
    'menu_marker_x': 'offsetof(MenuMapMarker,x)',
    'menu_marker_y': 'offsetof(MenuMapMarker,y)',
    'handoff_menu_active': 'offsetof(QaHandoffMenu,active)',
    'handoff_menu_cursor': 'offsetof(QaHandoffMenu,cursor)',
    'enum_menu_shop': 'HM_SHOP',
    'enum_menu_inn': 'HM_INN',
    'enum_menu_fuse': 'HM_FUSE',
    'enum_menu_hint': 'HM_HINT',
    'enum_menu_trophy': 'HM_TROPHY',
    'enum_menu_contract': 'HM_CONTRACT',
    'hub_ladder_x': 'HUB_CREAM_LADDER_X',
    'hub_ladder_foot': 'HUB_CREAM_LADDER_FOOT',
    'hub_ladder_return': 'HUB_CREAM_RETURN_Y',
    'obj_tile_end': 'OBJ_TILE_SHEETS_END',
}


def compile_abi(bundle, out):
    """Compile constants from exact frozen source; do not build the game."""
    bundle, out = Path(bundle), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    commit = (bundle / 'source-commit.txt').read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('bundle needs an exact full source commit')
    tree = out / 'headers'
    tree.mkdir(exist_ok=True)
    data = subprocess.check_output(['git', 'archive', commit, 'bartgame/src'], cwd=REPO)
    hashes = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive:
            if not member.isfile() or not member.name.endswith('.h'):
                continue
            rel = Path(member.name).relative_to('bartgame/src')
            if '..' in rel.parts:
                raise ValueError(member.name)
            path = tree / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.extractfile(member).read())
            hashes[member.name] = sha(path)
    shutil.copy2(bundle / 'assets.h', tree / 'assets.h')
    events=subprocess.check_output(['git','show',commit+':bartgame/src/handoff_events.c'],cwd=REPO,text=True)
    menu=re.search(r'static\s+struct\s*\{([^{}]*)\}\s*m\b',events,re.S)
    modes=re.search(r'enum\s*\{[^{}]*\bHM_NONE\b[^{}]*\}\s*;',events,re.S)
    if not menu or not modes:
        raise RuntimeError('frozen handoff menu declaration not found')
    unit = out / 'abi.c'
    includes = ['stddef.h', 'game.h', 'player.h', 'handoff_events.h',
                'regional_content.h', 'legacy_items.h', 'room.h', 'world.h',
                'cream_world.h', 'cream_runtime.h', 'gear_menu.h','menu_studies.h','hub_services.h']
    source = ''.join('#include <stddef.h>\n' if n == 'stddef.h' else '#include "' + n + '"\n'
                     for n in includes)
    source += 'typedef struct {'+menu.group(1)+'} QaHandoffMenu;\n'
    source += modes.group(0)+'\n'
    source += '__attribute__((used,section(".rodata.qa_abi")))\nconst unsigned qa_abi[]={\n'
    source += ',\n'.join('    ' + expression for expression in ABI.values())
    source += '\n};\n'
    unit.write_text(source)
    obj, raw = out / 'abi.o', out / 'abi.bin'
    command = ['arm-none-eabi-gcc', '-mcpu=arm7tdmi', '-mthumb', '-std=c99',
               '-DBART_FOREST_VARIANT=32', '-I', str(tree), '-c', str(unit), '-o', str(obj)]
    result = subprocess.run(command, capture_output=True, text=True)
    (out / 'compile.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.rodata.qa_abi',
                    str(obj), str(raw)], check=True)
    values = struct.unpack('<' + 'I' * len(ABI), raw.read_bytes())
    answer = dict(zip(ABI, values))
    provenance = dict(source_commit=commit, header_sha256=hashes,
                      handoff_source_sha256=hashlib.sha256(events.encode()).hexdigest(),
                      generated_assets_sha256=sha(tree/'assets.h'),
                      source_sha256=sha(unit), command=command, offsets=answer)
    (out / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return answer


class NativeRun:
    """Private mGBA instance with logged real input and read-only snapshots."""
    def __init__(self, bundle, out):
        self.bundle, self.out = Path(bundle).resolve(), Path(out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        # Keep the exact test sources beside raw observations. Their hashes
        # remain reviewable even if another candidate needs a later tool fix.
        harness=self.out/'harness-source';harness.mkdir(exist_ok=True)
        self.harness_sha256={}
        candidates={Path(__file__).resolve(),Path(sys.argv[0]).resolve()}
        for module in list(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path and Path(path).resolve().parent==GAME/'tools':candidates.add(Path(path).resolve())
        for path in sorted(candidates):
            if path.is_file() and path.suffix=='.py':
                shutil.copy2(path,harness/path.name);self.harness_sha256[path.name]=sha(path)
        self.abi = compile_abi(self.bundle, self.out / 'abi')
        self.private = self.out / 'private'
        self.private.mkdir(exist_ok=True)
        # These are this harness's private emulator files, never a player's
        # save path. A repeated review starts the same explicitly fresh case.
        for saved in self.private.glob('bartgame*.sav*'):
            saved.unlink()
        self.rom = self.private / 'bartgame.gba'
        shutil.copy2(self.bundle / 'bartgame.gba', self.rom)
        P.MAP = str(self.bundle / 'bartgame.map')
        P._syms = None
        self.inputs, self.fixtures, self.frames = [], [], 0
        self.c = None
        self.sections={}
        lines=(self.bundle/'bartgame.map').read_text().splitlines()
        for i,line in enumerate(lines):
            words=line.split()
            if words and words[0].startswith('.'):
                rest=words[1:] if len(words)>1 else (lines[i+1].split() if i+1<len(lines) else [])
                if rest and rest[0].startswith('0x'):
                    self.sections[words[0]]=int(rest[0],16)

    def u8(self, name, field=0):
        return P.r8(self.c, P.sym(name) + field)

    def u16(self, name, field=0):
        return P.r16(self.c, P.sym(name) + field)

    def start(self, seed=0xb4a7):
        options=dict(rom=str(self.rom),start=False)
        if 'finish_draft' in inspect.signature(P.boot).parameters:
            options['finish_draft']=False
        self.c = P.boot(**options)
        self.frames = 30
        if seed is not None:
            address = P.sym('gSeedOverride')
            P.w16(self.c, address, seed & 65535)
            P.w16(self.c, address+2, seed >> 16)
            self.fixtures.append(dict(kind='title seed', value=seed))
        self.keys('START', 2)
        for _ in range(1600):
            if self.u8('gGame', self.abi['game_state']) != 0:
                return self.snapshot()
            self.keys([], 1)
        raise RuntimeError('new run did not leave title')

    def keys(self, keys, count=1, record=False):
        if isinstance(keys, str):
            keys = [keys]
        ks = [P.key(self.c, name) for name in keys]
        self.inputs.append(dict(keys=list(keys), frames=count, initial=self.snapshot()))
        self.c.set_keys(*ks)
        pictures = []
        for index in range(count):
            self.c.run_frame()
            self.frames += 1
            if record and index % 4 == 0:
                pictures.append(self.c.bg_video.to_pil().convert('RGB').copy())
        self.c.clear_keys(*ks)
        self.inputs[-1]['final'] = self.snapshot()
        return pictures

    def tap(self, key, release=8):
        self.keys(key, 2)
        self.keys([], release)

    def snapshot(self):
        if self.c is None:
            return None
        a, g, h, q = self.abi, P.sym('gGame'), P.sym('gHandoffState'), P.sym('gHandoffState') + self.abi['handoff_quest']
        spots = P.sym('gRegionalSpots')
        def byte(address):return P.r8(self.c, address)
        def point(name):
            address=spots+a['spots_'+name]
            return [byte(address), byte(address+1)]
        starting=P._syms.get('gStartingDraft')
        inventory=P.sym('gLegacyInventory')
        menu=self.sections['.ewram_bss.handoff_menu']
        return dict(physical_frames=self.frames, state=byte(g+a['game_state']),
                    area=byte(g+a['game_area']), cell=byte(g+a['game_cell']),
                    actor=P.actor(self.c,0), text=self.u8('gTbActive'),
                    health=[self.u16('gPl',a['player_hp']),self.u16('gPl',a['player_hp_max'])],
                    gilt=self.u16('gPl',a['player_gilt']),
                    bombs=self.u8('gPl',a['player_bombs']),
                    entitlement=self.u8('gHandoffState',a['handoff_entitlement']),
                    inn_reward=self.u16('gHandoffState',a['handoff_inn_reward']),
                    inventory=dict(owned=[P.r32(self.c,inventory+a['inventory_owned']+i*4) for i in range(4)],
                                   skills=P.r16(self.c,inventory+a['inventory_skills'])),
                    starting_draft=None if starting is None else byte(starting),
                    service_menu=dict(active=byte(menu+a['handoff_menu_active']),cursor=byte(menu+a['handoff_menu_cursor'])),
                    draft=dict(round=byte(h+a['handoff_draft_round']),
                               state=byte(h+a['handoff_draft_state']),
                               options=[P.r16(self.c,h+a['handoff_draft']+i*2) for i in range(3)]),
                    chain={key:byte(h+a['handoff_contract_'+key]) for key in ['step','kind','state','target']},
                    quest={key:byte(q+a['quest_'+key]) for key in ['kind','state','origin_area','origin_cell','target_area','target_cell','progress','quota']},
                    spots=dict(door=point('door'),npc=point('npc'),cache=point('cache'),
                               mechanism=point('mechanism'),
                               flags={key:byte(spots+a['spots_has_'+key]) for key in ['door','npc','cache','mechanism']},
                               terrace=byte(spots+a['spots_terrace'])))

    def dismiss(self, limit=80):
        for _ in range(limit):
            if not self.u8('gTbActive'):
                return True
            self.tap('A', 8)
        return not self.u8('gTbActive')

    def settle(self, area=None, limit=1400):
        for _ in range(limit):
            view=self.snapshot()
            if view['state']==self.abi['enum_play'] and (area is None or view['area']==area):
                return view
            self.keys([],1)
        raise RuntimeError('transition did not settle: '+str(self.snapshot()))

    def image(self, name):
        P.snap(self.c, str(self.out/(name+'.png')))

    def resources(self):
        """Read native allocator/OAM observations, never repair missing art."""
        failures=P._syms.get('gSpriteAllocFailures')
        next_tile=self.sections.get('.bss.sNextTile')
        world=[]
        for i in range(128):
            a0=P.r16(self.c,0x07000000+i*8)&65535
            a1=P.r16(self.c,0x07000002+i*8)&65535
            a2=P.r16(self.c,0x07000004+i*8)&65535
            if (a0&0x0300)==0x0200 or (a0>>10)&3==2:
                continue
            tile=a2&1023
            if tile>=self.abi['obj_tile_end']:
                continue
            x=a1&511;y=a0&255
            if x>=256:x-=512
            if y>=160:y-=256
            world.append(dict(i=i,x=x,y=y,tile=tile,priority=(a2>>10)&3,
                              palette=a2>>12,shape=a0>>14,size=a1>>14))
        return dict(alloc_failures=None if failures is None else P.r16(self.c,failures),
                    next_tile=None if next_tile is None else P.r16(self.c,next_tile),
                    world_tile_limit=self.abi['obj_tile_end'],
                    oam_count=self.u16('gOamCount'),world_oam=world)

    def finish_draft(self, choices=(0,1,2)):
        """Choose by actual input; do not assign draft or inventory state."""
        selected=[]
        for _ in range(200):
            self.dismiss()
            view=self.snapshot()
            state, round_=view['draft']['state'],view['draft']['round']
            if state==self.abi['enum_draft_done']:
                return selected
            if state!=self.abi['enum_draft_running']:
                self.keys([],2)
                continue
            if round_>=len(choices):
                raise RuntimeError('unexpected fourth draft round')
            option=choices[round_]
            selected.append(dict(round=round_, index=option,
                                 item=view['draft']['options'][option], before=view))
            self.image('draft-round-'+str(round_))
            for _ in range(option):self.tap('DOWN',4)
            self.tap('A',6)
            self.dismiss()
            self.keys([],2)
            selected[-1]['after']=self.snapshot()
            if self.snapshot()['draft']['round']==round_:
                raise RuntimeError('draft selection did not advance')
        raise RuntimeError('opening draft did not finish')

    def report_identity(self):
        return dict(source_commit=(self.bundle/'source-commit.txt').read_text().strip(),
                    rom_sha256=sha(self.rom), support_sha256=sha(__file__),
                    emulator='mGBA0.10.5', fixtures=self.fixtures,
                    harness_source_sha256=self.harness_sha256,
                    input_method='Actual key input; no gameplay-state or video assignments.')
