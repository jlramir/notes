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
