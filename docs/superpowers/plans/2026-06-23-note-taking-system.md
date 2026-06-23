# Note-Taking System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a zero-dependency Python CLI that manages Markdown notes and generates a themed static HTML viewer with client-side search.

**Architecture:** Notes are `.md` files with YAML frontmatter on disk. A CLI (`main.py`) wraps CRUD operations and a `build` command that walks the notes directory, renders Markdown to HTML, embeds all note data as inline JS, and writes `output/index.html` + per-note pages. Six game-themed CSS files provide visual skins switched at runtime via `localStorage`.

**Tech Stack:** Python 3.12 stdlib only (`argparse`, `pathlib`, `json`, `re`, `subprocess`, `datetime`, `shutil`). Vanilla JS (no libraries). CSS custom properties for theming.

## Global Constraints

- Python 3.12+; zero third-party dependencies (`pip install` nothing)
- All HTML output goes to `output/` (gitignored); never commit generated files
- Notes source files live in `notes/` subdirectories
- Theme CSS files live in `themes/`; builder copies them to `output/themes/`
- Note data is embedded inline in `index.html` as `const NOTES = [...]` — no `fetch()` needed (avoids `file://` CORS issues)
- CLI is invoked as `python main.py <command>` from the project root
- `$EDITOR` env var controls which editor opens for `new`/`edit` (default: `nano`)
- Slug format: lowercase, spaces → hyphens, special chars stripped

---

### Task 1: Project scaffold

**Files:**
- Create: `notes_app/__init__.py`
- Create: `notes/work/.gitkeep`
- Create: `notes/personal/.gitkeep`
- Create: `notes/ideas/.gitkeep`
- Create: `themes/` (empty directory placeholder)
- Modify: `.gitignore`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: `notes_app` package importable; `notes/` and `themes/` directories exist

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p notes_app tests notes/work notes/personal notes/ideas themes output
touch notes_app/__init__.py tests/__init__.py
touch notes/work/.gitkeep notes/personal/.gitkeep notes/ideas/.gitkeep
```

- [ ] **Step 2: Write .gitignore**

```
output/
__pycache__/
*.pyc
.notes-config.json
```

- [ ] **Step 3: Verify structure**

```bash
find . -not -path './.git/*' -not -path './docs/*' | sort
```

Expected output includes `./notes_app/__init__.py`, `./tests/__init__.py`, `./notes/work/.gitkeep`, `./themes/`.

- [ ] **Step 4: Commit**

```bash
git add notes_app/__init__.py tests/__init__.py notes/ themes/ .gitignore
git commit -m "feat: scaffold project structure"
```

---

### Task 2: Frontmatter parser/writer

**Files:**
- Create: `notes_app/frontmatter.py`
- Create: `tests/test_frontmatter.py`

**Interfaces:**
- Produces:
  - `parse_frontmatter(path: Path) -> tuple[dict, str]` — returns `(metadata, content)`; `metadata` is `{}` if no frontmatter
  - `write_frontmatter(path: Path, metadata: dict, content: str) -> None`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_frontmatter.py
from pathlib import Path
import pytest
from notes_app.frontmatter import parse_frontmatter, write_frontmatter


def test_parse_with_tags(tmp_path):
    note = tmp_path / "test.md"
    note.write_text("---\ntitle: Hello World\ntags: [a, b, c]\ndate: 2026-06-23\nfolder: work\n---\n\nContent here.")
    meta, content = parse_frontmatter(note)
    assert meta["title"] == "Hello World"
    assert meta["tags"] == ["a", "b", "c"]
    assert meta["date"] == "2026-06-23"
    assert meta["folder"] == "work"
    assert content.strip() == "Content here."


def test_parse_no_frontmatter(tmp_path):
    note = tmp_path / "bare.md"
    note.write_text("Just content, no frontmatter.")
    meta, content = parse_frontmatter(note)
    assert meta == {}
    assert content == "Just content, no frontmatter."


def test_parse_empty_tags(tmp_path):
    note = tmp_path / "notags.md"
    note.write_text("---\ntitle: No Tags\ntags: []\ndate: 2026-06-23\nfolder: \n---\n\nBody.")
    meta, content = parse_frontmatter(note)
    assert meta["tags"] == []
    assert content.strip() == "Body."


def test_roundtrip(tmp_path):
    note = tmp_path / "roundtrip.md"
    write_frontmatter(note, {"title": "RT", "tags": ["x", "y"], "date": "2026-01-01", "folder": "ideas"}, "Round trip body.")
    meta, content = parse_frontmatter(note)
    assert meta["title"] == "RT"
    assert meta["tags"] == ["x", "y"]
    assert content.strip() == "Round trip body."


def test_write_creates_file(tmp_path):
    note = tmp_path / "new.md"
    write_frontmatter(note, {"title": "New", "tags": [], "date": "2026-06-23", "folder": ""}, "")
    assert note.exists()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_frontmatter.py -v
```

Expected: `ModuleNotFoundError: No module named 'notes_app.frontmatter'`

- [ ] **Step 3: Implement `notes_app/frontmatter.py`**

