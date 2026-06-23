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
