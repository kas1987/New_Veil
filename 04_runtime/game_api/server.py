"""FastAPI server exposing The Veil RPG engine and optional local media adapter.

Run from repository root:
    uvicorn 04_runtime.game_api.server:app --reload --port 8765
    # or:
    python 04_runtime/game_api/server.py
"""

from __future__ import annotations

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

from engine import (  # noqa: E402
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
from media_adapter import MediaAdapter  # noqa: E402


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
    app.state.engine = engine
    app.state.media = media

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

    # Serve built Vite client if present
    dist_dir = _ROOT / "07_ui" / "game_client" / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="game_client")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
