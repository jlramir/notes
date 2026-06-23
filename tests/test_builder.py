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
