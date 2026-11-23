"""FastAPI server exposing The Veil RPG engine and optional local media adapter.

Run from repository root:
    uvicorn 04_runtime.game_api.server:app --reload --port 8765
    # or:
    python 04_runtime/game_api/server.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from engine import (
    AdvanceVeil,
    Buy,
    ChooseBeat,
    Inspect,
    PlayResult,
    Resolve,
    Talk,
    ToggleParty,
    Travel,
    Use,
    VeilGameEngine,
)
from media_adapter import MediaAdapter

from veil_loader import load_module

_VOICE_MOD = load_module("veil_server_dialogue_voice", _HERE / "dialogue_voice.py")
_TTS_MOD = load_module("veil_tts_adapter", _ROOT / "15_voice" / "tts_adapter.py")
_LLM_MOD = load_module("veil_server_llm_provider", _ROOT / "04_runtime" / "llm_provider.py")
_SCORER_MOD = load_module("veil_server_scorer", _ROOT / "05_alignment" / "scorer.py")
_QUARANTINE_MOD = load_module("veil_server_quarantine", _ROOT / "05_alignment" / "quarantine.py")


class TravelRequest(BaseModel):
    location_id: str


class DialogueRequest(BaseModel):
    npc_id: str
    message: str


class ItemRequest(BaseModel):
    item_id: str


class EncounterRequest(BaseModel):
    encounter_id: str
    choice_id: str


class SaveRequest(BaseModel):
    slot_id: str
    label: str = ""


class PartyRequest(BaseModel):
    character_id: str


class PortraitBindRequest(BaseModel):
    npc_id: str
    media_key: str


class InspectRequest(BaseModel):
    object_id: str


class BeatChoiceRequest(BaseModel):
    beat_id: str
    choice: str


class VoiceSynthesizeRequest(BaseModel):
    npc_id: str
    text: str
    veil_state: str | None = None
    emotion: str | None = None
    queue: bool = False


class LLMPreviewRequest(BaseModel):
    npc_id: str
    message: str
    execute_live: bool = False


def create_app(db_path: Path | str | None = None) -> FastAPI:
    app = FastAPI(title="The Veil — RPG Game API", version="0.4.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8765",
            "http://127.0.0.1:8765",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    engine = VeilGameEngine(repo_root=_ROOT, db_path=db_path)
    media = MediaAdapter(repo_root=_ROOT)
    tts = _TTS_MOD.VeilTTSAdapter()
    app.state.engine = engine
    app.state.media = media
    app.state.tts = tts

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "world": engine.world["world_id"], "version": "0.4.0"}

    def _played(result: PlayResult) -> dict:
        return {"ok": result.ok, "message": result.message, "state": result.scene}

    @app.get("/api/game/state")
    def get_state() -> dict:
        return engine.scene()

    @app.get("/api/game/ending")
    def get_ending() -> dict:
        return engine.scene()["ending_status"]

    @app.post("/api/world/travel")
    def travel(req: TravelRequest) -> dict:
        try:
            return _played(engine.play(Travel(req.location_id)))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/world/advance-veil")
    def advance_veil() -> dict:
        result = engine.play(AdvanceVeil())
        return {"ok": result.ok, "veil_state": result.scene["world"]["veil_state"], "state": result.scene}

    @app.post("/api/world/inspect")
    def inspect_object(req: InspectRequest) -> dict:
        try:
            return _played(engine.play(Inspect(req.object_id)))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/world/beat-choice")
    def choose_beat(req: BeatChoiceRequest) -> dict:
        try:
            return _played(engine.play(ChooseBeat(req.beat_id, req.choice)))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/dialogue/turn")
    def dialogue_turn(req: DialogueRequest) -> dict:
        try:
            result = engine.play(Talk(req.npc_id, req.message))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        reply = result.reply
        return {
            "ok": result.ok,
            "npc_id": req.npc_id,
            "speaker": reply.speaker if reply else "",
            "reply": reply.text if reply else "",
            "resonance_delta": reply.resonance_delta if reply else 0,
            "cue_type": reply.cue_type if reply else "standard_harmonic",
            "signals": reply.signals if reply else {},
            "sealed_out": result.scene["player"]["resonance"] <= 0.0,
            "veil_state": result.scene["world"]["veil_state"],
            "state": result.scene,
        }

    @app.post("/api/economy/buy")
    def buy_item(req: ItemRequest) -> dict:
        try:
            return _played(engine.play(Buy(req.item_id)))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/inventory/use")
    def use_item(req: ItemRequest) -> dict:
        try:
            return _played(engine.play(Use(req.item_id)))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/encounters/resolve")
    def resolve_encounter(req: EncounterRequest) -> dict:
        try:
            result = engine.play(Resolve(req.encounter_id, req.choice_id))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if result.check is None:
            return {"ok": result.ok, "message": result.message, "state": result.scene}
        check = result.check
        return {
            "ok": result.ok,
            "success": check.success,
            "roll": check.roll,
            "modifier": check.modifier,
            "total": check.total,
            "dc": check.dc,
            "outcome_text": check.outcome_text,
            "state": result.scene,
        }

    @app.post("/api/saves/save")
    def save_game(req: SaveRequest) -> dict:
        result = engine.save(req.slot_id, req.label)
        return {
            "ok": result.ok,
            "slot_id": req.slot_id,
            "label": result.message,
            "saves": result.scene["saves"],
        }

    @app.post("/api/saves/load/{slot_id}")
    def load_game(slot_id: str) -> dict:
        try:
            result = engine.load(slot_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"ok": result.ok, "message": result.message, "state": result.scene}

    @app.get("/api/media/portrait/{character_key}")
    def get_portrait(character_key: str):
        path = media.find_portrait(character_key)
        if not path:
            raise HTTPException(status_code=404, detail="Portrait not found")
        return FileResponse(path)

    @app.get("/api/media/local-shelf")
    def list_local_shelf() -> dict:
        return {"characters": media.list_local_shelf_characters()}

    @app.post("/api/media/bind")
    def bind_portrait(req: PortraitBindRequest) -> dict:
        try:
            result = engine.bind_portrait(req.npc_id, req.media_key)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": result.ok, "npc_id": req.npc_id, "media_key": result.message, "state": result.scene}

    @app.post("/api/party/toggle")
    def toggle_party(req: PartyRequest) -> dict:
        try:
            result = engine.play(ToggleParty(req.character_id))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "ok": result.ok,
            "message": result.message,
            "party": result.scene["world"]["active_party"],
            "state": result.scene,
        }

    @app.get("/api/codex")
    def get_codex() -> dict:
        return {"entries": engine.codex()}

    @app.get("/api/runtime/status")
    def runtime_status() -> dict:
        return engine.status(shelf_count=len(media.list_local_shelf_characters(limit=100)))

    @app.post("/api/game/reset")
    def reset_game() -> dict:
        result = engine.reset_session()
        return {"ok": result.ok, "message": result.message, "state": result.scene}

    @app.get("/api/voice/profiles")
    def list_voice_profiles() -> dict:
        veil_state = engine.scene()["world"]["veil_state"]
        return {"voices": tts.list_profiles(veil_state=veil_state)}

    @app.post("/api/voice/synthesize")
    def synthesize_voice(req: VoiceSynthesizeRequest) -> dict:
        if req.npc_id not in engine.characters:
            raise HTTPException(status_code=404, detail=f"Unknown NPC: {req.npc_id}")
        veil_state = req.veil_state or engine.scene()["world"]["veil_state"]
        return tts.synthesize(
            agent_id=req.npc_id,
            text=req.text,
            veil_state=veil_state,
            emotion=req.emotion,
            queue=req.queue,
        )

    @app.get("/api/llm/status")
    def llm_status() -> dict:
        return {
            "live_llm_enabled": os.environ.get("VEIL_USE_LIVE_LLM") == "1",
            "model": _LLM_MOD.DEFAULT_MODEL,
            "base_url": _LLM_MOD.OLLAMA_BASE_URL,
            "agents_with_prompts": [
                cid for cid in engine.characters if bool(_LLM_MOD.load_system_prompt(cid))
            ],
        }

    @app.post("/api/dialogue/llm-preview")
    def preview_llm_dialogue(req: LLMPreviewRequest) -> dict:
        if req.npc_id not in engine.characters:
            raise HTTPException(status_code=404, detail=f"Unknown NPC: {req.npc_id}")
        scene = engine.scene()
        veil_state = str(scene["world"]["veil_state"])
        resonance = float(scene["player"]["resonance"])
        arcs_row = engine._row_dict("SELECT encounter_arcs FROM player_stats WHERE player_id='player'")
        arcs = json.loads(arcs_row.get("encounter_arcs") or "{}")
        npc_arcs = arcs.get("npcs") or {}
        enc = ((npc_arcs.get(req.npc_id) or {}).get("encounter")) or {}
        npc_bond = float(enc.get("npcBond", 0.0))
        stance = str(enc.get("currentStance") or "guarded")
        memory_ctx = _VOICE_MOD.collect_bounded_memory(engine._conn, req.npc_id, npc_arcs)
        user_prompt = _VOICE_MOD.build_live_llm_prompt(
            beats_pack=engine.dialogue_beats,
            npc_id=req.npc_id,
            location_name=scene["world"]["current_location"]["name"],
            veil_state=veil_state,
            resonance=resonance,
            npc_bond=npc_bond,
            stance=stance,
            cue_type="preview",
            memory_ctx=memory_ctx,
            player_text=req.message,
        )
        system_prompt = _LLM_MOD.load_system_prompt(req.npc_id)
        live_result: dict | None = None
        if req.execute_live:
            candidate = _LLM_MOD.generate_agent_output(req.npc_id, user_prompt=user_prompt)
            text = str(candidate.get("output") or "").strip() if isinstance(candidate, dict) else ""
            score_dict = _SCORER_MOD.score_text(
                text, canon_refs=["VEIL-001"], agent_id=req.npc_id
            ).to_dict()
            quarantined, reason = _QUARANTINE_MOD.should_quarantine(
                score_dict, veil_state=veil_state
            )
            live_result = {
                **candidate,
                "quarantined": quarantined,
                "quarantine_reason": reason,
                "alignment": score_dict,
            }
        return {
            "ok": True,
            "npc_id": req.npc_id,
            "system_prompt_loaded": bool(system_prompt),
            "system_prompt_excerpt": system_prompt[:240],
            "user_prompt": user_prompt,
            "live_result": live_result,
        }

    # Serve built Vite client if present
    dist_dir = _ROOT / "07_ui" / "game_client" / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="game_client")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