```python
import re
from pathlib import Path

_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = _PATTERN.match(text)
    if not match:
        return {}, text
    return _parse_yaml(match.group(1)), text[match.end():]


def write_frontmatter(path: Path, metadata: dict, content: str) -> None:
    path.write_text(f"---\n{_dump_yaml(metadata)}---\n\n{content}", encoding="utf-8")


def _parse_yaml(raw: str) -> dict:
    result = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()] if inner else []
        else:
            result[key] = value.strip("'\"")
    return result


def _dump_yaml(metadata: dict) -> str:
    lines = []
    for key, value in metadata.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests — all must pass**

```bash
python -m pytest tests/test_frontmatter.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add notes_app/frontmatter.py tests/test_frontmatter.py
git commit -m "feat: add frontmatter parser/writer"
```

---

### Task 3: Markdown renderer

**Files:**
- Create: `notes_app/renderer.py`
- Create: `tests/test_renderer.py`

**Interfaces:**
- Produces: `render_markdown(text: str) -> str` — converts Markdown to HTML string

- [ ] **Step 1: Write failing tests**

```python
# tests/test_renderer.py
from notes_app.renderer import render_markdown


def test_heading_1():
    assert "<h1>Hello</h1>" in render_markdown("# Hello")


def test_heading_2():
    assert "<h2>World</h2>" in render_markdown("## World")


def test_heading_3():
    assert "<h3>Sub</h3>" in render_markdown("### Sub")


def test_bold():
    assert "<strong>bold</strong>" in render_markdown("**bold**")


def test_italic():
    assert "<em>italic</em>" in render_markdown("*italic*")


def test_inline_code():
    assert "<code>x = 1</code>" in render_markdown("`x = 1`")


def test_link():
    result = render_markdown("[click](https://example.com)")
    assert '<a href="https://example.com">click</a>' in result


def test_unordered_list():
    result = render_markdown("- item one\n- item two")
    assert "<ul>" in result
    assert "<li>item one</li>" in result
    assert "<li>item two</li>" in result
    assert "</ul>" in result


def test_code_block():
    result = render_markdown("```python\nprint('hi')\n```")
    assert "<pre><code" in result
    assert "print(&#x27;hi&#x27;)" in result or "print('hi')" in result
    assert "</code></pre>" in result


def test_paragraph():
    assert "<p>Hello world</p>" in render_markdown("Hello world")


def test_html_escaping_in_code_block():
    result = render_markdown("```\n<script>alert(1)</script>\n```")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_renderer.py -v
```

Expected: `ModuleNotFoundError: No module named 'notes_app.renderer'`

- [ ] **Step 3: Implement `notes_app/renderer.py`**

```python
import re


def render_markdown(text: str) -> str:
    lines = text.split("\n")
    out = []
    in_code = False
    in_list = False

    for line in lines:
        if line.startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                lang = line[3:].strip()
                cls = f' class="language-{lang}"' if lang else ""
                out.append(f"<pre><code{cls}>")
                in_code = True
            continue

        if in_code:
            out.append(_escape(line))
            continue

        if line.startswith("### "):
            _close_list(out, in_list); in_list = False
            out.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            _close_list(out, in_list); in_list = False
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            _close_list(out, in_list); in_list = False
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(line[2:])}</li>")
        elif line.strip() == "":
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("")
        else:
            _close_list(out, in_list); in_list = False
            out.append(f"<p>{_inline(line)}</p>")

    if in_list:
        out.append("</ul>")
    if in_code:
        out.append("</code></pre>")

    return "\n".join(out)


def _close_list(out: list, in_list: bool) -> None:
    if in_list:
        out.append("</ul>")


def _inline(text: str) -> str:
    text = _escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("'", "&#x27;")
            .replace('"', "&quot;")
    )
```

- [ ] **Step 4: Run tests — all must pass**

```bash
python -m pytest tests/test_renderer.py -v
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add notes_app/renderer.py tests/test_renderer.py
git commit -m "feat: add stdlib-only Markdown renderer"
```

---

### Task 4: Config management

**Files:**
- Create: `notes_app/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces:
  - `VALID_THEMES: list[str]` — `['cyberpunk', 'last-of-us', 'rdr2', 'returnal', 'dead-space', 'doom']`
  - `get_config() -> dict` — returns `{"theme": "cyberpunk"}` if no config file exists
  - `set_config(key: str, value: str) -> None` — writes/updates `.notes-config.json`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_config.py
import json
from pathlib import Path
import pytest
from notes_app.config import get_config, set_config, VALID_THEMES


def test_default_config_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = get_config()
    assert config["theme"] == "cyberpunk"


def test_set_and_get_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    set_config("theme", "doom")
    config = get_config()
    assert config["theme"] == "doom"


def test_set_config_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    set_config("theme", "rdr2")
    assert (tmp_path / ".notes-config.json").exists()


def test_set_config_preserves_other_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    set_config("theme", "doom")
    set_config("other_key", "value")
    config = get_config()
    assert config["theme"] == "doom"
    assert config["other_key"] == "value"


