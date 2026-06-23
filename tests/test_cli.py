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
