# Complete performance measurements

[Summary JSON](summary.json) and [all paired case metrics CSV](cases.csv) expose every measured case. The following lossless gzip files retain the original complete pretty-printed JSON, every raw video/game-age sample, initial/periodic/final rosters, fixtures, transition records and integrity checks. Decompressed byte hashes are recorded in the [index](index.json).

- [before broad / complete raw JSON.gz](before-broad.json.gz) — original SHA256 `5a905d6e58aafd931ba48695943ec53ed7d38a522d22e7771d19ddec61d30867`.
- [before throughput / complete raw JSON.gz](before-throughput.json.gz) — original SHA256 `07e23ef9ccac84829e94788621e1ea953113e1c89942813ceba2663249793f80`.
- [before steady / complete raw JSON.gz](before-steady.json.gz) — original SHA256 `71886fd29c23b747e2c6f2fe98f759c826cea55fe7b863b54490ac0290c200fd`.
- [after broad / complete raw JSON.gz](after-broad.json.gz) — original SHA256 `d22b52af017eca177c93bbf22daddbf4a0690d8bc1c5f0fe70fe1782a3fb8032`.
- [after throughput / complete raw JSON.gz](after-throughput.json.gz) — original SHA256 `77f46490540eae198f68add97a8dfde9b29a77a43f5907b2458d4f0e5c099448`.
- [after steady / complete raw JSON.gz](after-steady.json.gz) — original SHA256 `73db47271d382318ad9aedfa800a6262f698ef17aa5dc157d578ae1164e32d04`.

## Observed menu input-to-state latency

| Target | Previous video frames | Optimized video frames |
| --- | ---: | ---: |
| items | 8 | 7 |
| keys | 4 | 3 |
| overview | 11 | 9 |
| zoom | 23 | 22 |
| overview-return | 3 | 3 |
| close | 3 | 3 |

These are observed video-frame counts under the fixed real-input script, including its minimum three-frame detection schedule. They are not idle gameplay FPS. Cold page drawing, room generation/fades and modal states remain separate records in the broad report.

Graphs are scientific measurement artifacts generated with Matplotlib. They are not screenshots or new game artwork. All rates derive from eligible logic updates divided by eligible video frames, multiplied by 262144/4389 Hz.
