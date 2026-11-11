/* BARTGAME: what the world does when struck, burned, blown up, unlocked. */
#include "gba.h"
#include "util.h"
#include "room.h"
#include "world.h"
#include "roomgen.h"
#include "player.h"
#include "sound.h"
#include "objects.h"
#include "game.h"
#include "react.h"
#include "myst.h"
#include "cream_room.h"
#include "handoff_events.h"
#include "text.h"

static u32 sTrialWarningFrame;
static u8 sTrialWarningShown;
static bool8 trial_gate_blocked(int side) {
    if(side<0||world_trial_gate_ready(gGame.cell,side))return FALSE;
    if(!sTrialWarningShown || gGame.run_frames-sTrialWarningFrame>60) {
        sTrialWarningShown=1;sTrialWarningFrame=gGame.run_frames;
        textbox_open("A trial seal holds this crossing.|Complete this wood's required task and claim its prize. A tool found elsewhere does not break the oath.");
    }
    sfx_play(SFX_BUMP);return TRUE;
}

static void tile_cleared(int tx,int ty) {
    if(gGame.area==AREA_MYST) myst_tile_cleared(tx,ty);
    if(gGame.area==AREA_CREAM) cream_room_gate_cleared(tx,ty);
    handoff_tile_cleared(tx,ty);
}

/* If the tile is part of a door opening, which side. -1 otherwise. */
int tile_gate_side(int tx, int ty) {
    int s, x0, y0, x1, y1;
    if (gGame.area != AREA_FOREST)
        return -1;
    for (s = 0; s < 4; s++) {
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        if ((tx == x0 && ty == y0) || (tx == x1 && ty == y1))
            return s;
    }
    return -1;
}

/* the room's trail and plain ground: the blight's own in a blighted room */
static bool8 blighted_here(void) {
    return gGame.area == AREA_FOREST && roomgen_blighted(gGame.cell);
}

static u16 trail_here(void) {
    return blighted_here() ? MT_BLIGHT_VEIN : MT_PATH;
}

static u16 ground_here(int tx, int ty) {
    if(gGame.area==AREA_CREAM) return cream_room_floor(tx,ty);
    return blighted_here() ? MT_BLIGHT_FLOOR : MT_MOSS0 + (hash32(tx, ty) % 3);
}

static void open_gate_tiles(int side, u16 mt) {
    int x0, y0, x1, y1;
    roomgen_gate_tiles(side, &x0, &y0, &x1, &y1);
    room_change(x0, y0, mt);
    room_change(x1, y1, mt);
    world_open_gate(gGame.cell, side);
}

void room_crack_open(int tx, int ty) {
    int side = tile_gate_side(tx, ty);
    if(trial_gate_blocked(side))return;
    if (side >= 0)
        open_gate_tiles(side, MT_DOOR_OPEN);
    else {
        room_change(tx, ty, gGame.area==AREA_CREAM?cream_room_floor(tx,ty):trail_here());
        if (gGame.area == AREA_FOREST && gSpots.has_treasure &&
            tx == gSpots.pocket_gate.x && ty == gSpots.pocket_gate.y && gSpots.pocket_kind == 1)
            gWorld.cells[gGame.cell].opened |= CELL_POCKET_OPEN;
    }
    fx_spawn(FX_PUFF, tx * 16 + 8, ty * 16 + 8);
    sfx_play(SFX_SECRET);
    tile_cleared(tx,ty);
}

void room_web_burn(int tx, int ty) {
    int side = tile_gate_side(tx, ty);
    if(trial_gate_blocked(side))return;
    if (side >= 0)
        open_gate_tiles(side, trail_here());
    else {
        room_change(tx, ty, gGame.area==AREA_CREAM?cream_room_floor(tx,ty):trail_here());
        if (gGame.area == AREA_FOREST && gSpots.has_treasure &&
            tx == gSpots.pocket_gate.x && ty == gSpots.pocket_gate.y && gSpots.pocket_kind == 2)
            gWorld.cells[gGame.cell].opened |= CELL_POCKET_OPEN;
    }
    fx_spawn(FX_FLAME, tx * 16 + 8, ty * 16 + 8);
    sfx_play(SFX_LAMP);
    tile_cleared(tx,ty);
}

bool8 room_door_unlock(int tx, int ty) {
    int side = tile_gate_side(tx, ty);
    if (gPl.keys == 0)
        return FALSE;
    gPl.keys--;
    if (side >= 0)
        open_gate_tiles(side, MT_DOOR_OPEN);
    else
        room_change(tx, ty, MT_DOOR_OPEN);
    sfx_play(SFX_DOOR);
    tile_cleared(tx,ty);
    return TRUE;
}

