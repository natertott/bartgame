# Performance regression and provenance

[Independent frozen-ROM regression](regression/report.json) includes authored/resolved-art scope, gameplay/UI/save suites and 24 matched native RGB views. Underlying suite reports/logs are preserved with their original counts; they are not additional disjoint tests to sum. [Native comparison manifest](regression/isolated-native.json) records all 48 before/after untouched 240×160 views and their hashes.

[Supplemental native and workload checks](SUPPLEMENTAL.md) retain all 45 exact menu RGB comparisons, 90 native menu PNGs, the extended Heart-pressure measurements and scenario-media validation.

- [actor](host/actor.json): its original schema, counts and source hashes.
- [effects](host/effects.json): its original schema, counts and source hashes.
- [visibility](host/visibility.json): its original schema, counts and source hashes.
- [objects](host/objects.json): its original schema, counts and source hashes.
- [system](host/system.json): its original schema, counts and source hashes.
- [torch](host/torch.json): its original schema, counts and source hashes.
- [menu](host/menu.json): its original schema, counts and source hashes.
- [visibility-ubsan](host/visibility-ubsan.json): its original schema, counts and source hashes.

Host differential checks establish equivalent routines under their disclosed fixtures. They do not measure GBA speed, exhaust every possible game state or replace production timing. [Frozen build records](frozen/) pin production source, inputs and linked symbols. [Publication QA](publication-qa.json) verifies lossless reports, exact native/GIF/crop pixels, release identity and local links.

[Artifact prose review](artifact-doc-review.json) verifies the final documentation links and unchanged non-Markdown payloads separately from the original publication QA.
