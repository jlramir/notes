# Cyberpunk Theme Background Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the cyberpunk journal index a richer, game-accurate background — corner vignette + subtle noise texture, a top magenta→red gradient bleed, and a glowing-red scrollbar.

**Architecture:** All styling for the cyberpunk index lives in one inline `<style>` block inside `notes_app/builder.py`'s `_write_index_cyberpunk` function. The three changes are additive CSS edits to that block: layered `background` on `body`, a decorative gradient element on the topbar, and upgraded `::-webkit-scrollbar-thumb` rules on the two scroll containers. Tests assert the generated `index.html` contains the new CSS markers.

**Tech Stack:** Python 3.12 (stdlib only), pytest, `uv`, CSS (multi-layer backgrounds, inline SVG `data-URI`, `-webkit-scrollbar`).

## Global Constraints

- **Python ≥ 3.12**; run everything via `uv run` (system python is older).
- **Zero binary/third-party assets** — noise texture must be an inline SVG `data:image/svg+xml,...` background layer, not an image file.
- **Additive & structure-preserving** — only edit CSS for the three gaps; no HTML structure or JS behavior changes; keep existing class names.
- **Readability first** — new layers stay low-opacity; body/note text must remain legible.
- **The inline style uses `str.format`-style doubled braces** (`{{` / `}}`) because the whole block is inside an f-string. Every literal `{` or `}` you add inside the `_write_index_cyberpunk` f-string MUST be doubled. A `%`-free SVG `data-URI` avoids extra escaping headaches.
- Commit after each task.

---

### Task 1: Rich `body` background — vignette + noise texture

**Files:**
- Modify: `notes_app/builder.py` (the `body {{ ... }}` rule at ~`279-288`, inside `_write_index_cyberpunk`)
- Test: `tests/test_builder_cyberpunk.py`

**Interfaces:**
- Consumes: existing `build(notes_dir, themes_dir, output_dir)` and the test helpers `_setup` / `_make_note` already in `tests/test_builder_cyberpunk.py`.
- Produces: generated `output/index.html` now contains a `data:image/svg+xml` background layer and a `radial-gradient(` vignette in the `body` rule. No new Python symbols.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_builder_cyberpunk.py`:

```python
def test_cyberpunk_body_has_vignette_and_noise(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Bg Note", "work", [])
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    # vignette: a radial gradient darkening the corners
    assert "radial-gradient(" in html
    # texture: inline SVG noise layer (no binary asset)
    assert "data:image/svg+xml" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_builder_cyberpunk.py::test_cyberpunk_body_has_vignette_and_noise -v`
Expected: FAIL — `assert "radial-gradient(" in html` (neither marker present yet).

- [ ] **Step 3: Implement the layered background**

In `notes_app/builder.py`, replace the `body` rule's `background:` line (currently a single `linear-gradient(...)` at ~line 280) with three comma-separated layers. Because this text is inside the `_write_index_cyberpunk` f-string, the CSS braces are already handled by the surrounding rule — you are only editing the `background:` property value, which contains no braces. Use this exact value:

```css
      background:
        radial-gradient(ellipse 120% 90% at 50% 0%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E"),
        linear-gradient(180deg, #220808 0%, #140404 20%, #0c0404 45%, #080404 100%);
```

Notes:
- The `radial-gradient` is the vignette (transparent center → dark corners).
- The `url("data:image/svg+xml,...")` is the noise texture; `%23` is an encoded `#` and `%3C`/`%3E` are `<`/`>` so the SVG needs no external file. It contains no `{`/`}`, so no f-string escaping is needed.
- The original `linear-gradient` stays as the bottom layer so the maroon base is preserved.

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_builder_cyberpunk.py::test_cyberpunk_body_has_vignette_and_noise -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite to confirm nothing broke**

Run: `uv run pytest -q`
Expected: all tests pass (previous count + 1).

- [ ] **Step 6: Commit**

```bash
git add notes_app/builder.py tests/test_builder_cyberpunk.py
git commit -m "feat: add vignette + noise texture to cyberpunk background"
```

---

### Task 2: Top magenta→red gradient strip

**Files:**
- Modify: `notes_app/builder.py` (add a `.cp-topbar::before` rule near the `.cp-topbar` rule at ~`291-298`, inside `_write_index_cyberpunk`)
- Test: `tests/test_builder_cyberpunk.py`

**Interfaces:**
- Consumes: existing build + test helpers.
- Produces: generated `index.html` contains a `.cp-topbar::before` selector and a `linear-gradient` using a magenta stop (`#ff00`-ish). No new Python symbols.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_builder_cyberpunk.py`:

```python
def test_cyberpunk_has_top_gradient_strip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert ".cp-topbar::before" in html
    # magenta stop present in the strip gradient
    assert "#e0006a" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_builder_cyberpunk.py::test_cyberpunk_has_top_gradient_strip -v`
Expected: FAIL — `.cp-topbar::before` not found.

- [ ] **Step 3: Implement the strip**

In `notes_app/builder.py`, immediately AFTER the closing `}}` of the `.cp-topbar {{ ... }}` rule (~line 298), insert this new rule. Note the doubled braces `{{` / `}}` — required because this is inside the f-string:

```css
    .cp-topbar {{ position: relative; }}
    .cp-topbar::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, #e0006a 0%, #cc2020 45%, rgba(204,32,32,0) 100%);
      box-shadow: 0 0 10px rgba(224,0,106,0.5);
      pointer-events: none;
    }}
```

(The extra `.cp-topbar {{ position: relative; }}` ensures the absolutely-positioned `::before` anchors to the topbar. It is additive and does not conflict with the existing `.cp-topbar` rule.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_builder_cyberpunk.py::test_cyberpunk_has_top_gradient_strip -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add notes_app/builder.py tests/test_builder_cyberpunk.py
git commit -m "feat: add magenta->red top gradient strip to cyberpunk topbar"
```

