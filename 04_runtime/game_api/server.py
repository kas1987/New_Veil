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

from engine import VeilGameEngine  # noqa: E402
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

    @app.get("/api/game/state")
    def get_state() -> dict:
        return engine.get_state()

    @app.get("/api/game/ending")
    def get_ending() -> dict:
        return engine.evaluate_ending()

    @app.post("/api/world/travel")
    def travel(req: TravelRequest) -> dict:
        try:
            return engine.travel(req.location_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/world/advance-veil")
    def advance_veil() -> dict:
        return engine.advance_veil()

    @app.post("/api/dialogue/turn")
    def dialogue_turn(req: DialogueRequest) -> dict:
        try:
            return engine.talk(req.npc_id, req.message)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/economy/buy")
    def buy_item(req: ItemRequest) -> dict:
        try:
            return engine.buy_item(req.item_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/inventory/use")
    def use_item(req: ItemRequest) -> dict:
        try:
            return engine.use_or_equip_item(req.item_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/encounters/resolve")
    def resolve_encounter(req: EncounterRequest) -> dict:
        try:
            return engine.resolve_encounter(req.encounter_id, req.choice_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/saves/save")
    def save_game(req: SaveRequest) -> dict:
        return engine.save_game(req.slot_id, req.label)

    @app.post("/api/saves/load/{slot_id}")
    def load_game(slot_id: str) -> dict:
        try:
            return engine.load_game(slot_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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
            return engine.bind_portrait(req.npc_id, req.media_key)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/party/toggle")
    def toggle_party(req: PartyRequest) -> dict:
        try:
            return engine.toggle_party(req.character_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/codex")
    def get_codex() -> dict:
        return {"entries": engine.get_codex()}

    @app.get("/api/runtime/status")
    def runtime_status() -> dict:
        return engine.runtime_status(shelf_count=len(media.list_local_shelf_characters(limit=100)))

    # Serve built Vite client if present
    dist_dir = _ROOT / "07_ui" / "game_client" / "dist"
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="game_client")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
