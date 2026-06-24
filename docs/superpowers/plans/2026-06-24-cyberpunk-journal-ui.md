# Cyberpunk 2077 Journal UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the default card-grid index with a Cyberpunk 2077 in-game journal-inspired two-panel SPA layout when the cyberpunk theme is active, and update `cyberpunk.css` to a red-on-dark palette matching the reference screenshot.

**Architecture:** `builder.py`'s `build()` function dispatches to `_write_index_cyberpunk()` when `active_theme == "cyberpunk"`, otherwise the existing `_write_index()`. The cyberpunk index is a self-contained single-page app — left panel lists notes grouped by folder as collapsible sections; clicking a note renders content inline on the right (no page navigation). Note HTML is embedded directly in the page as `const NOTES = [...]`. Other themes continue to use the existing card-grid layout. Note pages (`output/note/...`) are always generated for all themes and always reflect the active theme CSS.

**Tech Stack:** Python 3.12 stdlib, vanilla JS (string concatenation — no template literals to avoid f-string conflicts), CSS custom properties.

## Global Constraints

- Python 3.12+; zero third-party dependencies
- All HTML output goes to `output/` (gitignored)
- Cyberpunk index includes `html` field in embedded `NOTES`; `notes.json` and default index do NOT include `html`
- `</` in all embedded JSON must be replaced with `<\/` to prevent script injection
- `build()` public signature unchanged: `build(notes_dir, themes_dir, output_dir) -> None`
- All 57 existing tests must continue to pass after changes
- CLI invoked as `python main.py <command>` from project root
- Themes applied at build time via active theme CSS link; browser dropdown switches CSS live via `localStorage`

---

### Task 1: Update cyberpunk.css to red-on-dark CP2077 journal palette

**Files:**
- Modify: `themes/cyberpunk.css`

**Interfaces:**
- Produces: 12 CSS custom properties consumed by both the cyberpunk index template and note pages

- [ ] **Step 1: Read the current file**

```bash
cat themes/cyberpunk.css
```

- [ ] **Step 2: Overwrite with red-on-dark journal palette**

Write `themes/cyberpunk.css` with the following content (all 12 required variables):

```css
/* Cyberpunk 2077 — journal red */
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&family=Share+Tech+Mono&display=swap');

:root {
  --bg-primary:     #0a0808;
  --bg-secondary:   #0f0b0b;
  --bg-card:        #0c0909;
  --text-primary:   #ddd0c8;
  --text-secondary: #5a3a3a;
  --text-accent:    #cc2020;
  --border-color:   #2a0808;
  --font-body:      'Share Tech Mono', 'Courier New', monospace;
  --font-heading:   'Barlow Condensed', 'Arial Narrow', sans-serif;
  --highlight-color:#e04010;
  --tag-bg:         #1a0505;
  --tag-text:       #cc2020;
}
```

- [ ] **Step 3: Verify all 12 variables present**

```bash
grep -c '\-\-' themes/cyberpunk.css
```

Expected output: `12`

- [ ] **Step 4: Run full test suite — no regressions**

```bash
uv run pytest tests/ -q
```

Expected: `57 passed`

- [ ] **Step 5: Commit**

```bash
git add themes/cyberpunk.css
git commit -m "feat: update cyberpunk theme to red-on-dark journal palette"
```

---

### Task 2: Add `_write_index_cyberpunk` and dispatch logic to builder.py

**Files:**
- Modify: `notes_app/builder.py`
- Create: `tests/test_builder_cyberpunk.py`

**Interfaces:**
- Consumes from `notes_app/builder.py` (existing, unchanged):
  - `_collect_notes(notes_dir: Path) -> list[dict]` — each dict has keys: `path`, `title`, `folder`, `tags`, `date`, `content`, `excerpt`, `slug`, `url`, `html`
  - `_VALID_THEMES: list[str]` = `["cyberpunk", "last-of-us", "rdr2", "returnal", "dead-space", "doom"]`
  - `_THEME_LABELS: dict[str, str]` — maps theme slug to display name
  - `get_config() -> dict` from `notes_app.config` — returns `{"theme": "cyberpunk"}` if no config file
