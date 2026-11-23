"""Unified RPG Game Engine for The Veil.

Consolidates world hierarchy (11_world), districts (01_districts), RPG systems
(02_systems), characters (13_agents), psychometrics (14_psychometrics), voice
cues (15_voice), and SQLite persistence (03_memory/schema.sql) into a single
coherent runtime engine.
"""

from __future__ import annotations

import json
import os
import random
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_VEIL_CYCLE = ["calm", "still", "storm", "quasar_active"]
_TIME_CYCLE = ["dawn", "day", "dusk", "night"]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class VeilGameEngine:
    """Stateful RPG runtime backed by SQLite + canonical JSON registries."""

    def __init__(self, repo_root: Path, db_path: Path | str | None = None) -> None:
        self.repo_root = Path(repo_root).resolve()
        if db_path is None:
            logs_dir = self.repo_root / "06_logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            self.db_path: Path | str = logs_dir / "veil_rpg.sqlite"
        else:
            self.db_path = db_path

        # Load canonical registries
        self.world = _load_json(self.repo_root / "11_world" / "world_manifest.json")
        self.factions = _load_json(self.repo_root / "11_world" / "factions.json")["factions"]
        self.items_catalog = {
            item["id"]: item
            for item in _load_json(self.repo_root / "02_systems" / "items.json")["items"]
        }
        self.quests_catalog = {
            q["id"]: q
            for q in _load_json(self.repo_root / "02_systems" / "quests.json")["quests"]
        }
        self.encounters_catalog = {
            e["id"]: e
            for e in _load_json(self.repo_root / "02_systems" / "encounters.json")["encounters"]
        }
        self.economy = _load_json(self.repo_root / "02_systems" / "economy.json")
        self.characters = {
            c["id"]: c
            for c in _load_json(self.repo_root / "13_agents" / "roster_index.json")["characters"]
        }
        self.psychometrics = _load_json(self.repo_root / "14_psychometrics" / "attributes.json")
        self.voices = _load_json(self.repo_root / "15_voice" / "voice_registry.json")["voices"]

        self.locations = {loc["id"]: loc for loc in self.world["locations"]}
        self.settlements = {s["id"]: s for s in self.world["settlements"]}
        self.regions = {r["id"]: r for r in self.world["regions"]}
        self.merchants_by_location = {
            m["location_id"]: m for m in self.economy.get("merchants", [])
        }

        self._conn = self._init_db()
        self._seed_defaults()

    def _init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        schema_sql = (self.repo_root / "03_memory" / "schema.sql").read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.commit()
        return conn

    def _seed_defaults(self) -> None:
        cur = self._conn.cursor()
        cur.execute("INSERT OR IGNORE INTO player_state (player_id) VALUES ('player')")
        cur.execute("INSERT OR IGNORE INTO world_state (player_id) VALUES ('player')")
        cur.execute("INSERT OR IGNORE INTO player_stats (player_id) VALUES ('player')")

        # Starter items
        cur.execute(
            "INSERT OR IGNORE INTO inventory (player_id, item_id, quantity, equipped) "
            "VALUES ('player', 'echo_shard', 2, 0)"
        )
        # Starter quests
        for qid in ("q_first_awakening", "q_solstice_trade"):
            cur.execute(
                "INSERT OR IGNORE INTO quest_progress (player_id, quest_id, status, stage_index) "
                "VALUES ('player', ?, 'active', 0)",
                (qid,),
            )
        # Starter factions
        for faction in self.factions:
            cur.execute(
                "INSERT OR IGNORE INTO faction_reputation (player_id, faction_id, reputation, rank) "
                "VALUES ('player', ?, 0, ?)",
                (faction["id"], faction["ranks"][0]),
            )
        # Starter relationships for key NPCs
        for cid in ("mira", "solenne", "vael", "kaelen_lanternwright"):
            cur.execute(
                "INSERT OR IGNORE INTO relationships (agent_a, agent_b, trust, affection, suspicion, resistance) "
                "VALUES (?, 'player', 52.0, 50.0, 10.0, 65.0)",
                (cid,),
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _row_dict(self, sql: str, params: tuple = ()) -> dict[str, Any]:
        row = self._conn.execute(sql, params).fetchone()
        return dict(row) if row else {}

    def _rows_list(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def _inventory_map(self) -> dict[str, dict[str, Any]]:
        rows = self._rows_list("SELECT * FROM inventory WHERE player_id='player' AND quantity > 0")
        return {r["item_id"]: r for r in rows}

    def _effective_stats(self, raw_stats: dict[str, Any], inv: dict[str, dict[str, Any]]) -> dict[str, Any]:
        bonuses = {k: 0 for k in ("clarity", "empathy", "resolve", "perception", "veil_attunement")}
        for item_id, row in inv.items():
            if row.get("equipped") and item_id in self.items_catalog:
                for stat_key, val in self.items_catalog[item_id].get("stat_bonuses", {}).items():
                    if stat_key in bonuses:
                        bonuses[stat_key] += int(val)
        effective = dict(raw_stats)
        effective["emotional_tags"] = json.loads(raw_stats.get("emotional_tags") or "[]")
        effective["bonuses"] = bonuses
        for stat_key, bonus in bonuses.items():
            effective[stat_key] = int(raw_stats.get(stat_key, 10)) + bonus
        # Resonance tier
        res = float(effective.get("resonance", 0.35))
        tier = self.psychometrics["resonance_tiers"][0]
        for t in self.psychometrics["resonance_tiers"]:
            if res >= t["min_resonance"]:
                tier = t
        effective["resonance_tier"] = tier
        return effective

    def _check_location_access(
        self,
        loc: dict[str, Any],
        stats: dict[str, Any],
        world_state: dict[str, Any],
        inv: dict[str, dict[str, Any]],
        turns_taken: int,
    ) -> tuple[bool, str]:
        cond = loc.get("unlock_conditions") or {}
        res = float(stats.get("resonance", 0.0))
        min_res = float(cond.get("min_resonance", 0.0))
        if res < min_res:
            return False, f"Requires {min_res:.2f} Resonance (current: {res:.2f})."

        min_inter = int(cond.get("min_interactions", 0))
        if turns_taken < min_inter:
            return False, f"Requires {min_inter} meaningful interactions (current: {turns_taken})."

        req_item = cond.get("requires_item")
        if req_item and req_item not in inv:
            item_name = self.items_catalog.get(req_item, {}).get("name", req_item)
            return False, f"Requires {item_name}."

        req_district = cond.get("requires_district")
        discovered = set(json.loads(world_state.get("discovered_locations") or "[]"))
        discovered_districts = {
            self.locations[lid]["district_id"] for lid in discovered if lid in self.locations
        }
        if req_district and req_district not in discovered_districts:
            return False, f"Must visit {req_district} first."

        allowed_veil = cond.get("veil_states")
        if allowed_veil and world_state.get("veil_state") not in allowed_veil:
            return False, f"Only reveals itself during: {', '.join(allowed_veil)}."

        return True, "Path open."

    def _adjacent_locations(self, location_id: str) -> set[str]:
        adj: set[str] = set()
        for edge in self.world["connections"]:
            if edge["from"] == location_id:
                adj.add(edge["to"])
            elif edge.get("bidirectional") and edge["to"] == location_id:
                adj.add(edge["from"])
        return adj

    def _advance_quest_stage(self, quest_id: str, min_stage: int) -> None:
        quest = self.quests_catalog.get(quest_id)
        if not quest:
            return
        row = self._row_dict(
            "SELECT * FROM quest_progress WHERE player_id='player' AND quest_id=?", (quest_id,)
        )
        if not row:
            self._conn.execute(
                "INSERT INTO quest_progress (player_id, quest_id, status, stage_index) "
                "VALUES ('player', ?, 'active', ?)",
                (quest_id, min_stage),
            )
            return
        if row["status"] == "completed":
            return
        current_stage = int(row["stage_index"])
        if min_stage > current_stage:
            if min_stage >= len(quest["stages"]):
                self._complete_quest(quest_id)
            else:
                self._conn.execute(
                    "UPDATE quest_progress SET stage_index=?, updated_at=CURRENT_TIMESTAMP "
                    "WHERE player_id='player' AND quest_id=?",
                    (min_stage, quest_id),
                )

    def _complete_quest(self, quest_id: str) -> None:
        quest = self.quests_catalog.get(quest_id)
        if not quest:
            return
        self._conn.execute(
            "UPDATE quest_progress SET status='completed', stage_index=?, updated_at=CURRENT_TIMESTAMP "
            "WHERE player_id='player' AND quest_id=?",
            (len(quest["stages"]), quest_id),
        )
        rewards = quest.get("rewards") or {}
        if rewards.get("xp"):
            self._add_xp(int(rewards["xp"]))
        if rewards.get("echoes"):
            self._conn.execute(
                "UPDATE world_state SET echoes = echoes + ? WHERE player_id='player'",
                (int(rewards["echoes"]),),
            )
        for item_id in rewards.get("items", []):
            self._give_item(item_id, 1)
        for faction_id, delta in (rewards.get("faction") or {}).items():
            self._adjust_faction(faction_id, int(delta))

    def _add_xp(self, amount: int) -> None:
        stats = self._row_dict("SELECT level, xp FROM player_stats WHERE player_id='player'")
        new_xp = int(stats.get("xp", 0)) + amount
        new_level = 1 + (new_xp // 100)
        self._conn.execute(
            "UPDATE player_stats SET xp=?, level=?, updated_at=CURRENT_TIMESTAMP WHERE player_id='player'",
            (new_xp, new_level),
        )

    def _give_item(self, item_id: str, qty: int = 1) -> None:
        self._conn.execute(
            "INSERT INTO inventory (player_id, item_id, quantity, equipped) VALUES ('player', ?, ?, 0) "
            "ON CONFLICT(player_id, item_id) DO UPDATE SET quantity = quantity + ?",
            (item_id, qty, qty),
        )

    def _adjust_faction(self, faction_id: str, delta: int) -> None:
        row = self._row_dict(
            "SELECT reputation FROM faction_reputation WHERE player_id='player' AND faction_id=?",
            (faction_id,),
        )
        new_rep = max(-100, min(100, int(row.get("reputation", 0)) + delta))
        faction_def = next((f for f in self.factions if f["id"] == faction_id), None)
        rank = "Outsider"
        if faction_def:
            ranks = faction_def["ranks"]
            idx = min(len(ranks) - 1, max(0, (new_rep + 20) // 25))
            rank = ranks[idx]
        self._conn.execute(
            "UPDATE faction_reputation SET reputation=?, rank=?, updated_at=CURRENT_TIMESTAMP "
            "WHERE player_id='player' AND faction_id=?",
            (new_rep, rank, faction_id),
        )

    # ── Public Game State API ───────────────────────────────────────────────

    def get_state(self) -> dict[str, Any]:
        ws = self._row_dict("SELECT * FROM world_state WHERE player_id='player'")
        ps = self._row_dict("SELECT * FROM player_state WHERE player_id='player'")
        raw_stats = self._row_dict("SELECT * FROM player_stats WHERE player_id='player'")
        inv_map = self._inventory_map()
        stats = self._effective_stats(raw_stats, inv_map)
        turns_taken = int(ps.get("turns_taken", 0))

        current_loc_id = ws["current_location"]
        current_loc = self.locations[current_loc_id]
        adjacent = self._adjacent_locations(current_loc_id)
        discovered = set(json.loads(ws.get("discovered_locations") or "[]"))

        # Enrich locations with lock/unlock & adjacency info
        map_locations = []
        for loc in self.world["locations"]:
            unlocked, reason = self._check_location_access(loc, stats, ws, inv_map, turns_taken)
            if loc.get("hidden") and not unlocked and loc["id"] not in discovered:
                continue  # Canon rule: hidden paths stay unseen until earned
            map_locations.append(
                {
                    **loc,
                    "unlocked": unlocked,
                    "lock_reason": "" if unlocked else reason,
                    "is_current": loc["id"] == current_loc_id,
                    "is_adjacent": loc["id"] in adjacent,
                    "discovered": loc["id"] in discovered,
                    "settlement_name": self.settlements[loc["settlement_id"]]["name"],
                    "settlement_type": self.settlements[loc["settlement_id"]]["type"],
                }
            )

        # Relationships
        rels = {
            r["agent_a"]: r
            for r in self._rows_list("SELECT * FROM relationships WHERE agent_b='player'")
        }

        # Present NPCs at current location
        present_npcs = []
        for cid in current_loc.get("npcs", []):
            char = self.characters.get(cid)
            if not char:
                continue
            rel = rels.get(
                cid,
                {"trust": 50.0, "affection": 50.0, "suspicion": 10.0, "resistance": 70.0, "interactions": 0},
            )
            display_name = char["display_name"]
            if (
                char.get("true_name")
                and float(stats["resonance"]) >= float(char.get("true_name_min_resonance", 0.8))
                and ws["veil_state"] == "quasar_active"
            ):
                display_name = f"{char['display_name']} ({char['true_name']})"
            present_npcs.append(
                {
                    **char,
                    "display_name": display_name,
                    "voice": self.voices.get(cid, {}),
                    "relationship": {
                        "trust": round(float(rel["trust"]), 1),
                        "affection": round(float(rel["affection"]), 1),
                        "suspicion": round(float(rel["suspicion"]), 1),
                        "resistance": round(float(rel["resistance"]), 1),
                        "interactions": int(rel["interactions"]),
                    },
                    "portrait_url": f"/api/media/portrait/{char.get('portrait_hint', cid)}",
                }
            )

        # Inventory enriched
        inventory = []
        for item_id, row in inv_map.items():
            item_def = self.items_catalog.get(item_id)
            if not item_def:
                continue
            show_dq = float(stats["resonance"]) >= float(item_def.get("depth_reveal_threshold", 0.99))
            inventory.append(
                {
                    **item_def,
                    "quantity": row["quantity"],
                    "equipped": bool(row["equipped"]),
                    "active_description": item_def["dq_description"] if show_dq else item_def["prism_description"],
                }
            )

        # Quests enriched
        quest_rows = {
            r["quest_id"]: r
            for r in self._rows_list("SELECT * FROM quest_progress WHERE player_id='player'")
        }
        quests = []
        for qid, qdef in self.quests_catalog.items():
            qrow = quest_rows.get(qid)
            status = qrow["status"] if qrow else "available"
            stage_index = int(qrow["stage_index"]) if qrow else 0
            quests.append(
                {
                    **qdef,
                    "status": status,
                    "stage_index": stage_index,
                    "current_objective": (
                        qdef["stages"][stage_index]["objective"]
                        if stage_index < len(qdef["stages"])
                        else "Completed"
                    ),
                }
            )

        # Factions enriched
        rep_rows = {
            r["faction_id"]: r
            for r in self._rows_list("SELECT * FROM faction_reputation WHERE player_id='player'")
        }
        factions = [
            {
                **f,
                "reputation": int(rep_rows.get(f["id"], {}).get("reputation", 0)),
                "rank": rep_rows.get(f["id"], {}).get("rank", f["ranks"][0]),
            }
            for f in self.factions
        ]

        # Available encounters at current location
        encounters = [
            enc
            for enc in self.encounters_catalog.values()
            if enc["location_id"] == current_loc_id
            and ws["veil_state"] in enc.get("veil_states", _VEIL_CYCLE)
        ]

        # Merchant at current location
        merchant = None
        if current_loc_id in self.merchants_by_location:
            mdef = self.merchants_by_location[current_loc_id]
            merchant = {
                **mdef,
                "items": [self.items_catalog[iid] for iid in mdef["stock"] if iid in self.items_catalog],
            }

        # Recent memories / log
        recent_logs = self._rows_list(
            "SELECT id, agent_id, content, created_at FROM memories ORDER BY id DESC LIMIT 12"
        )

        return {
            "world": {
                "world_id": self.world["world_id"],
                "display_name": self.world["display_name"],
                "day_count": ws["day_count"],
                "time_of_day": ws["time_of_day"],
                "veil_state": ws["veil_state"],
                "echoes": ws["echoes"],
                "current_region": self.regions[ws["current_region"]],
                "current_settlement": self.settlements[ws["current_settlement"]],
                "current_location": current_loc,
                "active_party": json.loads(ws.get("active_party") or "[]"),
                "regions": self.world["regions"],
                "settlements": self.world["settlements"],
                "locations": map_locations,
                "connections": self.world["connections"],
            },
            "player": {
                **stats,
                "turns_taken": turns_taken,
                "dreams_seen": int(ps.get("dreams_seen", 0)),
            },
            "npcs_here": present_npcs,
            "all_characters": list(self.characters.values()),
            "inventory": inventory,
            "quests": quests,
            "factions": factions,
            "encounters": encounters,
            "merchant": merchant,
            "recent_logs": list(reversed(recent_logs)),
            "saves": self.list_saves(),
        }

    # ── Actions ─────────────────────────────────────────────────────────────

    def travel(self, location_id: str) -> dict[str, Any]:
        if location_id not in self.locations:
            raise ValueError(f"Unknown location: {location_id}")
        ws = self._row_dict("SELECT * FROM world_state WHERE player_id='player'")
        ps = self._row_dict("SELECT * FROM player_state WHERE player_id='player'")
        raw_stats = self._row_dict("SELECT * FROM player_stats WHERE player_id='player'")
        inv_map = self._inventory_map()
        stats = self._effective_stats(raw_stats, inv_map)

        target = self.locations[location_id]
        unlocked, reason = self._check_location_access(
            target, stats, ws, inv_map, int(ps.get("turns_taken", 0))
        )
        if not unlocked:
            return {"ok": False, "message": reason, "state": self.get_state()}

        settlement = self.settlements[target["settlement_id"]]
        discovered = set(json.loads(ws.get("discovered_locations") or "[]"))
        discovered.add(location_id)

        # Advance time by 1 tick on travel
        next_time_idx = (_TIME_CYCLE.index(ws["time_of_day"]) + 1) % len(_TIME_CYCLE)
        next_day = int(ws["day_count"]) + (1 if next_time_idx == 0 else 0)

        self._conn.execute(
            "UPDATE world_state SET current_region=?, current_settlement=?, current_district=?, "
            "current_location=?, time_of_day=?, day_count=?, discovered_locations=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE player_id='player'",
            (
                settlement["region_id"],
                settlement["id"],
                target["district_id"],
                location_id,
                _TIME_CYCLE[next_time_idx],
                next_day,
                json.dumps(sorted(discovered)),
            ),
        )
        self._conn.execute(
            "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('event', 'world', 'player', ?)",
            (f"Traveled to {target['name']} ({settlement['name']}).",),
        )

        # Quest progression hooks
        if location_id == "solstice_bazaar":
            self._advance_quest_stage("q_solstice_trade", 1)
        elif location_id == "stillward_cloister":
            self._advance_quest_stage("q_stilling_bell", 1)
        elif location_id == "ashveil_forges":
            self._advance_quest_stage("q_ashes_of_belief", 1)
        elif location_id == "ember_vaults_anvil":
            self._advance_quest_stage("q_ashes_of_belief", 2)
        elif location_id == "hollow_clearing":
            self._advance_quest_stage("q_nine_sisters", 1)

        self._conn.commit()
        return {"ok": True, "message": f"Arrived at {target['name']}.", "state": self.get_state()}

    def talk(self, npc_id: str, player_text: str) -> dict[str, Any]:
        if npc_id not in self.characters:
            raise ValueError(f"Unknown character: {npc_id}")
        text = player_text.strip()
        if not text:
            raise ValueError("Message cannot be empty")

        char = self.characters[npc_id]
        ws = self._row_dict("SELECT * FROM world_state WHERE player_id='player'")
        stats = self._row_dict("SELECT * FROM player_stats WHERE player_id='player'")
        veil_state = ws["veil_state"]
        res = float(stats.get("resonance", 0.35))

        # Compute emotional depth & resonance delta from input richness
        lowered = text.lower()
        deep_keywords = ("veil", "quasar", "prism", "truth", "memory", "shadow", "dream", "trust", "fear", "why")
        depth_hits = sum(1 for kw in deep_keywords if kw in lowered)
        res_delta = min(0.08, 0.02 + depth_hits * 0.015 + (0.01 if len(text) > 45 else 0.0))
        new_res = round(min(1.0, res + res_delta), 3)

        # Optional live orchestrator hook when explicitly enabled
        reply: str | None = None
        if os.environ.get("VEIL_USE_LIVE_LLM") == "1":
            try:
                from veil_loader import load_module

                orch = load_module("orchestrator", self.repo_root / "04_runtime" / "orchestrator.py")
                out = orch.run_once(agent_id=npc_id, target_agent="player", player_input=text)
                if out and out.get("output"):
                    reply = str(out["output"])
            except Exception:
                reply = None

        if not reply:
            if veil_state == "quasar_active":
                reply = (
                    f"{char['display_name']} studies you beneath the Quasar's gravity. "
                    f"\"You asked about '{text[:60]}'. Strip away the Prism's comfort—{char['hidden_function'].lower()}.\""
                )
            elif depth_hits >= 1 or new_res >= 0.55:
                reply = (
                    f"{char['display_name']} pauses, the surface smile softening into real attention. "
                    f"\"Few travelers look past the warmth so quickly. Remember: {char['surface_function']}. "
                    f"Keep listening, and the Veil will answer.\""
                )
            else:
                reply = f"{char['display_name']} answers warmly: \"{char['greeting']}\""

        # DSSM-inspired relationship update (Quasar gravity applies in quasar_active!)
        rel = self._row_dict(
            "SELECT * FROM relationships WHERE agent_a=? AND agent_b='player'", (npc_id,)
        )
        trust = float(rel.get("trust", 50.0))
        affection = float(rel.get("affection", 50.0))
        suspicion = float(rel.get("suspicion", 10.0))
        resistance = float(rel.get("resistance", 70.0))
        interactions = int(rel.get("interactions", 0)) + 1

        if veil_state == "quasar_active":
            suspicion = min(100.0, suspicion + 4.0)
            affection = max(0.0, affection - 1.5)
            trust = min(100.0, trust + 3.5)
        else:
            trust = min(100.0, trust + 2.5 + depth_hits * 0.8)
            affection = min(100.0, affection + 2.0)
            resistance = max(0.0, resistance - 2.0)

        self._conn.execute(
            "INSERT INTO relationships (agent_a, agent_b, trust, affection, suspicion, resistance, interactions, last_interaction) "
            "VALUES (?, 'player', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(agent_a, agent_b) DO UPDATE SET "
            "trust=excluded.trust, affection=excluded.affection, suspicion=excluded.suspicion, "
            "resistance=excluded.resistance, interactions=excluded.interactions, updated_at=CURRENT_TIMESTAMP",
            (npc_id, trust, affection, suspicion, resistance, interactions),
        )

        # Update player resonance, turns, XP, memory
        self._conn.execute(
            "UPDATE player_stats SET resonance=?, updated_at=CURRENT_TIMESTAMP WHERE player_id='player'",
            (new_res,),
        )
        self._conn.execute(
            "UPDATE player_state SET turns_taken = turns_taken + 1, emotional_depth = ?, "
            "last_updated=CURRENT_TIMESTAMP WHERE player_id='player'",
            (new_res,),
        )
        self._add_xp(15)
        self._conn.execute(
            "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('shared', ?, 'player', ?)",
            (npc_id, f"Player: {text} | {char['display_name']}: {reply}"),
        )

        # Quest triggers
        if npc_id == "mira":
            self._advance_quest_stage("q_first_awakening", 1)
            if new_res >= 0.45:
                self._advance_quest_stage("q_first_awakening", 3)
        elif npc_id == "kaelen_lanternwright":
            self._advance_quest_stage("q_solstice_trade", 2)
        elif npc_id == "warden":
            self._advance_quest_stage("q_stilling_bell", 2)
        elif npc_id == "rendered":
            self._advance_quest_stage("q_ashes_of_belief", 3)

        self._conn.commit()
        return {
            "ok": True,
            "npc_id": npc_id,
            "speaker": char["display_name"],
            "reply": reply,
            "resonance_delta": round(res_delta, 3),
            "veil_state": veil_state,
            "state": self.get_state(),
        }

    def advance_veil(self) -> dict[str, Any]:
        ws = self._row_dict("SELECT * FROM world_state WHERE player_id='player'")
        next_veil = _VEIL_CYCLE[(_VEIL_CYCLE.index(ws["veil_state"]) + 1) % len(_VEIL_CYCLE)]
        next_time_idx = (_TIME_CYCLE.index(ws["time_of_day"]) + 1) % len(_TIME_CYCLE)
        next_day = int(ws["day_count"]) + (1 if next_time_idx == 0 else 0)

        self._conn.execute(
            "UPDATE world_state SET veil_state=?, time_of_day=?, day_count=?, updated_at=CURRENT_TIMESTAMP "
            "WHERE player_id='player'",
            (next_veil, _TIME_CYCLE[next_time_idx], next_day),
        )
        self._conn.execute(
            "UPDATE player_state SET veil_state=?, last_updated=CURRENT_TIMESTAMP WHERE player_id='player'",
            (next_veil,),
        )
        self._conn.execute(
            "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('event', 'veil', 'player', ?)",
            (f"The Veil shifted to {next_veil.replace('_', ' ')} ({_TIME_CYCLE[next_time_idx]}).",),
        )
        self._conn.commit()
        return {"ok": True, "veil_state": next_veil, "state": self.get_state()}

    def buy_item(self, item_id: str) -> dict[str, Any]:
        item = self.items_catalog.get(item_id)
        if not item:
            raise ValueError(f"Unknown item: {item_id}")
        ws = self._row_dict("SELECT * FROM world_state WHERE player_id='player'")
        merchant = self.merchants_by_location.get(ws["current_location"])
        if not merchant or item_id not in merchant["stock"]:
            return {"ok": False, "message": "This item is not sold here.", "state": self.get_state()}
        cost = int(item["value_echoes"])
        if int(ws["echoes"]) < cost:
            return {"ok": False, "message": f"Need {cost} Echoes (you have {ws['echoes']}).", "state": self.get_state()}

        self._conn.execute(
            "UPDATE world_state SET echoes = echoes - ? WHERE player_id='player'", (cost,)
        )
        self._give_item(item_id, 1)
        if item_id == "lantern":
            self._advance_quest_stage("q_first_awakening", 2)
        self._conn.commit()
        return {"ok": True, "message": f"Acquired {item['name']} for {cost} Echoes.", "state": self.get_state()}

    def use_or_equip_item(self, item_id: str) -> dict[str, Any]:
        item = self.items_catalog.get(item_id)
        if not item:
            raise ValueError(f"Unknown item: {item_id}")
        inv = self._inventory_map()
        if item_id not in inv:
            return {"ok": False, "message": "You do not carry this item.", "state": self.get_state()}

        if item.get("equippable"):
            new_eq = 0 if inv[item_id]["equipped"] else 1
            self._conn.execute(
                "UPDATE inventory SET equipped=? WHERE player_id='player' AND item_id=?",
                (new_eq, item_id),
            )
            msg = f"{'Equipped' if new_eq else 'Unequipped'} {item['name']}."
        else:
            effect = item.get("effect") or {}
            delta = float(effect.get("resonance_delta", 0.0))
            if delta:
                stats = self._row_dict("SELECT resonance FROM player_stats WHERE player_id='player'")
                new_res = round(min(1.0, float(stats["resonance"]) + delta), 3)
                self._conn.execute(
                    "UPDATE player_stats SET resonance=? WHERE player_id='player'", (new_res,)
                )
            self._conn.execute(
                "UPDATE inventory SET quantity = quantity - 1 WHERE player_id='player' AND item_id=?",
                (item_id,),
            )
            msg = f"Used {item['name']} (+{delta:.2f} Resonance)."

        self._conn.commit()
        return {"ok": True, "message": msg, "state": self.get_state()}

    def resolve_encounter(self, encounter_id: str, choice_id: str, seed: int | None = None) -> dict[str, Any]:
        enc = self.encounters_catalog.get(encounter_id)
        if not enc:
            raise ValueError(f"Unknown encounter: {encounter_id}")
        choice = next((c for c in enc["choices"] if c["id"] == choice_id), None)
        if not choice:
            raise ValueError(f"Unknown choice: {choice_id}")

        raw_stats = self._row_dict("SELECT * FROM player_stats WHERE player_id='player'")
        stats = self._effective_stats(raw_stats, self._inventory_map())
        attr = choice["attribute"]
        attr_val = int(stats.get(attr, 10))
        modifier = (attr_val - 10) // 2
        rng = random.Random(seed)
        roll = rng.randint(1, 20)
        total = roll + modifier
        dc = int(choice["dc"])
        success = total >= dc

        rewards = choice.get("rewards") or {}
        if success:
            if rewards.get("xp"):
                self._add_xp(int(rewards["xp"]))
            if rewards.get("echoes"):
                self._conn.execute(
                    "UPDATE world_state SET echoes = echoes + ? WHERE player_id='player'",
                    (int(rewards["echoes"]),),
                )
            if rewards.get("resonance_delta"):
                new_res = round(min(1.0, float(stats["resonance"]) + float(rewards["resonance_delta"])), 3)
                self._conn.execute(
                    "UPDATE player_stats SET resonance=? WHERE player_id='player'", (new_res,)
                )
            outcome_text = choice["success_text"]
        else:
            self._add_xp(10)
            outcome_text = choice["failure_text"]

        self._conn.execute(
            "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('event', 'trial', 'player', ?)",
            (f"{enc['title']} ({'Success' if success else 'Resisted'} {total}/{dc}): {outcome_text}",),
        )
        self._conn.commit()
        return {
            "ok": True,
            "success": success,
            "roll": roll,
            "modifier": modifier,
            "total": total,
            "dc": dc,
            "outcome_text": outcome_text,
            "state": self.get_state(),
        }

    # ── Save / Load ─────────────────────────────────────────────────────────

    def list_saves(self) -> list[dict[str, Any]]:
        return self._rows_list(
            "SELECT slot_id, label, updated_at FROM save_slots ORDER BY updated_at DESC"
        )

    def save_game(self, slot_id: str, label: str = "") -> dict[str, Any]:
        snapshot = {
            "world_state": self._row_dict("SELECT * FROM world_state WHERE player_id='player'"),
            "player_state": self._row_dict("SELECT * FROM player_state WHERE player_id='player'"),
            "player_stats": self._row_dict("SELECT * FROM player_stats WHERE player_id='player'"),
            "inventory": self._rows_list("SELECT item_id, quantity, equipped FROM inventory WHERE player_id='player'"),
            "quests": self._rows_list("SELECT quest_id, status, stage_index FROM quest_progress WHERE player_id='player'"),
            "factions": self._rows_list("SELECT faction_id, reputation, rank FROM faction_reputation WHERE player_id='player'"),
        }
        slot_label = label.strip() or f"Save {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
        self._conn.execute(
            "INSERT INTO save_slots (slot_id, label, snapshot_json, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(slot_id) DO UPDATE SET label=excluded.label, snapshot_json=excluded.snapshot_json, updated_at=CURRENT_TIMESTAMP",
            (slot_id, slot_label, json.dumps(snapshot)),
        )
        self._conn.commit()
        return {"ok": True, "slot_id": slot_id, "label": slot_label, "saves": self.list_saves()}

    def load_game(self, slot_id: str) -> dict[str, Any]:
        row = self._row_dict("SELECT snapshot_json FROM save_slots WHERE slot_id=?", (slot_id,))
        if not row:
            raise ValueError(f"Save slot not found: {slot_id}")
        snap = json.loads(row["snapshot_json"])
        ws = snap["world_state"]
        ps = snap["player_state"]
        st = snap["player_stats"]

        self._conn.execute(
            "UPDATE world_state SET current_region=?, current_settlement=?, current_district=?, "
            "current_location=?, day_count=?, time_of_day=?, veil_state=?, echoes=?, discovered_locations=?, active_party=? "
            "WHERE player_id='player'",
            (
                ws["current_region"],
                ws["current_settlement"],
                ws["current_district"],
                ws["current_location"],
                ws["day_count"],
                ws["time_of_day"],
                ws["veil_state"],
                ws["echoes"],
                ws["discovered_locations"],
                ws["active_party"],
            ),
        )
        self._conn.execute(
            "UPDATE player_state SET emotional_depth=?, turns_taken=?, unlocked_districts=?, dreams_seen=?, veil_state=? "
            "WHERE player_id='player'",
            (
                ps["emotional_depth"],
                ps["turns_taken"],
                ps["unlocked_districts"],
                ps["dreams_seen"],
                ps["veil_state"],
            ),
        )
        self._conn.execute(
            "UPDATE player_stats SET level=?, xp=?, resonance=?, clarity=?, empathy=?, resolve=?, perception=?, veil_attunement=? "
            "WHERE player_id='player'",
            (
                st["level"],
                st["xp"],
                st["resonance"],
                st["clarity"],
                st["empathy"],
                st["resolve"],
                st["perception"],
                st["veil_attunement"],
            ),
        )
        self._conn.execute("DELETE FROM inventory WHERE player_id='player'")
        for item in snap.get("inventory", []):
            self._conn.execute(
                "INSERT INTO inventory (player_id, item_id, quantity, equipped) VALUES ('player', ?, ?, ?)",
                (item["item_id"], item["quantity"], item["equipped"]),
            )
        self._conn.execute("DELETE FROM quest_progress WHERE player_id='player'")
        for q in snap.get("quests", []):
            self._conn.execute(
                "INSERT INTO quest_progress (player_id, quest_id, status, stage_index) VALUES ('player', ?, ?, ?)",
                (q["quest_id"], q["status"], q["stage_index"]),
            )
        self._conn.commit()
        return {"ok": True, "message": f"Loaded slot '{slot_id}'.", "state": self.get_state()}