def test_valid_themes_list():
    assert "cyberpunk" in VALID_THEMES
    assert "last-of-us" in VALID_THEMES
    assert "rdr2" in VALID_THEMES
    assert "returnal" in VALID_THEMES
    assert "dead-space" in VALID_THEMES
    assert "doom" in VALID_THEMES
    assert len(VALID_THEMES) == 6
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'notes_app.config'`

- [ ] **Step 3: Implement `notes_app/config.py`**

```python
import json
from pathlib import Path

VALID_THEMES = ["cyberpunk", "last-of-us", "rdr2", "returnal", "dead-space", "doom"]
_CONFIG_PATH = Path(".notes-config.json")
_DEFAULTS = {"theme": "cyberpunk"}


def get_config() -> dict:
    if not _CONFIG_PATH.exists():
        return _DEFAULTS.copy()
    return {**_DEFAULTS, **json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))}


def set_config(key: str, value: str) -> None:
    config = get_config()
    config[key] = value
    _CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run tests — all must pass**

```bash
python -m pytest tests/test_config.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add notes_app/config.py tests/test_config.py
git commit -m "feat: add config management"
```

---

### Task 5: Note CRUD operations

**Files:**
- Create: `notes_app/note_ops.py`
- Create: `tests/test_note_ops.py`

**Interfaces:**
- Consumes:
  - `parse_frontmatter(path: Path) -> tuple[dict, str]` from `notes_app.frontmatter`
  - `write_frontmatter(path: Path, metadata: dict, content: str) -> None` from `notes_app.frontmatter`
- Produces:
  - `slugify(title: str) -> str`
  - `find_note(query: str, notes_dir: Path) -> Path | None`
  - `new_note(title: str, folder: str, tags: list[str], notes_dir: Path) -> Path` (does NOT open editor in tests)
  - `edit_note(query: str, notes_dir: Path) -> None` (opens `$EDITOR`)
  - `delete_note(query: str, notes_dir: Path, confirm: bool = True) -> bool`
  - `tag_note(query: str, add: list[str], remove: list[str], notes_dir: Path) -> None`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_note_ops.py
from pathlib import Path
import pytest
from notes_app.note_ops import slugify, find_note, new_note, delete_note, tag_note
from notes_app.frontmatter import parse_frontmatter


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_special_chars():
    assert slugify("C++  Notes!") == "c--notes"


def test_new_note_creates_file(tmp_path):
    path = new_note("My Note", "work", ["a", "b"], notes_dir=tmp_path)
    assert path.exists()
    meta, _ = parse_frontmatter(path)
    assert meta["title"] == "My Note"
    assert meta["folder"] == "work"
    assert meta["tags"] == ["a", "b"]


def test_new_note_no_folder(tmp_path):
    path = new_note("Root Note", "", [], notes_dir=tmp_path)
    assert path.exists()
    assert path.parent == tmp_path


def test_new_note_creates_subfolder(tmp_path):
    new_note("Deep Note", "personal/journal", [], notes_dir=tmp_path)
    assert (tmp_path / "personal" / "journal").is_dir()


def test_find_note_by_slug(tmp_path):
    new_note("Find Me", "work", [], notes_dir=tmp_path)
    found = find_note("find-me", tmp_path)
    assert found is not None
    assert found.name == "find-me.md"


def test_find_note_by_title_substring(tmp_path):
    new_note("Find Me Please", "work", [], notes_dir=tmp_path)
    found = find_note("find me", tmp_path)
    assert found is not None


def test_find_note_missing_returns_none(tmp_path):
    assert find_note("nonexistent", tmp_path) is None


def test_delete_note(tmp_path):
    new_note("Delete Me", "", [], notes_dir=tmp_path)
    result = delete_note("delete-me", tmp_path, confirm=False)
    assert result is True
    assert not (tmp_path / "delete-me.md").exists()


def test_delete_note_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        delete_note("ghost", tmp_path, confirm=False)


def test_tag_note_add(tmp_path):
    new_note("Tagged", "", ["existing"], notes_dir=tmp_path)
    tag_note("tagged", add=["new"], remove=[], notes_dir=tmp_path)
    meta, _ = parse_frontmatter(tmp_path / "tagged.md")
    assert "existing" in meta["tags"]
    assert "new" in meta["tags"]


def test_tag_note_remove(tmp_path):
    new_note("Tagged", "", ["keep", "remove-me"], notes_dir=tmp_path)
    tag_note("tagged", add=[], remove=["remove-me"], notes_dir=tmp_path)
    meta, _ = parse_frontmatter(tmp_path / "tagged.md")
    assert "keep" in meta["tags"]
    assert "remove-me" not in meta["tags"]


def test_tag_note_no_duplicates(tmp_path):
    new_note("Tagged", "", ["a"], notes_dir=tmp_path)
    tag_note("tagged", add=["a", "b"], remove=[], notes_dir=tmp_path)
    meta, _ = parse_frontmatter(tmp_path / "tagged.md")
    assert meta["tags"].count("a") == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_note_ops.py -v
```

Expected: `ModuleNotFoundError: No module named 'notes_app.note_ops'`

- [ ] **Step 3: Implement `notes_app/note_ops.py`**

```python
import os
import re
import subprocess
from datetime import date
from pathlib import Path

from notes_app.frontmatter import parse_frontmatter, write_frontmatter

_NOTES_DIR = Path("notes")


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug.strip())
    return slug


