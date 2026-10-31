#!/usr/bin/env python3
"""Measure direct-source GBA capture alignment and fidelity without editing it.

Compare Rxx direct PCM versions only. Waveform correlation is not an appropriate
quality test for Ixx instrument reconstructions with intentionally new timbres.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import wave

import numpy as np


def source_audio(path, rate):
    process = subprocess.run([
        'ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ac', '2',
        '-ar', str(rate), '-f', 'f32le', 'pipe:1'
    ], capture_output=True, check=True)
    return np.frombuffer(process.stdout, dtype='<f4').reshape(-1, 2)


def capture_audio(path):
    with wave.open(str(path), 'rb') as recording:
        rate = recording.getframerate()
        if recording.getnchannels() != 2 or recording.getsampwidth() != 2:
            raise ValueError('Capture must be signed16-bit stereo WAV')
        pcm = np.frombuffer(recording.readframes(recording.getnframes()), dtype='<i2')
    return rate, pcm.reshape(-1, 2).astype(np.float32) / 32768


def log_db(value):
    return float(20 * np.log10(max(float(value), 1e-15)))


def compare(args):
    rate, recording = capture_audio(args.capture)
    source = source_audio(args.source, rate)
    count = min(len(source), len(recording))
    window = min(round(args.window_seconds * rate), count)
    if window < rate:
        raise ValueError('At least one second of source/capture is required')
    max_lag = round(args.max_latency_seconds * rate)
    rows = []
    for fraction in (.2, .5, .8):
        start = max(0, min(count - window, round(count * fraction - window / 2)))
        reference = source[start:start + window].astype(np.float64)
        observed = recording[start:start + window].astype(np.float64)
        if np.sqrt(np.mean(reference ** 2)) < 1e-5:
            rows.append({'start_seconds': start / rate, 'source_silence': True})
            continue
        # Use the stronger source channel; a wide mix can cancel in mono.
        channel = int(np.argmax(np.mean(reference ** 2, axis=0)))
        x = reference[:, channel] - np.mean(reference[:, channel])
        y = observed[:, channel] - np.mean(observed[:, channel])
        fft_size = 1 << (len(x) + len(y) - 2).bit_length()
        spectrum = np.fft.rfft(y, fft_size) * np.conj(np.fft.rfft(x, fft_size))
        cross = np.fft.irfft(spectrum, fft_size)
        limit = min(max_lag, window - 1)
        lags = np.arange(-limit, limit + 1)
        lag = int(lags[np.argmax(cross[lags % fft_size])])
        # Refine the measured delay below one output sample. Integer-only
        # alignment exaggerates error at high frequencies. This changes
        # only comparison arrays; the recorded WAV is never edited.
        omega = 2 * np.pi * np.fft.rfftfreq(fft_size)
        refined = float(lag)
        for _ in range(5):
            z = spectrum[1:-1] * np.exp(1j * omega[1:-1] * refined)
            derivative = -np.sum(omega[1:-1] * z.imag)
            curvature = -np.sum(omega[1:-1] ** 2 * z.real)
            if curvature >= -1e-20:
                break
            step = float(derivative / curvature)
            refined = float(np.clip(refined - step, lag - 1, lag + 1))
            if abs(step) < 1e-7:
                break
        shift = np.exp(-1j * omega * (refined - lag))
        delayed = np.column_stack([
            np.fft.irfft(np.fft.rfft(reference[:, side] - np.mean(reference[:, side]), fft_size) * shift,
                         fft_size)[:window]
            for side in range(2)
        ])
        if lag >= 0:
            x0 = delayed[:window - lag or None]
            y0 = observed[lag:]
        else:
            x0 = delayed[-lag:]
            y0 = observed[:window + lag]
        guard = min(256, len(x0) // 20)
        x0 = x0[guard:-guard]
        y0 = y0[guard:-guard]
        channels = []
        for side in range(2):
            sx = x0[:, side] - np.mean(x0[:, side])
            sy = y0[:, side] - np.mean(y0[:, side])
            if np.std(sx) < 1e-12 or np.std(sy) < 1e-12:
                channels.append({'source_silence': bool(np.std(sx) < 1e-12),
                                 'capture_silence': bool(np.std(sy) < 1e-12),
                                 'waveform_correlation': None})
                continue
            gain = float(np.dot(sx, sy) / max(1e-20, np.dot(sx, sx)))
            error = sy - gain * sx
            signal_rms = float(np.sqrt(np.mean((gain * sx) ** 2)))
            error_rms = float(np.sqrt(np.mean(error ** 2)))
            channels.append({
                'gain_capture_over_source': gain,
                'waveform_correlation': float(np.corrcoef(sx, sy)[0, 1]),
                'gain_fitted_snr_db': log_db(signal_rms / max(error_rms, 1e-15)),
                'difference_rms_dbfs': log_db(error_rms),
            })
        rows.append({'start_seconds': start / rate, 'window_seconds': window / rate,
                     'lag_samples': lag, 'fractional_lag_samples': refined,
                     'lag_milliseconds': refined * 1000 / rate,
                     'channel_statistics': channels})
    active = [row for row in rows if 'lag_samples' in row]
    report = {
        'source': str(args.source), 'capture': str(args.capture),
        'comparison_rate_hz': rate,
        'source_decoded_seconds': len(source) / rate,
        'capture_seconds': len(recording) / rate,
        'windows': rows,
        'timing_drift_samples_last_minus_first': active[-1]['lag_samples'] - active[0]['lag_samples']
            if len(active) >= 2 else None,
        'fractional_delay_change_samples_last_minus_first': active[-1]['fractional_lag_samples'] - active[0]['fractional_lag_samples']
            if len(active) >= 2 else None,
        'median_start_latency_milliseconds': float(np.median([row['lag_milliseconds'] for row in active]))
            if active else None,
        'scope': 'Direct-source comparison only. Fractional-delay alignment and gain fitting are measurements; no audio files are changed. Full-mix error includes GBA/emulator filtering and must not be equated with single-tone quantization SNR.',
    }
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--capture', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--window-seconds', type=float, default=8)
    parser.add_argument('--max-latency-seconds', type=float, default=.15)
    args = parser.parse_args()
    compare(args)


if __name__ == '__main__':
    main()
