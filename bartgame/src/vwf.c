/* BARTGAME: the UI's text, set a pixel at a time. A glyph of the face
   (art/ui_font.py) is a width and nine rows of bits; it is drawn into a
   canvas, a run of BG0's tiles held from the pool (or a sprite's tiles),
   which is copied to VRAM when it is done or, a few letters at a time,
   at the VBlank. */
#include "gba.h"
#include "video.h"
#include "actor.h"
#include "vwf.h"
#include "assets.h"
#include "ui.h"

static u32 sPix[384 * 8] EWRAM_BSS;
static u16 sNext, sEnd;

void vwf_pool(int first, int end) {
    sNext = first;
    sEnd = end;
}

bool8 vwf_canvas(Canvas* c, int tw, int th) {
    int n = tw * th;
    if (sNext + n > sEnd) {
        c->tw = c->th = 0;
        return FALSE;
    }
    vwf_canvas_at(c, sNext, tw, th);
    sNext += n;
    return TRUE;
}

void vwf_canvas_at(Canvas* c, int tile, int tw, int th) {
    c->tile = tile;
    c->tw = tw;
    c->th = th;
    c->obj = 0;
    c->px = sPix + tile * 8;
}

void vwf_canvas_obj(Canvas* c, u32* buf, int tile, int tw, int th) {
    c->tile = tile;
    c->tw = tw;
    c->th = th;
    c->obj = 1;
    c->px = buf;
}

void vwf_clear(Canvas* c, int ink) {
    u32 w = (ink & 15) * 0x11111111u;
    int i, n = c->tw * c->th * 8;
    for (i = 0; i < n; i++)
        c->px[i] = w;
}

/* a row of eight pixels turned end for end */
static u32 mirror(u32 w) {
    u32 o = 0;
    int i;
    for (i = 0; i < 8; i++)
        o |= ((w >> (i * 4)) & 15) << ((7 - i) * 4);
    return o;
}

void vwf_kit(Canvas* c, int tx, int ty, int ui_tile, int flip, bool8 over) {
    const u32* src = (const u32*)ui_current_tiles() + ui_tile * 8;
    u32* dst;
    int y, i;
    if (tx < 0 || ty < 0 || tx >= c->tw || ty >= c->th)
        return;
    dst = c->px + (ty * c->tw + tx) * 8;
    for (y = 0; y < 8; y++) {
        u32 w = src[(flip & 2) ? 7 - y : y];
        if (flip & 1)
            w = mirror(w);
        if (!over) {
            dst[y] = w;
            continue;
        }
        for (i = 0; i < 8; i++) {
            u32 m = 15u << (i * 4);
            if (w & m)
                dst[y] = (dst[y] & ~m) | (w & m);
        }
    }
}

void vwf_kit_px(Canvas* c, int x, int y, int ui_tile, int flip) {
    const u32* src = (const u32*)ui_current_tiles() + ui_tile * 8;
    int r, i;
    for (r = 0; r < 8; r++) {
        u32 w = src[(flip & 2) ? 7 - r : r];
        for (i = 0; i < 8; i++) {
            int v = (w >> (((flip & 1) ? 7 - i : i) * 4)) & 15;
            if (v)
                vwf_pixel(c, x + i, y + r, v);
        }
    }
}

void vwf_pixel(Canvas* c, int x, int y, int ink) {
    u32* w;
    int s;
    if (x < 0 || y < 0 || x >= c->tw * 8 || y >= c->th * 8)
        return;
    w = c->px + ((y >> 3) * c->tw + (x >> 3)) * 8 + (y & 7);
    s = (x & 7) * 4;
    *w = (*w & ~(15u << s)) | ((u32)(ink & 15) << s);
}

static int glyph_index(int ch) {
    ch &= 0xFF;
    if (ch < VWF_FIRST || ch >= VWF_FIRST + VWF_COUNT)
        return '?' - VWF_FIRST;
    return ch - VWF_FIRST;
}

int vwf_advance(int ch) {
    if (ch == ' ')
        return VWF_SPACE;
    if ((ch & 0xFF) < ' ')
        return 0;
    return vwf_w[glyph_index(ch)] + 1;
}

