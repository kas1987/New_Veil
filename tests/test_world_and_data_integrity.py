"""Cross-plane RPG data & referential integrity tests.

Catches broken IDs, missing NPCs, invalid quest rewards, dangling travel edges,
and schema drift across 01_districts, 02_systems, 11_world, 13_agents,
14_psychometrics, and 15_voice.
"""

from __future__ import annotations

import json
from pathlib import Path

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_world_manifest_graph_integrity() -> None:
    world = _load("11_world/world_manifest.json")
    region_ids = {r["id"] for r in world["regions"]}
    settlement_ids = {s["id"] for s in world["settlements"]}
    location_ids = {loc["id"] for loc in world["locations"]}

    assert len(region_ids) == len(world["regions"])
    assert len(settlement_ids) == len(world["settlements"])
    assert len(location_ids) == len(world["locations"])

    for settlement in world["settlements"]:
        assert settlement["region_id"] in region_ids, f"Bad region_id on {settlement['id']}"

    for loc in world["locations"]:
        assert loc["settlement_id"] in settlement_ids, f"Bad settlement_id on {loc['id']}"
        coords = loc["map_coords"]
        assert 0 <= coords["x"] <= 100
        assert 0 <= coords["y"] <= 100

    for edge in world["connections"]:
        assert edge["from"] in location_ids, f"Dangling connection from={edge['from']}"
        assert edge["to"] in location_ids, f"Dangling connection to={edge['to']}"


def test_character_roster_and_nine_sisters_complete() -> None:
    world = _load("11_world/world_manifest.json")
    factions = {f["id"] for f in _load("11_world/factions.json")["factions"]}
    voices = _load("15_voice/voice_registry.json")["voices"]
    roster = _load("13_agents/roster_index.json")["characters"]

    location_ids = {loc["id"] for loc in world["locations"]}
    char_ids = {c["id"] for c in roster}
    assert len(char_ids) == len(roster), "Duplicate character IDs in roster_index.json"

    # Canonical Nine Sisters must all be present
    expected_sisters = {"mira", "solenne", "vael", "lyra", "shadow", "ashara", "nyth", "thessa", "witness"}
    assert expected_sisters.issubset(char_ids), f"Missing sisters: {expected_sisters - char_ids}"

    for char in roster:
        assert char["faction_id"] in factions, f"{char['id']} references unknown faction {char['faction_id']}"
        assert char["home_location"] in location_ids, f"{char['id']} references unknown home_location"
        assert char["id"] in voices, f"{char['id']} missing from 15_voice/voice_registry.json"

    for loc in world["locations"]:
        for npc_id in loc.get("npcs", []):
            assert npc_id in char_ids, f"Location {loc['id']} references unknown NPC {npc_id}"


def test_quests_economy_and_encounters_integrity() -> None:
    world = _load("11_world/world_manifest.json")
    factions = {f["id"] for f in _load("11_world/factions.json")["factions"]}
    items = {i["id"] for i in _load("02_systems/items.json")["items"]}
    quests = _load("02_systems/quests.json")["quests"]
    economy = _load("02_systems/economy.json")
    encounters = _load("02_systems/encounters.json")["encounters"]
    roster = {c["id"] for c in _load("13_agents/roster_index.json")["characters"]}
    attributes = {a["id"] for a in _load("14_psychometrics/attributes.json")["attributes"]}
    location_ids = {loc["id"] for loc in world["locations"]}

    for quest in quests:
        assert quest["giver"] in roster, f"Quest {quest['id']} unknown giver {quest['giver']}"
        assert len(quest["stages"]) >= 1
        rewards = quest.get("rewards") or {}
        for item_id in rewards.get("items", []):
            assert item_id in items, f"Quest {quest['id']} unknown reward item {item_id}"
        for faction_id in (rewards.get("faction") or {}).keys():
            assert faction_id in factions, f"Quest {quest['id']} unknown reward faction {faction_id}"

    for merchant in economy["merchants"]:
        assert merchant["npc_id"] in roster
        assert merchant["location_id"] in location_ids
        for item_id in merchant["stock"]:
            assert item_id in items, f"Merchant {merchant['id']} unknown stock item {item_id}"

    for enc in encounters:
        assert enc["location_id"] in location_ids
        for choice in enc["choices"]:
            assert choice["attribute"] in attributes, f"Encounter {enc['id']} unknown attribute {choice['attribute']}"


def test_district_unlock_engine_works_for_all_districts() -> None:
    unlock_engine = load_module("unlock_engine", ROOT / "01_districts" / "unlock_engine.py")
    for district_id in ("caetherra", "stillward", "ashveil", "ember_vaults", "the_hollow"):
        res = unlock_engine.check_unlock(
            district_id=district_id,
            resonance=0.9,
            interactions=10,
            emotional_tags=["warmth", "mystery", "recognition"],
            veil_state="calm",
            player_state={"unlocked_districts": ["caetherra", "ashveil"], "has_lantern": True, "lantern_used": True},
        )
        assert res.unlocked is True, f"Expected {district_id} to unlock at high resonance: {res.reason}"
