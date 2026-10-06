"""MetaChromatic hero page package."""

from .character_catalog import card_display_fields, load_catalog
from .render import render_hero_html

__all__ = ["card_display_fields", "load_catalog", "render_hero_html"]
