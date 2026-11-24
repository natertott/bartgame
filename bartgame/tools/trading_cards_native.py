#!/usr/bin/env python3
"""Observe the trading-card loop in mGBA with private SRAM and actual controls.

Explicit fixtures choose the title seed and position Bloom at routes, drops,
and live trade or combat approaches. Isolated regional cases request the
normal room-load path. Drop rarity coverage uses a logged PRNG fixture.
Collection, trade, damage, rewards and checkpoint outcomes come from the ROM.
"""

import argparse
import json
from pathlib import Path
import traceback

import critical_path as C
import probe as P
import release_boundary_review as boundary
from regional_save_native import Review, SHA, SRAM


CARD_COUNT = 16
PICKUP_CARD = 10
TRADE_OPEN = 3
TRADER_REQUESTS = (2, 7, 8, 12)


def loot_roll(card):
    """Find a loot roll for each identity using the game's documented thresholds."""
    mask = 0xffffffff
    for roll in range(1 << 24):
        mixed = ((roll * 0x9e3779b1) & mask) ^ (0x43415244 + 0x7f4a7c15)
        mixed = ((mixed ^ (mixed >> 15)) * 0x85ebca77) & mask
        mixed = ((mixed ^ (mixed >> 13)) * 0xc2b2ae3d) & mask
        mixed ^= mixed >> 16
        if ((mixed >> 24) * 100 >> 8) >= 30:
            continue
        rarity_draw = ((mixed >> 8) & 0xffff) % 100
        rarity = sum(rarity_draw >= threshold for threshold in (56, 81, 94))
        if rarity * 4 + (mixed & 3) == card:
            return roll
    raise AssertionError(f'No defined drop roll for card {card}')


def rarity_inks(sprites):
    """Read each rarity's dominant channel from the loaded native ramp."""
    channels = []
    shared = set.intersection(*(set(sprite['colors']) for sprite in sprites))
    for sprite in sprites:
        colors = set(sprite['colors']) - shared
        channels.append(tuple(sum((color >> shift) & 31 for color in colors) for shift in (0, 5, 10)))
    return channels


