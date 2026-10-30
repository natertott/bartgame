# Drain visual inventory


> Current study additions: the physical tile/room inventory below is inherited
> unchanged from the released source contract. The concept builds retain the
> appended `peddler_body.breathe` ID 14 from v2, giving **15 frog body frames and
> 30 world keeper/flame frames** in total. Portraits have a separately authored
> 48×48 drawing inside the retained padded sheet. The complete current artwork,
> selected recipe styles and frame hashes are in [catalogue.json](catalogue.json).
> Historical source bounds identify feature envelopes, not a requirement to
> preserve old pixel silhouettes.


Basis: `1f2dc676a5c9c533cffdc8121561cdf7cd34e762`. The room is **30×20 cells / 480×320 pixels**, with 16×16 metatiles and 8×8 hardware quarters.

**370 active tile IDs**: 350 ground IDs across600 cells,20 foreground IDs across57 nonempty cells. There are332 static IDs and38 animated IDs, comprising623 native metatile-frame drawings. These opaque numbered IDs are pieces of larger fixtures, not 370unrelated objects.

The room layout, quarter collisions and object anchors remain fixed. Collision bits are8/4/2/1 for top-left/top-right/bottom-left/bottom-right.

## Complete visible fixture vocabulary

| ID | Fixture | Native source bounds (inclusive pixels) |
| --- | --- | --- |
| north_wall | Gray retaining brick wall | 0,0,479,63 |
| side_walls | Raised side masonry | 0,64,15,271; 464,64,479,271 |
| slimy_floor | Walkable damp gray brick/flagstone floor | 16,64,463,143; 16,208,463,271 |
| channel | Central flowing sewage stream and scum | 16,144,463,207 |
| north_coping | Near bank lip above the stream | 16,144,463,153 |
| south_coping | Far bank lip below the stream | 16,193,463,207 |
| north_rail | Rail/post foreground along north bank | 16,128,223,143; 256,128,463,143 |
| bridge | Narrow central usable bridge with landings | 224,144,255,207 |
| bottom_rail | Lower foreground railing | 16,256,447,271 |
| bottom_bank | Lower coping and hanging lichen | 0,272,479,287 |
| bottom_water | Lower dark water and moving reflections | 0,288,479,319 |
| cistern | Large barred wall outfall, waterfall and basin | 184,0,292,105 |
| forest_ladder | Functional ladder, dark aperture and warm arch | 128,16,175,63 |
| gold_pipe_h | Horizontal brass pipe with couplings | 18,31,125,42 |
| gold_pipe_v | Vertical brass wall pipe with couplings | 417,6,427,62 |
| market | Peddler market awning, counter and supports | 16,57,127,110 |
| market_goods | Counter bottles / displayed wares | 38,77,42,88; 99,76,103,87 |
| wizard_rug | Keeper/wizard rug | 304,71,382,111 |
| wizard_shelf | Keeper shelf and animated brass candles | 288,51,382,68 |
| storage | Two wooden crates and a barrel | 400,65,423,94; 424,65,447,94; 440,72,458,95 |
| grime | Grease/lichen deposited below pipes and banks | 28,43,48,56; 87,43,107,56; 429,62,449,75; 166,108,186,121; 368,116,388,129; 50,224,70,237; 389,246,409,259 |
| puddles | Oily floor puddles | 139,101,163,111; 320,122,344,132; 88,228,112,238; 322,228,346,238; 213,209,237,219 |
| small_outfall | Small corroded sewage spout pouring into stream | 427,116,448,175 |
| floor_grate | Walkable lower barred drain / grate | 207,225,273,255 |
| authored_glints | Small art-authored animated highlights | 33,34,33,34; 119,33,119,33; 151,30,151,30; 225,16,225,16; 261,83,261,83; 295,62,295,62; 372,62,372,62; 438,137,438,137; 219,229,219,229; 265,246,265,246 |

Source bounds identify authored feature regions before repeated IDs are replaced with reusable material panels. A tile may contain several regions. The exact per-ID placements are in [inventory.json](inventory.json).

## Every keeper sprite and face

| Sheet | Native canvas | Frames | Purpose |
| --- | --- | --- | --- |
| `peddler_head` | 16×16 | `open`, `blink`, `left`, `down`, `grin` | Billious Peddler face; new direction must be absentminded cartoon frog |
| `peddler_body` | 32×32 | `rest`, `tap`, `tap2`, `lift`, `spin9`, `spin7`, `spin5`, `spin3`, `spin5b`, `spin7b`, `spin9b`, `slap`, `rub0`, `rub1` | Billious Peddler body, hands and coin |
| `gatekeeper` | 32×32 | `idle`, `blink`, `breath`, `breath_blink`, `kindle`, `kindle_blink` | Pale Gatekeeper body; new direction is old hooded purple wizard with staff |
| `wisp` | 8×8 | `w0`, `w1`, `w2`, `w3` | Animated keeper orb flame; new direction should anchor to staff tip |
| `face` | 64×64 | `peddler` | Peddler dialogue/shop portrait |
| `face` | 64×64 | `gatekeeper` | Wizard dialogue portrait (existing gatekeeper identifier) |
| `glitter` | 8×8 | `none`, `dim`, `glint`, `star`, `glint2`, `fade` | Existing surface-attached glitter; user explicitly likes it |

The frog merchant is anchored at foot (72,94), cell (4,5). The purple wizard replaces the current sage/Gatekeeper at foot (344,94), cell (21,5). The forest ladder/exit is at cell (9,2); the initial spawn is cell (12,16). The head/body split and animation frame identifiers can remain intact.

Preserve the six glitter drawings, surface-aware emitter, phase schedule and 24-site viewport budget. Existing art-authored material glints also coexist with that system.

## New study-only handrail sprite

The concepts append `sewerrail.rail`, a **16×8** native sprite using two hardware
tiles and the unchanged global gold OBJ palette (`fx`). Each of five metal
styles supplies one alternative. Up to 26 camera-culled strips connect the
existing north-bank posts, leaving the bridge opening clear. This adds no room
tile IDs, collision changes, actor-anchor changes or glitter changes. It is
excluded from the baseline 370 tile IDs / 623 tile frames / 29 keeper frames.

## Shared or conditional visuals

