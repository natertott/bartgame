# BARTGAME: a GBA game built from scratch.
#
#   make            builds bartgame.gba
#   make assets     regenerates build/gen/* from art/*.py
#   make clean
#
# Code is Thumb in ROM. Files named *_iwram.c are compiled as ARM and
# placed in IWRAM by the linker script (the hot per-actor loops).

PREFIX  := arm-none-eabi-
CC      := $(PREFIX)gcc
AS      := $(PREFIX)as
LD      := $(PREFIX)gcc
OBJCOPY := $(PREFIX)objcopy
GBAFIX  := ../tools/bin/gbafix
PYTHON  := python3

BUILD   := build
GEN     := $(BUILD)/gen
TARGET  := bartgame

ARCH    := -mcpu=arm7tdmi -mtune=arm7tdmi
CFLAGS  := $(ARCH) -O2 -g -Wall -Wno-unused-function -fno-strict-aliasing \
           -fomit-frame-pointer -ffunction-sections -fdata-sections \
           -fno-builtin -nostdlib -Isrc -I$(GEN) -MMD -MP
THUMB   := -mthumb
ARM     := -marm
LDFLAGS := $(ARCH) -mthumb -nostdlib -Wl,-T,gba.ld -Wl,--gc-sections -Wl,-Map,$(BUILD)/$(TARGET).map
LIBS    := -lgcc

SRC_C     := $(filter-out %_iwram.c,$(wildcard src/*.c))
SRC_IWRAM := $(wildcard src/*_iwram.c)
SRC_S     := $(wildcard src/*.s)
GEN_C     := $(GEN)/assets.c
ART       := $(wildcard art/*.py) tools/build_assets.py

OBJS := $(patsubst src/%.c,$(BUILD)/%.o,$(SRC_C)) \
        $(patsubst src/%.c,$(BUILD)/%.o,$(SRC_IWRAM)) \
        $(patsubst src/%.s,$(BUILD)/%.o,$(SRC_S)) \
        $(BUILD)/assets.o

.PHONY: all clean assets
all: $(TARGET).gba

assets: $(GEN)/assets.c

$(GEN)/assets.c $(GEN)/assets.h: $(ART)
	@mkdir -p $(GEN)
	$(PYTHON) tools/build_assets.py $(GEN)

$(BUILD)/assets.o: $(GEN)/assets.c
	$(CC) $(CFLAGS) $(THUMB) -c $< -o $@

$(BUILD)/%_iwram.o: src/%_iwram.c $(GEN)/assets.h
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) $(ARM) -c $< -o $@

$(BUILD)/%.o: src/%.c $(GEN)/assets.h
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) $(THUMB) -c $< -o $@

$(BUILD)/%.o: src/%.s
	@mkdir -p $(BUILD)
	$(CC) $(ARCH) -c $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJS) gba.ld
	$(LD) $(LDFLAGS) $(OBJS) $(LIBS) -o $@

$(TARGET).gba: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O binary $< $@
	$(GBAFIX) $@ -tBARTGAME -cBART -m00 >/dev/null
	@$(PREFIX)size $<

clean:
	rm -rf $(BUILD) $(TARGET).gba

-include $(OBJS:.o=.d)

# The maze generator compiled for the host: twenty thousand seeds checked
# for reachability (keys before gates, no lock in the way) and quests.
verify-world:
	gcc -w -I src -I build/gen -o build/host/gates build/host/gates.c src/world.c src/util.c
	./build/host/gates
.PHONY: verify-world
