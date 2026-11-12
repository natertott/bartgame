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
# Profile9 is the selected final Drain; 0..8 preserve historical art studies.
BART_SEWER ?= 9
ifneq ($(words $(BART_SEWER)),1)
$(error BART_SEWER must be one integer in 0..9)
endif
ifneq ($(BART_SEWER),$(filter $(BART_SEWER),0 1 2 3 4 5 6 7 8 9))
$(error BART_SEWER must be one integer in 0..9)
endif
SEWER_STAMP := $(GEN)/sewer-profile-$(BART_SEWER).stamp
# Selected Winebound HUD; title Options select frames/colors at runtime.
BART_UI ?= 6
ifneq ($(words $(BART_UI)),1)
$(error BART_UI must be one integer in 0..10)
endif
ifneq ($(BART_UI),$(filter $(BART_UI),0 1 2 3 4 5 6 7 8 9 10))
$(error BART_UI must be one integer in 0..10)
endif
UI_STAMP := $(GEN)/ui-profile-$(BART_UI).stamp
# Gilt HUD refresh; zero preserves the earlier compact interface/item art.
BART_HUD ?= 1
ifneq ($(words $(BART_HUD)),1)
$(error BART_HUD must be one integer in 0..1)
endif
ifneq ($(BART_HUD),$(filter $(BART_HUD),0 1))
$(error BART_HUD must be one integer in 0..1)
endif
HUD_STAMP := $(GEN)/hud-profile-$(BART_HUD).stamp
# Selected Workbench items with the separately selected Ledger map.
BART_MENU ?= 1
ifneq ($(words $(BART_MENU)),1)
$(error BART_MENU must be one integer in 0..10)
endif
ifneq ($(BART_MENU),$(filter $(BART_MENU),0 1 2 3 4 5 6 7 8 9 10))
$(error BART_MENU must be one integer in 0..10)
endif
MENU_STAMP := $(GEN)/menu-profile-$(BART_MENU).stamp

# Selected five enemies and the purple Broken Heart are the normal build.
# 0 preserves pre-selection art; 1..10 retain historical comparison sets.
BART_ENEMY ?= 11
ifneq ($(words $(BART_ENEMY)),1)
$(error BART_ENEMY must be one integer in 0..11)
endif
ifneq ($(BART_ENEMY),$(filter $(BART_ENEMY),0 1 2 3 4 5 6 7 8 9 10 11))
$(error BART_ENEMY must be one integer in 0..11)
endif
ENEMY_STAMP := $(GEN)/enemy-profile-$(BART_ENEMY).stamp
# Optional lab fixtures; all three mechanics also live in normal encounters.
BART_ENEMY_LAB ?= 0
ifneq ($(words $(BART_ENEMY_LAB)),1)
$(error BART_ENEMY_LAB must be 0 or 1)
endif
ifneq ($(BART_ENEMY_LAB),$(filter $(BART_ENEMY_LAB),0 1))
$(error BART_ENEMY_LAB must be 0 or 1)
endif
LAB_STAMP := $(GEN)/enemy-lab-$(BART_ENEMY_LAB).stamp

# Profile32 refines forest room composition; 0..31 remain historical.
BART_FOREST ?= 32
ifneq ($(words $(BART_FOREST)),1)
$(error BART_FOREST must be one integer in 0..32)
endif
ifneq ($(BART_FOREST),$(filter $(BART_FOREST),0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32))
$(error BART_FOREST must be one integer in 0..32)
endif
FOREST_STAMP := $(GEN)/forest-profile-$(BART_FOREST).stamp

# Selected Weathered Heights and Contour Folio with Exploded Shelves icons.
# Explicit profiles0--11 retain the historical builds.
BART_CREAM ?= 12
ifneq ($(words $(BART_CREAM)),1)
$(error BART_CREAM must be one integer in 0..12)
endif
ifneq ($(BART_CREAM),$(filter $(BART_CREAM),0 1 2 3 4 5 6 7 8 9 10 11 12))
$(error BART_CREAM must be one integer in 0..12)
endif
CREAM_STAMP := $(GEN)/cream-profile-$(BART_CREAM).stamp

ARCH    := -mcpu=arm7tdmi -mtune=arm7tdmi
CFLAGS  := $(ARCH) -O2 -g -Wall -Wno-unused-function -fno-strict-aliasing \
           -fomit-frame-pointer -ffunction-sections -fdata-sections \
           -fno-builtin -nostdlib -Isrc -I$(GEN) -MMD -MP
THUMB   := -mthumb
ARM     := -marm
LDFLAGS := $(ARCH) -mthumb -nostdlib -Wl,-T,gba.ld -Wl,--gc-sections -Wl,-Map,$(BUILD)/$(TARGET).map
ifeq ($(BART_FOREST),30)
LDFLAGS += -Wl,--undefined=tree_study_begin
endif
LIBS    := -lgcc
PROFILE ?= 0
ifneq ($(words $(PROFILE)),1)
$(error PROFILE must be 0 or 1)
endif
ifneq ($(PROFILE),$(filter $(PROFILE),0 1))
$(error PROFILE must be 0 or 1)
endif
CFLAGS += -DBART_PROFILE=$(PROFILE) -DBART_ENEMY_LAB=$(BART_ENEMY_LAB)
PROFILE_STAMP := $(BUILD)/profile-$(PROFILE).stamp

