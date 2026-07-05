# notes

A local-first Markdown note manager with a CLI and a static-site generator. Notes are plain `.md` files with YAML frontmatter; `build` turns them into a searchable, themeable single-page HTML journal — no server, no database, no third-party dependencies.

## Requirements

- **Python ≥ 3.12** (the code uses modern type-union syntax like `Path | None`)
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency management

> **macOS note:** the system `python3` is often older than 3.12 and will fail to run this directly. Always invoke through `uv run`, which uses the project's pinned 3.12 interpreter.

## Setup

```bash
uv sync          # create the venv and install dev dependencies
```

## Usage

All commands run through `uv run python main.py <command>`.

| Command | Description |
|---|---|
| `new <title> [--folder F] [--tags a,b]` | Create a note (opens `$EDITOR` when run in a terminal) |
| `edit <query>` | Open a matching note in `$EDITOR` (falls back to `nano`) |
| `delete <query>` | Delete a note (prompts for confirmation) |
| `list [--folder F] [--tag T]` | List notes, optionally filtered |
| `search <query>` | Full-text search across titles, tags, folders, and content |
| `tag <query> [--add a,b] [--remove c]` | Add or remove tags on a note |
| `build` | Generate the static HTML site into `output/` |
| `theme <name>` | Set the active visual theme |

### Examples

```bash
uv run python main.py new "Weekly Plan" --folder work --tags planning,todo
uv run python main.py list --folder work
uv run python main.py search "deadline"
uv run python main.py tag "Weekly Plan" --add urgent
uv run python main.py build      # writes output/index.html
uv run python main.py theme doom
```

After `build`, open `output/index.html` in a browser:

```bash
open output/index.html
```

The generated page has live client-side search, folder navigation, and an in-page theme switcher (your choice is remembered via `localStorage`).

## How it works

- **Notes** live in `notes/`, organized into subfolders. Each is a Markdown file with YAML frontmatter (`title`, `date`, `folder`, `tags`).
- **`build`** parses every note, renders the Markdown to HTML, copies the theme stylesheets, and emits a self-contained static site under `output/`:
  - `index.html` — the searchable journal index
  - `note/<folder>/<slug>.html` — one page per note
  - `notes.json` — note metadata
  - `themes/*.css` — copied theme stylesheets
- The active theme is stored in `.notes-config.json` (created on first `theme` change; defaults to `cyberpunk`).

## Themes

Game-inspired visual themes, selectable via `theme <name>` or the in-page switcher (your choice is remembered in `localStorage`):

`cyberpunk` · `last-of-us` · `rdr2` · `returnal` · `dead-space` · `doom`

All themes share live client-side search and folder filtering. The generated site is fully self-contained — every theme is pure CSS with no binary assets or external dependencies.

### Cyberpunk 2077 journal (default)

The `cyberpunk` theme renders a two-panel **journal** modeled on the in-game shard reader, rather than the standard card grid:

- **Journal top bar** — live `NOTES` / `FOLDERS` counts and a `JOURNAL` tab with a glowing cyan underline, plus search and the theme switcher.
- **Sidebar** — notes grouped into collapsible folder sections with HUD-style thumbnails; click a note to open it in the reading pane.
- **Reading pane** — the selected note rendered inline with neon headings and a code block **COPY** button.
- **In-game atmosphere** — a layered maroon background with a corner vignette and subtle noise texture, a magenta→red gradient bleed along the top edge, angular (clipped-corner) panels, scanline overlays, neon red/cyan/amber glow accents, and a glowing red scrollbar.

### Other themes

`last-of-us`, `rdr2`, `returnal`, `dead-space`, and `doom` use a searchable **card-grid** index with a folder sidebar and one page per note, each restyled through its own palette and fonts.

## Configuration

| Variable | Effect |
|---|---|
| `$EDITOR` | Editor used by `new` and `edit` (defaults to `nano`) |

## Project layout

```
main.py            CLI entry point (argparse)
notes_app/
  config.py        theme/config persistence (.notes-config.json)
  note_ops.py      create/edit/delete/tag, slugify, editor launch
  list_search.py   list and full-text search
  frontmatter.py   YAML frontmatter parse/dump
  renderer.py      Markdown → HTML renderer
  builder.py       static-site generation
notes/             your Markdown notes (gitkept subfolders)
themes/            theme stylesheets
output/            generated site (gitignored)
tests/             pytest suite
```

## Development

```bash
uv run pytest     # run the test suite
```
