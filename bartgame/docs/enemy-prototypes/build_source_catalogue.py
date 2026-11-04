#!/usr/bin/env python3
"""Reproduce the carried-over roster and raw combat-data provenance.

This is a read-only source extraction, not a runtime enemy configuration.
Run from any directory; output sits beside this script.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PICKS = ROOT / "src/game.c"
STATS = ROOT / "docs/newgame/data/enemies.csv"
MATRIX = ROOT / "docs/newgame/data/collision_matrix.csv"


def main():
    source = PICKS.read_text()
    stats = list(csv.DictReader(STATS.open(newline="")))
    stat_index = {(r["name"], int(r["form"])): (i + 2, r)
                  for i, r in enumerate(stats)}
    matrix = list(csv.DictReader(MATRIX.open(newline="")))
    matrix_index = {(int(r["hitType"]), int(r["hurtType"])): (i + 2, r)
                    for i, r in enumerate(matrix)}
    entries = []
    counts = {}
    for tier in ("1", "2", "3", "4", "5", "Elite"):
        array = "sQuickStartElites" if tier == "Elite" else "sQuickStartLevel" + tier
        match = re.search(r"static const QuickStartEnemyPick " + array +
                          r"\[\] = \{(.*?)\n\};", source, re.S)
        assert match, array
        tier_entries = []
        for line in match.group(1).splitlines(keepends=True):
            clean = re.sub(r"/\*.*?\*/|//[^\n]*", "", line)
            pick = re.match(r"\s*\{\s*([A-Z_0-9]+),\s*(\d+)\s*,(.*?)\}", clean)
            if not pick:
                continue
            name, form, tail = pick.groups()
            roles, cost, requires, *theme = [v.strip() for v in tail.split(",")]
            stat_key = (name, int(form))
            shared_definition = stat_key not in stat_index
            if shared_definition:
                # Rupee Like uses a single shared EnemyDefinition for its three
                # curated colors. The extractor emits that definition once.
                assert name == "RUPEE_LIKE" and int(form) in (1, 2)
                stat_key = (name, 0)
            stat_line, stat = stat_index[stat_key]
            data = {k: (int(v, 0) if k == "id" else float(v)
                         if k == "speed_px_per_frame" else int(v)
                         if k in {"form", "health", "speed_q8_8", "damage_type",
                                  "collision_mask", "hb_off_x", "hb_off_y",
                                  "hb_half_w", "hb_half_h"} else v)
                    for k, v in stat.items()}
            raw_cells = {}
            for label, hurt_type in (("player_body_0", 0), ("normal_sword_13", 13)):
                cell = matrix_index.get((data["damage_type"], hurt_type))
                if cell:
                    csv_line, values = cell
                    raw_cells[label] = {"source_line": csv_line, "values": values}
            tier_entries.append({
                "name": name, "form": int(form), "legacy_tier": tier,
                "roles": [v.strip().removeprefix("QS_R_") for v in roles.split("|")],
                "legacy_gfx_cost": int(cost), "legacy_required_item": requires,
                "legacy_theme": theme[0].removeprefix("QS_T_") if theme else None,
                "roster_array": array,
                "roster_line": source[:source.index(line, match.start())].count("\n") + 1,
                "stats_csv_line": stat_line, "initial_reference_stats": data,
                "shared_base_definition": shared_definition,
                "initial_state_matrix_cells": raw_cells,
            })
        counts[tier] = len(tier_entries)
        entries.extend(tier_entries)
    assert counts == {"1": 10, "2": 15, "3": 17, "4": 12, "5": 11, "Elite": 6}, counts
    assert len(stats) == 213 and len(entries) == 71
    assert len({(e["name"], e["form"]) for e in entries}) == 71
    paths = [PICKS, STATS, MATRIX, ROOT / "tools/newgame/extract_feel.py",
             ROOT / "src/collision.c", ROOT / "src/ui.c", ROOT / "src/enemy.c",
             ROOT / "docs/newgame/00_README.md",
             ROOT / "docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md",
             ROOT / "docs/newgame/06_CURRENT_GAME_DESIGN.md",
             ROOT / "docs/newgame/12_FROM_SCRATCH_ENGINE.md"]
    paths += [ROOT / "src/enemy" / (name + ".c") for name in
              ("rope", "spikedBeetle", "crow", "helmasaur", "leever",
               "tektite", "puffstool", "bobomb", "rupeeLike")]
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       text=True).strip()
    catalogue = {
        "status": "Reference extraction only; not an adopted roster or new-game balance table.",
        "source_revision": revision,
        "source_repository": "https://github.com/natertott/bartgame",
        "raw_reference_form_count": len(stats), "curated_pick_count": len(entries),
        "curated_enemy_id_count": len({entry["name"] for entry in entries}),
        "curated_counts_by_legacy_tier": counts,
        "units": {"speed_q8_8": "256 units = 1 pixel/frame",
                  "health": "Reference entity units; special lifecycles may ignore ordinary HP.",
                  "player_health": "8 units = 1 heart; ordinary contact 2 units = quarter heart.",
                  "damage_type": "Collision row ID, never a damage amount.",
                  "legacy_gfx_cost": "Old TMC dynamic graphics slots, not new-engine actor cost."},
        "cautions": [
            "Stats describe initial forms, not every armor/airborne/exposure state.",
            "Handlers, contact callbacks and damage modifiers can override matrix defaults.",
            "CSV damage_to_org means damage to player/weapon side; damage_to_tgt means damage to enemy.",
            "Only handler=default cells are direct generic damage values; numeric handlers require code review.",
            "No implicit conversion from raw HP 255 to a damage-sponge enemy is valid.",
            "Historical tiers are provenance, not a new hard difficulty or progression gate.",
        ],
        "sources": [{"path": str(p.relative_to(ROOT)),
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
        "entries": entries,
    }
    destination = HERE / "source_catalogue.json"
    destination.write_text(json.dumps(catalogue, indent=2) + "\n")
    print(f"{len(entries)} curated picks; {len(stats)} raw forms; wrote {destination}")


if __name__ == "__main__":
    main()
