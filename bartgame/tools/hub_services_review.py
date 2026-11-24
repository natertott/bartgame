#!/usr/bin/env python3
"""Execute the Drain ladder stamp against explicit host adapters.

Use the selected authored Drain definition to check exact ladder-ID reuse,
unchanged furnishings and dry routes through the cleared service sites.
Native input and interactions are checked separately in mGBA.
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
GameState gGame;Room gRoom;
static int rendered;
u16 room_get(int x,int y){return gRoom.ground[y*32+x];}
u16 room_get_overlay(int x,int y){return gRoom.overlay[y*32+x];}
void room_set(int x,int y,u16 mt){gRoom.ground[y*32+x]=mt;gRoom.underlay[y*32+x]=mt;}
void room_set_overlay(int x,int y,u16 mt){gRoom.overlay[y*32+x]=mt;}
void room_render(void){rendered++;}
void init(void){gGame.area=AREA_SEWER;gRoom.w=30;gRoom.h=20;rendered=0;}
void set_cell(int layer,int x,int y,int mt){if(layer)room_set_overlay(x,y,mt);else room_set(x,y,mt);}
int get_cell(int layer,int x,int y){return layer?room_get_overlay(x,y):room_get(x,y);}
void area(int a){gGame.area=a;}
int renders(void){return rendered;}
'''


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--assets-header',type=Path,default=GAME/'build/gen/assets.h')
    ap.add_argument('--baseline',default='127ea61b',help='Published source before Drain integration')
    args=ap.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(GAME/'art'))
    import rooms
    import sewer_final_contracts as S
    room=rooms.ROOMS[0]
    header=args.assets_header.read_text()
    ids={name.lower():int(value) for name,value in re.findall(r'^#define MT_(\w+) (\d+)$',header,re.M)}
    records={x['name']:x for x in S.CLONES}
    original=json.loads((GAME/'art/reboot_contracts.json').read_text())
    records.update({x['name']:x for x in original['tiles']})
    meta={ids[name]:(record['coll'],record['type']) for name,record in records.items() if name in ids}
    adapter=out/'adapter.c';adapter.write_text(ADAPTER)
    binary=out/'hub-services.so'
    command=['gcc','-shared','-fPIC','-O2','-Wno-attributes','-I'+str(GAME/'src'),
             '-I'+str(args.assets_header.resolve().parent),str(GAME/'src/hub_services.c'),str(adapter),'-o',str(binary)]
    result=subprocess.run(command,capture_output=True,text=True);(out/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
    lib=C.CDLL(str(binary));lib.get_cell.restype=C.c_int;lib.renders.restype=C.c_int
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
    check('one final room render after bounded stamp',lib.renders()==1)
    for layer in range(2):
        for y in range(20):
            for x in range(30):
                wanted=before[layer][y][x-10] if 18<=x<=20 and y<5 else before[layer][y][x]
                check('exact selected ladder copy or untouched furnishing',lib.get_cell(layer,x,y)==wanted,[layer,x,y])
    def solid(x,y):
        if x<5 or x>474 or y<8 or y>319:return True
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
    fronts=[(120,126),(152,254),(304,254),(352,254),(384,254),(416,254),
            (152,62),(312,94),(312,62),(392,126)]
    for p in fronts:
        check('dry player route reaches the marked hub coordinate',p in previous,list(p))
        if p in previous:
            path=[];cur=p
            while cur is not None:path.append(cur);cur=previous[cur]
            paths[str(p)]=list(reversed(path))
    lib.area(1);lib.hub_services_build()
    check('ladder stamp only renders in the Drain',lib.renders()==1)
    report=dict(method=__doc__,checks=checks,passed=sum(x['passed'] for x in checks),total=len(checks),
                baseline_art_commit=args.baseline,
                paths=paths,source_sha256={str(p.relative_to(GAME)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [GAME/'src/hub_services.c',GAME/'src/hub_services.h',GAME/'art/cream_actors.py']},
                tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),compile_command=command,
                scope='Actual ladder module with room and renderer adapters. Dry-route flood uses authored native metadata and the cabinet footprint.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',report['passed'],'/',report['total'])
    if report['passed']!=report['total']:raise SystemExit(1)


if __name__=='__main__':main()
