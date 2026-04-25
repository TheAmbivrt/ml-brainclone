"""
system_tag_batch.py — Apply `system/<area>` tags to vault files based on path.

Pattern: walk the vault, classify each .md file by location, add the appropriate
tag to its YAML frontmatter. Idempotent — re-running adds nothing if the tag is
already present.

Usage:
    python system_tag_batch.py [--vault PATH] [--apply]

Without --apply, runs in DRY-RUN mode and prints what would change.

See `docs/system-taxonomy.md` for the full pattern.
"""
import argparse
import re
from pathlib import Path

# --- Customize these for your vault ----------------------------------------

ROOT_SCAFFOLD = {
    "ARCHITECTURE.md", "CLAUDE.md", "CLAUDE-TEMPLATE.md", "CONTRIBUTING.md",
    "DATAVIEW-DASHBOARD.md", "GRAPH-COLOR-PALETTE.md", "HOME.md",
    "LEXICON-TEMPLATE.md", "PRIVACY-TEMPLATE.md", "QUICK-START.md",
    "README.md", "README-template.md", "SETUP.md", "SYSTEM-INDEX.md",
    "_active-context.md",
}

# Folders directly under 03-projects/ that are agent-specific
AGENT_FOLDERS = {
    "larry", "barry", "harry", "parry", "tarry", "carry", "darry",
    "scarry", "farry", "bert", "milla",
}

# Subdirs inside the brainclone folder and their tags
BRAINCLONE_SUBDIRS = {
    "architecture": "system/architecture",
    "operations": "system/operations",
    "setup": "system/setup",
    "skills": "system/skills",
    "bus": "system/bus",
    "search": "system/search",
    "eval": "system/eval",
    "bugs": "system/bugs",
    "todos": "system/todos",
    "trajectories": "system/trajectories",
    "notifications": "system/notifications",
    "scripts": "system/scripts",
    "patches": "system/patches",
    "nattskift": "system/nattskift",
    "nattskift-reports": "system/nattskift",
}

# Path of the brainclone (orchestrator) folder relative to vault root
BRAINCLONE_PATH = ("03-projects", "ml-brainclone")

SKIP_DIRS = {
    "_private", ".obsidian", ".trash", ".git", ".claude",
    ".playwright-mcp", "node_modules", "06-archive",
    "bin", ".venv",
}

# --- Implementation --------------------------------------------------------


def classify(rel_path: Path) -> list[str]:
    """Return list of system tags for this path, [] if not a system file."""
    parts = rel_path.parts
    name = parts[-1]

    # Root scaffold
    if len(parts) == 1 and name in ROOT_SCAFFOLD:
        return ["system/scaffold"]

    # GitHub templates
    if len(parts) >= 2 and parts[0] == ".github" and parts[1] == "template":
        return ["system/template"]

    # Brainclone (orchestrator) subdirs
    if (
        len(parts) >= len(BRAINCLONE_PATH) + 1
        and parts[: len(BRAINCLONE_PATH)] == BRAINCLONE_PATH
    ):
        if len(parts) == len(BRAINCLONE_PATH) + 1:
            return ["system/ml-brainclone"]
        sub = parts[len(BRAINCLONE_PATH)]
        if sub in BRAINCLONE_SUBDIRS:
            return [BRAINCLONE_SUBDIRS[sub]]
        return ["system/ml-brainclone"]

    # Agent-specific folders
    if len(parts) >= 3 and parts[0] == "03-projects" and parts[1] in AGENT_FOLDERS:
        return [f"system/agent/{parts[1]}"]

    return []


def split_frontmatter(text: str):
    if not (text.startswith("---\n") or text.startswith("---\r\n")):
        return None, text
    rest = text[4:] if text.startswith("---\n") else text[5:]
    m = re.search(r"^---\s*$", rest, flags=re.MULTILINE)
    if not m:
        return None, text
    fm = rest[: m.start()]
    body = rest[m.end():].lstrip("\n").lstrip("\r\n")
    return fm, body


def parse_tags(fm: str):
    inline = re.search(r"^tags\s*:\s*\[([^\]]*)\]\s*$", fm, flags=re.MULTILINE)
    if inline:
        items = re.findall(
            r'"([^"]*)"|\'([^\']*)\'|([^,\s][^,]*[^,\s]|[^,\s])',
            inline.group(1),
        )
        flat = [a or b or c for (a, b, c) in items]
        tags = [t.strip().strip('"').strip("'") for t in flat if t.strip()]
        return tags, "inline", inline
    block = re.search(
        r"^(tags\s*:\s*\n((?:[ \t]+-\s*.+\n?)+))",
        fm,
        flags=re.MULTILINE,
    )
    if block:
        tags = []
        for line in block.group(0).split("\n")[1:]:
            m = re.match(r"^([ \t]+)-\s*(.+?)\s*$", line)
            if m:
                tags.append(m.group(2).strip().strip('"').strip("'"))
        return tags, "block", block
    return [], "none", None


def add_tags(fm: str, new_tags: list[str]):
    existing, fmt, match_obj = parse_tags(fm)
    to_add = [t for t in new_tags if t not in existing]
    if not to_add:
        return fm, False
    merged = existing + to_add

    if fmt == "inline":
        new_inline = "tags: [" + ", ".join(merged) + "]"
        return fm.replace(match_obj.group(0), new_inline), True

    if fmt == "block":
        block_lines = match_obj.group(0).split("\n")
        indent = "  "
        for line in block_lines[1:]:
            m = re.match(r"^([ \t]+)-", line)
            if m:
                indent = m.group(1)
                break
        new_block = "tags:\n" + "\n".join(f"{indent}- {t}" for t in merged) + "\n"
        return fm.replace(match_obj.group(0), new_block), True

    # No tags field at all — prepend
    new_line = f"tags: [{', '.join(merged)}]"
    return new_line + "\n" + fm, True


def process_file(path: Path, vault: Path, dry_run: bool):
    rel = path.relative_to(vault)
    tags = classify(rel)
    if not tags:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return ("error", rel, str(e))
    fm, body = split_frontmatter(text)
    if fm is None:
        return ("no-fm", rel)
    new_fm, changed = add_tags(fm, tags)
    if not changed:
        return ("already-tagged", rel)
    if not dry_run:
        new_text = "---\n" + new_fm.rstrip() + "\n---\n\n" + body
        path.write_text(new_text, encoding="utf-8")
    return ("tagged", rel, tags)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", default=".", help="Vault root path")
    ap.add_argument("--apply", action="store_true", help="Actually write changes")
    args = ap.parse_args()

    vault = Path(args.vault).resolve()
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Vault: {vault}")

    counts = {"tagged": 0, "already-tagged": 0, "no-fm": 0, "error": 0, "skipped": 0}
    samples = []

    for path in vault.rglob("*.md"):
        rel = path.relative_to(vault)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        result = process_file(path, vault, dry_run=not args.apply)
        if result is None:
            counts["skipped"] += 1
            continue
        kind = result[0]
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "tagged" and len(samples) < 15:
            samples.append((str(rel), result[2]))

    print("\n=== Summary ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    if samples:
        print("\nFirst 15 tagged samples:")
        for rel, tags in samples:
            print(f"  + {rel}  -> {tags}")


if __name__ == "__main__":
    main()
