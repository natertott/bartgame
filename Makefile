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

quickstart: tools
	@rm -f build/USA/src/game.o build/USA/src/game.s build/USA/src/game.i build/USA/src/gba/m4a.o build/USA/src/gba/m4a.s build/USA/src/gba/m4a.i
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1

# The same game, but the player starts holding the kit that opens the gated
# overworld routes: the Blue Sword, bombs, and the Spin Attack. For walking
# a route without having to win its items first - notably North Hyrule
# Field's WNW border, the only door into Royal Valley.
quickstart-testkit: tools
	@rm -f build/USA/src/game.o build/USA/src/game.s build/USA/src/game.i build/USA/src/gba/m4a.o build/USA/src/gba/m4a.s build/USA/src/gba/m4a.i
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_TESTKIT=1

# The same two builds, but every run starts at difficulty 3 instead of 0 -
# for playtesting the middle of the curve without having to win up to it.
# It is a floor, not a pin: a win still moves the counter on to 4.
quickstart-d3: tools
	@rm -f build/USA/src/game.o build/USA/src/game.s build/USA/src/game.i build/USA/src/gba/m4a.o build/USA/src/gba/m4a.s build/USA/src/gba/m4a.i
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_START_DIFFICULTY=3

quickstart-testkit-d3: tools
	@rm -f build/USA/src/game.o build/USA/src/game.s build/USA/src/game.i build/USA/src/gba/m4a.o build/USA/src/gba/m4a.s build/USA/src/gba/m4a.i
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
	@rm -f build/USA/src/game.o build/USA/src/game.s build/USA/src/game.i build/USA/src/gba/m4a.o build/USA/src/gba/m4a.s build/USA/src/gba/m4a.i
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_AUDIO_CHANNELS=4 QUICKSTART_AUDIO_REVERB=0 QUICKSTART_AUDIO_FREQ=4

quickstart-audiomin: tools
	@rm -f build/USA/src/game.o build/USA/src/game.s build/USA/src/game.i build/USA/src/gba/m4a.o build/USA/src/gba/m4a.s build/USA/src/gba/m4a.i
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_AUDIO_CHANNELS=4 QUICKSTART_AUDIO_REVERB=0 QUICKSTART_AUDIO_FREQ=2

# Dev-only: boot into South Hyrule Field, just outside Hyrule Castle Town's
# south gate, with the entire main quest done except the Vaati fight - see
# src/game.c. For manually walking the full overworld and recording
# entrance/exit/enemy-spawn coordinates.
mapexplore: tools
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
