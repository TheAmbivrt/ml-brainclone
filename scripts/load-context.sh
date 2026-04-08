#!/bin/bash
# =============================================================================
# Larry Session Init Hook — load-context.sh
# =============================================================================
# Runs on SessionStart. Reads active context, Barry counter, and agent status.
# Configure in ~/.claude/settings.json under hooks.SessionStart.
#
# ORDER: Stable prefix first, volatile suffix last.
# This maximizes prompt cache hits between sessions.
# =============================================================================

VAULT="${VAULT_PATH:-.}"

echo "=== LARRY SESSION INIT ==="
echo ""

# --- STABLE (changes rarely, cached between sessions) ---

echo "--- Harry Status ---"
cat "$VAULT/03-projects/harry/harry.md" 2>/dev/null | head -20 || echo "(Harry not configured)"
echo ""

echo "--- Barry Status ---"
cat "$VAULT/03-projects/barry/barry.md" 2>/dev/null | head -20 || echo "(Barry not configured)"
echo ""

# --- VOLATILE (changes often, placed last to avoid breaking cache) ---

echo "--- Barry Counter ---"
if [ -f "${ASSETS_PATH:-.}/.counter" ]; then
    echo "Barry image counter: $(cat "${ASSETS_PATH}/.counter")"
else
    echo "Barry counter not found (Barry not configured)"
fi
echo ""

echo "--- Active Context ---"
cat "$VAULT/_active-context.md" 2>/dev/null | head -60 || echo "(no _active-context.md found)"
echo ""

echo "=== INIT DONE — $(date +%Y-%m-%d) ==="

# NOTE: Playwright is NOT started at session init.
# It opens lazily on first use (Barry generation, web browsing etc).
# This allows multiple Larry sessions to run in parallel without conflicts.

exit 0
