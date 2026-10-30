# Pixel-art reference register

Record what has actually been accessed. An article's URL or title is not
evidence that its text and illustrations were read. Keep source notes linked
to the [art bible](ART_BIBLE.md) and [decision log](ART_DIRECTION_LOG.md).

## Read article PDFs — 2026-10-30

All six user-supplied PDFs have now been received and read. Direct website
requests previously returned 403; that access failure is not used as evidence
of the contents. Page citations refer to the uploaded browser-print PDFs,
including navigation and footers. [Source records](references/sources.json)
contain their real filenames, page counts, URLs and SHA256 hashes.

| Source | Requested page | PDF filename / pages | Status |
| --- | --- | --- | --- |
| R1 — Richard Janes | [Introduction to pixel art](http://rjanes.com/tutorials/introduction_to_pixel_art.php) | 5 pages; [notes](references/JANES_GALVAN_PALEF.md) | Read |
| R2 — the-pixel.art | [Pixel-art character design](https://the-pixel.art/articles/pixel-art-character-design/) | 10 pages; [notes](references/CHARACTER_DESIGN_LIVRESQUARE.md) | Read |
| R3 — Alain Galvan | [Pixel-art design for game development](https://alain.xyz/blog/pixel-art-design-for-game-dev) | 6 pages; [notes](references/JANES_GALVAN_PALEF.md) | Read |
| R4 — John Park / Adafruit | [Pixel-art fundamentals](https://learn.adafruit.com/homebrew-game-boy-games/pixel-art-fundamentals) | 39 pages; [notes](references/ADAfruit_FUNDAMENTALS.md) | Read |
| R5 — Thomas Palef | [Tips to make pixel art for your games](https://medium.com/@thomaspalef/tips-to-make-pixel-art-for-your-games-7b770ffcfde3) | 9 pages; [notes](references/JANES_GALVAN_PALEF.md) | Read |
| R6 — Livresquare | [Creating pixel character art](https://tips.clip-studio.com/en-us/articles/11408) | 37 pages; [notes](references/CHARACTER_DESIGN_LIVRESQUARE.md) | Read |

All tutorial text and available relevant illustrations were reviewed. R2's
embedded figures needed direct extraction when page rendering hid them. R6
contains introductory examples and costume sketches, but its later main
tutorial illustration spaces lack images in the supplied PDF. Their explicit
text was read; missing figures are not falsely claimed as inspected. R4's
actual article occupies pp. 6–19; other pages are navigation and related content.

The [application matrix](REFERENCE_APPLICATION.md) connects the recommendations
to adopted shared rules, native-GBA adaptations and the second Drain pass.

## Source notes and future references

Record the real filename, page count and content hash, then read both text
and available example images. Create source notes with page references, paraphrased
recommendations, relevant example observations and the affected design rules.
Distinguish an author's explicit advice from our interpretation.

For each recommendation, record its application to this game, its scope and
any necessary GBA adaptation. Guidance aimed at another resolution, platform,
genre or animation scale needs an explicit translation rather than automatic
adoption. Resolve conflicting recommendations against the user's goals and
the native hardware constraints, and record the reason.

The redesign review should connect each adopted rule to visible examples in
the five Drain sets and state any advice intentionally deferred or inapplicable.
The earlier [research register](RESEARCH.md) remains separate evidence; it must
not be presented as a substitute for reading later references.

## Follow-up Drain application — third pass

The user’s review of the second-pass gallery is the direct evidence for this
iteration, followed by their request to keep varying both NPCs. The existing
six PDF notes remain the reference basis; this pass does not claim a new
article or missing illustration was accessed. Concrete applications and
tradeoffs are recorded in [third-pass characters](references/DRAIN_V3_CHARACTERS.md),
[fixtures](references/DRAIN_V3_FIXTURES.md), [terrain](references/DRAIN_V3_TERRAIN.md)
and the [direction log](ART_DIRECTION_LOG.md).
The preferred second-pass #1 frog and #5 wizard are comparison anchors, not
new sources or automatic adoption of a whole room.
