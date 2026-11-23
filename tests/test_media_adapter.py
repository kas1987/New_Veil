"""Security and resolution tests for the optional local MediaAdapter."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]


def test_media_adapter_resolves_local_and_blocks_traversal(tmp_path: Path, monkeypatch) -> None:
    media_dir = tmp_path / "portraits"
    media_dir.mkdir()
    mira_img = media_dir / "mira.png"
    mira_img.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    nested_dir = media_dir / "Adeline"
    nested_dir.mkdir()
    nested_img = nested_dir / "preview.webp"
    nested_img.write_bytes(b"RIFFfake")

    secret_outside = tmp_path / "secret.png"
    secret_outside.write_bytes(b"topsecret")

    monkeypatch.setenv("VEIL_MEDIA_DIR", str(media_dir))
    mod = load_module("veil_media_adapter", ROOT / "04_runtime" / "game_api" / "media_adapter.py")
    adapter = mod.MediaAdapter(repo_root=tmp_path)

    assert adapter.find_portrait("mira") == mira_img.resolve()
    assert adapter.find_portrait("adeline") == nested_img.resolve()
    # Path traversal must be sanitized and never resolve outside media_dir
    assert adapter.find_portrait("../secret") is None
    assert adapter.find_portrait("..\\secret") is None
    assert adapter.find_portrait("nonexistent_character_xyz") is None


def test_media_endpoint_returns_404_for_missing_portrait() -> None:
    server_mod = load_module("veil_game_server", ROOT / "04_runtime" / "game_api" / "server.py")
    client = TestClient(server_mod.create_app(db_path=":memory:"))
    resp = client.get("/api/media/portrait/definitely_not_a_real_character_99999")
    assert resp.status_code == 404

