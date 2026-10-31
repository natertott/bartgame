#!/usr/bin/env python3
"""Write the standard GBA cartridge boot header and its complement checksum.

This small build utility has no external dependencies and does not modify game
code or pad a ROM. The logo is the fixed 156-byte GBA boot recognition sequence.
"""
from __future__ import annotations
import argparse
from pathlib import Path

GBA_LOGO = bytes.fromhex(
    '24ffae51699aa2213d84820a84e409ad11248b98c0817f21a352be199309ce201'
    '0464a4af82731ec58c7e83382e3cebf85f4df94ce4b09c194568ac01372a7fc9'
    'f844d73a3ca9a615897a327fc039876231dc7610304ae56bf38840040a70efdff'
    '52fe036f9530f197fbc08560d68025a963be03014e38e2f9a234ffbb3e034478'
    '0090cb88113a9465c07c6387f03cafd625e48b380aac7221d4f807'
)


def ascii_field(value, length, name):
    try:
        encoded = value.encode('ascii')
    except UnicodeEncodeError as error:
        raise ValueError(f'{name} must contain ASCII characters only') from error
    if len(encoded) > length:
        raise ValueError(f'{name} must contain at most {length} characters')
    return encoded.ljust(length, b'\0')


def fix_header(path, title='GBAORIGINAL', code='ORIG', maker='00'):
    rom = bytearray(path.read_bytes())
    if len(rom) < 0xC0 or len(rom) > 32 * 1024 * 1024:
        raise ValueError('GBA ROM must be at least 192 bytes and at most 32 MiB')
    assert len(GBA_LOGO) == 156
    rom[4:0xA0] = GBA_LOGO
    rom[0xA0:0xAC] = ascii_field(title, 12, 'title')
    rom[0xAC:0xB0] = ascii_field(code, 4, 'code')
    rom[0xB0:0xB2] = ascii_field(maker, 2, 'maker')
    rom[0xB2] = 0x96
    rom[0xB3:0xBC] = bytes(9)
    rom[0xBD] = (-sum(rom[0xA0:0xBD]) - 0x19) & 255
    rom[0xBE:0xC0] = bytes(2)
    path.write_bytes(rom)
    assert (sum(rom[0xA0:0xBE]) + 0x19) & 255 == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--title', default='GBAORIGINAL')
    parser.add_argument('--code', default='ORIG')
    parser.add_argument('--maker', default='00')
    args = parser.parse_args()
    fix_header(args.rom, args.title, args.code, args.maker)


if __name__ == '__main__':
    main()
