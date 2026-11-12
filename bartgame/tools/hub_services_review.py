#!/usr/bin/env python3
"""Execute the actual Drain service C against explicit host adapters.

The room metadata is the selected authored Drain definition, not a guessed
rectangle. Check exact ladder-ID reuse, unchanged furnishings, dry paths to
all standing fronts, real service input filtering and bounded draw dispatch.
This is host placement/state evidence; actual mGBA play remains a separate test.
"""
import argparse
from collections import deque
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

GAME=Path(__file__).resolve().parent.parent

ADAPTER=r'''
#include "hub_services.h"
#include "game.h"
#include "room.h"
#include "player.h"
#include "handoff_events.h"
GameState gGame;Room gRoom;Actor gActors[ACTOR_MAX];Actor* gPlayer=&gActors[0];
PlayerState gPl;HandoffState gHandoffState;s16 gCamX,gCamY;
const u8 interactivechest_frame_pal[8]={9,9,9,9,9,9,9,9};
static int rendered,last_service,draws,loads,claims;
u16 room_get(int x,int y){return gRoom.ground[y*32+x];}
u16 room_get_overlay(int x,int y){return gRoom.overlay[y*32+x];}
void room_set(int x,int y,u16 mt){gRoom.ground[y*32+x]=mt;gRoom.underlay[y*32+x]=mt;}
void room_set_overlay(int x,int y,u16 mt){gRoom.overlay[y*32+x]=mt;}
void room_render(void){rendered++;}
u16 sprite_load_frame(int sheet,int frame){loads++;return 100+frame;}
void draw_sprite(int x,int y,int sheet,u16 tile,int frame,int flip,int priority,int pal){draws++;}
bool8 handoff_open_service(int service){last_service=service;return TRUE;}
bool8 handoff_claim_inn_reward(void){if(!gHandoffState.inn_reward)return FALSE;gHandoffState.inn_reward=0;claims++;return TRUE;}
void init(void){
    gGame.area=AREA_SEWER;gRoom.w=30;gRoom.h=20;gPlayer->kind=AK_PLAYER;
    gPlayer->state=PS_NORMAL;gPlayer->facing=FACE_N;gHandoffState.inn_reward=0;
    rendered=last_service=draws=loads=claims=0;
}
void set_cell(int layer,int x,int y,int mt){if(layer)room_set_overlay(x,y,mt);else room_set(x,y,mt);}
int get_cell(int layer,int x,int y){return layer?room_get_overlay(x,y):room_get(x,y);}
void hero(int x,int y,int facing,int state){gPlayer->x=x<<16;gPlayer->y=y<<16;gPlayer->facing=facing;gPlayer->state=state;}
void area(int a){gGame.area=a;}
void reward(int r){gHandoffState.inn_reward=r;}
int metric(int n){return n==0?rendered:n==1?last_service:n==2?draws:n==3?loads:claims;}
'''


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--baseline',default='127ea61b',help='Published source before Drain integration')
    args=ap.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(GAME/'art'))
    import rooms
    import sewer_final_contracts as S
    room=rooms.ROOMS[0]
    header=(GAME/'build/gen/assets.h').read_text()
    ids={name.lower():int(value) for name,value in re.findall(r'^#define MT_(\w+) (\d+)$',header,re.M)}
    records={x['name']:x for x in S.CLONES}
    original=json.loads((GAME/'art/reboot_contracts.json').read_text())
    records.update({x['name']:x for x in original['tiles']})
    meta={ids[name]:(record['coll'],record['type']) for name,record in records.items() if name in ids}
    adapter=out/'adapter.c';adapter.write_text(ADAPTER)
    binary=out/'hub-services.so'
    command=['gcc','-shared','-fPIC','-O2','-Wno-attributes','-I'+str(GAME/'src'),
             '-I'+str(GAME/'build/gen'),'-DF_CREAMFOLK_DRAIN_BED=12',
             '-DF_CREAMFOLK_DRAIN_TROPHY=13',str(GAME/'src/hub_services.c'),str(adapter),'-o',str(binary)]
    result=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
    lib=C.CDLL(str(binary));lib.get_cell.restype=C.c_int;lib.metric.restype=C.c_int
    lib.hub_services_try_interact.argtypes=[C.c_uint16];lib.hub_services_try_interact.restype=C.c_uint16
    lib.hub_services_box_solid.restype=C.c_uint8
    checks=[]
    def check(name,passed,detail=None):
        checks.append(dict(name=name,passed=bool(passed),detail=detail))
        if not passed:print('FAIL',name,detail)
    import cream_actors
    old_source=subprocess.check_output(['git','show',args.baseline+':bartgame/art/cream_actors.py'],cwd=GAME.parent,text=True)
    old_scope={'__name__':'old_cream_actors','__file__':str(GAME/'art/cream_actors.py')}
    exec(compile(old_source,'old_cream_actors.py','exec'),old_scope)
    old_sheets=old_scope['build_sheets']();new_sheets=cream_actors.build_sheets()
    check('all preexisting Cream sheet IDs stay in order',[x['name'] for x in old_sheets]==[x['name'] for x in new_sheets])
    for old,new in zip(old_sheets,new_sheets):
        for field in ('w','h','pal'):check('existing sheet geometry and palette remain exact',old[field]==new[field],[old['name'],field])
        check('existing frame IDs remain prefix',list(new['frames'])[:len(old['frames'])]==list(old['frames']),old['name'])
        for name,pixels in old['frames'].items():check('existing frame pixels remain exact',new['frames'][name]==pixels,[old['name'],name])
        for name,pixels in new['frames'].items():
            check('native canvas and 4bpp inks',len(pixels)==new['h'] and all(len(row)==new['w'] and all(0<=int(c,16)<16 for c in row) for row in pixels),[new['name'],name])
    lib.init()
    for layer,key in enumerate(('ground','overlay')):
        for y in range(20):
            for x in range(30):lib.set_cell(layer,x,y,ids[room[key][y][x]] if room[key][y][x] else 65535)
    before=[[[lib.get_cell(layer,x,y) for x in range(30)] for y in range(20)] for layer in range(2)]
    lib.hub_services_build()
    check('one final room render after bounded stamp',lib.metric(0)==1)
    for layer in range(2):
        for y in range(20):
            for x in range(30):
                wanted=before[layer][y][x-10] if 18<=x<=20 and y<5 else before[layer][y][x]
                check('exact selected ladder copy or untouched furnishing',lib.get_cell(layer,x,y)==wanted,[layer,x,y])
    lib.hub_services_enter();check('six single-frame allocations only',lib.metric(3)==6)
    service_points=[(120,110,3),(152,238,4),(304,238,7),(352,238,2),(416,238,5)]
    for x,y,service in service_points:
        lib.hero(x,y+16,0,0)
        check('front A reaches its actual service',lib.hub_services_try_interact(1)==1 and lib.metric(1)==service,[x,y,service])
        lib.hero(x,y+16,1,0);check('side-facing does not steal another NPC input',lib.hub_services_try_interact(1)==0)
        lib.hero(x+15,y+16,0,0);check('outside front width stays ordinary input',lib.hub_services_try_interact(1)==0)
        for state in range(1,14):
            lib.hero(x,y+16,0,state);check('busy player state cannot open service',lib.hub_services_try_interact(1)==0,state)
    lib.hero(304,254,0,0);check('guide R opens local hint',lib.hub_services_try_interact(256)==256 and lib.metric(1)==6)
    lib.hero(384,254,0,0);check('empty bedside has no invisible chest',lib.hub_services_try_interact(1)==0)
    lib.reward(77);check('paid bedside chest is claimed through input',lib.hub_services_try_interact(1)==1 and lib.metric(4)==1)
    lib.hero(200,270,0,0);lib.hub_services_draw(0)
    check('each physical service draws once behind lower Bloom',lib.metric(2)==5)
    lib.hub_services_draw(1);check('opposite depth pass does not double-draw',lib.metric(2)==5)
    lib.reward(1)

    def solid(x,y):
        if x<5 or x>474 or y<8 or y>319:return True
        if lib.hub_services_box_solid(x-5,y-8,x+4,y-1):return True
        if x-5<=403 and x+4>=380 and y-8<=110 and y-1>=97:return True
        for py in range(y-8,y):
            for px in range(x-5,x+5):
                tx,ty=px//16,py//16
                ground=lib.get_cell(0,tx,ty);overlay=lib.get_cell(1,tx,ty)
                mask,kind=meta[ground]
                if kind in ('PIT','WATER','HURT'):return True
                if overlay!=65535:
                    cm,ct=meta[overlay]
                    if ct!='FLOOR':mask|=cm
                if mask&(8>>((py%16//8)*2+px%16//8)):return True
        return False
    start=(200,270);previous={start:None};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((0,-4),(4,0),(0,4),(-4,0)):
            p=(x+dx,y+dy)
            if p not in previous and not solid(*p):previous[p]=(x,y);queue.append(p)
    paths={}
    fronts=[(x,y+16) for x,y,_ in service_points]+[(384,254),(152,62),(312,94),(312,62),(392,126)]
    for p in fronts:
        check('dry player route reaches physical standing front',p in previous,list(p))
        if p in previous:
            path=[];cur=p
            while cur is not None:path.append(cur);cur=previous[cur]
            paths[str(p)]=list(reversed(path))
    lib.area(1);lib.hub_services_draw(0)
    check('services inert outside authored Drain',lib.hub_services_try_interact(1)==0 and not lib.hub_services_box_solid(0,0,480,320))
    report=dict(method=__doc__,checks=checks,passed=sum(x['passed'] for x in checks),total=len(checks),
                baseline_art_commit=args.baseline,
                paths=paths,source_sha256={str(p.relative_to(GAME)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [GAME/'src/hub_services.c',GAME/'src/hub_services.h',GAME/'art/cream_actors.py']},
                tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),compile_command=command,
                scope='Actual service module plus explicit room/render/service spies. Dry-front flood uses authored native metadata and cabinet footprint; it does not model moving NPCs or qualify PPU output.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',report['passed'],'/',report['total'])
    if report['passed']!=report['total']:raise SystemExit(1)


if __name__=='__main__':main()
