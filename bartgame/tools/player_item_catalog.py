#!/usr/bin/env python3
"""Generate the audited player-item report from stable current item metadata.

Acquisition annotations below are a source audit, not a runtime collection
claim. Update them when award paths change; a grant API alone is not a path.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/items"
STRING = r'"(?:\\.|[^"\\])*"'


def read(name):
    return (ROOT / name).read_text()


def line(name, needle):
    for n, text in enumerate(read(name).splitlines(), 1):
        if needle in text:
            return n
    raise ValueError((name, needle))


def ref(name, needle, label=None):
    return f'[{label or name}](../../{name}#L{line(name, needle)})'


def enums(text, start):
    block = text.split(start, 1)[1].split('};', 1)[0]
    block = re.sub(r'/\*.*?\*/', '', block, flags=re.S)
    values, previous = {}, -1
    for entry in block.split(','):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split('=', 1)
        name = parts[0].strip()
        if not re.fullmatch(r'[A-Z][A-Z0-9_]+', name):
            raise ValueError(entry)
        if len(parts) == 1:
            value = previous + 1
        else:
            tokens = parts[1].strip().split('+')
            value = sum(values[t.strip()] if t.strip() in values else int(t.strip(), 0) for t in tokens)
        values[name] = previous = value
    return values


# These routes were traced outside the shared reward pool, including .inc files.
DIRECT = {
    'LI_SMITH_SWORD': ('Starting equipment; synchronized from the original Sword flag.', 'src/player.c', 'void player_new_game'),
    'LI_SHIELD': ('Starting equipment; synchronized from the original Bark Shield flag.', 'src/player.c', 'void player_new_game'),
    'LI_BOTTLE2': ('Further Glass Bottle awards add the second vessel.', 'src/legacy_items.c', 'if(item==LI_BOTTLE1&&previously_owned)'),
    'LI_BOTTLE3': ('Further Glass Bottle awards add the third vessel.', 'src/legacy_items.c', 'if(item==LI_BOTTLE1&&previously_owned)'),
    'LI_BOTTLE4': ('Further Glass Bottle awards add the fourth vessel.', 'src/legacy_items.c', 'if(item==LI_BOTTLE1&&previously_owned)'),
    'LI_BOTTLE_WATER': ('Fill an empty equipped vessel beside water or shallow water; content state, not a separate grant.', 'src/legacy_items.c', 'gLegacyInventory.bottles[slot]=LI_BOTTLE_WATER'),
    'LI_BOTTLE_HALF_MILK': ('Drink the first half of Bottle Milk; remaining content state, not a separate grant.', 'src/legacy_items.c', 'gLegacyInventory.bottles[slot]=content==LI_BOTTLE_MILK'),
    'LI_EARTH_ELEMENT': ('Collect the materialized final Four-Seal contract reward.', 'src/handoff_events.c', 'legacy_item_spawn(LI_EARTH_ELEMENT'),
    'LI_FIRE_ELEMENT': ('First completed step of the optional Four-Seal contract.', 'src/handoff_events.c', 'if(step<3){give(LI_FIRE_ELEMENT+step)'),
    'LI_WATER_ELEMENT': ('Second completed step of the optional Four-Seal contract.', 'src/handoff_events.c', 'if(step<3){give(LI_FIRE_ELEMENT+step)'),
    'LI_WIND_ELEMENT': ('Third completed step of the optional Four-Seal contract.', 'src/handoff_events.c', 'if(step<3){give(LI_FIRE_ELEMENT+step)'),
    'LI_BIG_KEY': ('Physical pickup in a generated regional mechanism interior, pattern1.', 'src/handoff_objects.c', 'sObj.pattern==1&&'),
    'LI_RUPEE20': ('Regional mechanism/mobility reward; also a draft fallback.', 'src/handoff_mobility.c', 'legacy_item_grant(LI_RUPEE20'),
    'LI_BOMBS5': ('Fixed stock in the extended Drain exchange:25 gilt.', 'src/handoff_events.c', 'gHandoffState.stock[1]=LI_BOMBS5'),
    'LI_ARROWS10': ('Fixed stock in the extended Drain exchange:25 gilt.', 'src/handoff_events.c', 'gHandoffState.stock[2]=LI_ARROWS10'),
    'LI_ARROWS5': ('Emergency refill in regional mechanism interior pattern10 when bow-owned and out of arrows.', 'src/handoff_objects.c', 'sObj.pattern==10&&'),
    'LI_FAIRY': ('Fairy-well interior pickups or defeated Spark enemies; catchable in a bottle.', 'src/legacy_enemies.c', 'if(f==LF_SPARK) legacy_item_spawn(LI_FAIRY'),
    'LI_KINSTONE': ('Colored/shaped enemy drops collected into counters; discovery is recorded without necessarily setting the legacy owned bit.', 'src/handoff_events.c', 'gHandoffState.kinstone_shapes[c][a]=MIN'),
    'LI_KINSTONE_BAG': ('Reward for a successful green-fuser match.', 'src/handoff_events.c', 'give(index==0?LI_KINSTONE_BAG'),
}

EXTRA = {
    'LI_BOMBS': 'Also the Forest seed trial and Cream trial1.',
    'LI_LANTERN_OFF': 'Also the Forest flame trial and Cream trial2.',
    'LI_ROCS_CAPE': 'Also the Forest petal trial and Cream trial3.',
    'LI_PACCI_CANE': 'Also Cream trial3, together with the cloak.',
    'LI_GRIP_RING': 'Also granted on first Cream entry.',
    'LI_BOW': 'Also Forest bow chests and Cream chests.',
    'LI_MAP': 'Also original Forest map chests.',
    'LI_POWER_BRACELETS': 'Also original Root Gauntlet chests and Cream chests.',
    'LI_BOOMERANG': 'Also Cream chests.',
    'LI_GUST_JAR': 'Also Cream chests.',
    'LI_MOLE_MITTS': 'Also Cream chests.',
    'LI_PEGASUS_BOOTS': 'Also Cream chests.',
    'LI_FLIPPERS': 'Also Cream chests.',
    'LI_HEART_PIECE': 'Also original heart-piece rewards, quests and Cream chests.',
    'LI_HEART_CONTAINER': 'Also original Forest chest/quest rewards.',
    'LI_COMPASS': 'Same map-marker effect as the original Astrolabe, which also has Forest chests.',
}

PREREQ = {
    'LI_REMOTE_BOMBS': 'Bombs owned.',
    'LI_LIGHT_ARROW': 'Thorn Bow owned.',
    'LI_ARROW_BUTTERFLY': 'Thorn Bow owned.',
    'LI_MAGIC_BOOMERANG': 'Boomerang owned.',
    'LI_BLUE_SWORD': 'Red Sword owned.',
    'LI_FOURSWORD': 'Blue Sword owned for the random pool; also a Four-Seal completion reward.',
    'LI_GREEN_SWORD': 'Sword Beam learned; its run blessing has not already been taken.',
    'LI_BOMBBAG': 'Bombs owned and bag below upgrade3.',
    'LI_LARGE_QUIVER': 'Thorn Bow owned and quiver below upgrade3.',
    'LI_DIG_BUTTERFLY': 'Mole Mitts owned.',
    'LI_SWIM_BUTTERFLY': 'Flippers owned.',
    'LI_SKILL_DOWN_THRUST': 'Petal Cloak owned.',
    'LI_SKILL_GREAT_SPIN': 'Spin Attack learned.',
    'LI_SKILL_FAST_SPIN': 'Spin Attack learned.',
    'LI_SKILL_FAST_SPLIT': 'Spin Attack learned for reward eligibility; Fourfold Sword is needed to use splitting.',
    'LI_SKILL_LONG_SPIN': 'Actual reward eligibility checks Spin Attack, although its description says Great Spin.',
}

NO_ROUTE = {
    'LI_BOTTLE_EMPTY': 'An empty vessel is obtainable through Glass Bottle; this distinct legacy award ID is not used.',
    'LI_SHELLS': 'Its3-second protective effect is implemented, but no current award source was found.',
    'LI_DUNGEON_MAP': 'Map of the Wood supplies the same effect; this separate legacy ID is not awarded.',
    'LI_SMALL_KEY': 'Original Small Key pickups/chests are available; this separate legacy ID is not awarded.',
    'LI_RUPEE1': 'Original Gilt provides1gilt; this separate legacy ID is not awarded.',
    'LI_RUPEE5': 'No5-gilt award route for this ID was found.',
    'LI_HEART': 'Original loose Heart pickups provide the effect; this separate legacy ID is not awarded.',
    'LI_BOMBS10': 'No10-seed legacy refill source was found.',
    'LI_BOMBS30': 'No30-seed legacy refill source was found.',
    'LI_ARROWS30': 'No30-arrow legacy refill source was found.',
}

ALIASES = {
    'LI_SMITH_SWORD': 'JI_SWORD', 'LI_SHIELD': 'JI_SHIELD',
    'LI_MIRROR_SHIELD': 'JI_SHIELD_UPGRADED (shared appearance; additionally reflects beams)',
    'LI_BOMBS': 'JI_BOMBS', 'LI_LANTERN_OFF': 'JI_LAMP',
    'LI_ROCS_CAPE': 'JI_CLOAK', 'LI_POWER_BRACELETS': 'JI_GAUNTLET',
    'LI_BOW': 'JI_BOW', 'LI_MAP': 'JI_MAP', 'LI_DUNGEON_MAP': 'JI_MAP / LI_MAP effect',
    'LI_COMPASS': 'JI_ASTROLABE', 'LI_HEART_PIECE': 'JI_HEART_PIECE',
    'LI_HEART_CONTAINER': 'JI_HEART_CONTAINER', 'LI_SMALL_KEY': 'JI_KEY',
    'LI_HEART': 'JI_HEART', 'LI_RUPEE1': 'JI_GILT',
    'LI_BOTTLE_EMPTY': 'LI_BOTTLE1 vessel concept',
    'LI_OCARINA': 'JI_HUBCAP return-to-Drain verb; separate actual item',
}

BASE = {
    'JI_SWORD': ('Tool; equip A/B/L', 'New-run starting equipment.', 'src/player.c', 'void player_new_game'),
    'JI_SHIELD': ('Tool; equip A/B/L', 'New-run starting equipment.', 'src/player.c', 'void player_new_game'),
    'JI_SHIELD_UPGRADED': ('Shield appearance/upgrade', 'Award Mirror Shield; its upgrade flag selects the green-and-gold picture.', 'src/legacy_items.c', 'case LI_MIRROR_SHIELD:'),
    'JI_BOMBS': ('Tool; consumes seeds', 'Forest seed trial, Cream trial1, or eligible reward pool.', 'src/game.c', 'void game_give_key_item'),
    'JI_LAMP': ('Tool; equip A/B/L', 'Forest flame trial, Cream trial2, or eligible reward pool.', 'src/game.c', 'void game_give_key_item'),
    'JI_CLOAK': ('Tool; equip A/B/L', 'Forest petal trial, Cream trial3, or eligible reward pool.', 'src/game.c', 'void game_give_key_item'),
    'JI_GAUNTLET': ('Passive strength', 'Forest gauntlet chest; Power Bracelets reward/Cream chest.', 'src/game.c', 'case CHEST_GAUNTLET:'),
    'JI_BOW': ('Tool; consumes arrows', 'Forest bow chest; eligible rewards; Cream chest.', 'src/game.c', 'case CHEST_BOW:'),
    'JI_HUBCAP': ('Tool; equip A/B/L', 'In the pack at the start of every new run.', 'src/player.c', 'gPl.items2 = ITEM2_HUBCAP'),
    'JI_MAP': ('Passive map information', 'Forest map chest or Map of the Wood reward.', 'src/game.c', 'case CHEST_MAP:'),
    'JI_ASTROLABE': ('Passive map information', 'Forest astrolabe chest; Compass reward provides the same marker flag.', 'src/game.c', 'case CHEST_ASTROLABE:'),
    'JI_RELIC': ('Quest possession', 'Physical Forest relic; return to the Weeping Nun.', 'src/objects.c', 'case PK_RELIC:'),
    'JI_HEART_PIECE': ('Health progression', 'Chests, mystery rooms, NPC quests, exchange or reward pool.', 'src/game.c', 'case CHEST_HEART_PIECE:'),
    'JI_HEART_CONTAINER': ('Health progression', 'Forest chest or Nun quest; eligible reward pool.', 'src/game.c', 'case CHEST_HEART_CONTAINER:'),
    'JI_KEY': ('Consumable key counter', 'Key chests, quest drops and loose key pickups.', 'src/game.c', 'case ROLE_KEYCHEST:'),
    'JI_HEART': ('Immediate healing pickup', 'Ordinary enemy/cleared-object drop rolls.', 'src/objects.c', 'void drop_roll'),
    'JI_GILT': ('Currency counter', 'Ordinary enemy/cleared-object drop rolls.', 'src/objects.c', 'void drop_roll'),
    'JI_GILT_BIG': ('Currency pickup', 'Ordinary drops, placed hoards, quests and gilt chest awards.', 'src/objects.c', 'case PK_GILT_BIG:'),
    'JI_BOMB_PICKUP': ('Ammunition pickup', 'Ordinary drop rolls after Bombs are owned.', 'src/objects.c', 'case PK_BOMB:'),
    'JI_ARROW1': ('Ammunition pickup', 'Ordinary drop rolls after the Thorn Bow is owned.', 'src/objects.c', 'case PK_ARROW1:'),
    'JI_ARROW5': ('Ammunition pickup', 'Ordinary drop rolls after the Thorn Bow is owned.', 'src/objects.c', 'case PK_ARROW5:'),
    'JI_ARROW10': ('Ammunition pickup', 'Ordinary bow-owned drops; frog market sells ten for10gilt.', 'src/npc.c', 'static const ShopItem sShop'),
    'JI_GRAIL': ('Run-ending objective', 'Dropped by the Forest Blight Heart; collect it to win.', 'src/objects.c', 'case PK_GRAIL:'),
    'JI_HEALING_PETAL': ('Immediate healing purchase', 'Frog market:10gilt; heals16HP/two hearts.', 'src/npc.c', 'if (choice == 0)'),
}

EFFECT = {
    'LI_GREEN_SWORD': 'A run blessing enables learned Sword Beam at any health. When awarded with Sword Beam already learned, handoff_apply_item_effect returns before ordinary sword_level promotion.',
    'LI_RED_SWORD': 'Sets sword level to at least2; charged spin damage becomes6. Ordinary sword cuts retain their base damage before other blessings.',
    'LI_BLUE_SWORD': 'Sets sword level to at least3; charged spin damage becomes8. Ordinary sword cuts retain their base damage before other blessings.',
    'LI_FOURSWORD': 'Sets sword level4 and enables split-pad charging for up to three companions; companions copy real attacks and activate clone mechanisms.',
    'LI_BOTTLE_BUTTER': 'Drink from its vessel to restore8HP/one heart, leaving the bottle empty.',
    'LI_BOTTLE_WATER': 'Fill a vessel from water, then pour it on marked sprouts/features. Filling stores the state without marking this separate legacy catalogue entry.',
    'LI_BOTTLE_HALF_MILK': 'Milk remaining after its first use; drink for40HP/five hearts. The state change does not mark this separate legacy catalogue entry.',
    'LI_CHARM_NAYRU': 'Award fills an empty vessel. Drink to activate run-long incoming-damage/4, rounded with a minimum of1.',
    'LI_CHARM_FARORE': 'Award fills an empty vessel. Drink to activate half incoming damage and1.5× outgoing damage for the run.',
    'LI_CHARM_DIN': 'Award fills an empty vessel. Drink to activate double outgoing damage for the run.',
    'LI_ORB_GREEN': 'Run curse: periodically loses1HP while above2HP; this rot tick does not itself kill Bloom.',
    'LI_SHELLS': 'If granted: adds shell counter and180ticks of protection. No current award route was found.',
    'LI_SHELLS30': 'Adds30shells and immediately activates the run-long rare-reward blessing. Reward eligibility is once per run despite repeat metadata.',
    'LI_SKILL_LONG_SPIN': 'Doubles charged spin duration from34to68ticks. Actual eligibility requires Spin Attack, not the metadata description\'s Great Spin.',
    'LI_KINSTONE': 'Collect green/blue/red halves in three tooth shapes per color; matched counters unlock fusions. Shaped pickups record discovery without necessarily setting this legacy owned bit.',
    'LI_ARROW_BUTTERFLY': 'Cuts ordinary bow recovery from16to8ticks.',
    'LI_SKILL_FAST_SPIN': 'Lowers spin-charge threshold from80to40ticks.',
    'LI_SKILL_FAST_SPLIT': 'Lowers clone split-pad charge threshold from80to40ticks; requires Fourfold Sword to produce companions.',
}


def normalize(text):
    # Keep prose readable when numeric source terms were authored compactly.
    text = re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', text)
    text = re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', text)
    return re.sub(r':(?=\d)', ': ', text)


def main():
    ids = enums(read('src/legacy_items.h'), 'enum LegacyItem {')
    jid = enums(read('src/journal.h'), 'enum {')
    metadata = {}
    pattern = rf'\[(LI_\w+)\]\s*=\s*\{{({STRING}),({STRING}),([^\n]+?)\}},'
    for match in re.finditer(pattern, read('src/legacy_items_metadata.inc')):
        token, name, description, tail = match.groups()
        equip, category, tier, requirement, flags, frame = tail.split(',')
        metadata[token] = dict(name=ast.literal_eval(name), description=ast.literal_eval(description), equip=equip,
                               category=category, tier=int(tier), requirement=requirement, flags=flags, frame=int(frame))
    pool_text = read('src/handoff_events.c').split('static const Reward sRewards[]={', 1)[1].split('\n};', 1)[0]
    pool = {}
    for token, cats, tier, repeat in re.findall(r'\{([A-Z_0-9]+),([^,]+),(\d+),(\d+)\}', pool_text):
        pool.setdefault(token, []).append(dict(categories=cats, tier=int(tier), repeat=bool(int(repeat))))
    assert len(metadata) == ids['LI_COUNT']
    visible_legacy = {t for t, d in metadata.items() if 'LIF_HIDDEN' not in d['flags']}
    actual_no_route = visible_legacy - set(pool) - set(DIRECT)
    assert actual_no_route == set(NO_ROUTE), (actual_no_route, set(NO_ROUTE))
    entries = []
    base_pattern = rf'\[(JI_\w+)\]\s*=\s*ENTRY\(({STRING}),\s*({STRING}),([^\n]+)\),'
    for token, name, description, _ in re.findall(base_pattern, read('src/journal.c')):
        mode, acquire, path, needle = BASE[token]
        entries.append(dict(journal_id=jid[token], source_namespace='original', source_id=jid[token], source_token=token,
            name=ast.literal_eval(name), effect=ast.literal_eval(description), mode=mode, acquisition_status='available',
            acquisition=normalize(acquire), duplicate_of='', metadata_description=ast.literal_eval(description),
            source_ref=ref('src/journal.c', '['+token+']'), acquisition_ref=ref(path, needle)))
    hidden = []
    for token, d in sorted(metadata.items(), key=lambda x: ids[x[0]]):
        raw = jid['JI_LEGACY_BASE'] + ids[token]
        if 'LIF_HIDDEN' in d['flags']:
            hidden.append(dict(source_token=token, legacy_id=ids[token], journal_id=raw, **d))
            continue
        if token in pool:
            tiers = sorted({x['tier'] for x in pool[token]})
            market = any(any(cat in x['categories'] for cat in ('LCAT_REWARD','LCAT_WEAPON','LCAT_SKILL','LCAT_STAT')) for x in pool[token])
            acquire = 'Eligible regional event/quest/cache rewards (pool tier'+('/'.join(map(str,tiers)))+').'
            if market:
                acquire += ' Also eligible extended-market stock.'
            if token in EXTRA:
                acquire += ' '+EXTRA[token]
            if token in PREREQ:
                acquire += ' '+PREREQ[token]
            if ids['LI_BOTTLE_BUTTER'] <= ids[token] <= ids['LI_CHARM_DIN']:
                acquire += ' Needs an empty owned vessel.'
            pool_start=read('src/handoff_events.c').index('static const Reward sRewards[]={')+len('static const Reward sRewards[]={')
            pool_line=read('src/handoff_events.c')[:pool_start+pool_text.index('{'+token+',')].count('\n')+1
            acquire_ref=f'[src/handoff_events.c](../../src/handoff_events.c#L{pool_line})'
            status = 'available'
        elif token in DIRECT:
            acquire, path, needle = DIRECT[token]
            acquire_ref = ref(path, needle)
            status = 'available_content_state' if token in ('LI_BOTTLE_WATER','LI_BOTTLE_HALF_MILK') else 'available'
        else:
            acquire = NO_ROUTE[token]
            acquire_ref = ref('src/legacy_items.c', 'void legacy_item_grant')
            status = 'defined_only_no_current_award'
        mode = 'Equip A/B/L: '+d['equip'] if d['equip']!='EQ_NONE' else 'Passive / counter / immediate effect'
        if ids['LI_BOTTLE_EMPTY'] <= ids[token] <= ids['LI_CHARM_DIN']:
            mode = 'Vessel contents / drink or pour' if token!='LI_BOTTLE_EMPTY' else 'Empty-vessel award alias'
        if token.startswith('LI_SKILL_'):
            mode = 'Learned passive action'
        entries.append(dict(journal_id=raw, source_namespace='legacy', source_id=ids[token], source_token=token,
            name=d['name'], effect=normalize(EFFECT.get(token, d['description'])), mode=mode,
            acquisition_status=status, acquisition=normalize(acquire), duplicate_of=ALIASES.get(token,''),
            metadata_description=d['description'], equip=d['equip'], category=d['category'], pool=pool.get(token,[]),
            source_ref=ref('src/legacy_items_metadata.inc', '['+token+']'), acquisition_ref=acquire_ref,
            requirement=d['requirement'], flags=d['flags'], tier=d['tier']))
    gold_names = ('Flow Gold Half','Left Gold Half','Middle Gold Half','Right Gold Half')
    for i, token in enumerate(('HANDOFF_GOLD_FLOW','HANDOFF_GOLD_LEFT','HANDOFF_GOLD_MIDDLE','HANDOFF_GOLD_RIGHT')):
        entries.append(dict(journal_id=jid['JI_GOLD_FLOW']+i, source_namespace='gold_half', source_id=0x100+i, source_token=token,
            name=gold_names[i], effect='Match the Flow seal to open its gate.' if i==0 else 'Combine left, middle and right halves at a generated gold-gate interior to open the statue seal/cache.',
            mode='Fusion key possession', acquisition_status='available', acquisition='Eligible tier 1 regional rewards; not ordinary colored kinstone shapes.',
            duplicate_of='', metadata_description='', source_ref=ref('src/journal.c','static const JournalEntry sGoldHalves'),
            acquisition_ref=ref('src/handoff_events.c','{'+token+',')))
    entries.sort(key=lambda e:e['journal_id'])
    for n, entry in enumerate(entries, 1):
        entry['visible_ordinal'] = n
    summary = dict(raw_journal_slots=jid['JI_COUNT'], original_entries=jid['JI_BASE_COUNT'],
        legacy_slots_including_none=ids['LI_COUNT'], hidden_legacy_slots=len(hidden),
        visible_legacy_entries=len(visible_legacy), gold_halves=4, visible_catalogue_entries=len(entries),
        current_acquisition_or_state_entries=sum(e['acquisition_status']!='defined_only_no_current_award' for e in entries),
        defined_only_visible_entries=sum(e['acquisition_status']=='defined_only_no_current_award' for e in entries),
        actual_bottle_states_without_separate_discovery=['LI_BOTTLE_WATER','LI_BOTTLE_HALF_MILK'],
        unique_legacy_ids_in_reward_pool=len(set(pool)&set(metadata)), reward_pool_rows=sum(map(len,pool.values())))
    assert summary['visible_catalogue_entries'] == 139 and summary['raw_journal_slots']==146
    paths=['src/legacy_items.h','src/legacy_items.c','src/legacy_items_metadata.inc','src/journal.h','src/journal.c',
           'src/handoff_events.c','src/handoff_field.inc','src/handoff_objects.c','src/handoff_mobility.c',
           'src/cream_runtime.c','src/objects.c','src/player.c','src/npc.c','src/game.c','src/regional_content.c']
    sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    result=dict(audit_date='2026-11-12', method='Static current-source definitions and acquisition-path audit; not a 139-item runtime collection test.',
        summary=summary, entries=entries, hidden_legacy_slots=hidden,
        extra_available_effects=[dict(token='HANDOFF_FLEET',value=0x104,name='Fleet / Golden Croissant',
            acquisition='Complete five regional field waves.',storage='gHandoffState.food_mask bit HF_FLEET',
            effect='Brief protection on future room entry; no separate visible item-journal entry.')],
        special_drop_codes=[dict(token='LI_KINSTONE_RED',value=0xFC,effect='Adds red kinstone count.'),
            dict(token='LI_KINSTONE_BLUE',value=0xFD,effect='Adds blue kinstone count.'),
            dict(token='LI_KINSTONE_GREEN',value=0xFE,effect='Adds green kinstone count.'),
            dict(token='LI_ENEMY_BEETLE',value=0xFF,effect='Spawns a beetle; not inventory.')],
        source_sha256=sources)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'PLAYER_ITEM_CATALOG.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    fields=('visible_ordinal','journal_id','source_namespace','source_id','source_token','name','equip','category','requirement','flags','tier','mode','effect','acquisition_status','acquisition','duplicate_of','source_ref','acquisition_ref')
    with (OUT/'PLAYER_ITEM_CATALOG.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(entries)
    write_markdown(entries,hidden,summary)
    print(json.dumps(summary,indent=2))


def write_markdown(entries, hidden, summary):
    lines = ['# Every player item: current catalogue and availability','',
        '**There are139 visible entries in the arcade item catalogue. They are not139different equippable tools or unique possessions.**','',
        '| Count | What it means |','|---:|---|',
        '|24|Original item, pickup, objective and purchase entries.|',
        '|118|Legacy metadata slots, including None and helper aliases.|',
        '|−7|Hidden/reserved legacy slots omitted by the visible catalogue.|',
        '|+4|Gold fusion halves, stored outside the ordinary legacy item IDs.|',
        '|**139**|**Visible catalogue entries:24+118−7+4.**|',
        '|146|Raw saved journal IDs before filtering.|',
        '|129|Visible entries with a current acquisition path or reachable bottle-content state.|',
        '|10|Visible legacy entries with no current award route found; listed below.|','',
        'This report audits the current C source and generated reward paths. It is a static availability audit, not a claim that all items were collected in one playthrough. Seed, progression, choices, prerequisites and optional entitlement settings affect which items appear in a run.','',
        'Audit date:2026-11-12. [CSV](PLAYER_ITEM_CATALOG.csv) · [JSON, including source hashes](PLAYER_ITEM_CATALOG.json)','',
        '## How to read the list','',
        '- **#** is the visible1-based arcade ordinal, not a serialized inventory ID. **Journal** is its stable raw saved ID. The JSON/CSV also include source namespace, token and numeric item ID.',
        '- **Available** includes starting equipment, rewards, purchases, world drops, fusions and reachable bottle states. The catalogue deliberately contains aliases: Sword/Hopeful Sword, Root Gauntlet/Power Bracelets, Astrolabe/Compass, several map/heart/key entries and multiple refill quantities.',
        '- **Pool** means the actual shared reward list used by integrated regional events, quests/caches, inn rewards and eligible exchange stock. Its82unique legacy IDs plus four gold halves occupy87rows because Glass Bottle has two entries. Opening drafts draw from the same list with extra category and eligibility restrictions; this does not mean every pooled item can appear in the opening draft.',
        '- Equipped tools can bind to **A, B or L**. Passive skills, boons, curses, keys and counters do not need equipment. Bottle contents are used through one of four equipped vessels.',
        '- Ordinary inventory, equipment, bottle contents and effects belong to the current run and its unfinished-run save. The arcade journal remembers discoveries across runs. Being recorded as seen/owned does not prove a consumable is still physically in a vessel.',
        '- Source links identify metadata and a current acquisition implementation. API support without a caller is classified as defined-only.','',
        '## Original24 entries','',
        '|#|Journal|Item|Use / effect|Current acquisition|','|---:|---:|---|---|---|']
    for namespace,title in [('original',None),('legacy','Legacy111 visible entries'),('gold_half','Gold fusion halves4 entries')]:
        if title:
            lines += ['', '## '+title, '', '|#|Journal|Item|Use / effect|Current acquisition|','|---:|---:|---|---|---|']
        for e in entries:
            if e['source_namespace']!=namespace:
                continue
            effect=e['mode']+'. '+e['effect']
            if e.get('duplicate_of'):
                effect+=' Alias/overlap: '+e['duplicate_of']+'.'
            status='**No current award route:** ' if e['acquisition_status']=='defined_only_no_current_award' else ''
            name=f"[{e['name']}](../../src/{'journal.c' if namespace in ('original','gold_half') else 'legacy_items_metadata.inc'}#L{line('src/journal.c' if namespace in ('original','gold_half') else 'src/legacy_items_metadata.inc','['+e['source_token']+']' if namespace!='gold_half' else 'static const JournalEntry sGoldHalves')})"
            lines.append('|%d|%d|%s|%s|%s%s %s|'%(e['visible_ordinal'],e['journal_id'],name,effect.replace('|','/'),status,e['acquisition'],e['acquisition_ref']))
    lines += ['', '## The ten visible entries with no current award route','',
        'These are not hidden by the catalogue filter. Most are stale alternate award IDs whose effect is already provided by another item. The visible list can therefore show undiscovered entries that current ordinary play cannot award.','',
        '|Legacy ID|Name|Current finding|','|---|---|---|']
    for e in entries:
        if e['acquisition_status']=='defined_only_no_current_award':
            lines.append('|`%s` /0x%02X|%s|%s|'%(e['source_token'],e['source_id'],e['name'],e['acquisition']))
    lines += ['', '## Seven hidden helper slots','',
        'These seven slots remain in the saved raw journal range but are excluded from139 visible entries. None is an additional normally awarded player item.','',
        '|Legacy ID|Name|Reason|','|---|---|---|']
    reasons={'LI_NONE':'Sentinel, not a possession.','LI_LANTERN_ON':'Lit-lamp helper alias; Grail Lamp is the usable tool.','LI_TRY_PICKUP_OBJECT':'Interaction helper.','LI_32':'Reserved placeholder.','LI_33':'Reserved placeholder.','LI_5A':'Reserved placeholder.','LI_WALLET':'Hidden keepsake; existing gilt limit is already999; no award route found.'}
    for e in hidden:
        lines.append('|`%s` /0x%02X|%s|%s|'%(e['source_token'],e['legacy_id'],e['name'],reasons[e['source_token']]))
    lines += ['', '## Available effects and variants outside the139 count','',
        '- **Fleet / Golden Croissant (`HANDOFF_FLEET=0x104`)** is a real additional run blessing. Completing five field waves awards it; it provides brief protection on later room entry. It is represented by an effect bit, not a separate visible journal item. See '+ref('src/handoff_field.inc','give(HANDOFF_FLEET)')+'.',
        '- **Ordinary kinstones** have three colors and three tooth shapes per color. Their nine matched counters belong to the one Kinstone catalogue entry. The four gold halves are separate and are already counted above.',
        '- Legacy drop codes **0xFC/0xFD/0xFE** add red/blue/green kinstones; **0xFF** spawns a beetle. They are not four more ordinary inventory IDs. Normal shaped drops use their own physical pickup path.',
        '- Bushes, rocks, boulders, pots and liftable enemies are temporary carried world objects, not extra item-catalogue possessions.','',
        '## Implementation details that matter','',
        '1. **Water and Half Milk are usable but can remain undiscovered as separate legacy entries.** Filling a vessel and drinking the first milk half directly update `bottles[]`; those assignments do not call the item/journal grant path. Their usable contents exist even if their duplicate arcade entry remains unknown.',
        '2. **Bottle charms activate on drinking.** Nayru/Farore/Din awards first occupy an empty vessel. Picolytes also activate on drinking and last1,800 active update ticks, about30seconds at60updates/second. Current biases: red→hearts; orange→hearts/gilt; yellow→gilt; green→all bias categories; blue→kinstones; white→rare rewards.',
        '3. **The original and legacy ammunition paths use different caps.** Legacy grants respect upgraded bags/quivers (seeds30/50/70/99; arrows50/65/80/99). Original loose pickups, original frog purchases and some original chest paths still clamp seeds to30 or arrows to50. A refill can therefore reduce an upgraded stock above those original caps. The report describes each path rather than claiming all refill sources use upgrades.',
        '4. **Enduring Blade is a blessing-path sword record.** Its current eligible award sets the any-health beam blessing and returns before the ordinary sword-level assignment; Red/Blue affect charged spin strength, not base normal-cut damage.',
        '5. **Long Spin eligibility differs from its text.** The metadata says Great Spin; the live reward predicate checks Spin Attack. Once learned it doubles spin duration34→68ticks.',
        '6. **Names retain source vocabulary.** Rupee entries grant gilt; Bombs are Blightseeds; Grip Ring does not make bare cliff walls climbable. The Root Gauntlet and Power Bracelets share the strength flag; Astrolabe and Compass share a map-marker flag. Mirror Shield also selects the gilded appearance, while adding reflection mechanics.',
        '7. **Effects reset with a new run.** Relics, proofs, ordinary money, learned skills, boons/curses and possession records survive an unfinished-run save, but are not permanent meta unlocks solely because the journal remembers them. Optional entitlement mode separately gates reward eligibility by rank/score.',
        '', '## Reproduce and audit','',
        'Run `python3 tools/player_item_catalog.py` from `bartgame/`. It parses the actual enum, metadata and reward pool, then applies the explicitly audited direct-path annotations. The generator asserts that the no-route set agrees with the current pool/direct-route coverage. Re-audit annotations when gameplay acquisition changes.',
        '', 'Primary sources: '+', '.join([ref('src/journal.h','JI_SWORD'),ref('src/journal.c','static bool8 item_listed'),ref('src/legacy_items.h','enum LegacyItem'),ref('src/legacy_items_metadata.inc','const LegacyItemDef'),ref('src/legacy_items.c','void legacy_item_grant'),ref('src/handoff_events.c','static bool8 eligible'),ref('src/handoff_events.c','static const Reward sRewards'),ref('src/handoff_field.inc','give(HANDOFF_FLEET)')])+'.','']
    # Add spaces to the explanatory compact count phrases, not IDs/code links.
    replacements={'are139':'are 139','not139different':'not 139 different','|24|':'| 24 |','|118|':'| 118 |','|−7|':'| −7 |','|+4|':'| +4 |','|146|':'| 146 |','|129|':'| 129 |','|10|':'| 10 |','entries:24+118−7+4':'entries: 24 + 118 − 7 + 4','visible1-based':'visible 1-based','Its82unique':'Its 82 unique','Its82':'Its 82','pool. Its82':'pool. Its 82','plus four gold halves occupy87rows':'plus four gold halves occupy 87 rows','Original24':'Original 24','Legacy111':'Legacy 111','halves4':'halves: 4','from139':'from 139','the139':'the 139','already999':'already 999','last1,800':'last 1,800','about30seconds':'about 30 seconds','at60updates':'at 60 updates','seeds30':'seeds 30','arrows50':'arrows 50','to30':'to 30','to50':'to 50','duration34':'duration 34','→68ticks':'→68 ticks'}
    text='\n'.join(lines)
    for old,new in replacements.items():
        text=text.replace(old,new)
    text=text.replace('Audit date:2026-11-12.', 'Audit date: 2026-11-12.')
    text='\n'.join('| '+' | '.join(c.strip() for c in row.strip('|').split('|'))+' |' if row.startswith('|') else row for row in text.split('\n'))
    (OUT/'PLAYER_ITEM_CATALOG.md').write_text(text)


if __name__=='__main__':
    main()
