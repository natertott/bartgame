# Animation scheduling and unlit-torch cache qualification

`tools/perf_system_equivalence.py` runs the actual baseline and candidate
animation C functions on the host, recording the ordered DMA writes and
palette writes. Animation descriptors and every frame byte come from the
frozen previous ROM's three linked tilesets: forest75, Drain69, mystery6.

The suite compares244,052 calls, including all65,025 combinations of nonzero
byte-sized speed and frame count. Mixed255-descriptor lists stress shared
speed quotients, all eight seen-bit words, power-of-two/non-power-of-two frame
counts, and24 zero-frame descriptors whose speed is also zero. Disabled
animation is checked separately. Active descriptors require nonzero speed,
matching the authored assets and the original division contract.

Clock-read fixtures preserve the actual volatile-read sequence and inject
constant, incrementing, wrapping and reset values, including changes between
the due test and the second frame-selection read. The latter catches the
speed1 interrupt corner. The final run matches512,772 ordered DMA events and
12,910 palette writes, with3,552,202 observed clock-value transitions. No
descriptor, frame count, playback interval or native pixel is removed.

The same command invokes `tools/perf_torch_equivalence.py`. Its actual old/new
room write APIs and raw/cached torch scans run against native metatile types,
properties and collision masks. Geometry, substrate selection, torch lighting
and collision rebuilds use the extracted C. Video, forest planning/rendering,
interactive notifications and FX are pure test stubs. The actual
`roomgen_preview_details()` save/restore routine uses a disclosed deterministic
generator stub which writes through the room APIs and does not query the cache
inside a preview, matching the production generator's call contract.

The torch suite passes12,959 cases and259,347 assertions, including90,713
repeated cache hits without extra scans,6,855 invalid-coordinate writes,42
torch-light transitions and29 valid/invalid preview cases. No invalidation
defect was found. Direct raw room restoration inside a future preview which
also queries the cache would need explicit invalidation; the current generator
never queries it during a preview.

An independent unprofiled ARM compilation with the production Thumb/O2 flags
reports `tiles_animate()`'s own static stack allocation as48 bytes before and
1,104 bytes after. This is the compiler's function allocation, **not** a total
stack high-water measurement: caller frames, library callees and interrupts
are excluded. Production stack headroom and full-game behavior are separately
qualified by the native performance review.

These source differential tests establish scheduling/cache equivalence under
their disclosed fixtures. Real room generation, gameplay, forest depth,
framebuffer output and cycle costs require the matched mGBA suite. Reports
record source hashes and the frozen native-asset ROM identity.
