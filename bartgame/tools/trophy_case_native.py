#!/usr/bin/env python3
"""Play the Drain and Trophy Case in mGBA and capture untouched native frames.

The hub approaches, interactions, catalogue controls, rewards and settings
use ordinary game inputs. A private cartridge and seed make the run repeatable.
The shared card probe shortens travel and selects a loot roll for a real enemy
defeat. A second core boots with the cartridge-produced SRAM to test retention.
"""

import argparse
import json
from pathlib import Path
import re
import traceback

import critical_path as C
import probe as P
from trading_cards_native import CardReview, SHA, SRAM, loot_roll


PLAY, CASE = 1, 7
DRAIN, FOREST, CREAM = 0, 1, 3
MILESTONES, ITEMS, CREATURES, CARDS = range(4)
BLIGHTSEEDS, PEDDLER_EXCHANGE = 2, 4


class TrophyReview(CardReview):
    def configure(self, bundle):
        super().configure(bundle)
        self.shop, _ = self.abi.variable('text.c', 'sShopActive')
        self.has_checkpoint, _ = self.abi.variable('game.c', 'sTitleHasSave')
        header = (self.bundle / 'assets.h').read_text()
        menu = int(re.search(r'^#define PAL_SLOT_MENU (\d+)$', header, re.M)[1])
        self.case_palette_banks = (8, 9, menu)

    def value(self, c, name):
        return P.r8(c, P.sym(name))

    def catalogue(self, c):
        keys = ('Page', 'Cursor', 'Top', 'Detail', 'Seen', 'Entry', 'Count', 'Filter',
                'PreviewSheet', 'PreviewFrame', 'PreviewSourcePalette')
        result = {key: self.value(c, 'gArcade' + key) for key in keys}
        result['PreviewTiles'] = P.r16(c, P.sym('gArcadePreviewTiles'))
        return result

    def in_field(self, c):
        return (C.gstate(c) == PLAY and C.area(c) == DRAIN and not self.mode(c)
                and not self.value(c, 'gTbActive') and not P.r8(c, self.shop))

    def walk(self, c, x, y):
        for _ in range(1000):
            if not self.in_field(c):
                break
            px, py = P.player_pos(c)
            if abs(px - x) <= 1 and abs(py - y) <= 1:
                return
            if abs(px - x) > 1:
                delta = x - px
                key = 'RIGHT' if delta > 0 else 'LEFT'
            else:
                delta = y - py
                key = 'DOWN' if delta > 0 else 'UP'
            P.hold(c, key, min(8, max(1, int((abs(delta) - 1) / 1.25))))
            if P.player_pos(c) == (px, py):
                break
        raise AssertionError(('could not reach Drain point by walking', (x, y), self.state(c)))

    def front(self, c, x, y):
        px, py = P.player_pos(c)
        bank = 142 if py < 200 else 270
        destination = 142 if y < 200 else 270
        self.walk(c, px, bank)
        if bank != destination:
            self.walk(c, 248, bank)
            self.walk(c, 248, destination)
        self.walk(c, x, destination)
        self.walk(c, x, y + 2)
        self.press(c, 'UP', 1, 3)

    def cabinet_front(self, c):
        self.front(c, P.r16(c, P.sym('gCabinetX')), P.r16(c, P.sym('gCabinetY')) + 20)

    def open_case(self, c):
        self.cabinet_front(c)
        self.press(c, 'A', 2, 12)
        self.check('real walk and A open the single physical Trophy Case', C.gstate(c) == CASE,
                   self.state(c))

    def select_page(self, c, page):
        for _ in range(4):
            if self.catalogue(c)['Page'] == page:
                return
            self.press(c, 'R', 2, 5)
        raise AssertionError(('could not reach catalogue page', page, self.catalogue(c)))

    def set_filter(self, c, found_only):
        if bool(self.catalogue(c)['Filter']) != found_only:
            self.press(c, 'SELECT', 2, 8)

    def select_entry(self, c, entry):
        self.set_filter(c, False)
        for _ in range(100):
            selected = self.catalogue(c)['Entry']
            if selected == entry:
                return
            self.press(c, 'DOWN' if selected < entry else 'UP', 2, 4)
            if self.catalogue(c)['Entry'] == selected:
                break
        raise AssertionError(('could not select catalogue entry', entry, self.catalogue(c)))

    def screen_setup(self, c):
        return dict(display=P.r16(c, 0x04000000), bg1=P.r16(c, 0x0400000a),
                    bg3=P.r16(c, 0x0400000e), music_hook=P.r32(c, P.sym('gVBlankHook')),
                    palettes=[self.raw(c, 0x05000000 + bank * 32, 32).hex()
                              for bank in self.case_palette_banks])

    def browse(self, c):
        self.cabinet_front(c)
        self.shot(c, '01-drain-trophy-case')
        display = self.screen_setup(c)
        discoveries = P.r16(c, P.sym('gJournalRevision'))
        self.open_case(c)
        position = P.player_pos(c)
        view = self.catalogue(c)
        self.check('the case opens on a populated All Milestones page',
                   view['Page'] == MILESTONES and view['Count'] > PEDDLER_EXCHANGE
                   and not view['Filter'] and not view['Detail'], view)
        frames = self.run_frames(c)
        video = P.r32(c, P.sym('gFrame'))
        P.run(c, 60)
        self.check('the case pauses the expedition clock while native video keeps updating',
                   self.run_frames(c) == frames and P.r32(c, P.sym('gFrame')) == video + 60)
        self.shot(c, '02-milestones-index')
        self.select_entry(c, PEDDLER_EXCHANGE)
        locked = self.catalogue(c)
        self.check('a new run leaves the Peddler exchange milestone locked',
                   not locked['Seen'] and not locked['PreviewTiles'], locked)
        self.press(c, 'L', 2, 8)
        self.check('L wraps from Milestones to Cards', self.catalogue(c)['Page'] == CARDS)
        self.press(c, 'R', 2, 8)
        self.check('R wraps from Cards to Milestones', self.catalogue(c)['Page'] == MILESTONES)
        self.press(c, 'R', 2, 8)
        start = self.catalogue(c)
        self.check('R opens Items with a full collection index',
                   start['Page'] == ITEMS and start['Count'] > 10 and start['Cursor'] == 0, start)
        self.press(c, 'DOWN', 2, 8)
        self.check('Down advances the index by one row', self.catalogue(c)['Cursor'] == 1)
        self.press(c, 'RIGHT', 2, 8)
        right = self.catalogue(c)
        self.check('Right skips five rows and scrolls the list', right['Cursor'] == 6 and right['Top'] > 0, right)
        self.press(c, 'LEFT', 2, 8)
        self.check('Left skips five rows back', self.catalogue(c)['Cursor'] == 1)
        self.press(c, 'UP', 2, 8)
        self.check('Up goes to the preceding row', self.catalogue(c)['Cursor'] == 0)
        self.set_filter(c, True)
        found = self.catalogue(c)
        self.check('Select narrows Items to genuinely discovered rows',
                   found['Filter'] and found['Seen'] and 1 < found['Count'] < start['Count'], found)
        self.shot(c, '03-items-found-only')
        self.press(c, 'A', 2, 8)
        item = self.catalogue(c)
        self.check('A inspects the selected item with its own native art',
                   item['Detail'] and item['Entry'] == found['Entry'] and item['PreviewTiles'] == 56,
                   item)
        self.shot(c, '04-item-inspection')
        self.press(c, 'RIGHT', 2, 8)
        right = self.catalogue(c)
        self.check('Right browses the next discovered entry in inspection',
                   right['Detail'] and right['Seen'] and right['Entry'] != item['Entry'], right)
        self.press(c, 'LEFT', 2, 8)
        self.press(c, 'B', 2, 8)
        back = self.catalogue(c)
        self.check('Left and B return to the original index selection',
                   not back['Detail'] and back['Entry'] == item['Entry'], back)
        self.select_page(c, CARDS)
        empty = self.catalogue(c)
        self.check('Found Only carries to Cards and handles an empty album',
                   empty['Filter'] and empty['Count'] == 0 and empty['Entry'] == 255
                   and not empty['PreviewTiles'], empty)
        self.press(c, 'A', 2, 8)
        self.check('A on an empty album stays safely at the index', not self.catalogue(c)['Detail'])
        self.set_filter(c, False)
        unknown = self.catalogue(c)
        self.check('All shows the 16 undiscovered cards without revealing artwork',
                   unknown['Count'] == 16 and not unknown['Seen'] and not unknown['PreviewTiles'], unknown)
        self.press(c, 'A', 2, 8)
        unknown = self.catalogue(c)
        self.check('inspecting an undiscovered card keeps its artwork concealed',
                   unknown['Detail'] and not unknown['Seen'] and unknown['PreviewFrame'] == 255, unknown)
        self.press(c, 'B', 2, 8)
        self.press(c, 'B', 2, 12)
        after = self.screen_setup(c)
        self.check('B restores Drain position, display registers, palettes and audio callback',
                   self.in_field(c) and P.player_pos(c) == position and display == after,
                   dict(before=display, after=after, position_before=position, position_after=P.player_pos(c)))
        self.check('browsing changes no item or creature discoveries',
                   P.r16(c, P.sym('gJournalRevision')) == discoveries)

    def hub(self, c):
        actors = self.actors(c, 5)
        self.check('The Drain retains exactly its Wizard and Billious Peddler actors',
                   sorted(actor['type'] for actor in actors) == [0, 1], actors)
        for actor in actors:
            self.front(c, actor['x'], actor['y'] + 23)
            self.press(c, 'A', 2, 10)
            if actor['type'] == 0:
                self.check('walking to the Wizard and pressing A opens his genuine dialogue',
                           bool(self.value(c, 'gTbActive')) and not self.mode(c), self.state(c))
                self.shot(c, '05-drain-wizard')
            else:
                self.check('walking to the Peddler and pressing A opens his regular shop',
                           bool(P.r8(c, self.shop)) and not self.mode(c), self.state(c))
                self.shot(c, '06-billious-peddler-shop')
                self.press(c, 'B', 2, 12)
            self.settle(c, DRAIN)

        old_fronts = (('second shop', 120, 126), ('fusion broker', 152, 254),
                      ('contract guide', 304, 254), ('beds', 352, 254),
                      ('bed chest', 384, 254), ('trophy cup', 416, 254))
        for name, x, y in old_fronts:
            self.front(c, x, y)
            self.press(c, 'A', 2, 16)
            self.press(c, 'R', 2, 16)
            self.check(f'former {name} approach has no field interaction', self.in_field(c), self.state(c))
        self.shot(c, '07-cleared-drain-bank')

    def ladder(self, c, x, y, area):
        self.front(c, x, y)
        key = P.key(c, 'UP')
        c.set_keys(key)
        try:
            reached = self.seen_frames(c, 300, lambda: C.area(c) == area)
        finally:
            c.clear_keys(key)
        self.check(f'walking up the real {"Cream" if area == CREAM else "Forest"} ladder loads its region',
                   reached, self.state(c))
        self.settle(c, area)

    def acquire(self, c):
        self.ladder(c, 152, 94, FOREST)
        self.loot_card(c, BLIGHTSEEDS, loot_roll(BLIGHTSEEDS), {self.forest_boss(c)})
        self.load_room(c, DRAIN, 0)
        self.offer(c, 0)
        self.check('the only owned Blightseeds card was spent at the retained Peddler',
                   self.progress(c)['counts'][BLIGHTSEEDS] == 0, self.progress(c))

    def earned(self, c, online):
        self.open_case(c)
        self.select_page(c, MILESTONES)
        self.select_entry(c, PEDDLER_EXCHANGE)
        milestone = self.catalogue(c)
        prefix = 'The active run' if online else 'A cold New Game'
        self.check(prefix + ' shows the earned Peddler exchange milestone',
                   milestone['Seen'] and milestone['PreviewTiles'] == 56, milestone)
        self.press(c, 'A', 2, 8)
        self.check(prefix + ' can inspect the earned milestone', self.catalogue(c)['Detail'] == 1)
        if online:
            self.shot(c, '08-earned-milestone-inspection')
        self.press(c, 'B', 2, 8)
        self.select_page(c, CARDS)
        self.set_filter(c, True)
        card = self.catalogue(c)
        self.check(prefix + ' records the spent card in Found Only with its true artwork',
                   card['Count'] == 1 and card['Entry'] == BLIGHTSEEDS and card['Seen']
                   and card['PreviewTiles'] == 56 and card['PreviewFrame'] == BLIGHTSEEDS, card)
        self.press(c, 'A', 2, 8)
        self.check(prefix + ' inspects the discovered card with no live copy',
                   self.catalogue(c)['Detail'] == 1 and self.progress(c)['counts'][BLIGHTSEEDS] == 0)
        if online:
            self.shot(c, '09-discovered-card-inspection')
        self.press(c, 'B', 2, 8)
        if online:
            self.select_page(c, CREATURES)
            enemy = self.catalogue(c)
            self.check('a real encounter supplies a creature entry and artwork',
                       enemy['Seen'] and enemy['Count'] > 0 and enemy['PreviewTiles'] == 56, enemy)
            self.press(c, 'A', 2, 8)
            self.shot(c, '10-creature-inspection')
            self.press(c, 'B', 2, 8)
        self.press(c, 'B', 2, 12)

    def run_options(self, c):
        self.open_case(c)
        self.select_page(c, ITEMS)
        self.press(c, 'DOWN', 2, 8)
        selected = self.catalogue(c)
        self.press(c, 'START', 2, 12)
        self.check('case Start opens the new physical Run Options route', self.mode(c) == 10, self.state(c))
        self.press(c, 'DOWN', 2, 8)
        self.press(c, 'A', 2, 12)
        self.check('the second row reaches the native difficulty picker', self.mode(c) == 9, self.state(c))
        self.press(c, 'B', 2, 12)
        self.check('B from difficulty returns to Run Options', self.mode(c) == 10, self.state(c))
        self.press(c, 'B', 2, 12)
        self.check('B from Run Options restores the same Trophy Case page, filter and selection',
                   C.gstate(c) == CASE and self.catalogue(c) == selected, self.catalogue(c))
        self.press(c, 'START', 2, 12)
        self.press(c, 'DOWN', 2, 8)
        self.press(c, 'A', 2, 12)
        self.press(c, 'DOWN', 2, 8)
        self.press(c, 'DOWN', 2, 8)
        self.press(c, 'A', 2, 12)
        self.settle(c, DRAIN)
        difficulty = self.address('HandoffState', 'difficulty')
        self.check('actual settings input changes run difficulty to 2', P.r8(c, difficulty) == 2)
        sram = self.raw(c, SRAM, 32768)
        continued = self.start('cold-difficulty-continue', sram)
        self.check('a cold Continue retains the difficulty chosen from the case',
                   P.r8(continued, difficulty) == 2 and not self.value(continued, 'gStartingDraft'),
                   self.state(continued))

    def run_case(self):
        c = self.start('live-trophy-case', seed=self.args.seed)
        self.browse(c)
        self.hub(c)
        self.acquire(c)
        self.earned(c, online=True)
        saved = self.raw(c, SRAM, 32768)
        cold = self.fresh('cold-new-game', saved, start=False)
        self.fixtures.append(dict(kind='cold private cartridge with actual profile SRAM', sha256=SHA(saved)))
        if P.r8(cold, self.has_checkpoint):
            self.press(cold, 'DOWN', 2, 8)
        new_seed = self.args.seed + 1
        self.w32(cold, P.sym('gSeedOverride'), new_seed)
        self.fixtures.append(dict(kind='title run seed', seed=new_seed))
        self.press(cold, 'START', 2, 8)
        self.settle(cold, DRAIN)
        self.check('the cold title starts a genuinely different new run',
                   P.r32(cold, P.sym('gGame') + self.game_fields['seed']) == new_seed
                   and not self.progress(cold)['completed'], self.progress(cold))
        self.earned(cold, online=False)
        self.run_options(cold)

        cream = self.start('cream-ladder', seed=self.args.seed)
        self.ladder(cream, 312, 94, CREAM)
        self.press(cream, 'A', 2, 10)
        self.settle(cream, DRAIN)
        self.check('the Cream entry stairs return to a stable Drain approach',
                   P.player_pos(cream) == (312, 94), self.state(cream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=lambda value: int(value, 0), default=0xb4a7)
    args = parser.parse_args()
    review = TrophyReview(args)
    error = None
    try:
        review.configure(args.bundle)
        review.run_case()
    except Exception:
        error = traceback.format_exc()
        raise
    finally:
        report = dict(source_commit=(args.bundle / 'source-commit.txt').read_text().strip(),
                      rom_sha256=SHA((args.bundle / 'bartgame.gba').read_bytes()), seed=args.seed,
                      tool_sha256=SHA(Path(__file__).read_bytes()), emulator='mGBA 0.10.5',
                      checks=review.rows, fixtures=review.fixtures, frames=review.media,
                      complete=error is None and all(row['passed'] for row in review.rows), error=error)
        (review.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
