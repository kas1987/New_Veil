"""Optional local media & portrait adapter for The Veil RPG.

Resolves character portraits from operator-local directories (such as
``VEIL_MEDIA_DIR`` or the gitignored ``90_intake/from_rly_shelf/RLY_Thot``)
without ever committing binary assets or machine paths to the repository.
"""

from __future__ import annotations

import os
from pathlib import Path

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


class MediaAdapter:
    """Safely discovers local character portrait files if present on disk."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self._roots = self._discover_roots()

    def _discover_roots(self) -> list[Path]:
        roots: list[Path] = []
        env_dir = os.environ.get("VEIL_MEDIA_DIR", "").strip()
        if env_dir:
            p = Path(env_dir).expanduser()
            if p.is_dir():
                roots.append(p.resolve())

        intake_rly = self.repo_root / "90_intake" / "from_rly_shelf" / "RLY_Thot"
        if intake_rly.is_dir():
            roots.append(intake_rly.resolve())

        local_portraits = self.repo_root / "07_ui" / "hero" / "portraits"
        if local_portraits.is_dir():
            roots.append(local_portraits.resolve())

        return roots

    def find_portrait(self, character_key: str) -> Path | None:
        """Return a safe, resolved image path for ``character_key`` if available."""
        key = "".join(ch for ch in character_key.lower() if ch.isalnum() or ch in ("_", "-"))
        if not key:
            return None

        for root in self._roots:
            # 1. Direct file match in root
            for ext in _IMAGE_EXTS:
                candidate = (root / f"{key}{ext}").resolve()
                if candidate.is_file() and candidate.is_relative_to(root):
                    return candidate

            # 2. Subfolder match (case-insensitive, e.g. RLY_Thot/Adeline/*.png)
            try:
                for entry in root.iterdir():
                    if not entry.is_dir():
                        continue
                    if entry.name.lower() == key or key in entry.name.lower():
                        for img in sorted(entry.rglob("*")):
                            if img.is_file() and img.suffix.lower() in _IMAGE_EXTS:
                                resolved = img.resolve()
                                if resolved.is_relative_to(root):
                                    return resolved
            except OSError:
                continue

        return None

    def list_local_shelf_characters(self, limit: int = 24) -> list[dict]:
        """List optional local intake shelf characters for portrait binding."""
        intake_rly = self.repo_root / "90_intake" / "from_rly_shelf" / "RLY_Thot"
        if not intake_rly.is_dir():
            return []
        found: list[dict] = []
        try:
            for entry in sorted(intake_rly.iterdir(), key=lambda p: p.name.lower()):
                if not entry.is_dir() or entry.name.startswith("."):
                    continue
                found.append(
                    {
                        "id": entry.name.lower(),
                        "display_name": entry.name,
                        "source": "local_rly_shelf",
                        "portrait_url": f"/api/media/portrait/{entry.name.lower()}",
                    }
                )
                if len(found) >= limit:
                    break
        except OSError:
            return []
        return found
