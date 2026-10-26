/* BARTGAME: the people of the drain and the wood, and their quests.

   The Sage of the Drain explains. The Merchant sells. In the wood, the
   Hermit Knight asks for a glade cleared, the Weeping Nun for her relic
   from another chamber, the Blind Gardener for his four censers lit.
   Every quest reward is a pickup at the giver's feet or a text-given
   gift, and every quest is optional: the critical path needs none. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "text.h"
#include "world.h"
#include "roomgen.h"
#include "enemy.h"
#include "objects.h"
#include "react.h"
#include "game.h"
#include "npc.h"
#include "myst.h"

static Actor* sTalking;
static u8 sDlgState; /* 0 none, 1 text, 2 shop menu, 3 after-menu text */
static u8 sPendingReward;

static const u8 sFrames[NPC_COUNT] = { F_NPC_SAGE, F_NPC_MERCHANT, F_NPC_HERMIT, F_NPC_NUN, F_NPC_GARDENER, F_NPC_HERMIT };

/* ------------------------------------------------ the hub's two keepers --
   The Peddler behind his counter and the Gatekeeper on her rug are drawn
   large and by hand (art/sw_folk.py), and kept busy. He breathes and
   blinks and watches the hero come; between customers he spins a coin and
   slaps it flat, rubs his hands, drums his fingers (his acts, steps of
   body and face from the art). She breathes and blinks, now and then
   kindles a light over her palm, and the wisp over her orb burns while
   its glow pulses in two entries of her palette. Each sprite's frames
   stream into tiles held for it, queued for the VBlank like the hero's,
   so a whole repertoire costs the VRAM of one frame. */
#define KEEPER_BLINK 6
static Rng sKeepRng;

static struct {
    Actor* a;
    u16 head_tile, body_tile;
    u8 head, body;          /* the frames in the tiles */
    const u8* step;         /* the act in hand, or NULL */
    u8 t, act;
    u16 idle, blink_in;
    u8 blink;
} sPed;

static struct {
    Actor* a;
    u16 tile, wisp_tile;
    u8 frame;               /* the frame in the tiles */
    u16 idle, blink_in;
    u8 kindle, blink, glow;
} sGate;

/* a frame into a sprite's held tiles: at once, or at the next VBlank */
static void keeper_frame(int sheet, int frame, u16 tile, bool8 now) {
    const SpriteSheet* sh = &sheets[sheet];
    const u16* src = sh->tiles + frame * sh->frame_tiles * 16;
    if (now)
        dma3_copy32(src, OBJ_TILE(tile), sh->frame_tiles * 32);
    else
        vram_queue(src, OBJ_TILE(tile), sh->frame_tiles * 32);
}

static void keeper_spawn(Actor* a) {
    rng_seed(&sKeepRng, 0x6B33 + a->type);
    if (a->type == NPC_MERCHANT) {
        sPed.a = a;
        sPed.head_tile = sprite_alloc(sheets[SHEET_PEDDLER_HEAD].frame_tiles);
        sPed.body_tile = sprite_alloc(sheets[SHEET_PEDDLER_BODY].frame_tiles);
        sPed.head = F_PEDDLER_HEAD_OPEN;
        sPed.body = F_PEDDLER_BODY_REST;
        keeper_frame(SHEET_PEDDLER_HEAD, sPed.head, sPed.head_tile, TRUE);
        keeper_frame(SHEET_PEDDLER_BODY, sPed.body, sPed.body_tile, TRUE);
        sPed.step = NULL;
        sPed.idle = 150;
        sPed.blink_in = 90;
        sPed.blink = 0;
        actor_set_sheet(a, SHEET_PEDDLER_BODY, sPed.body_tile);
    } else {
        sGate.a = a;
        sGate.tile = sprite_alloc(sheets[SHEET_GATEKEEPER].frame_tiles);
        sGate.wisp_tile = sprite_load_sheet(SHEET_WISP);
        sGate.frame = F_GATEKEEPER_IDLE;
        keeper_frame(SHEET_GATEKEEPER, sGate.frame, sGate.tile, TRUE);
        sGate.idle = 240;
        sGate.blink_in = 50;
        sGate.blink = sGate.kindle = sGate.glow = 0;
        actor_set_sheet(a, SHEET_GATEKEEPER, sGate.tile);
    }
}

