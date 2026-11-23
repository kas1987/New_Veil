"""End-to-end Veil Town & District 1 voice coverage and progression playtest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_API = ROOT / "04_runtime" / "game_api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from engine import (  # noqa: E402
    AdvanceVeil,
    Buy,
    ChooseBeat,
    Inspect,
    Resolve,
    Talk,
    Travel,
    VeilGameEngine,
)

_FORBIDDEN_GENERIC_FRAGMENTS = (
    "Few travelers look past the warmth so quickly",
    "answers warmly:",
    "offers warm Prism guidance",
)
_RENDERED_WARMTH_FORBIDDEN = ("gentle", "soft", "candle", "dawn")


def _engine() -> VeilGameEngine:
    return VeilGameEngine(repo_root=ROOT, db_path=":memory:")


def test_all_roster_npcs_have_authored_dialogue_beat_packs() -> None:
    roster = json.loads((ROOT / "13_agents" / "roster_index.json").read_text(encoding="utf-8"))["characters"]
    roster_ids = {c["id"] for c in roster}

    caetherra_npcs = json.loads((ROOT / "13_agents" / "caetherra_dialogue_beats.json").read_text(encoding="utf-8"))["npcs"]
    town_npcs = json.loads((ROOT / "13_agents" / "veil_town_dialogue_beats.json").read_text(encoding="utf-8"))["npcs"]
    assert set(caetherra_npcs).isdisjoint(set(town_npcs))

    merged = {**caetherra_npcs, **town_npcs}
    assert set(merged.keys()) == roster_ids

    for npc_id, entry in merged.items():
        tiers = entry["tiers"]
        assert set(tiers.keys()) == {"stranger", "trusted", "deep"}
        for tier_name, families in tiers.items():
            assert set(families.keys()) == {"reflective", "grounded", "friction", "quasar"}
            for family_name, lines in families.items():
                assert len(lines) >= 2, f"{npc_id}.{tier_name}.{family_name} needs >= 2 lines"
                assert all(isinstance(line, str) and line.strip() for line in lines)
                if npc_id == "rendered":
                    for line in lines:
                        lower = line.lower()
                        for banned in _RENDERED_WARMTH_FORBIDDEN:
                            assert banned not in lower, f"Rendered line used warmth word '{banned}': {line}"
                if npc_id == "shadow":
                    for line in lines:
                        assert len(line.split()) <= 12, f"Shadow line too verbose: {line}"

        callbacks = entry["beat_callbacks"]
        for required_beat in ("inspected:lantern:dq", "inspected:wall_of_the_unseen_gate:dq", "false_comfort_declined", "caetherra_awakened"):
            assert required_beat in callbacks and callbacks[required_beat].strip()


def test_full_veil_town_progression_playtest_zero_generic_fallbacks() -> None:
    engine = _engine()
    observed_replies: list[tuple[str, str]] = []

    def say(npc_id: str, prompt: str) -> str:
        res = engine.play(Talk(npc_id, prompt))
        assert res.ok is True and res.reply is not None, f"Talk failed for {npc_id}: {res.message}"
        reply = res.reply.text
        assert reply.strip()
        for frag in _FORBIDDEN_GENERIC_FRAGMENTS:
            assert frag not in reply, f"Generic fallback leaked for {npc_id}: {reply}"
        observed_replies.append((npc_id, reply))
        return reply

    # 1. Caetherra Sunlit Plaza: inspect surface objects, talk to Mira, Solenne, Greeter
    assert engine.play(Inspect("lantern")).ok is True
    assert engine.play(Inspect("mirror")).ok is True
    say("mira", "I wonder why the warm lanterns burn brighter in Caetherra — what lies beneath?")
    say("solenne", "Do small candles hold peace beside this sunlit plaza?")
    say("greeter", "Are the lanterns lit for every stranger who rests here?")
    assert engine.play(Resolve("trial_prism_surface", "accept_warmth", seed=0)).ok is True

    # 2. Solstice Crossing: talk to Kaelen and buy the Prism Lantern
    assert engine.play(Travel("solstice_bazaar")).ok is True
    say("kaelen_lanternwright", "Does brass and prismatic glass hold steady along the eastern rim?")
    assert engine.play(Buy("lantern")).ok is True

    # Raise resonance across Stillward -> Ashveil -> Ember Vaults -> Hollow -> Rim thresholds
    engine._conn.execute("UPDATE player_stats SET resonance=815.0, has_crossed_first_threshold=1 WHERE player_id='player'")
    engine._conn.commit()
    for i in range(4):
        assert engine.play(Travel("caetherra_plaza")).ok is True
        say("mira", f"What quiet memory #{i} stays behind your warm mirror?")
        assert engine.play(Travel("solstice_bazaar")).ok is True

    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(ChooseBeat("caetherra_false_comfort", "decline")).ok is True

    # 3. Stillward Cloister: talk to Warden & Archivist, then advance to storm & solve trial
    assert engine.play(Travel("stillward_cloister")).ok is True
    say("warden", "Why does the Stilling Bell ring softly beneath white stone?")
    say("archivist", "What erased margins stay organized in Ledger Twelve?")
    assert engine.play(AdvanceVeil()).scene["world"]["veil_state"] == "still"
    assert engine.play(AdvanceVeil()).scene["world"]["veil_state"] == "storm"
    trial = engine.play(Resolve("trial_stillward_mirror", "attune_bell", seed=0))
    assert trial.ok is True and trial.check is not None and trial.check.success is True

    # 4. Listening Wall (storm): inspect wall_of_the_unseen_gate + Witness + Threadwatcher
    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(Travel("listening_wall")).ok is True
    assert engine.play(Inspect("wall_of_the_unseen_gate")).ok is True
    say("witness", "What stayed written along this mortar?")
    say("threadwatcher", "Why is that silver filament pulled taut toward Ashveil?")

    # 5. Mira's Garden -> Caetherra Awakened
    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(Travel("miras_garden")).ok is True
    say("mira", "I saw the unseen gate in the storm — what does Caetherra ask now?")
    assert engine.scene()["district_status"]["caetherra_awakened"] is True

    # 6. Ashveil & Ember Vaults -> Vael & Rendered
    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(Travel("ashveil_forges")).ok is True
    say("vael", "Why does forge heat strip surface comfort down to bare iron?")
    assert engine.play(Travel("ember_vaults_anvil")).ok is True
    say("rendered", "What remains in iron beneath Vault Seven after ash settles?")

    # 7. The Hollow -> Lyra, Shadow, Ashara, Thessa + void_door inspect -> Gravity Spire & Nyth
    assert engine.play(Travel("ashveil_forges")).ok is True
    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(Travel("stillward_cloister")).ok is True
    assert engine.play(Travel("hollow_clearing")).ok is True
    assert engine.play(Inspect("void_door")).ok is True
    say("lyra", "What dream echo lingers across dark glass water tonight?")
    say("shadow", "What did you notice behind my last quiet pause?")
    say("ashara", "Does still water remember what travelers set down to stay comfortable?")
    say("thessa", "Which bearing opens east toward obsidian cliffs tonight?")

    assert engine.play(Travel("gravity_spire_deck")).ok is True
    assert engine.play(AdvanceVeil()).scene["world"]["veil_state"] == "quasar_active"
    say("nyth", "Does gravity break unearned warmth along this rim?")
    assert engine.play(Travel("void_threshold")).ok is True

    assert engine.scene()["ending_status"]["trajectory"] == "true_ending_ready"
    spoken_ids = {npc_id for npc_id, _ in observed_replies}
    assert len(spoken_ids) == 15
