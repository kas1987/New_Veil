#!/usr/bin/env python3
"""Public CI gate for New_Veil scaffold integrity."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "REPO_STATUS.md",
    "CHROMATIC_TREES.md",
    "PROJECT_INDEX.json",
    "JOIN_FROM.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    ".gitignore",
    "09_registry/09.03_WORKTREE_MAPS/09.03.01_WORKTREE_MAP.json",
    "90_intake/sources.example.json",
]

REQUIRED_DIRS = [
    "00_charter",
    "00_harness",
    "01_districts",
    "03_memory",
    "04_runtime",
    "05_alignment",
    "06_logs",
    "07_ui",
    "09_registry",
    "10_canon",
    "11_world",
    "12_metaphysics",
    "13_agents",
    "14_psychometrics",
    "15_voice",
    "90_intake",
    "99_archive",
    "design",
    "docs",
    "scripts",
    "tests",
    ".github/workflows",
]

# High-confidence secret-ish patterns (fail CI if found in tracked text).
SECRET_RE = re.compile(
    r"(?i)("
    r"ghp_[A-Za-z0-9]{20,}"
    r"|gho_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"
    r")"
)

# Discourage committing operator machine roots in tracked JSON/docs (allow examples).
ABS_PATH_RE = re.compile(r"(?i)(?:[A-Z]:\\\\|/home/|/Users/)[^\s\"']+")

SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".sqlite", ".db"}
SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}


def iter_text_files() -> list[Path]:
    out: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        # Local-only intake dumps must not be tracked; if present on disk, skip scan noise.
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("90_intake/from_"):
            continue
        if rel == "90_intake/sources.json":
            continue
        out.append(path)
    return out


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"missing file: {rel}")

    for rel in REQUIRED_DIRS:
        if not (ROOT / rel).is_dir():
            errors.append(f"missing dir: {rel}")

    index_path = ROOT / "PROJECT_INDEX.json"
    map_path = ROOT / "09_registry/09.03_WORKTREE_MAPS/09.03.01_WORKTREE_MAP.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        worktree = json.loads(map_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CI wants the message
        errors.append(f"JSON load failed: {exc}")
        index, worktree = {}, {}

    if index.get("github") != "kas1987/New_Veil":
        errors.append("PROJECT_INDEX.json github must be kas1987/New_Veil")
    if "promoted_planes" not in index:
        errors.append("PROJECT_INDEX.json missing promoted_planes")
    if "planes" not in worktree:
        errors.append("worktree map missing planes")

    # Canon / runtime anchors expected after promotions
    for rel in (
        "10_canon/IMMUTABLE_CANON.md",
        "10_canon/CANON_INDEX.json",
        "00_charter/VEIL_TOWN_CHARTER.md",
        "12_metaphysics/THE_VEIL.md",
        "13_agents/mira/profile.json",
        "01_districts/unlock_engine.py",
        "design/veil_motif_design_doc.md",
        "03_memory/schema.sql",
        "03_memory/memory_router.py",
        "04_runtime/orchestrator.py",
        "04_runtime/veil_core/prism.py",
        "05_alignment/scorer.py",
        "05_alignment/rules.json",
        "07_ui/gradio_app.py",
        "07_ui/metachromatic_design_system/SKILL.md",
        "veil_loader.py",
    ):
        if not (ROOT / rel).is_file():
            errors.append(f"missing promoted keeper: {rel}")

    for path in iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SECRET_RE.search(text):
            errors.append(f"possible secret material: {path.relative_to(ROOT).as_posix()}")
        rel = path.relative_to(ROOT).as_posix()
        if rel.endswith("sources.example.json"):
            continue
        if ABS_PATH_RE.search(text) and rel.endswith((".json", ".md")):
            # Allow mention of pattern D:\\.30_Veil as documentation of local root only in JOIN_FROM examples? Prefer fail.
            if "sources.example.json" in rel:
                continue
            errors.append(f"absolute machine path in tracked file: {rel}")

    if errors:
        print("Scaffold check FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Scaffold check OK")
    print(f"  root: {ROOT}")
    print(f"  promoted_planes: {', '.join(index.get('promoted_planes', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