/* blinks come every few seconds, a few frames long */
static bool8 keeper_blinks(u16* blink_in, u8* blink) {
    if (*blink) {
        (*blink)--;
        return TRUE;
    }
    if (*blink_in && --*blink_in)
        return FALSE;
    *blink = KEEPER_BLINK;
    *blink_in = 150 + rng_range(&sKeepRng, 150);
    return TRUE;
}

static void peddler_update(void) {
    Actor* a = sPed.a;
    bool8 talking = sTalking == a && sDlgState;
    u8 body = F_PEDDLER_BODY_REST, face = F_PEDDLER_HEAD_OPEN;
    if (talking) {
        /* a customer: his business waits, and he grins over his wares */
        sPed.step = NULL;
        sPed.idle = 120;
        if (sDlgState == 2)
            face = F_PEDDLER_HEAD_GRIN;
    } else if (sPed.step) {
        body = sPed.step[0];
        face = sPed.step[1];
        if (++sPed.t >= sPed.step[2]) {
            sPed.t = 0;
            sPed.step += 3;
            if (!sPed.step[2]) {
                sPed.step = NULL;
                sPed.idle = 180 + rng_range(&sKeepRng, 240);
            }
        }
    } else if (!--sPed.idle) {
        /* the coin twice as often as the rest, never the same act twice */
        static const u8 kActs[4] = { 0, 1, 0, 2 };
        u8 act;
        do
            act = kActs[rng_range(&sKeepRng, 4)];
        while (act == sPed.act && act != 0);
        sPed.act = act;
        sPed.step = &peddler_acts[peddler_act_at[act]];
        sPed.t = 0;
    }
    /* his eyes follow the hero round to his left */
    if (face == F_PEDDLER_HEAD_OPEN && PX(gPlayer->x) < PX(a->x) - 24 && PX(gPlayer->y) < PX(a->y) + 96)
        face = F_PEDDLER_HEAD_LEFT;
    if (keeper_blinks(&sPed.blink_in, &sPed.blink) && face != F_PEDDLER_HEAD_GRIN)
        face = F_PEDDLER_HEAD_BLINK;
    if (face != sPed.head) {
        sPed.head = face;
        keeper_frame(SHEET_PEDDLER_HEAD, face, sPed.head_tile, FALSE);
    }
    if (body != sPed.body) {
        sPed.body = body;
        keeper_frame(SHEET_PEDDLER_BODY, body, sPed.body_tile, FALSE);
    }
}

static void gatekeeper_update(void) {
    bool8 talking = sTalking == sGate.a && sDlgState;
    u8 frame;
    if (sGate.kindle) {
        sGate.kindle--;
    } else if (!talking && !--sGate.idle) {
        sGate.kindle = 80;
        sGate.idle = 300 + rng_range(&sKeepRng, 300);
    }
    if (sGate.kindle)
        frame = F_GATEKEEPER_KINDLE;
    else
        frame = ((gFrame + 40) & 64) ? F_GATEKEEPER_BREATH : F_GATEKEEPER_IDLE;
    if (keeper_blinks(&sGate.blink_in, &sGate.blink))
        frame++; /* each pose's blink follows it */
    if (frame != sGate.frame) {
        sGate.frame = frame;
        keeper_frame(SHEET_GATEKEEPER, frame, sGate.tile, FALSE);
    }
    /* the orb's glow: a step every eight frames, held at its brightest
       while her own light burns */
    if (!(gFrame & 7)) {
        u8 g = sGate.kindle ? ORB_GLOW_STEPS / 2 : (sGate.glow + 1) % ORB_GLOW_STEPS;
        sGate.glow = g;
        gPalObj[PAL_OBJ_GATEKEEPER * 16 + ORB_GLOW_INDEX] = orb_glow[g * 2];
        gPalObj[PAL_OBJ_GATEKEEPER * 16 + ORB_GLOW_INDEX + 1] = orb_glow[g * 2 + 1];
        gPalDirty = 1;
    }
}