void room_torch_light(int tx, int ty) {
    room_change(tx, ty, gGame.area==AREA_CREAM?MT_CREAM_LAMP_LIT:MT_TORCH_LIT);
    fx_spawn(FX_FLAME, tx * 16 + 8, ty * 16);
    sfx_play(SFX_LAMP);
}

void room_thorn_cut(int tx, int ty) {
    /* a hedge cut leaves grass; a gate of thorns, the trail it closed */
    room_change(tx, ty, tile_gate_side(tx, ty) >= 0 ? trail_here() : ground_here(tx, ty));
    fx_spawn(FX_PUFF, tx * 16 + 8, ty * 16 + 8);
    if ((hash32(gGame.run_frames, tx * 7 + ty) & 7) == 0)
        drop_roll(tx * 16 + 8, ty * 16 + 12, hash32(ty, tx));
    tile_cleared(tx,ty);
}

/* what lies under a bush or a stone: in the wood, its grass (its tiles
   beside may be edges of something); elsewhere the floor beside it */
static u16 ground_under(int tx, int ty) {
    static const s8 d[4][2] = { { 0, 1 }, { -1, 0 }, { 1, 0 }, { 0, -1 } };
    int i;
    if (gGame.area == AREA_FOREST)
        return ground_here(tx, ty);
    if (gGame.area == AREA_MYST)
        return myst_ground(tx, ty);
    if (gGame.area == AREA_CREAM)
        return cream_room_floor(tx,ty);
    for (i = 0; i < 4; i++) {
        u16 m = room_get(tx + d[i][0], ty + d[i][1]);
        if (m != MT_NONE && metatile_type[m] == TT_FLOOR && m != MT_BRIDGE && m != MT_PATH)
            return m;
    }
    return MT_MOSS0 + (hash32(tx, ty) % 3);
}

/* lifts a bush, a pot or a stone off its tile; returns what is carried */
int room_lift(int tx, int ty) {
    u16 mt = room_get(tx, ty);
    bool8 pot = (mt == MT_SW_POT || mt == MT_CAVE_FLOOR_LIFT || mt == MT_HOLLOW_FLOOR_LIFT || mt == MT_THICKET_FLOOR_LIFT);
    int kind = (mt == MT_BUSH) ? CARRY_BUSH : pot ? CARRY_POT : (mt == MT_BOULDER) ? CARRY_BOULDER : CARRY_ROCK;
    room_change(tx, ty, ground_under(tx, ty));
    room_change_overlay(tx, ty, MT_NONE); /* a mystery's pot is drawn on the overlay */
    tile_cleared(tx, ty);
    return kind;
}

/* a bush cut or a pot smashed where it stands */
void room_break_lift(int tx, int ty) {
    u16 mt = room_get(tx, ty);
    room_change(tx, ty, ground_under(tx, ty));
    room_change_overlay(tx, ty, MT_NONE);
    fx_spawn(FX_PUFF, tx * 16 + 8, ty * 16 + 8);
    tile_cleared(tx, ty);
    if ((mt == MT_BUSH || mt == MT_SW_POT) && (hash32(gGame.run_frames, tx * 7 + ty) & 3) == 0)
        drop_roll(tx * 16 + 8, ty * 16 + 12, hash32(ty, tx));
}

void react_cut_box(int x0, int y0, int x1, int y1) {
    int tx, ty;
    for (ty = y0 >> 4; ty <= (y1 >> 4); ty++)
        for (tx = x0 >> 4; tx <= (x1 >> 4); tx++) {
            if (room_type(tx, ty) == TT_THORN)
                room_thorn_cut(tx, ty);
            else if (room_type(tx, ty) == TT_LIFT1 && room_get(tx, ty) == MT_BUSH)
                room_break_lift(tx, ty);
        }
}

void react_burn_box(int x0, int y0, int x1, int y1) {
    int tx, ty;
    for (ty = y0 >> 4; ty <= (y1 >> 4); ty++)
        for (tx = x0 >> 4; tx <= (x1 >> 4); tx++) {
            u8 t = room_type(tx, ty);
            if (t == TT_WEB)
                room_web_burn(tx, ty);
            else if (t == TT_TORCH)
                room_torch_light(tx, ty);
            else if (t == TT_THORN)
                room_thorn_cut(tx, ty);
        }
}

u8 gRoomTorchesDirty=1;
static s16 sUnlitTorches;

int room_torches_unlit(void) {
    if(!gRoomTorchesDirty)return sUnlitTorches;
    int x, y, n = 0;
    for (y = 0; y < gRoom.h; y++)
        for (x = 0; x < gRoom.w; x++)
            if (room_type(x, y) == TT_TORCH)
                n++;
    sUnlitTorches=n;gRoomTorchesDirty=0;
    return n;
}
