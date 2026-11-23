---
status: accepted
---

# Typed Session Interface Boundary Below FastAPI

`VeilGameEngine` exposes a framework-free Python session interface—`scene()`, `play(action)` (`Travel`, `Talk`, `AdvanceVeil`, `Buy`, `Use`, `Resolve`, `ToggleParty`), `save()`, `load()`, `bind_portrait()`, `codex()`, and `reset_session()`—while FastAPI (`04_runtime/game_api/server.py`) acts strictly as a thin HTTP transport adapter. All world rules, quest hooks, drift ticks, and Canon checks live inside the engine rather than route handlers.

## Considered Options

- **Logic inside FastAPI routes:** Requires spinning up ASGI test clients for every simulation and forces psychometric harnesses through HTTP serialization overhead.

## Consequences

- Isolated `:memory:` harnesses (`eval_runner.py` and `pytest` suites) run full 25-turn trajectories directly against the authoritative engine in milliseconds.
- HTTP response shapes remain replaceable without rewriting progression or narrative rules.
