# MetaChromatic — Mobile UI Kit

Interactive recreation of the MetaChromatic mobile PWA (the `apps/metachromatic-mobile` app inside `Image-Prism`). Open `index.html` and tap the bottom-nav tabs to switch between screens.

## Screens
- **Generate** — checkpoint picker, character chips, positive/negative prompt, primary gradient button, progress bar with cyan glow.
- **Models** — searchable 2-col grid of model cards with bio-image thumb + score tier pill. Tap a card → detail view.
- **Review** — single-item review stack with 5-star rating and Keep / Reject.
- **Outputs / Tag / Export / Audio** — placeholders wired to the nav.

## Files
| File | Purpose |
|---|---|
| `index.html` | App shell inside an iPhone frame, routes tabs to screens. |
| `tokens.jsx` | Single source of truth for color / gradient / radius / shadow values. |
| `Primitives.jsx` | `GlassPanel`, `GlassCard`, `Button`, `Input`, `Label`, `Pill`, `ProgressBar`, `Skeleton`. |
| `NavBar.jsx` | 7-slot bottom nav with cyan glow active tab + status dot. |
| `ModelGallery.jsx` | Search + 2-col card grid. |
| `Generator.jsx` | Prompt panels + chip pickers + submit flow. |
| `ReviewQueue.jsx` | Swipe-style review with star ratings. |
| `ios-frame.jsx` | Device bezel starter. |

## Re-creation notes
Layout, spacing, glass recipes, cyan accent, and the 7-tab nav are lifted from `apps/metachromatic-mobile/src/components/NavBar.tsx`, `screens/ModelGallery.tsx`, `screens/Generator.tsx`, and the `index.css` glass utility classes. Model thumbnails are synthesized radial gradients (no real scraped images in this sandbox).
