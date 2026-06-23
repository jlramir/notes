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
