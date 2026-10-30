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
# Approved production swing: Step-and-cut. Other profiles remain opt-in.
BART_SWING ?= 3
ifneq ($(words $(BART_SWING)),1)
$(error BART_SWING must be one integer in 0..5)
endif
ifneq ($(BART_SWING),$(filter $(BART_SWING),0 1 2 3 4 5))
$(error BART_SWING must be one integer in 0..5)
endif
SWING_STAMP := $(GEN)/swing-profile-$(BART_SWING).stamp
# Drain art choices remain review prototypes until the user selects one.
BART_SEWER ?= 0
ifneq ($(words $(BART_SEWER)),1)
$(error BART_SEWER must be one integer in 0..8)
endif
ifneq ($(BART_SEWER),$(filter $(BART_SEWER),0 1 2 3 4 5 6 7 8))
$(error BART_SEWER must be one integer in 0..8)
endif
SEWER_STAMP := $(GEN)/sewer-profile-$(BART_SEWER).stamp

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
ART       := $(wildcard art/reboot_*.py) art/reboot_contracts.json tools/build_assets.py \
             art/palettes.py art/tiles.py art/sprites.py art/rooms.py art/ui_kit.py \
             art/ui_font.py art/faces.py art/title.py art/sw_folk.py art/sword_studies.py \
             art/sewer_concepts.py art/sewer_concepts_terrain.py art/sewer_concepts_npcs.py \
             art/sewer_v3_fixtures.py

OBJS := $(patsubst src/%.c,$(BUILD)/%.o,$(SRC_C)) \
        $(patsubst src/%.c,$(BUILD)/%.o,$(SRC_IWRAM)) \
        $(patsubst src/%.s,$(BUILD)/%.o,$(SRC_S)) \
        $(BUILD)/assets.o

.PHONY: all clean assets
all: $(TARGET).gba

assets: $(GEN)/assets.c

# one run writes both (assets.h last), so a parallel make runs it once
$(SWING_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/swing-profile-*.stamp
	@printf '%s\n' '$(BART_SWING)' > $@

$(SEWER_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/sewer-profile-*.stamp
	@printf '%s\n' '$(BART_SEWER)' > $@

$(GEN)/assets.c: $(ART) $(SWING_STAMP) $(SEWER_STAMP)
	@mkdir -p $(GEN)
	BART_SWING=$(BART_SWING) BART_SEWER=$(BART_SEWER) $(PYTHON) tools/build_assets.py $(GEN)

$(GEN)/assets.h: $(GEN)/assets.c ;

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
	rm -rf $(BUILD) $(TARGET).gba build_pt bartgame_packtiles.gba

-include $(OBJS:.o=.d)

# The maze generator compiled for the host: twenty thousand seeds checked
# for reachability (keys before gates, no lock in the way) and quests.
verify-world:
	gcc -O2 -fno-builtin -w -I src -I build/gen -o build/host/gates build/host/gates.c src/world.c src/util.c
	./build/host/gates
	gcc -O2 -fno-builtin -w -I src -I build/gen -o build/host/pacing build/host/pacing.c src/world.c src/util.c
	./build/host/pacing
.PHONY: verify-world
