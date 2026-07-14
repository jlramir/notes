# tests/test_builder_rdr2.py
import json
from pathlib import Path
import pytest
from notes_app.builder import build
from notes_app.frontmatter import write_frontmatter


def _setup(tmp_path, theme="rdr2"):
    notes_dir = tmp_path / "notes"
    themes_dir = tmp_path / "themes"
    output_dir = tmp_path / "output"
    themes_dir.mkdir(parents=True, exist_ok=True)
    (themes_dir / f"{theme}.css").write_text(":root {}")
    if theme == "rdr2":
        (themes_dir / "rdr2-map.png").write_bytes(b"")
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


def test_rdr2_css_has_parchment_accent(tmp_path):
    """themes/rdr2.css must define --text-accent as amber #d4882a."""
    css = (Path(__file__).parent.parent / "themes" / "rdr2.css").read_text()
    assert "--text-accent:" in css
    assert "#d4882a" in css


def test_rdr2_index_has_two_panel_layout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Test Note", "work", [])
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index-rdr2.html").read_text()
    assert "rdr-sidebar" in html
    assert "rdr-content" in html
    assert "rdr-topbar" in html


def test_rdr2_index_shows_journal_title(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index-rdr2.html").read_text()
    assert "JOURNAL" in html


def test_rdr2_index_embeds_html_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Rich Note", "work", [], content="## Section\n\nHello")
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index-rdr2.html").read_text()
    assert '"html"' in html
    assert "<h2>" in html


def test_rdr2_index_groups_by_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(notes_dir, "Work Note", "work", [])
    _make_note(notes_dir, "Ideas Note", "ideas", [])
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index-rdr2.html").read_text()
    assert '"work"' in html
    assert '"ideas"' in html


def test_rdr2_index_escapes_script_injection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    _make_note(
        notes_dir, "Bad Note", "work", [],
        content="</script><script>alert(1)</script>",
    )
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index-rdr2.html").read_text()
    assert "</script><script>alert(1)" not in html


def test_rdr2_index_has_dark_content_background(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index-rdr2.html").read_text()
    assert "#0e0e0c" in html


def test_rdr2_index_switchtheme_navigates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    html = (output_dir / "index-rdr2.html").read_text()
    assert "window.location.href" in html
    assert "savedTheme !== 'rdr2'" in html


def test_rdr2_css_has_parchment_background(tmp_path):
    """themes/rdr2.css must define --bg-primary as parchment #c8bc7a."""
    css = (Path(__file__).parent.parent / "themes" / "rdr2.css").read_text()
    assert "--bg-primary:" in css
    assert "#c8bc7a" in css


def test_rdr2_build_copies_map_asset(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes_dir, themes_dir, output_dir = _setup(tmp_path)
    build(notes_dir=notes_dir, themes_dir=themes_dir, output_dir=output_dir)
    assert (output_dir / "rdr2-map.png").exists()
