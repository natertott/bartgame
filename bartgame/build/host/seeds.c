#include <stdio.h>
#include <stdlib.h>
#include "world.h"
int main(int argc, char** argv) {
    unsigned s; int shown = 0;
    for (s = 1; s < 3000 && shown < 8; s++) {
        world_generate(s);
        int hunt = 0, fetch = 0, torch = 0, shrine = 0, lock = 0, i, k;
        for (i = 0; i < CELLS; i++) {
            Cell* c = &gWorld.cells[i];
            hunt += c->role == ROLE_NPC_HUNT; fetch += c->role == ROLE_NPC_FETCH;
            torch += c->role == ROLE_NPC_TORCH; shrine += c->role == ROLE_SHRINE;
            for (k = 0; k < 4; k++) lock += c->gate[k] == GATE_LOCK;
        }
        if (fetch && torch && hunt) {
            printf("seed 0x%x: hunt %d fetch %d torch %d shrine %d locks %d path %d\n", s, hunt, fetch, torch, shrine, lock / 2, gWorld.path_len);
            shown++;
        }
    }
    return 0;
}
