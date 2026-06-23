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
