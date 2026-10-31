#!/usr/bin/env bash
set -euo pipefail
# Run from any directory; GAME_DIR/BUILD_DIR may override the local defaults.
tool_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
game_dir="${GAME_DIR:-$(cd "$tool_dir/.." && pwd)}"
build_dir="${BUILD_DIR:-$game_dir/build/soundtest}"
data_dir="${DATA_DIR:-$game_dir/src}"
asset_root="${ASSET_ROOT:-$game_dir}"
mkdir -p "$build_dir"
arch=(-mcpu=arm7tdmi -mtune=arm7tdmi)
asarch=(-mcpu=arm7tdmi)
cflags=("${arch[@]}" -mthumb -O2 -g -Wall -Wextra -fomit-frame-pointer
        -ffunction-sections -fdata-sections -fno-builtin -nostdlib
        -fno-strict-aliasing
        -I"$game_dir/src")
arm-none-eabi-gcc "${cflags[@]}" -c "$game_dir/src/sound.c" -o "$build_dir/sound.o"
arm-none-eabi-gcc "${cflags[@]}" -c "$data_dir/soundtrack_data.c" -o "$build_dir/soundtrack_data.o"
arm-none-eabi-gcc "${cflags[@]}" -c "$tool_dir/player.c" -o "$build_dir/player.o"
arm-none-eabi-as "${asarch[@]}" "$game_dir/src/crt0.s" -o "$build_dir/crt0.o"
# Relative .incbin paths resolve from the game directory, matching its Makefile.
(cd "$asset_root" && arm-none-eabi-as "${asarch[@]}" "$data_dir/soundtrack_pcm.s" -o "$build_dir/soundtrack_pcm.o")
arm-none-eabi-gcc "${arch[@]}" -mthumb -nostdlib \
    -Wl,-T,"$game_dir/gba.ld" -Wl,--gc-sections -Wl,-Map,"$build_dir/soundtrack.map" \
    "$build_dir/crt0.o" "$build_dir/player.o" "$build_dir/sound.o" \
    "$build_dir/soundtrack_data.o" "$build_dir/soundtrack_pcm.o" -lgcc \
    -o "$build_dir/soundtrack.elf"
arm-none-eabi-objcopy -O binary "$build_dir/soundtrack.elf" "$build_dir/soundtrack.gba"
python3 "$tool_dir/fix_header.py" "$build_dir/soundtrack.gba" --title "${ROM_TITLE:-GBAORIGINAL}" --code "${ROM_CODE:-ORIG}"
arm-none-eabi-size "$build_dir/soundtrack.elf"
printf 'Built %s\n' "$build_dir/soundtrack.gba"