- Ordinary HUD: heart/purse/key canvas, three equipment panels, A/B/L badges, counts, equipped icons and minimap. These are common UI, not unique sewer tiles.
- Frog shop and wizard dialogue: frames, native font, portraits, cursors, price/description ink and the heart/bomb/arrow-bundle merchandise icons. Arrows appear for sale only after the bow is owned.
- Start menu: global bag/key-item/map assets. These remain shared with the rest of the game.
- Item-use/return effects: shared pickup, bomb, flame, puff, projectile, arrow, cap-mouth and held-tool sheets can appear conditionally. They are not authored static Drain objects. Bloom and its actions remain unchanged.
- There are no authored Drain enemy, chest, switch, key-door or mystery-room spawns.

## Complete active tile list

Every identifier below has five concept columns in the eventual art selection atlas. Frames and collision/interaction contracts must remain stable. Each row lists all occurrences as `layer:x,y`; `g` is ground and `o` foreground.

| Global ID | Tile | Type | Collision mask | Animation | All occurrences |
| --- | --- | --- | --- | --- | --- |
| 526 | `swh_000` | SOLID | 15 | 1frame | g:0,0; g:0,4; g:0,8 |
| 527 | `swh_001` | SOLID | 15 | 1frame | g:1,0 |
| 528 | `swh_002` | SOLID | 15 | 1frame | g:2,0 |
| 529 | `swh_003` | SOLID | 15 | 1frame | g:3,0 |
| 530 | `swh_004` | SOLID | 15 | 1frame | g:4,0 |
| 531 | `swh_005` | SOLID | 15 | 1frame | g:5,0 |
| 532 | `swh_006` | SOLID | 15 | 1frame | g:6,0 |
| 533 | `swh_007` | SOLID | 15 | 1frame | g:7,0 |
| 534 | `swh_008` | SOLID | 15 | 1frame | g:8,0 |
| 535 | `swh_009` | SOLID | 15 | 1frame | g:9,0 |
| 536 | `swh_010` | SOLID | 15 | 1frame | g:10,0 |
| 537 | `swh_011` | SOLID | 15 | 1frame | g:11,0 |
| 538 | `swh_012` | SOLID | 15 | 1frame | g:12,0 |
| 539 | `swh_013` | SOLID | 15 | 1frame | g:13,0; g:16,0; g:28,0 |
| 540 | `swh_014` | SOLID | 15 | 1frame | g:14,0 |
| 541 | `swh_015` | SOLID | 15 | 1frame | g:15,0 |
| 542 | `swh_016` | SOLID | 15 | 1frame | g:17,0 |
| 543 | `swh_017` | SOLID | 15 | 1frame | g:18,0 |
| 544 | `swh_018` | SOLID | 15 | 1frame | g:19,0 |
| 545 | `swh_019` | SOLID | 15 | 1frame | g:20,0 |
| 546 | `swh_020` | SOLID | 15 | 1frame | g:21,0 |
| 547 | `swh_021` | SOLID | 15 | 1frame | g:22,0; g:25,0 |
| 548 | `swh_022` | SOLID | 15 | 1frame | g:23,0 |
| 549 | `swh_023` | SOLID | 15 | 1frame | g:24,0 |
| 550 | `swh_024` | SOLID | 15 | 1frame | g:26,0 |
| 551 | `swh_025` | SOLID | 15 | 1frame | g:27,0 |
| 552 | `swh_026` | SOLID | 15 | 1frame | g:29,0; g:29,4; g:29,8 |
| 553 | `swh_027` | SOLID | 15 | 1frame | g:0,1; g:0,5 |
| 554 | `swh_028` | SOLID | 15 | 1frame | g:1,1 |
| 555 | `swh_029` | SOLID | 15 | 1frame | g:2,1 |
| 556 | `swh_030` | SOLID | 15 | 1frame | g:3,1; g:6,1 |
| 557 | `swh_031` | SOLID | 15 | 1frame | g:4,1 |
| 558 | `swh_032` | SOLID | 15 | 1frame | g:5,1 |
| 559 | `swh_033` | SOLID | 15 | 1frame | g:7,1 |
| 560 | `swh_034` | SOLID | 15 | 1frame | g:8,1 |
| 561 | `swh_035` | SOLID | 15 | 1frame | g:9,1 |
| 562 | `swh_036` | SOLID | 15 | 1frame | g:10,1 |
| 563 | `swh_037` | SOLID | 15 | 1frame | g:11,1 |
| 564 | `swh_038` | SOLID | 15 | 3frames / 8updates each | g:12,1 |
| 565 | `swh_039` | SOLID | 15 | 1frame | g:13,1 |
| 566 | `swh_040` | SOLID | 15 | 1frame | g:14,1 |
| 567 | `swh_041` | SOLID | 15 | 1frame | g:15,1 |
| 568 | `swh_042` | SOLID | 15 | 1frame | g:16,1 |
| 569 | `swh_043` | SOLID | 15 | 3frames / 8updates each | g:17,1 |
| 570 | `swh_044` | SOLID | 15 | 1frame | g:18,1 |
| 571 | `swh_045` | SOLID | 15 | 1frame | g:19,1 |
| 572 | `swh_046` | SOLID | 15 | 1frame | g:20,1 |
| 573 | `swh_047` | SOLID | 15 | 1frame | g:21,1 |
| 574 | `swh_048` | SOLID | 15 | 1frame | g:22,1 |
| 575 | `swh_049` | SOLID | 15 | 1frame | g:23,1 |
| 576 | `swh_050` | SOLID | 15 | 1frame | g:24,1 |
| 577 | `swh_051` | SOLID | 15 | 1frame | g:25,1 |
| 578 | `swh_052` | SOLID | 15 | 1frame | g:26,1 |
| 579 | `swh_053` | SOLID | 15 | 1frame | g:27,1 |
| 580 | `swh_054` | SOLID | 15 | 1frame | g:28,1 |
| 581 | `swh_055` | SOLID | 15 | 1frame | g:29,1; g:29,5 |
| 582 | `swh_056` | SOLID | 15 | 1frame | g:0,2; g:0,6 |
| 583 | `swh_057` | SOLID | 15 | 1frame | g:1,2 |
| 584 | `swh_058` | SOLID | 15 | 1frame | g:2,2; g:5,2 |
| 585 | `swh_059` | SOLID | 15 | 1frame | g:3,2; g:6,2 |
| 586 | `swh_060` | SOLID | 15 | 1frame | g:4,2 |
| 587 | `swh_061` | SOLID | 15 | 1frame | g:7,2 |
| 588 | `swh_062` | SOLID | 15 | 1frame | g:8,2 |
| 589 | `swh_063` | EXIT | 0 | 1frame | g:9,2 |
| 590 | `swh_064` | SOLID | 15 | 1frame | g:10,2 |
| 591 | `swh_065` | SOLID | 15 | 1frame | g:11,2 |
| 592 | `swh_066` | SOLID | 15 | 1frame | g:12,2 |
| 593 | `swh_067` | SOLID | 15 | 1frame | g:13,2 |
| 594 | `swh_068` | SOLID | 15 | 4frames / 4updates each | g:14,2 |
| 595 | `swh_069` | SOLID | 15 | 4frames / 4updates each | g:15,2 |
| 596 | `swh_070` | SOLID | 15 | 1frame | g:16,2 |
| 597 | `swh_071` | SOLID | 15 | 1frame | g:17,2 |
| 598 | `swh_072` | SOLID | 15 | 1frame | g:18,2 |
| 599 | `swh_073` | SOLID | 15 | 1frame | g:19,2; g:25,2; g:28,2 |
| 600 | `swh_074` | SOLID | 15 | 1frame | g:20,2 |
| 601 | `swh_075` | SOLID | 15 | 1frame | g:21,2 |
| 602 | `swh_076` | SOLID | 15 | 1frame | g:22,2 |
| 603 | `swh_077` | SOLID | 15 | 1frame | g:23,2 |
| 604 | `swh_078` | SOLID | 15 | 1frame | g:24,2 |
| 605 | `swh_079` | SOLID | 15 | 1frame | g:26,2 |
| 606 | `swh_080` | SOLID | 15 | 1frame | g:27,2 |
| 607 | `swh_081` | SOLID | 15 | 1frame | g:29,2; g:29,6 |
| 608 | `swh_082` | SOLID | 15 | 1frame | g:0,3; g:0,7 |
| 609 | `swh_083` | SOLID | 15 | 1frame | g:1,3 |
| 610 | `swh_084` | SOLID | 15 | 1frame | g:2,3 |
| 611 | `swh_085` | SOLID | 15 | 1frame | g:3,3 |
| 612 | `swh_086` | SOLID | 15 | 1frame | g:4,3; g:28,3 |
| 613 | `swh_087` | SOLID | 15 | 1frame | g:5,3; g:17,3 |
| 614 | `swh_088` | SOLID | 15 | 1frame | g:6,3; g:12,3 |
| 615 | `swh_089` | SOLID | 15 | 1frame | g:7,3 |
| 616 | `swh_090` | SOLID | 15 | 1frame | g:8,3 |
| 617 | `swh_091` | FLOOR | 0 | 1frame | g:9,3 |
| 618 | `swh_092` | SOLID | 15 | 1frame | g:10,3 |
| 619 | `swh_093` | SOLID | 15 | 1frame | g:11,3 |
| 620 | `swh_094` | SOLID | 15 | 1frame | g:13,3 |
| 621 | `swh_095` | SOLID | 15 | 4frames / 4updates each | g:14,3 |
| 622 | `swh_096` | SOLID | 15 | 4frames / 4updates each | g:15,3 |
| 623 | `swh_097` | SOLID | 15 | 1frame | g:16,3 |
| 624 | `swh_098` | SOLID | 15 | 1frame | g:18,3 |
| 625 | `swh_099` | SOLID | 15 | 1frame | g:19,3 |
| 626 | `swh_100` | SOLID | 15 | 3frames / 8updates each | g:20,3 |
| 627 | `swh_101` | SOLID | 15 | 3frames / 8updates each | g:21,3 |
| 628 | `swh_102` | SOLID | 15 | 3frames / 8updates each | g:22,3 |
| 629 | `swh_103` | SOLID | 15 | 1frame | g:23,3 |
| 630 | `swh_104` | SOLID | 15 | 1frame | g:24,3 |
| 631 | `swh_105` | SOLID | 15 | 1frame | g:25,3 |
| 632 | `swh_106` | SOLID | 15 | 1frame | g:26,3 |
| 633 | `swh_107` | SOLID | 15 | 1frame | g:27,3 |
| 634 | `swh_108` | SOLID | 15 | 1frame | g:29,3; g:29,7 |
| 635 | `swh_109` | SOLID | 15 | 1frame | g:1,4 |
| 636 | `swh_110` | SOLID | 15 | 1frame | g:2,4 |
| 637 | `swh_111` | SOLID | 15 | 1frame | g:3,4 |
| 638 | `swh_112` | SOLID | 15 | 1frame | g:4,4 |
| 639 | `swh_113` | SOLID | 15 | 1frame | g:5,4 |
| 640 | `swh_114` | SOLID | 15 | 1frame | g:6,4 |
| 641 | `swh_115` | FLOOR | 10 | 1frame | g:7,4 |
| 642 | `swh_116` | FLOOR | 0 | 1frame | g:8,4 |
| 643 | `swh_117` | FLOOR | 0 | 1frame | g:9,4 |
| 644 | `swh_118` | FLOOR | 0 | 1frame | g:10,4 |
| 645 | `swh_119` | FLOOR | 0 | 1frame | g:11,4 |
| 646 | `swh_120` | SOLID | 15 | 1frame | g:12,4 |
| 647 | `swh_121` | SOLID | 15 | 1frame | g:13,4 |
| 648 | `swh_122` | SOLID | 15 | 12frames / 4updates each | g:14,4 |
| 649 | `swh_123` | SOLID | 15 | 12frames / 4updates each | g:15,4 |
| 650 | `swh_124` | SOLID | 15 | 1frame | g:16,4 |
| 651 | `swh_125` | SOLID | 15 | 1frame | g:17,4 |
| 652 | `swh_126` | FLOOR | 4 | 1frame | g:18,4 |
| 653 | `swh_127` | FLOOR | 12 | 1frame | g:19,4 |
| 654 | `swh_128` | FLOOR | 12 | 1frame | g:20,4 |
| 655 | `swh_129` | FLOOR | 12 | 1frame | g:21,4 |
| 656 | `swh_130` | FLOOR | 12 | 1frame | g:22,4 |
| 657 | `swh_131` | FLOOR | 13 | 1frame | g:23,4 |
| 658 | `swh_132` | SOLID | 15 | 1frame | g:24,4 |
| 659 | `swh_133` | SOLID | 15 | 1frame | g:25,4 |
| 660 | `swh_134` | SOLID | 15 | 1frame | g:26,4 |
| 661 | `swh_135` | SOLID | 15 | 1frame | g:27,4 |
| 662 | `swh_136` | FLOOR | 0 | 1frame | g:28,4 |
| 663 | `swh_137` | SOLID | 15 | 1frame | g:1,5 |
| 664 | `swh_138` | SOLID | 15 | 1frame | g:2,5 |
| 665 | `swh_139` | SOLID | 15 | 1frame | g:3,5 |
| 666 | `swh_140` | SOLID | 15 | 1frame | g:4,5 |
| 667 | `swh_141` | SOLID | 15 | 1frame | g:5,5 |
| 668 | `swh_142` | SOLID | 15 | 1frame | g:6,5 |
| 669 | `swh_143` | FLOOR | 10 | 1frame | g:7,5 |
| 670 | `swh_144` | FLOOR | 0 | 1frame | g:8,5; g:8,15; g:20,15 |
| 671 | `swh_145` | FLOOR | 0 | 1frame | g:9,5; g:9,15; g:21,15 |
| 672 | `swh_146` | FLOOR | 0 | 1frame | g:10,5; g:4,15; g:10,15; g:22,15 |
| 673 | `swh_147` | FLOOR | 0 | 1frame | g:11,5; g:11,15; g:17,15; g:23,15 |
| 674 | `swh_148` | SOLID | 15 | 1frame | g:12,5 |
| 675 | `swh_149` | SOLID | 15 | 1frame | g:13,5 |
| 676 | `swh_150` | SOLID | 15 | 1frame | g:14,5 |
| 677 | `swh_151` | SOLID | 15 | 1frame | g:15,5 |
| 678 | `swh_152` | SOLID | 15 | 1frame | g:16,5 |
| 679 | `swh_153` | SOLID | 15 | 1frame | g:17,5 |
| 680 | `swh_154` | FLOOR | 0 | 1frame | g:18,5; g:24,5; g:12,15; g:24,15 |
| 681 | `swh_155` | FLOOR | 0 | 1frame | g:19,5 |
| 682 | `swh_156` | FLOOR | 0 | 1frame | g:20,5 |
| 683 | `swh_157` | FLOOR | 0 | 1frame | g:21,5 |
| 684 | `swh_158` | FLOOR | 0 | 1frame | g:22,5 |
| 685 | `swh_159` | FLOOR | 0 | 1frame | g:23,5 |
| 686 | `swh_160` | SOLID | 15 | 1frame | g:25,5 |
| 687 | `swh_161` | SOLID | 15 | 1frame | g:26,5 |
| 688 | `swh_162` | SOLID | 15 | 1frame | g:27,5 |
| 689 | `swh_163` | FLOOR | 0 | 1frame | g:28,5 |
| 690 | `swh_164` | FLOOR | 12 | 1frame | g:1,6 |
| 691 | `swh_165` | FLOOR | 12 | 1frame | g:2,6 |
| 692 | `swh_166` | FLOOR | 12 | 1frame | g:3,6 |
| 693 | `swh_167` | FLOOR | 12 | 1frame | g:4,6 |
| 694 | `swh_168` | FLOOR | 12 | 1frame | g:5,6; g:17,6 |
| 695 | `swh_169` | FLOOR | 12 | 1frame | g:6,6 |
| 696 | `swh_170` | FLOOR | 8 | 1frame | g:7,6 |
| 697 | `swh_171` | FLOOR | 0 | 1frame | g:8,6; g:26,6; g:8,16; g:14,16; g:20,16 |
| 698 | `swh_172` | FLOOR | 0 | 1frame | g:9,6; g:27,6; g:9,16; g:15,16; g:21,16 |
| 699 | `swh_173` | FLOOR | 0 | 1frame | g:10,6; g:10,16; g:16,16; g:22,16 |
| 700 | `swh_174` | FLOOR | 0 | 1frame | g:11,6; g:5,16; g:11,16; g:17,16; g:23,16 |
| 701 | `swh_175` | FLOOR | 12 | 1frame | g:12,6 |
| 702 | `swh_176` | FLOOR | 12 | 1frame | g:13,6 |
| 703 | `swh_177` | FLOOR | 12 | 1frame | g:14,6 |
| 704 | `swh_178` | FLOOR | 12 | 1frame | g:15,6 |
| 705 | `swh_179` | FLOOR | 12 | 1frame | g:16,6 |
| 706 | `swh_180` | FLOOR | 0 | 1frame | g:18,6; g:24,6; g:6,16; g:12,16; g:18,16; g:24,16 |
| 707 | `swh_181` | FLOOR | 0 | 1frame | g:19,6 |
| 708 | `swh_182` | FLOOR | 0 | 1frame | g:20,6 |
| 709 | `swh_183` | FLOOR | 0 | 1frame | g:21,6 |
| 710 | `swh_184` | FLOOR | 0 | 1frame | g:22,6 |
| 711 | `swh_185` | FLOOR | 0 | 1frame | g:23,6 |
| 712 | `swh_186` | FLOOR | 0 | 1frame | g:25,6; g:7,16; g:13,16; g:19,16; g:25,16 |
| 713 | `swh_187` | FLOOR | 0 | 1frame | g:28,6 |
| 714 | `swh_188` | FRONT | 0 | 1frame | g:1,7 |
| 715 | `swh_189` | FRONT | 0 | 1frame | g:2,7 |
| 716 | `swh_190` | FRONT | 0 | 1frame | g:3,7 |
| 717 | `swh_191` | FRONT | 0 | 1frame | g:4,7 |
| 718 | `swh_192` | FRONT | 0 | 1frame | g:5,7 |
| 719 | `swh_193` | FRONT | 0 | 1frame | g:6,7 |
| 720 | `swh_194` | FRONT | 0 | 1frame | g:7,7 |
| 721 | `swh_195` | FLOOR | 0 | 1frame | g:8,7; g:14,7; g:26,7 |
| 722 | `swh_196` | FLOOR | 0 | 1frame | g:9,7; g:15,7; g:27,7 |
| 723 | `swh_197` | FLOOR | 0 | 1frame | g:10,7; g:16,7 |
| 724 | `swh_198` | FLOOR | 0 | 1frame | g:11,7; g:17,7 |
| 725 | `swh_199` | FLOOR | 0 | 1frame | g:12,7; g:18,7 |
| 726 | `swh_200` | FLOOR | 0 | 1frame | g:13,7 |
| 727 | `swh_201` | FLOOR | 0 | 1frame | g:19,7 |
| 728 | `swh_202` | FLOOR | 0 | 1frame | g:20,7 |
| 729 | `swh_203` | FLOOR | 0 | 1frame | g:21,7 |
| 730 | `swh_204` | FLOOR | 0 | 1frame | g:22,7 |
| 731 | `swh_205` | FLOOR | 0 | 1frame | g:23,7 |
| 732 | `swh_206` | FLOOR | 0 | 1frame | g:24,7 |
| 733 | `swh_207` | FLOOR | 0 | 1frame | g:25,7 |
| 734 | `swh_208` | FLOOR | 0 | 1frame | g:28,7 |
| 735 | `swh_209` | FLOOR | 0 | 1frame | g:1,8; g:1,13 |
| 736 | `swh_210` | FLOOR | 0 | 1frame | g:2,8; g:8,8; g:14,8; g:20,8; g:26,8; g:2,13; g:8,13; g:20,13; g:26,13 |
| 737 | `swh_211` | FLOOR | 0 | 1frame | g:3,8; g:9,8; g:15,8; g:21,8; g:27,8; g:3,13; g:9,13; g:21,13; g:27,13 |
| 738 | `swh_212` | FLOOR | 0 | 1frame | g:4,8; g:10,8; g:16,8; g:22,8; g:4,13; g:10,13; g:22,13 |
| 739 | `swh_213` | FLOOR | 0 | 1frame | g:5,8; g:11,8; g:17,8; g:5,13; g:11,13; g:17,13; g:23,13 |
| 740 | `swh_214` | FLOOR | 0 | 1frame | g:6,8; g:12,8; g:18,8; g:24,8; g:6,13; g:12,13; g:18,13; g:24,13 |
| 741 | `swh_215` | FLOOR | 0 | 1frame | g:7,8; g:13,8; g:19,8; g:25,8; g:7,13; g:19,13; g:25,13 |
| 742 | `swh_216` | FLOOR | 0 | 1frame | g:23,8 |
| 743 | `swh_217` | FLOOR | 0 | 1frame | g:28,8; g:28,13 |
| 744 | `swh_218` | SOLID | 15 | 1frame | g:0,9 |
| 745 | `swh_219` | SOLID | 15 | 1frame | g:1,9 |
| 746 | `swh_220` | SOLID | 15 | 1frame | g:2,9; g:8,9; g:20,9; g:26,9 |
| 747 | `swh_221` | SOLID | 15 | 1frame | g:3,9; g:9,9; g:21,9 |
| 748 | `swh_222` | SOLID | 15 | 1frame | g:4,9; g:10,9; g:22,9 |
| 749 | `swh_223` | SOLID | 15 | 1frame | g:5,9; g:11,9; g:17,9; g:23,9 |
| 750 | `swh_224` | SOLID | 15 | 1frame | g:6,9; g:12,9; g:18,9; g:24,9 |
| 751 | `swh_225` | SOLID | 15 | 1frame | g:7,9; g:19,9; g:25,9 |
| 752 | `swh_226` | SOLID | 15 | 1frame | g:13,9 |
| 753 | `swh_227` | FLOOR | 0 | 1frame | g:14,9 |
| 754 | `swh_228` | FLOOR | 0 | 1frame | g:15,9 |
| 755 | `swh_229` | SOLID | 15 | 1frame | g:16,9 |
| 756 | `swh_230` | SOLID | 15 | 1frame | g:27,9 |
| 757 | `swh_231` | SOLID | 15 | 1frame | g:28,9 |
| 758 | `swh_232` | SOLID | 15 | 1frame | g:29,9 |
| 759 | `swh_233` | SOLID | 15 | 1frame | g:0,10 |
| 760 | `swh_234` | SOLID | 15 | 8frames / 12updates each | g:1,10 |
| 761 | `swh_235` | SOLID | 15 | 8frames / 12updates each | g:2,10; g:4,10; g:6,10; g:8,10; g:12,10; g:16,10; g:18,10; g:20,10; g:22,10; g:24,10; g:26,10 |
| 762 | `swh_236` | SOLID | 15 | 8frames / 12updates each | g:3,10; g:5,10; g:7,10; g:9,10; g:13,10; g:17,10; g:19,10; g:21,10; g:23,10; g:25,10; g:27,10 |
| 763 | `swh_237` | SOLID | 15 | 8frames / 12updates each | g:10,10 |
| 764 | `swh_238` | SOLID | 15 | 8frames / 12updates each | g:11,10 |
| 765 | `swh_239` | FLOOR | 0 | 1frame | g:14,10; g:14,11 |
| 766 | `swh_240` | FLOOR | 0 | 1frame | g:15,10; g:15,11 |
| 767 | `swh_241` | SOLID | 15 | 8frames / 12updates each | g:28,10 |
| 768 | `swh_242` | SOLID | 15 | 1frame | g:29,10 |
| 769 | `swh_243` | SOLID | 15 | 1frame | g:0,11 |
| 770 | `swh_244` | SOLID | 15 | 8frames / 12updates each | g:1,11 |
| 771 | `swh_245` | SOLID | 15 | 8frames / 12updates each | g:2,11; g:4,11; g:6,11; g:8,11; g:10,11; g:12,11; g:18,11; g:20,11; g:22,11; g:24,11; g:26,11 |
| 772 | `swh_246` | SOLID | 15 | 8frames / 12updates each | g:3,11; g:5,11; g:7,11; g:9,11; g:11,11; g:17,11; g:19,11; g:21,11; g:23,11; g:25,11 |
| 773 | `swh_247` | SOLID | 15 | 8frames / 12updates each | g:13,11; g:27,11 |
| 774 | `swh_248` | SOLID | 15 | 8frames / 12updates each | g:16,11 |
| 775 | `swh_249` | SOLID | 15 | 8frames / 12updates each | g:28,11 |
| 776 | `swh_250` | SOLID | 15 | 1frame | g:29,11 |
| 777 | `swh_251` | SOLID | 15 | 1frame | g:0,12 |
| 778 | `swh_252` | SOLID | 15 | 1frame | g:1,12 |
| 779 | `swh_253` | SOLID | 15 | 1frame | g:2,12; g:8,12; g:20,12; g:26,12 |
| 780 | `swh_254` | SOLID | 15 | 1frame | g:3,12; g:9,12; g:21,12; g:27,12 |
| 781 | `swh_255` | SOLID | 15 | 1frame | g:4,12; g:10,12; g:22,12 |
| 782 | `swh_256` | SOLID | 15 | 1frame | g:5,12; g:11,12; g:17,12; g:23,12 |
| 783 | `swh_257` | SOLID | 15 | 1frame | g:6,12; g:12,12; g:18,12; g:24,12 |
| 784 | `swh_258` | SOLID | 15 | 1frame | g:7,12; g:13,12; g:19,12; g:25,12 |
| 785 | `swh_259` | FLOOR | 0 | 1frame | g:14,12 |
| 786 | `swh_260` | FLOOR | 0 | 1frame | g:15,12 |
| 787 | `swh_261` | SOLID | 15 | 1frame | g:16,12 |
| 788 | `swh_262` | SOLID | 15 | 1frame | g:28,12 |
| 789 | `swh_263` | SOLID | 15 | 1frame | g:29,12 |
| 790 | `swh_264` | SOLID | 15 | 1frame | g:0,13 |
| 791 | `swh_265` | FLOOR | 0 | 1frame | g:13,13 |
| 792 | `swh_266` | FLOOR | 0 | 1frame | g:14,13 |
| 793 | `swh_267` | FLOOR | 0 | 1frame | g:15,13 |
| 794 | `swh_268` | FLOOR | 0 | 1frame | g:16,13 |
| 795 | `swh_269` | SOLID | 15 | 1frame | g:29,13 |
| 796 | `swh_270` | SOLID | 15 | 1frame | g:0,14 |
| 797 | `swh_271` | SOLID | 15 | 1frame | g:1,14 |
| 798 | `swh_272` | SOLID | 15 | 1frame | g:2,14 |
| 799 | `swh_273` | FLOOR | 10 | 1frame | g:3,14 |
| 800 | `swh_274` | FLOOR | 0 | 1frame | g:4,14; g:10,14 |
| 801 | `swh_275` | FLOOR | 0 | 1frame | g:5,14 |
| 802 | `swh_276` | FLOOR | 0 | 1frame | g:6,14 |
| 803 | `swh_277` | FLOOR | 0 | 1frame | g:7,14 |
| 804 | `swh_278` | FLOOR | 0 | 1frame | g:8,14 |
| 805 | `swh_279` | FLOOR | 0 | 1frame | g:9,14 |
| 806 | `swh_280` | FLOOR | 0 | 1frame | g:11,14; g:17,14; g:23,14 |
| 807 | `swh_281` | FLOOR | 0 | 1frame | g:12,14; g:18,14; g:24,14 |
| 808 | `swh_282` | FLOOR | 0 | 1frame | g:13,14 |
| 809 | `swh_283` | FLOOR | 0 | 1frame | g:14,14 |
| 810 | `swh_284` | FLOOR | 0 | 1frame | g:15,14 |
| 811 | `swh_285` | FLOOR | 0 | 1frame | g:16,14 |
| 812 | `swh_286` | FLOOR | 0 | 1frame | g:19,14; g:25,14 |
| 813 | `swh_287` | FLOOR | 0 | 1frame | g:20,14 |
| 814 | `swh_288` | FLOOR | 0 | 1frame | g:21,14 |
| 815 | `swh_289` | FLOOR | 0 | 1frame | g:22,14 |
| 816 | `swh_290` | FLOOR | 5 | 1frame | g:26,14 |
| 817 | `swh_291` | SOLID | 15 | 1frame | g:27,14 |
| 818 | `swh_292` | SOLID | 15 | 1frame | g:28,14 |
| 819 | `swh_293` | SOLID | 15 | 1frame | g:29,14 |
| 820 | `swh_294` | SOLID | 15 | 1frame | g:0,15 |
| 821 | `swh_295` | SOLID | 15 | 1frame | g:1,15 |
| 822 | `swh_296` | SOLID | 15 | 1frame | g:2,15 |
| 823 | `swh_297` | FLOOR | 10 | 1frame | g:3,15 |
| 824 | `swh_298` | FLOOR | 0 | 1frame | g:5,15 |
| 825 | `swh_299` | FLOOR | 0 | 1frame | g:6,15 |
| 826 | `swh_300` | FLOOR | 0 | 1frame | g:7,15; g:25,15 |
| 827 | `swh_301` | FLOOR | 0 | 1frame | g:13,15 |
| 828 | `swh_302` | FLOOR | 0 | 1frame | g:14,15 |
| 829 | `swh_303` | FLOOR | 0 | 1frame | g:15,15 |
| 830 | `swh_304` | FLOOR | 0 | 1frame | g:16,15 |
| 831 | `swh_305` | FLOOR | 0 | 1frame | g:18,15 |
| 832 | `swh_306` | FLOOR | 0 | 1frame | g:19,15 |
| 833 | `swh_307` | FLOOR | 5 | 1frame | g:26,15 |
| 834 | `swh_308` | SOLID | 15 | 1frame | g:27,15 |
| 835 | `swh_309` | SOLID | 15 | 1frame | g:28,15 |
| 836 | `swh_310` | SOLID | 15 | 1frame | g:29,15 |
| 837 | `swh_311` | SOLID | 15 | 1frame | g:0,16 |
| 838 | `swh_312` | SOLID | 15 | 1frame | g:1,16 |
| 839 | `swh_313` | SOLID | 15 | 1frame | g:2,16 |
| 840 | `swh_314` | FLOOR | 10 | 1frame | g:3,16 |
| 841 | `swh_315` | FLOOR | 0 | 1frame | g:4,16 |
| 842 | `swh_316` | FLOOR | 5 | 1frame | g:26,16 |
| 843 | `swh_317` | SOLID | 15 | 1frame | g:27,16 |
| 844 | `swh_318` | SOLID | 15 | 1frame | g:28,16 |
| 845 | `swh_319` | SOLID | 15 | 1frame | g:29,16 |
| 846 | `swh_320` | SOLID | 15 | 1frame | g:0,17 |
| 847 | `swh_321` | SOLID | 15 | 1frame | g:1,17 |
| 848 | `swh_322` | SOLID | 15 | 1frame | g:2,17; g:8,17; g:14,17; g:20,17; g:26,17 |
| 849 | `swh_323` | SOLID | 15 | 1frame | g:3,17; g:9,17; g:15,17; g:21,17; g:27,17 |
| 850 | `swh_324` | SOLID | 15 | 1frame | g:4,17 |
| 851 | `swh_325` | SOLID | 15 | 1frame | g:5,17; g:11,17; g:17,17; g:23,17 |
| 852 | `swh_326` | SOLID | 15 | 1frame | g:6,17; g:12,17; g:18,17; g:24,17 |
| 853 | `swh_327` | SOLID | 15 | 2frames / 4updates each | g:7,17 |
| 854 | `swh_328` | SOLID | 15 | 1frame | g:10,17; g:16,17 |
| 855 | `swh_329` | SOLID | 15 | 1frame | g:13,17; g:19,17; g:25,17 |
| 856 | `swh_330` | SOLID | 15 | 2frames / 4updates each | g:22,17 |
| 857 | `swh_331` | SOLID | 15 | 1frame | g:28,17 |
| 858 | `swh_332` | SOLID | 15 | 1frame | g:29,17 |
| 859 | `swh_333` | SOLID | 15 | 1frame | g:0,18 |
| 860 | `swh_334` | SOLID | 15 | 8frames / 12updates each | g:1,18; g:3,18; g:5,18; g:9,18; g:11,18; g:13,18; g:15,18; g:17,18; g:19,18; g:23,18; g:25,18; g:27,18 |
| 861 | `swh_335` | SOLID | 15 | 8frames / 12updates each | g:2,18; g:6,18; g:8,18; g:10,18; g:14,18; g:16,18; g:18,18; g:24,18; g:26,18; g:28,18 |
| 862 | `swh_336` | SOLID | 15 | 8frames / 12updates each | g:4,18 |
| 863 | `swh_337` | SOLID | 15 | 24frames / 4updates each | g:7,18 |
| 864 | `swh_338` | SOLID | 15 | 8frames / 12updates each | g:12,18 |
| 865 | `swh_339` | SOLID | 15 | 8frames / 12updates each | g:20,18 |
| 866 | `swh_340` | SOLID | 15 | 8frames / 12updates each | g:21,18 |
| 867 | `swh_341` | SOLID | 15 | 24frames / 4updates each | g:22,18 |
| 868 | `swh_342` | SOLID | 15 | 1frame | g:29,18 |
| 869 | `swh_343` | SOLID | 15 | 1frame | g:0,19 |
| 870 | `swh_344` | SOLID | 15 | 8frames / 12updates each | g:1,19; g:3,19; g:5,19; g:7,19; g:9,19; g:13,19; g:15,19; g:17,19; g:19,19; g:21,19; g:23,19; g:25,19; g:27,19 |
| 871 | `swh_345` | SOLID | 15 | 8frames / 12updates each | g:2,19; g:4,19; g:6,19; g:8,19; g:10,19; g:14,19; g:16,19; g:18,19; g:22,19; g:24,19; g:26,19; g:28,19 |
| 872 | `swh_346` | SOLID | 15 | 8frames / 12updates each | g:11,19 |
| 873 | `swh_347` | SOLID | 15 | 8frames / 12updates each | g:12,19 |
| 874 | `swh_348` | SOLID | 15 | 8frames / 12updates each | g:20,19 |
| 875 | `swh_349` | SOLID | 15 | 1frame | g:29,19 |
| 876 | `swh_350` | FLOOR | 0 | 1frame | o:8,1 |
| 877 | `swh_351` | FLOOR | 0 | 1frame | o:9,1 |
| 878 | `swh_352` | FLOOR | 0 | 1frame | o:10,1 |
| 879 | `swh_353` | FLOOR | 0 | 1frame | o:8,2 |
| 880 | `swh_354` | FLOOR | 0 | 1frame | o:9,2 |
| 881 | `swh_355` | FLOOR | 0 | 1frame | o:10,2 |
| 882 | `swh_356` | FLOOR | 0 | 1frame | o:2,5 |
| 883 | `swh_357` | FLOOR | 0 | 1frame | o:3,5; o:5,5 |
| 884 | `swh_358` | FLOOR | 0 | 1frame | o:4,5 |
| 885 | `swh_359` | FLOOR | 0 | 1frame | o:6,5 |
| 886 | `swh_360` | FLOOR | 0 | 1frame | o:2,6 |
| 887 | `swh_361` | FLOOR | 0 | 1frame | o:3,6; o:5,6 |
| 888 | `swh_362` | FLOOR | 0 | 1frame | o:4,6 |
| 889 | `swh_363` | FLOOR | 0 | 1frame | o:6,6 |
| 890 | `swh_364` | FLOOR | 0 | 1frame | o:1,8; o:3,8; o:5,8; o:7,8; o:9,8; o:11,8; o:13,8; o:17,8; o:19,8; o:21,8; o:23,8; o:25,8; o:27,8 |
| 891 | `swh_365` | FLOOR | 0 | 1frame | o:16,8 |
| 892 | `swh_366` | FLOOR | 0 | 1frame | o:1,16 |
| 893 | `swh_367` | FLOOR | 0 | 1frame | o:2,16; o:4,16; o:6,16; o:8,16; o:10,16; o:12,16; o:14,16; o:16,16; o:18,16; o:20,16; o:22,16; o:24,16; o:26,16 |
| 894 | `swh_368` | FLOOR | 0 | 1frame | o:3,16; o:5,16; o:7,16; o:9,16; o:11,16; o:13,16; o:15,16; o:17,16; o:19,16; o:21,16; o:23,16; o:25,16 |
| 895 | `swh_369` | FLOOR | 0 | 1frame | o:27,16 |