- Produces:
  - `_write_index_cyberpunk(notes: list[dict], output_dir: Path, theme: str) -> None`
  - Updated `build()`: calls `_write_index_cyberpunk` when `active_theme == "cyberpunk"`, else `_write_index`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_builder_cyberpunk.py
import json
from pathlib import Path
import pytest
from notes_app.builder import build
from notes_app.frontmatter import write_frontmatter


def _setup(tmp_path, theme="cyberpunk"):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    themes_dir.mkdir(parents=True, exist_ok=True)
    (themes_dir / f"{theme}.css").write_text(":root {}")
    (tmp_path / ".notes-config.json").write_text(json.dumps({"theme": theme}))
    return notes_dir, themes_dir, output_dir


def _make_note(notes_dir, title, folder, tags, content="Hello world"):
    from notes_app.note_ops import slugify
    from datetime import date
    slug = slugify(title)
    folder_path = notes_dir / folder if folder else notes_dir
    folder_path.mkdir(parents=True, exist_ok=True)
    path = folder_path / f"{slug}.md"
    write_frontmatter(
        path,
        {"title": title, "date": str(date.today()), "folder": folder, "tags": tags},
        content,
    )


def test_cyberpunk_index_has_two_panel_layout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Test Note", "work", [])
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert "cp-sidebar" in html
    assert "cp-content" in html
    assert "cp-topbar" in html


def test_cyberpunk_index_shows_journal_tab_active(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert "cp-tab active" in html
    assert "JOURNAL" in html


def test_cyberpunk_index_embeds_html_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Rich Note", "work", [], content="## Section\n\nHello")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert '"html"' in html
    assert "<h2>" in html


def test_cyberpunk_index_groups_by_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Work Note", "work", [])
    _make_note(notes_dir, "Ideas Note", "ideas", [])
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert '"work"' in html
    assert '"ideas"' in html


def test_cyberpunk_index_escapes_script_injection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(
        notes_dir, "Bad Note", "work", [],
        content="</script><script>alert(1)</script>",
    )
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert "</script><script>alert(1)" not in html


def test_non_cyberpunk_theme_uses_default_layout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path, theme="doom")
    (themes_dir / "doom.css").write_text(":root {}")
    _make_note(notes_dir, "Doom Note", "work", [])
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert "cp-sidebar" not in html
    assert "note-card" in html


