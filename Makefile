.PHONY: default all
default: build
all: eu jp usa demo_jp demo_usa

MAKEFLAGS += --no-print-directory

.PHONY: build eu jp usa demo_jp demo_usa custom quickstart mapexplore
build: GAME_VERSION ?=USA
build: tools
	@$(MAKE) -f GBA.mk build GAME_VERSION=$(GAME_VERSION)

eu: GAME_VERSION=EU
jp: GAME_VERSION=JP
usa: GAME_VERSION=USA
demo_jp: GAME_VERSION=DEMO_JP
demo_usa: GAME_VERSION=DEMO_USA
eu jp usa demo_jp demo_usa: tools
	@$(MAKE) GAME_VERSION=$(GAME_VERSION)

custom: tools
	@$(MAKE) GAME_VERSION=USA CUSTOM=1

# Objects whose SOURCE is conditional on QUICKSTART or MAPEXPLORE. None of
# them depends on the flags that select a variant, so make will happily
# reuse one built for a different build - which has produced a hybrid ROM
# more than once (a shipping ROM with the testkit's game.o; a 'vanilla
# audio' measurement still carrying a 7,884Hz m4a.o; and a mapexplore
# build that failed to link because data/scripts.o still had QUICKSTART's
# script table in it). Every variant target below deletes the lot first.
# Regenerate with:
#   grep -rl 'QUICKSTART\|MAPEXPLORE' src/ data/ asm/ --include=*.c --include=*.s
VARIANT_OBJS := \
	build/USA/data/scripts.o \
	build/USA/src/collision.o build/USA/src/collision.s build/USA/src/collision.i \
	build/USA/src/data/transitions.o build/USA/src/data/transitions.s build/USA/src/data/transitions.i \
	build/USA/src/enemy/businessScrub.o build/USA/src/enemy/businessScrub.s build/USA/src/enemy/businessScrub.i \
	build/USA/src/enemy/chuchuBoss.o build/USA/src/enemy/chuchuBoss.s build/USA/src/enemy/chuchuBoss.i \
	build/USA/src/game.o build/USA/src/game.s build/USA/src/game.i \
	build/USA/src/gameUtils.o build/USA/src/gameUtils.s build/USA/src/gameUtils.i \
	build/USA/src/gba/m4a.o build/USA/src/gba/m4a.s build/USA/src/gba/m4a.i \
	build/USA/src/interrupts.o build/USA/src/interrupts.s build/USA/src/interrupts.i \
	build/USA/src/itemMetaData.o build/USA/src/itemMetaData.s build/USA/src/itemMetaData.i \
	build/USA/src/itemUtils.o build/USA/src/itemUtils.s build/USA/src/itemUtils.i \
	build/USA/src/manager/ezloHintManager.o build/USA/src/manager/ezloHintManager.s build/USA/src/manager/ezloHintManager.i \
	build/USA/src/manager/miscManager.o build/USA/src/manager/miscManager.s build/USA/src/manager/miscManager.i \
	build/USA/src/manager/vaati3StartManager.o build/USA/src/manager/vaati3StartManager.s build/USA/src/manager/vaati3StartManager.i \
	build/USA/src/menu/figurineMenu.o build/USA/src/menu/figurineMenu.s build/USA/src/menu/figurineMenu.i \
	build/USA/src/menu/kinstoneMenu.o build/USA/src/menu/kinstoneMenu.s build/USA/src/menu/kinstoneMenu.i \
	build/USA/src/menu/pauseMenuScreen6.o build/USA/src/menu/pauseMenuScreen6.s build/USA/src/menu/pauseMenuScreen6.i \
	build/USA/src/npc/ministerPotho.o build/USA/src/npc/ministerPotho.s build/USA/src/npc/ministerPotho.i \
	build/USA/src/npc/npc4E.o build/USA/src/npc/npc4E.s build/USA/src/npc/npc4E.i \
	build/USA/src/object/bossDoor.o build/USA/src/object/bossDoor.s build/USA/src/object/bossDoor.i \
	build/USA/src/object/cutsceneOrchestrator.o build/USA/src/object/cutsceneOrchestrator.s build/USA/src/object/cutsceneOrchestrator.i \
	build/USA/src/object/figurineDevice.o build/USA/src/object/figurineDevice.s build/USA/src/object/figurineDevice.i \
	build/USA/src/object/itemOnGround.o build/USA/src/object/itemOnGround.s build/USA/src/object/itemOnGround.i \
	build/USA/src/object/pot.o build/USA/src/object/pot.s build/USA/src/object/pot.i \
	build/USA/src/object/pressurePlate.o build/USA/src/object/pressurePlate.s build/USA/src/object/pressurePlate.i \
	build/USA/src/object/specialChest.o build/USA/src/object/specialChest.s build/USA/src/object/specialChest.i \
	build/USA/src/playerItem/playerItemBomb.o build/USA/src/playerItem/playerItemBomb.s build/USA/src/playerItem/playerItemBomb.i \
	build/USA/src/playerItem/playerItemBottle.o build/USA/src/playerItem/playerItemBottle.s build/USA/src/playerItem/playerItemBottle.i \
	build/USA/src/playerUtils.o build/USA/src/playerUtils.s build/USA/src/playerUtils.i \
	build/USA/src/roomInit.o build/USA/src/roomInit.s build/USA/src/roomInit.i \
	build/USA/src/script.o build/USA/src/script.s build/USA/src/script.i \
	build/USA/src/subtask.o build/USA/src/subtask.s build/USA/src/subtask.i \
	build/USA/src/subtask/subtaskFastTravel.o build/USA/src/subtask/subtaskFastTravel.s build/USA/src/subtask/subtaskFastTravel.i \
	build/USA/src/subtask/subtaskWorldEvent.o build/USA/src/subtask/subtaskWorldEvent.s build/USA/src/subtask/subtaskWorldEvent.i \
	build/USA/src/ui.o build/USA/src/ui.s build/USA/src/ui.i \
	build/USA/src/vram.o build/USA/src/vram.s build/USA/src/vram.i

