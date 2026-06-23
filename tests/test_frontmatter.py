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