SRC_C     := $(filter-out %_iwram.c,$(wildcard src/*.c))
ifneq ($(BART_CREAM),6)
SRC_C     := $(filter-out src/cream_visuals.c,$(SRC_C))
endif
ifeq ($(filter $(BART_CREAM),7 8 9 10 11 12),)
SRC_C     := $(filter-out src/cream_polish.c src/cream_polish_blend.c,$(SRC_C))
endif
ifneq ($(BART_CREAM),12)
SRC_C     := $(filter-out src/cream_topology.c src/cream_map_concepts.c src/cream_map_forms_a.c src/cream_map_forms_b.c,$(SRC_C))
endif
ifeq ($(PROFILE),0)
SRC_C     := $(filter-out src/performance.c,$(SRC_C))
endif
ifneq ($(BART_FOREST),30)
SRC_C     := $(filter-out src/tree_study.c,$(SRC_C))
endif
ifeq ($(filter $(BART_FOREST),31 32),)
SRC_C     := $(filter-out src/forest_trees.c,$(SRC_C))
endif
ifneq ($(BART_FOREST),32)
SRC_C     := $(filter-out src/forest_paths.c,$(SRC_C))
endif
# Even an empty extra object changes GNU ld's ARM/Thumb veneer ordering.
# Historical profiles retain their exact original linker input list.
ifneq ($(filter $(BART_FOREST),0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 31 32),)
SRC_C     := $(filter-out src/canopy_scene.c,$(SRC_C))
endif
SRC_IWRAM := $(wildcard src/*_iwram.c)
SRC_S     := $(wildcard src/*.s)
GEN_C     := $(GEN)/assets.c
ART       := $(wildcard art/reboot_*.py) art/reboot_contracts.json tools/build_assets.py \
             art/palettes.py art/tiles.py art/sprites.py art/rooms.py art/ui_kit.py \
             art/ui_font.py art/faces.py art/title.py art/sw_folk.py art/sword_studies.py \
             art/sewer_concepts.py art/sewer_concepts_terrain.py art/sewer_concepts_npcs.py \
             art/sewer_v3_fixtures.py art/ui_studies.py art/sewer_final.py art/sewer_final_contracts.py \
             $(wildcard art/enemy_studies*.py) art/enemy_heart.py \
             $(wildcard art/forest_concepts*.py) $(wildcard art/forest_canopy_adaptive*.py) \
             $(wildcard art/forest_canopy_emerald*.py) $(wildcard art/forest_tree_study*.py) \
             $(wildcard art/forest_trees*.py) $(wildcard art/forest_cohesion*.py) \
             $(wildcard art/hud_gilt*.py) $(wildcard art/enemy_prototypes*.py) \
             art/arcade_cabinet.py $(wildcard art/cream_*.py) $(wildcard art/handoff_*.py)

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

$(UI_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/ui-profile-*.stamp
	@printf '%s\n' '$(BART_UI)' > $@

$(MENU_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/menu-profile-*.stamp
	@printf '%s\n' '$(BART_MENU)' > $@

$(ENEMY_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/enemy-profile-*.stamp
	@printf '%s\n' '$(BART_ENEMY)' > $@

$(FOREST_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/forest-profile-*.stamp
	@printf '%s\n' '$(BART_FOREST)' > $@

$(CREAM_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/cream-profile-*.stamp
	@printf '%s\n' '$(BART_CREAM)' > $@

$(HUD_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/hud-profile-*.stamp
	@printf '%s\n' '$(BART_HUD)' > $@

$(LAB_STAMP):
	@mkdir -p $(GEN)
	@rm -f $(GEN)/enemy-lab-*.stamp
	@printf '%s\n' '$(BART_ENEMY_LAB)' > $@

$(GEN)/assets.c: $(ART) $(SWING_STAMP) $(SEWER_STAMP) $(UI_STAMP) $(HUD_STAMP) $(MENU_STAMP) $(ENEMY_STAMP) $(FOREST_STAMP) $(LAB_STAMP) $(CREAM_STAMP)
	@mkdir -p $(GEN)
	BART_SWING=$(BART_SWING) BART_SEWER=$(BART_SEWER) BART_UI=$(BART_UI) BART_HUD=$(BART_HUD) BART_MENU=$(BART_MENU) BART_ENEMY=$(BART_ENEMY) BART_ENEMY_LAB=$(BART_ENEMY_LAB) BART_FOREST=$(BART_FOREST) BART_CREAM=$(BART_CREAM) $(PYTHON) tools/build_assets.py $(GEN)

$(GEN)/assets.h: $(GEN)/assets.c ;

$(BUILD)/assets.o: $(GEN)/assets.c
	$(CC) $(CFLAGS) $(THUMB) -c $< -o $@

$(BUILD)/%_iwram.o: src/%_iwram.c $(GEN)/assets.h $(PROFILE_STAMP)
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) $(ARM) -c $< -o $@

$(PROFILE_STAMP):
	@mkdir -p $(BUILD)
	@rm -f $(BUILD)/profile-*.stamp
	@touch $@

$(BUILD)/%.o: src/%.c $(GEN)/assets.h $(PROFILE_STAMP)
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) $(THUMB) -c $< -o $@

$(BUILD)/%.o: src/%.s
	@mkdir -p $(BUILD)
	$(CC) $(ARCH) -c $< -o $@

# The assembler embeds the original recordings directly; a re-import must
# relink even when the small assembly wrapper itself has not changed.
$(BUILD)/original_music_pcm.o: $(wildcard audio/original/pcm/*.pcm)

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
