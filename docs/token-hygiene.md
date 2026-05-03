# Token Hygiene — Reducing Context Overhead

Claude Code loads several pieces of context on every turn: CLAUDE.md, MEMORY.md, plugin skill listings, MCP tool schemas, and conversation history. When these grow unchecked, productive tokens shrink.

## The problem

A typical setup accumulates overhead silently:

| Source | Tokens/turn | Loaded |
|--------|------------|--------|
| CLAUDE.md | 1,500–5,000 | Every turn |
| MEMORY.md index | 1,000–4,000 | Every turn |
| Plugin skill listings | 500–3,000 | Every turn |
| MCP tool schemas | 500–2,000 | Every turn |
| Conversation history | Growing | Every turn |
| Session init hook | 500–2,000 | In history |

A bloated setup can spend 70%+ of tokens on overhead before your actual prompt is read.

## Thresholds

| Component | Target | Why |
|-----------|--------|-----|
| **CLAUDE.md** | < 800 words (~1,000 tokens) | Loaded every turn. Move details to on-demand reference files |
| **MEMORY.md** | < 150 lines | Auto-loaded index. Truncated after ~200 lines. Keep entries to 1 line each |
| **Active plugins** | ≤ 5 | Each plugin lists skills in the system prompt. Disable unused ones |
| **MCP servers** | ≤ 3 always-on | Each ships tool schemas every request |
| **Conversation length** | ≤ 20 messages | Use /compact instead of /clear for continuity |

## The fix: on-demand loading

Instead of putting everything in CLAUDE.md, create reference files loaded only when needed:

```
CLAUDE.md (lean, ~800 words)
├── Core rules (privacy, conventions, search routing)
├── Session init steps
└── Reference table pointing to detail files:

| Reference | File |
|-----------|------|
| Barry rules | 03-projects/barry/barry-rules.md |
| Harry rules | 03-projects/harry/harry-rules.md |
| Milla guide | architecture/milla-guide.md |
| Bus commands | bus/README |
| Night shift | operations/nightly/README |
```

Larry reads the detail file when a task matches — one extra Read call, but thousands of tokens saved on every other turn.

Same for MEMORY.md: move domain-specific memories (e.g. all Barry prompt-craft rules) into a consolidated reference file. Replace 40 index entries with one pointer.

## Automated checking

Run `scripts/token_hygiene_check.py` weekly (or add to your reminder system):

```bash
python scripts/token_hygiene_check.py
```

Output:
```json
{
  "all_ok": true,
  "claude_md": {"ok": true, "words": 487, "threshold": 800},
  "memory_md": {"ok": true, "lines": 120, "threshold": 150},
  "plugins": {"ok": true, "active": 4, "threshold": 5}
}
```

Non-zero exit code when any threshold is exceeded — easy to wire into cron or night shift.

Configure via environment variables:
```bash
TOKEN_HYGIENE_CLAUDE_WORDS=1000
TOKEN_HYGIENE_MEMORY_LINES=200
TOKEN_HYGIENE_MAX_PLUGINS=6
```

## What NOT to do

- **Don't disable all plugins** — you'll re-type the same instructions manually. Keep 3-5 you actually use
- **Don't aggressive /clear** — lost context costs more than the overhead. Use /compact
- **Don't skip CLAUDE.md** — the rules matter. Just make them concise
- **Don't move session-critical rules to reference files** — privacy rules, search routing, and conventions must stay in CLAUDE.md since they apply to every turn
