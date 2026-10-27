#include <stdio.h>
#include <stdlib.h>
#include "world.h"
#include "myst.h"

static int same_world(const World* a,const World* b) {
    unsigned i;const unsigned char* x=(const unsigned char*)a;const unsigned char* y=(const unsigned char*)b;
    for(i=0;i<sizeof(*a);i++)if(x[i]!=y[i])return 0;
    return 1;
}
/* Test the actual gate graph independently from generator route scoring. */
static unsigned reachable(int stage) {
    unsigned seen=1u<<gWorld.entry;
    int change=1,i,s;
    while(change) {
        change=0;
        for(i=0;i<CELLS;i++) if(seen&(1u<<i)) for(s=0;s<4;s++) {
            int n=cell_neighbor(i,s),g=gWorld.cells[i].gate[s];
            if(n<0||g==GATE_WALL||g==GATE_LOCK||g==GATE_EXIT||
               (g==GATE_CRACK&&stage<1)||(g==GATE_WEB&&stage<2)||(g==GATE_CHASM&&stage<3))continue;
            if(!(seen&(1u<<n))){seen|=1u<<n;change=1;}
        }
    }
    return seen;
}
static int fail(unsigned seed,int profile,const char* why) {
    printf("FAIL seed %u profile %d: %s\n",seed,profile,why);return 1;
}
int main(int argc,char** argv) {
    unsigned seed, count=argc>1?atoi(argv[1]):5000;
    int profile, failures=0;
    if(sizeof(Cell)!=13) return fail(0,0,"Cell ABI changed");
    for(profile=0;profile<WORLD_PROFILE_COUNT;profile++) {
        const WorldTuning* t=&world_profiles[profile];
        unsigned total=0, optional=0, back=0, detours=0, low=255, high=0, violations=0, tries=0, fallbacks=0;
        for(seed=1;seed<=count;seed++) {
            WorldRouteMetrics m;
            int i,s,n;
            world_generate_tuned(seed,t);
            world_route_metrics(&m);
            fallbacks+=gWorldGenerationFallback; tries+=gWorldGenerationAttempts; total+=m.required_crossings;optional+=CELLS-m.required_cells;
            back+=m.backtrack_edges;detours+=m.detours;
            if(m.required_crossings<low)low=m.required_crossings;
            if(m.required_crossings>high)high=m.required_crossings;
            if(m.required_crossings<t->min_crossings||m.required_crossings>t->max_crossings||
               m.required_cells>CELLS-t->min_optional||m.detours<t->min_detours||
               m.spine_edges<t->spine_min||m.spine_edges>t->spine_max){violations++; if(violations<4)printf("miss seed %u: crossings %d cells %d spine %d detours %d\n",seed,m.required_crossings,m.required_cells,m.spine_edges,m.detours);}
            if(m.required_cells>=CELLS){ failures+=fail(seed,profile,"all rooms required");break; }
            for(i=0;i<3;i++) {
                int cell=gWorld.key_cell[i];
                unsigned r=reachable(i);
                if(i>0&&(reachable(i-1)&(1u<<cell))){failures+=fail(seed,profile,"milestone bypasses previous barrier");break;}
                if(!(r&(1u<<cell))){failures+=fail(seed,profile,"reward behind its own item");break;}
                if(r&(1u<<gWorld.goal)){failures+=fail(seed,profile,"goal reachable before all three rewards");break;}
                if(gWorld.cells[cell].role!=ROLE_KEYITEM||gWorld.cells[cell].role_arg!=i+1||
                   !gWorld.myst[cell]){failures+=fail(seed,profile,"missing milestone event");break;}
                if(MYST_KIND(gWorld.myst[cell])==MK_TORCHES||MYST_KIND(gWorld.myst[cell])==MK_BOULDERS)
                    {failures+=fail(seed,profile,"milestone needs its own prize");break;}
            }
            if(!(reachable(3)&(1u<<gWorld.goal))){failures+=fail(seed,profile,"goal not reachable");break;}
            for(i=0;i<CELLS;i++)for(s=0;s<4;s++) {
                n=cell_neighbor(i,s);
                if(n>=0&&gWorld.cells[i].gate[s]!=gWorld.cells[n].gate[(s+2)&3])
                    {printf("edge %d side %d => %d: %d vs %d\n",i,s,n,gWorld.cells[i].gate[s],gWorld.cells[n].gate[(s+2)&3]);failures+=fail(seed,profile,"asymmetric edge");goto done;}
            }
            if(gWorldGenerationAttempts>t->attempts+1){failures+=fail(seed,profile,"unbounded candidate budget");break;}
            if(seed<=64) {
                WorldTuning quick=*t; WorldRouteMetrics qm;
                quick.attempts=1;
                world_generate_tuned(seed,&quick);world_route_metrics(&qm);
                if(qm.required_crossings<t->min_crossings||qm.required_crossings>t->max_crossings||
                   qm.required_cells>CELLS-t->min_optional||qm.detours<t->min_detours||
                   qm.spine_edges<t->spine_min||qm.spine_edges>t->spine_max)
                    {failures+=fail(seed,profile,"certified fallback out of range");break;}
                world_generate_tuned(seed,t);
            }
            if(seed<=20){
                World copy=gWorld;
                world_generate_tuned(seed,t);
                if(!same_world(&copy,&gWorld)){failures+=fail(seed,profile,"nondeterministic");break;}
            }
        }
        printf("profile %d: %u seeds, crossings %.2f [%u,%u], optional %.2f, repeated crossings %.2f, detours %.2f, tuning misses %u, attempts/run %.2f, fallbacks %u\n",
               profile,count,total/(double)count,low,high,optional/(double)count,back/(double)count,detours/(double)count,violations,tries/(double)count,fallbacks);
        if(violations) failures+=fail(0,profile,"pacing range missed");
    }
done:
    printf("%s: progression and pacing\n",failures?"FAILED":"PASS");
    return failures?1:0;
}
