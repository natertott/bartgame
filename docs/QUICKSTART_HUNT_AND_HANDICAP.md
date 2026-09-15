# The hunt quest, the handicap, and the scroll-seam fix

Three things that landed together, because they share a flag bank and an
enemy placer.

---

## 1. Scroll seams (the Grimblade dojo bug) - FIXED

**Symptom the user reported:** wave gauntlets in the dojo under the Castle
Garden ladder spawn enemies "in both the Dojo room and the antechamber", and
the fight can never be cleared.

**What is actually going on.** Rooms inside one area share a pixel grid.
`gAreaRoomHeaders` gives each room a `map_x`/`map_y` and a size, and two rooms
whose rectangles touch along an edge are joined by a **scroll seam** - the
player crosses by walking, with no door and no fade. The engine wipes
`gRoomVars.flags` on the crossing, and that is where every "? room" event
keeps its per-visit state.

Measured in the emulator:

| room | origin | size |
|---|---|---|
| `ROOM_DOJOS_GRIMBLADE` (arena) | (1280, 0) | 240x192 |
| `ROOM_DOJOS_TO_GRIMBLADE` (ante room, ladder) | (1280, 192) | 240x160 |

Walking south off the arena floor crosses in **43 frames**. A room flag set
before the crossing reads back as **0** in the ante room, and still 0 on
returning.

So: back up 24px mid-fight and step forward again, and both the "this wave is
already spawned" latch and the wave counter are gone. A fresh wave 1 spawns
on top of everything still alive. Do it a few times and the arena holds more
enemies than can be cleared. The second half is that enemies chase, so a wave
walks itself into the ante room and camps there - still counting, because
`QuickStartEnemyIsOurs` matches on `ENT_PERSIST` rather than room bounds.

**The fix.** The gauntlet's state moves out of the room flags into
`FLAG_BANK_11` bits 43-58, tagged with the room it belongs to. Only one
gauntlet runs at a time, so one record is enough. `LIVE` and `SPAWNED` are
separate bits, because there is one frame between clearing a wave and
spawning the next where the gauntlet is live but nothing is out - folding
them together would lose the counter if the player crossed during it. Stray
enemies get the leash the miniboss kind already puts on out-of-bounds
Wizzrobes, generalized to any of ours.

**`tools/quickstart/seam_audit.py`** enumerates seams from the ROM. Five
QUICKSTART rooms have one:

| room | seam |
|---|---|
| `ROOM_DOJOS_GRIMBLADE` | south -> `TO_GRIMBLADE` |
| `ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST` | east -> `RANCH_HOUSE_EAST` |
| `ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST` | west -> `RANCH_HOUSE_WEST` |
| `ROOM_CAVES_LON_LON_RANCH` | east -> `LON_LON_RANCH_SECRET` |
| `ROOM_HYRULE_CASTLE_CELLAR_0` | east -> `CELLAR_1` |

Grimblade is the only one hosting combat, which is why only it was reported.
The other four are small kinds, whose latches are cheap to lose. **Run the
audit before giving any new room a stateful event.**

---

## 2. The handicap

"Take away all items, buffs and upgrades and leave one weapon." Used by the
hunt below and, as a rarer variant, by the ? room wave gauntlet.

### Where the snapshot lives

`game.o` gets no `.bss` or `.data` - `linker.ld` is an absolute NOLOAD layout
- so there is nowhere in that file for one. It goes in `gSave`, in the three
u32s the engine itself documents as unused (`timer4`, `timer5`, `timer6`,
save.h). They are already saved, restored and zeroed with everything else,
and nothing anywhere in the tree reads them.

| field | holds |
|---|---|
| `timer4` | the hunt's countdown, in frames |
| `timer5` | one bit per `sQuickStartHandicapItems` entry that was owned and taken (hence the 32-entry cap) |
| `timer6` | `equipped[0]` \| `equipped[1]`<<8 \| `equippedExtra[0]`<<16 \| charm mask<<24 |

The equip slots have to be saved: taking the item out from under them leaves
the HUD pointing at something the player no longer holds.

### What is and is not taken

Taken: every weapon, tool, movement upgrade and learned sword skill - 31
items. Charms are suspended by clearing our own ownership bits
(`QUICKSTART_CHARM_BIT`, which `CalculateDamage` reads) plus the vanilla byte
`GetPlayerPalette` tints from.

