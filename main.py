import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="notes", description="Local Markdown note manager")
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_new = sub.add_parser("new", help="Create a new note")
    p_new.add_argument("title")
    p_new.add_argument("--folder", default="", help="Subfolder (e.g. work)")
    p_new.add_argument("--tags", default="", help="Comma-separated tags")

    p_edit = sub.add_parser("edit", help="Open a note in $EDITOR")
    p_edit.add_argument("query", help="Note title or slug")

    p_delete = sub.add_parser("delete", help="Delete a note")
    p_delete.add_argument("query", help="Note title or slug")

    p_list = sub.add_parser("list", help="List notes")
    p_list.add_argument("--folder", default=None)
    p_list.add_argument("--tag", default=None)

    p_search = sub.add_parser("search", help="Full-text search notes")
    p_search.add_argument("query")

    p_tag = sub.add_parser("tag", help="Add or remove tags on a note")
    p_tag.add_argument("query", help="Note title or slug")
    p_tag.add_argument("--add", default="", help="Comma-separated tags to add")
    p_tag.add_argument("--remove", default="", help="Comma-separated tags to remove")

    sub.add_parser("build", help="Generate static HTML output")

    p_theme = sub.add_parser("theme", help="Set active visual theme")
    from notes_app.config import VALID_THEMES
    p_theme.add_argument("name", choices=VALID_THEMES)

    args = parser.parse_args()

    if args.command == "new":
        from notes_app.note_ops import new_note, _open_editor
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        path = new_note(args.title, args.folder, tags)
        if sys.stdout.isatty() and sys.environ.get("EDITOR"):
            _open_editor(path)
        print(f"Created: {path}")

    elif args.command == "edit":
        from notes_app.note_ops import edit_note
        try:
            edit_note(args.query)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "delete":
        from notes_app.note_ops import delete_note
        try:
            deleted = delete_note(args.query)
            if deleted:
                print("Deleted.")
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        from notes_app.list_search import list_notes
        notes = list_notes(args.folder, args.tag)
        if not notes:
            print("No notes found.")
        for n in notes:
            tags = f"  [{', '.join(n['tags'])}]" if n["tags"] else ""
            print(f"[{n['folder'] or 'root'}] {n['title']} ({n['date']}){tags}")

    elif args.command == "search":
        from notes_app.list_search import search_notes
        results = search_notes(args.query)
        if not results:
            print("No results.")
        for n in results:
            print(f"[{n['folder'] or 'root'}] {n['title']}")

    elif args.command == "tag":
        from notes_app.note_ops import tag_note
        add = [t.strip() for t in args.add.split(",") if t.strip()]
        remove = [t.strip() for t in args.remove.split(",") if t.strip()]
        try:
            tag_note(args.query, add, remove)
            print("Tags updated.")
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif args.command == "build":
        from notes_app.builder import build
        build()
        print("Build complete → output/index.html")

    elif args.command == "theme":
        from notes_app.config import set_config
        set_config("theme", args.name)
        print(f"Theme set to {args.name}. Run `python main.py build` to apply.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
