#!/usr/bin/env python3
"""Capture the actual audio output of a GBA ROM executed by mGBA.

Requires mGBA 0.10.x Python bindings (source /workspace/setup/activate.sh).
No synthesis, EQ, limiting, normalisation or post-processing is applied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
import wave

import mgba
import mgba.core
import mgba.image
import mgba.log
from mgba._pylib import ffi


def symbols(elf: Path) -> dict[str, int]:
    nm = shutil.which('arm-none-eabi-nm')
    if nm is None:
        raise RuntimeError('arm-none-eabi-nm is missing; activate the GBA toolchain')
    values = {}
    for line in subprocess.check_output([nm, '-n', str(elf)], text=True).splitlines():
        columns = line.split()
        if len(columns) == 3:
            try:
                values[columns[2]] = int(columns[0], 16)
            except ValueError:
                pass
    return values


def read_u16(core, address):
    return core.memory.u8[address] | core.memory.u8[address + 1] << 8


def read_u32(core, address):
    return sum(core.memory.u8[address + i] << (8 * i) for i in range(4))


def write_u16(core, address, value):
    core.memory.u8[address] = value & 255
    core.memory.u8[address + 1] = value >> 8 & 255


def write_u32(core, address, value):
    for i in range(4):
        core.memory.u8[address + i] = value >> (8 * i) & 255


def capture(args):
    mgba.log.silence()
    table = symbols(args.elf)
    needed = ['gAudioReviewRequest', 'gAudioReviewActive', 'gAudioReviewFrame']
    missing = [name for name in needed if name not in table]
    if missing:
        raise RuntimeError('ROM ELF is missing review symbols: ' + ', '.join(missing))
    core = mgba.core.load_path(str(args.rom))
    if core is None:
        raise RuntimeError(f'mGBA could not load {args.rom}')
    image = mgba.image.Image(240, 160)
    core.set_video_buffer(image)
    core.set_audio_buffer_size(4096)
    channels = core.get_audio_channels()
    channels.set_rate(args.rate)
    core.reset()
    for _ in range(args.boot_frames):
        core.run_frame()
        channels.clear()
    for name in ['gAudioProfileMaxCycles', 'gAudioProfileSumCycles', 'gAudioProfileCalls']:
        if name in table:
            write_u32(core, table[name], 0)
    write_u16(core, table['gAudioReviewRequest'], args.song)
    total_frames = args.frames or math.ceil(args.seconds * core.frequency / core.frame_cycles)
    target_samples = (round(args.seconds * args.rate) if args.frames is None else
                      round(total_frames * core.frame_cycles / core.frequency * args.rate))
    samples_written = 0
    buffer = ffi.new('short[8192]')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    last_song_frame = None
    loops = 0
    active_samples = set()
    boundaries = []
    with wave.open(str(args.output), 'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(args.rate)
        for frame in range(total_frames + 1):
            core.run_frame()
            active = read_u16(core, table['gAudioReviewActive'])
            active_samples.add(active)
            song_frame = (read_u16(core, table['sSongFrame']) if 'sSongFrame' in table else
                          read_u32(core, table['gAudioReviewFrame']))
            if last_song_frame is not None and song_frame < last_song_frame:
                loops += 1
                boundaries.append({'emulated_frame': frame, 'sample': samples_written})
            last_song_frame = song_frame
            while channels.available:
                count = channels.read_into(buffer, min(channels.available, 4096))
                write_count = min(count, target_samples - samples_written)
                if write_count > 0:
                    output.writeframesraw(ffi.buffer(buffer, write_count * 4))
                    samples_written += write_count
            if samples_written >= target_samples:
                break
    if samples_written < target_samples:
        raise RuntimeError(f'Emulator audio underflow: {samples_written} < {target_samples}')
    if active_samples != {args.song}:
        raise RuntimeError(f'Unexpected active song IDs: {sorted(active_samples)}, expected {args.song}')
    metadata = {
        'capture_method': 'mGBA emulation of compiled GBA ARM ROM; unprocessed stereo output',
        'physical_hardware_capture': False,
        'emulator': 'mGBA', 'emulator_version': mgba.__version__,
        'rom': args.rom.name,
        'rom_sha256': hashlib.sha256(args.rom.read_bytes()).hexdigest(),
        'elf_sha256': hashlib.sha256(args.elf.read_bytes()).hexdigest(),
        'song_id': args.song,
        'sample_rate_hz': args.rate, 'channels': 2, 'sample_format': 'signed 16-bit little-endian PCM',
        'samples_per_channel': samples_written,
        'duration_seconds': samples_written / args.rate,
        'emulated_frame_rate': core.frequency / core.frame_cycles,
        'emulated_frames': frame + 1,
        'last_song_frame': last_song_frame,
        'song_timeline_symbol': 'sSongFrame' if 'sSongFrame' in table else 'gAudioReviewFrame',
        'observed_loop_count': loops, 'loop_boundaries': boundaries,
        'elapsed_wall_seconds': round(time.monotonic() - started, 3),
        'audio_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
        'hardware_registers_at_capture_end': {
            'sound_bias': hex(read_u16(core, 0x04000088)),
            'sound_control_high': hex(read_u16(core, 0x04000082)),
            'timer0_control': hex(read_u16(core, 0x04000102)),
            'note': 'Timer0 counter readout is not its reload value; rate is specified by the compiled song descriptor.',
        },
    }
    if 'gAudioProfileCalls' in table:
        calls = read_u32(core, table['gAudioProfileCalls'])
        maximum = read_u32(core, table['gAudioProfileMaxCycles'])
        total = read_u32(core, table['gAudioProfileSumCycles'])
        metadata['driver_cpu_profile'] = {
            'method': 'GBA timers 2+3 count cycles around sound_update; DMA stalls included',
            'calls': calls,
            'total_cycles': total,
            'maximum_cycles_per_update': maximum,
            'mean_cycles_per_update': round(total / max(1, calls), 3),
            'mean_percent_of_frame': round(total / max(1, calls) / core.frame_cycles * 100, 5),
            'maximum_percent_of_frame': round(maximum / core.frame_cycles * 100, 5),
            'scope': 'CPU driver only; DMA bus occupancy outside the call is excluded',
        }
    args.output.with_suffix('.capture.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata))
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--elf', type=Path, required=True)
    parser.add_argument('--song', type=int, required=True)
    length = parser.add_mutually_exclusive_group(required=True)
    length.add_argument('--seconds', type=float)
    length.add_argument('--frames', type=int)
    parser.add_argument('--rate', type=int, default=44100)
    parser.add_argument('--boot-frames', type=int, default=8)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.song <= 65535:
        parser.error('--song must be in 1..65535')
    if args.seconds is not None and args.seconds <= 0 or args.frames is not None and args.frames <= 0:
        parser.error('capture length must be positive')
    capture(args)


if __name__ == '__main__':
    main()