/* his head over his body, breathing; her wisp over her */
static void peddler_draw(void) {
    Actor* a = sPed.a;
    int sx = PX(a->x) - 32 - gCamX, sy = PX(a->y) - gCamY;
    int breath = ((gFrame + 17) >> 6) & 1;
    if (!sPed.head_tile || !sPed.body_tile)
        return; /* no tiles to hold him: better unseen than drawn from another's */
    draw_sprite(sx, sy - 48 + breath, SHEET_PEDDLER_HEAD, sPed.head_tile, 0, 0, a->prio, PAL_OBJ_PEDDLER);
    draw_sprite(sx, sy - 32, SHEET_PEDDLER_BODY, sPed.body_tile, 0, 0, a->prio, PAL_OBJ_PEDDLER);
}

static void gatekeeper_draw(void) {
    Actor* a = sGate.a;
    int sx = PX(a->x) - 32 - gCamX, sy = PX(a->y) - 64 - gCamY;
    if (!sGate.tile || !sGate.wisp_tile)
        return;
    draw_sprite(sx + WISP_X, sy + WISP_Y, SHEET_WISP, sGate.wisp_tile, (gFrame / 6) & 3, 0, a->prio, PAL_OBJ_GATEKEEPER);
    draw_sprite(sx, sy, SHEET_GATEKEEPER, sGate.tile, 0, 0, a->prio, PAL_OBJ_GATEKEEPER);
}

Actor* npc_spawn(int type, int px, int py) {
    Actor* a = actor_new(AK_NPC, type, px, py);
    gDbg[0]++;
    gDbg[1] = (u32)a;
    if (!a)
        return NULL;
    if (type == NPC_SAGE || type == NPC_MERCHANT) {
        keeper_spawn(a);
    } else {
        /* the folk of the wood: only their own frame is resident */
        actor_set_sheet(a, SHEET_NPC, sprite_load_frame(SHEET_NPC, sFrames[type]));
        a->frame = 0;
    }
    gDbg[3] = a->kind;
    a->hitbox = HB_TALL;
    a->flags = AF_SOLID;
    a->prio = 2;
    return a;
}

void npc_room_reset(void) {
    sPed.a = NULL;
    sGate.a = NULL;
    sTalking = NULL;
    sDlgState = 0;
}

void npcs_update(void) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        if (a->kind != AK_NPC)
            continue;
        if (a == sPed.a)
            peddler_update();
        else if (a == sGate.a)
            gatekeeper_update();
        else
            a->z = ((gFrame + i * 20) & 32) ? 0 : Q16(1); /* a slow breathing bob */
        /* keep the hero out of them */
        if (actors_overlap(a, gPlayer) && gPlayer->state != PS_HURT) {
            int d = actor_dir_to(a, gPlayer);
            actor_move(gPlayer, Q8(1.0), d);
        }
    }
}

/* the folk nearer the viewer than the hero are drawn before him, so over
   him; the rest after */
static void npcs_draw_pass(bool8 front) {
    int i, hy = PX(gPlayer->y);
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        if (a->kind != AK_NPC || (PX(a->y) > hy) != front)
            continue;
        if (a == sPed.a)
            peddler_draw();
        else if (a == sGate.a)
            gatekeeper_draw();
        else
            actor_draw(a);
    }
}

void npcs_draw_front(void) {
    npcs_draw_pass(TRUE);
}

void npcs_draw(void) {
    npcs_draw_pass(FALSE);
}

/* the NPC the hero faces, within reach */
static Actor* npc_facing(void) {
    Actor* p = gPlayer;
    int px = PX(p->x), py = PX(p->y) - 10;
    int i;
    switch (p->facing) {
        case FACE_N: py -= 18; break;
        case FACE_S: py += 18; break;
        case FACE_E: px += 18; break;
        default: px -= 18; break;
    }
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        if (a->kind != AK_NPC)
            continue;
        if (actor_box_overlap(a, px - 6, py - 6, px + 6, py + 6))
            return a;
    }
    return NULL;
}

/* -------------------------------------------------------- dialogue -- */
static const char* dir_words(int from, int to) {
    int dx = cell_x(to) - cell_x(from), dy = cell_y(to) - cell_y(from);
    if (dy < 0 && dx < 0) return "north and west";
    if (dy < 0 && dx > 0) return "north and east";
    if (dy > 0 && dx < 0) return "south and west";
    if (dy > 0 && dx > 0) return "south and east";
    if (dy < 0) return "north";
    if (dy > 0) return "south";
    if (dx < 0) return "west";
    if (dx > 0) return "east";
    return "here";
}