def find_note(query: str, notes_dir: Path = _NOTES_DIR) -> Path | None:
    p = Path(query)
    if p.exists():
        return p
    slug = slugify(query)
    for path in notes_dir.rglob("*.md"):
        if path.stem == slug or slug in path.stem or query.lower() in path.stem.replace("-", " "):
            return path
    return None


def new_note(title: str, folder: str = "", tags: list[str] | None = None, notes_dir: Path = _NOTES_DIR) -> Path:
    slug = slugify(title)
    folder_path = notes_dir / folder if folder else notes_dir
    folder_path.mkdir(parents=True, exist_ok=True)
    path = folder_path / f"{slug}.md"
    write_frontmatter(path, {
        "title": title,
        "date": str(date.today()),
        "folder": folder,
        "tags": tags or [],
    }, "")
    return path


def edit_note(query: str, notes_dir: Path = _NOTES_DIR) -> None:
    path = find_note(query, notes_dir)
    if not path:
        raise FileNotFoundError(f"Note not found: {query}")
    _open_editor(path)


def delete_note(query: str, notes_dir: Path = _NOTES_DIR, confirm: bool = True) -> bool:
    path = find_note(query, notes_dir)
    if not path:
        raise FileNotFoundError(f"Note not found: {query}")
    if confirm:
        answer = input(f"Delete {path}? [y/N] ")
        if answer.lower() != "y":
            return False
    path.unlink()
    return True


def tag_note(query: str, add: list[str], remove: list[str], notes_dir: Path = _NOTES_DIR) -> None:
    path = find_note(query, notes_dir)
    if not path:
        raise FileNotFoundError(f"Note not found: {query}")
    metadata, content = parse_frontmatter(path)
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tags] if tags else []
    tags = [t for t in tags if t not in remove]
    for t in add:
        if t not in tags:
            tags.append(t)
    metadata["tags"] = tags
    write_frontmatter(path, metadata, content)


def _open_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(path)])
```

- [ ] **Step 4: Run tests — all must pass**

```bash
python -m pytest tests/test_note_ops.py -v
```

Expected: `13 passed`

- [ ] **Step 5: Commit**

```bash
git add notes_app/note_ops.py tests/test_note_ops.py
git commit -m "feat: add note CRUD operations"
```

---

### Task 6: List and terminal search

**Files:**
- Create: `notes_app/list_search.py`
- Create: `tests/test_list_search.py`

**Interfaces:**
- Consumes:
  - `parse_frontmatter(path: Path) -> tuple[dict, str]` from `notes_app.frontmatter`
- Produces:
  - `list_notes(folder: str | None, tag: str | None, notes_dir: Path) -> list[dict]`
  - `search_notes(query: str, notes_dir: Path) -> list[dict]`
  - Each returned dict has keys: `path`, `title`, `folder`, `tags`, `date`, `content`, `excerpt`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_list_search.py
from pathlib import Path
from notes_app.list_search import list_notes, search_notes
from notes_app.note_ops import new_note
from notes_app.frontmatter import write_frontmatter


def _make_note(notes_dir: Path, title: str, folder: str, tags: list, content: str = "") -> None:
    from notes_app.note_ops import slugify
    from datetime import date
    slug = slugify(title)
    folder_path = notes_dir / folder if folder else notes_dir
    folder_path.mkdir(parents=True, exist_ok=True)
    path = folder_path / f"{slug}.md"
    write_frontmatter(path, {"title": title, "date": str(date.today()), "folder": folder, "tags": tags}, content)


def test_list_all(tmp_path):
    _make_note(tmp_path, "Note A", "work", [])
    _make_note(tmp_path, "Note B", "personal", [])
    results = list_notes(None, None, notes_dir=tmp_path)
    assert len(results) == 2


def test_list_by_folder(tmp_path):
    _make_note(tmp_path, "Note A", "work", [])
    _make_note(tmp_path, "Note B", "personal", [])
    results = list_notes("work", None, notes_dir=tmp_path)
    assert len(results) == 1
    assert results[0]["title"] == "Note A"


def test_list_by_tag(tmp_path):
    _make_note(tmp_path, "Note A", "", ["python"])
    _make_note(tmp_path, "Note B", "", ["rust"])
    results = list_notes(None, "python", notes_dir=tmp_path)
    assert len(results) == 1
    assert results[0]["title"] == "Note A"


def test_search_by_title(tmp_path):
    _make_note(tmp_path, "Python Tips", "", [])
    _make_note(tmp_path, "Rust Notes", "", [])
    results = search_notes("python", notes_dir=tmp_path)
    assert len(results) == 1
    assert results[0]["title"] == "Python Tips"


def test_search_by_tag(tmp_path):
    _make_note(tmp_path, "Note A", "", ["backend"])
    _make_note(tmp_path, "Note B", "", ["frontend"])
    results = search_notes("backend", notes_dir=tmp_path)
    assert len(results) == 1


def test_search_by_content(tmp_path):
    _make_note(tmp_path, "Note A", "", [], content="This talks about databases")
    _make_note(tmp_path, "Note B", "", [], content="This talks about APIs")
    results = search_notes("databases", notes_dir=tmp_path)
    assert len(results) == 1


def test_search_title_ranked_above_content(tmp_path):
    _make_note(tmp_path, "Cyberpunk", "", [], content="nothing relevant")
    _make_note(tmp_path, "General Note", "", [], content="mentions cyberpunk somewhere")
    results = search_notes("cyberpunk", notes_dir=tmp_path)
    assert results[0]["title"] == "Cyberpunk"


def test_search_no_results(tmp_path):
    _make_note(tmp_path, "Note A", "", [])
    results = search_notes("zzznomatch", notes_dir=tmp_path)
    assert results == []
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_list_search.py -v
```

