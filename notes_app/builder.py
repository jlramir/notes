import html
import json
import shutil
from pathlib import Path

from notes_app.config import get_config
from notes_app.frontmatter import parse_frontmatter
from notes_app.note_ops import slugify
from notes_app.renderer import render_markdown

_NOTES_DIR = Path("notes")
_THEMES_DIR = Path("themes")
_OUTPUT_DIR = Path("output")

_VALID_THEMES = ["cyberpunk", "last-of-us", "rdr2", "returnal", "dead-space", "doom"]
_THEME_LABELS = {
    "cyberpunk": "Cyberpunk 2077",
    "last-of-us": "The Last of Us",
    "rdr2": "Red Dead Redemption 2",
    "returnal": "Returnal",
    "dead-space": "Dead Space",
    "doom": "Doom",
}


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
    _write_index(notes, output_dir, active_theme)


def _collect_notes(notes_dir: Path) -> list[dict]:
    notes = []
    if not notes_dir.exists():
        return notes
    for path in sorted(notes_dir.rglob("*.md")):
        meta, content = parse_frontmatter(path)
        folder = meta.get("folder", "")
        title = meta.get("title", path.stem)
        slug = slugify(title)
        url_parts = ["note", folder, f"{slug}.html"] if folder else ["note", f"{slug}.html"]
        notes.append({
            "path": path,
            "title": title,
            "folder": folder,
            "tags": meta.get("tags", []),
            "date": meta.get("date", ""),
            "content": content.strip(),
            "excerpt": content.strip()[:200],
            "slug": slug,
            "url": "/".join(url_parts),
            "html": render_markdown(content),
        })
    return notes


def _copy_themes(themes_dir: Path, output_dir: Path) -> None:
    dest = output_dir / "themes"
    dest.mkdir(exist_ok=True)
    if themes_dir.exists():
        for css in themes_dir.glob("*.css"):
            shutil.copy2(css, dest / css.name)


def _write_notes_json(notes: list[dict], output_dir: Path) -> None:
    data = [
        {k: v for k, v in n.items() if k not in ("path", "html")}
        for n in notes
    ]
    (output_dir / "notes.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_note_page(note: dict, output_dir: Path, theme: str) -> None:
    if note["folder"]:
        page_dir = output_dir / "note" / note["folder"]
    else:
        page_dir = output_dir / "note"
    page_dir.mkdir(parents=True, exist_ok=True)
    depth = len(note["folder"].split("/")) + 2 if note["folder"] else 2
    theme_path = "../" * depth + f"themes/{theme}.css"
    index_path = "../" * depth + "index.html"
    tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in note["tags"])
    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(note["title"])}</title>
  <link id="theme-css" rel="stylesheet" href="{theme_path}">
  {_base_styles()}
  {_note_styles()}
</head>
<body>
  <header class="top-bar">
    <a class="back-btn" href="{index_path}">← Back</a>
    <select id="theme-switcher" onchange="switchTheme(this.value)">
      {"".join(f'<option value="{t}"{" selected" if t == theme else ""}>{_THEME_LABELS[t]}</option>' for t in _VALID_THEMES)}
    </select>
  </header>
  <main class="note-page">
    <h1 class="note-title">{html.escape(note["title"])}</h1>
    <div class="note-meta">
      <span class="note-date">{html.escape(note["date"])}</span>
      <span class="note-folder">{html.escape(note["folder"] or "root")}</span>
    </div>
    <div class="note-tags">{tags_html}</div>
    <div class="note-body">{note["html"]}</div>
  </main>
  {_theme_switcher_js(depth)}
