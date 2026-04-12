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

# --- TEMPORAL AWARENESS ---
# Gives Larry a sense of time: clock, day, upcoming calendar events.
# Requires: gws CLI (https://github.com/nicholasgasior/gws) authenticated.

echo "--- Time & Calendar ---"
echo "Now: $(date '+%Y-%m-%d %H:%M') ($(date '+%A'))"
echo ""
if command -v gws &>/dev/null; then
    echo "Today:"
    gws calendar +agenda --today --format table 2>/dev/null || echo "(no events or GWS unavailable)"
    echo ""
    echo "Tomorrow:"
    gws calendar +agenda --tomorrow --format table 2>/dev/null || echo "(no events)"
else
    echo "(gws not installed — calendar unavailable)"
fi
echo ""

echo "=== INIT DONE — $(date +%Y-%m-%d) ==="

# NOTE: Playwright is NOT started at session init.
# It opens lazily on first use (Barry generation, web browsing etc).
# This allows multiple Larry sessions to run in parallel without conflicts.

exit 0