## Retained named sewer catalog, not used by this room

The 80 `sw_` IDs below still have painter definitions (113 frame drawings) but are not placed by `sewer_main` and are not held by its active tileset. Their existence does not mean the corresponding fixture is absent: most visible fixtures are painted into the active `swh_` IDs. List them separately to avoid claiming they are all active sewer sprites.

| ID | Catalog tile | Type | Frames |
| --- | --- | --- | --- |
| 281 | `sw_floor0` | FLOOR | 1 |
| 282 | `sw_floor1` | FLOOR | 1 |
| 283 | `sw_floor2` | FLOOR | 1 |
| 284 | `sw_floor_slime` | SLOW | 1 |
| 285 | `sw_wall` | SOLID | 1 |
| 286 | `sw_wall_top` | SOLID | 1 |
| 287 | `sw_wall_slime` | SOLID | 1 |
| 288 | `sw_water` | WATER | 2 |
| 289 | `sw_lilypad` | WATER | 2 |
| 290 | `sw_waterfall` | SOLID | 2 |
| 291 | `sw_water_edge_n` | FLOOR | 1 |
| 292 | `sw_water_edge_s` | FLOOR | 1 |
| 293 | `sw_grate` | FLOOR | 1 |
| 294 | `sw_drain_nw` | FLOOR | 1 |
| 295 | `sw_drain_ne` | FLOOR | 1 |
| 296 | `sw_drain_sw` | FLOOR | 1 |
| 297 | `sw_drain_se` | FLOOR | 1 |
| 298 | `sw_pipe` | SOLID | 1 |
| 299 | `sw_pipe_h` | SOLID | 1 |
| 300 | `sw_ladder` | EXIT | 1 |
| 301 | `sw_ladder_down` | FLOOR | 1 |
| 302 | `sw_hole` | EXIT | 1 |
| 303 | `sw_torch_lit` | TORCH_LIT | 2 |
| 304 | `sw_candles` | SOLID | 2 |
| 305 | `sw_lantern` | SOLID | 2 |
| 306 | `sw_banner_teal` | SOLID | 1 |
| 307 | `sw_banner_red` | SOLID | 1 |
| 308 | `sw_arch` | SOLID | 1 |
| 309 | `sw_rubble` | SOLID | 1 |
| 310 | `sw_counter` | SOLID | 1 |
| 311 | `sw_awning_l` | SOLID | 1 |
| 312 | `sw_awning_r` | SOLID | 1 |
| 313 | `sw_rug_nw` | FLOOR | 1 |
| 314 | `sw_rug_ne` | FLOOR | 1 |
| 315 | `sw_rug_sw` | FLOOR | 1 |
| 316 | `sw_rug_se` | FLOOR | 1 |
| 317 | `sw_barrel` | SOLID | 1 |
| 318 | `sw_crate` | SOLID | 1 |
| 319 | `sw_skull` | FLOOR | 1 |
| 320 | `sw_pot` | LIFT1 | 1 |
| 321 | `sw_gold` | FLOOR | 1 |
| 322 | `sw_floor_grime` | FLOOR | 1 |
| 323 | `sw_floor_grime2` | FLOOR | 1 |
| 324 | `sw_floor_crack` | FLOOR | 1 |
| 325 | `sw_floor_crack2` | FLOOR | 1 |
| 326 | `sw_floor_moss` | FLOOR | 1 |
| 327 | `sw_floor_moss2` | FLOOR | 1 |
| 328 | `sw_floor_puddle` | FLOOR | 2 |
| 329 | `sw_floor_bones` | FLOOR | 1 |
| 330 | `sw_floor_shroom` | FLOOR | 2 |
| 331 | `sw_floor_drip` | FLOOR | 4 |
| 332 | `sw_wall_crack` | SOLID | 1 |
| 333 | `sw_wall_moss` | SOLID | 1 |
| 334 | `sw_wall_chain` | SOLID | 1 |
| 335 | `sw_wall_drip` | SOLID | 4 |
| 336 | `sw_wall_web` | SOLID | 1 |
| 337 | `sw_wall_web_r` | SOLID | 1 |
| 338 | `sw_wall_fungus` | SOLID | 2 |
| 339 | `sw_wall_tally` | SOLID | 1 |
| 340 | `sw_wall_window` | SOLID | 2 |
| 341 | `sw_wall_skull` | SOLID | 1 |
| 342 | `sw_wall_rust` | SOLID | 1 |
| 343 | `sw_wall_top_moss` | SOLID | 1 |
| 344 | `sw_water_scum` | WATER | 2 |
| 345 | `sw_water_bubble` | WATER | 4 |
| 346 | `sw_water_glint` | WATER | 2 |
| 347 | `sw_water_edge_n_moss` | FLOOR | 1 |
| 348 | `sw_water_edge_s_moss` | FLOOR | 1 |
| 349 | `sw_glint` | FLOOR | 3 |
| 350 | `sw_glint2` | FLOOR | 3 |
| 351 | `sw_glint3` | FLOOR | 3 |
| 352 | `sw_arch_r` | SOLID | 1 |
| 353 | `sw_grate_r` | FLOOR | 1 |
| 354 | `sw_counter_r` | SOLID | 1 |
| 355 | `sw_fall_0` | SOLID | 2 |
| 356 | `sw_fall_1` | SOLID | 2 |
| 357 | `sw_fall_2` | SOLID | 2 |
| 358 | `sw_fall_3` | SOLID | 2 |
| 359 | `sw_fall_4` | SOLID | 2 |
| 360 | `sw_fall_5` | SOLID | 2 |

## Build and review rules

- Each swh_000..swh_369 is an exact native16x16 metatile ID, not an independent semantic object. Large fixtures consist of several IDs.
- Five full concepts must replace every active ID/frame while keeping type/coll/prop metadata, layout and object anchors stable.
- Reuse repeated ground IDs only for reusable material panels. Their original occurrence positions can span unrelated visual regions.
- Keep overlay transparency and existing occlusion. North rail posts and counter face foreground must not become opaque floor squares.
- Only 38 active IDs animate; whole-room source-phase changes are invisible when a cropped ID has one declared frame. Author flowing water into the actual declared animated IDs, or explicitly review an animation-contract extension.
- The existing keeper palette pulses only indices 13/14. New wizard cloth must not use those indices if the pulse is preserved; reserve them for flame.
- Keep wisp body-relative position aligned to actual staff tip, or change WISP_AT consistently in all render paths.
- No enemy/chest/switch/locked-door static actors are authored in the Drain room. Its four object descriptors are spawn, forest exit, wizard and merchant.
- Native hardware may load source sheets for shared gameplay tools even when they are not visible. Loaded is different from spawned/visible.
