#!/usr/bin/env python3
"""Capture new style remixes and ten menu layouts from actual mGBA runs.

Inventory/resources, seed, safe position, visited flags and navigation are
explicit fixtures. UI pixels, drawing canvases, menu focus, animation phases
and poses are never assigned. All presentation comes from real game controls.
"""
import argparse,json
from pathlib import Path
import probe as P
import bloom_probe as B
import critical_path as C
from drain_ui_review import Review as BaseReview,hud_payload,digest
from sewer_concept_audit import NativeRom

class Review(BaseReview):
    def __init__(self,args):
        super().__init__(args)
        self.menu=self.defs.get('BART_MENU_VARIANT',0)
        self.action_timings=[]
        self.navigation_graph={}
        self.check('valid menu layout',0<=self.menu<=10,self.menu)
    def check(self,name,condition,detail=None):
        if name=='valid UI profile':condition=0<=self.ui<=10
        super().check(name,condition,detail)
    def symbol8(self,name,default=-1):
        try:return P.r8(self.c,P.sym(name))
        except KeyError:return default
    def state(self):
        row=super().state()
        if self.menu:
            row['menu_page']=self.symbol8('gMenuStudyPage')
            row['menu_cursor']=self.symbol8('gMenuStudyCursor')
            row['map_cell']=self.symbol8('gMenuStudyMapCell')
            row['map_zoom']=self.symbol8('gMenuStudyZoom')
            row['menu_draw_frames']=P.r16(self.c,P.sym('gMenuStudyDrawFrames'))
        return row
    def save(self):
        super().save()
        p=self.out/'capture.json';row=json.loads(p.read_text());row['menu_variant']=getattr(self,'menu',self.defs.get('BART_MENU_VARIANT',0));row['ui_variant']=self.ui
        row['method']=__doc__.strip();row['kind']=self.args.kind;row['menu_action_timings']=getattr(self,'action_timings',[]);row['navigation_graph']=getattr(self,'navigation_graph',{})
        freeze_path=self.frozen/'freeze.json'
        if freeze_path.exists():row['source_commit']=json.loads(freeze_path.read_text()).get('source_commit')
        p.write_text(json.dumps(row,indent=2)+'\n')
    def page(self,number):
        for _ in range(4):
            before=self.symbol8('gMenuStudyPage')
            if before==number:return
            tick=P.r32(self.c,P.sym('gFrame'))
            P.press(self.c,'R',2,2)
            # A cold terrain atlas legitimately builds cached room previews.
            # Do not inject another R while its first transition is rendering.
            for wait in range(300):
                if self.symbol8('gMenuStudyPage')!=before:break
                P.run(self.c,1)
            self.action_timings.append({'action':'R page','from':before,'to':self.symbol8('gMenuStudyPage'),'video_frames':P.r32(self.c,P.sym('gFrame'))-tick})
        raise AssertionError('page cycle did not reach '+str(number))
    def seek(self,target):
        from collections import deque
        current=self.symbol8('gMenuStudyCursor');queue=deque([(current,[])])
        visited=set()
        while queue:
            node,path=queue.popleft()
            if node==target:
                for key in path:P.press(self.c,key,2,8)
                return self.symbol8('gMenuStudyCursor')==target
            if node in visited:continue
            visited.add(node)
            for key,other in self.navigation_graph.get(node,{}).items():
                if other not in visited:queue.append((other,path+[key]))
        return False
    def explore_navigation(self):
        directions=('RIGHT','DOWN','LEFT','UP')
        for _ in range(80):
            current=self.symbol8('gMenuStudyCursor')
            edges=self.navigation_graph.setdefault(current,{})
            key=next((k for k in directions if k not in edges),None)
            if key is None:
                frontier=next((n for n,e in self.navigation_graph.items() if len(e)<4),None)
                if frontier is None:break
                if not self.seek(frontier):break
                continue
            P.press(self.c,key,2,8);other=self.symbol8('gMenuStudyCursor')
            edges[key]=other;self.navigation_graph.setdefault(other,{})
        self.check('all seven owned tools reachable through actual D-pad navigation',set(self.navigation_graph)==set(range(7)),self.navigation_graph)
    def masks(self):
        try:return P.r32(self.c,B.static_symbol('sMaskDone'))
        except KeyError:return None
    def paused_integrity(self):
        c=self.c
        return {'world':digest(B.bytes_at(c,P.sym('gWorld'),668)),
                'room':digest(B.bytes_at(c,P.sym('gRoom'),10242)),
                'rng':P.r32(c,B.static_symbol('sRand'))}
    def restored_world_tiles(self):
        rom=NativeRom(self.frozen);ts=rom.tileset('forest');raw=B.bytes_at(self.c,0x06000000,ts['tile_count']*32)
        moving={tile for a in ts['animations'] for tile in range(a['base'],a['base']+4)}
        static_ok=all(raw[i*32:(i+1)*32]==ts['tiles'][i*32:(i+1)*32]
                      for i in range(ts['tile_count']) if i not in moving)
        anim_ok=all(raw[a['base']*32:(a['base']+4)*32] in
                    [a['data'][i*128:(i+1)*128] for i in range(a['frames'])]
                    for a in ts['animations'])
        self.check('closing menu restores every static world VRAM tile',static_ok)
        self.check('closing menu restores legal live animation allocations',anim_ok)
        self.check('closing menu restores every world BG palette bank',B.bytes_at(self.c,0x05000000,len(ts['palettes']))==ts['palettes'])
    def layout_suite(self):
        self.forest(0);self.inventory(True);pl=P.sym('gPl')
        P.press(self.c,'START',2,16)
        paused=self.paused_integrity()
        self.record('layout-items',40,note='Real Start opens the native study; full inventory is a fixture.',
            expect=lambda t:all(r['game_state']==4 and r['menu_page']==0 for r in t))
        cursor=self.symbol8('gMenuStudyCursor')
        direction='DOWN' if self.menu in (2,4,6) else 'RIGHT'
        self.record('layout-navigate',80,{i:[direction] for i in range(8,10)},
            'Ordinary D-pad moves focus in this layout, including its own spatial navigation.',
            expect=lambda t:any(r['menu_cursor']!=cursor for r in t),motion=True)
        selected=self.symbol8('gMenuStudyCursor');eq_order=(1,5,2,3,4,6,7)
        self.explore_navigation()
        for target,label in ((2,'seeds'),(5,'bow')):
            self.check('actual navigation reaches '+label,self.seek(target))
            self.record('layout-'+label,32,note='Actual navigation selects ammunition tool; inspect name, useful prose and exact count.',expect=lambda t:all(r['menu_cursor']==target for r in t))
        self.check('actual navigation restores initial inspected tool',self.seek(selected))
        expected_eq=eq_order[selected] if 0<=selected<len(eq_order) else None
        expected_slots=[P.r8(self.c,pl+9+i) for i in range(3)]
        for slot,key in enumerate(('A','B','L')):
            P.press(self.c,key,2,10)
            expected_slots=[0 if eq==expected_eq else eq for eq in expected_slots]
            expected_slots[slot]=expected_eq
            actual=[P.r8(self.c,pl+9+i) for i in range(3)]
            self.check('ordinary '+key+' moves focused item to its button',expected_eq is not None and actual==expected_slots,{'cursor':selected,'expected':expected_slots,'actual':actual})
        self.record('layout-assigned',32,note='A/B/L assign the selected tool through actual controls.',expect=lambda t:all(r['game_state']==4 for r in t))
        focus=selected
        self.page(1);self.record('layout-key-items',40,note='R cycles to key items.',expect=lambda t:all(r['menu_page']==1 for r in t))
        self.page(2);self.record('layout-map',48,note='Actual generated overview map with Map/Astrolabe ownership fixtures.',expect=lambda t:all(r['menu_page']==2 and not r['map_zoom'] for r in t))
        self.record('layout-map-navigate',64,{8:['RIGHT'],9:['RIGHT'],24:['DOWN'],25:['DOWN']},
            'Ordinary map-cursor movement, with current-room marker distinct from the inspected room.',motion=True)
        P.press(self.c,'A',2,20)
        self.record('layout-zoom-map',48,note='A toggles the actual known-room detail map.',expect=lambda t:all(r['map_zoom'] for r in t))
        P.press(self.c,'B',2,12)
        self.check('B returns from zoom to overview',self.symbol8('gMenuStudyZoom')==0)
        self.page(0)
        self.check('item focus survives page cycling',self.symbol8('gMenuStudyCursor')==focus,{'before':focus,'after':self.symbol8('gMenuStudyCursor')})
        self.record('layout-focus-return',32,note='R returns to the same selected tool; no selection fixture.',expect=lambda t:all(r['menu_page']==0 for r in t))
        self.check('menu/map navigation preserves world, room and gameplay RNG',self.paused_integrity()==paused,{'before':paused,'after':self.paused_integrity()})
        P.press(self.c,'START',2,18)
        self.restored_world_tiles()
        self.record('layout-hud-return',48,note='Start closes the study and restores the live HUD with assigned equipment.',hud=True,expect=lambda t:all(r['game_state']==1 for r in t),motion=True)
        self.check('closing menu retains unique assigned tools',[P.r8(self.c,pl+9+i) for i in range(3)]==expected_slots)
        # Fresh emulator, no cached known maps from the full-inventory preview.
        world,cell=self.forest(0);pl=P.sym('gPl');P.w8(self.c,pl+8,0);P.w8(self.c,pl+36,0)
        for slot in range(3):P.w8(self.c,pl+9+slot,0)
        for i in range(25):P.w8(self.c,P.sym('gWorld')+4+i*13+11,1 if i==cell else 0)
        P.run(self.c,4);P.press(self.c,'START',2,16)
        self.record('layout-empty-items',40,note='Disclosed empty-inventory fixture checks absence and layout stability.',expect=lambda t:all(r['game_state']==4 for r in t))
        P.press(self.c,'A',2,8)
        self.check('empty tool cannot be equipped',P.r8(self.c,pl+9)==0)
        self.page(1);self.record('layout-empty-key-items',32,note='Empty key-item page has explicit absence rather than invented progress.')
        self.page(2);self.record('layout-fog-map',48,note='Only the current room is visited; no Map/Astrolabe. Unknown room geometry must stay hidden.')
        mask=self.masks();self.check('fog map does not fetch unknown-room geometry',mask is not None and not(mask&~(1<<cell)),{'current':cell,'mask_bits':mask})
        direction='RIGHT' if cell%5<4 else 'LEFT'
        P.press(self.c,direction,2,8)
        self.check('fog inspection selects a different room',self.symbol8('gMenuStudyMapCell')!=cell)
        P.press(self.c,'A',2,12)
        self.record('layout-fog-zoom',40,note='Inspecting a fogged neighbor cannot disclose its generated terrain.')
        mask=self.masks();self.check('unknown zoom retains terrain privacy',mask is not None and not(mask&~(1<<cell)),{'current':cell,'mask_bits':mask})
        P.press(self.c,'START',2,16)
        self.check('empty/fog flow returns to play',C.gstate(self.c)==1)

    def run(self):
        if self.args.kind=='layout':groups=('layout_suite',)
        elif self.args.kind=='baseline':groups=('hud','interfaces')
        else:groups=('hud','interfaces','events')
        for group in groups:getattr(self,group)()
        self.save();print('RESULT',sum(r['passed'] for r in self.checks),'/',len(self.checks),'captures',len(self.rows),flush=True)
        return int(any(not r['passed'] for r in self.checks))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frozen',required=True);p.add_argument('--out',required=True);p.add_argument('--kind',choices=('baseline','style','layout'),required=True);p.add_argument('--no-video',action='store_true');a=p.parse_args();return Review(a).run()
if __name__=='__main__':raise SystemExit(main())
