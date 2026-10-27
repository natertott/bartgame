/* BARTGAME: the maze generator.

   1. A spanning tree over the 5x5 grid (randomized depth-first, biased to
      long corridors), entry at the bottom middle.
   2. The goal is the tree's farthest cell. The entry-to-goal path gets the
      three key gates in order: crack (Blightseed Bombs), web (Grail Lamp),
      chasm (Petal Cloak). Each key item is placed in a room reachable
      BEFORE its gate, so the critical path is always solvable, by
      construction. QUICKSTART's lesson: never leave a key to a random
      draw.
   3. Side branches get locked doors whose small keys sit in rooms that
      need no key at all, so two keys can never deadlock; no lock ever
      stands between the entry and a key item, a key chest or the goal.
   4. Dead ends get chests, quest givers, relics and shrines. A few extra
      edges within one stage make loops.
   5. Every room gets an archetype, an enemy theme and a density that grows
      with the stage. */
#include "gba.h"
#include "world.h"
#include "myst.h"

World gWorld EWRAM_BSS;
u8 gWorldGenerationAttempts;
u8 gWorldGenerationFallback;

static const s8 sDx[4] = { 0, 1, 0, -1 };
static const s8 sDy[4] = { -1, 0, 1, 0 };

int cell_x(int cell) {
    return cell % MAZE_W;
}
int cell_y(int cell) {
    return cell / MAZE_W;
}

int cell_neighbor(int cell, int side) {
    int x = cell_x(cell) + sDx[side], y = cell_y(cell) + sDy[side];
    if (x < 0 || y < 0 || x >= MAZE_W || y >= MAZE_H)
        return -1;
    return y * MAZE_W + x;
}

static int opposite(int side) {
    return (side + 2) & 3;
}

void world_open_gate(int cell, int side) {
    int n = cell_neighbor(cell, side);
    gWorld.cells[cell].opened |= 1 << side;
    if (n >= 0)
        gWorld.cells[n].opened |= 1 << opposite(side);
}

bool8 world_gate_open(int cell, int side) {
    return (gWorld.cells[cell].opened >> side) & 1;
}

const char* gate_name(int gate) {
    switch (gate) {
        case GATE_THORN: return "thorns";
        case GATE_CRACK: return "a cracked wall";
        case GATE_WEB: return "a pale web";
        case GATE_LOCK: return "a locked door";
        case GATE_CHASM: return "a chasm";
        default: return "nothing";
    }
}

/* ---------------------------------------------------------- the tree -- */
static u8 sTree[CELLS][4]; /* 1 where a tree edge exists */

static void tree_build(Rng* r, int entry) {
    u8 visited[CELLS];
    u8 stack[CELLS];
    int sp = 0, i;
    memset(visited, 0, sizeof(visited));
    memset(sTree, 0, sizeof(sTree));
    visited[entry] = 1;
    stack[sp++] = entry;
    int last_dir = -1;
    while (sp) {
        /* a growing tree: mostly grow from the newest cell (corridors),
           but a third of the time from any open cell (branches, so the
           maze has side rooms and not one long hall) */
        int pick = sp - 1;
        if (sp > 1 && rng_range(r, 3) == 0) {
            pick = rng_range(r, sp);
            last_dir = -1;
        }
        int cur = stack[pick];
        int cand[4], nc = 0;
        for (i = 0; i < 4; i++) {
            int n = cell_neighbor(cur, i);
            if (n >= 0 && !visited[n])
                cand[nc++] = i;
        }
        if (nc == 0) {
            for (i = pick; i < sp - 1; i++)
                stack[i] = stack[i + 1];
            sp--;
            last_dir = -1;
            continue;
        }
        int d;
        /* keep going straight half the time: longer corridors */
        if (last_dir >= 0 && (rng_next(r) & 1)) {
            d = -1;
            for (i = 0; i < nc; i++)
                if (cand[i] == last_dir)
                    d = last_dir;
            if (d < 0)
                d = cand[rng_range(r, nc)];
        } else {
            d = cand[rng_range(r, nc)];
        }
        int n = cell_neighbor(cur, d);
        sTree[cur][d] = 1;
        sTree[n][opposite(d)] = 1;
        visited[n] = 1;
        stack[sp++] = n;
        last_dir = d;
    }
}

