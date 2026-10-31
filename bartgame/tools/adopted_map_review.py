#!/usr/bin/env python3
"""Review the adopted Workbench/graph map using actual mGBA input.

Each reference position is harvested by loading the actual generated room.
Visited/inventory/completion state and safe transitions are disclosed fixtures.
No menu focus, zoom, canvas, marker report, animation pose or output pixel is
assigned. The immutable ROM must contain the current map diagnostics.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import probe as P
import bloom_probe as B
import critical_path as C
import lift_probe as L
import bloom_review as BR
from ui_layout_review import Review

COUNT=25
MARKS=417
MYST_FLAGS=392
YOU,DOOR,TASK,CHEST,HEAL,HEART,FOLK,RELIC,GATE=range(9)
MP_FOR={DOOR:0,TASK:1,CHEST:2,RELIC:3,HEAL:4,FOLK:1}


class MapReview(Review):
    def __init__(self,args):
        self.actual_layouts={};self.map_marker_samples=[];self.map_timings=[]
        super().__init__(args)
        self.check('adopted Workbench profile selected',self.menu==1)

    def save(self):
        super().save()
        path=self.out/'capture.json';data=json.loads(path.read_text())
        data['method']=__doc__.strip()
        data['actual_generated_reference_marks']=self.actual_layouts
        data['seed']='0xB4A7 all-room comparison, first naturally generated shrine seed recorded below, and seed11 fog'
        data['map_marker_samples']=self.map_marker_samples
        data['map_timings']=self.map_timings
        data['fixtures']='Seed, inventory/resources, enemy removal, safe transition/position, visited and completion flags only. Presentation is controlled by real buttons.'
        path.write_text(json.dumps(data,indent=2)+'\n')

    def wait_report(self,name,value,limit=1800):
        for _ in range(limit):
            if self.symbol8(name)==value:
                P.run(self.c,3);return
            P.run(self.c,1)
        raise AssertionError((name,value,self.symbol8(name)))

    def press_map(self,key,report=None,value=None):
        tick=P.r32(self.c,P.sym('gFrame'))
        P.press(self.c,key,2,2)
        if report:self.wait_report(report,value)
        else:P.run(self.c,6)
        self.map_timings.append({'key':key,'report':report,'value':value,'video_frames':P.r32(self.c,P.sym('gFrame'))-tick})

    def seek_cell(self,target):
        while self.symbol8('gMenuStudyMapCell')!=target:
            old=self.symbol8('gMenuStudyMapCell');x,y=old%5,old//5
            tx,ty=target%5,target//5
            if x<tx:key='RIGHT';value=old+1
            elif x>tx:key='LEFT';value=old-1
            elif y<ty:key='DOWN';value=old+5
            else:key='UP';value=old-5
            self.press_map(key,'gMenuStudyMapCell',value)

    def snapshot(self):
        return {name:hashlib.sha256(B.bytes_at(self.c,P.sym(name),size)).hexdigest()
                for name,size in [('gWorld',668),('gRoom',10242),('gSpots',58),('gPl',38)]}|{'rng':P.r32(self.c,B.static_symbol('sRand'))}

    def cell(self,n):
        at=P.sym('gWorld')+4+n*13
        return {'gates':[P.r8(self.c,at+i) for i in range(4)],'opened':P.r8(self.c,at+4),
                'role':P.r8(self.c,at+5),'flags':P.r8(self.c,at+11),
                'marks':list(B.bytes_at(self.c,P.sym('gWorld')+MARKS+n*10,10)),
                'myst_done':P.r8(self.c,P.sym('gWorld')+MYST_FLAGS+n)&1}

    def closed_sides(self,n):
        c=self.cell(n)
        return [i for i,g in enumerate(c['gates']) if 2<=g<=6 and not(c['opened']&(1<<i))]

    def relic_target(self):
        if P.r8(self.c,P.sym('gPl')+8)&16:return -1
        asked=any(self.cell(n)['role']==6 and self.cell(n)['flags']&64 and not(self.cell(n)['flags']&4) for n in range(25))
        return next((n for n in range(25) if self.cell(n)['role']==8 and not(self.cell(n)['flags']&16)),-1) if asked else -1

    def expected_events(self,n,include_you=False):
        c=self.cell(n);role,flags,m=c['role'],c['flags'],c['marks'];out=0
        astro=bool(P.r8(self.c,P.sym('gPl')+36)&8)
        if flags&1:
            if m[0] and not c['myst_done']:out|=1<<DOOR
            if m[2] and not(role in (5,6,7) and flags&4):out|=1<<(TASK if role in (5,6,7) else FOLK)
            if m[8] and not(flags&128):out|=1<<HEAL
        if astro:
            if role in (4,10) and not(flags&2):out|=1<<CHEST
            if n==C.world(self.c)['goal'] and not(flags&32):out|=1<<HEART
            if self.closed_sides(n):out|=1<<GATE
        if self.relic_target()==n:out|=1<<RELIC
        here=C.cell(self.c) if C.area(self.c)==1 else C.world(self.c)['entry']
        if include_you and n==here:out|=1<<YOU
        return out

    def check_overview(self,label):
        actual=[P.r16(self.c,P.sym('gMenuMapEvents')+2*n) for n in range(25)]
        expected=[self.expected_events(n,True) for n in range(25)]
        self.check(label+' all25 room content types match knowledge/completion',actual==expected,{'actual':actual,'expected':expected})
        # Ordinary role exclusivity permits at most three pending types plus
        # player. Four9px slots fit the chosen28x20 room interior.
        self.check(label+' all event/player glyphs fit separate card slots',max(v.bit_count() for v in actual)<=4,{'max_icons':max(v.bit_count() for v in actual)})

    def markers(self):
        count=self.symbol8('gMenuMapMarkerCount');out=[]
        for i in range(count):
            v=struct.unpack('<BBhhhhBB',B.bytes_at(self.c,P.sym('gMenuMapMarkers')+i*12,12))
            out.append(dict(zip(('cell','kind','x','y','source_x','source_y','tile_x','tile_y'),v)))
        return out

    def check_locations(self,n,reference,label):
        marks=self.markers();events=self.expected_events(n);expected=[]
        # The adopted160x112 chamber has square5px tiles, centered at13,35.
        for kind,mp in MP_FOR.items():
            if events&(1<<kind) and reference[mp*2]:
                tx,ty=reference[mp*2]-1,reference[mp*2+1]-1
                expected.append((kind,tx,ty,13+(tx-1)*5+2,35+(ty-2)*5+2))
        if events&(1<<HEART):
            px,py=272,192
            if C.area(self.c)==1 and C.cell(self.c)==n:
                boss=next((P.actor(self.c,i) for i in range(1,96) if P.actor(self.c,i)['kind']==2 and P.actor(self.c,i)['type']==5),None)
                if boss:px,py=boss['x'],boss['y']
            expected.append((HEART,px//16,py//16,13+(px-16)*5//16,35+(py-32)*5//16))
        if events&(1<<GATE):
            corners={0:(15,1,16,1),1:(31,11,31,12),2:(15,23,16,23),3:(0,11,0,12)}
            for side in self.closed_sides(n):
                x0,y0,x1,y1=corners[side]
                # int division truncates toward zero on the ARM target.
                sx=13+int((((x0+x1+1)*8-16)*5)/16)
                sy=35+int((((y0+y1+1)*8-32)*5)/16)
                expected.append((GATE,(x0+x1)//2,(y0+y1)//2,sx,sy))
        if C.area(self.c)==1 and C.cell(self.c)==n:
            px,py=P.player_pos(self.c)
            expected.append((YOU,px//16,py//16,13+(px-16)*5//16,35+(py-32)*5//16))
        actual=[(m['kind'],m['tile_x'],m['tile_y'],m['source_x'],m['source_y']) for m in marks]
        self.check(label+' every marker anchors to actual generated location',sorted(actual)==sorted(expected),{'actual':actual,'expected':expected})
        self.check(label+' marker bodies stay within chart',all(12<=m['x']<=162 and 37<=m['y']<=138 for m in marks),marks)
        self.check(label+' adjacent marker bodies do not overlap',all(abs(a['x']-b['x'])>=9 or abs(a['y']-b['y'])>=9 for i,a in enumerate(marks) for b in marks[i+1:]),marks)
        self.map_marker_samples.append({'label':label,'cell':n,'reference_actual_marks':reference,'markers':marks})

    def open_map(self):
        P.press(self.c,'START',2,12);self.wait_report('gMenuStudyPage',0);self.page(2)
        if getattr(self,'last_focus_core',None) is self.c:
            self.check('reopening map preserves inspected cell and zoom',(self.symbol8('gMenuStudyMapCell'),self.symbol8('gMenuStudyZoom'))==self.last_focus)
        if self.symbol8('gMenuStudyZoom'):self.press_map('B','gMenuStudyZoom',0)

    def check_menu_focus(self):
        cell=self.symbol8('gMenuStudyMapCell');self.page(0)
        self.press_map('RIGHT');item_focus=self.symbol8('gMenuStudyCursor')
        self.check('Workbench ordinary input changes selected tool',item_focus==1)
        expected=[P.r8(self.c,P.sym('gPl')+9+i) for i in range(3)]
        for slot,key in enumerate(('A','B','L')):
            self.press_map(key);expected=[0 if eq==5 else eq for eq in expected];expected[slot]=5
            self.check('Workbench '+key+' assigns selected shield uniquely',[P.r8(self.c,P.sym('gPl')+9+i) for i in range(3)]==expected)
        self.page(1);self.press_map('RIGHT');key_focus=self.symbol8('gMenuStudyCursor')
        before=B.bytes_at(self.c,P.sym('gPl')+9,3);self.press_map('A')
        self.check('Key Items A cannot replace equipment',B.bytes_at(self.c,P.sym('gPl')+9,3)==before)
        self.page(2);self.check('map location survives item/key page changes',self.symbol8('gMenuStudyMapCell')==cell)
        self.page(0);self.check('Workbench tool focus persists independently',self.symbol8('gMenuStudyCursor')==item_focus)
        self.page(1);self.check('key-item focus persists independently',self.symbol8('gMenuStudyCursor')==key_focus)
        self.page(2)

    def close_map(self):
        self.last_focus_core=self.c;self.last_focus=(self.symbol8('gMenuStudyMapCell'),self.symbol8('gMenuStudyZoom'))
        P.press(self.c,'START',2,18)
        self.check('Start closes adopted map',C.gstate(self.c)==1)
        self.restored_world_tiles()

    def suite(self):
        self.boot(seed=0xB4A7);self.inventory(True);world=C.world(self.c)
        P.enter_forest(self.c);C.dismiss(self.c)
        actual=[]
        for n,c in enumerate(world['cells']):
            P.w16(self.c,P.sym('gPl'),80)
            L.warp(self.c,n,next(i for i,g in enumerate(c['gate']) if g))
            C.dismiss(self.c);C.clear_enemies(self.c);actual.append(self.cell(n)['marks'])
        self.actual_layouts['0xB4A7']=actual
        # Activate the real relic-quest state to exercise its existing map rule.
        fetch=next(n for n,c in enumerate(world['cells']) if c['role']==6)
        P.w8(self.c,P.sym('gWorld')+4+fetch*13+11,self.cell(fetch)['flags']|64)
        P.w8(self.c,P.sym('gPl')+8,P.r8(self.c,P.sym('gPl')+8)&~16)
        entry=world['entry'];L.warp(self.c,entry,next(i for i,g in enumerate(world['cells'][entry]['gate']) if g));C.dismiss(self.c);C.clear_enemies(self.c)
        point=BR.natural_spot(self.c,0,0);assert point;self.focus(point)
        self.open_map();self.check_menu_focus();paused=self.snapshot();self.check_overview('full known')
        self.record('map-overview-all-known',24,note='All25 cells loaded normally; full inventory/active relic quest are review fixtures.')
        for n in range(25):
            self.seek_cell(n);self.press_map('A','gMenuStudyZoom',1)
            self.check_locations(n,actual[n],f'visited room{n:02}')
            self.record(f'map-room-{n:02}',8,note='Exact marks compared against the same room previously loaded by the real game.')
            self.press_map('B','gMenuStudyZoom',0)
        self.check('all25 map previews preserve live world/room/spots/player/RNG',self.snapshot()==paused)
        self.close_map()
        # Fresh core/run: the charted unvisited chest has neither remembered
        # marks nor a warm preview cache. Compare its pure preview against the
        # same room's real generated location harvested in the previous run.
        chest=next(n for n,c in enumerate(world['cells']) if c['role'] in (4,10))
        self.boot(seed=0xB4A7);self.inventory(True);P.enter_forest(self.c);C.dismiss(self.c);C.clear_enemies(self.c)
        point=BR.natural_spot(self.c,0,0);assert point;self.focus(point)
        self.check('unvisited chest fixture has no remembered marks or visit',not(self.cell(chest)['flags']&1) and not any(self.cell(chest)['marks']))
        self.open_map();self.seek_cell(chest);paused=self.snapshot();self.press_map('A','gMenuStudyZoom',1)
        self.check_locations(chest,actual[chest],'charted unvisited chest')
        self.record('map-charted-unvisited-chest',24,note='Fresh core: Map+Astrolabe reveal this unvisited chest; a cold pure preview locates it without visiting or changing live state.')
        self.check('unvisited metadata preview preserves live game state',self.snapshot()==paused)
        self.close_map()
        # The current-room Heart is a moving actor, so verify that the H mark
        # follows its actual paused position rather than always using spawn.
        goal=world['goal'];L.warp(self.c,goal,next(i for i,g in enumerate(world['cells'][goal]['gate']) if g));C.dismiss(self.c)
        point=BR.natural_spot(self.c,0,0);assert point;self.focus(point);P.run(self.c,48)
        self.check('actual live Heart actor exists',any(P.actor(self.c,i)['kind']==2 and P.actor(self.c,i)['type']==5 for i in range(1,96)))
        self.record('map-live-heart-world',24,note='The actual Heart moves under normal boss AI; no boss pose, position or state is assigned.')
        self.open_map();self.seek_cell(goal);paused=self.snapshot();actors=hashlib.sha256(B.bytes_at(self.c,P.sym('gActors'),96*64)).hexdigest()
        self.press_map('A','gMenuStudyZoom',1);self.check_locations(goal,self.cell(goal)['marks'],'live moving Heart')
        self.record('map-live-heart-zoom',24,note='H is anchored to the real paused boss position; player and event markers have separate callouts.')
        self.check('map inspection freezes live actor positions/state',hashlib.sha256(B.bytes_at(self.c,P.sym('gActors'),96*64)).hexdigest()==actors)
        self.check('live boss map preserves world/room/spots/player/RNG',self.snapshot()==paused)
        self.close_map()
        # Completed-state fixtures exercise suppression without replaying every
        # combat/trial workflow, which this map-only pass does not change.
        for n in range(25):
            at=P.sym('gWorld')+4+n*13
            P.w8(self.c,at+11,self.cell(n)['flags']|1|2|4|16|32|128)
            P.w8(self.c,at+4,self.cell(n)['opened']|15)
            P.w8(self.c,P.sym('gWorld')+MYST_FLAGS+n,1)
        self.open_map();self.check_overview('completed');self.record('map-completed',24,note='Completion flags are explicit fixtures: no spent find remains advertised.')
        self.close_map()
        # Shrine placement is optional; use a separately generated seed that
        # genuinely contains one rather than inventing a map mark.
        shrine_found=False
        for seed in (1,2,3,4,5,6,7,8,9,11):
            self.boot(seed=seed);self.inventory(True);world=C.world(self.c)
            candidates=[n for n,c in enumerate(world['cells']) if c['role']==9]
            if not candidates:continue
            P.enter_forest(self.c);C.dismiss(self.c)
            for n in candidates:
                L.warp(self.c,n,next(i for i,g in enumerate(world['cells'][n]['gate']) if g));C.dismiss(self.c);C.clear_enemies(self.c)
                reference=self.cell(n)['marks']
                if not reference[8]:continue
                point=BR.natural_spot(self.c,0,0)
                if not point:continue
                self.focus(point);self.actual_layouts[f'shrine seed{seed} cell{n}']=reference
                self.record('map-shrine-world',24,note=f'Actual optional shrine, seed{seed}, cell{n}; no shrine/mark was inserted.')
                self.open_map();self.seek_cell(n);self.check_overview('shrine');self.press_map('A','gMenuStudyZoom',1)
                self.check_locations(n,reference,'actual shrine room');self.record('map-shrine-zoom',24,note=f'Healing shrine uses the heart pictogram and Shrine label; boss uses H, seed{seed}, cell{n}.')
                self.check('actual shrine has distinct healing icon',any(m['kind']==HEAL for m in self.markers()))
                self.close_map();shrine_found=True;break
            if shrine_found:break
        self.check('at least one naturally generated healing shrine reviewed',shrine_found)
        # Fog starts in a fresh core/run so no previously cached room mask can
        # conceal an accidental unknown preview request.
        self.boot(seed=11);self.inventory(True);P.enter_forest(self.c);C.dismiss(self.c);C.clear_enemies(self.c)
        world=C.world(self.c);here=C.cell(self.c);target=next(n for n in range(25) if abs(n%5-here%5)+abs(n//5-here//5)==1)
        for n in range(25):
            at=P.sym('gWorld')+4+n*13;P.w8(self.c,at+11,(self.cell(n)['flags']&~1)|(1 if n==here else 0))
        P.w8(self.c,P.sym('gPl')+36,P.r8(self.c,P.sym('gPl')+36)&~12)
        self.open_map();self.check_overview('fogged');self.seek_cell(target)
        mask_before=P.r32(self.c,B.static_symbol('sMaskDone'));paused=self.snapshot();self.record('map-fog-overview',24,note='No Map/Astrolabe; only current room visited.')
        self.press_map('A','gMenuStudyZoom',1);self.record('map-fog-zoom',24,note='Unknown room stays Not charted; no event location is invented.')
        self.check('unknown room exposes no location markers',not self.markers())
        self.check('unknown zoom fetches no terrain',P.r32(self.c,B.static_symbol('sMaskDone'))==mask_before)
        self.check('fog navigation preserves live game state',self.snapshot()==paused)
        self.close_map()
        # Map geometry alone must not grant Astrolabe locations. A charted
        # unvisited chamber has terrain, but no invented central event icon.
        P.w8(self.c,P.sym('gPl')+36,(P.r8(self.c,P.sym('gPl')+36)|4)&~8)
        self.open_map();self.seek_cell(target);self.check_overview('Map without Astrolabe')
        self.record('map-charted-without-astrolabe',24,note='Map ownership charts geometry; the unvisited room has no Astrolabe event locations.')
        paused=self.snapshot();self.press_map('A','gMenuStudyZoom',1)
        self.record('map-charted-without-astrolabe-zoom',24,note='Terrain is visible without disclosed chest/Heart/gate positions.')
        self.check('Map-only unvisited zoom has no event locations',not self.markers())
        self.check('charted unvisited room permits terrain preview',bool(P.r32(self.c,B.static_symbol('sMaskDone'))&(1<<target)))
        self.check('Map-only metadata rendering preserves live game state',self.snapshot()==paused)
        self.close_map();self.save()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frozen',required=True);p.add_argument('--out',required=True);p.add_argument('--no-video',action='store_true');args=p.parse_args();args.kind='adopted-map'
    review=MapReview(args);review.suite();review.save()
    failures=[c for c in review.checks if not c['passed']]
    print('RESULT',len(review.checks)-len(failures),'/',len(review.checks),'captures',len(review.rows))
    return bool(failures)

if __name__=='__main__':raise SystemExit(main())
