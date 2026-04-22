# Notifications Setup — Telegram Multi-Modal Channel

Larry communicates with the user via Telegram: outbound notifications, inbound text/photo/voice, conversational replies with optional TTS voice, and daily conversation logs.

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
         ▼ (text / photo / voice     │
            / callback)              │
  larry_bot_listener.py ◄────────────┘
  (long-polling daemon)
         │
         ├─► _private/notify-queue.json    (async bridge)
         ├─► _private/telegram/YYYY-MM-DD.md  (daily log)
         ├─► _private/telegram-chat-history.json  (rolling context)
         ├─► Claude Agent SDK (vision — primary, uses Claude Code auth)
         ├─► Gemini 2.5 Flash (vision fallback / STT)
         ├─► Gemini TTS (voice responses)
         └─► Anthropic SDK (text responses — see v2 spec below)
```

> **v2 Migration (planned):** The listener is being rebuilt with Anthropic SDK directly, replacing the `claude -p` subprocess approach. The brain becomes interface-agnostic (`LarryBrain` class) shared between Telegram, a PWA chat interface, and potentially CLI. See [architecture/telegram-v2-spec.md](../architecture/telegram-v2-spec.md).

---

## Components

### `larry_checkin.py` — Proactive Check-in

Scheduled script (e.g. 10:00, 15:00, 20:00 via Task Scheduler). Reads vault context, calendar, and last interaction — sends a Telegram message ONLY if there's something actionable. Never PDA.

```bash
python larry_checkin.py              # Run check-in logic
python larry_checkin.py --dry-run    # Show what would be sent
python larry_checkin.py --force      # Send regardless of filters
```

**Anti-PDA rules (configurable):**
- Minimum 4 hours between check-ins
- Maximum 2 proactive check-ins per day
- Quiet hours: 23:00-07:00
- Skip if recent chat within last 60 minutes

### `larry_session_nudge.py` — Post-Session Nudge

Called as a Claude Code hook (`PostSessionEnd`) or manually. Reads latest session activity and sends a short summary message via Telegram.

```bash
python larry_session_nudge.py "short session summary"
python larry_session_nudge.py --auto    # Read from latest git activity
```

### `larry_notify.py` — Send

Importable module. All Larry scripts: `from larry_notify import notify`.

```python
notify(text, title=None, priority="default", buttons=None)
notify_approval(subject, body)         # Three-button approval flow
notify_barry_done(count, path, counter_end)
notify_error(source, message)
notify_photo(photo_path, caption=None) # Send image via Telegram
```

Config: `{{VAULT_PATH}}/_private/larry-telegram-config.json`
```json
{"bot_token": "<BOT_TOKEN>", "chat_id": <CHAT_ID>}
```

### `larry_bot_listener.py` — Receive & Respond

Long-polling daemon. Run at startup via Task Scheduler.

Handles:
- **Text messages**: conversational reply via `claude -p` with rolling context
- **Photo messages**: download → Gemini vision analysis → vault-note → categorized reply
- **Voice messages**: download → Gemini STT transcription → Larry reply (text + optional TTS)
- **Inline keyboard callbacks**: `approve` / `edit` / `skip` data values
- **Commands**: `/status`, `/voice`, `/queue`, `/stop`

All inbound data written to `_private/notify-queue.json`.

---

## Inbound Pipelines

### Text → Conversational Reply

```
User sends text
  → sentiment analysis (keyword-based)
  → build prompt with conversation history (last 10 messages)
  → claude -p --system-prompt <persona> (45s timeout)
  → text reply to Telegram
  → if /voice enabled: TTS → voice reply
  → logged in daily log + chat history
```

### Photo → Vision Analysis

```
User sends photo
  → download largest resolution from Telegram API
  → save to {{ASSETS_PATH}}/imported/telegram/
  → Claude Agent SDK (primary) — spawns `claude` via bundled CLI,
    uses existing Claude Code auth (no separate API key needed),
    tools restricted to [Read], max_turns=3 → returns JSON:
    {category, title, description, tags, extracted, vault_note, suggested_action}
    Falls back to Gemini 2.5 Flash on exception or empty response
    (useful when Claude refuses NSFW or content-policy sensitive frames).
  → create vault-note in {{VAULT_PATH}}/00-inbox/
  → queue entry with analysis metadata
  → categorized reply (receipt/inspiration/screenshot/document/photo)
  → logged in daily log
```

**Photo categories:**
| Category | What's extracted | Emoji |
|----------|-----------------|-------|
| receipt | amount, store, date | 🧾 |
| inspiration | style, mood, composition | 🎨 |
| screenshot | text content, UI elements | 📱 |
| document | text content | 📄 |
| photo | scene description | 📸 |
| meme | description (vault_note=false) | 😂 |

### Voice → Transcription + Reply

```
User sends voice message
  → download .oga/.ogg from Telegram API
  → save to {{AUDIO_PATH}}/imported/telegram/
  → Gemini 2.5 Flash audio transcription → JSON:
    {transcript, language, summary, tags, mood, action_items}
  → create vault-note in {{VAULT_PATH}}/00-inbox/
  → Larry replies to transcript (text + optional TTS voice)
  → logged in daily log
```

---

## Voice Responses (TTS)

Larry can respond with voice messages using Gemini TTS. Disabled by default — toggle with `/voice`.

### Voice Profile

Each personality gets a voice profile. Larry's default:

```python
LARRY_VOICE   = "Enceladus"
LARRY_PITCH   = "-20%"        # baseline pitch (overridden per sentiment)
LARRY_RATE    = "1.2"         # baseline rate (overridden per sentiment)
TTS_MODEL     = "gemini-2.5-pro-preview-tts"

