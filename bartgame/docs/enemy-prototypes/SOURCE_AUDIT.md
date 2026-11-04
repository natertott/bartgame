# The carried-over enemy design: source audit

Status: reference research for new prototypes, 2026-11-04. These are source
facts and admission constraints, not a newly adopted 71-enemy bestiary. The
new-game proposals and any implemented lab behavior are documented separately.
Existing Coin Toad, Quill Moth, Trumpet Bellflower, Pear Bladder, Moth Confessor
and the broken purple Heart remain the selected appearance families.

## Which original document?

The repository contains the original handoff; no missing external document
needs to be guessed. [The handoff](../../../docs/newgame/00_README.md) identifies
the outer TMC/QUICKSTART project as the mechanics reference for the standalone
game. Its [enemy/object specification](../../../docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md#enemies)
records the curated enemy list, roles, special item requirements, excluded
forms and encounter budgets. [Current-game design](../../../docs/newgame/06_CURRENT_GAME_DESIGN.md)
and the [from-scratch specification](../../../docs/newgame/12_FROM_SCRATCH_ENGINE.md)
explain which mechanics and data should carry over.

That means the **curated QUICKSTART roster is the starting list**, rather than
all 213 raw rows of [enemies.csv](../../../docs/newgame/data/enemies.csv).
Those raw rows include colors, segmented children, scripted boss pieces and
other forms that are not independent, safe room encounters. The curated list
has 71 unique enemy/form picks from 57 enemy IDs; several picks still create
more than one actor. This is a design source, not permission to spawn every
old form in every new room.

Read snapshot: repository revision
`04a42521264349e23d8057744e6467eace0bdd13`. Every referenced input's SHA256 and
each roster/stat/matrix row location are retained in
[source_catalogue.json](source_catalogue.json). Reproduce the extraction with
`python3 bartgame/docs/enemy-prototypes/build_source_catalogue.py` from the
repository root. It reads sources; it does not change game data.

## The actual curated list

The live arrays at [src/game.c:9423](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/game.c#L9423)
take precedence over nearby historical comments. For example, a comment still
describes Darknuts split across tiers 4/5 even though all four forms now live
in the Elite array. A later comment says two Madderpillar chains, while the
actual live-cap table allows one. Neither stale comment should become a new
design rule.

| Original bucket | Count | Enemy/forms |
| --- | ---: | --- |
| L1 | 10 | Beetle; Keese; Small Pesto; red Tektite; Crow; Mini Slime; red Octorok; Peahat; green ChuChu; Rope. |
| L2 | 15 | Octorok2; blue Octorok; Slime; red/blue Stalfos; Keaton; Helmasaur; red Pesto; blue ChuChu; Bob-omb; Bombarossa; red/blue Leever; red Mulldozer; blue Tektite. |
| L3 | 17 | Moldorm; Ghini; Armos; Eyegore; blue Mulldozer; blue Pesto; red ChuChu; Rock ChuChu; Spiny ChuChu; Spiked Beetle; Puffstool; Fireball Guy; Mini Fireball Guy; Bomb Peahat; Cloud Piranha; Spiny Beetle; ENEMY_50. |
| L4 | 12 | Like Like; green/red/blue Rupee Like; Takkuri; Gibdo (`GOBDO` in enum); Scissors Beetle; Moldworm; ENEMY_4D; Bow Moblin; Spear Moblin; Acro Bandit. |
| L5 | 11 | Fire/Ice/Wind Wizzrobe; golden Tektite/Octorok/Rope; Rollobite; red/blue Wisp; Spark; Lakitu. |
| Elite | 6 | Four Darknut forms; Ball and Chain Soldier (`BALL_CHAIN_SOLIDER` in enum); Madderpillar. |

Historical tiers are provenance, not a proposed hard appearance gate for the
new forest. Difficulty shifts probabilities and density; required player
capabilities, navigable terrain and room/entity budgets are separate checks.

## Damage units: avoid three misleading shortcuts

1. **`damage_type` is a collision-row ID.** Rope's 25, Spiked Beetle's 99 and
   Helmasaur's 111 are not damage amounts. The matrix is indexed as
   `hitType * 34 + hurtType`. The initial enemy row may change when armor is
   removed, a creature flips, or a different attack state begins.
2. **CSV damage columns are already renamed for the receiver.** The player or
   player item is `org`; the enemy is `tgt`. `damage_to_org` is health lost on
   the player side, while `damage_to_tgt` is lost on the enemy side. In the
   original C struct the corresponding fields have the opposite-looking
   names `tgtDamage` and `orgDamage`. The extractor explains this explicitly at
   [extract_feel.py:132](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/tools/newgame/extract_feel.py#L132);
   [CollisionDefault:826](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/collision.c#L826)
   and `CalculateDamage` apply it.
3. **Player health uses eight units per heart.** The original HUD first halves
   health ([ui.c:193](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/ui.c#L193)),
   then divides its HUD units by four (`ui.c:463`). The standalone HUD uses
   `hp_max / 8` directly ([text.c](../../src/text.c)). Therefore ordinary
   contact damage 2 is a quarter heart, not two hearts. Enemy HP uses entity
   units and should be discussed as HP/hits, not converted into player hearts.

`handler=default` matrix cells provide ordinary generic damage. Numbered
handlers and enemy contact callbacks can override them: deflect, grab,
flip, remove a shield, start a fuse, or kill immediately. Item-level/charm
modifiers can also change damage. The special collision contact IDs in
`include/collision.h` are not a complete list of all weapon-strength columns;
in particular, do not infer every arrow's exact damage from one contact ID.

## Verified behavior families for new work

These numbers describe **the reference**, not proposed standalone tuning.
The ordinary sword entry below is matrix column 13. Contact entries describe
an ordinary unmodified body exchange in the indicated initial state.

| Source family | Initial HP; base movement | Body damage to player | Taking damage and the distinctive mechanic |
| --- | --- | --- | --- |
| Rope | 4; 0.5 px/frame | 2 = ¼ heart | Ordinary sword deals 2. Detects an aligned player, spends 30 frames preparing, then charges at 1.625 px/frame with direction locked. Walls/obstruction end the pass. |
| Spiked Beetle | 4; 0.375 px/frame | 2 = ¼ heart upright | Upright sword/ordinary arrow exchanges deal zero. Shield/flip contact changes row 99 to row 100; after landing the exposed belly lasts 150 frames, with a wobble in the last 60. A 30-frame tell precedes a 1.75 px/frame charge; it can turn slightly every 16 frames. |
| Crow | 2; table base 1.25 px/frame | 2 = ¼ heart | Ordinary sword deals 2; the contact callback also handles immediate death from a positive damaging hit. Waits on a perch, lifts for 16 frames, readies for 24, swoops at 1.75 px/frame and steers every 8 frames; departure is 1.5 px/frame. |
| Helmasaur | 4; table base 1 px/frame | 2 = ¼ heart | Front-sector hits rebound; accepted rear-angle hits use the ordinary row-25 damage table. Original helmet removal requires Gust Jar. Its full windup setup is 60 frames before a 3 px/frame charge, not the later 30-frame charge timer. |
| Leever, red/blue | 6/8; table base 0.5 px/frame | 2 = ¼ heart | Ordinary sword deals 2 while exposed. Buried/emerging/active/retracting states; collision becomes active on an emergence animation cue. Active life is 180/110 frames, then a 240-frame buried cooldown. Actual movement speed follows animation cues, and blue adds 0.25 px/frame. |
| Tektite, red/blue | 3/6; 1/1.25 px/frame | 2 = ¼ heart | Ordinary sword deals 2. Preparation depends on animation completion; blue chains three hops. Contact callbacks make arrow contacts lethal and boomerang contact reset its hop cycle. New art cannot promise sword invulnerability merely because the body is airborne. |
| Bob-omb | 255 sentinel HP; 0.5 px/frame base | 2 = ¼ heart for the walking body | First/second hits drive an armed/stopped/carryable lifecycle. This is not a 128-sword-hit enemy. Carried fuse can be 120 frames; explosion damage must be audited separately from body damage. |
| Puffstool | 1; 0.25 px/frame | 2 = ¼ heart while coated | Coated row 130 takes zero ordinary sword damage. Gust contact strips coating, selects exposed row 131 and starts a 660-frame exposure timer. A candle-based alternative would be a new design adaptation, not the original rule. |

Behavior evidence:

- [Rope:138](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/rope.c#L138),
  preparation/movement at 180 and base wander at 196.
- [Spiked Beetle:34](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/spikedBeetle.c#L34),
  charge at 84–143, exposed duration at 155–180. The new implementation must
  explicitly route a successful shield block into the flip transition; art
  alone does not add this counter.
- [Crow:121](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/crow.c#L121),
  phased takeoff/swoop at 204 and offscreen return at 143. The activation
  rectangle is 136×80 radii and checks that the player is south of its perch.
- [Helmasaur:99](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/helmasaur.c#L99),
  charge setup at 177; directional armor handler
  [collision.c:738](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/collision.c#L738).
- [Leever:74](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/leever.c#L74),
  terrain checks at 127 and movement at 170.
- [Tektite:62](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/tektite.c#L62),
  preparation at 119 and chain-hop handling at 194.
- [Bob-omb:42](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/bobomb.c#L42),
  carrying at 115, detonation at 290.
- [Puffstool:74](https://github.com/natertott/bartgame/blob/04a42521264349e23d8057744e6467eace0bdd13/src/enemy/puffstool.c#L74).

Rope, Spiked Beetle and Crow offer three distinct next prototypes: a
committed ground charge, a shield reversal and an announced perched swoop.
They can use the current sword/shield/movement vocabulary without adding a
new mandatory item. The reference numbers above establish provenance; kinder
recovery windows, reduced turning or different health must be labeled new
tuning. Original forms/names are mechanics references; final creature designs
should be original and remain unselected until reviewed.

## Admission constraints inherited from the source

- Spark is boomerang-only and Lakitu is Pacci-only in their reference
  callbacks. Those tools are absent from the current standalone inventory.
  Defer mandatory encounters unless an explicitly documented new supported
  counter replaces the missing tool. Helmasaur/Puffstool likewise need their
  absent Gust Jar interaction addressed before promising armor removal.
- Gyorg Child, Sluggula, Wall Master, ENEMY_64 and boss parts were deliberately
  omitted: parent scripts, replacement/deletion behavior, undefined dungeon
  entrance warps or oversized multipart bodies made bare room spawning unsafe.
- Madderpillar is about seven live entities; Acro Bandit bursts into six.
  Source live caps at `src/game.c:9845` are Darknut 2–3, Ball and Chain 3,
  Madderpillar 1 chain, Acro Bandit 2, Like Like/Rupee Like/Takkuri 3, and a
  shared Wizzrobe family 6–8. These old caps are evidence of costs, not tested
  new-engine limits.
- Legacy `cost` means dynamic GFX slots in TMC. Price new enemies independently
  in actor slots, OAM objects, OBJ tiles, projectiles and measured cycles. A
  one-placement creature must not hide an unbudgeted swarm.
- Ground encounters require reachable dry floor and recovery space. Perched
  encounters need an intentional perch and a clear announced approach.
  Burrowers must validate terrain and avoid spawning under the player,
  permanent obstacles or item gates. Disappearing phases must not silently
  complete a required clear-room event, strand the final enemy or alter quest
  barriers. These are new-engine integration checks motivated by documented
  original failures, not claims of implemented safeguards.

## Relation to the current build and art direction

The current standalone definitions remain five ordinary families plus Heart:
HP 2/2/2/4/10/40, body damage 2/2/2/2/4/4, with the selected step-and-cut sword
timing. They are not the full old roster. The old reference's animation timing
does not override the user's subsequently chosen sword. Accepted sprites,
terrain, UI and mechanics should remain intact while new behaviors are
exercised in controlled prototypes.

The shared art bible, direction log and reference register were read before
these notes. No new visual style is adopted here. Apply their native 16px-cell,
RGB555/palette, consistent foot baseline, quiet floor and silhouette-before-
detail rules to later creature art. Telegraphs must advertise a real state
transition, armor plates must correspond to actual protection, and a ground
contact shadow must correspond to real altitude. Filth/glitter decoration
must not masquerade as a pickup or conceal a damaging edge. New source code
should implement these behavior ideas independently; copying the reference
state machines or artwork is unnecessary.