/* BFS distances through tree edges, with a blocked-gate mask per stage:
   passable(cell, side) decides. */
typedef bool8 (*PassFn)(int cell, int side);
static u8 sDist[CELLS];
static u8 sParent[CELLS];

static void flood(int start, PassFn pass) {
    u8 q[CELLS];
    int qh = 0, qt = 0, i;
    memset(sDist, 0xFF, sizeof(sDist));
    sDist[start] = 0;
    sParent[start] = 0xFF;
    q[qt++] = start;
    while (qh < qt) {
        int c = q[qh++];
        for (i = 0; i < 4; i++) {
            int n = cell_neighbor(c, i);
            if (n < 0 || !sTree[c][i] || sDist[n] != 0xFF)
                continue;
            if (pass && !pass(c, i))
                continue;
            sDist[n] = sDist[c] + 1;
            sParent[n] = c;
            q[qt++] = n;
        }
    }
}

static int sStageLimit; /* gates with index >= this block */
static bool8 pass_stage(int cell, int side) {
    int g = gWorld.cells[cell].gate[side];
    if (g == GATE_LOCK)
        return FALSE; /* keys never count toward item-gate reachability */
    if (g == GATE_CRACK && sStageLimit < 1)
        return FALSE;
    if (g == GATE_WEB && sStageLimit < 2)
        return FALSE;
    if (g == GATE_CHASM && sStageLimit < 3)
        return FALSE;
    return TRUE;
}

/* Does the subtree beyond `cell`, entered from `from`, hold a room the run
   depends on? A lock in front of one would strand the player. */
static bool8 subtree_holds_key(int cell, int from) {
    int s;
    u8 role = gWorld.cells[cell].role;
    if (role == ROLE_KEYITEM || role == ROLE_KEYCHEST || cell == gWorld.goal)
        return TRUE;
    for (s = 0; s < 4; s++) {
        int n = cell_neighbor(cell, s);
        if (n < 0 || n == from || !sTree[cell][s])
            continue;
        if (subtree_holds_key(n, cell))
            return TRUE;
    }
    return FALSE;
}

static int degree(int cell) {
    int i, n = 0;
    for (i = 0; i < 4; i++)
        n += sTree[cell][i];
    return n;
}

/* Pick a room for a role: reachable (sDist set), unused, preferring dead
   ends far from the entry. Returns -1 if none. */
static int pick_room(Rng* r, int exclude_goal) {
    int best = -1, best_score = -1, i;
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        if (sDist[i] == 0xFF || c->role != ROLE_NONE)
            continue;
        if (i == gWorld.entry || (exclude_goal && i == gWorld.goal))
            continue;
        int score = sDist[i] * 4 + (degree(i) == 1 ? 12 : 0) + (int)rng_range(r, 6);
        if (score > best_score) {
            best_score = score;
            best = i;
        }
    }
    return best;
}

/* The mysteries: two cells in five, never the entry, the goal or the
   gardener's dark garden. A size, a style, then a kind from the size's
   pool: the small pool is the quiet kinds and the gauntlets; the medium
   pool adds the plates and the censers; the large pool is mostly fights
   and the set pieces. Censers and boulders stand on grass: thickets. */
