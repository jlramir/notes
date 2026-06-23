# Note-Taking System Design

**Date:** 2026-06-23
**Status:** Approved

## Overview

A local, offline-first note-taking system built with Python. Notes are written as Markdown files on disk. A CLI manages notes (create, edit, delete, tag, search, list). A build command generates a static HTML viewer (`output/`) that can be opened directly in a browser — no server required. Six game-inspired visual themes are available as swappable CSS skins.

---

## Directory Structure

```
notes/
├── main.py              # CLI entry point
├── notes/               # Markdown note files (source of truth)
│   ├── work/
│   ├── personal/
│   └── ideas/
├── output/              # Generated HTML output (gitignored)
│   ├── index.html       # Note list + search UI
│   ├── notes.json       # Pre-built search index loaded by JS
│   └── note/            # Per-note HTML pages
│       └── <folder>/
│           └── <slug>.html
└── themes/              # CSS theme files
    ├── cyberpunk.css
    ├── last-of-us.css
    ├── rdr2.css
    ├── returnal.css
    ├── dead-space.css
    └── doom.css
```

---

## Note Format

Notes are Markdown files with YAML frontmatter:

```yaml
---
title: My Note Title
date: 2026-06-23
folder: work
tags: [meeting, q2, planning]
---

Note content here...
```

- `folder` mirrors the subdirectory the file lives in
- `tags` is a list of arbitrary strings for cross-cutting categorization
- `date` is set automatically at creation time by the CLI

---

## CLI Commands

| Command | Description |
|---|---|
| `notes new <title> [--folder <f>] [--tags <t1,t2>]` | Create a note, open in `$EDITOR` |
| `notes edit <title-or-path>` | Open existing note in `$EDITOR` |
| `notes delete <title-or-path>` | Delete note (with confirmation) |
| `notes list [--folder <f>] [--tag <t>]` | List notes, filterable |
| `notes search <query>` | Full-text terminal search |
| `notes tag <title-or-path> --add <t> / --remove <t>` | Modify tags on a note |
| `notes build` | Generate `output/` from all notes |
| `notes theme <name>` | Set active theme (written to config, applied at build) |

The CLI is implemented as a single `main.py` using only Python stdlib (`argparse`, `pathlib`, `subprocess`, `json`, `datetime`, `shutil`).

---

## Build Pipeline

`notes build` performs the following steps in order:

1. Walk `notes/` recursively, parse each `.md` file's frontmatter + content
2. Convert Markdown to HTML using a minimal stdlib-only renderer (no third-party `markdown` library)
3. Write one `output/note/<folder>/<slug>.html` per note
4. Write `output/notes.json` — array of all notes with: `title`, `slug`, `folder`, `tags`, `date`, `content` (plain text for search), `excerpt`
5. Write `output/index.html` — includes the active theme CSS link, the search UI, and the folder sidebar

---

## Search Design

Search runs entirely in the browser via vanilla JS — no server, no build step at search time.

**On page load:** `index.html` fetches `notes.json` into memory.

**As user types:** JS filters the in-memory array in real time.

**Ranking order:**
1. Exact title match
2. Tag match
3. Folder match
4. Content match (full-text)

**Display:** Matching notes appear as cards showing title, folder path, tags (as chips), date, and a content excerpt with the matched keyword highlighted.

---

## Browser UI

### `index.html`
- **Top bar:** Search input + theme switcher dropdown
- **Left sidebar:** Folder tree for browsing by category
- **Main area:** Filtered note cards (title, tags, date, excerpt)
- Clicking a card opens the corresponding `note/<folder>/<slug>.html`

### `note/<folder>/<slug>.html`
- **Back button:** Returns to `index.html`, restoring search state via URL params
- **Header:** Note title, date, tags as chips
- **Body:** Rendered Markdown HTML
- Theme is consistent with index

---

## Theming

All HTML references only CSS custom properties (variables). Swapping themes means swapping which CSS file defines those variables. The active theme is written into the HTML `<link>` tag at build time. Users can also switch themes live in the browser via the dropdown — the choice is saved in `localStorage` and survives page reloads.

**CSS variable contract:**
```css
:root {
  --bg-primary
  --bg-secondary
  --bg-card
  --text-primary
  --text-secondary
  --text-accent
  --border-color
  --font-body
  --font-heading
  --highlight-color   /* search match highlight */
  --tag-bg
  --tag-text
}
```

**Theme personalities:**

| Theme | Feel | Color palette | Typography |
|---|---|---|---|
| Cyberpunk 2077 | Neon noir | Cyan/magenta on near-black | Monospace, glitchy |
| The Last of Us | Post-apocalyptic warm | Amber/brown on dark grey | Serif, worn |
| RDR2 | Western journal | Sepia/tan on parchment | Slab serif |
| Returnal | Sci-fi alien | Purple/green bioluminescent | Geometric sans |
| Dead Space | Horror industrial | Blood red on near-black | Heavy condensed |
| Doom | Brutal metal | Orange/red on black | Bold aggressive |

---

## Constraints & Decisions

- **Zero runtime dependencies** — Python stdlib only; no `pip install` required
- **No server required** — output is fully static; open `output/index.html` directly in a browser
- **Markdown renderer** — minimal stdlib-only implementation covering headings, bold, italic, code blocks, lists, links. No full CommonMark compliance needed for personal notes.
- **WSL-compatible** — no file watchers; manual `notes build` is the rebuild mechanism
- **Gitignore `output/`** — generated files are not committed; only source `.md` files and themes are versioned
