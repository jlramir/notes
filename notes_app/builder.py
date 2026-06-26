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
    if active_theme == "cyberpunk":
        _write_index_cyberpunk(notes, output_dir, active_theme)
    else:
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

    note_count = len(notes)
    folder_count = len(folder_order)

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
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500&family=Barlow+Condensed:wght@400;600;700&family=Share+Tech+Mono&display=swap">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    /* ── Base ──────────────────────────────────────────────── */
    body {{
      background: linear-gradient(180deg, #220808 0%, #140404 20%, #0c0404 45%, #080404 100%);
      color: #d0c8c0;
      font-family: 'Barlow Condensed', sans-serif;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      font-size: 16px;
    }}

    /* ── Top bar ───────────────────────────────────────────── */
    .cp-topbar {{
      background: #0a0808;
      border-bottom: 2px solid #cc2020;
      display: flex;
      align-items: stretch;
      height: 46px;
      flex-shrink: 0;
    }}

    /* left stats block — mirrors "2 LEVEL / 2 STREET CRED" */
    .cp-stats {{
      display: flex;
      align-items: center;
      gap: 0;
      padding: 0;
      border-right: 1px solid #1a0808;
      flex-shrink: 0;
    }}
    .cp-stat {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 0 16px;
      height: 100%;
      border-right: 1px solid #140404;
    }}
    .cp-stat-badge {{
      width: 22px;
      height: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      border: 1px solid;
    }}
    .cp-stat-val {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.9rem;
      font-weight: 700;
      line-height: 1;
    }}
    .cp-stat-label {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.58rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      line-height: 1;
    }}
    .cp-stat-text {{ display: flex; flex-direction: column; gap: 2px; }}

    /* NOTES = cyan (like "2 LEVEL" in CP2077) */
    .cp-stat-notes .cp-stat-badge {{ background: #001e1e; border-color: #00c8c0; }}
    .cp-stat-notes .cp-stat-val {{ color: #00d0c8; text-shadow: 0 0 4px #00d0c8, 0 0 10px #00d0c8, 0 0 22px #00d0c8, 0 0 42px rgba(0,208,200,0.6); }}
    .cp-stat-notes .cp-stat-label {{ color: #005a56; }}

    /* FOLDERS = green (like "2 STREET CRED" in CP2077) */
    .cp-stat-folders .cp-stat-badge {{ background: #0e1800; border-color: #80c020; }}
    .cp-stat-folders .cp-stat-val {{ color: #88c828; text-shadow: 0 0 4px #88c828, 0 0 10px #88c828, 0 0 22px #88c828, 0 0 42px rgba(120,200,32,0.6); }}
    .cp-stat-folders .cp-stat-label {{ color: #3a5008; }}

    /* tabs */
    .cp-tabs {{
      display: flex;
      align-items: stretch;
      flex: 1;
      justify-content: center;
    }}
    .cp-tab {{
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 0 18px;
      color: #b03030;
      text-shadow: 0 0 7px rgba(180,30,20,0.45);
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      cursor: default;
      border-right: 1px solid #1a0505;
      position: relative;
    }}
    .cp-tab:first-child {{ border-left: 1px solid #1a0505; }}
    .cp-tab.active {{
      color: #00d0c8;
      text-shadow: 0 0 4px #00d0c8, 0 0 10px #00d0c8, 0 0 22px #00d0c8, 0 0 42px rgba(0,208,200,0.6);
      background: #110a0a;
    }}
    .cp-tab.active::after {{ content: none; }}
    .cp-tab-icon {{ font-size: 0.7rem; color: inherit; opacity: 0.8; }}

    /* right side search + theme */
    .cp-topbar-right {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 16px;
      flex-shrink: 0;
    }}
    .cp-search {{
      background: transparent;
      border: none;
      border-bottom: 1px solid #4a3c00;
      color: #c8b400;
      text-shadow: 0 0 4px #c8b400, 0 0 10px #c8b400, 0 0 22px #c8b400, 0 0 42px rgba(200,180,0,0.6);
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.78rem;
      letter-spacing: 0.14em;
      padding: 2px 6px;
      width: 160px;
      outline: none;
      text-transform: uppercase;
    }}
    .cp-search:focus {{ border-bottom-color: #c8b400; }}
    .cp-search::placeholder {{ color: #4a3c00; text-shadow: none; }}
    .cp-theme-select {{
      background: #0a0808;
      border: 1px solid #4a3c00;
      color: #c8b400;
      text-shadow: 0 0 4px #c8b400, 0 0 10px #c8b400, 0 0 22px #c8b400, 0 0 42px rgba(200,180,0,0.6);
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.7rem;
      letter-spacing: 0.08em;
      padding: 3px 6px;
      cursor: pointer;
    }}

    /* ── Layout ────────────────────────────────────────────── */
    .cp-layout {{ display: flex; flex: 1; overflow: hidden; }}

    /* ── Sidebar — 1/3 width, translucent over body gradient ── */
    .cp-sidebar {{
      flex: 0 0 33.333%;
      width: 33.333%;
      overflow-y: auto;
      flex-shrink: 0;
    }}
    .cp-sidebar::-webkit-scrollbar {{ width: 4px; }}
    .cp-sidebar::-webkit-scrollbar-track {{ background: #0a0808; }}
    .cp-sidebar::-webkit-scrollbar-thumb {{ background: #2a0808; }}

    /* section headers — MAIN JOBS / SIDE JOBS style */
    .cp-section-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px 8px 14px;
      background: #080606;
      border-bottom: 1px solid #1a0505;
      cursor: pointer;
      user-select: none;
    }}
    .cp-section-title {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.22em;
      color: #c8b400;
      text-transform: uppercase;
    }}
    .cp-section-arrow {{
      color: #c8b400;
      font-size: 0.6rem;
      transition: transform 0.15s;
      display: inline-block;
      opacity: 0.8;
    }}
    .cp-section-arrow.collapsed {{ transform: rotate(-90deg); }}

    /* note list items */
    .cp-note-item {{
      display: flex;
      align-items: center;
      padding: 8px 12px;
      cursor: pointer;
      border-bottom: 1px solid #120404;
      gap: 10px;
      min-height: 70px;
      transition: background 0.08s;
    }}
    .cp-note-item:hover {{ background: #1a0808; }}
    .cp-note-item.active {{ background: #c83020; }}
    .cp-note-item.active .cp-note-title {{ color: #0a0000; text-shadow: none; }}
    .cp-note-item.active .cp-note-subtitle {{ color: rgba(20,0,0,0.65); }}
    .cp-note-item.active .cp-note-icon {{ border-color: rgba(0,0,0,0.3); opacity: 0.75; }}

    /* thumbnail — scan-line textured dark-red frame */
    .cp-note-icon {{
      width: 52px;
      height: 52px;
      flex-shrink: 0;
      position: relative;
      overflow: hidden;
      border: 1px solid #6a1010;
      background:
        repeating-linear-gradient(
          0deg,
          rgba(0,0,0,0) 0px,
          rgba(0,0,0,0) 1px,
          rgba(0,0,0,0.35) 1px,
          rgba(0,0,0,0.35) 2px
        ),
        linear-gradient(150deg, #2a0808 0%, #1c0404 45%, #280606 100%);
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    /* top-edge highlight */
    .cp-note-icon::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 1px;
      background: rgba(200,80,40,0.6);
    }}
    /* corner accent */
    .cp-note-icon::after {{
      content: '';
      position: absolute;
      top: 3px; right: 3px;
      width: 6px; height: 6px;
      border-top: 1px solid rgba(200,160,0,0.7);
      border-right: 1px solid rgba(200,160,0,0.7);
    }}
    .cp-note-icon-text {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 1.1rem;
      font-weight: 700;
      color: #c8b400;
      letter-spacing: 0.04em;
      position: relative;
      z-index: 1;
      text-shadow: 0 0 6px #c8b400, 0 0 14px rgba(200,180,0,0.5);
    }}

    .cp-note-info {{ flex: 1; min-width: 0; }}
    .cp-note-title {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.9rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #00d0c8;
      text-shadow: 0 0 6px rgba(0,208,200,0.8), 0 0 14px rgba(0,208,200,0.35);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.2;
    }}
    .cp-note-subtitle {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.7rem;
      font-weight: 600;
      color: #c04030;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-top: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.2;
    }}

    /* ── Content panel — 2/3 width ─────────────────────────── */
    .cp-content {{
      flex: 1;
      overflow-y: auto;
      padding: 32px 40px;
      background: repeating-linear-gradient(
        0deg,
        rgba(0,0,0,0) 0px,
        rgba(0,0,0,0) 2px,
        rgba(0,0,0,0.25) 2px,
        rgba(0,0,0,0.25) 3px
      );
    }}
    .cp-content::-webkit-scrollbar {{ width: 4px; }}
    .cp-content::-webkit-scrollbar-track {{ background: #0a0808; }}
    .cp-content::-webkit-scrollbar-thumb {{ background: #2a0808; }}

    .cp-content-empty {{
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #220e0e;
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.78rem;
      letter-spacing: 0.4em;
      text-transform: uppercase;
    }}

    /* note title */
    .cp-note-header {{
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid #2a0808;
      position: relative;
    }}
    .cp-note-header::after {{
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0;
      width: 60px;
      height: 1px;
      background: #cc2020;
    }}
    .cp-note-heading {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 1.6rem;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #00d0c8;
      text-shadow: 0 0 6px rgba(0,208,200,0.8), 0 0 14px rgba(0,208,200,0.35);
      margin-bottom: 10px;
      line-height: 1.1;
    }}
    .cp-note-meta {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .cp-note-date {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.68rem;
      color: #6a4040;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    .cp-tag {{
      font-family: 'Barlow Condensed', sans-serif;
      font-size: 0.62rem;
      font-weight: 600;
      color: #cc2020;
      border: 1px solid #5a0808;
      padding: 2px 7px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      background: #100404;
    }}

    /* note body — regular Barlow (not condensed) for readability */
    .cp-note-body {{
      font-family: 'Barlow', 'Barlow Condensed', sans-serif;
      font-size: 0.95rem;
      font-weight: 400;
      line-height: 1.8;
      color: #c0b0a8;
    }}
    .cp-note-body h1, .cp-note-body h2, .cp-note-body h3 {{
      font-family: 'Barlow Condensed', sans-serif;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin: 28px 0 10px;
      line-height: 1.2;
    }}
    .cp-note-body h1 {{ font-size: 1.2rem; color: #00d0c8; text-shadow: 0 0 6px rgba(0,208,200,0.6), 0 0 14px rgba(0,208,200,0.25); }}
    .cp-note-body h2 {{ font-size: 1rem; color: #c8b400; text-shadow: 0 0 6px rgba(200,180,0,0.6), 0 0 12px rgba(200,180,0,0.25); }}
    .cp-note-body h3 {{ font-size: 0.88rem; color: #cc2020; }}
    .cp-note-body p {{ margin-bottom: 14px; }}
    .cp-note-body ul, .cp-note-body ol {{ padding-left: 1.5rem; margin-bottom: 14px; }}
    .cp-note-body li {{ margin-bottom: 5px; }}
    .cp-note-body strong {{ color: #f0ece8; font-weight: 700; }}
    .cp-note-body em {{ color: #9a8880; font-style: italic; }}
    .cp-note-body a {{ color: #cc2020; text-decoration: none; }}
    .cp-note-body a:hover {{ text-decoration: underline; }}
    .cp-note-body code {{
      font-family: 'Share Tech Mono', monospace;
      color: #cc4040;
      font-size: 0.85em;
      background: #130404;
      padding: 1px 5px;
      border: 1px solid #2a0606;
    }}
    .cp-note-body pre {{
      background: #0a0606;
      border: 1px solid #220606;
      border-left: 2px solid #cc2020;
      padding: 16px 18px;
      overflow-x: auto;
      margin-bottom: 14px;
    }}
    .cp-note-body pre code {{ background: none; border: none; padding: 0; color: #b8a8a0; font-size: 0.88em; }}

    /* search highlight */
    mark {{ background: #cc2020; color: #fff; padding: 0 2px; }}
  </style>
</head>
<body>
  <header class="cp-topbar">
    <div class="cp-stats">
      <div class="cp-stat cp-stat-notes">
        <div class="cp-stat-badge"><span class="cp-stat-val">{note_count}</span></div>
        <div class="cp-stat-text"><span class="cp-stat-label">NOTES</span></div>
      </div>
      <div class="cp-stat cp-stat-folders">
        <div class="cp-stat-badge"><span class="cp-stat-val">{folder_count}</span></div>
        <div class="cp-stat-text"><span class="cp-stat-label">FOLDERS</span></div>
      </div>
    </div>
    <div class="cp-tabs">
      <div class="cp-tab"><span>⊕</span>MAP</div>
      <div class="cp-tab"><span>◈</span>CHARACTER</div>
      <div class="cp-tab active"><span>▦</span>JOURNAL</div>
      <div class="cp-tab"><span>⚙</span>CRAFTING</div>
      <div class="cp-tab"><span>◇</span>INVENTORY</div>
    </div>
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
              '<div class="cp-note-icon"><span class="cp-note-icon-text">' + note.title.trim().substring(0, 2).toUpperCase() + '</span></div>' +
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
            '<div class="cp-note-icon"><span class="cp-note-icon-text">' + note.title.trim().substring(0, 2).toUpperCase() + '</span></div>' +
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
