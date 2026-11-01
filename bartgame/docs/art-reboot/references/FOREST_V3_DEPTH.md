# Canopy visibility in the third forest studies

The user's 2026-11-01 feedback rejects unrecognizable canopy masses and asks
for lateral branches that partly cover Bloom without making him disappear.
The new native canopy drawings provide the normal overlap. A small rendering
safety layer preserves a recognizable part of Bloom at dense intersections.
This behavior is conditional on forest profiles 11–18; earlier profiles keep
their existing rendering path.

## Existing artwork, retained depth

The original complete Bloom body stays at its normal environmental priority.
It can still pass behind the real BG1 leaves. The safety layer uses a second
32×32 OBJ allocation containing a masked subset of the **current native body
frame**. It has the same foot anchor, airborne offset, palette and horizontal
flip as the body. It adds no invented pixels, outline, color or pose.

Only the lower source portion is eligible. Starting at the bottom, the cutoff
grows upward until it contains at least 48 opaque pixels and 24 meaningfully
colored pixels, or a third of each whole-frame count when that is larger.
Counts are capped at the number of pixels actually present in the source.
A twelve-pixel connected colored component is required where the original
frame contains one; otherwise the entire small frame remains available. This prevents
a numerically large collection of detached feet/highlights from becoming the
only visible sign of the character. The asset builder computes this native
source analysis once for all hero frames and emits an immutable ROM table.
Runtime rendering reads its cutoff and four counts without scanning poses or
searching connected components while the action clock is running.

The meaningful-color predicate uses the existing RGB555 palette: a nonzero
ink with a largest channel of at least 5 and a channel sum of at least 10.
It is a review threshold, not a palette replacement or a contrast guarantee
against every possible background.

The mask copies an eligible source pixel only where the current BG1 pixel is
both vegetation and opaque. It reads the real resident tile and screen-map
entry, including horizontal/vertical tile flips. Transparent leaves already
show the original body and need no duplicate pixel. Architecture remains
untouched; there is no rectangular opening cut into the world.

Authored crowns, connected canopy aliases, special tree crowns and projecting
foliage qualify. Timber root-arch roofs deliberately retain ordinary underpass
occlusion; they are separate from the canopy visibility exception. Ground
shadows keep their original independent depth and position.

## Tools and intentional disappearance

When a protected fragment is needed, the directionally front-held draw group
temporarily uses foreground priority too. Its existing OAM order keeps it in
front of the protected body pixels. The complete body then returns to its
normal priority before drawing. North-facing shields and other far-side
parts retain their original behind-body priority. This avoids drawing feet or
lower-body ink over the front of a shield.

The tradeoff is explicit: front-held tools can remain clearer than the leaves
during this safety interval. The upper body is still genuinely occluded; the
whole character does not jump to the foreground. The older whole-body
wall-recoil priority exception is disabled in these new profiles.

Hidden flags, normal hurt blinking, intentional death blinking and the
existing final fall/drowning disappearance still apply. A shrinking frame is
not enlarged to meet a pixel quota. For example, the unchanged `fall_3` source
contains only four meaningfully colored pixels in two small components.
The safety layer preserves that authored shrinking behavior. Falling uses
the same no-z drawing origin as the existing fall body; ordinary poses and
jumps use their actual airborne offset.

## Transfers and resource contract

The forest player reserves one additional 16-tile OBJ slot. It is allocated
only in the forest, so Drain and mystery-room sprite allocation is retained.
An active fragment consumes one additional OAM entry. The conservative world
OBJ union increases from 848 to 864 of the 876 available tiles.

Visibility uploads use a dedicated packet flushed after the ordinary 16-entry
VRAM queue. Its capacity is independent of that queue. The packet refreshes
the unchanged current full body and the 512-byte mask together, preventing a
busy queue from leaving a stale fragment over a newer pose. Ordinary queue
capacity and ordering remain unchanged. This is a fixed-size transfer path,
not an unbounded upload list.

The mask and diagnostic observations add 536 EWRAM bytes; queue/render state
adds 28 IWRAM bytes in the offline-table pilot. Its linked totals are 216,820
EWRAM bytes and 21,928 IWRAM bytes. The 133-row table uses 1,330 ROM bytes.
Final frozen resource measurements supersede these pilot values. Runtime
masking checks the eligible lower pixels on each active draw. Recorded
game/IRQ cadence is separate evidence and must not be described as a universal
CPU benchmark.

## Review evidence and diagnostic interface

`gForestV3Visibility` contains twelve unsigned 16-bit software observations:

| Index | Meaning |
| ---: | --- |
| 0 | A fragment OAM entry was emitted this draw. |
| 1 | Native hero source frame used for cutoff selection. |
| 2 | Stable reserved fragment OBJ tile index. |
| 3 | First eligible native source row. |
| 4 / 5 | Whole-frame / eligible-lower opaque counts. |
| 6 / 7 | Whole-frame / eligible-lower meaningful-color counts. |
| 8 / 9 | Actual copied opaque / meaningful-color counts. |
| 10 | Original body terrain priority. |
| 11 | Emitted fragment OAM index, or 65535 when absent. |

These observations are not framebuffer pixels and may be one update ahead
of displayed hardware. Actual OAM, resident body/mask tiles, BG1 map/ink,
applied camera and native framebuffer colors remain the authoritative proof.

The isolated native-source check first executed the literal extracted cutoff
helpers against all 133 current hero frames. All pass their size/count and
connectivity contracts, with the original tiny shrinking `fall_3` explicitly
identified. The emitted offline metadata then matched that independently
executed reference algorithm exactly in every one of its 133 rows. A separate
literal C queue check uses a memcpy DMA stub to verify
the ordinary sixteen entries, unchanged seventeenth-entry rejection, dedicated
visibility upload ordering and pending reset. Neither host check is emulator
or transfer-timing evidence.

The updated isolated profile 6 ROM remains byte-identical to its previous
release, SHA256
`fc8e92f92a4aa43aa5cc56c0caff7a6dc1394f21dc356e7830ef9a7e07f234a1`.
New profile 11 compiles without warnings. The first actual pilot exposed a
real cadence regression from runtime pose scanning and connectivity searches:
several video intervals did not advance gameplay, and same-input endpoints
no longer matched the control. That pilot is superseded, and the immutable
ROM metadata removes that work. The strict action/position comparisons are
retained. Final publication still requires
the separately frozen actual movement, roll/recoil, jump and four-direction
sword/shield captures, including partial cover and visible-body checks.