</body>
</html>"""
    (page_dir / f"{note['slug']}.html").write_text(page_html, encoding="utf-8")


def _write_index(notes: list[dict], output_dir: Path, theme: str) -> None:
    notes_json = json.dumps([
        {k: v for k, v in n.items() if k not in ("path", "html")}
        for n in notes
    ]).replace("</", "<\\/")
    folders = sorted(set(n["folder"] for n in notes if n["folder"]))
    folder_items = '<div class="folder-item active" onclick="filterFolder(event, null)">All Notes</div>'
    for f in folders:
        folder_items += f'<div class="folder-item" onclick="filterFolder(event, \'{f}\')">{f}</div>'

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Notes</title>
  <link id="theme-css" rel="stylesheet" href="themes/{theme}.css">
  {_base_styles()}
  {_index_styles()}
</head>
<body>
  <header class="top-bar">
    <input id="search" type="text" placeholder="Search notes..." oninput="onSearch(this.value)" autocomplete="off">
    <select id="theme-switcher" onchange="switchTheme(this.value)">
      {"".join(f'<option value="{t}"{" selected" if t == theme else ""}>{_THEME_LABELS[t]}</option>' for t in _VALID_THEMES)}
    </select>
  </header>
  <div class="layout">
    <nav class="sidebar">
      <div class="sidebar-title">Folders</div>
      {folder_items}
    </nav>
    <main id="notes-container"></main>
  </div>
  <script>
    const NOTES = {notes_json};
    let activeFolder = null;
    let searchQuery = "";

    function onSearch(q) {{
      searchQuery = q;
      render();
    }}

    function filterFolder(event, folder) {{
      activeFolder = folder;
      document.querySelectorAll(".folder-item").forEach(el => el.classList.remove("active"));
      event.target.classList.add("active");
      render();
    }}

    function score(note, q) {{
      if (!q) return 1;
      let s = 0;
      if (note.title.toLowerCase().includes(q)) s += 10;
      if ((note.tags || []).some(t => t.toLowerCase().includes(q))) s += 8;
      if ((note.folder || "").toLowerCase().includes(q)) s += 5;
      if ((note.content || "").toLowerCase().includes(q)) s += 1;
      return s;
    }}

    function highlight(text, q) {{
      if (!q) return text;
      const esc = q.replace(/[.*+?^${{}}()|[\\]\\\\]/g, "\\\\$&");
      return text.replace(new RegExp("(" + esc + ")", "gi"), "<mark>$1</mark>");
    }}

    function excerpt(content, q, len = 160) {{
      if (!q) return content.slice(0, len) + (content.length > len ? "..." : "");
      const idx = content.toLowerCase().indexOf(q.toLowerCase());
      if (idx === -1) return content.slice(0, len) + "...";
      const s = Math.max(0, idx - 60);
      const e = Math.min(content.length, idx + q.length + 60);
      return (s > 0 ? "..." : "") + content.slice(s, e) + (e < content.length ? "..." : "");
    }}

    function render() {{
      const q = searchQuery.toLowerCase().trim();
      let notes = NOTES;
      if (activeFolder) notes = notes.filter(n => n.folder === activeFolder);
      if (q) {{
        notes = notes
          .map(n => ({{ n, s: score(n, q) }}))
          .filter(x => x.s > 0)
          .sort((a, b) => b.s - a.s)
          .map(x => x.n);
      }}
      const container = document.getElementById("notes-container");
      if (notes.length === 0) {{
        container.innerHTML = '<div class="empty">No notes found.</div>';
        return;
      }}
      container.innerHTML = notes.map(n => `
        <a class="note-card" href="${{n.url}}">
          <div class="note-card-title">${{highlight(n.title, q)}}</div>
          <div class="note-card-meta">
            <span class="note-folder">${{n.folder || "root"}}</span>
            <span class="note-date">${{n.date}}</span>
          </div>
          <div class="note-tags">${{(n.tags || []).map(t => `<span class="tag">${{t}}</span>`).join("")}}</div>
          <div class="note-excerpt">${{highlight(excerpt(n.content, q), q)}}</div>
        </a>
      `).join("");
    }}

    {_theme_switcher_js_inline()}

    const saved = localStorage.getItem("notes-theme");
    if (saved) switchTheme(saved, false);
    render();
  </script>
</body>
</html>"""
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")


def _theme_switcher_js(depth: int) -> str:
    prefix = "../" * depth
    return f"""<script>
    {_theme_switcher_js_inline(prefix)}
    const saved = localStorage.getItem("notes-theme");
    if (saved) switchTheme(saved, false);
  </script>"""


