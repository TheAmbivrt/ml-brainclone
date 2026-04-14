# Notifications Setup — Telegram Two-Way Channel

Larry communicates with the user via Telegram: outbound notifications (events, approvals, errors) and inbound responses (text messages, inline keyboard callbacks).

---

## Architecture

```
Larry / Barry / Harry / Parry
         │  (larry_notify.py)
         ▼
  Telegram Bot API ──────────────────┐
         │                           │
         ▼                           │
  User's Telegram app                │
         │                           │
         ▼ (text / callback)         │
  larry_bot_listener.py ◄────────────┘
  (long-polling daemon)
         │
         ▼
  _private/notify-queue.json
  (async bridge for other scripts)
```

---

## Components

### `larry_notify.py` — Send
Importable module. All Larry scripts: `from larry_notify import notify`.

```python
notify(text, title=None, priority="default", buttons=None)
notify_approval(subject, body)         # Three-button approval flow
notify_barry_done(count, path, counter_end)
notify_error(source, message)
```

Config: `{{VAULT_PATH}}/_private/larry-telegram-config.json`
```json
{"bot_token": "<BOT_TOKEN>", "chat_id": <CHAT_ID>}
```

### `larry_bot_listener.py` — Receive
Long-polling daemon. Run at startup via Task Scheduler.

Handles:
- **Inline keyboard callbacks**: `approve` / `edit` / `skip` data values
- **Freetext messages**: queued + answered via `claude -p --system-prompt`
- **Commands**: `/status`, `/queue`, `/stop`

All inbound data written to `_private/notify-queue.json`.
Other scripts poll this file to read approvals.

---

## Setup

### 1. Create bot
1. Open Telegram → search `@BotFather`
2. Send `/newbot` → follow prompts → copy `BOT_TOKEN`

### 2. Get CHAT_ID
```bash
python larry_notify.py --setup
# Paste token → send a message to your bot → CHAT_ID auto-fetched
# Config saved to _private/larry-telegram-config.json
```

### 3. Test
```bash
python larry_notify.py --message "Larry is online."
```

### 4. Start listener
```bash
python larry_bot_listener.py
```

**Windows startup (recommended):** Add to Task Scheduler → trigger At logon → action: `pythonw larry_bot_listener.py` (no console window).

---

## Notification categories

| Trigger | Function | Priority |
|---------|----------|----------|
| Barry batch complete | `notify_barry_done()` | default |
| Approval request (mail, action) | `notify_approval()` | high |
| Error in any script | `notify_error()` | high |
| Custom / ad-hoc | `notify()` | any |

---

## Approval flow

```python
# Send approval request with three buttons
notify_approval(
    subject="Mail to Samson",
    body="Hi Samson,\n\nFollowing up on...",
    approve_data="mail_approve",
    edit_data="mail_edit",
    skip_data="mail_skip",
)

# Read result (polling notify-queue.json)
queue = json.loads(Path("_private/notify-queue.json").read_text())
pending = [e for e in queue if not e.get("read") and e["type"] == "callback"]
```

---

## Conversational replies

The listener calls `claude -p --system-prompt "<persona>"` from a neutral working directory (no `CLAUDE.md`) for freetext messages. This gives Larry-flavored responses without triggering the full session init. Response timeout: 45s.

---

## Privacy

- `_private/larry-telegram-config.json` — privacy L3. Never commit.
- `_private/notify-queue.json` — privacy L3. Ephemeral, not committed.
- Bot name is personal/internal — never referenced in public repos.