Expected: `ModuleNotFoundError: No module named 'notes_app.list_search'`

- [ ] **Step 3: Implement `notes_app/list_search.py`**

```python
from pathlib import Path
from notes_app.frontmatter import parse_frontmatter

_NOTES_DIR = Path("notes")


def _collect(notes_dir: Path) -> list[dict]:
    results = []
    for path in sorted(notes_dir.rglob("*.md")):
        meta, content = parse_frontmatter(path)
        results.append({
            "path": path,
            "title": meta.get("title", path.stem),
            "folder": meta.get("folder", ""),
            "tags": meta.get("tags", []),
            "date": meta.get("date", ""),
            "content": content.strip(),
            "excerpt": content.strip()[:150],
        })
    return results


def list_notes(folder: str | None = None, tag: str | None = None, notes_dir: Path = _NOTES_DIR) -> list[dict]:
    notes = _collect(notes_dir)
    if folder:
        notes = [n for n in notes if n["folder"] == folder]
    if tag:
        notes = [n for n in notes if tag in n["tags"]]
    return notes


def search_notes(query: str, notes_dir: Path = _NOTES_DIR) -> list[dict]:
    q = query.lower()
    scored = []
    for note in _collect(notes_dir):
        score = 0
        if q in note["title"].lower():
            score += 10
        if any(q in t.lower() for t in note["tags"]):
            score += 8
        if q in note["folder"].lower():
            score += 5
        if q in note["content"].lower():
            score += 1
        if score > 0:
            scored.append((score, note))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [n for _, n in scored]
```

- [ ] **Step 4: Run tests — all must pass**

```bash
python -m pytest tests/test_list_search.py -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add notes_app/list_search.py tests/test_list_search.py
git commit -m "feat: add list and terminal search"
```

---

### Task 7: Build pipeline

**Files:**
- Create: `notes_app/builder.py`
- Create: `tests/test_builder.py`

**Interfaces:**
- Consumes:
  - `parse_frontmatter(path: Path) -> tuple[dict, str]` from `notes_app.frontmatter`
  - `render_markdown(text: str) -> str` from `notes_app.renderer`
  - `get_config() -> dict` from `notes_app.config`
  - `slugify(title: str) -> str` from `notes_app.note_ops`
- Produces:
  - `build(notes_dir: Path, themes_dir: Path, output_dir: Path) -> None`
  - Side effects: writes `output_dir/index.html`, `output_dir/notes.json`, `output_dir/note/<folder>/<slug>.html`, copies `themes_dir/*.css` to `output_dir/themes/`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_builder.py
import json
from pathlib import Path
from notes_app.builder import build
from notes_app.frontmatter import write_frontmatter


def _make_note(notes_dir: Path, title: str, folder: str, tags: list, content: str = "Hello world") -> None:
    from notes_app.note_ops import slugify
    from datetime import date
    slug = slugify(title)
    folder_path = notes_dir / folder if folder else notes_dir
    folder_path.mkdir(parents=True, exist_ok=True)
    path = folder_path / f"{slug}.md"
    write_frontmatter(path, {"title": title, "date": str(date.today()), "folder": folder, "tags": tags}, content)


def _make_theme(themes_dir: Path, name: str) -> None:
    themes_dir.mkdir(parents=True, exist_ok=True)
    (themes_dir / f"{name}.css").write_text(f":root {{ --bg-primary: #000; }}")


def test_build_creates_index(tmp_path):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    _make_note(notes_dir, "Test Note", "work", ["tag1"])
    _make_theme(themes_dir, "cyberpunk")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    assert (output_dir / "index.html").exists()


def test_build_creates_notes_json(tmp_path):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    _make_note(notes_dir, "JSON Note", "ideas", ["a"])
    _make_theme(themes_dir, "cyberpunk")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    data = json.loads((output_dir / "notes.json").read_text())
    assert len(data) == 1
    assert data[0]["title"] == "JSON Note"
    assert data[0]["tags"] == ["a"]


def test_build_creates_note_page(tmp_path):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    _make_note(notes_dir, "My Note", "work", [], content="## Section\n\nHello")
    _make_theme(themes_dir, "cyberpunk")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    note_page = output_dir / "note" / "work" / "my-note.html"
    assert note_page.exists()
    html = note_page.read_text()
    assert "My Note" in html
    assert "<h2>" in html


def test_build_copies_theme_css(tmp_path):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    notes_dir.mkdir()
    _make_theme(themes_dir, "cyberpunk")
    _make_theme(themes_dir, "doom")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    assert (output_dir / "themes" / "cyberpunk.css").exists()
    assert (output_dir / "themes" / "doom.css").exists()


