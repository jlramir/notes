# Cyberpunk 2077 Theme Polish — Design

**Date:** 2026-07-02
**Branch:** `frontend/updates`
**Status:** Approved (pending spec review)

## Goal

Polish the existing `cyberpunk` theme's journal index so it more closely evokes the in-game Cyberpunk 2077 journal/shard screen. The current implementation is structurally faithful (two-panel layout, topbar tabs, collapsible folder sections, file list + reading pane) but visually flat: a near-black background, no depth, no glow, square corners, and default scrollbars.

The reference is the in-game journal screen (`~/Desktop/cyberpunk.png`): a warm maroon textured background with a corner vignette, a magenta→red gradient bleed at the top edge, neon-red accents, angular HUD corners, faint scanline texture, a glowing red scrollbar, and subtle teal/cyan secondary accents (LEVEL / STREET CRED chips).

## Scope

**In scope:** visual polish of the cyberpunk journal *index* page only. No layout/structure changes, no new features, no JS behavior changes beyond styling hooks.

**Out of scope:** other themes; the generic card-grid index; per-note standalone pages (for cyberpunk the reading pane is inline, so standalone note pages are secondary); any raster image assets; build-pipeline changes.

## Constraints

- **Zero binary assets.** Background texture is produced with layered CSS gradients + an inline SVG `data-URI` noise overlay. This keeps the repo self-contained and works with the existing `build` (which copies only `*.css`).
- **Readability first.** Texture, scanlines, and vignette stay low-opacity; body text must remain comfortably legible.
- **Keep the existing structure and class names.** Changes are additive CSS on existing selectors.

## Where changes live

- **`themes/cyberpunk.css`** — the `:root` custom properties (palette). Add/adjust:
  - `--bg-primary` → warmer near-black maroon (from `#0a0808` toward a dark maroon).
  - New `--accent-teal` secondary accent (e.g. a muted cyan) for small elements.
  - New `--glow-color` (red glow tint) for shadows.
- **`notes_app/builder.py`, `_write_index_cyberpunk` inline `<style>`** — all layout-level styling for the journal index lives here; this is where the background layers, glow, clip-path, scanline overlay, scrollbar, and micro-interactions are applied.

## Design

### Part 1 — Background & palette

1. **Layered `body` background:**
   - Base: dark maroon vertical gradient (slightly lifted toward top-center).
   - Vignette: `radial-gradient` darkening the corners/edges.
   - Texture: a low-opacity inline SVG noise/diagonal-scratch `data-URI` overlay (via a `body::before` fixed layer so it doesn't scroll or intercept clicks — `pointer-events: none`).
2. **Top magenta→red gradient strip:** a thin gradient bleeding down from the top edge under `.cp-topbar` (implemented as a `.cp-topbar` top border-image or a fixed `::before` bar). Purely decorative.
3. **Sidebar/content separation:** keep the current subtle `--border-color` line — no glow (glow is reserved for the scrollbar, which is the bright vertical element in the reference).
4. **Palette — option (b), a touch of teal:** introduce `--accent-teal` used *sparingly* on small secondary elements only (e.g. `.cp-note-date`, section count/subtitle text) so the red identity stays dominant while nodding at the game's cyan chips.

### Part 2 — Polish items

- **Neon glow:** `text-shadow` glow on red accents — `.cp-tab.active`, `.cp-note-heading`, `.cp-section-title`; `box-shadow`/glow on `.cp-note-item.active` and `.cp-search:focus`. Tuned subtle, using `--glow-color`.
- **Angular clip-path corners:** notched/beveled corners (CP2077 HUD shape) via `clip-path` on `.cp-note-icon`, `.cp-tag`, and note/section panels where it reads well. Applied conservatively to avoid clipping text.
- **Scanline / CRT overlay:** a full-page fixed `body::after` layer using a `repeating-linear-gradient` of faint horizontal lines at very low opacity, `pointer-events: none`. No animation initially (flicker can be added later if desired).
- **Glowing red scrollbar:** style `::-webkit-scrollbar` on `.cp-sidebar` and `.cp-content` — thin track, red thumb with a `box-shadow` glow (this is the bright vertical element identified in the reference). Include a `scrollbar-color` fallback for Firefox.
- **Micro-interactions:** smoother `transition`s on hover/selection for `.cp-note-item`; a subtle glitch shimmer on hover (small, fast transform/opacity nudge). Keep motion minimal.

## Testing

- `tests/test_builder_cyberpunk.py` must continue to pass. Update it if any assertions depend on exact style strings.
- Add lightweight assertions that the polished markers are present in generated HTML (e.g. the noise/scanline layers, the teal accent variable usage, `::-webkit-scrollbar` styling) so regressions are caught.
- Manual verification: create a couple of sample notes across folders, run `uv run python main.py build`, open `output/index.html`, and confirm the background, glow, corners, scanlines, teal accents, and scrollbar render and remain readable.

## Success criteria

- The cyberpunk journal index visibly matches the reference's mood: warm maroon textured background, top gradient bleed, neon-red glow, angular corners, faint scanlines, glowing red scrollbar, subtle teal accents.
- Text remains fully legible; no layout breakage; all tests pass; no binary assets added; `build` unchanged.