quickstart: tools
	@rm -f $(VARIANT_OBJS)
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1

# The same game, but the player starts holding the kit that opens the gated
# overworld routes: the Blue Sword, bombs, and the Spin Attack. For walking
# a route without having to win its items first - notably North Hyrule
# Field's WNW border, the only door into Royal Valley.
quickstart-testkit: tools
	@rm -f $(VARIANT_OBJS)
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_TESTKIT=1

# The same two builds, but every run starts at difficulty 3 instead of 0 -
# for playtesting the middle of the curve without having to win up to it.
# It is a floor, not a pin: a win still moves the counter on to 4.
quickstart-d3: tools
	@rm -f $(VARIANT_OBJS)
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_START_DIFFICULTY=3

quickstart-testkit-d3: tools
	@rm -f $(VARIANT_OBJS)
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_TESTKIT=1 QUICKSTART_START_DIFFICULTY=3

# The two audio-trim playtest builds. m4a's mixer is ~40% of a North Hyrule
# Field frame, so it is the largest single lever the mode has - and every
# setting here is an audible trade, which is why they are separate builds
# rather than a change to the default. Measured numbers are in the roadmap.
#
#   audiolight  4 channels, no reverb, 13,379Hz - the moderate trade
#   audiomin    4 channels, no reverb,  7,884Hz - as far as it goes while
#               still having music and effects at all
quickstart-audiolight: tools
	@rm -f $(VARIANT_OBJS)
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_AUDIO_CHANNELS=4 QUICKSTART_AUDIO_REVERB=0 QUICKSTART_AUDIO_FREQ=4

quickstart-audiomin: tools
	@rm -f $(VARIANT_OBJS)
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_AUDIO_CHANNELS=4 QUICKSTART_AUDIO_REVERB=0 QUICKSTART_AUDIO_FREQ=2

# Dev-only: boot into South Hyrule Field, just outside Hyrule Castle Town's
# south gate, with the entire main quest done except the Vaati fight - see
# src/game.c. For manually walking the full overworld and recording
# entrance/exit/enemy-spawn coordinates.
mapexplore: tools
	@rm -f $(VARIANT_OBJS)
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 MAPEXPLORE=1

.PHONY: extract_assets
extract_assets: tools
	@$(MAKE) -f GBA.mk extract_assets

.PHONY: tools
tools: tools/bin

tools/bin:
	mkdir -p tools/cmake-build
	cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=tools -S tools -B tools/cmake-build
	cmake --build tools/cmake-build -j --target install

.PHONY: clean clean-tools
clean:
	@$(MAKE) -f GBA.mk clean

clean-tools:
	rm -rf tools/bin
	rm -rf tools/cmake-build
