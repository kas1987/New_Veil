"""End-to-end smoke tests for The Veil RPG vertical slice."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]


def _make_client() -> TestClient:
    server_mod = load_module("veil_game_server", ROOT / "04_runtime" / "game_api" / "server.py")
    app = server_mod.create_app(db_path=":memory:")
    return TestClient(app)


def test_game_state_and_world_bootstrap() -> None:
    client = _make_client()
    resp = client.get("/api/game/state")
    assert resp.status_code == 200
    data = resp.json()

    assert data["world"]["world_id"] == "the_veil"
    assert data["world"]["current_location"]["id"] == "caetherra_plaza"
    assert data["world"]["veil_state"] == "calm"
    assert len(data["world"]["regions"]) >= 3
    assert len(data["world"]["settlements"]) >= 3
    assert len(data["all_characters"]) >= 15
    assert any(npc["id"] == "mira" for npc in data["npcs_here"])


def test_dialogue_travel_economy_encounter_and_saves() -> None:
    client = _make_client()

    # 1. Talk to Mira
    talk = client.post(
        "/api/dialogue/turn",
        json={"npc_id": "mira", "message": "What truth lies beneath the Prism and the Veil?"},
    )
    assert talk.status_code == 200
    assert talk.json()["ok"] is True
    assert talk.json()["resonance_delta"] > 0

    # 2. Travel to Solstice Crossing town
    travel = client.post("/api/world/travel", json={"location_id": "solstice_bazaar"})
    assert travel.status_code == 200
    assert travel.json()["ok"] is True
    assert travel.json()["state"]["world"]["current_location"]["id"] == "solstice_bazaar"

    # 3. Buy an Echo Shard from Kaelen
    buy = client.post("/api/economy/buy", json={"item_id": "echo_shard"})
    assert buy.status_code == 200
    assert buy.json()["ok"] is True

    # 4. Advance Veil state
    veil = client.post("/api/world/advance-veil")
    assert veil.status_code == 200
    assert veil.json()["veil_state"] == "still"

    # 5. Save and Load checkpoint
    saved = client.post("/api/saves/save", json={"slot_id": "slot1", "label": "Test Save"})
    assert saved.status_code == 200
    loaded = client.post("/api/saves/load/slot1")
    assert loaded.status_code == 200
    assert loaded.json()["ok"] is True
