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

static u16 sNpcTile;
static Actor* sTalking;
static u8 sDlgState; /* 0 none, 1 text, 2 shop menu, 3 after-menu text */
static u8 sPendingReward;

static const u8 sFrames[NPC_COUNT] = { F_NPC_SAGE, F_NPC_MERCHANT, F_NPC_HERMIT, F_NPC_NUN, F_NPC_GARDENER };

Actor* npc_spawn(int type, int px, int py) {
    if (!sNpcTile)
        sNpcTile = sprite_load_sheet(SHEET_NPC);
    Actor* a = actor_new(AK_NPC, type, px, py);
    gDbg[0]++;
    gDbg[1] = (u32)a;
    gDbg[2] = sNpcTile;
    if (!a)
        return NULL;
    actor_set_sheet(a, SHEET_NPC, sNpcTile);
    gDbg[3] = a->kind;
    a->frame = sFrames[type];
    a->hitbox = HB_TALL;
    a->flags = AF_SOLID;
    a->prio = 2;
    return a;
}

void npc_room_reset(void) {
    sNpcTile = 0;
    sTalking = NULL;
    sDlgState = 0;
}

void npcs_update(void) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        if (a->kind != AK_NPC)
            continue;
        /* a slow breathing bob */
        a->z = ((gFrame + i * 20) & 32) ? 0 : Q16(1);
        /* keep the hero out of them */
        if (actors_overlap(a, gPlayer) && gPlayer->state != PS_HURT) {
            int d = actor_dir_to(a, gPlayer);
            actor_move(gPlayer, Q8(1.0), d);
        }
    }
}

void npcs_draw(void) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++)
        if (gActors[i].kind == AK_NPC)
            actor_draw(&gActors[i]);
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

static void start_text(const char* s) {
    textbox_open(s);
    sDlgState = 1;
}

static void talk_sage(void) {
    Cell* goal = &gWorld.cells[gWorld.goal];
    (void)goal;
    if (!(gPl.items & ITEM_BOMBS))
        start_text("You grew in the muck, stalk-child, from a seed the dead king swallowed.|The wood above has taken the blight into its heart. Three doors it keeps: one cracked, one webbed, one a chasm.|What opens them lies in chests before them. Cut what you can with the sword. R rolls. Go up the drain.");
    else if (!(gPl.items & ITEM_CLOAK))
        start_text("The blight keeps its keys close to its locks. Look for chests in the dead ends. The wood is a maze, but every maze is a tree.");
    else
        start_text("You carry the seed, the flame and the petal. The Heart waits in the deepest glade. Cut it out.");
}

static const char* const sShopOpts[2] = { "A heart potion, 10 gilt", "Five blightseeds, 15 gilt" };

static void talk_merchant(void) {
    textbox_open_menu("Gilt for the living. What will you buy?", sShopOpts, 2);
    sDlgState = 2;
}

static void finish_shop(int choice) {
    if (choice == 0) {
        if (gPl.gilt >= 10) {
            gPl.gilt -= 10;
            player_heal(16);
            sfx_play(SFX_HEART);
            start_text("Drink. The wood does not care if you bleed, but I do, a little.");
        } else {
            start_text("Ten gilt. You have less. Come back with pockets.");
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
            start_text("Fifteen gilt. The dead pay better than you.");
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
    }
    return TRUE;
}

bool8 npc_dialogue_active(void) {
    return sDlgState != 0;
}

void npc_dialogue_update(void) {
    textbox_update();
    if (sDlgState == 2) {
        int r = textbox_menu_result();
        if (r == -2)
            return;
        textbox_close();
        finish_shop(r);
        return;
    }
    if (!textbox_active())
        sDlgState = 0;
}
