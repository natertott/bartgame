#include <stdio.h>
#include <stdlib.h>
#include "world.h"
static const char* G = "#.tCWLXe";
int main(int argc, char** argv) {
    unsigned s = strtoul(argv[1], 0, 0); int i, k;
    world_generate(s);
    printf("seed 0x%x entry %d goal %d path_len %d stages %d\n", s, gWorld.entry, gWorld.goal, gWorld.path_len, gWorld.stages);
    printf("path:"); for (i = 0; i < gWorld.path_len; i++) printf(" %d", gWorld.path[i]); printf("\n");
    for (i = 0; i < 3; i++) printf("gate %d: cell %d side %d type %c  key cell %d (stage %d)\n", i, gWorld.gate_cell[i], gWorld.gate_side[i], G[gWorld.cells[gWorld.gate_cell[i]].gate[gWorld.gate_side[i]]], gWorld.key_cell[i], gWorld.cells[gWorld.key_cell[i]].stage);
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        printf("cell %2d role %2d arg %2d stage %d arch %d gates N%c E%c S%c W%c\n", i, c->role, c->role_arg, c->stage, c->arch, G[c->gate[0]], G[c->gate[1]], G[c->gate[2]], G[c->gate[3]]);
    }
    return 0;
}