static char sBuf[200];
static void bufcat(const char* s) {
    int n = 0;
    while (sBuf[n])
        n++;
    while (*s && n < 198)
        sBuf[n++] = *s++;
    sBuf[n] = 0;
}

static void reward_drop(Actor* a, int kind) {
    int px = PX(a->x), py = PX(a->y) + 10;
    pickup_spawn(kind, px, py);
}

/* who speaks: a name in gold and a portrait beside the words */
static const char* const sNames[NPC_COUNT] = {
    "The Pale Gatekeeper", "The Billious Peddler", "The Hermit Knight", "The Weeping Nun", "The Blind Gardener", "A Stranger"
};
static const u8 sPortraits[NPC_COUNT] = {
    F_PORTRAIT_GATEKEEPER, F_PORTRAIT_PEDDLER, F_PORTRAIT_HERMIT, F_PORTRAIT_NUN, F_PORTRAIT_GARDENER, F_PORTRAIT_HERMIT
};

static void start_text(const char* s) {
    int who = sTalking ? sTalking->type : NPC_SAGE;
    textbox_open_named(sNames[who], sPortraits[who], s);
    sDlgState = 1;
}

static void talk_sage(void) {
    Cell* goal = &gWorld.cells[gWorld.goal];
    (void)goal;
    if (!(gPl.items & ITEM_BOMBS))
        start_text("Ahh... you bloomed. In the muck, from a seed the dead king swallowed.|The wood above has taken the blight into its heart. Three doors it keeps: one cracked, one webbed, one a chasm.|What opens them lies in chests before them. Cut what you can. R rolls. Go up the drain, little bloom.");
    else if (!(gPl.items & ITEM_CLOAK))
        start_text("The blight keeps its keys close to its locks. Look for chests in the dead ends. The wood is a maze, but every maze is a tree.");
    else
        start_text("You carry the seed, the flame and the petal. The Heart waits in the deepest glade. Cut it out.");
}

static const ShopItem sShop[3] = {
    { "Healing Petal", "A preserved bloom. It", "restores two hearts.", 10, F_ITEMS_HEART },
    { "Blightseeds x5", "Five seeds that burst and", "open cracked walls.", 15, F_ITEMS_BOMBS },
    { "Arrows x10", "Thorn-tipped, fletched with", "crow. For the bow.", 10, F_ITEMS_ARROW10 },
};

/* the third ware, arrows, is on the counter once the hero has the bow */
static void talk_merchant(void) {
    shop_open("The Billious Peddler", sShop, (gPl.items2 & ITEM2_BOW) ? 3 : 2);
    sDlgState = 2;
}

static void finish_shop(int choice) {
    if (choice == 0) {
        if (gPl.gilt >= 10) {
            gPl.gilt -= 10;
            player_heal(16);
            sfx_play(SFX_HEART);
            start_text("Hmph. Chew it, don't savour it. Nothing comes for free in the sewers, little petal.");
        } else {
            start_text("Ten gilt. You have less. Look with your eyes, not your hands.");
        }
    } else if (choice == 1) {
        if (!(gPl.items & ITEM_BOMBS)) {
            start_text("Seeds? You would not know how to plant them. Find the chest first.");
        } else if (gPl.gilt >= 15) {
            gPl.gilt -= 15;
            gPl.bombs += 5;
            if (gPl.bombs > 30)
                gPl.bombs = 30;
            sfx_play(SFX_PICKUP);
            start_text("Five seeds. Keep them from the damp.");
        } else {
            start_text("Fifteen gilt. The dead pay better than you. Everything here is mine, and it stays mine.");
        }
    } else if (choice == 2) {
        if (gPl.gilt >= 10) {
            gPl.gilt -= 10;
            gPl.arrows += 10;
            if (gPl.arrows > 50)
                gPl.arrows = 50;
            sfx_play(SFX_PICKUP);
            start_text("Ten arrows. Aim for the soft parts. Everything has soft parts.");
        } else {
            start_text("Ten gilt the bundle. Come back when the dead have paid you.");
        }
    } else {
        sDlgState = 0;
    }
}

