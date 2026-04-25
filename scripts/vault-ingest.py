"""
vault-ingest.py — Convert any file to Markdown and drop into vault inbox.

Uses Microsoft's MarkItDown (MIT, 114k+ stars).
Supports: PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, MSG, ZIP, etc.

Usage:
    python vault-ingest.py <file> [--tags tag1,tag2] [--privacy 1-4] [--status draft|active] [--dest path/in/vault]
    python vault-ingest.py presentation.pptx --tags work/project --privacy 2
    python vault-ingest.py contract.pdf --privacy 3 --dest _private/

Requirements:
    pip install 'markitdown[pdf,docx,pptx,xlsx]'
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# ── Configure your vault root ──────────────────────────────────────────────
VAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INBOX = VAULT_ROOT / "00-inbox"

FORMAT_MAP = {
    ".pdf": "pdf", ".docx": "docx", ".doc": "docx",
    ".pptx": "pptx", ".ppt": "pptx",
    ".xlsx": "xlsx", ".xls": "xlsx",
    ".html": "html", ".htm": "html",
    ".csv": "csv", ".json": "json", ".xml": "xml",
    ".msg": "email", ".eml": "email",
    ".epub": "epub", ".ipynb": "notebook",
    ".zip": "archive",
}


def slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


def build_frontmatter(source: Path, tags: list[str], privacy: int, status: str) -> str:
    ext = source.suffix.lower()
    fmt = FORMAT_MAP.get(ext, "document")
    all_tags = [f"source/{fmt}"] + tags
    tag_str = ", ".join(all_tags)
    date = datetime.now().strftime("%Y-%m-%d")
    return (
        f"---\n"
        f"tags: [{tag_str}]\n"
        f"status: {status}\n"
        f"created: {date}\n"
        f"privacy: {privacy}\n"
        f"source_file: {source.name}\n"
        f"---\n\n"
    )


def convert(source: Path) -> str:
    from markitdown import MarkItDown
    md = MarkItDown()
    result = md.convert(str(source))
    return result.text_content


def main():
    parser = argparse.ArgumentParser(description="Convert file to Markdown in vault inbox")
    parser.add_argument("file", type=Path, help="File to convert")
    parser.add_argument("--tags", default="", help="Comma-separated tags (added to auto-tag)")
    parser.add_argument("--privacy", type=int, default=2, choices=[1, 2, 3, 4])
    parser.add_argument("--status", default="draft", choices=["draft", "active", "review", "done"])
    parser.add_argument("--dest", default=None, help="Destination dir in vault (relative to vault root)")
    parser.add_argument("--name", default=None, help="Output filename (without .md)")
    parser.add_argument("--stdout", action="store_true", help="Write to stdout instead of file")
    args = parser.parse_args()

    source = args.file.resolve()
    if not source.exists():
        print(f"File not found: {source}", file=sys.stderr)
        sys.exit(1)

    ext = source.suffix.lower()
    if ext not in FORMAT_MAP and ext not in (".txt", ".md", ".rst"):
        print(f"Warning: {ext} may not be fully supported by MarkItDown", file=sys.stderr)

    content = convert(source)
    if not content or not content.strip():
        print(f"Conversion returned empty result for {source.name}", file=sys.stderr)
        sys.exit(1)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    frontmatter = build_frontmatter(source, tags, args.privacy, args.status)
    full = frontmatter + content

    if args.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(full)
        return

    if args.dest:
        dest_dir = VAULT_ROOT / args.dest
    elif args.privacy >= 3:
        dest_dir = VAULT_ROOT / "_private"
    else:
        dest_dir = DEFAULT_INBOX

    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = args.name or slugify(source.stem)
    dest = dest_dir / f"{stem}.md"

    if dest.exists():
        dest = dest_dir / f"{stem}-{datetime.now().strftime('%H%M%S')}.md"

    dest.write_text(full, encoding="utf-8")
    print(f"{source.name} -> {dest.relative_to(VAULT_ROOT)}")


if __name__ == "__main__":
    main()