LARRY_PERSONA = (
    "[Deep voice. Calm authority. Late-night radio host who has seen it all. "
    "Charlie Sheen's wit meets Ted Lasso's warmth — never loud, never rushed. "
    "Dry humor lives just beneath every sentence. Speaks like he means it.]"
)
```

### Sentiment-Adaptive Tone

Incoming messages are analyzed for sentiment. Each sentiment maps to a full profile: emotion directive + pitch + rate override. Text replies are **suppressed** when `/voice` is active — only the voice message is sent.

| Sentiment | Rate | Pitch | Character |
|-----------|------|-------|-----------|
| `tired`   | 0.90 | -28%  | Soft, late-night, running on fumes |
| `sad`     | 0.95 | -26%  | Gentle, unhurried, just present |
| `angry`   | 1.00 | -24%  | Quiet intensity, measured restraint |
| `frustrated` | 1.05 | -23% | Calm, grounded, empathetic |
| `curious` | 1.15 | -20%  | Thoughtful, leaning in |
| `neutral` | 1.20 | -20%  | Dry wit, slightly amused |
| `happy`   | 1.25 | -17%  | Warm, genuine, real smile |
| `playful` | 1.30 | -16%  | Light, tease, laugh under the surface |
| `excited` | 1.35 | -15%  | Energized, can barely contain it |

Longer replies (>120 chars) get automatic `<break>` pauses after sentence endings.

### TTS Pipeline

```
Larry text reply
  → _analyze_sentiment(user_message) → sentiment
  → SENTIMENT_PROFILE[sentiment] → {emotion, rate, pitch}
  → SSML: LARRY_PERSONA + emotion + <prosody pitch rate> + auto-breaks
  → Gemini TTS (gemini-2.5-pro-preview-tts) → PCM 24kHz
  → FFmpeg atempo + libmp3lame → MP3 192kbps
  → send as Telegram voice message (text suppressed when /voice active)
```

---

## Persistence Layers

Three parallel persistence mechanisms:

| Layer | Path | Purpose | Retention |
|-------|------|---------|-----------|
| **Chat history** | `_private/telegram-chat-history.json` | Rolling context for claude -p (last 10 messages) | Overwritten continuously |
| **Daily log** | `_private/telegram/YYYY-MM-DD.md` | Full daily transcript (text, photos, voice, callbacks) | Permanent, vault-searchable |
| **Queue** | `_private/notify-queue.json` | Async bridge for other scripts | Ephemeral |

### Daily Log Format

```markdown
---
tags: [telegram, dagbok, auto]
status: active
created: 2026-04-14
privacy: 3
---

# Telegram — 2026-04-14

- `12:06` **User:** Message text here
- `12:06` *Larry:* Response text here
- `12:07` 📸 **Foto:** Title (category) → `filename.jpg`
- `12:14` 🎙️ **Rost:** Summary → `voice-file.oga`
- `12:15` 🔘 **Callback:** ✅ Godkänd
```

These logs are indexable by MemPalace and searchable in Obsidian.

---

## Commands

| Command | Action |
|---------|--------|
| `/status` | Online-status, uptime, restarts, queue, voice |
| `/voice` | Toggla röst på/av (default: av) |
| `/queue` | Visa antal olästa i queue |
| `/clearqueue` | Rensa hela notify-queue.json |
| `/uptime` | Uptime + starttid + restarts |
| `/stop` | Stäng ner listener-processen |

**OBS:** `/stop` stänger processen helt — omstart måste ske manuellt eller via Task Scheduler. Inget `/start`-kommando finns (ingen aktiv process att ta emot det).

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

**Important:** Only ONE listener instance at a time. Multiple instances cause `409 Conflict` errors from the Telegram API. Kill existing processes before restarting.

**Startup flush:** On every start, the listener calls `getUpdates` once with `offset=-1` to drain any stale messages (e.g. old `/stop` commands sitting in the Telegram queue). This prevents the daemon from immediately shutting down after a restart.

### 5. Dependencies
```bash
pip install requests google-genai claude-agent-sdk
# FFmpeg required for TTS (system install)
# claude-agent-sdk bundles its own `claude` CLI — uses existing Claude Code auth
```

### 6. GCP Setup (for vision + voice)
Gemini vision/STT/TTS requires Google Cloud authentication:
```bash
gcloud auth application-default login
# Project must have Vertex AI API enabled
```

---

## Multi-Bot Architecture (Personalities)

Each personality can have its own Telegram bot for separate conversations:

```json
{
  "bots": {
    "larry": {"bot_token": "...", "chat_id": 123},
    "hope":  {"bot_token": "...", "chat_id": 123},
    "self":  {"bot_token": "...", "chat_id": 123}
  }
}
```

Each bot gets:
- Its own voice profile (voice name + pitch + rate + emotion style)
- Its own system prompt (from `personalities/{name}/character.md`)
- Full multimedia support (text + photo + voice)

---

## Privacy

- `_private/larry-telegram-config.json` — privacy L3. Never commit.
- `_private/notify-queue.json` — privacy L3. Ephemeral, not committed.
- `_private/telegram-chat-history.json` — privacy L3. Rolling context.
- `_private/telegram/*.md` — privacy L3. Daily logs, vault-searchable.
- Bot name is personal/internal — never referenced in public repos.
- Voice audio files stored outside vault (no binaries in vault).
