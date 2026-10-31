#!/usr/bin/env python3
"""Offline GM orchestration with FluidR3; produces stereo floats, never GBA DSP.

render_song(song, sample_rate=32768) returns an Nx2 float32 array spanning
exactly round(beats * 60 / bpm * sample_rate) frames. Optional tail_seconds
adds the released sound/effect tail for an external loop-folding stage.

Program numbers are 0-based GM; preset selection is explicit and validated.
Note commands are scheduled at rounded sample indices (FluidSynth internally
renders 64-sample quanta). The output is unnormalized and intentionally has
headroom; the caller performs downsampling/mastering/8-bit quantization.
"""
from __future__ import annotations

import argparse
import ctypes as C
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
FLUIDR3 = HERE / "banks/fluidr3/usr/share/sounds/sf2/FluidR3_GM.sf2"
TIMGM = Path('/usr/share/sounds/sf2/TimGM6mb.sf2')


def soundfont_path(path: str | Path | None = None) -> Path:
    candidates = [Path(path)] if path else []
    if not path and os.environ.get('GBA_SOUNDFONT'):
        candidates.append(Path(os.environ['GBA_SOUNDFONT']))
    if not path:
        candidates.extend([FLUIDR3, TIMGM])
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError('No GM SoundFont found: ' + ', '.join(map(str, candidates)))


def _bind():
    lib = C.CDLL(ctypes.util.find_library('fluidsynth') or 'libfluidsynth.so.3')
    pointer, integer, number, string = C.c_void_p, C.c_int, C.c_double, C.c_char_p
    declarations = {
        'new_fluid_settings': (pointer, []),
        'delete_fluid_settings': (None, [pointer]),
        'fluid_settings_setnum': (integer, [pointer, string, number]),
        'fluid_settings_setint': (integer, [pointer, string, integer]),
        'new_fluid_synth': (pointer, [pointer]),
        'delete_fluid_synth': (None, [pointer]),
        'fluid_synth_sfload': (integer, [pointer, string, integer]),
        'fluid_synth_get_sfont_by_id': (pointer, [pointer, integer]),
        'fluid_sfont_iteration_start': (None, [pointer]),
        'fluid_sfont_iteration_next': (pointer, [pointer]),
        'fluid_preset_get_banknum': (integer, [pointer]),
        'fluid_preset_get_num': (integer, [pointer]),
        'fluid_preset_get_name': (string, [pointer]),
        'fluid_synth_set_channel_type': (integer, [pointer, integer, integer]),
        'fluid_synth_program_select': (integer, [pointer, integer, integer, integer, integer]),
        'fluid_synth_cc': (integer, [pointer, integer, integer, integer]),
        'fluid_synth_noteon': (integer, [pointer, integer, integer, integer]),
        'fluid_synth_noteoff': (integer, [pointer, integer, integer]),
        'fluid_synth_all_sounds_off': (integer, [pointer, integer]),
        'fluid_synth_set_interp_method': (integer, [pointer, integer, integer]),
        'fluid_synth_set_reverb': (None, [pointer, number, number, number, number]),
        'fluid_synth_set_chorus': (None, [pointer, integer, number, number, number, integer]),
        'fluid_synth_write_float': (integer, [pointer, integer, pointer, integer, integer, pointer, integer, integer]),
        'fluid_version_str': (string, []),
    }
    for name, (returns, arguments) in declarations.items():
        fn = getattr(lib, name)
        fn.restype, fn.argtypes = returns, arguments
    return lib


_LIB = None
_PRESET_CACHE: dict[str, list[dict]] = {}


def library():
    global _LIB
    if _LIB is None:
        _LIB = _bind()
    return _LIB


