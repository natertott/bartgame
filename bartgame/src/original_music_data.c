/* Imported native original music; see audio/original/manifest.json. */
#include "original_music_data.h"

extern const s8 gOriginalPcm_sewer[];
extern const s8 gOriginalPcm_forest[];
extern const s8 gOriginalPcm_boss[];
extern const s8 gOriginalPcm_title[];
extern const s8 gOriginalPcm_win[];

const OriginalSong gOriginalSongs[BGM_COUNT] = {
    [BGM_NONE] = { 0, 0, 0, 0, 0, 0, "Silence" },
    [BGM_SEWER] = { gOriginalPcm_sewer, 1966272u, 0u, 3584, 0, 1, "Undertow Circuit" },
    [BGM_FOREST] = { gOriginalPcm_forest, 1685376u, 0u, 3072, 0, 2, "Verdant Afterimage" },
    [BGM_BOSS] = { gOriginalPcm_boss, 1310666u, 0u, 2389, 0, 3, "Heart of Chrome" },
    [BGM_TITLE] = { gOriginalPcm_title, 2330011u, 291320u, 4247, 531, 26, "Crown of the Afterlight - Dawn Overture" },
    [BGM_WIN] = { gOriginalPcm_win, 1521886u, 0u, 2774, 0, 25, "Aurora Unbound" },
};