static void talk_hermit(Actor* a) {
    Cell* c = &gWorld.cells[gGame.cell];
    if (c->flags & CF_QUEST_DONE) {
        start_text("The glade is quiet. I will sit here until the roots take me. Go.");
        return;
    }
    if (!(c->flags & CF_QUEST_ACTIVE)) {
        c->flags |= CF_QUEST_ACTIVE;
        start_text("I was a knight of the Grail before the wood rotted. My sword is rust.|Slay every beast in this glade. I will pay what a knight can still pay.");
        return;
    }
    if (enemies_alive() == 0) {
        c->flags |= CF_QUEST_DONE;
        sPendingReward = 1;
        reward_drop(a, PK_KEY);
        reward_drop(a, PK_GILT_BIG);
        reward_drop(a, PK_GILT_BIG);
        start_text("Dead, all of them. Take the key I kept for a door I never found, and the gilt.");
        sfx_play(SFX_SECRET);
        return;
    }
    start_text("They still breathe. I can hear them chewing.");
}

static void talk_nun(Actor* a) {
    Cell* c = &gWorld.cells[gGame.cell];
    if (c->flags & CF_QUEST_DONE) {
        start_text("Bless you. The relic weeps now so that I need not.");
        return;
    }
    if (gPl.items & ITEM_RELIC) {
        c->flags |= CF_QUEST_DONE;
        gPl.items &= ~ITEM_RELIC;
        gPl.hp_max += 8;
        gPl.hp = gPl.hp_max;
        sfx_play(SFX_SECRET);
        start_text("My relic! Here, the only gift I have: a heart that was once a saint's.|It beats on your stalk now. A HEART CONTAINER.");
        return;
    }
    c->flags |= CF_QUEST_ACTIVE;
    sBuf[0] = 0;
    bufcat("I wept and the relic slipped from my hands into the chamber to the ");
    bufcat(dir_words(gGame.cell, c->role_arg));
    bufcat(" of here. Bring it back and I will give you what I have.");
    start_text(sBuf);
    (void)a;
}

static void talk_gardener(Actor* a) {
    Cell* c = &gWorld.cells[gGame.cell];
    if (c->flags & CF_QUEST_DONE) {
        start_text("I can feel the warmth of the censers on my face. Thank you, child of the stalk.");
        return;
    }
    if (room_torches_unlit() == 0) {
        c->flags |= CF_QUEST_DONE;
        reward_drop(a, PK_KEY);
        reward_drop(a, PK_GILT_BIG);
        sfx_play(SFX_SECRET);
        start_text("All four burn. I kept a key in the ash for the one who would light them. Take it.");
        return;
    }
    c->flags |= CF_QUEST_ACTIVE;
    if (gPl.items & ITEM_LAMP)
        start_text("Four censers stand cold in this garden. I cannot see to light them. Your lamp can.");
    else
        start_text("Four censers stand cold in this garden. Somewhere in the wood is a flame that is not of this wood. Bring it.");
}

/* the stranger in a mystery room: a piece of heart for ten gilt, once */
static void talk_stranger(Actor* a) {
    (void)a;
    if (myst_done()) {
        start_text("I have nothing more. The wood has nothing more. Go on, little petal.");
        return;
    }
    if (myst_stranger_trade())
        start_text("Ten gilt, and a piece of a heart that was somebody's. Fair, I'd say.|It beats a little on your stalk. A PIECE OF HEART.");
    else
        start_text("I sell pieces of hearts. Ten gilt the piece. You have less. Come back heavier.");
}

bool8 npc_try_talk(void) {
    Actor* a = npc_facing();
    if (!a || gPlayer->state != PS_NORMAL)
        return FALSE;
    sTalking = a;
    /* the NPC turns to face the hero */
    gPlayer->speed = 0;
    switch (a->type) {
        case NPC_SAGE: talk_sage(); break;
        case NPC_MERCHANT: talk_merchant(); break;
        case NPC_HERMIT: talk_hermit(a); break;
        case NPC_NUN: talk_nun(a); break;
        case NPC_GARDENER: talk_gardener(a); break;
        case NPC_STRANGER: talk_stranger(a); break;
    }
    return TRUE;
}

bool8 npc_dialogue_active(void) {
    return sDlgState != 0;
}

void npc_dialogue_update(void) {
    if (sDlgState != 2)
        textbox_update();
    if (sDlgState == 2) {
        int r;
        shop_update();
        r = shop_result();
        if (r == -2)
            return;
        shop_close();
        finish_shop(r);
        return;
    }
    if (!textbox_active())
        sDlgState = 0;
}
