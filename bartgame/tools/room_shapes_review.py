#!/usr/bin/env python3
"""Execute actual shape/room collision C and compare it to native art alpha.

Private host adapters supply the unchanged coarse grid and room storage.
The tested fine-mask, point-query and inclusive box-query functions are the
actual production sources. This qualifies geometry, not emulator timing.
"""
import argparse,ctypes as C,json,random,re,subprocess,sys
from pathlib import Path
GAME=Path(__file__).resolve().parent.parent
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True);args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(GAME/'art'));import handoff_shapes as A
    source=(GAME/'src/room_shapes.c').read_text();source=re.sub(r'^#include[^\n]*','',source,flags=re.M)
    room=(GAME/'src/room.c').read_text();room=room[room.index('bool8 room_solid_px('):room.index('void room_load_def(')]
    prefix='''#include <stdint.h>
#include <string.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;typedef int bool8;
#define EWRAM_BSS
#define IWRAM_CODE
#define TRUE 1
#define FALSE 0
#define ROOM_MAX_W 32
#define ROOM_MAX_H 32
#define MT_NONE 65535
typedef struct {u8 w,h;u8 solid[4096];u16 overlay[1024];} Room;
Room gRoom;u8 metatile_coll[2048];
void memset32(void*p,int n,int size){memset(p,n,size);}
u16 room_get_overlay(int x,int y){return gRoom.overlay[y*32+x];}
'''
    prefix+='\n'.join('#define MT_LH_SHAPE_%s %d'%(name.upper(),1000+i) for i,name in enumerate(A.KINDS))+'\n'
    unit=out/'actual-shapes.c';unit.write_text(prefix+source+'\n'+room)
    libpath=out/'actual-shapes.so';subprocess.run(['gcc','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',str(unit),'-o',str(libpath)],check=True)
    lib=C.CDLL(str(libpath))
    class Room(C.Structure):_fields_=[('w',C.c_uint8),('h',C.c_uint8),('solid',C.c_uint8*4096),('overlay',C.c_uint16*1024)]
    r=Room.in_dll(lib,'gRoom');r.w=r.h=8
    for i in range(1024):r.overlay[i]=65535
    masks=(C.c_uint8*2048).in_dll(lib,'metatile_coll');masks[1]=15
    count=C.c_uint16.in_dll(lib,'gRoomShapeCount');checks=0;random.seed(0x53484150)
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:raise AssertionError(label)
    for i,name in enumerate(A.KINDS):
        lib.room_shapes_clear();check(count.value==0,'clear count')
        for y in range(6,8):
            for x in range(6,8):r.solid[y*64+x]=1
        lib.room_shape_tile(3,3,1000+i);check(count.value==1,'install count')
        alpha=A.image(name)
        for y in range(16):
            for x in range(16):check(bool(lib.room_solid_px(48+x,48+y))==bool(alpha.getpixel((x,y))),'native alpha '+name)
        for _ in range(500):
            x0,x1=sorted(random.randrange(48,64) for _ in range(2));y0,y1=sorted(random.randrange(48,64) for _ in range(2))
            expected=any(alpha.getpixel((x,y)) for y in range(y0-48,y1-47) for x in range(x0-48,x1-47))
            check(bool(lib.room_box_solid(x0,y0,x1,y1))==bool(expected),'inclusive rectangle '+name)
        r.overlay[3*32+3]=1
        check(all(lib.room_solid_px(48+x,48+y) for y in range(16) for x in range(16)),'overlay collision wins')
        for quarter in range(4):
            masks[2]=8>>quarter;r.overlay[3*32+3]=2
            for y in range(16):
                for x in range(16):
                    expected=bool(alpha.getpixel((x,y))) or (y//8)*2+x//8==quarter
                    check(bool(lib.room_solid_px(48+x,48+y))==expected,'asymmetric overlay quarter '+name)
        r.overlay[3*32+3]=65535
        lib.room_shape_tile(3,3,0);check(count.value==0,'replace returns coarse path')
        check(lib.room_solid_px(60,60)==1,'original coarse collision retained')
    check(lib.room_box_solid(-1,0,0,0),'negative bounds solid');check(lib.room_solid_px(128,128),'outside room solid')
    report={'checks':checks,'passed':checks,'failed':0,'native_shapes':len(A.KINDS),'method':__doc__}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
