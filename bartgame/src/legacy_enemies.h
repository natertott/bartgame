#ifndef LEGACY_ENEMIES_H
#define LEGACY_ENEMIES_H
#include "enemy.h"

/* Appended IDs preserve the original nine species and their saved sightings.
   Order is the 71-row curated roster in the migration handoff, followed by
   the three explicitly required legacy bosses and the new summit boss. */
#define LEGACY_ENEMY_BASE 9
#define LEGACY_CURATED_COUNT 71
#define LEGACY_ENEMY_COUNT 75
#define LEGACY_ENEMY_END (LEGACY_ENEMY_BASE + LEGACY_ENEMY_COUNT)
enum LegacyEnemyType {
    LE_BEETLE_0 = LEGACY_ENEMY_BASE,
    LE_KEESE_0,
    LE_SMALL_PESTO_0,
    LE_TEKTITE_0,
    LE_CROW_0,
    LE_MINI_SLIME_0,
    LE_OCTOROK_0,
    LE_PEAHAT_0,
    LE_CHUCHU_0,
    LE_ROPE_0,
    LE_OCTOROK2_0,
    LE_OCTOROK_1,
    LE_SLIME_0,
    LE_STALFOS_0,
    LE_STALFOS_1,
    LE_KEATON_0,
    LE_HELMASAUR_0,
    LE_PESTO_0,
    LE_CHUCHU_2,
    LE_BOBOMB_0,
    LE_BOMBAROSSA_0,
    LE_LEEVER_0,
    LE_MULLDOZER_0,
    LE_TEKTITE_1,
    LE_LEEVER_1,
    LE_MOLDORM_0,
    LE_GHINI_0,
    LE_ARMOS_0,
    LE_EYEGORE_0,
    LE_MULLDOZER_1,
    LE_PESTO_1,
    LE_CHUCHU_1,
    LE_ROCK_CHUCHU_0,
    LE_SPINY_CHUCHU_0,
    LE_SPIKED_BEETLE_0,
    LE_PUFFSTOOL_0,
    LE_FIREBALL_GUY_0,
    LE_MINI_FIREBALL_GUY_0,
    LE_BOMB_PEAHAT_0,
    LE_CLOUD_PIRANHA_0,
    LE_SPINY_BEETLE_0,
    LE_UNKNOWN_50_0,
    LE_LIKE_LIKE_0,
    LE_RUPEE_LIKE_0,
    LE_RUPEE_LIKE_2,
    LE_RUPEE_LIKE_1,
    LE_TAKKURI_0,
    LE_GOBDO_0,
    LE_SCISSORS_BEETLE_0,
    LE_MOLDWORM_0,
    LE_UNKNOWN_4D_0,
    LE_BOW_MOBLIN_0,
    LE_SPEAR_MOBLIN_0,
    LE_ACRO_BANDIT_0,
    LE_WIZZROBE_FIRE_0,
    LE_WIZZROBE_ICE_0,
    LE_WIZZROBE_WIND_0,
    LE_TEKTITE_GOLDEN_0,
    LE_OCTOROK_GOLDEN_0,
    LE_ROPE_GOLDEN_0,
    LE_ROLLOBITE_0,
    LE_WISP_0,
    LE_WISP_1,
    LE_SPARK_0,
    LE_LAKITU_0,
    LE_DARK_NUT_0,
    LE_DARK_NUT_1,
    LE_DARK_NUT_2,
    LE_DARK_NUT_3,
    LE_BALL_CHAIN_SOLIDER_0,
    LE_MADDERPILLAR_0,
    LE_GIANT_CHUCHU_GREEN, LE_GIANT_CHUCHU_ELECTRIC,
    LE_BIG_OCTOROK, LE_CREAM_GLEEROK
};
enum LegacyHitKind {
    LE_HIT_SWORD, LE_HIT_ARROW, LE_HIT_BOMB, LE_HIT_LANTERN,
    LE_HIT_GUST_SMALL, LE_HIT_GUST_BIG, LE_HIT_BOOMERANG,
    LE_HIT_PACCI, LE_HIT_SHIELD, LE_HIT_ICE, LE_HIT_FIRE,
    LE_HIT_THROWN, LE_HIT_BEAM, LE_HIT_REFLECTED
};
extern u8 gLegacyHitKind;
enum LegacyEnemyFamily {
    LF_BEETLE, LF_KEESE, LF_SMALL_PESTO, LF_TEKTITE, LF_CROW,
    LF_MINI_SLIME, LF_OCTOROK, LF_PEAHAT, LF_CHUCHU, LF_ROPE,
    LF_SLIME, LF_STALFOS, LF_KEATON, LF_HELMASAUR, LF_PESTO,
    LF_BOBOMB, LF_BOMBAROSSA, LF_LEEVER, LF_MULLDOZER, LF_MOLDORM,
    LF_GHINI, LF_ARMOS, LF_EYEGORE, LF_ROCK_CHUCHU, LF_SPINY_CHUCHU,
    LF_SPIKED_BEETLE, LF_PUFFSTOOL, LF_FIREBALL, LF_MINI_FIREBALL,
    LF_BOMB_PEAHAT, LF_CLOUD_PIRANHA, LF_SPINY_BEETLE, LF_UNKNOWN50,
    LF_LIKE_LIKE, LF_RUPEE_LIKE, LF_TAKKURI, LF_GIBDO, LF_SCISSORS,
    LF_MOLDWORM, LF_UNKNOWN4D, LF_BOW_MOBLIN, LF_SPEAR_MOBLIN,
    LF_ACRO_BANDIT, LF_WIZZROBE_FIRE, LF_WIZZROBE_ICE, LF_WIZZROBE_WIND,
    LF_ROLLOBITE, LF_WISP, LF_SPARK, LF_LAKITU, LF_DARKNUT,
    LF_BALL_CHAIN, LF_MADDERPILLAR, LF_GIANT_CHUCHU, LF_BIG_OCTOROK,
    LF_GLEEROK, LF_COUNT
};
enum { LE_ROLE_CHAFF=1, LE_ROLE_HEAVY=2, LE_ROLE_RANGED=4,
       LE_ROLE_FLYER=8, LE_ROLE_AMBUSH=16, LE_ROLE_FAST=32,
       LE_ROLE_SLOW=64, LE_ROLE_THIEF=128 };
