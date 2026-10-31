#!/usr/bin/env python3
"""Measure capture integrity, levels, stereo differences and long silence."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import wave
import numpy as np


def db(value):
    return round(20 * math.log10(max(float(value), 1e-12)), 3)


def analyze(path, max_silence_seconds=None):
    with wave.open(str(path), 'rb') as source:
        rate, channels, width = source.getframerate(), source.getnchannels(), source.getsampwidth()
        assert width == 2, f'{path}: expected 16-bit PCM'
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype='<i2').reshape(-1, channels)
    x = pcm.astype(np.float64) / 32768
    block = max(1, rate // 10)
    length = len(x) // block
    energy = np.sqrt(np.mean(x[:length * block].reshape(length, block, channels) ** 2, axis=(1, 2)))
    quiet = energy < 10 ** (-65 / 20)
    longest = run = 0
    for item in quiet:
        run = run + 1 if item else 0
        longest = max(run, longest)
    per_channel = [{'peak_dbfs': db(np.max(np.abs(x[:, c]))),
                    'rms_dbfs': db(np.sqrt(np.mean(x[:, c] ** 2))),
                    'dc_offset': round(float(np.mean(x[:, c])), 7)} for c in range(channels)]
    clipping_samples = int(np.count_nonzero((pcm == 32767) | (pcm == -32768)))
    sections = []
    for start in range(0, len(x), 4 * rate):
        section = x[start:start + 4 * rate]
        sections.append({'start_seconds': round(start / rate, 3),
                         'rms_dbfs': db(np.sqrt(np.mean(section * section))),
                         'peak_dbfs': db(np.max(np.abs(section)))})
    row = {
        'file': path.name,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'sample_rate_hz': rate, 'channels': channels, 'sample_width_bytes': width,
        'duration_seconds': round(len(x) / rate, 6),
        'peak_dbfs': db(np.max(np.abs(x))), 'rms_dbfs': db(np.sqrt(np.mean(x * x))),
        'clipped_sample_count': clipping_samples,
        'longest_near_silence_seconds': round(longest * block / rate, 3),
        'silence_limit_seconds': max_silence_seconds,
        'silence_policy': 'Preserve expected source-file intros/tails; measure silence without rejecting it'
            if max_silence_seconds is None else 'Explicit maximum near-silence duration',
        'channel_statistics': per_channel,
        'four_second_level_history': sections,
        'stereo_difference_rms_dbfs': db(np.sqrt(np.mean((x[:, 0] - x[:, 1]) ** 2))) if channels == 2 else None,
        'stereo_correlation': round(float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]), 6)
            if channels == 2 and np.std(x[:, 0]) > 0 and np.std(x[:, 1]) > 0 else None,
        'side_to_mid_db': db(np.sqrt(np.mean((x[:, 0] - x[:, 1]) ** 2)) /
                             max(1e-12, np.sqrt(np.mean((x[:, 0] + x[:, 1]) ** 2))))
            if channels == 2 else None,
        'passed_integrity': bool(channels == 2 and width == 2 and len(x) > rate and
                                 clipping_samples == 0 and np.max(np.abs(x)) > .002 and
                                 (max_silence_seconds is None or longest * block / rate < max_silence_seconds)),
    }
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--max-silence', type=float, default=None,
                        help='Optional silence limit; default retains legitimate source-file silence')
    args = parser.parse_args()
    rows = [analyze(path, args.max_silence) for path in args.files]
    report = {'total_files': len(rows), 'passed': sum(row['passed_integrity'] for row in rows), 'files': rows}
    encoded = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(encoded)
    print(encoded)
    raise SystemExit(any(not row['passed_integrity'] for row in rows))


if __name__ == '__main__':
    main()