def test_notes_json_excludes_html_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Any Note", "work", [], content="## Heading\n\nBody")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    data = json.loads((output_dir / "notes.json").read_text())
    assert len(data) == 1
    assert "html" not in data[0]
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
uv run pytest tests/test_builder_cyberpunk.py -v
```

Expected: `FAILED` — `cp-sidebar`, `cp-topbar`, `cp-content` not present in current index output (default layout used for all themes)

- [ ] **Step 3: Add `_write_index_cyberpunk` to `notes_app/builder.py`**

Insert the following function **after** `_write_index` (after line ~240, before `_theme_switcher_js`):

```python
def _write_index_cyberpunk(notes: list[dict], output_dir: Path, theme: str) -> None:
    notes_json = json.dumps([
        {k: v for k, v in n.items() if k != "path"}
        for n in notes
    ]).replace("</", "<\\/")

    folder_order: list[str] = []
    for n in notes:
        if n["folder"] and n["folder"] not in folder_order:
            folder_order.append(n["folder"])
    folder_order_js = json.dumps(folder_order)

    theme_options = "".join(
        f'<option value="{t}"{" selected" if t == theme else ""}>{_THEME_LABELS[t]}</option>'
        for t in _VALID_THEMES
    )

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Notes — JOURNAL</title>
  <link id="theme-css" rel="stylesheet" href="themes/{theme}.css">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg-primary); color: var(--text-primary); font-family: var(--font-body); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }}
    .cp-topbar {{ background: var(--bg-secondary); border-bottom: 2px solid var(--text-accent); display: flex; align-items: center; padding: 0 1rem; height: 44px; flex-shrink: 0; gap: 0; }}
    .cp-tab {{ padding: 0 1.2rem; height: 100%; display: flex; align-items: center; color: var(--text-secondary); font-family: var(--font-heading); font-size: 0.78rem; letter-spacing: 0.12em; text-transform: uppercase; cursor: default; border-right: 1px solid var(--border-color); gap: 0.35rem; }}
    .cp-tab.active {{ color: var(--text-accent); border-bottom: 2px solid var(--text-accent); margin-bottom: -2px; }}
    .cp-topbar-right {{ margin-left: auto; display: flex; align-items: center; gap: 1rem; }}
    .cp-search {{ background: transparent; border: none; border-bottom: 1px solid var(--border-color); color: var(--text-primary); font-family: var(--font-body); font-size: 0.78rem; padding: 0.2rem 0.5rem; width: 180px; outline: none; }}
    .cp-search:focus {{ border-bottom-color: var(--text-accent); }}
    .cp-search::placeholder {{ color: var(--text-secondary); }}
    .cp-theme-select {{ background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); font-family: var(--font-body); font-size: 0.7rem; padding: 0.2rem 0.4rem; cursor: pointer; }}
    .cp-layout {{ display: flex; flex: 1; overflow: hidden; }}
    .cp-sidebar {{ width: 280px; min-width: 220px; background: var(--bg-secondary); border-right: 1px solid var(--border-color); overflow-y: auto; flex-shrink: 0; }}
    .cp-section-header {{ display: flex; align-items: center; justify-content: space-between; padding: 0.55rem 1rem; background: rgba(0,0,0,0.5); border-top: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); cursor: pointer; user-select: none; }}
    .cp-section-header:first-child {{ border-top: none; }}
    .cp-section-title {{ font-family: var(--font-heading); font-size: 0.72rem; letter-spacing: 0.18em; color: var(--text-accent); text-transform: uppercase; font-weight: 700; }}
    .cp-section-arrow {{ color: var(--text-accent); font-size: 0.65rem; transition: transform 0.15s; display: inline-block; }}
    .cp-section-arrow.collapsed {{ transform: rotate(-90deg); }}
    .cp-note-item {{ display: flex; align-items: flex-start; padding: 0.5rem 1rem 0.5rem 1.2rem; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.03); gap: 0.6rem; transition: background 0.1s; }}
    .cp-note-item:hover {{ background: rgba(204,32,32,0.12); }}
    .cp-note-item.active {{ background: var(--text-accent); }}
    .cp-note-item.active .cp-note-title {{ color: #000; }}
    .cp-note-item.active .cp-note-subtitle {{ color: rgba(0,0,0,0.6); }}
    .cp-note-item.active .cp-note-icon {{ background: rgba(0,0,0,0.2); border-color: rgba(0,0,0,0.3); color: #000; }}
    .cp-note-icon {{ width: 34px; height: 34px; background: var(--bg-card, #0c0909); border: 1px solid var(--border-color); flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.55rem; color: var(--text-accent); font-family: var(--font-heading); font-weight: 700; }}
    .cp-note-info {{ flex: 1; min-width: 0; }}
    .cp-note-title {{ font-family: var(--font-heading); font-size: 0.82rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; }}
    .cp-note-subtitle {{ font-size: 0.62rem; color: var(--text-secondary); letter-spacing: 0.08em; text-transform: uppercase; margin-top: 0.15rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .cp-content {{ flex: 1; overflow-y: auto; padding: 2rem 2.5rem; background: var(--bg-primary); }}
    .cp-content-empty {{ display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary); font-family: var(--font-heading); letter-spacing: 0.25em; text-transform: uppercase; font-size: 0.75rem; }}
    .cp-note-header {{ margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; }}
    .cp-note-heading {{ font-family: var(--font-heading); font-size: 1.75rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-primary); margin-bottom: 0.5rem; font-weight: 700; }}
    .cp-note-meta {{ display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }}
    .cp-note-date {{ font-size: 0.68rem; color: var(--text-secondary); letter-spacing: 0.1em; }}
    .cp-tag {{ font-size: 0.62rem; color: var(--text-accent); border: 1px solid var(--text-accent); padding: 0.1rem 0.4rem; letter-spacing: 0.1em; text-transform: uppercase; }}
    .cp-note-body {{ line-height: 1.75; }}
    .cp-note-body h1, .cp-note-body h2, .cp-note-body h3 {{ font-family: var(--font-heading); color: var(--text-accent); letter-spacing: 0.08em; text-transform: uppercase; margin: 1.5rem 0 0.5rem; font-weight: 700; }}
    .cp-note-body h1 {{ font-size: 1.3rem; }}
    .cp-note-body h2 {{ font-size: 1.05rem; }}
    .cp-note-body h3 {{ font-size: 0.88rem; }}
    .cp-note-body p {{ margin-bottom: 0.85rem; }}
    .cp-note-body ul {{ padding-left: 1.5rem; margin-bottom: 0.85rem; }}
    .cp-note-body li {{ margin-bottom: 0.3rem; }}
    .cp-note-body strong {{ color: var(--text-primary); }}
    .cp-note-body em {{ color: var(--text-secondary); font-style: italic; }}
    .cp-note-body code {{ font-family: var(--font-body); color: var(--text-accent); font-size: 0.9em; }}
    .cp-note-body pre {{ background: var(--bg-secondary); border: 1px solid var(--border-color); border-left: 3px solid var(--text-accent); padding: 1rem; overflow-x: auto; margin-bottom: 0.85rem; }}
    .cp-note-body pre code {{ color: var(--text-primary); }}
    .cp-note-body a {{ color: var(--text-accent); }}
    mark {{ background: var(--highlight-color); color: #000; padding: 0 2px; }}
  </style>
</head>
<body>
  <header class="cp-topbar">
    <div class="cp-tab"><span>⊕</span>MAP</div>
    <div class="cp-tab"><span>◈</span>CHARACTER</div>
    <div class="cp-tab active"><span>▦</span>JOURNAL</div>
    <div class="cp-tab"><span>⚙</span>CRAFTING</div>
    <div class="cp-tab"><span>◇</span>INVENTORY</div>
    <div class="cp-topbar-right">
      <input class="cp-search" type="text" placeholder="SEARCH..." oninput="onSearch(this.value)" autocomplete="off">
      <select class="cp-theme-select" id="theme-switcher" onchange="switchTheme(this.value)">
        {theme_options}
      </select>
    </div>
  </header>
  <div class="cp-layout">
    <nav class="cp-sidebar" id="cp-sidebar"></nav>
    <main class="cp-content" id="cp-content">
      <div class="cp-content-empty">SELECT A FILE</div>
    </main>
  </div>
  <script>
    const NOTES = {notes_json};
    let activeId = null;
    let searchQuery = '';
    const collapsed = {{}};
    const folderOrder = {folder_order_js};

    function selectNote(id) {{
      activeId = id;
      document.querySelectorAll('.cp-note-item').forEach(function(el) {{ el.classList.remove('active'); }});
      var item = document.querySelector('[data-id="' + id + '"]');
      if (item) item.classList.add('active');
      var note = NOTES.find(function(n) {{ return n.slug === id; }});
      if (!note) return;
      var tags = (note.tags || []).map(function(t) {{ return '<span class="cp-tag">' + t + '</span>'; }}).join('');
      document.getElementById('cp-content').innerHTML =
        '<div class="cp-note-header">' +
          '<div class="cp-note-heading">' + note.title + '</div>' +
          '<div class="cp-note-meta">' +
            '<span class="cp-note-date">' + note.date + '</span>' + tags +
          '</div>' +
        '</div>' +
        '<div class="cp-note-body">' + (note.html || '') + '</div>';
    }}

    function toggleSection(folder) {{
      collapsed[folder] = !collapsed[folder];
      renderSidebar();
    }}

    function highlight(text, q) {{
      if (!q) return text;
      var esc = q.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
      return text.replace(new RegExp('(' + esc + ')', 'gi'), '<mark>$1</mark>');
    }}

    function score(note, q) {{
      if (!q) return 1;
      var s = 0;
      if (note.title.toLowerCase().indexOf(q) !== -1) s += 10;
      if ((note.tags || []).some(function(t) {{ return t.toLowerCase().indexOf(q) !== -1; }})) s += 8;
      if ((note.folder || '').toLowerCase().indexOf(q) !== -1) s += 5;
      if ((note.content || '').toLowerCase().indexOf(q) !== -1) s += 1;
      return s;
    }}

    function onSearch(q) {{
      searchQuery = q.toLowerCase().trim();
      renderSidebar();
    }}

    function renderSidebar() {{
      var q = searchQuery;
      var notes = NOTES;
      if (q) {{
        notes = notes
          .map(function(n) {{ return {{ n: n, s: score(n, q) }}; }})
          .filter(function(x) {{ return x.s > 0; }})
          .sort(function(a, b) {{ return b.s - a.s; }})
          .map(function(x) {{ return x.n; }});
      }}

      var byFolder = {{}};
      var rootNotes = [];
      notes.forEach(function(note) {{
        if (note.folder) {{
          if (!byFolder[note.folder]) byFolder[note.folder] = [];
          byFolder[note.folder].push(note);
        }} else {{
          rootNotes.push(note);
        }}
      }});

      var folders = q ? Object.keys(byFolder) : folderOrder;
      var html = '';

      folders.forEach(function(folder) {{
        var folderNotes = byFolder[folder] || [];
        if (!folderNotes.length) return;
        var isCollapsed = !q && collapsed[folder];
        html += '<div class="cp-section-header" onclick="toggleSection(\\'' + folder + '\\')">' +
          '<span class="cp-section-title">' + folder.toUpperCase() + '</span>' +
          '<span class="cp-section-arrow' + (isCollapsed ? ' collapsed' : '') + '">&#9660;</span>' +
          '</div>';
        if (!isCollapsed) {{
          folderNotes.forEach(function(note) {{
            var sub = (note.tags || []).join(' \xb7 ') || note.date || '';
            var titleHtml = q ? highlight(note.title.toUpperCase(), q.toUpperCase()) : note.title.toUpperCase();
            html += '<div class="cp-note-item' + (note.slug === activeId ? ' active' : '') + '" ' +
              'data-id="' + note.slug + '" onclick="selectNote(\\'' + note.slug + '\\')">' +
              '<div class="cp-note-icon">&#9635;</div>' +
              '<div class="cp-note-info">' +
                '<div class="cp-note-title">' + titleHtml + '</div>' +
                '<div class="cp-note-subtitle">' + sub.toUpperCase() + '</div>' +
              '</div></div>';
          }});
        }}
      }});

      if (rootNotes.length) {{
        rootNotes.forEach(function(note) {{
          var sub = (note.tags || []).join(' \xb7 ') || note.date || '';
          html += '<div class="cp-note-item' + (note.slug === activeId ? ' active' : '') + '" ' +
            'data-id="' + note.slug + '" onclick="selectNote(\\'' + note.slug + '\\')">' +
            '<div class="cp-note-icon">&#9635;</div>' +
            '<div class="cp-note-info">' +
              '<div class="cp-note-title">' + note.title.toUpperCase() + '</div>' +
              '<div class="cp-note-subtitle">' + sub.toUpperCase() + '</div>' +
            '</div></div>';
        }});
      }}

      if (!html) {{
        html = '<div style="padding:2rem;color:var(--text-secondary);text-align:center;' +
          'font-size:0.75rem;letter-spacing:0.12em;font-family:var(--font-heading)">NO FILES FOUND</div>';
      }}

      document.getElementById('cp-sidebar').innerHTML = html;
      if (activeId) {{
        var active = document.querySelector('[data-id="' + activeId + '"]');
        if (active) active.classList.add('active');
      }}
    }}

    function switchTheme(name, save) {{
      if (save === undefined) save = true;
      document.getElementById('theme-css').href = 'themes/' + name + '.css';
      document.getElementById('theme-switcher').value = name;
      if (save) localStorage.setItem('notes-theme', name);
    }}

    var savedTheme = localStorage.getItem('notes-theme');
    if (savedTheme) switchTheme(savedTheme, false);
    renderSidebar();
    if (NOTES.length > 0) selectNote(NOTES[0].slug);
  </script>
</body>
</html>"""
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")
```

- [ ] **Step 4: Update `build()` in `notes_app/builder.py` to dispatch based on theme**

Find the current `build()` function (lines 26–42). Replace its last line:

```python
    _write_index(notes, output_dir, active_theme)
```

With:

```python
    if active_theme == "cyberpunk":
        _write_index_cyberpunk(notes, output_dir, active_theme)
    else:
        _write_index(notes, output_dir, active_theme)
```

The full updated `build()` looks like:

```python
def build(
    notes_dir: Path = _NOTES_DIR,
    themes_dir: Path = _THEMES_DIR,
    output_dir: Path = _OUTPUT_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "note").mkdir(exist_ok=True)

    config = get_config()
    active_theme = config.get("theme", "cyberpunk")

    notes = _collect_notes(notes_dir)
    _copy_themes(themes_dir, output_dir)
    _write_notes_json(notes, output_dir)
    for note in notes:
        _write_note_page(note, output_dir, active_theme)
    if active_theme == "cyberpunk":
        _write_index_cyberpunk(notes, output_dir, active_theme)
    else:
        _write_index(notes, output_dir, active_theme)
```

- [ ] **Step 5: Run new tests — all 7 must pass**

```bash
uv run pytest tests/test_builder_cyberpunk.py -v
```

Expected: `7 passed`

- [ ] **Step 6: Run full test suite — all 57 original tests must still pass**

```bash
uv run pytest tests/ -q
```

Expected: `64 passed` (57 original + 7 new)

- [ ] **Step 7: Manual smoke test — rebuild and open**

```bash
# Ensure cyberpunk theme is active
python main.py theme cyberpunk
python main.py build
explorer.exe output/index.html   # or xdg-open output/index.html
```

Expected: two-panel layout with CP2077 journal aesthetic — red-on-dark, folder sections in left panel, note content renders on right when clicked.

- [ ] **Step 8: Commit**

```bash
git add notes_app/builder.py tests/test_builder_cyberpunk.py
git commit -m "feat: add Cyberpunk 2077 journal two-panel index layout"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task |
|---|---|
| Two-panel SPA layout (left list, right content) | Task 2 |
| Left panel: folders as collapsible sections (uppercase) | Task 2 |
| Left panel: note items with icon + title in caps + tags as subtitle | Task 2 |
| Selected note highlighted red | Task 2 |
| Right panel: note title + rendered Markdown inline | Task 2 |
| Top bar: CP2077-style tab strip, JOURNAL tab active | Task 2 |
| Search filters left panel in real time | Task 2 |
| Theme switcher dropdown preserved | Task 2 |
| Other themes use existing card-grid layout | Task 2 (dispatch logic) |
| Note pages still generated for all themes | Unchanged (not affected) |
| Red-on-dark palette matching CP2077 journal | Task 1 |
| `</script>` injection protection | Task 2 (`.replace("</", "<\\/"`)  |
| `html` field in cyberpunk NOTES, excluded from `notes.json` | Task 2 |
| 57 existing tests pass | Task 2 step 6 |

All requirements covered. No placeholders.