static void myst_generate(World* w, Rng* r) {
    int i;
    for (i = 0; i < CELLS; i++) {
        Cell* c = &w->cells[i];
        int size, style, roll, kind;
        w->myst[i] = 0;
        w->myst_flags[i] = 0;
        if (i == w->entry || i == w->goal || c->role == ROLE_NPC_TORCH)
            continue;
        if (rng_range(r, 10) >= 4)
            continue;
        roll = rng_range(r, 10);
        size = roll < 4 ? MS_SMALL : roll < 7 ? MS_MEDIUM : MS_LARGE;
        style = rng_range(r, 3);
        roll = rng_range(r, 16);
        if (size == MS_SMALL)
            kind = roll < 3 ? MK_POTS : roll < 6 ? MK_CHEST : roll < 9 ? MK_NPC : roll < 10 ? MK_FAIRY : roll < 14 ? MK_WAVES : MK_SURVIVE;
        else if (size == MS_MEDIUM)
            kind = roll < 2 ? MK_POTS : roll < 4 ? MK_CHEST : roll < 6 ? MK_NPC : roll < 7 ? MK_FAIRY : roll < 11 ? MK_WAVES : roll < 13 ? MK_SURVIVE : roll < 15 ? MK_SWITCHES : MK_TORCHES;
        else
            kind = roll < 4 ? MK_WAVES : roll < 6 ? MK_SURVIVE : roll < 10 ? MK_MINIBOSS : roll < 12 ? MK_SWITCHES : roll < 13 ? MK_TORCHES : roll < 14 ? MK_BOULDERS : roll < 15 ? MK_CHEST : MK_FAIRY;
        if (kind == MK_TORCHES || kind == MK_BOULDERS)
            style = MY_THICKET;
        w->myst[i] = MYST_PACK(kind, size, style);
    }
}