int vwf_glyph(Canvas* c, int x, int y, int ch, int ink) {
    int g, r, i, w;
    if (ch == ' ')
        return VWF_SPACE;
    g = glyph_index(ch);
    w = vwf_w[g];
    for (r = 0; r < VWF_HEIGHT; r++) {
        u8 bits = vwf_bits[g * VWF_HEIGHT + r];
        for (i = 0; bits; i++, bits >>= 1)
            if (bits & 1)
                vwf_pixel(c, x + i, y + r, ink);
    }
    return w + 1;
}

/* the inks a colour code selects; INK_BASE is the text's own */
int vwf_ink(int code, int base) {
    switch (code) {
        case 2: return UI_INK_HIGH;
        case 3: return UI_INK_RED;
        case 4: return UI_INK_GOLD;
        case 5: return UI_INK_DIM;
        default: return base;
    }
}

/* one ink throughout when flat, else as the codes say */
static int run(Canvas* c, int x, int y, const char* s, int ink, bool8 flat) {
    int cur = ink;
    for (; *s; s++) {
        u8 ch = (u8)*s;
        if (ch < ' ') {
            if (!flat)
                cur = vwf_ink(ch, ink);
            continue;
        }
        x += vwf_glyph(c, x, y, ch, cur);
    }
    return x;
}

int vwf_text(Canvas* c, int x, int y, const char* s, int ink) {
    return run(c, x, y, s, ink, FALSE);
}

int vwf_text_fx(Canvas* c, int x, int y, const char* s, int ink, int fx_ink, int fx) {
    if (fx == FX_SHADOW) {
        run(c, x + 1, y + 1, s, fx_ink, TRUE);
    } else if (fx == FX_OUTLINE) {
        int dx, dy;
        for (dy = -1; dy <= 1; dy++)
            for (dx = -1; dx <= 1; dx++)
                if (dx || dy)
                    run(c, x + dx, y + dy, s, fx_ink, TRUE);
    }
    return run(c, x, y, s, ink, FALSE);
}

int vwf_width(const char* s) {
    int w = 0, last = 0;
    for (; *s; s++) {
        int a = vwf_advance((u8)*s);
        w += a;
        if (a)
            last = (*s == ' ') ? 0 : 1;
    }
    return w - last; /* no spacing after the last glyph */
}

int vwf_fit(const char* s, int w) {
    int x = 0, i = 0, brk = 0;
    while (s[i] && s[i] != '\n' && s[i] != '|') {
        int a = vwf_advance((u8)s[i]);
        if (s[i] == ' ')
            brk = i;
        if (x + a - 1 > w && s[i] != ' ')
            return brk ? brk : (i ? i : 1);
        x += a;
        i++;
    }
    return i;
}

int vwf_block(Canvas* c, int x, int y, int w, int pitch, const char* s, int ink, int lines) {
    int n = 0, cur = ink;
    while (*s && n < lines) {
        int len = vwf_fit(s, w), i, px = x;
        for (i = 0; i < len; i++) {
            u8 ch = (u8)s[i];
            if (ch < ' ')
                cur = vwf_ink(ch, ink);
            else if (!(ch == ' ' && px == x))
                px += vwf_glyph(c, px, y, ch, cur);
        }
        s += len;
        while (*s == ' ' || *s == '\n')
            s++;
        y += pitch;
        n++;
    }
    return n;
}

void vwf_flush(Canvas* c, bool8 now) {
    vu16* dst = c->obj ? OBJ_TILE(c->tile) : CHARBLOCK(2) + c->tile * 16;
    u32 bytes = c->tw * c->th * 32;
    if (!bytes)
        return;
    if (now)
        dma3_copy32(c->px, dst, bytes);
    else
        vram_queue(c->px, dst, bytes);
}

void vwf_map(const Canvas* c, u16* map, int tx, int ty, int pal) {
    int x, y;
    for (y = 0; y < c->th; y++)
        for (x = 0; x < c->tw; x++)
            if (tx + x >= 0 && tx + x < 32 && ty + y >= 0 && ty + y < 32)
                map[(ty + y) * 32 + tx + x] = (c->tile + y * c->tw + x) | (pal << 12);
}

char* vwf_num(char* buf, int n, int width) {
    char tmp[8];
    int i = 0, k = 0;
    if (n < 0)
        n = 0;
    do {
        tmp[i++] = '0' + n % 10;
        n /= 10;
    } while (n && i < 7);
    while (i + k < width && k < 7)
        buf[k++] = ' ';
    while (i)
        buf[k++] = tmp[--i];
    buf[k] = 0;
    return buf;
}