def _theme_switcher_js_inline(prefix: str = "") -> str:
    return f"""function switchTheme(name, save = true) {{
      document.getElementById("theme-css").href = "{prefix}themes/" + name + ".css";
      document.getElementById("theme-switcher").value = name;
      if (save) localStorage.setItem("notes-theme", name);
    }}"""


def _base_styles() -> str:
    return """<style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg-primary); color: var(--text-primary); font-family: var(--font-body); min-height: 100vh; }
    a { color: var(--text-accent); text-decoration: none; }
    .top-bar { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1.5rem; background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); position: sticky; top: 0; z-index: 10; }
    select { background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color); padding: 0.3rem 0.5rem; font-family: var(--font-body); cursor: pointer; }
    .tag { display: inline-block; background: var(--tag-bg); color: var(--tag-text); padding: 0.15rem 0.5rem; margin: 0.1rem; font-size: 0.75rem; border-radius: 2px; }
    mark { background: var(--highlight-color); color: var(--bg-primary); padding: 0 2px; }
  </style>"""


def _index_styles() -> str:
    return """<style>
    #search { flex: 1; background: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border-color); padding: 0.4rem 0.75rem; font-family: var(--font-body); font-size: 1rem; }
    #search::placeholder { color: var(--text-secondary); }
    #search:focus { outline: 1px solid var(--text-accent); }
    .layout { display: flex; height: calc(100vh - 50px); }
    .sidebar { width: 200px; min-width: 160px; background: var(--bg-secondary); border-right: 1px solid var(--border-color); overflow-y: auto; padding: 1rem 0; }
    .sidebar-title { color: var(--text-secondary); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; padding: 0 1rem 0.5rem; }
    .folder-item { padding: 0.5rem 1rem; cursor: pointer; color: var(--text-secondary); font-size: 0.9rem; }
    .folder-item:hover, .folder-item.active { color: var(--text-accent); background: var(--bg-primary); }
    #notes-container { flex: 1; overflow-y: auto; padding: 1.5rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; align-content: start; }
    .note-card { display: block; background: var(--bg-card); border: 1px solid var(--border-color); padding: 1rem; transition: border-color 0.15s; }
    .note-card:hover { border-color: var(--text-accent); }
    .note-card-title { font-family: var(--font-heading); font-size: 1.1rem; color: var(--text-primary); margin-bottom: 0.35rem; }
    .note-card-meta { display: flex; gap: 0.75rem; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.35rem; }
    .note-tags { margin-bottom: 0.4rem; }
    .note-excerpt { font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5; }
    .empty { color: var(--text-secondary); text-align: center; padding: 3rem; grid-column: 1/-1; }
  </style>"""


def _note_styles() -> str:
    return """<style>
    .back-btn { color: var(--text-accent); font-size: 0.9rem; }
    .note-page { max-width: 780px; margin: 2rem auto; padding: 0 1.5rem 4rem; }
    .note-title { font-family: var(--font-heading); font-size: 2rem; color: var(--text-primary); margin-bottom: 0.5rem; }
    .note-meta { display: flex; gap: 1rem; color: var(--text-secondary); font-size: 0.8rem; margin-bottom: 0.5rem; }
    .note-tags { margin-bottom: 1.5rem; }
    .note-body { line-height: 1.7; }
    .note-body h1, .note-body h2, .note-body h3 { font-family: var(--font-heading); color: var(--text-accent); margin: 1.5rem 0 0.5rem; }
    .note-body p { margin-bottom: 0.85rem; }
    .note-body ul { padding-left: 1.5rem; margin-bottom: 0.85rem; }
    .note-body li { margin-bottom: 0.25rem; }
    .note-body pre { background: var(--bg-secondary); border: 1px solid var(--border-color); padding: 1rem; overflow-x: auto; margin-bottom: 0.85rem; }
    .note-body code { font-family: var(--font-body); font-size: 0.9em; color: var(--text-accent); }
    .note-body pre code { color: var(--text-primary); }
    .note-body a { color: var(--text-accent); text-decoration: underline; }
    .note-body strong { color: var(--text-primary); }
  </style>"""
