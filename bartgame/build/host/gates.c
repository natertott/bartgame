#include <stdio.h>
#include "world.h"
/* BFS over the world's gates: passable if open/thorn/exit, or a key gate at stage <= limit; locks never. */
static int reach[CELLS];
static void bfs(int limit) {
    int q[CELLS], qh = 0, qt = 0, i;
    { int z; for (z = 0; z < CELLS; z++) reach[z] = 0; }
    reach[gWorld.entry] = 1; q[qt++] = gWorld.entry;
    while (qh < qt) {
        int c = q[qh++];
        for (i = 0; i < 4; i++) {
            int g = gWorld.cells[c].gate[i], n;
            int x = c % MAZE_W + (i == 1) - (i == 3), y = c / MAZE_W + (i == 2) - (i == 0);
            if (x < 0 || y < 0 || x >= MAZE_W || y >= MAZE_H) continue;
            n = y * MAZE_W + x;
            if (g == GATE_WALL || g == GATE_LOCK || g == GATE_EXIT) continue;
            if (g == GATE_CRACK && limit < 1) continue;
            if (g == GATE_WEB && limit < 2) continue;
            if (g == GATE_CHASM && limit < 3) continue;
            if (!reach[n]) { reach[n] = 1; q[qt++] = n; }
        }
    }
}
int main(void) {
    unsigned s; int bad = 0, shortp = 0, locks_total = 0, keych_total = 0, quest_ok = 0;
    for (s = 1; s < 20000; s++) {
        world_generate(s);
        int i, k, n[8] = {0}, hunt = 0, fetch = 0, torch = 0;
        for (i = 0; i < CELLS; i++) for (k = 0; k < 4; k++) n[gWorld.cells[i].gate[k]]++;
        if (n[GATE_CRACK] != 2 || n[GATE_WEB] != 2 || n[GATE_CHASM] != 2) { bad++; if (bad < 4) printf("seed 0x%x: crack %d web %d chasm %d path %d\n", s, n[GATE_CRACK], n[GATE_WEB], n[GATE_CHASM], gWorld.path_len); }
        if (gWorld.path_len < 6) shortp++;
        locks_total += n[GATE_LOCK] / 2;
        /* each key item reachable with the gates before it, no locks */
        for (i = 0; i < 3; i++) { bfs(i); if (!reach[gWorld.key_cell[i]]) { bad++; if (bad < 12) printf("seed 0x%x: key %d (cell %d) unreachable at stage %d\n", s, i, gWorld.key_cell[i], i); } }
        bfs(3); if (!reach[gWorld.goal]) { bad++; if (bad < 12) printf("seed 0x%x: goal unreachable\n", s); }
        /* every key chest reachable without locks at stage 3; every quest present */
        for (i = 0; i < CELLS; i++) {
            Cell* c = &gWorld.cells[i];
            if (c->role == ROLE_KEYCHEST) { keych_total++; if (!reach[i]) { bad++; if (bad < 12) printf("seed 0x%x: key chest %d behind a lock\n", s, i); } }
            hunt += c->role == ROLE_NPC_HUNT; fetch += c->role == ROLE_NPC_FETCH; torch += c->role == ROLE_NPC_TORCH;
            if (c->role == ROLE_NPC_FETCH) { Cell* rc = &gWorld.cells[c->role_arg]; if (rc->role != ROLE_RELIC) { bad++; if (bad < 12) printf("seed 0x%x: fetch at %d has no relic (arg %d role %d)\n", s, i, c->role_arg, rc->role); } }
        }
        if (hunt && fetch && torch) quest_ok++;
    }
    printf("seeds 1..19999: bad %d, short paths %d, locks/run %.2f, key chests/run %.2f, all three quests %d\n", bad, shortp, locks_total / 19999.0, keych_total / 19999.0, quest_ok);
    return bad ? 1 : 0;
}
