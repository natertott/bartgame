#!/usr/bin/env python3
"""Capture one full first pass plus loop review for every soundtrack entry."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from validate import analyze


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True, type=Path)
    ap.add_argument('--rom', required=True, type=Path)
    ap.add_argument('--elf', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--loop-seconds', type=float, default=0)
    ap.add_argument('--stereo-through', type=int, default=0,
                    help='Require meaningful L/R differences for IDs up to this value (0 disables)')
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    started = time.monotonic()
    script = Path(__file__).with_name('capture.py')
    for song in manifest['songs']:
        path = args.output / f"{song['id']:02d}_{song['slug']}.wav"
        seconds = song['seconds'] + args.loop_seconds
        command = [sys.executable, str(script), '--rom', str(args.rom), '--elf', str(args.elf),
                   '--song', str(song['id']), '--seconds', str(seconds), '--output', str(path)]
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            raise RuntimeError(f"Capture failed for song {song['id']}")
        capture = json.loads(path.with_suffix('.capture.json').read_text())
        validation = analyze(path)
        row = {'id': song['id'], 'title': song['title'], 'file': path.name,
               'capture': capture, 'validation': validation}
        rows.append(row)
        if args.loop_seconds > 0:
            assert capture['observed_loop_count'] >= 1, f"No loop observed for song {song['id']}"
        assert validation['passed_integrity'], f"Audio integrity failed for song {song['id']}"
        if song['id'] <= args.stereo_through:
            assert validation['stereo_difference_rms_dbfs'] > -60, f"No stereo difference for song {song['id']}"
            assert all(ch['rms_dbfs'] > -60 for ch in validation['channel_statistics']), f"Silent side for song {song['id']}"
        print(f"{song['id']:02d} {song['title']}: {capture['duration_seconds']:.2f}s, "
              f"{capture['observed_loop_count']} loop, peak {validation['peak_dbfs']:.1f}dBFS, "
              f"L/R diff {validation['stereo_difference_rms_dbfs']:.1f}dBFS, "
              f"driver {capture.get('driver_cpu_profile', {}).get('mean_percent_of_frame', '?')}% frame",
              flush=True)
    report = {'capture_source': 'actual mGBA output of compiled standalone GBA ROM',
              'physical_hardware_recording': False,
              'count': len(rows), 'passed': sum(row['validation']['passed_integrity'] for row in rows),
              'loop_review_seconds_requested': args.loop_seconds,
              'elapsed_wall_seconds': round(time.monotonic() - started, 3),
              'songs': rows}
    report_path = args.output / 'capture_validation.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(f"Captured and validated {len(rows)} tracks -> {report_path}", flush=True)


if __name__ == '__main__':
    main()