static bool8 world_candidate(u32 seed, u32 layout_seed, const WorldTuning* tuning) {
    Rng r;
    int i, s;
    World* w = &gWorld;
    memset(w, 0, sizeof(*w));
    w->seed = seed;
    rng_seed(&r, layout_seed);
    for (i = 0; i < CELLS; i++)
        for (s = 0; s < 4; s++)
            w->cells[i].gate[s] = GATE_WALL;
    w->entry = (MAZE_H - 1) * MAZE_W + MAZE_W / 2;
    tree_build(&r, w->entry);

    /* distances; the goal is the farthest cell (ties: lowest row) */
    flood(w->entry, NULL);
    int goal = w->entry, gd = -1;
    for (i = 0; i < CELLS; i++) {
        int d = sDist[i] * 8 - cell_y(i);
        if (sDist[i] != 0xFF && d > gd) {
            gd = d;
            goal = i;
        }
    }
    w->goal = goal;
    for (i = 0; i < CELLS; i++)
        w->cells[i].dist = sDist[i];
    /* the main path, entry..goal */
    {
        u8 rev[CELLS];
        int n = 0, c = goal;
        while (c != 0xFF && n < CELLS) {
            rev[n++] = c;
            c = sParent[c];
        }
        for (i = 0; i < n; i++)
            w->path[i] = rev[n - 1 - i];
        w->path_len = n;
    }
    /* Reject an unsuitable skeleton before spending time on roles, quests,
       loops and event assignment. Attempt zero is retained as a fallback. */
    if (tuning && (w->path_len - 1 < tuning->spine_min ||
                   w->path_len - 1 > tuning->spine_max))
        return FALSE;
    /* tree edges become open gates; thorns on some */
    for (i = 0; i < CELLS; i++)
        for (s = 0; s < 4; s++)
            if (sTree[i][s] && cell_neighbor(i, s) > i) {
                int n = cell_neighbor(i, s);
                int gate = (rng_range(&r, 5) == 0) ? GATE_THORN : GATE_OPEN;
                w->cells[i].gate[s] = gate;
                w->cells[n].gate[opposite(s)] = gate;
            }
    /* the exit back to the sewer */
    w->cells[w->entry].gate[SIDE_S] = GATE_EXIT;
    w->cells[w->entry].role = ROLE_ENTRY;
    w->cells[w->entry].arch = ARCH_ENTRY;
    w->cells[goal].role = ROLE_GOAL;
    w->cells[goal].arch = ARCH_ARENA;

    /* three key gates on the main path at rising depths */
    int edges = w->path_len - 1; /* edges on the path, 0..edges-1 */
    static const u8 gate_types[3] = { GATE_CRACK, GATE_WEB, GATE_CHASM };
    int lo = 1;
    for (i = 0; i < 3; i++) {
        /* gate i takes an edge in [lo, hi], leaving room for the gates
           after it, and never the same edge twice; spread along the path */
        int hi = edges - 1 - (2 - i);
        int span;
        if (hi < lo)
            hi = lo;
        span = (hi - lo) / (3 - i) + 1;
        int e = lo + (int)rng_range(&r, span);
        if (e > hi)
            e = hi;
        if (e > edges - 1)
            e = edges - 1;
        if (e < 1)
            e = 1;
        int a = w->path[e], b = w->path[e + 1];
        int side = -1;
        for (s = 0; s < 4; s++)
            if (cell_neighbor(a, s) == b)
                side = s;
        w->cells[a].gate[side] = gate_types[i];
        w->cells[b].gate[opposite(side)] = gate_types[i];
        w->gate_cell[i] = a;
        w->gate_side[i] = side;
        lo = e + 1;
    }
    /* key items: each in a room reachable before its gate */
    static const u8 key_items[3] = { 1, 2, 3 }; /* item ids: bombs, lamp, cloak */
    for (i = 0; i < 3; i++) {
        sStageLimit = i;
        flood(w->entry, pass_stage);
        int room = -1, best = -999, k;
        for (k = 0; k < CELLS; k++) {
            int p, onpath = 0, attachment = 0, depth = 0, sc;
            if (sDist[k] == 0xFF || w->cells[k].role != ROLE_NONE)
                continue;
            for (p = 0; p < w->path_len; p++)
                if (w->path[p] == k)
                    onpath = 1;
            p = k;
            while (p != 0xFF) {
                int j, at = -1;
                for (j = 0; j < w->path_len; j++)
                    if (w->path[j] == p) at = j;
                if (at >= 0) { attachment = at; break; }
                depth++;
                p = sParent[p];
            }
            /* The previous barrier is behind this branch's attachment. */
            if (i > 0) {
                int prev = 0, j;
                for (j = 0; j < w->path_len; j++)
                    if (w->path[j] == w->gate_cell[i - 1]) prev = j;
                if (attachment <= prev) continue;
            }
            sc = (!onpath ? 30 : 0) + MIN(depth, 4) * 8 +
                 (degree(k) == 1 ? 6 : 0) + rng_range(&r, 7);
            if (sc > best) { best = sc; room = k; }
        }
        if (room < 0)
            room = pick_room(&r, 1);
        if (room < 0)
            room = w->entry; /* invalid candidates are rejected by pacing */
        w->key_cell[i] = room;
        w->cells[room].role = ROLE_KEYITEM;
        w->cells[room].role_arg = key_items[i];
    }
    /* stages: the stage of a cell is the number of key gates needed */
    for (i = 0; i < CELLS; i++)
        w->cells[i].stage = 0xFF;
    for (s = 0; s <= 3; s++) {
        sStageLimit = s;
        flood(w->entry, pass_stage);
        for (i = 0; i < CELLS; i++)
            if (sDist[i] != 0xFF && w->cells[i].stage == 0xFF)
                w->cells[i].stage = s;
    }
    for (i = 0; i < CELLS; i++)
        if (w->cells[i].stage == 0xFF)
            w->cells[i].stage = 3; /* unreachable without keys: behind a lock only */
    w->stages = 4;

    /* locked doors on side branches: a tree edge from a parent reachable
       without any lock to a roleless child off the main path, with
       nothing the run needs beyond it. Its key waits in a room reachable
       at the lock's stage with no locks. Two of them. */
    int locks = 0;
    for (i = 0; i < 80 && locks < 2; i++) {
        int c = rng_range(&r, CELLS);
        s = rng_range(&r, 4);
        int n = cell_neighbor(c, s);
        if (n < 0 || !sTree[c][s] || w->cells[c].gate[s] != GATE_OPEN)
            continue;
        if (w->cells[n].dist != w->cells[c].dist + 1 || w->cells[n].role != ROLE_NONE)
            continue;
        int onpath = 0, k;
        for (k = 0; k < w->path_len; k++)
            if (w->path[k] == n)
                onpath = 1;
        if (onpath || subtree_holds_key(n, c))
            continue;
        sStageLimit = 3;
        flood(w->entry, pass_stage);
        if (sDist[c] == 0xFF)
            continue; /* already behind a lock */
        w->cells[c].gate[s] = GATE_LOCK;
        w->cells[n].gate[opposite(s)] = GATE_LOCK;
        sStageLimit = w->cells[c].stage;
        flood(w->entry, pass_stage);
        int room = pick_room(&r, 1);
        if (room >= 0) {
            w->cells[room].role = ROLE_KEYCHEST;
            w->cells[room].role_arg = CHEST_KEY;
            /* the room behind the lock holds a reward */
            w->cells[n].role = ROLE_CHEST;
            w->cells[n].role_arg = (locks == 0) ? CHEST_HEART_CONTAINER : CHEST_GAUNTLET;
            locks++;
        } else {
            w->cells[c].gate[s] = GATE_OPEN;
            w->cells[n].gate[opposite(s)] = GATE_OPEN;
        }
    }

    /* quests and chests in the remaining dead ends and rooms */
    sStageLimit = 3;
    flood(w->entry, NULL);
    int fetch_relic = -1;
    for (i = 0; i < CELLS; i++) {
        Cell* c = &w->cells[i];
        if (c->role != ROLE_NONE)
            continue;
        int roll = rng_range(&r, 10);
        if (degree(i) == 1) {
            if (roll < 4) {
                c->role = ROLE_CHEST;
                c->role_arg = (roll == 0) ? CHEST_HEART_PIECE : (roll == 1) ? CHEST_BOMBS : CHEST_GILT;
            } else if (roll < 6) {
                c->role = ROLE_NPC_HUNT;
            } else if (roll < 8 && fetch_relic < 0) {
                c->role = ROLE_NPC_FETCH;
                fetch_relic = i;
            } else if (roll == 8) {
                c->role = ROLE_NPC_TORCH;
            } else {
                c->role = ROLE_SHRINE;
            }
        } else if (roll < 2) {
            c->role = ROLE_NPC_HUNT;
        } else if (roll == 2) {
            c->role = ROLE_CHEST;
            c->role_arg = CHEST_GILT;
        }
    }
    /* every run gets at least one of each quest, in rooms still free */
    {
        int want[3] = { ROLE_NPC_HUNT, ROLE_NPC_FETCH, ROLE_NPC_TORCH };
        int q;
        for (q = 0; q < 3; q++) {
            int have = 0, best = -1, bs = -1;
            for (i = 0; i < CELLS; i++)
                if (w->cells[i].role == want[q])
                    have = 1;
            if (have)
                continue;
            for (i = 0; i < CELLS; i++) {
                Cell* c = &w->cells[i];
                if (c->role != ROLE_NONE || i == w->entry || i == w->goal)
                    continue;
                int sc = c->dist * 2 + (int)rng_range(&r, 5);
                if (sc > bs) {
                    bs = sc;
                    best = i;
                }
            }
            if (best >= 0) {
                w->cells[best].role = want[q];
                if (want[q] == ROLE_NPC_FETCH)
                    fetch_relic = best;
            }
        }
    }
    /* the Root Gauntlet, which lifts boulders, waits in some chest */
    {
        int have = 0, best = -1, bs = -1;
        for (i = 0; i < CELLS; i++)
            if (w->cells[i].role == ROLE_CHEST && w->cells[i].role_arg == CHEST_GAUNTLET)
                have = 1;
        for (i = 0; i < CELLS && !have; i++) {
            Cell* c = &w->cells[i];
            if (c->role != ROLE_NONE || i == w->entry || i == w->goal)
                continue;
            int sc = c->dist + (int)rng_range(&r, 4);
            if (sc > bs) {
                bs = sc;
                best = i;
            }
        }
        if (!have && best >= 0) {
            w->cells[best].role = ROLE_CHEST;
            w->cells[best].role_arg = CHEST_GAUNTLET;
        }
    }

    /* the Thorn Bow waits in a chest near the start: a free room of the
       first stage, the nearest to the entry that is not the entry */
    {
        int best = -1, bs = 999;
        for (i = 0; i < CELLS; i++) {
            Cell* c = &w->cells[i];
            if (c->role != ROLE_NONE || i == w->entry || i == w->goal || c->stage != 0)
                continue;
            int sc = c->dist * 2 + (int)rng_range(&r, 3);
            if (sc < bs) {
                bs = sc;
                best = i;
            }
        }
        if (best < 0)
            for (i = 0; i < CELLS; i++)
                if (w->cells[i].role == ROLE_NONE && i != w->entry && i != w->goal) {
                    best = i;
                    break;
                }
        if (best >= 0) {
            w->cells[best].role = ROLE_CHEST;
            w->cells[best].role_arg = CHEST_BOW;
        }
    }

    /* the fetch quest's relic: a room at the same or lower stage, not behind a lock */
    if (fetch_relic >= 0) {
        int st = w->cells[fetch_relic].stage;
        int best = -1, bs = -1;
      again:
        sStageLimit = st;
        flood(w->entry, pass_stage);
        for (i = 0; i < CELLS; i++) {
            Cell* c = &w->cells[i];
            if (sDist[i] == 0xFF || i == fetch_relic || i == w->goal || i == w->entry)
                continue;
            if (c->role != ROLE_NONE && c->role != ROLE_SHRINE)
                continue;
            int sc = ABS(cell_x(i) - cell_x(fetch_relic)) + ABS(cell_y(i) - cell_y(fetch_relic)) * 2 + (int)rng_range(&r, 3);
            if (sc > bs) {
                bs = sc;
                best = i;
            }
        }
        if (best >= 0) {
            w->cells[best].role = ROLE_RELIC;
            w->cells[fetch_relic].role_arg = best;
        } else if (st < 3) {
            st = 3; /* nothing free this early: a chamber deeper in */
            goto again;
        } else {
            w->cells[fetch_relic].role = ROLE_NPC_HUNT;
        }
    }

    /* loops: extra open edges between cells of the same stage */
    int loops = 0;
    for (i = 0; i < 40 && loops < 3; i++) {
        int c = rng_range(&r, CELLS);
        int s2 = rng_range(&r, 4);
        int n = cell_neighbor(c, s2);
        if (n < 0 || sTree[c][s2] || w->cells[c].gate[s2] != GATE_WALL)
            continue;
        if (w->cells[c].stage != w->cells[n].stage)
            continue;
        /* neither behind a lock: both reachable in the lock-free flood */
        sStageLimit = w->cells[c].stage;
        flood(w->entry, pass_stage);
        if (sDist[c] == 0xFF || sDist[n] == 0xFF)
            continue;
        w->cells[c].gate[s2] = (rng_next(&r) & 1) ? GATE_OPEN : GATE_THORN;
        w->cells[n].gate[opposite(s2)] = w->cells[c].gate[s2];
        loops++;
    }

    myst_generate(w, &r);
    /* These are the three milestones, never an event needing its own prize.
       A floor-plate trial, a wave trial and a knight trial are all completable
       with the starting sword; the event system grants the item's chest. */
    {
        static const u8 trials[3] = { MK_SWITCHES, MK_WAVES, MK_MINIBOSS };
        for (i = 0; i < 3; i++)
            w->myst[w->key_cell[i]] = MYST_PACK(trials[i], MS_MEDIUM,
                                              rng_range(&r, 3));
    }
    /* the Map and the Astrolabe wait in two more chests, in free rooms:
       the Map early (the first stage, nearest after the bow), the
       Astrolabe anywhere free */
    {
        int want[2] = { CHEST_MAP, CHEST_ASTROLABE }, q;
        for (q = 0; q < 2; q++) {
            int best = -1, bs = 999;
            for (i = 0; i < CELLS; i++) {
                Cell* c = &w->cells[i];
                if (c->role != ROLE_NONE || i == w->entry || i == w->goal)
                    continue;
                if (q == 0 && c->stage > 1)
                    continue;
                {
                    int sc = (q == 0 ? c->dist * 2 : (int)(c->dist & 3)) + (int)rng_range(&r, 3);
                    if (sc < bs) {
                        bs = sc;
                        best = i;
                    }
                }
            }
            if (best >= 0) {
                w->cells[best].role = ROLE_CHEST;
                w->cells[best].role_arg = want[q];
            }
        }
    }

    /* archetypes, themes, density */
    for (i = 0; i < CELLS; i++) {
        Cell* c = &w->cells[i];
        if (c->arch == ARCH_GLADE && i != w->entry) {
            c->arch = rng_range(&r, ARCH_ARENA); /* glade..boneyard */
            if (c->role == ROLE_NPC_TORCH || c->role == ROLE_SHRINE)
                c->arch = ARCH_RUINS;
            if (c->role == ROLE_NPC_FETCH)
                c->arch = ARCH_GLADE;
        }
        c->theme = rng_range(&r, 4);
        c->density = 2 + c->stage + (int)rng_range(&r, 2);
        if (c->role == ROLE_SHRINE || c->role == ROLE_NPC_FETCH)
            c->density = 1;
        if (i == w->entry)
            c->density = 1;
        if (i == w->goal)
            c->density = 0;
        c->flags = 0;
        c->opened = 0;
    }
    return TRUE;
}

