# Forest second-pass engine review

Read-only review against `69b69ba0`, with current `0dce1529` plus the pending engine corrections. No repository files were edited. Read `AGENTS.md`, current art bible, direction log/reference register and `FOREST_V2_ENGINE.md`.

## Concrete finding

**Corrected during review: recoil body/tool depth differed.** `player_draw()` computes normal terrain priority, then assigns `a->prio = 1` for the new NORMAL/positive-height/low-fringe exception (`src/player.c:1031`). Its held tools use that final priority. However, `actor_draw()` recomputes `room_prop_priority()` at `src/actor.c:364`; the overhead-first branch (`src/room.c:394`) returns 2 for either input 1 or 2 on that same low fringe. Thus the body can stay behind the canopy while its held tools are in front, and the intended recoil readability exception is undone for the body. Sent the exact call chain to the engine owner and root before freeze. The body must use the same final priority as its tools; shadow must keep its separate ground sorting.

## Checked without another concrete issue

- `>= 6` preprocessing guards keep the new render/generator behavior outside production/first-round profiles. Existing independently frozen legacy byte results are evidence supplied by the main audit, not claimed as a new rebuild by this code review.
- Two visual maps each contain `32 * 32` u16 entries (4096 added EWRAM bytes combined). Renderer indexing uses bounded room coordinates; original semantic/collision maps remain gameplay authority. The four 32x32 screenblocks per layer fit the existing 64x64-tile hardware map contract.
- Canopy/water aliases read only the generated lookup tables; MT_NONE is checked before indexing. Neighbor queries bound room coordinates. Concave-corner bits require both cardinal connections. Rendering a changed ground cell also refreshes its eight neighbors.
- Isolated water retains real hazardous collision while transparent exterior pixels reveal an explicit local floor on BG2. An occupied meaningful overlay retains its foreground instead of making an alpha hole. Crown detection runs before water promotion, preserving foreground depth.
- Pulse updates are disabled outside live non-Drain gameplay; generated slots map only resident world palettes. Menu/HUD/OBJ palette banks are not pulse destinations. Paused menus retain phase and restore OBJ palettes through the existing menu path.
- Landmark frames reserve dedicated streamed OBJ slots, share the lock payload across multiple gate pairs, and use one keyhole per physical gate pair. Missing allocation falls back to legacy BG markers. Wood B appends frames6/7 and changes only appearance through a deterministic hash, not RNG/reward tier.
- Log promotion calls the existing complete-footprint plain-ground/connectivity guards. The late pair repair removes an orphan instead of rebuilding a blocking half over the route/event that consumed it; it restores dry passable underlay and consumes no RNG. Full large-seed rerun belongs to the main audit; this review does not relabel its earlier failed corpus as final passing evidence.
- Root-arch placement requires solid outer banks, an existing marked trail, empty overlay slots and an actual zero-collision north/under/south lane. Event clearance is explicit and rank uses a deterministic hash. The upper span is scenery; it does not falsely introduce a second accessible elevation.
- Opened crack/web/key gates regenerate as trail. Clearing a thorn/crack/web/key barrier chooses its saved legitimate floor before adjacent/area fallback, preserving physics and world progression ownership.

## Final correction and independent packer check

The engine owner has replaced the local override with `player_recoil_priority()`, called after normal terrain sorting both in `player_draw()` and in `actor_draw()`. The helper restricts the exception to `a == gPlayer`, NORMAL, positive height and the dry low-fringe predicate; the separately drawn shadow and all other actors retain their original sorting. The final call chain now leaves body and held parts at the same priority, resolving the concrete finding above. This source review verifies the correction; final frozen compilation and mGBA body/tool/shadow frames remain part of the runtime suite.

An independent sub-review freshly packed all five profiles outside the repository and ran **201,845 passing checks** (40,369 each). It reconstructed every held metatile/animation quarter from native tile/map/palette payloads, checked alias range/parent/overhead metadata, 47-shape lookup validity, contiguous animation storage, RGB555 pulse inks and area palette isolation. Profiles6–10 use 855/851/853/851/852 forest subtiles with ten world banks, 73 animation allocations; Drain stays822/one bank and mystery107/six banks. The supplemental reviewer-local evidence is `topology-review/results.json` and `topology-review-check.py` under `/workspace/setup/forest-concepts-v2`; those working files are not included in this publication. This supplemental review freshly ran isolated source packs and independently decoded native tile/map/palette/animation payloads without calling the publisher. Its coverage overlaps the final native/source audit published alongside this report.

**Code-review result: no unresolved concrete defect found.** No repository edits by this reviewer. This report does not substitute for final frozen build/runtime/large-seed verification.


## Bounded approach-repair follow-up

Reviewed the engine owner's explicit ready candidate after `deb9e835` (current `src/roomgen.c` SHA256 `4e47daa50032c1c33c952560bf3dcaf26b1aad9687146ed2be2929805c44f07e`). No unresolved concrete bug found in the added approach repair. This is source review, with the owner's ten named regression traces inspected separately; the final frozen large-seed/runtime audit remains pending rather than assumed.

- `required_reserved` prevents later solid furniture from claiming an existing mouth/frame/threshold, chest's south stance, NPC lane, shrine activation space or earlier quest-torch stance. Normal random placement uses it before furniture changes physical terrain.
- Finite `scan_fronted_spot` retains existing floor and its entry-connected south stance. Its `simple_spot` predicate verifies the target is an ordinary empty floor and local connectivity remains around the new solid.
- The bounded clearing fallback chooses an **already-solid** future furniture cell. Its complete3×3,2×2 or1×2 footprint has an existing entry-reached floor connection away from that center. Returning the center to solid furniture therefore cannot consume the old connection. Every cell is interior, accepts only dry floor/solid/liftable material, excludes meaningful overlays/reserved earlier landmarks, and performs no water/cliff/perimeter-gate carving. The fallback precedes optional pockets, so it cannot carve through a later item gate.
- Mouth fallback connects its actual south approach directly to the existing entry component, while excluding the full future solid frame. `from`/queue arrays are boundedW×H; an interior tile is marked before enqueue and is visited once. Reverse directions `k ^ 2` match N/E/S/W, and reconstruction stops at the sentinel start before indexing it as a direction. Existing unpassable water becomes a ground-level plank bridge; explicit item barriers/exit tiles are excluded.
- `sEntryX/Y` is assigned from the actual selected door/center before it is used. Reflooding from that entry after the new mouth and role furniture prevents stale reach data from choosing monster/reward positions in a disconnected center. New state does not enter World/save, and all added behavior is guarded for profiles6–10.
- New static BFS storage is2304bytes for a32×24 room; it is finite and below the prior IWRAM headroom. The final linker boundary still needs its ordinary frozen audit check.

No generator, art or source file was changed by this reviewer.


## Final source revision

The production/art source was frozen after these corrections as `e5e3fcb21fe1bcc50c965943164146a2dc1e3c46`. The final native/source and generation audit is the authoritative frozen result: its source-bound report records 121,211 passing checks including the 20,000-seed / 500,000-room host corpus. The source-gallery verifier separately records 47,515 passing checks. Earlier draft traces and the supplemental isolated-packing counts above are explicitly supporting review history, rather than replacement provenance for the final artifact. Final emulator capture counts and the final publication manifest are reported in the adjacent validation summaries.
