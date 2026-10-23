#include <stdio.h>
#include "world.h"
int main(void) {
    unsigned s; long pl = 0, locks = 0, deadends = 0, offpath = 0, keyroles = 0, chests = 0; int minpl = 99, maxpl = 0;
    for (s = 1; s < 20000; s++) {
        world_generate(s);
        int i, k, n = 0;
        pl += gWorld.path_len; if (gWorld.path_len < minpl) minpl = gWorld.path_len; if (gWorld.path_len > maxpl) maxpl = gWorld.path_len;
        for (i = 0; i < CELLS; i++) {
            Cell* c = &gWorld.cells[i]; int deg = 0, on = 0;
            for (k = 0; k < 4; k++) { if (c->gate[k] == GATE_LOCK) n++; deg += c->gate[k] != GATE_WALL && c->gate[k] != GATE_EXIT; }
            deadends += deg == 1;
            for (k = 0; k < gWorld.path_len; k++) on |= gWorld.path[k] == i;
            offpath += !on;
            chests += c->role == ROLE_CHEST || c->role == ROLE_KEYCHEST;
        }
        locks += n / 2;
    }
    printf("path_len mean %.1f min %d max %d; off-path cells/run %.1f; dead ends/run %.1f; locks/run %.2f; chests/run %.2f\n", pl / 19999.0, minpl, maxpl, offpath / 19999.0, deadends / 19999.0, locks / 19999.0, chests / 19999.0);
    return 0;
}
