from pathlib import Path
from notes_app.frontmatter import parse_frontmatter

_NOTES_DIR = Path("notes")


def _collect(notes_dir: Path) -> list[dict]:
    results = []
    for path in sorted(notes_dir.rglob("*.md")):
        meta, content = parse_frontmatter(path)
        results.append({
            "path": path,
            "title": meta.get("title", path.stem),
            "folder": meta.get("folder", ""),
            "tags": meta.get("tags", []),
            "date": meta.get("date", ""),
            "content": content.strip(),
            "excerpt": content.strip()[:150],
        })
    return results


def list_notes(folder: str | None = None, tag: str | None = None, notes_dir: Path = _NOTES_DIR) -> list[dict]:
    notes = _collect(notes_dir)
    if folder:
        notes = [n for n in notes if n["folder"] == folder]
    if tag:
        notes = [n for n in notes if tag in n["tags"]]
    return notes


def search_notes(query: str, notes_dir: Path = _NOTES_DIR) -> list[dict]:
    q = query.lower()
    scored = []
    for note in _collect(notes_dir):
        score = 0
        if q in note["title"].lower():
            score += 10
        if any(q in t.lower() for t in note["tags"]):
            score += 8
        if q in note["folder"].lower():
            score += 5
        if q in note["content"].lower():
            score += 1
        if score > 0:
            scored.append((score, note))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [n for _, n in scored]
