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
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1

# The same game, but the player starts holding the kit that opens the gated
# overworld routes: the Blue Sword, bombs, and the Spin Attack. For walking
# a route without having to win its items first - notably North Hyrule
# Field's WNW border, the only door into Royal Valley.
quickstart-testkit: tools
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_TESTKIT=1

# The same two builds, but every run starts at difficulty 3 instead of 0 -
# for playtesting the middle of the curve without having to win up to it.
# It is a floor, not a pin: a win still moves the counter on to 4.
quickstart-d3: tools
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_START_DIFFICULTY=3

quickstart-testkit-d3: tools
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_TESTKIT=1 QUICKSTART_START_DIFFICULTY=3

# Playtest build: the same game with m4a trimmed to four direct-sound
# channels and no reverb, which measured 15% of a North Hyrule Field frame.
# Fewer simultaneous sounds and no reverb tail - build it, play it, decide.
quickstart-audiolight: tools
	@$(MAKE) GAME_VERSION=USA CUSTOM=1 QUICKSTART=1 QUICKSTART_AUDIO_CHANNELS=4 QUICKSTART_AUDIO_REVERB=0

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
