"""Contract & mechanics tests for The Veil unified Game API."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]


def _make_client() -> TestClient:
    server_mod = load_module("veil_game_server", ROOT / "04_runtime" / "game_api" / "server.py")
    app = server_mod.create_app(db_path=":memory:")
    return TestClient(app)


def test_health_and_error_handling() -> None:
    client = _make_client()
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.post("/api/world/travel", json={"location_id": "nonexistent"}).status_code == 404
    assert client.post("/api/dialogue/turn", json={"npc_id": "ghost", "message": "hi"}).status_code == 400
    assert client.post("/api/dialogue/turn", json={"npc_id": "mira", "message": "   "}).status_code == 400
    assert client.post("/api/economy/buy", json={"item_id": "fake_item"}).status_code == 404
    assert client.post("/api/inventory/use", json={"item_id": "fake_item"}).status_code == 404
    assert client.post("/api/encounters/resolve", json={"encounter_id": "bad", "choice_id": "bad"}).status_code == 404
    assert client.post("/api/saves/load/missing_slot").status_code == 404


def test_locked_district_blocks_travel_until_earned() -> None:
    client = _make_client()
    # The Hollow requires 0.75 resonance; starter player has 0.35
    resp = client.post("/api/world/travel", json={"location_id": "hollow_clearing"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "Resonance" in body["message"]
    assert body["state"]["world"]["current_location"]["id"] == "caetherra_plaza"


def test_economy_equip_and_consumable_mechanics() -> None:
    client = _make_client()
    # Cannot buy lantern at Caetherra Plaza (no merchant there)
    no_shop = client.post("/api/economy/buy", json={"item_id": "lantern"}).json()
    assert no_shop["ok"] is False

    # Move to Solstice Bazaar where Kaelen sells items
    client.post("/api/world/travel", json={"location_id": "solstice_bazaar"})
    # Player starts with 12 echoes; lantern costs 15 -> should fail
    too_poor = client.post("/api/economy/buy", json={"item_id": "lantern"}).json()
    assert too_poor["ok"] is False
    assert "Need 15 Echoes" in too_poor["message"]

    # Buy mirror (10 echoes) -> succeeds, then equip it for +2 empathy
    bought = client.post("/api/economy/buy", json={"item_id": "mirror"}).json()
    assert bought["ok"] is True
    assert bought["state"]["world"]["echoes"] == 2

    equipped = client.post("/api/inventory/use", json={"item_id": "mirror"}).json()
    assert equipped["ok"] is True
    assert equipped["state"]["player"]["bonuses"]["empathy"] == 2
    assert equipped["state"]["player"]["empathy"] == 12

    # Consume starter echo_shard -> boosts resonance
    before_res = equipped["state"]["player"]["resonance"]
    used = client.post("/api/inventory/use", json={"item_id": "echo_shard"}).json()
    assert used["ok"] is True
    assert used["state"]["player"]["resonance"] > before_res


def test_quasar_active_gravity_and_true_name_reveal() -> None:
    client = _make_client()
    engine = client.app.state.engine

    # Shift Veil: calm -> still -> storm -> quasar_active
    for expected in ("still", "storm", "quasar_active"):
        res = client.post("/api/world/advance-veil").json()
        assert res["veil_state"] == expected

    # Raise resonance to >= 0.80 so Mira's true name reveals under quasar_active
    engine._conn.execute("UPDATE player_stats SET resonance = 0.85 WHERE player_id='player'")
    engine._conn.commit()

    before = client.get("/api/game/state").json()
    mira_before = next(n for n in before["npcs_here"] if n["id"] == "mira")
    assert "Thesmera Locke" in mira_before["display_name"]

    # Talking during quasar_active applies Dark Quasar gravity (suspicion rises, affection sags)
    after = client.post(
        "/api/dialogue/turn",
        json={"npc_id": "mira", "message": "I am ready to face the Dark Quasar truth."},
    ).json()
    mira_after = next(n for n in after["state"]["npcs_here"] if n["id"] == "mira")
    assert mira_after["relationship"]["suspicion"] > mira_before["relationship"]["suspicion"]
    assert mira_after["relationship"]["affection"] < mira_before["relationship"]["affection"]


def test_encounter_deterministic_resolution_and_save_restore() -> None:
    client = _make_client()
    engine = client.app.state.engine

    # Save baseline at Caetherra Plaza
    client.post("/api/saves/save", json={"slot_id": "baseline", "label": "Day 1 Start"})

    # Resolve encounter with deterministic seed
    res = engine.resolve_encounter("trial_prism_surface", "accept_warmth", seed=42)
    assert res["ok"] is True
    assert 1 <= res["roll"] <= 20
    assert res["state"]["player"]["xp"] > 0

    # Travel away, then restore baseline
    client.post("/api/world/travel", json={"location_id": "solstice_bazaar"})
    loaded = client.post("/api/saves/load/baseline").json()
    assert loaded["ok"] is True
    assert loaded["state"]["world"]["current_location"]["id"] == "caetherra_plaza"
    assert loaded["state"]["player"]["xp"] == 0


def test_expanded_town_pois_and_true_vs_false_ending_tracker() -> None:
    client = _make_client()
    engine = client.app.state.engine

    # Baseline is false_ending_risk
    initial = client.get("/api/game/ending").json()
    assert initial["trajectory"] == "false_ending_risk"

    # Travel to expanded Solstice Crossing POIs
    assert client.post("/api/world/travel", json={"location_id": "crossroads_tavern"}).json()["ok"] is True
    assert client.post("/api/world/travel", json={"location_id": "mirror_well"}).json()["ok"] is True

    # Satisfy all 4 True Ending canon criteria
    engine._conn.execute("UPDATE player_stats SET resonance = 0.85 WHERE player_id='player'")
    engine._conn.execute("UPDATE relationships SET trust = 75.0 WHERE agent_a='mira' AND agent_b='player'")
    engine._conn.commit()
    for _ in range(3):
        client.post("/api/world/advance-veil")  # reaches quasar_active
    assert client.post("/api/world/travel", json={"location_id": "void_threshold"}).json()["ok"] is True

    ready = client.get("/api/game/ending").json()
    assert ready["trajectory"] == "true_ending_ready"
    assert all(ready["criteria"].values())
    assert "void_threshold" in ready["hidden_paths_found"]


def test_party_codex_portrait_binding_and_runtime_status() -> None:
    client = _make_client()

    # Party toggle: recruit Solenne, dismiss Mira, reject non-recruitable Greeter
    add_sol = client.post("/api/party/toggle", json={"character_id": "solenne"}).json()
    assert add_sol["ok"] is True
    assert "solenne" in add_sol["party"]

    rm_mira = client.post("/api/party/toggle", json={"character_id": "mira"}).json()
    assert rm_mira["ok"] is True
    assert "mira" not in rm_mira["party"]

    reject = client.post("/api/party/toggle", json={"character_id": "greeter"}).json()
    assert reject["ok"] is False

    # Codex returns entries with resonance gating
    codex = client.get("/api/codex").json()["entries"]
    assert len(codex) >= 4
    lore = next(e for e in codex if e["id"] == "lore_bible")
    quasar = next(e for e in codex if e["id"] == "dark_quasar")
    assert lore["unlocked"] is True
    assert quasar["unlocked"] is False  # Starter resonance 0.35 < 0.60

    # Portrait binding updates NPC portrait_url cleanly
    bound = client.post("/api/media/bind", json={"npc_id": "mira", "media_key": "adeline"}).json()
    assert bound["ok"] is True
    mira = next(n for n in bound["state"]["npcs_here"] if n["id"] == "mira")
    assert mira["portrait_url"] == "/api/media/portrait/adeline"

    # Runtime status endpoint
    status = client.get("/api/runtime/status").json()
    assert "live_llm_enabled" in status
    assert "comfy_hub" in status
