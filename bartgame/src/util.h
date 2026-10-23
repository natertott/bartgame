#ifndef UTIL_H
#define UTIL_H
#include "gba.h"

typedef struct {
    u32 s;
} Rng;

u32 rand_next(void);
u32 rand_range(u32 n);
void rng_seed(Rng* r, u32 seed);
u32 rng_next(Rng* r);
u32 rng_range(Rng* r, u32 n);
u32 hash32(u32 a, u32 b);

#endif
