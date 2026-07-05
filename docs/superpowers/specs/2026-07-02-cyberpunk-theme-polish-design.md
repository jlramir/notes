# Cyberpunk 2077 Theme Polish — Design

**Date:** 2026-07-02 (scope revised 2026-07-03)
**Branch:** `frontend/updates`
**Status:** Approved (scope tightened after reviewing current code)

## Goal

Make the `cyberpunk` journal index's **background** evoke the in-game Cyberpunk 2077 journal screen. The current background reads as flat/plain; the reference (`~/Desktop/cyberpunk.png`) has a warm maroon field with a corner vignette, a faint mottled texture, a magenta→red gradient bleed at the top edge, and a bright glowing-red scrollbar.

## Context: what already exists

A prior merged pass (PR #1) already implemented much of the "game aesthetic." **These are done and out of scope:**
- Neon glow (`text-shadow`) on tabs, titles, headings, search, stat values.
- Angular `clip-path` corners on section headers, note items, thumbnails, copy buttons.
- A teal secondary accent (option b) on the NOTES stat, active note titles, `h1`, code borders.
- Per-panel scanline texture (`repeating-linear-gradient`) on the sidebar, content panel, and note thumbnails.

## Scope — the three real gaps

1. **Rich background** on `body`: keep the maroon base gradient but add (a) a corner **vignette** and (b) a low-opacity **mottled noise texture**, so the field has depth instead of a flat gradient.
2. **Top magenta→red gradient strip**: a thin decorative gradient bleeding down from the very top edge, under/over the topbar's existing red bottom border.
3. **Glowing red scrollbar**: replace the flat dark `#2a0808` scrollbar thumbs on `.cp-sidebar` and `.cp-content` with a brighter red thumb carrying a `box-shadow` glow, matching the reference's bright vertical bar.

**Out of scope:** everything listed under "what already exists"; other themes; the generic card-grid index; standalone note pages; build-pipeline changes; any raster/binary assets.

## Constraints

- **Zero binary assets.** The noise texture is an inline SVG `data-URI` (via CSS `background-image`), not an image file. This keeps the repo self-contained and works with the existing `build` (which copies only `*.css`).
- **Readability first.** Vignette, noise, and gradient strip stay low-opacity; body and note text must remain comfortably legible against the new background.
- **Additive, structure-preserving.** Only touch the CSS involved in the three gaps. No HTML structure or JS behavior changes. Keep existing class names and selectors.

## Where changes live

All three changes are in the inline `<style>` block of `notes_app/builder.py`, function `_write_index_cyberpunk`:
- **Background** — `body { background: ... }` at `builder.py:279-288`. Layer the vignette (`radial-gradient`) and SVG-noise (`url("data:image/svg+xml,...")`) on top of the existing linear gradient (CSS supports multiple comma-separated background layers).
- **Top gradient strip** — add a fixed/absolute decorative element or a `background`/`border-image` on `.cp-topbar` (`builder.py:291-298`).
- **Scrollbar** — `::-webkit-scrollbar-thumb` rules at `builder.py:434` (sidebar) and `builder.py:602` (content); add a `box-shadow` glow and brighter red, plus a Firefox `scrollbar-color` fallback on the two scroll containers.

`themes/cyberpunk.css` (`:root` vars) is not required for these changes but may hold a new `--scrollbar-glow` value if it keeps the inline CSS tidy.

## Testing

- `tests/test_builder_cyberpunk.py` must continue to pass.
- Add lightweight assertions that the three markers appear in generated `index.html`: the SVG-noise `data:image/svg+xml` background layer, the top gradient strip element/rule, and a glowing `::-webkit-scrollbar-thumb` (e.g. asserting `box-shadow` appears in a scrollbar rule).
- Manual verification: create a couple of sample notes across folders, run `uv run python main.py build`, open `output/index.html`, and confirm the background has visible depth (vignette + texture), the top strip renders, the scrollbar glows red, and all text stays readable.

## Success criteria

- The journal index background no longer looks flat: visible corner vignette + subtle texture, a top magenta→red bleed, and a glowing-red scrollbar — matching the reference's mood.
- Text remains fully legible; no layout breakage; all tests pass; no binary assets added; `build` unchanged.
