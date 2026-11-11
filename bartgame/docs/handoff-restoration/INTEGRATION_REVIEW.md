# Integration boundary review

This review checks the interactions between the restored systems, rather
than treating a catalogue entry or an isolated host test as runtime proof.
It reads the game/area loaders, player and weapon pipeline, collision,
encounter lifetime, annex contracts, independent persistence and menu
ownership. The source was changing concurrently; native counterexamples below
refer specifically to the frozen `integration3` development bundle.

## Native counterexamples

`tools/integration_guard_review.py` runs private mGBA cores and records the
ROM and tool hashes, unchanged native PNGs, declared fixtures and assertions.
The development run passed its four positive controls and reproduced four
bugs below. These are diagnostic results, not final acceptance evidence.

| Boundary | Counterexample | Required correction |
| --- | --- | --- |
| Fairy and damage reduction | A real4HP bomb at playerHP4 consumed a Fairy even with Nayru, which should reduce damage to1. | Apply global mitigation before testing whether a Fairy rescue is needed. Keep zero-damage attacks from producing knockback. |
| Bomb charge and dialogue | Hold a B-assigned bomb, press A to speak to the Sage, release B during dialogue, then close it. The charge survived and consumed ammunition in an unintended throw. | Cancel charge when a text, cabinet or service modal takes input ownership. |
| Health beyond ten hearts | With restored maximum health160, the native heart display remained identical at health160 and120. | Show the additional health, while preserving the existing single row at ordinary maximum health. |
| Existing health beyond twenty hearts | Piece conversion can exceed160HP. The exact health panel must visibly distinguish168HP from164HP while retaining the existing health growth. | Show current/maximum numerically above the twenty-heart display capacity, within the existing HUD height. |

The fixtures supply player health, ownership, bottle contents, equipment,
Nayru ownership and navigation/facing only. Bomb damage and Sage dialogue
come from real input. No enemy state/HP, completion, geometry, VRAM or
framebuffer is edited. Rerun the tool on the final frozen bundle; a source
correction alone does not establish that the counterexample is closed.

## Source findings handed to owners

- Cream originally tracked only its initial encounter actors. Slime splits
  and other descendants could remain alive after the component was marked
  cleared. Parent/child encounter tracking is now connected at spawn.
- The new draft can grant the Forest's traversal tools before its required
  trials. Mandatory Forest cuts therefore need both the tool and the
  corresponding claimed-trial facts. Optional tool pockets remain governed
  by their original item rules.
- A contract's item was stored in a byte although golden halves use IDs
  `0x100..0x103`. It now needs a16-bit field and a high-ID positive/negative
  test. The unpublished extension format must reflect the final layout.
- Fixed contract targets may already be cleared and their prizes consumed.
  A new contract must choose, instantiate or explicitly rearm a usable
  objective rather than entering a completed room that never notifies it.
- Cart/parachute movement needs scoped ownership of tool input. A cart that
  returns Bloom to NORMAL each tick can otherwise overwrite a Drain Cap
  swallow or let Boots/Spin take movement ownership mid-ride.
- A live rank must follow score changes. Explicit meta preference changes
  must persist consistently with their run checkpoint; publishing a profile
  with new score but old completed-quest flags permits replay farming.
- Shallow/deep water needs distinct movement feedback, and submerged attack
  immunity must be checked before capture/contact as well as before damage.

The runtime owners are applying these corrections. Final status belongs in
the main feature ledger and frozen native reports. This note does not claim
that every historical TMC object, all source binary layouts, or every edge
across every generated seed has been independently observed in an emulator.
