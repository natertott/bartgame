# Original-world mechanisms in additive courses

The Challenge desk reaches four mechanism courts, independently of the
existing forest, Drain and mystery rooms. They use native32px canvases
with16–28px object silhouettes and their own small streamed-frame pool.
`handoff_events` exclusively dispatches build/enter/pre/update/draw/tool,
collision and completion hooks. Every moving item is a live world object;
source artwork sheets are not evidence of runtime behavior.

The mechanical court offers movable statues, graves, furniture and rocks,
pressure switches, pull/push/hit/heavy levers, and Big Key, Farm Key,
Graveyard Key, metal, light and battle doors. R plus direction moves props
at0.5px/update; the south exit footprint is forbidden to moved furniture.
A real two-foe guardian pair controls the battle door. Trained clones can
press the same physical pressure plates as Bloom and movable blocks.

The crossing court offers floating rafts, lava platforms, lily pads,
steam vents, fans, a launch whirlwind and circling bars/fire. Platforms
move and carry supported feet; a root floor hook distinguishes their actual
footprint from the pit/water underneath. Native hazard tiles belong to the
annex pack, avoiding an unloaded global tile's black fallback. Broad ice,
swamp, dust, shallow water and crumbling-floor stations expose their real
surface verbs without modifying old areas.

The hidden court offers an inspectable hidden ladder, a watered beanstalk,
paired warps, delayed trapdoors, a rotating trapdoor, a lever-appearing bridge
and a three-phase weather vane. Weather adds physical wind or native rain;
its draw pass allocates no effects. A physically enclosed Minish pocket has
a4px gap and visible portal; three separate clone plates provide room to
stage the Four Sword formation.

The tool court offers a Pacci-flippable pot, a suction-load that launches
through the existing thrown-object physics, timed torches, eye/light/hit
switches, a jar-shaped Minish portal, soft earth/dig walls, dash walls,
spring holes, ice and a water sprout. A32px ice block melts under fire or
mineral water; a frozen flower thaws and offers a single healing use;
a barrel's web burns or vacuums away. A narrow directional light ray hurts
an unprotected player; the Mirror Shield facing the beam reflects it to a
receiver. Downstairs and a visibly distinct destination hole form a pair:
travel validates a dry, unblocked landing before an actual falling arc,
instead of applying damaging-pit behavior to a fake destination.

`art/handoff_objects.py` adds42mechanism families with idle/active native
frames and a tiny8px rain/leaf/ray family. It never reads or changes old
sprite pixels. Each course uses at most24objects and reserves16OBJ tiles
per present object, with frame uploads in the existing VBlank item stream.
The new object records and cold course state live in EWRAM; old fast-memory
buffers are unchanged.

These courses preserve the handoff's interactive categories. They are
original adaptations, not a claim that every vanilla cinematic prop or
object subtype has been recreated one for one. ARM syntax checks and the
integrated mGBA review distinguish code-connected behavior from actions
observed in the emulator.

`python tools/handoff_objects_host.py --out OUT` executes the actual course C
against explicit room/input spies. Its277checks cover all four course bounds,
exact32-update/16px pushing, exit reservation, clone pressure, fire/mineral
versus ordinary water on ice, thawing and suction,180/240update timers, the
actual three-row appearing bridge, reflected-ray receiver contact and inert
hooks after reset. The fixture does not establish rendering quality or GBA
performance; `handoff_objects_native.py` records the real emulator separately.

Final release3 qualification: all95item/object native checks pass; see
[evidence and exact ROM hash](evidence/items-objects/README.md).
