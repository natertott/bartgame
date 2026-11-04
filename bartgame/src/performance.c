#include "performance.h"
#if BART_PROFILE
u32 gPerfWorking[PF_COUNT],gPerfCycles[PF_COUNT];
u32 gPerfSequence;
static u32 sPerfStart;

void perf_init(void) {
    REG16(0x10E)=0;REG16(0x10A)=0;
    REG16(0x108)=0;REG16(0x10C)=0;
    REG16(0x10E)=0x84; /* timer3 cascades from timer2 */
    REG16(0x10A)=0x80; /* full CPU rate, free running */
}

u32 perf_clock(void) {
    u32 hi,lo,again;
    do { hi=REG16(0x10C);lo=REG16(0x108);again=REG16(0x10C); }while(hi!=again);
    return (hi<<16)|lo;
}

void perf_frame_begin(void) {
    int i;sPerfStart=perf_clock();
    for(i=0;i<PF_COUNT;i++)gPerfWorking[i]=0;
}

void perf_frame_end(void) {
    int i;gPerfWorking[PF_TOTAL]=perf_clock()-sPerfStart;
    for(i=0;i<PF_COUNT;i++)gPerfCycles[i]=gPerfWorking[i];
    gPerfSequence++;
}
#endif
