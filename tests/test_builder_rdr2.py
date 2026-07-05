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
    css = Path("themes/rdr2.css").read_text()
    assert "--text-accent:" in css
    assert "#d4882a" in css
