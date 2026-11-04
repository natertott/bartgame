#!/usr/bin/env python3
"""Compile actual ambient C before/after against deterministic host fixtures.

This checks density arithmetic and animation stages for every source count
from zero through forty, including odd/sparse views. It is algorithm evidence;
the separate native mGBA captures establish real video/OAM behavior.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from perf_effects_equivalence import FIXTURE, aliases

GAME = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()

VIEW = r'''
int @P@_view(int i,int* site,int* x,int* y,int* fractional) {
    if(!sAmbientTile || i>=sAmbientViewCount)return 0;
    const AmbientViewSite* view=&sAmbientView[i];
    const AmbientSite* point=&sAmbientSites[view->site];
    *site=view->site;*x=point->x-3;*y=point->y-3;
    *fractional=@F@;
    return 1;
}
'''

MAIN = r'''
void before_ambient_room_reset(void),after_ambient_room_reset(void);
void before_ambient_draw(bool8),after_ambient_draw(bool8);
int before_view(int,int*,int*,int*,int*),after_view(int,int*,int*,int*,int*);
typedef struct {int site,x,y,fractional;} Point;
static Point points[2][24];
static u8 sequence[2][24][512];
static unsigned cases,frame_cases,odd_cases,checks;
static unsigned totals[2];

static int check(int ok,const char* message,int count,int salt) {
    checks++;
    if(!ok)printf("FAIL %s count%d salt%d\n",message,count,salt);
    return ok;
}

static int one(int count,int salt) {
    int side,tick,i,j,n[2]={0,0};
    unsigned total[2]={0,0};
    gRoom.w=16;gRoom.h=12;gCamX=gCamY=0;
    gWorld.seed=0xb4a7+salt*111;gGame.area=salt%3;gGame.cell=salt%25;
    for(i=0;i<1024;i++){gRoom.ground[i]=3;gRoom.overlay[i]=MT_NONE;}
    /* Every point is inside the exact inner viewport, with isolated actors.
       Alternate reflective floor and foreground material across seeds. */
    for(i=0;i<count;i++)gRoom.ground[(2+i/14)*32+1+i%14]=(salt&1)?2:1;
    before_ambient_room_reset();after_ambient_room_reset();
    memset(sequence,0,sizeof(sequence));
    for(side=0;side<2;side++) {
        gFrame=0;gOamCount=0;call_count=0;
        if(side){after_ambient_draw(TRUE);after_ambient_draw(FALSE);}
        else{before_ambient_draw(TRUE);before_ambient_draw(FALSE);}
        for(i=0;i<24;i++) {
            Point* p=&points[side][i];
            int exists=side?after_view(i,&p->site,&p->x,&p->y,&p->fractional):
                            before_view(i,&p->site,&p->x,&p->y,&p->fractional);
            if(!exists)break;
            n[side]++;
        }
        for(tick=0;tick<512;tick++) {
            gFrame=tick;gOamCount=0;call_count=0;
            if(side){after_ambient_draw(TRUE);after_ambient_draw(FALSE);}
            else{before_ambient_draw(TRUE);before_ambient_draw(FALSE);}
            total[side]+=call_count;frame_cases++;
            for(i=0;i<call_count;i++) {
                for(j=0;j<n[side];j++)if(calls[i].x==points[side][j].x&&calls[i].y==points[side][j].y)break;
                if(!check(j<n[side],"drawn point belongs to selected view",count,salt))return 1;
                sequence[side][j][tick]=calls[i].frame;
            }
        }
    }
    if(!check(n[0]==MIN(count,24),"old count capped at24",count,salt))return 1;
    if(!check(n[1]==(n[0]+1)/2,"alternating subset count",count,salt))return 1;
    if(!check(total[1]*2==total[0],"exactly half integrated visible density",count,salt))return 1;
    for(i=0;i<n[1];i++) {
        Point* p=&points[1][i];
        int fractional=(n[0]&1)&&i==n[1]-1;
        if(!check(p->site==points[0][i*2].site,"stable alternating source order",count,salt))return 1;
        if(!check(p->fractional==fractional,"only the unpaired site is fractional",count,salt))return 1;
    }
    for(side=0;side<2;side++)for(i=0;i<n[side];i++) {
        int lit=0,stages=0,period=side?128:64,half_same=1;
        for(tick=0;tick<512;tick++) {
            int value=sequence[side][i][tick];lit+=value!=0;stages|=1<<value;
            if(tick>=period&&value!=sequence[side][i][tick-period])
                if(!check(0,"full animation period",count,salt))return 1;
            if(tick>=period/2&&value!=sequence[side][i][tick-period/2])half_same=0;
        }
        if(!check(!half_same,"period is not accidentally halved",count,salt))return 1;
        if(!check(lit==(points[side][i].fractional?128:256),"bright duty",count,salt))return 1;
        if(!check(stages==(1<<SHEET_GLITTER_FRAMES)-1,"all native stages preserved",count,salt))return 1;
    }
    totals[0]+=total[0];totals[1]+=total[1];cases++;odd_cases+=n[0]&1;
    return 0;
}

int main(void) {
    int count,salt,failed=0;
    for(salt=0;salt<16&&!failed;salt++)for(count=0;count<=40&&!failed;count++)failed=one(count,salt);
    printf("{\"passed\":%s,\"cases\":%u,\"odd_cases\":%u,\"video_frame_cases\":%u,\"checks\":%u,\"draws_before\":%u,\"draws_after\":%u}\n",
           failed?"false":"true",cases,odd_cases,frame_cases,checks,totals[0],totals[1]);
    return failed;
}
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', default='04a42521264349e23d8057744e6467eace0bdd13')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    output = Path(args.out).resolve()
    work = output.parent / (output.stem + '-build')
    work.mkdir(parents=True, exist_ok=True)
    objects, inputs, log = [], {}, []
    for phase in ('before', 'after'):
        data = (subprocess.check_output(['git', 'show', args.baseline + ':bartgame/src/ambient.c'], cwd=GAME.parent)
                if phase == 'before' else (GAME / 'src/ambient.c').read_bytes())
        inputs[phase] = SHA(data)
        source = data.decode()
        wrapper = VIEW.replace('@P@', phase).replace('@F@', 'view->fractional' if phase == 'after' else '0')
        path = work / (phase + '.c')
        path.write_text(aliases(source, phase) + source + wrapper)
        obj = path.with_suffix('.o')
        cmd = ['gcc', '-O2', '-fno-builtin', '-ffunction-sections', '-fdata-sections', '-w',
               '-Isrc', '-Ibuild/gen', '-c', str(path), '-o', str(obj)]
        result = subprocess.run(cmd, cwd=GAME, text=True, capture_output=True)
        log += [str(cmd), result.stdout, result.stderr]
        if result.returncode: raise RuntimeError(result.stderr)
        objects.append(str(obj))
    fixture = work / 'fixture.c'
    fixture.write_text(FIXTURE.split('void before_ambient_room_reset')[0] + MAIN)
    binary = work / 'density'
    cmd = ['gcc', '-O2', '-fno-builtin', '-w', '-Isrc', '-Ibuild/gen', '-Wl,--gc-sections',
           str(fixture), *objects, '-o', str(binary)]
    result = subprocess.run(cmd, cwd=GAME, text=True, capture_output=True)
    log += [str(cmd), result.stdout, result.stderr]
    (work / 'compile.log').write_text('\n'.join(log))
    if result.returncode: raise RuntimeError(result.stderr)
    result = subprocess.run([str(binary)], text=True, capture_output=True)
    (work / 'run.log').write_text(result.stdout + result.stderr)
    report = json.loads(result.stdout.splitlines()[-1])
    report.update(method=__doc__.strip(), baseline=args.baseline, source_sha256=inputs,
                  tool_sha256=SHA(Path(__file__).read_bytes()), fixture_sha256=SHA(fixture.read_bytes()),
                  executable_sha256=SHA(binary.read_bytes()))
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