/* -------------------------------------------------------- run pacing -- */
const WorldTuning world_profiles[WORLD_PROFILE_COUNT] = {
    /* crossings, detours, optional cells, spine, candidate budget */
    { 18, 24, 1, 6,  9, 14, 24 }, /* focused */
    { 24, 32, 2, 4, 10, 17, 32 }, /* balanced: the default */
    { 25, 34, 3, 3,  9, 19, 64 }, /* wandering */
};

/* Actual graph distances: loops are counted, item barriers respected, locks
   excluded. The parent path is also a certificate of the required visit set. */
static int route_walk(int from, int to, int stage, u32* visits) {
    u32 targets = to < 0 ? 0 : 1u << to;
    int found = -1;
    if (to < 0) {
        int k;
        for (k = 0; k < gWorld.path_len; k++) targets |= 1u << gWorld.path[k];
    }
    u8 q[CELLS], distance[CELLS], parent[CELLS];
    int head = 0, tail = 0, i;
    memset(distance, 255, sizeof(distance));
    memset(parent, 255, sizeof(parent));
    distance[from] = 0;
    q[tail++] = from;
    while (head < tail) {
        int c = q[head++];
        if (targets & (1u << c)) { found = c; break; }
        for (i = 0; i < 4; i++) {
            int n = cell_neighbor(c, i), g = gWorld.cells[c].gate[i];
            if (n < 0 || distance[n] != 255 || g == GATE_WALL ||
                g == GATE_EXIT || g == GATE_LOCK ||
                (g == GATE_CRACK && stage < 1) ||
                (g == GATE_WEB && stage < 2) ||
                (g == GATE_CHASM && stage < 3)) continue;
            distance[n] = distance[c] + 1;
            parent[n] = c;
            q[tail++] = n;
        }
    }
    if (found < 0) return 255;
    i = found;
    while (i != 255) {
        *visits |= 1u << i;
        if (i == from) break;
        i = parent[i];
    }
    return distance[found];
}

