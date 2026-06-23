import re
from pathlib import Path

_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = _PATTERN.match(text)
    if not match:
        return {}, text
    return _parse_yaml(match.group(1)), text[match.end():]


def write_frontmatter(path: Path, metadata: dict, content: str) -> None:
    path.write_text(f"---\n{_dump_yaml(metadata)}---\n\n{content}", encoding="utf-8")


def _parse_yaml(raw: str) -> dict:
    result = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()] if inner else []
        else:
            result[key] = value.strip("'\"")
    return result


def _dump_yaml(metadata: dict) -> str:
    lines = []
    for key, value in metadata.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"
