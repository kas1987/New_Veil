"""HTML renderer for MetaChromatic hero page (PDR-0002)."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
CSS_PATH = ROOT / "07_ui" / "metachromatic_design_system" / "hero_page.css"


def _esc(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(html.escape(str(item)) for item in value)
    return html.escape(str(value))


def _render_card(card: dict[str, Any]) -> str:
    slug = _esc(card.get("model_slug", ""))
    name = _esc(card.get("character_name") or card.get("model_name") or slug)
    summary = _esc(card.get("summary", ""))
    tier = _esc(card.get("aurora_tier", "—"))
    quadrant = _esc(card.get("aurora_quadrant", "—"))
    archetype = _esc(card.get("archetype", "—"))
    emotional = _esc(card.get("emotional_archetype", "—"))
    tags = _esc(card.get("identity_tags", []))
    anchors = _esc(card.get("visual_anchors", []))
    return f"""
<article class="mc-hero-card" data-slug="{slug}">
  <div class="mc-hero-card__glow"></div>
  <header class="mc-hero-card__head">
    <h3>{name}</h3>
    <code class="mc-hero-card__slug">{slug}</code>
  </header>
  <p class="mc-hero-card__summary">{summary}</p>
  <dl class="mc-hero-card__meta">
    <div><dt>aurora_tier</dt><dd>{tier}</dd></div>
    <div><dt>aurora_quadrant</dt><dd>{quadrant}</dd></div>
    <div><dt>archetype</dt><dd>{archetype}</dd></div>
    <div><dt>emotional_archetype</dt><dd>{emotional}</dd></div>
    <div><dt>identity_tags</dt><dd>{tags}</dd></div>
    <div><dt>visual_anchors</dt><dd>{anchors}</dd></div>
  </dl>
  <footer class="mc-hero-card__actions">
    <span class="mc-hero-card__cta">Attune</span>
    <span class="mc-hero-card__cta mc-hero-card__cta--ghost">Inspect</span>
  </footer>
</article>
"""


def render_hero_html(
    cards: list[dict[str, Any]],
    *,
    bg_opacity: float = 0.35,
    title: str = "MetaChromatic Portal",
    subtitle: str = "Choose a persona pathway. Metadata drives the route toward the Prismatic Veil.",
) -> str:
    opacity = max(0.05, min(0.85, float(bg_opacity)))
    css = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""
    card_html = "".join(_render_card(card) for card in cards) or "<p class='mc-hero-empty'>No character cards loaded.</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>
<section class="mc-hero" style="--hero-bg-opacity: {opacity:.2f};">
  <div class="mc-hero__atmosphere" aria-hidden="true"></div>
  <div class="mc-hero__veil-overlay" aria-hidden="true"></div>
  <div class="mc-hero__content">
    <header class="mc-hero__header">
      <p class="mc-hero__eyebrow">Viel Small Town · Observatory</p>
      <h1>{html.escape(title)}</h1>
      <p class="mc-hero__subtitle">{html.escape(subtitle)}</p>
    </header>
    <div class="mc-hero__grid">{card_html}</div>
  </div>
</section>
</body>
</html>
"""