class Synth:
    def __init__(self, sample_rate=32768, soundfont=None, gain=.28, effects=True):
        self.lib = library()
        self.settings = self.synth = None
        self.path = soundfont_path(soundfont)
        if not 22050 <= sample_rate <= 96000:
            raise ValueError('Render at 22050..96000 Hz; downsample for GBA after rendering')
        self.settings = self.lib.new_fluid_settings()
        if not self.settings:
            raise MemoryError('new_fluid_settings failed')
        try:
            for key, value in [('synth.sample-rate', sample_rate), ('synth.gain', gain)]:
                if self.lib.fluid_settings_setnum(self.settings, key.encode(), float(value)) != 0:
                    raise ValueError('Unsupported FluidSynth setting: '+key)
            for key, value in [('synth.polyphony', 256), ('synth.midi-channels', 16),
                               ('synth.cpu-cores', 1), ('synth.threadsafe-api', 0),
                               ('synth.min-note-length', 0),
                               ('synth.reverb.active', int(effects)),
                               ('synth.chorus.active', int(effects))]:
                if self.lib.fluid_settings_setint(self.settings, key.encode(), value) != 0:
                    raise ValueError('Unsupported FluidSynth setting: '+key)
            self.synth = self.lib.new_fluid_synth(self.settings)
            if not self.synth:
                raise MemoryError('new_fluid_synth failed')
            self.sfid = self.lib.fluid_synth_sfload(self.synth, str(self.path).encode(), 0)
            if self.sfid < 0:
                raise RuntimeError('Failed to load SoundFont: '+str(self.path))
            self.lib.fluid_synth_set_interp_method(self.synth, -1, 7)
            # Small, wide room; restrained chorus avoids blurring quick rhythms.
            self.lib.fluid_synth_set_reverb(self.synth, .34, .58, 72.0, .19)
            self.lib.fluid_synth_set_chorus(self.synth, 2, .18, .32, 2.5, 0)
            self.presets = self._presets()
            self.available = {(p['bank'], p['program']): p['name'] for p in self.presets}
        except BaseException:
            self.close()
            raise

    def _presets(self):
        key = str(self.path)
        if key not in _PRESET_CACHE:
            sf = self.lib.fluid_synth_get_sfont_by_id(self.synth, self.sfid)
            self.lib.fluid_sfont_iteration_start(sf)
            result = []
            while True:
                preset = self.lib.fluid_sfont_iteration_next(sf)
                if not preset:
                    break
                bank = self.lib.fluid_preset_get_banknum(preset)
                result.append({'bank': bank,
                               'program': self.lib.fluid_preset_get_num(preset),
                               'name': self.lib.fluid_preset_get_name(preset).decode('utf-8', 'replace'),
                               'drum': bank == 128})
            _PRESET_CACHE[key] = sorted(result, key=lambda p: (p['bank'], p['program']))
        return _PRESET_CACHE[key]

    def close(self):
        if self.synth:
            self.lib.delete_fluid_synth(self.synth)
            self.synth = None
        if self.settings:
            self.lib.delete_fluid_settings(self.settings)
            self.settings = None

    def __enter__(self): return self
    def __exit__(self, *args): self.close()

    def write(self, target, start, end):
        n = end-start
        if n <= 0:
            return
        # Interleaved stereo: both output pointers reference the same array.
        address = target.ctypes.data + start * 2 * target.dtype.itemsize
        if self.lib.fluid_synth_write_float(self.synth, n, address, 0, 2, address, 1, 2) != 0:
            raise RuntimeError('FluidSynth sample rendering failed')


def listpresets(soundfont=None) -> list[dict]:
    """Return actual bank/program/name triples; no assumed drum-kit support."""
    with Synth(soundfont=soundfont, effects=False) as synth:
        return [dict(p) for p in synth.presets]


# Alias for callers using conventional snake_case.
list_presets = listpresets


