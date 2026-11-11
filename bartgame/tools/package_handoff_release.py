#!/usr/bin/env python3
"""Package one immutable original-game release and its qualified evidence.

This copies existing emulator captures; it does not draw or alter screenshots.
The workspace proof paths are explicit so a later release cannot silently reuse
another ROM's native reports. SRAM, save states and duplicate private ROMs are
excluded. Host reports remain separately labelled as host execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', required=True, type=Path)
    ap.add_argument('--evidence', required=True, type=Path,
                    help='JSON manifest of named native directories and host files')
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    bundle, out = args.bundle.resolve(), args.out.resolve()
    config = json.loads(args.evidence.read_text())
    rom_hash = sha(bundle / 'bartgame.gba')
    source = (bundle / 'source-commit.txt').read_text().strip()
    out.mkdir(parents=True, exist_ok=True)
    stem = 'bartgame-' + source[:8]
    rom = out / (stem + '.gba')
    shutil.copy2(bundle / 'bartgame.gba', rom)
    inventory = []

    def record(path, archive_name, kind):
        inventory.append(dict(path=archive_name, sha256=sha(path),
                              bytes=path.stat().st_size, kind=kind))

    def native_hashes(value):
        if not isinstance(value, dict):
            return set()
        return {value[k] for k in ('rom_sha256', 'sha256')
                if k in value and isinstance(value[k], str)}

    # Every suite's top-level native report must pin this exact ROM.
    for name, directory in config['native'].items():
        report = Path(directory) / 'report.json'
        data = json.loads(report.read_text())
        assert rom_hash in native_hashes(data), (name, 'wrong ROM', native_hashes(data))
        assert not data.get('errors'), (name, data['errors'])
        assert data.get('complete') is not False, (name, 'incomplete')
        assert data.get('scope_complete') is not False, (name, 'scope incomplete')
        for check in data.get('checks', []):
            if isinstance(check, dict):
                for key in ('passed', 'pass', 'ok'):
                    if key in check:
                        assert check[key], (name, check)
        if isinstance(data.get('passed'), bool):
            assert data['passed'], (name, 'failed')
        if 'total' in data and isinstance(data.get('passed'), int):
            assert data['passed'] == data['total'], (name, 'failed total')

    archive = out / 'native-evidence.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in ('bartgame.gba', 'bartgame.elf', 'bartgame.map', 'assets.h', 'source-commit.txt'):
            path = bundle / name
            rel = 'frozen/' + name
            z.write(path, rel)
            record(path, rel, 'frozen build')
        for name, directory in config['native'].items():
            directory = Path(directory)
            for path in sorted(directory.rglob('*')):
                if not path.is_file() or path.suffix.lower() not in ('.json', '.png', '.gif', '.wav', '.txt'):
                    continue
                relative = path.relative_to(directory)
                if any(p in ('private', 'bundle') for p in relative.parts):
                    continue
                rel = 'native/' + name + '/' + relative.as_posix()
                z.write(path, rel)
                record(path, rel, 'actual mGBA output/report')
        for name, filename in config['host'].items():
            path = Path(filename)
            rel = 'host/' + name + '.json'
            z.write(path, rel)
            record(path, rel, 'actual C host proof, not emulator output')
        for name, filename in config.get('other', {}).items():
            path = Path(filename)
            rel = 'qualification/' + name
            z.write(path, rel)
            record(path, rel, 'qualification/build metadata')
        manifest = dict(source_commit=source, rom_sha256=rom_hash,
                        emulator='mGBA0.10.5', files=inventory)
        z.writestr('manifest.json', json.dumps(manifest, indent=2) + '\n')
    (out / 'evidence-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(out / (stem + '.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(rom, rom.name)
        z.writestr('README.txt', 'BARTGAME original standalone GBA game.\n'
                   'Source: ' + source + '\nROM SHA256: ' + rom_hash + '\n'
                   'See the adjacent README.md and curdled-cream-review/README.md '
                   'for controls, the feature audit and actual mGBA captures.\n')
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
    (out / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + p.name + '\n' for p in files))
    print(json.dumps(dict(source_commit=source, rom_sha256=rom_hash,
                          files=len(inventory), evidence_bytes=archive.stat().st_size)))


if __name__ == '__main__':
    main()
