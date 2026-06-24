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
