---
tags: [system/scaffold, system/index, moc]
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
privacy: 1
---

# SYSTEM-INDEX

Top-level map of all system files in this vault — scaffold, agents, architecture, operations, setup, templates. Personal notes live separately under `01-personal/` and `_private/`.

See [system-taxonomy.md](system-taxonomy.md) for the full pattern.

## Tag convention

- `system/scaffold` — root-level scaffold (ARCHITECTURE, README, CLAUDE, HOME, etc.)
- `system/architecture` — architecture specs and design docs
- `system/operations` — runbooks, automation, recurring jobs
- `system/setup` — install + setup guides
- `system/skills` — skill system infrastructure
- `system/bus`, `system/search`, `system/eval`, `system/notifications` — subsystems
- `system/agent/<name>` — agent-specific docs (barry, harry, parry, …)
- `system/template` — repo templates in `.github/template/`

---

## Agents

Replace with your agent roster.

| Agent | Role | Spec | Folder |
|-------|------|------|--------|
| Larry | Orchestrator / OS | [[ml-brainclone-INDEX]] | `03-projects/ml-brainclone/` |
| Barry | Visual brain | — | [[03-projects/barry/barry]] |
| Harry | Audio brain | — | [[03-projects/harry/harry]] |
| Parry | Gatekeeper | — | [[03-projects/parry/parry]] |

---

## Scaffold (root)

Files that govern vault meta-structure and AI integration.

- [[ARCHITECTURE]] — vault architecture overview
- [[CLAUDE]] — project instructions for Claude Code
- [[CONTRIBUTING]] — contribution rules
- [[HOME]] — vault entry point
- [[README]] — vault readme
- [[SETUP]] — setup guide
- [[_active-context]] — active session context

---

## Subsystems

- [[bus/README|Brains-bus]] — inter-agent event bus
- [[search/README|Search]] — vault FTS5 + embedding search
- [[skills/SKILL-SPEC|Skills]] — skill system
- [[operations/nattskift/README|Night shift]] — nightly automation

---

## Templates

Files in `.github/template/` for bootstrapping new repos:

- ARCHITECTURE.md, CLAUDE.md, CONTRIBUTING.md
- LICENSE, PRIVACY.md, README.md, SETUP.md

---

## Live catalog (Dataview)

Auto-generated from `system/*` tags.

```dataview
TABLE WITHOUT ID
  file.link AS "File",
  filter(file.tags, (t) => startswith(t, "#system/")) AS "System tag"
FROM ""
WHERE contains(string(file.tags), "system/")
  AND !contains(file.path, "_private/")
  AND !contains(file.path, "06-archive/")
  AND !contains(file.path, "bin/")
SORT file.path ASC
```

### Counts per category

```dataview
TABLE WITHOUT ID
  T AS "Tag",
  rows.length AS "Count"
FROM ""
FLATTEN file.tags AS T
WHERE startswith(T, "#system/")
  AND !contains(file.path, "_private/")
  AND !contains(file.path, "06-archive/")
  AND !contains(file.path, "bin/")
GROUP BY T
SORT rows.length DESC
```

---

## Separation from personal notes

Personal content lives in:

- **`01-personal/`** — contacts, interests, goals, health, music, writing
- **`_private/`** — privacy 3-4 (sensitive), incl. owner profile

System files should never mix with personal reflections. If a system file starts collecting personal thoughts, move them to `01-personal/` or `_private/`.

---

**Maintenance:**
- Tag batch: `scripts/system_tag_batch.py` — re-run for new files
- Update Dataview categories as the system grows