def test_build_notes_json_has_url(tmp_path):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    _make_note(notes_dir, "URL Test", "work", [])
    _make_theme(themes_dir, "cyberpunk")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    data = json.loads((output_dir / "notes.json").read_text())
    assert "url" in data[0]
    assert "url-test" in data[0]["url"]


def test_build_index_embeds_notes_data(tmp_path):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    _make_note(notes_dir, "Embedded", "work", ["searchable"])
    _make_theme(themes_dir, "cyberpunk")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index.html").read_text()
    assert "const NOTES" in html
    assert "Embedded" in html
    assert "searchable" in html
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_builder.py -v
```

Expected: `ModuleNotFoundError: No module named 'notes_app.builder'`

- [ ] **Step 3: Implement `notes_app/builder.py`**

```python
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
    depth = 3 if note["folder"] else 2
    theme_path = "../" * depth + f"themes/{theme}.css"
    index_path = "../" * depth + "index.html"
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in note["tags"])
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{note["title"]}</title>
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
    <h1 class="note-title">{note["title"]}</h1>
    <div class="note-meta">
      <span class="note-date">{note["date"]}</span>
      <span class="note-folder">{note["folder"] or "root"}</span>
    </div>
    <div class="note-tags">{tags_html}</div>
    <div class="note-body">{note["html"]}</div>
  </main>
  {_theme_switcher_js(depth)}
</body>
</html>"""
    (page_dir / f"{note['slug']}.html").write_text(html, encoding="utf-8")


def _write_index(notes: list[dict], output_dir: Path, theme: str) -> None:
    notes_json = json.dumps([
        {k: v for k, v in n.items() if k not in ("path", "html")}
        for n in notes
    ])
    folders = sorted(set(n["folder"] for n in notes if n["folder"]))
    folder_items = '<div class="folder-item active" onclick="filterFolder(null)">All Notes</div>'
    for f in folders:
        folder_items += f'<div class="folder-item" onclick="filterFolder(\'{f}\')">{f}</div>'

    html = f"""<!DOCTYPE html>
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

    function filterFolder(folder) {{
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
    (output_dir / "index.html").write_text(html, encoding="utf-8")


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
```

- [ ] **Step 4: Run tests — all must pass**

```bash
python -m pytest tests/test_builder.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add notes_app/builder.py tests/test_builder.py
git commit -m "feat: add static site builder"
```

---

### Task 8: Theme CSS files

**Files:**
- Create: `themes/cyberpunk.css`
- Create: `themes/last-of-us.css`
- Create: `themes/rdr2.css`
- Create: `themes/returnal.css`
- Create: `themes/dead-space.css`
- Create: `themes/doom.css`

**Interfaces:**
- Produces: Six CSS files each defining the full set of CSS custom properties used in the HTML templates

The required variables (used in `_base_styles`, `_index_styles`, `_note_styles` in `builder.py`):
`--bg-primary`, `--bg-secondary`, `--bg-card`, `--text-primary`, `--text-secondary`, `--text-accent`, `--border-color`, `--font-body`, `--font-heading`, `--highlight-color`, `--tag-bg`, `--tag-text`

- [ ] **Step 1: Write `themes/cyberpunk.css`**

```css
/* Cyberpunk 2077 — neon noir */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@600&display=swap');

:root {
  --bg-primary:     #0a0a0f;
  --bg-secondary:   #0f0f1a;
  --bg-card:        #0d0d18;
  --text-primary:   #e0e0ff;
  --text-secondary: #6060a0;
  --text-accent:    #00f0ff;
  --border-color:   #1a1a35;
  --font-body:      'Share Tech Mono', 'Courier New', monospace;
  --font-heading:   'Rajdhani', 'Arial Narrow', sans-serif;
  --highlight-color:#ff00aa;
  --tag-bg:         #0a1a2a;
  --tag-text:       #00f0ff;
}
```

- [ ] **Step 2: Write `themes/last-of-us.css`**

```css
/* The Last of Us — post-apocalyptic warm */
@import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,400;0,700;1,400&family=Special+Elite&display=swap');

:root {
  --bg-primary:     #1a1410;
  --bg-secondary:   #211c17;
  --bg-card:        #1e1912;
  --text-primary:   #d4c4a0;
  --text-secondary: #7a6a50;
  --text-accent:    #c8a040;
  --border-color:   #3a2e1e;
  --font-body:      'Merriweather', Georgia, serif;
  --font-heading:   'Special Elite', 'Courier New', cursive;
  --highlight-color:#c8a040;
  --tag-bg:         #2a1e0e;
  --tag-text:       #c8a040;
}
```

- [ ] **Step 3: Write `themes/rdr2.css`**

```css
/* Red Dead Redemption 2 — western journal */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lora:ital,wght@0,400;1,400&display=swap');

:root {
  --bg-primary:     #2e2416;
  --bg-secondary:   #3a2e1a;
  --bg-card:        #342819;
  --text-primary:   #e8d5a0;
  --text-secondary: #9a8060;
  --text-accent:    #d4882a;
  --border-color:   #5a4020;
  --font-body:      'Lora', Georgia, serif;
  --font-heading:   'Playfair Display', Georgia, serif;
  --highlight-color:#d4882a;
  --tag-bg:         #4a3010;
  --tag-text:       #e8d5a0;
}
```

- [ ] **Step 4: Write `themes/returnal.css`**

```css
/* Returnal — sci-fi bioluminescent */
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;600&family=Space+Mono&display=swap');

:root {
  --bg-primary:     #080c14;
  --bg-secondary:   #0c1220;
  --bg-card:        #0a1018;
  --text-primary:   #c0d8f0;
  --text-secondary: #406080;
  --text-accent:    #40e0a0;
  --border-color:   #102030;
  --font-body:      'Space Mono', 'Courier New', monospace;
  --font-heading:   'Exo 2', 'Arial', sans-serif;
  --highlight-color:#a020f0;
  --tag-bg:         #081820;
  --tag-text:       #40e0a0;
}
```

- [ ] **Step 5: Write `themes/dead-space.css`**

```css
/* Dead Space — horror industrial */
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&family=IBM+Plex+Mono&display=swap');

:root {
  --bg-primary:     #080808;
  --bg-secondary:   #0f0a0a;
  --bg-card:        #0c0808;
  --text-primary:   #c8c0c0;
  --text-secondary: #604040;
  --text-accent:    #cc2020;
  --border-color:   #200a0a;
  --font-body:      'IBM Plex Mono', 'Courier New', monospace;
  --font-heading:   'Barlow Condensed', 'Arial Narrow', sans-serif;
  --highlight-color:#cc2020;
  --tag-bg:         #1a0505;
  --tag-text:       #cc2020;
}
```

- [ ] **Step 6: Write `themes/doom.css`**

```css
/* Doom — brutal metal */
@import url('https://fonts.googleapis.com/css2?family=Black+Ops+One&family=Share+Tech+Mono&display=swap');

:root {
  --bg-primary:     #080808;
  --bg-secondary:   #101010;
  --bg-card:        #0c0c0c;
  --text-primary:   #e0d0c0;
  --text-secondary: #604030;
  --text-accent:    #e04010;
  --border-color:   #2a1000;
  --font-body:      'Share Tech Mono', 'Courier New', monospace;
  --font-heading:   'Black Ops One', Impact, sans-serif;
  --highlight-color:#e04010;
  --tag-bg:         #1a0800;
  --tag-text:       #e04010;
}
```

- [ ] **Step 7: Verify all six files exist**

```bash
ls themes/
```

Expected: `cyberpunk.css  dead-space.css  doom.css  last-of-us.css  rdr2.css  returnal.css`

- [ ] **Step 8: Commit**

```bash
git add themes/
git commit -m "feat: add six game-themed CSS files"
```

---

### Task 9: CLI wiring

**Files:**
- Modify: `main.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes all public functions from Tasks 2–7
- Produces: `python main.py <command> [args]` works end-to-end

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cli.py
import subprocess
import sys
from pathlib import Path


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(Path(__file__).parents[1] / "main.py")] + args,
        capture_output=True, text=True, cwd=str(cwd)
    )