def _parts(song):
    parts = {str(k): dict(v) for k, v in song['parts'].items()}
    if not parts or len(parts) > 14:
        raise ValueError('Expected 1..14 scored instrumental parts')
    drums = [name for name, spec in parts.items() if spec.get('drum', False)]
    if len(drums) > 2:
        raise ValueError('At most two independent drum kits are supported')
    if len(parts)-len(drums) > 12:
        raise ValueError('At most twelve melodic parts are supported')
    drum_channels = dict(zip(drums, [9, 15]))
    available = iter(ch for ch in range(16) if ch != 9 and ch not in drum_channels.values())
    for name, spec in parts.items():
        spec['channel'] = drum_channels[name] if name in drum_channels else next(available)
        spec['program'] = int(spec.get('program', 0))
        spec['bank'] = 128 if spec.get('drum', False) else int(spec.get('bank', 0))
        spec['pan'] = float(spec.get('pan', 0))
        spec['volume'] = float(spec.get('volume', .78))
        if not 0 <= spec['program'] <= 127 or not -1 <= spec['pan'] <= 1 or not 0 <= spec['volume'] <= 1:
            raise ValueError('Invalid program, pan or volume for '+name)
    return parts


def _select_parts(synth, parts):
    result = []
    for name, spec in parts.items():
        channel, bank, program = spec['channel'], spec['bank'], spec['program']
        requested_program = program
        fallback = None
        if (bank, program) not in synth.available:
            if bank == 128 and (128, 0) in synth.available:
                program, fallback = 0, 'Requested drum kit absent; standard kit used'
            else:
                raise ValueError(f'Missing SoundFont preset bank{bank}/program{program} ({name})')
        synth.lib.fluid_synth_set_channel_type(synth.synth, channel, int(bank == 128))
        if synth.lib.fluid_synth_program_select(synth.synth, channel, synth.sfid, bank, program) != 0:
            raise RuntimeError(f'Could not select preset for {name}')
        controllers = [(7, round(spec['volume']*127)), (10, round((spec['pan']+1)*63.5)),
                       (11, 127), (91, round(float(spec.get('reverb', .26))*127)),
                       (93, round(float(spec.get('chorus', .08))*127))]
        for cc, value in controllers:
            synth.lib.fluid_synth_cc(synth.synth, channel, cc, min(127, max(0, value)))
        result.append({'part': name, 'channel': channel, 'drum': bank == 128,
                       'requested_program': requested_program, 'bank': bank, 'program': program,
                       'preset_name': synth.available[bank, program],
                       'pan': spec['pan'], 'volume': spec['volume'], 'fallback': fallback})
    return result


def instrument_metadata(song: dict, soundfont=None) -> dict:
    with Synth(soundfont=soundfont, effects=False) as synth:
        selected = _select_parts(synth, _parts(song))
        return {'soundfont': synth.path.name, 'fluidsynth': synth.lib.fluid_version_str().decode(),
                'parts': selected}


