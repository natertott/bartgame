#!/usr/bin/env bash
set -euo pipefail
tool_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$tool_dir/banks/fluidr3"
curl --fail --location --output "$tool_dir/banks/fluid-soundfont-gm.deb" 'https://deb.debian.org/debian/pool/main/f/fluid-soundfont/fluid-soundfont-gm_3.1-5.3_all.deb'
dpkg-deb -x "$tool_dir/banks/fluid-soundfont-gm.deb" "$tool_dir/banks/fluidr3"
python3 - "$tool_dir/banks/fluidr3/usr/share/sounds/sf2/FluidR3_GM.sf2" <<'CHECK'
from pathlib import Path
import sys,hashlib
p=Path(sys.argv[1]);expected='74594e8f4250680adf590507a306655a299935343583256f3b722c48a1bc1cb0'
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,'SoundFont checksum mismatch'
print('Verified FluidR3_GM.sf2')
CHECK
