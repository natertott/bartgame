# Run completion and Continue

A victory retires the active run immediately, before the victory screen.
The next title visit or cold boot offers New Game and Options, and starting
play generates a new forest with the normal starting inventory. Victory-screen
statistics remain available until the player leaves that screen.

Continue accepts only a valid, unfinished run. Old version1/version2 saves
whose goal cell has `CF_CLEARED` are rejected too, so the previous dead-Heart
softlock does not survive upgrading the ROM. That flag is checked only on the
goal cell; clearing another room never invalidates an unfinished run. The
stored goal index is checked before accessing its cell. A post-Heart death
or other save attempt cannot recreate a completed run record.

The run record's existing version, size and checksum are unchanged. Retiring
it clears only its eight-byte header. The independent discovery journal and
appearance preferences remain intact across victories and new runs.

The real ending is collecting the Grail after defeating the Heart. The goal's
cleared flag also identifies old post-Heart records without the transient Grail,
which could not previously finish after loading. Those records begin a fresh
run instead of offering an empty completed world.

`tools/victory_save_review.py` exercises actual sword combat/Grail collection,
title return, cold boot, fresh generation, profile retention and saved-record
admission. `tools/save_probe.py` separately verifies existing unfinished-run
migration and continue behavior. Release notes bind the final build and results.