def test_help_exits_zero(tmp_path):
    result = run(["--help"], cwd=tmp_path)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_new_note_creates_file(tmp_path):
    (tmp_path / "notes").mkdir()
    result = run(["new", "CLI Test Note", "--folder", "work", "--tags", "cli,test"], cwd=tmp_path)
    assert result.returncode == 0
    note = tmp_path / "notes" / "work" / "cli-test-note.md"
    assert note.exists()


def test_list_shows_notes(tmp_path):
    (tmp_path / "notes").mkdir()
    run(["new", "Listed Note", "--folder", "work"], cwd=tmp_path)
    result = run(["list"], cwd=tmp_path)
    assert result.returncode == 0
    assert "Listed Note" in result.stdout


def test_list_filter_by_folder(tmp_path):
    (tmp_path / "notes").mkdir()
    run(["new", "Work Note", "--folder", "work"], cwd=tmp_path)
    run(["new", "Personal Note", "--folder", "personal"], cwd=tmp_path)
    result = run(["list", "--folder", "work"], cwd=tmp_path)
    assert "Work Note" in result.stdout
    assert "Personal Note" not in result.stdout


def test_search_finds_by_title(tmp_path):
    (tmp_path / "notes").mkdir()
    run(["new", "Cyberpunk Note", "--folder", "ideas"], cwd=tmp_path)
    result = run(["search", "cyberpunk"], cwd=tmp_path)
    assert result.returncode == 0
    assert "Cyberpunk Note" in result.stdout


def test_tag_add_and_list(tmp_path):
    (tmp_path / "notes").mkdir()
    run(["new", "Tag Test", "--folder", "work"], cwd=tmp_path)
    result = run(["tag", "tag-test", "--add", "newTag"], cwd=tmp_path)
    assert result.returncode == 0


def test_theme_sets_config(tmp_path):
    result = run(["theme", "doom"], cwd=tmp_path)
    assert result.returncode == 0
    config_file = tmp_path / ".notes-config.json"
    assert config_file.exists()
    import json
    config = json.loads(config_file.read_text())
    assert config["theme"] == "doom"


