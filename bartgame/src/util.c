/* BARTGAME: memory helpers (no libc) and the PRNG. */
#include "gba.h"
#include "util.h"

void* memcpy(void* dst, const void* src, u32 n) {
    u8* d = dst;
    const u8* s = src;
    if ((((u32)d | (u32)s | n) & 3) == 0) {
        u32* d4 = dst;
        const u32* s4 = src;
        n >>= 2;
        while (n--)
            *d4++ = *s4++;
        return dst;
    }
    while (n--)
        *d++ = *s++;
    return dst;
}

void* memset(void* dst, int c, u32 n) {
    u8* d = dst;
    if ((((u32)d | n) & 3) == 0) {
        u32 v = (u8)c;
        v |= v << 8;
        v |= v << 16;
        u32* d4 = dst;
        n >>= 2;
        while (n--)
            *d4++ = v;
        return dst;
    }
    while (n--)
        *d++ = (u8)c;
    return dst;
}

void memcpy32(void* dst, const void* src, u32 bytes) {
    u32* d = dst;
    const u32* s = src;
    bytes >>= 2;
    while (bytes--)
        *d++ = *s++;
}

void memset32(void* dst, u32 value, u32 bytes) {
    u32* d = dst;
    bytes >>= 2;
    while (bytes--)
        *d++ = value;
}

/* Two streams: gameplay (advanced by everything) and a seedable one for
   the generator, so the world is a pure function of the run seed. */
static u32 sRand = 0x1234567;

u32 rand_next(void) {
    sRand = sRand * 1103515245u + 12345u;
    return sRand >> 8;
}

u32 rand_range(u32 n) {
    return n ? (rand_next() % n) : 0;
}

void rng_seed(Rng* r, u32 seed) {
    r->s = seed * 2654435761u + 0x9E3779B9u;
    if (r->s == 0)
        r->s = 1;
}

u32 rng_next(Rng* r) {
    /* xorshift32 */
    u32 x = r->s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    r->s = x;
    return x;
}

u32 rng_range(Rng* r, u32 n) {
    return n ? (rng_next(r) % n) : 0;
}

u32 hash32(u32 a, u32 b) {
    u32 h = a * 0x9E3779B1u ^ (b + 0x7F4A7C15u);
    h ^= h >> 15;
    h *= 0x85EBCA77u;
    h ^= h >> 13;
    h *= 0xC2B2AE3Du;
    h ^= h >> 16;
    return h;
}