---

### Task 3: Glowing red scrollbar

**Files:**
- Modify: `notes_app/builder.py` (the `.cp-sidebar::-webkit-scrollbar-*` rules at ~`432-434` and `.cp-content::-webkit-scrollbar-*` rules at ~`600-602`, plus `scrollbar-color` on `.cp-sidebar` ~`418` and `.cp-content` ~`588`, inside `_write_index_cyberpunk`)
- Test: `tests/test_builder_cyberpunk.py`

**Interfaces:**
- Consumes: existing build + test helpers.
- Produces: generated `index.html` contains a `::-webkit-scrollbar-thumb` rule with a `box-shadow` glow and a brighter red (`#cc2020`). No new Python symbols.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_builder_cyberpunk.py`:

```python
def test_cyberpunk_scrollbar_glows_red(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    # find the scrollbar-thumb block and confirm it glows
    idx = html.find("::-webkit-scrollbar-thumb")
    assert idx != -1
    thumb_region = html[idx:idx + 200]
    assert "box-shadow" in thumb_region
    assert "#cc2020" in thumb_region
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_builder_cyberpunk.py::test_cyberpunk_scrollbar_glows_red -v`
Expected: FAIL — current thumb is `#2a0808` with no `box-shadow`.

- [ ] **Step 3: Widen the scrollbar and make the thumb glow**

In `notes_app/builder.py`, update BOTH scrollbar groups (sidebar ~432-434 and content ~600-602). Replace each group with the following (doubled braces required — inside the f-string):

Sidebar group:
```css
    .cp-sidebar::-webkit-scrollbar {{ width: 6px; }}
    .cp-sidebar::-webkit-scrollbar-track {{ background: #0a0808; }}
    .cp-sidebar::-webkit-scrollbar-thumb {{ background: #cc2020; box-shadow: 0 0 8px rgba(204,32,32,0.8), 0 0 16px rgba(255,48,32,0.4); }}
```

Content group:
```css
    .cp-content::-webkit-scrollbar {{ width: 6px; }}
    .cp-content::-webkit-scrollbar-track {{ background: #0a0808; }}
    .cp-content::-webkit-scrollbar-thumb {{ background: #cc2020; box-shadow: 0 0 8px rgba(204,32,32,0.8), 0 0 16px rgba(255,48,32,0.4); }}
```

Then add a Firefox fallback by appending `scrollbar-width` and `scrollbar-color` to the existing `.cp-sidebar {{ ... }}` (~418) and `.cp-content {{ ... }}` (~588) rules. Add these two declarations inside each rule (before its closing `}}`):
```css
      scrollbar-width: thin;
      scrollbar-color: #cc2020 #0a0808;
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_builder_cyberpunk.py::test_cyberpunk_scrollbar_glows_red -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add notes_app/builder.py tests/test_builder_cyberpunk.py
git commit -m "feat: make cyberpunk scrollbar a glowing red bar"
```

---

### Task 4: Manual visual verification

**Files:**
- Create (temporary, not committed): a few sample notes under `notes/`
- No source or test changes.

**Interfaces:**
- Consumes: the CLI `build` command and the completed Tasks 1–3.
- Produces: a rendered `output/index.html` for eyeball review. No code artifacts.

- [ ] **Step 1: Create sample notes across folders**

```bash
uv run python main.py new "Neural Interface Notes" --folder tech --tags cyberware,braindance
uv run python main.py new "Night City Contacts" --folder people --tags fixers
uv run python main.py new "Loose Thoughts" --tags misc
```
(If `$EDITOR` opens, save/close each; these run in a terminal so the editor may launch.)

- [ ] **Step 2: Build the site**

Run: `uv run python main.py build`
Expected: `Build complete → output/index.html`

- [ ] **Step 3: Open and eyeball against the reference**

Run: `open output/index.html`
Confirm against `~/Desktop/cyberpunk.png`:
- Background shows a corner **vignette** (darker corners) and a subtle **texture**, not a flat gradient.
- A **magenta→red strip** bleeds along the very top edge.
- Scrolling the sidebar/content shows a **glowing red scrollbar**.
- All note text and headings remain **clearly legible**.

- [ ] **Step 4: Clean up sample notes**

```bash
rm -rf notes/tech notes/people notes/loose-thoughts.md
git status --short   # confirm only intended files changed; output/ is gitignored
```

- [ ] **Step 5: No commit needed** (verification only; sample notes removed, `output/` is gitignored).

---

## Self-Review

**Spec coverage:**
- Gap 1 (rich background: vignette + noise) → Task 1. ✅
- Gap 2 (top magenta→red strip) → Task 2. ✅
- Gap 3 (glowing red scrollbar) → Task 3. ✅
- Testing requirement (assert the three markers; manual verification) → tests in Tasks 1–3 + Task 4. ✅
- Constraint: zero binary assets (inline SVG) → enforced in Task 1 (`data:image/svg+xml`). ✅
- Constraint: readability → checked in Task 4 Step 3. ✅
- Out-of-scope items (glow/clip-path/teal/other themes/build changes) → not touched by any task. ✅

**Placeholder scan:** No TBD/TODO; every code step shows exact CSS and exact commands. ✅

**Type/selector consistency:** Selectors referenced in tests match those edited — `.cp-topbar::before`, `::-webkit-scrollbar-thumb`, `#cc2020`, `data:image/svg+xml`, `radial-gradient(` all appear in both the implementation steps and their assertions. The f-string doubled-brace rule is called out in Global Constraints and in each task that adds braces. ✅