#define LE_ROLE_FLYING LE_ROLE_FLYER
#define LE_ROLE_SHOOTER LE_ROLE_RANGED
#define LE_ROLE_ARMORED LE_ROLE_HEAVY
/* Boss status is base.flags & AF_BOSS; source role bits remain exact. */
typedef struct {
    EnemyDef base; /* MUST remain first: enemy_definition returns this prefix. */
    const char* name;
    const char* notes;
    u8 source_id, form, tier, family;
    u8 cost, cap, roles, theme;
} LegacyEnemyDef;
extern const LegacyEnemyDef gLegacyEnemyDefs[LEGACY_ENEMY_COUNT];
const LegacyEnemyDef* legacy_enemy_def(int type);
bool8 legacy_enemy_owns(int type);
void legacy_enemy_init(Actor* enemy);
void legacy_enemy_update(Actor* enemy);
void legacy_enemy_room_reset(void);
/* Temporary exposed-boss support in pixels; -1 means ordinary floor. */
int legacy_enemy_platform_height(int px,int py);
bool8 legacy_enemy_accept_hit(Actor* enemy,int kind,int* damage,int from_dir);
/* TRUE consumes contact instead of normal contact damage. */
bool8 legacy_enemy_contact(Actor* enemy);
void legacy_enemy_on_death(Actor* enemy);
void legacy_enemy_extra_draw(Actor* enemy);
/* Resolves segmented tail/mandible/flail collision before ordinary body hit.
   Called for a player weapon box once per attack, prior to body hurt. */
bool8 legacy_enemy_hit_parts(Actor* enemy,int x0,int y0,int x1,int y1,
                            int kind,int damage,int from_dir);
bool8 legacy_enemy_can_spawn(int type);
int legacy_enemy_pick(int tier,u32 roll);
/* Enemy-only projectiles use IDs 96..103; return FALSE for ordinary types. */
bool8 legacy_projectile_update(Actor* projectile);
bool8 legacy_projectile_draw(Actor* projectile);
bool8 legacy_enemy_liftable(const Actor* enemy);
bool8 legacy_enemy_lift(Actor* enemy);
bool8 legacy_enemy_throw(Actor* enemy,int direction,int distance);
#endif