**Not** taken: the Kinstone Bag and Wallet (bookkeeping - taking them would
strand rupees and pieces), bottles (a bottled fairy is a life, and taking
lives is a crueller mechanic than taking weapons), the Lon Lon key, and bomb
/ arrow **counts**. Zeroing the item already makes a weapon unusable, so
leaving the counts alone saves two bytes of snapshot and a class of bug.

The kept weapon is topped up to 30 rounds if it needs ammo, and that is **not
clawed back** afterwards - knowing what to claw back to would cost two more
bytes of snapshot, and a few spare bombs is a fair trade for having taken
everything else.

### Which weapon you keep

Rolled at the moment the handicap is applied, not at run start, because it
has to be something the player actually owns - a "bombs only" challenge given
to a run that never found bombs is not hard, it is unplayable. Order is
sword, bombs, bow, Fire Rod; the roll walks forward to the first one owned
and falls back to the sword, which every run has.

### Getting your kit back

Three ways, and they overlap on purpose:

1. The challenge is won (reward drops).
2. The challenge is lost (timer expires).
3. **The player leaves the room that applied it.** `QuickStartHandicapMonitor`
   runs from the room monitor in *every* room for exactly this - without it,
   walking out of a stripped-kit fight would strand the player on one weapon
   for the rest of the run.

---

## 3. The hunt quest

One giver per run, standing in one region of the chain. Talk to it, a pack
appears, a clock starts. Kill them all in time and it pays; miss and the
giver leaves - **one attempt per run**, per the brief.

| | |
|---|---|
| Time limit | 45 seconds (`QUICKSTART_HUNT_SECONDS`) |
| Pack size | 4 + difficulty/2, capped at 8 |
| Pack tier | run difficulty **+2** - a hunt is a step up from the wave already in the room |
| Handicap variant | 1 hunt in 3 |
| Reward | ladder pool normally; **rare** pool for the handicap variant |

**Placement.** The giver stands on one of the region's own enemy offsets -
the same table the pot quest uses, for the same reason: every entry is a
pre-verified walkable spot already filtered for item-gated zones by
`QuickStartPositionAllowed`. The roll walks forward from its index so a
blocked spot falls through rather than dropping the quest. Identity is by
position, not a flag, so it survives the entity list being rebuilt on every
room load - same trick as the kinstone fusers.

**Telling the pack apart from the region's endless waves** matters, because
both are in the room at once. Hunt enemies carry `enemyFlags` bit 7, the one
bit of that field vanilla never defines (`enemy.h` stops at
`EM_FLAG_MONITORED`, `1 << 6`).

**The clock** is drawn in the HUD's small-key slot (`DrawKeys`, ui.c).
QUICKSTART has no dungeons, so `AreaHasKeys()` is false everywhere reachable
and that counter - its BG0 cells, its icon and its two digit tiles - is dead
weight already wired up. It turns yellow under ten seconds, reusing the
over-cap rupee colour. Two digits is the hard cap on the time limit.

The icon is still a key. It reads as "a thing you are being timed on" well
enough; **a proper hourglass tile is the obvious follow-up.**

---

## 4. Flag map (FLAG_BANK_11)

| bits | owner |
|---|---|
| 0-31 | region chain per-slot wave counters |
| 32-39 | the pot quest |
| 40-42 | charm ownership |
| **43-58** | **live wave-gauntlet record (seam fix)** |
| **59-73** | **handicap record (active + owning room)** |
| **74-84** | **hunt quest (rolled, slot, spot, handicap, state)** |
| 85-191 | free |

All of 43-84 is cleared at the run boundary in `GameTask_Transition`, along
with `timer4`/`timer5`/`timer6` - a stale snapshot would otherwise hand the
next run a pile of free items the first time anything called
`QuickStartHandicapRestore`.

---

## 5. What has NOT been verified in play

Stated plainly, because it matters more than the design notes above:

- **The hunt has not been seen running.** It builds, the ROM boots, regions
  populate normally and the idle HUD is unchanged - but the scripted harness
  cannot walk up to an NPC and press A, so the offer, the clock, the pack,
  the win and the timeout are all reasoned rather than observed.
- **The handicap has not been seen applied.** Same reason.
- **The seam fix has not been seen fixing a live gauntlet.** The *diagnosis*
  is measured (origins, sizes, the 43-frame crossing, the flag reading back
  as 0), and the record lives in `gSave` rather than `gRoomVars` so it
  cannot be wiped by a crossing - but the end-to-end fight was not played.

First things to watch in a real session: does the giver appear at all; does
the key-slot clock render where the key counter would; and does a stripped
kit come back in full after both a win and a walk-out.