class CardReview(Review):
    def field(self, struct, field):
        return self.abi.members(struct)[field]

    def configure(self, bundle):
        super().configure(bundle)
        self.actor_fields = self.abi.members('Actor')
        self.game_fields = self.abi.members('GameState')
        self.spot_fields = self.abi.members('RegionalContentSpots')
        self.progress_fields = self.abi.members('TradingCardProgress')
        self.progress_base = P.sym('gTradingCardProgress')

    def start(self, label, sram=None, seed=None):
        self.fixtures.append(dict(kind='private cartridge start', label=label, seed=seed,
                                  sram='erased' if sram is None else SHA(sram)))
        return self.fresh(label, sram, seed)

    def load_room(self, c, area, cell, terrace=0):
        old = self.state(c)
        requests = dict(sNextArea=area, sNextCell=cell, sNextSide=2, sTransPhase=0)
        if area == 3:
            requests.update(sCreamNextNode=cell * 2 + terrace, sCreamNextFacing=0, sCreamDropRows=0)
            for name in ('sCreamNextX', 'sCreamNextY'):
                P.w16(c, boundary.static(name), 65535)
        for name, value in requests.items():
            P.w8(c, boundary.static(name), value)
        P.w8(c, P.sym('gGame') + self.game_fields['state'], 2)
        self.fixtures.append(dict(kind='ordinary room-load request', area=area,
                                  cell=cell, terrace=terrace, from_room=old))
        self.settle(c, area)

    def actor_byte(self, c, index, field, byte=0):
        return P.r8(c, P.sym('gActors') + P.ACTOR_SIZE * index + self.actor_fields[field] + byte)

    def actors(self, c, kind):
        return [dict(P.actor(c, index), index=index) for index in range(1, 96)
                if self.actor_byte(c, index, 'kind') == kind]

    def kills(self, c):
        return P.r16(c, P.sym('gGame') + self.game_fields['kills']) & 0xffff

    def progress(self, c):
        at = self.progress_base
        fields = self.progress_fields
        return dict(counts=list(self.raw(c, at + fields['counts'], CARD_COUNT)),
                    completed=P.r8(c, at + fields['completed']),
                    golden_defeated=P.r8(c, at + fields['golden_defeated']),
                    visits=list(self.raw(c, at + fields['visits'], 4)))

    def wallet(self, c):
        return P.r16(c, self.address('PlayerState', 'gilt')) & 0xffff

    def hearts(self, c):
        maximum = P.r16(c, self.address('PlayerState', 'hp_max'))
        pieces = P.r8(c, self.address('PlayerState', 'hearts_pieces'))
        return maximum // 2 + pieces

    def run_frames(self, c):
        return P.r32(c, P.sym('gGame') + self.game_fields['run_frames'])

    def forest_boss(self, c):
        return P.r8(c, self.address('World', 'goal'))

    def seen_frames(self, c, count, predicate):
        for _ in range(count):
            if predicate():
                return True
            c.run_frame()
        return predicate()

    def ordinary_attack(self, c, enemy, attempt, drop_roll=None):
        if C.gstate(c) != 1 or P.actor(c, 0)['state'] != 0:
            P.run(c, 8)
            return
        at = C.trial_attack_position(c, enemy, attempt)
        if at is None:
            P.run(c, 8)
            return
        x, y, direction = at
        self.nav(c, x, y, ('UP', 'RIGHT', 'DOWN', 'LEFT').index(direction))
        if drop_roll is None:
            P.hold(c, [direction, 'B'], 2)
            P.run(c, 20)
            return

        # The game LCG advances once before returning its high 24 bits.
        rng_addr, _ = self.abi.variable('util.c', 'sRand')
        rng_seed = (((drop_roll << 8) - 12345) * pow(1103515245, -1, 2**32)) & 0xffffffff
        self.fixtures.append(dict(kind='force candidate enemy loot roll before real attack frames',
                                  roll=drop_roll, seed=rng_seed, enemy=enemy['type']))
        keys = [P.key(c, key) for key in (direction, 'B')]
        c.set_keys(*keys)
        for frame in range(22):
            if frame == 2:
                c.clear_keys(*keys)
            self.w32(c, rng_addr, rng_seed)
            c.run_frame()
            if self.actor_byte(c, enemy['index'], 'kind') != 2:
                break
        c.clear_keys(*keys)

    def forest_kills(self, c, goal, avoid=()):
        for cell in range(25):
            if cell in avoid:
                continue
            self.load_room(c, 1, cell)
            for turn in range(100):
                if self.kills(c) >= goal:
                    return
                foes = [enemy for enemy in self.actors(c, 2) if enemy['hp'] > 0]
                if not foes or self.state(c)['actor']['state'] == 7:
                    break
                self.ordinary_attack(c, foes[turn % len(foes)], turn)
        raise AssertionError(f'Only {self.kills(c)} of {goal} planned enemy defeats occurred')

    def pickup_cards(self, c):
        return [dict(actor, card=self.actor_byte(c, actor['index'], 'v', 3))
                for actor in self.actors(c, 4) if actor['type'] == PICKUP_CARD]

    def card_sprite(self, c, pickup):
        i = pickup['index']
        a = P.sym('gActors') + P.ACTOR_SIZE * i
        tile = (P.r16(c, a + self.actor_fields['tile']) & 1023) + self.actor_byte(c, i, 'frame')
        palette = self.actor_byte(c, i, 'pal')
        packed = self.raw(c, 0x06010000 + tile * 32, 32)
        pixels = [index for pair in packed for index in (pair & 15, pair >> 4)]
        colors = [P.r16(c, 0x05000200 + 32 * palette + 2 * p) & 0x7fff
                  for p in sorted(set(pixels) - {0})]
        oam = []
        for slot in range(128):
            start = 0x07000000 + slot * 8
            attr0 = P.r16(c, start) & 0xffff
            attr2 = P.r16(c, start + 4) & 0xffff
            if attr0 & 0x0300 != 0x0200 and attr2 & 1023 == tile and attr2 >> 12 == palette:
                oam.append(slot)
        return dict(tile=tile, palette=palette, shape=''.join('1' if pixel else '0' for pixel in pixels),
                    pattern=pixels, colors=colors, oam=oam)

    def loot_card(self, c, card, roll, avoid=()):
        for cell in range(25):
            if cell in avoid:
                continue
            self.load_room(c, 1, cell)
            for turn in range(40):
                foes = [enemy for enemy in self.actors(c, 2) if enemy['hp'] > 0 and enemy['z'] == 0]
                if not foes or self.state(c)['actor']['state'] == 7:
                    break
                before = self.kills(c)
                self.ordinary_attack(c, foes[turn % len(foes)], turn, drop_roll=roll)
                if self.kills(c) == before:
                    continue
                pickup = next((item for item in self.pickup_cards(c) if item['card'] == card), None)
                if pickup is None:
                    continue
                self.check(f'an actual sword defeat drops card {card} on the ground', True, pickup)
                P.run(c, 3)
                sprite = self.card_sprite(c, pickup)
                self.check(f'card {card} appears in native sprite hardware', bool(sprite['oam']), sprite)
                self.shot(c, f'ground-card-{card:02d}')
                counts = self.progress(c)['counts']
                self.normal(c)
                self.nav(c, pickup['x'], pickup['y'])
                self.check(f'collecting card {card} adds exactly one copy',
                           self.seen_frames(c, 40, lambda: self.progress(c)['counts'][card] == counts[card] + 1),
                           self.progress(c))
                return sprite
        raise AssertionError(f'No live enemy defeat dropped card {card} under the chosen roll')

    def open_chest(self, c):
        for cell in range(25):
            if cell == self.forest_boss(c):
                continue
            self.load_room(c, 1, cell)
            w, h, tiles = C.room_tiles(c)
            kind = P.sym('metatile_type')
            chests = [(x, y) for y in range(h) for x in range(w) if tiles[x, y] < 65535
                      and P.r8(c, kind + tiles[x, y]) == 18]
            if not chests:
                continue
            self.normal(c)
            x, y = chests[0]
            before = sum(self.progress(c)['counts'])
            self.nav(c, x * 16 + 8, y * 16 + 32)
            P.hold(c, 'UP', 18)
            self.check('opening a real generated chest grants a card copy',
                       sum(self.progress(c)['counts']) == before + 1, dict(cell=cell, chest=[x, y]))
            self.shot(c, 'card-chest-reward')
            self.settle(c, 1)
            return
        raise AssertionError('No ordinary chest appeared in the generated Forest')

    def complete_quest(self, c, plan):
        self.plan_room(c, plan)
        self.approach_trader(c, region=True)
        count = sum(self.progress(c)['counts'])
        self.press(c, 'A', 2, 12)
        self.settle(c, plan['area'])
        self.check('a real generated quest giver starts the task', self.quest(c)['state'] == 2)
        fields = self.abi.members('HandoffQuest')
        base = self.address('HandoffState', 'quest')
        mode = P.r8(c, base + fields['mode'])
        self.check('the selected Scavenger task uses an accessible token or sword cache', mode in (0, 1), mode)
        for _ in range(20):
            if self.quest(c)['state'] == 3:
                break
            x = P.r16(c, base + fields['cargo_x'])
            y = P.r16(c, base + fields['cargo_y'])
            self.normal(c)
            self.nav(c, x, y + (22 if mode == 1 else 0))
            self.press(c, 'B', 2, 18) if mode == 1 else P.run(c, 8)
        self.check('actual quest completion grants one copy', self.quest(c)['state'] == 3
                   and sum(self.progress(c)['counts']) == count + 1, self.progress(c))
        self.shot(c, 'card-quest-reward')
        self.settle(c)

    def complete_event(self, c):
        world = P.sym('gCreamWorld')
        node = P.r8(c, world + self.field('CreamWorld', 'reward_node'))
        self.load_room(c, 3, node // 2, node & 1)
        info = P.sym('gCreamRoom') + self.field('CreamRoomInfo', 'terrace')
        mission = info + (node & 1) * self.abi.size('CreamTerraceSpots') + self.field('CreamTerraceSpots', 'mission')
        x, y = P.r8(c, mission), P.r8(c, mission + 1)
        self.normal(c)
        self.nav(c, x * 16 + 8, y * 16 + 22)
        self.press(c, 'A', 2, 12)
        self.settle(c, 4)
        count = sum(self.progress(c)['counts'])
        for plate in (0, 1, 2, 3, 0, 2):
            self.nav(c, (9 + plate * 4) * 16 + 8, 10 * 16 + 14)
        self.check('actual switch trial completion grants one copy',
                   sum(self.progress(c)['counts']) == count + 1, self.progress(c))
        self.shot(c, 'card-event-reward')
        self.settle(c)

    def npc(self, c, region=False):
        if not region:
            merchant = next(actor for actor in self.actors(c, 5) if actor['type'] == 1)
            return merchant['x'], merchant['y']
        a = P.sym('gRegionalSpots')
        assert P.r8(c, a + self.spot_fields['has_npc']), 'generated trader room has no NPC anchor'
        spot = a + self.spot_fields['npc']
        return P.r8(c, spot) * 16 + 8, P.r8(c, spot + 1) * 16 + 14

    def plan_room(self, c, plan):
        self.load_room(c, plan['area'], plan['cell'], plan['terrace'])

    def spot(self, c, name):
        a = P.sym('gRegionalSpots') + self.spot_fields[name]
        return P.r8(c, a) * 16 + 8, P.r8(c, a + 1) * 16 + 14

    def card_mode(self, c):
        return P.r8(c, P.sym('gCardUiMode'))

    def card_selection(self, c):
        return P.r8(c, P.sym('gCardUiSelected'))

    def approach_trader(self, c, region=False):
        self.normal(c)
        x, y = self.npc(c, region)
        self.nav(c, x, y + 17)

    def start_trade(self, c, region=False):
        self.approach_trader(c, region)
        self.press(c, 'SELECT', 2, 8)
        return self.card_mode(c) == TRADE_OPEN

    def choose_card(self, c, card):
        for _ in range(CARD_COUNT):
            selected = self.card_selection(c)
            if selected == card:
                return
            self.press(c, 'DOWN' if selected < card else 'UP', 2, 3)
            if self.card_selection(c) == selected:
                break
        raise AssertionError(f'Card {card} is missing from the visible selection')

    def open_collection(self, c):
        self.press(c, 'START', 2, 18)
        self.press(c, 'R', 2, 8)
        self.press(c, 'A', 2, 8)
        return self.card_mode(c) == 1

    def close_collection(self, c):
        self.press(c, 'B', 2, 8)
        self.press(c, 'START', 2, 14)
        self.settle(c)

    def trader_state(self, c):
        a, dwarf_type = self.abi.variable('card_traders.c', 'sTrader')
        fields = self.abi.members(dwarf_type)
        return {key: P.r8(c, a + fields[key]) for key in ('active', 'trader', 'bubble', 'offering')}

    def bubble(self, c):
        self.load_room(c, 0, 0)
        x, y = self.npc(c)
        self.normal(c)
        self.nav(c, x, y + 86)
        P.run(c, 18)
        self.check('the distant Peddler has no thought bubble', self.trader_state(c)['bubble'] == 0)
        self.nav(c, x, y + 17)
        opening = self.trader_state(c)['bubble']
        P.run(c, 15)
        open_ = self.trader_state(c)['bubble']
        self.shot(c, 'peddler-thought-bubble')
        self.check('approaching the Peddler grows the actual thought bubble', 0 < opening < open_,
                   dict(approach=opening, rendered_open=open_))
        self.nav(c, x, y + 86)
        closing = self.trader_state(c)['bubble']
        P.run(c, 15)
        self.check('the same bubble closes as Bloom leaves', 0 < closing < open_
                   and self.trader_state(c)['bubble'] == 0, dict(closing=closing))

    def verify_collection(self, c):
        self.check('the Start menu reaches the card collection', self.open_collection(c))
        self.shot(c, 'collection')
        captures = []
        for card in TRADER_REQUESTS:
            self.choose_card(c, card)
            self.press(c, 'A', 2, 10)
            self.check(f'card {card} opens full illustrated inspection',
                       self.card_mode(c) == 2 and self.card_selection(c) == card
                       and self.progress(c)['counts'][card] > 0)
            self.shot(c, f'collection-inspect-{card:02d}')
            pixels = c.bg_video.to_pil().convert('RGB').crop((32, 48, 80, 96)).tobytes()
            captures.append(SHA(pixels))
            self.press(c, 'B', 2, 10)
        self.check('the four inspected cards show distinct native illustrations', len(set(captures)) == 4, captures)
        self.close_collection(c)

    def offer(self, c, trader, reject=None):
        requested = TRADER_REQUESTS[trader]
        before = self.progress(c)
        self.check(f'trader {trader} opens a live portrait trade request',
                   self.start_trade(c, trader != 0) and P.r8(c, P.sym('gCardUiRequest')) == requested)
        self.shot(c, f'trader-{trader}-request')
        if reject is not None:
            self.choose_card(c, reject)
            self.press(c, 'A', 2, 12)
            self.check('the incorrect card gets rejected and every copy remains available',
                       self.card_mode(c) == TRADE_OPEN and P.r8(c, P.sym('gCardUiRefusals')) == 1
                       and self.progress(c) == before)
            self.shot(c, 'peddler-wrong-offer')
        self.choose_card(c, requested)
        self.press(c, 'A', 2, 10)
        after = self.progress(c)
        expected = before['counts'].copy()
        expected[requested] -= 1
        self.check(f'trader {trader} consumes exactly one matching copy',
                   self.card_mode(c) == 0 and after['counts'] == expected
                   and after['completed'] == (before['completed'] | (1 << trader)), after)
        self.settle(c)
        self.check(f'trader {trader} cannot pay twice', not self.start_trade(c, trader != 0))

    def golden(self, c, red):
        def marked():
            return [enemy for enemy in self.actors(c, 2)
                    if self.actor_byte(c, enemy['index'], 'v', 5) == 4]

        self.check('the matching red trade releases exactly one marked golden foe',
                   self.seen_frames(c, 40, lambda: len(marked()) == 1), self.progress(c))
        self.load_room(c, 0, 0)
        self.plan_room(c, red)
        self.check('an unfinished golden encounter returns after changing rooms',
                   self.seen_frames(c, 40, lambda: len(marked()) == 1), marked())
        original = marked()[0]
        self.check('the golden foe has 64 actual HP', original['hp'] == 64, original)
        wallet, heart_units = self.wallet(c), self.hearts(c)
        speeds = set()
        photographed = False
        for turn in range(350):
            enemies = marked()
            if not enemies or self.state(c)['actor']['state'] == 7:
                break
            enemy = enemies[0]
            speeds.add(enemy['speed'])
            sx = enemy['x'] - P.r16(c, P.sym('gCamX'))
            sy = enemy['y'] - P.r16(c, P.sym('gCamY'))
            if not photographed and 16 <= sx <= 224 and 44 <= sy <= 156:
                if not self.actor_byte(c, enemy['index'], 'iframes'):
                    self.shot(c, 'golden-encounter')
                    photographed = True
            self.ordinary_attack(c, enemy, turn)
        self.check('the marked golden encounter is visible on the native battlefield', photographed)
        self.check('the golden foe uses high native movement speed', max(speeds, default=0) >= 320,
                   dict(speed_q8_8=sorted(speeds)))
        self.check('real sword combat defeats the golden foe and gives 200 gilt and one Heart Piece',
                   not marked() and self.progress(c)['golden_defeated'] & 8
                   and self.wallet(c) == min(999, wallet + 200) and self.hearts(c) == heart_units + 1,
                   dict(wallet_before=wallet, wallet_after=self.wallet(c), heart_units_before=heart_units,
                        heart_units_after=self.hearts(c), foes=marked(), progress=self.progress(c)))
        self.shot(c, 'golden-rewards')
        self.settle(c)
        self.load_room(c, 0, 0)
        self.plan_room(c, red)
        P.run(c, 45)
        self.check('a defeated golden encounter never respawns on revisit', not marked())

    def run_cards(self):
        c = self.start('card-run', seed=self.args.seed)
        self.check('new run starts with no cards', not any(self.progress(c)['counts']))
        plans = self.plans(c)
        green, blue, red = [next(p for p in plans if p['fusion_color'] == color) for color in range(3)]
        self.plan_room(c, green)
        self.check('the Moss Archivist refuses a visit before four defeats',
                   self.kills(c) < 4 and not self.start_trade(c, True))
        self.plan_room(c, red)
        self.check('the Rind Collector refuses a visit before fifteen defeats',
                   self.kills(c) < 15 and not self.start_trade(c, True))
        self.plan_room(c, blue)
        self.check('the Brook Locksmith refuses a first visit',
                   self.progress(c)['visits'][2] == 1 and not self.start_trade(c, True))
        self.plan_room(c, green)
        self.plan_room(c, blue)
        self.check('the Brook Locksmith is on its second visit', self.progress(c)['visits'][2] == 2)
        self.approach_trader(c, True)
        self.check('the real clock reaches the Brook Locksmith rest window',
                   self.seen_frames(c, 600, lambda: 372 <= self.run_frames(c) % 480 <= 466))
        self.check('the Brook Locksmith closes during the rest window', not self.start_trade(c, True))
        self.check('the real clock reaches the Brook Locksmith open window',
                   self.seen_frames(c, 180, lambda: 15 <= self.run_frames(c) % 480 <= 250))
        self.check('the Brook Locksmith reopens without another visit', self.start_trade(c, True))
        self.press(c, 'B', 2, 10)

        self.open_chest(c)
        scavenger = next((p for p in plans if p['quest_kind'] == 3), None)
        if scavenger:
            self.complete_quest(c, scavenger)
        self.complete_event(c)
        avoid = {self.forest_boss(c), green['cell'], blue['cell']}
        sprites = [self.loot_card(c, card, loot_roll(card), avoid) for card in TRADER_REQUESTS]
        green_ink, blue_ink, cobalt_ink, gold_ink = rarity_inks(sprites)
        self.check('green, two distinct blue shades, and gold share the same native icon silhouette',
                   len({sprite['shape'] for sprite in sprites}) == 1
                   and len({tuple(sprite['colors']) for sprite in sprites}) == 4
                   and len({sprite['palette'] for sprite in sprites}) == 1
                   and green_ink[1] > max(green_ink[0], green_ink[2])
                   and all(ink[2] > max(ink[0], ink[1]) for ink in (blue_ink, cobalt_ink))
                   and gold_ink[0] > gold_ink[1] > gold_ink[2], sprites)

        self.bubble(c)
        self.verify_collection(c)
        boomerang_address = self.address('LegacyInventory', 'owned') + 1
        already_owned = bool(P.r8(c, boomerang_address) & 8)
        wallet = self.wallet(c)
        self.offer(c, 0, reject=TRADER_REQUESTS[1])
        self.check('the Peddler gives a Boomerang or its duplicate compensation',
                   bool(P.r8(c, boomerang_address) & 8) and
                   (not already_owned or self.wallet(c) == min(999, wallet + 100)))
        self.forest_kills(c, 15, avoid)
        self.plan_room(c, green)
        before = self.wallet(c)
        self.nav(c, *self.spot(c, 'cache'))
        self.press(c, 'A', 2, 12)
        self.settle(c)
        self.check('the Moss Archivist cache stays sealed before trading', self.wallet(c) == before)
        self.offer(c, 1)
        self.check('the Moss Archivist pays 100 actual gilt', self.wallet(c) == min(999, before + 100))
        before = self.wallet(c)
        self.nav(c, *self.spot(c, 'cache'))
        self.press(c, 'A', 2, 12)
        self.settle(c)
        self.check('the matched green trade opens the real nearby cache', self.wallet(c) == min(999, before + 100))
        self.plan_room(c, blue)
        self.nav(c, *self.spot(c, 'door'))
        self.press(c, 'A', 2, 12)
        self.settle(c)
        self.check('the regional pocket entrance stays locked before trading', C.area(c) == blue['area'])
        self.offer(c, 2)
        self.nav(c, *self.spot(c, 'door'))
        self.press(c, 'A', 2, 15)
        self.settle(c, 4)
        self.check('the matched blue trade opens a real regional pocket entrance', C.area(c) == 4)
        self.plan_room(c, red)
        self.offer(c, 3)
        self.golden(c, red)

        self.load_room(c, 0, 0)
        before_save = self.progress(c)
        saved = self.trophy_save(c)
        cold = self.start('cold-card-continue', saved)
        continued = self.progress(cold)
        self.check('cold Continue preserves card copies, trades and golden completion from actual SRAM',
                   continued['counts'] == before_save['counts'] and continued['completed'] == 15
                   and continued['golden_defeated'] == 8, dict(saved=before_save, loaded=continued))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=lambda value: int(value, 0), default=0xb4a7)
    args = parser.parse_args()
    review = CardReview(args)
    error = None
    try:
        review.configure(args.bundle)
        review.run_cards()
    except Exception:
        error = traceback.format_exc()
        raise
    finally:
        report = dict(source_commit=(args.bundle/'source-commit.txt').read_text().strip(),
                      rom_sha256=SHA((args.bundle/'bartgame.gba').read_bytes()), seed=args.seed,
                      checks=review.rows, fixtures=review.fixtures, frames=review.media,
                      complete=error is None and all(row['passed'] for row in review.rows), error=error)
        (review.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