void world_route_metrics(WorldRouteMetrics* out) {
    int i, j, from = gWorld.entry, crossings = 0;
    u32 visits = 0;
    memset(out, 0, sizeof(*out));
    out->spine_edges = gWorld.path_len - 1;
    for (i = 0; i < 4; i++) {
        int to = i < 3 ? gWorld.key_cell[i] : gWorld.goal;
        int d = route_walk(from, to, i, &visits);
        if (d == 255) { out->required_crossings = 255; return; }
        crossings += d;
        from = to;
        if (i < 3) {
            u32 ignored = 0;
            int onpath = 0, nearest = route_walk(to, -1, i, &ignored);
            for (j = 0; j < gWorld.path_len; j++)
                if (gWorld.path[j] == to) onpath = 1;
            if (!onpath) out->detours++;
            if (nearest != 255 && nearest > out->max_detour)
                out->max_detour = nearest;
        }
    }
    out->required_crossings = crossings;
    for (i = 0; i < CELLS; i++) out->required_cells += (visits >> i) & 1;
    out->backtrack_edges = crossings + 1 - out->required_cells;
}

static int outside(int value, int lo, int hi) {
    return value < lo ? lo - value : value > hi ? value - hi : 0;
}

static bool8 milestones_fit(void) {
    int i;
    for (i = 0; i < 3; i++) {
        const Cell* c = &gWorld.cells[gWorld.key_cell[i]];
        if (c->role != ROLE_KEYITEM || c->role_arg != i + 1 || c->stage != i)
            return FALSE;
    }
    return gWorld.cells[gWorld.entry].role == ROLE_ENTRY;
}