def render_song(song: dict, sample_rate: int = 32768, *, soundfont=None,
                gain: float | None = None, tail_seconds: float = 0,
                effects: bool = True, return_metadata: bool = False):
    """Render a complete score to unmastered stereo float32, with exact length.

    Optional return_metadata=True returns (audio, metadata). Scheduling uses
    stable off-before-on sample ordering and guards retriggered notes against
    stale note-off events. Parts use separate MIDI channels, including distinct
    drum channels/types for a second kit. Event program/pan overrides must agree
    with their part; a voice cannot silently change instrument mid-song.
    """
    sample_rate = int(sample_rate)
    bpm, beats = float(song['bpm']), float(song['beats'])
    if bpm <= 0 or beats <= 0 or tail_seconds < 0:
        raise ValueError('Tempo/length must be positive and tail nonnegative')
    main_samples = round(beats * 60/bpm * sample_rate)
    total_samples = main_samples + round(float(tail_seconds)*sample_rate)
    output = np.zeros((total_samples, 2), dtype=np.float32)
    parts = _parts(song)
    schedule = []
    for token, event in enumerate(song['events']):
        name = event['voice']
        if name not in parts:
            raise ValueError('Event references undefined part '+name)
        spec = parts[name]
        if 'program' in event and int(event['program']) != spec['program']:
            raise ValueError('Per-event program differs from scored part '+name)
        if 'pan' in event and abs(float(event['pan'])-spec['pan']) > 1e-6:
            raise ValueError('Per-event pan differs from scored part '+name)
        beat, duration = float(event['beat']), float(event['duration'])
        pitch, velocity = int(event['pitch']), float(event['velocity'])
        if beat < 0 or duration <= 0 or beat+duration > beats+1e-6:
            raise ValueError(f'Event outside song: {name} beat{beat} duration{duration}')
        if not 0 <= pitch <= 127 or not 0 <= velocity <= 1:
            raise ValueError('Invalid pitch/velocity')
        if velocity == 0:
            continue
        start = min(main_samples-1, round(beat*60/bpm*sample_rate))
        end = min(main_samples, max(start+1, round((beat+duration)*60/bpm*sample_rate)))
        schedule.append((start, 1, token, spec['channel'], pitch, max(1, round(velocity*127))))
        schedule.append((end, 0, token, spec['channel'], pitch, 0))
    schedule.sort(key=lambda e: (e[0], e[1], e[2]))
    gain = float(song.get('render_gain', .28) if gain is None else gain)
    if not 0 < gain <= 2:
        raise ValueError('Synth gain must be in (0,2]')
    with Synth(sample_rate, soundfont, gain, effects) as synth:
        selection = _select_parts(synth, parts)
        active = {}
        cursor = 0
        for sample, is_on, token, channel, pitch, velocity in schedule:
            if sample > cursor:
                synth.write(output, cursor, sample)
                cursor = sample
            key = channel, pitch
            if is_on:
                if key in active:
                    synth.lib.fluid_synth_noteoff(synth.synth, channel, pitch)
                synth.lib.fluid_synth_noteon(synth.synth, channel, pitch, velocity)
                active[key] = token
            elif active.get(key) == token:
                synth.lib.fluid_synth_noteoff(synth.synth, channel, pitch)
                del active[key]
        synth.write(output, cursor, total_samples)
        metadata = {'soundfont': synth.path.name,
                    'fluidsynth': synth.lib.fluid_version_str().decode(),
                    'sample_rate': sample_rate, 'main_samples': main_samples,
                    'tail_samples': total_samples-main_samples,
                    'gain': gain, 'effects': bool(effects), 'parts': selection,
                    'note_count': len(schedule)//2,
                    'scheduled_sample_accuracy': 1,
                    'synth_internal_block_samples': 64,
                    'peak': float(np.max(np.abs(output), initial=0)),
                    'rms': float(np.sqrt(np.mean(output.astype(np.float64)**2)))}
    if not np.isfinite(output).all():
        raise RuntimeError('Nonfinite synthesis output')
    return (output, metadata) if return_metadata else output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--presets', type=Path, help='Write actual instrument/kit inventory JSON')
    parser.add_argument('--score', type=Path, help='Render one JSON song or first song in a song collection')
    parser.add_argument('--output', type=Path, help='Write interleaved stereo float32 .npy')
    args = parser.parse_args()
    if args.presets:
        path = soundfont_path()
        report = {'soundfont': path.name, 'soundfont_bytes': path.stat().st_size,
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'fluidsynth': library().fluid_version_str().decode(), 'presets': listpresets(path)}
        args.presets.write_text(json.dumps(report, indent=2)+'\n')
        print(f"{path.name}: {len(report['presets'])} presets")
    if args.score:
        score = json.loads(args.score.read_text())
        song = score['songs'][0] if 'songs' in score else score
        output, meta = render_song(song, return_metadata=True)
        if args.output:
            np.save(args.output, output)
            args.output.with_suffix('.json').write_text(json.dumps(meta, indent=2)+'\n')
        print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
