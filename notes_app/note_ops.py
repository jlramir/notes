import os
import re
import subprocess
from datetime import date
from pathlib import Path

from notes_app.frontmatter import parse_frontmatter, write_frontmatter

_NOTES_DIR = Path("notes")


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "-", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-{3,}", "--", slug)
    return slug.strip("-")


def find_note(query: str, notes_dir: Path = _NOTES_DIR) -> Path | None:
    p = Path(query)
    if p.exists():
        return p
    slug = slugify(query)
    for path in notes_dir.rglob("*.md"):
        if path.stem == slug or slug in path.stem or query.lower() in path.stem.replace("-", " "):
            return path
    return None


def new_note(title: str, folder: str = "", tags: list[str] | None = None, notes_dir: Path = _NOTES_DIR) -> Path:
    slug = slugify(title)
    folder_path = notes_dir / folder if folder else notes_dir
    folder_path.mkdir(parents=True, exist_ok=True)
    path = folder_path / f"{slug}.md"
    write_frontmatter(path, {
        "title": title,
        "date": str(date.today()),
        "folder": folder,
        "tags": tags or [],
    }, "")
    return path


def edit_note(query: str, notes_dir: Path = _NOTES_DIR) -> None:
    path = find_note(query, notes_dir)
    if not path:
        raise FileNotFoundError(f"Note not found: {query}")
    _open_editor(path)


def delete_note(query: str, notes_dir: Path = _NOTES_DIR, confirm: bool = True) -> bool:
    path = find_note(query, notes_dir)
    if not path:
        raise FileNotFoundError(f"Note not found: {query}")
    if confirm:
        answer = input(f"Delete {path}? [y/N] ")
        if answer.lower() != "y":
            return False
    path.unlink()
    return True


def tag_note(query: str, add: list[str], remove: list[str], notes_dir: Path = _NOTES_DIR) -> None:
    path = find_note(query, notes_dir)
    if not path:
        raise FileNotFoundError(f"Note not found: {query}")
    metadata, content = parse_frontmatter(path)
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tags] if tags else []
    tags = [t for t in tags if t not in remove]
    for t in add:
        if t not in tags:
            tags.append(t)
    metadata["tags"] = tags
    write_frontmatter(path, metadata, content)


def _open_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(path)])