static bool8 metrics_fit(const WorldRouteMetrics* m, const WorldTuning* t) {
    return m->required_crossings >= t->min_crossings &&
           m->required_crossings <= t->max_crossings &&
           m->spine_edges >= t->spine_min && m->spine_edges <= t->spine_max &&
           m->detours >= t->min_detours &&
           m->required_cells <= CELLS - t->min_optional;
}

void world_generate_tuned(u32 seed, const WorldTuning* tuning) {
    /* Keep the best candidate rather than an unbounded retry loop on the GBA.
       The seed still names the whole run, including all art and event draws. */
    World best;
    WorldTuning settings = tuning ? *tuning : world_profiles[WORLD_BALANCED];
    int attempt, best_score = 0x7fffffff;
    int target;
    settings.max_crossings = MAX(settings.min_crossings, settings.max_crossings);
    settings.min_detours = MIN(settings.min_detours, 3);
    settings.spine_min = CLAMP(settings.spine_min, 5, CELLS - 1);
    settings.spine_max = CLAMP(settings.spine_max, settings.spine_min, CELLS - 1);
    settings.attempts = settings.attempts ? MIN(settings.attempts, 128) : 64;
    tuning = &settings;
    gWorldGenerationFallback = 0;
    target = tuning->min_crossings + hash32(seed, 0x726f7574) %
                 (tuning->max_crossings - tuning->min_crossings + 1);
    for (attempt = 0; attempt < tuning->attempts; attempt++) {
        WorldRouteMetrics m;
        int score;
        gWorldGenerationAttempts = attempt + 1;
        if (!world_candidate(seed, hash32(seed, attempt * 0x9e37u + 0x74726565),
                             attempt ? tuning : NULL))
            continue;
        world_route_metrics(&m);
        score = outside(m.required_crossings, tuning->min_crossings, tuning->max_crossings) * 40 +
                outside(m.spine_edges, tuning->spine_min, tuning->spine_max) * 30 +
                MAX(0, tuning->min_detours - m.detours) * 100 +
                MAX(0, tuning->min_optional - (CELLS - m.required_cells)) * 150 +
                ABS(m.required_crossings - target);
        if (!milestones_fit()) score += 10000;
        if (score < best_score) {
            best_score = score;
            memcpy(&best, &gWorld, sizeof(best));
            /* A two-crossing tolerance avoids freezing the title while
               hunting for an exact distance. All structural limits still
               hold: their penalties are at least thirty. */
            if (score <= 2) break;
        }
    }
    memcpy(&gWorld, &best, sizeof(gWorld));
    {
        /* Four certified skeletons per named profile make the runtime bound
           honest: exhausting the budget never silently requires all 25 rooms
           or loses a mandatory detour. Art still uses the original run seed.
           Custom infeasible targets return the best candidate, with this same
           no-full-clear safety fallback. Budget changes keep certification. */
        static const u32 fallback[WORLD_PROFILE_COUNT][4] = {
            { 6, 7, 11, 16 }, { 1, 7, 8, 10 }, { 8, 27, 28, 31 }
        };
        WorldRouteMetrics m;
        int profile = -1, p;
        world_route_metrics(&m);
        for (p = 0; p < WORLD_PROFILE_COUNT; p++) {
            const WorldTuning* t = &world_profiles[p];
            if (settings.min_crossings == t->min_crossings &&
                settings.max_crossings == t->max_crossings &&
                settings.min_detours == t->min_detours &&
                settings.min_optional == t->min_optional &&
                settings.spine_min == t->spine_min && settings.spine_max == t->spine_max)
                profile = p;
        }
        if ((profile >= 0 && !metrics_fit(&m, tuning)) || m.required_cells >= CELLS ||
            !milestones_fit()) {
            if (profile < 0) profile = WORLD_BALANCED;
            world_candidate(seed, fallback[profile][hash32(seed, 0x66616c6c) & 3], NULL);
            gWorldGenerationFallback = 1;
            gWorldGenerationAttempts++;
        }
    }
}

void world_generate(u32 seed) {
    world_generate_tuned(seed, &world_profiles[WORLD_BALANCED]);
}