def test_theme_invalid_rejected(tmp_path):
    result = run(["theme", "invalid-theme"], cwd=tmp_path)
    assert result.returncode != 0


def test_build_generates_output(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "themes").mkdir()
    (tmp_path / "themes" / "cyberpunk.css").write_text(":root {}")
    run(["new", "Build Test", "--folder", "work"], cwd=tmp_path)
    result = run(["build"], cwd=tmp_path)
    assert result.returncode == 0
    assert (tmp_path / "output" / "index.html").exists()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: failures (main.py is stub `print("Hello from notes!")`)

- [ ] **Step 3: Rewrite `main.py`**

```python
import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="notes", description="Local Markdown note manager")
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_new = sub.add_parser("new", help="Create a new note")
    p_new.add_argument("title")
    p_new.add_argument("--folder", default="", help="Subfolder (e.g. work)")
    p_new.add_argument("--tags", default="", help="Comma-separated tags")

    p_edit = sub.add_parser("edit", help="Open a note in $EDITOR")
    p_edit.add_argument("query", help="Note title or slug")

    p_delete = sub.add_parser("delete", help="Delete a note")
    p_delete.add_argument("query", help="Note title or slug")

    p_list = sub.add_parser("list", help="List notes")
    p_list.add_argument("--folder", default=None)
    p_list.add_argument("--tag", default=None)

    p_search = sub.add_parser("search", help="Full-text search notes")
    p_search.add_argument("query")

    p_tag = sub.add_parser("tag", help="Add or remove tags on a note")
    p_tag.add_argument("query", help="Note title or slug")
    p_tag.add_argument("--add", default="", help="Comma-separated tags to add")
    p_tag.add_argument("--remove", default="", help="Comma-separated tags to remove")

    sub.add_parser("build", help="Generate static HTML output")

    p_theme = sub.add_parser("theme", help="Set active visual theme")
    from notes_app.config import VALID_THEMES
    p_theme.add_argument("name", choices=VALID_THEMES)

    args = parser.parse_args()

    if args.command == "new":
        from notes_app.note_ops import new_note, _open_editor
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        path = new_note(args.title, args.folder, tags)
        _open_editor(path)
        print(f"Created: {path}")

    elif args.command == "edit":
        from notes_app.note_ops import edit_note
        try:
            edit_note(args.query)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "delete":
        from notes_app.note_ops import delete_note
        try:
            deleted = delete_note(args.query)
            if deleted:
                print("Deleted.")
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        from notes_app.list_search import list_notes
        notes = list_notes(args.folder, args.tag)
        if not notes:
            print("No notes found.")
        for n in notes:
            tags = f"  [{', '.join(n['tags'])}]" if n["tags"] else ""
            print(f"[{n['folder'] or 'root'}] {n['title']} ({n['date']}){tags}")

    elif args.command == "search":
        from notes_app.list_search import search_notes
        results = search_notes(args.query)
        if not results:
            print("No results.")
        for n in results:
            print(f"[{n['folder'] or 'root'}] {n['title']}")

    elif args.command == "tag":
        from notes_app.note_ops import tag_note
        add = [t.strip() for t in args.add.split(",") if t.strip()]
        remove = [t.strip() for t in args.remove.split(",") if t.strip()]
        try:
            tag_note(args.query, add, remove)
            print("Tags updated.")
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "build":
        from notes_app.builder import build
        build()
        print("Build complete → output/index.html")

    elif args.command == "theme":
        from notes_app.config import set_config
        set_config("theme", args.name)
        print(f"Theme set to {args.name}. Run `python main.py build` to apply.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests — everything must pass**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass (roughly 43+ passed)

- [ ] **Step 5: Smoke test the full flow manually**

```bash
# From the project root
mkdir -p notes/work notes/personal notes/ideas themes
# Copy a theme file or create a stub
echo ':root { --bg-primary: #000; --bg-secondary: #111; --bg-card: #0a0a0a; --text-primary: #eee; --text-secondary: #888; --text-accent: #0ff; --border-color: #222; --font-body: monospace; --font-heading: sans-serif; --highlight-color: #ff0; --tag-bg: #001; --tag-text: #0ff; }' > themes/cyberpunk.css
python main.py new "Hello World" --folder work --tags test,demo
# (editor opens — save and close)
python main.py list
python main.py search hello
python main.py build
# Open output/index.html in browser
```

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_cli.py
git commit -m "feat: wire CLI with all commands"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| Markdown files with YAML frontmatter | Task 2 |
| Folders + tags organization | Tasks 5, 6 |
| CLI: new, edit, delete, list, search, tag, build, theme | Tasks 5, 6, 7, 9 |
| Search: title/tags ranked above content | Tasks 6, 7 |
| `index.html` with search bar, folder sidebar, note cards | Task 7 |
| `note/<folder>/<slug>.html` per note | Task 7 |
| Theme switcher in browser via `localStorage` | Task 7 |
| Six game themes as CSS files | Task 8 |
| Zero third-party dependencies | All tasks (stdlib only) |
| WSL-compatible (no file watchers) | Design decision — satisfied by absence |
| `output/` gitignored | Task 1 |

All requirements covered.
