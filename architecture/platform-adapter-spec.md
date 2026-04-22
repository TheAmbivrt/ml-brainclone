# Platform Adapter — Spec

> Abstraction for multi-channel presence. Telegram today, Signal/Matrix/Discord/SMS tomorrow — without touching the core brain.

**Status:** Spec complete, implementation tied to Telegram v2 / PWA build.
**Inspiration:** Hermes pattern — adapter pattern for platform-agnostic core.
**Principle:** The brain should not know whether it's talking via Telegram, Signal, or a PWA chat. Just that an `InboundEvent` arrived and an `OutboundResponse` needs to be sent.

---

## 1. Why Now

The bot listener is a monolith (~2600 lines). Telegram protocol, event routing, brain logic, vault writing, image sorting, TTS — all mixed together. Two problems:

1. **Adding Signal/Matrix = cloning the entire file.** Operations and maintenance break down.
2. **Refactoring without direction = breaking production.** The Telegram bot is used daily.

The adapter pattern solves both — without requiring an immediate refactor of existing code. The spec is the foundation; implementation happens when the PWA build activates.

---

## 2. Mapping the Current Listener

### Platform-Specific (moves to adapter)

| Function | Description |
|----------|-------------|
| `_api()` | Calls Telegram Bot API |
| `_send()` | Sends text message |
| `_send_voice()` | Sends voice (OGG/Opus) |
| `_download_telegram_photo()` | Downloads photo from Telegram |
| `_download_telegram_file()` | Downloads any file |
| `_poll_loop()` | Long polling loop |
| `_kill_other_instances()` | Telegram-specific 409 conflict handling |

### Event Routing (partially platform-agnostic)

| Function | Notes |
|----------|-------|
| `handle_message()` | Takes Telegram update format — needs normalization to `InboundEvent` |
| `handle_photo()` | Same — Telegram format embedded |
| `handle_voice()` | Same |
| `handle_callback()` | Telegram inline keyboard — other platforms have their own mechanisms (Signal: reactions, Discord: buttons). Needs mapping |
| `handle_reaction()` | Telegram reaction format |
| `handle_command()` | `/!`, `/?`, `/stop` — generic, but `text.startswith("/")` parsing is a platform convention |

### Platform-Agnostic (stays in core)

| Function | Description |
|----------|-------------|
| `_larry_reply()` | The brain — Anthropic SDK |
| `_build_context_prompt()` | Vault + memory + history context |
| `_execute_tool()` | Tool handling (vault search, etc.) |
| `_analyze_sentiment()` | Text analysis |
| `_larry_speak()` | Harry TTS (platform-independent) |
| `_analyze_photo()` | Vision (Claude/Gemini) — platform-independent |
| `_create_vault_note()` | Vault writing — platform-independent |
| `_transcribe_audio()` | Gemini transcription — platform-independent |
| Queue/history/daily-log | Persistence — platform-independent |
| `_write_heartbeat()` | Watchdog — platform-independent |
| Brains-bus integration | Inter-agent communication — platform-independent |

**Conclusion:** Approximately 600-800 lines are platform-specific. The rest (1800+ lines) can stay platform-agnostic in the core.

---

## 3. Adapter Interface (Python pseudocode)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal, Optional

@dataclass
class InboundEvent:
    """Platform-normalized event."""
    platform: str                                   # "telegram", "signal", "matrix", ...
    event_type: Literal["text", "voice", "photo", "callback", "reaction", "command"]
    channel_id: str                                 # chat_id, room_id, etc.
    user_id: str                                    # sender
    text: str = ""                                  # for text/command/callback
    media_ref: Optional[str] = None                 # platform-specific file pointer
    command: Optional[str] = None                   # for command: "/status", "/stop"
    callback_data: Optional[str] = None             # for callback: "approve_42"
    reply_to: Optional[str] = None                  # message_id this replies to
    raw: dict = None                                # original event for debug

@dataclass
class OutboundResponse:
    """Platform-agnostic response."""
    response_type: Literal["text", "voice", "photo", "no_response"]
    text: str = ""
    audio_path: Optional[Path] = None
    photo_path: Optional[Path] = None
    caption: str = ""
    reply_to: Optional[str] = None                  # for threaded replies

class BasePlatformAdapter(ABC):
    """Abstract platform adapter."""

    name: str                                       # "telegram", "signal", ...

    # === Lifecycle ===
    @abstractmethod
    def start(self) -> None:
        """Establish connection, register webhooks/poll loop."""

    @abstractmethod
    def stop(self) -> None:
        """Shut down cleanly."""

    @abstractmethod
    def heartbeat(self) -> bool:
        """True if adapter is alive and can receive/send."""

    # === Inbound (platform → brain) ===
    @abstractmethod
    def receive(self) -> Iterator[InboundEvent]:
        """Yield normalized events. Long-polling, websocket, or webhook queue."""

    # === Outbound (brain → platform) ===
    @abstractmethod
    def send(self, channel_id: str, response: OutboundResponse) -> None:
        """Send response back to platform."""

    # === Media handling ===
    @abstractmethod
    def download_media(self, media_ref: str, dest_dir: Path) -> Path:
        """Download a media file and save locally. Return local path."""
```

---

## 4. Core Loop (platform-agnostic)

```python
def core_loop(adapters: list[BasePlatformAdapter]):
    """A single core loop for all adapters."""
    for adapter in adapters:
        adapter.start()

    try:
        while running:
            for adapter in adapters:
                for event in adapter.receive():
                    process_event(adapter, event)
    finally:
        for adapter in adapters:
            adapter.stop()

def process_event(adapter: BasePlatformAdapter, event: InboundEvent):
    """Route event → brain → response via adapter."""
    if event.event_type == "command":
        response = handle_command(event)
    elif event.event_type == "text":
        response = brain_reply(event)
    elif event.event_type == "voice":
        transcript = transcribe_audio(adapter.download_media(event.media_ref, VOICE_DIR))
        response = brain_reply(event_with_text(event, transcript))
    elif event.event_type == "photo":
        photo_path = adapter.download_media(event.media_ref, PHOTO_DIR)
        analyze_and_sort(photo_path, event.text)  # image pipeline
        response = OutboundResponse(response_type="text", text="Photo sorted.")
    # ...

    if response.response_type != "no_response":
        adapter.send(event.channel_id, response)
```

---

## 5. Telegram Adapter (sketch)

```python
class TelegramAdapter(BasePlatformAdapter):
    name = "telegram"

    def __init__(self, token: str, chat_id: int):
        self.token = token          # {{BOT_TOKEN}}
        self.chat_id = chat_id      # {{TELEGRAM_USER_ID}}
        self.offset = None

    def start(self):
        # Flush pending updates, take PID lock, write heartbeat
        ...

    def receive(self) -> Iterator[InboundEvent]:
        params = {"timeout": 30, "allowed_updates": [...]}
        if self.offset is not None:
            params["offset"] = self.offset
        data = self._api("getUpdates", params)
        for upd in data["result"]:
            self.offset = upd["update_id"] + 1
            yield self._normalize(upd)

    def send(self, channel_id: str, response: OutboundResponse):
        if response.response_type == "text":
            self._api("sendMessage", {"chat_id": channel_id, "text": response.text})
        elif response.response_type == "voice":
            self._send_voice(channel_id, response.audio_path)
        # ...

    def _normalize(self, telegram_update: dict) -> InboundEvent:
        """Telegram format → InboundEvent."""
        if "message" in telegram_update:
            msg = telegram_update["message"]
            if "voice" in msg:
                return InboundEvent(
                    platform="telegram",
                    event_type="voice",
                    channel_id=str(msg["chat"]["id"]),
                    user_id=str(msg["from"]["id"]),
                    media_ref=msg["voice"]["file_id"],
                    raw=telegram_update,
                )
            # ... etc
```

---

## 6. Migration Strategy

**Don't rush.** Three phases:

### M1 — Shadow (safe, parallel)
- Create `notifications/adapters/base.py` with abstract class
- Create `notifications/adapters/telegram.py` extracting Telegram API from existing listener
- Adapter is NOT used by the main listener yet — it lives alongside

### M2 — Migrate (risk moment)
- Refactor the main listener to use `TelegramAdapter`
- Keep all heartbeat/PID lock/watchdog mechanisms
- Test in parallel environment (separate bot token) before production

### M3 — Additional Adapters (value delivery)
- `signal.py`, `matrix.py`, `discord.py` — when actively needed
- `pwa.py` — websocket adapter when PWA frontend is built

**Trigger for M1+M2:** When the Telegram v2 build activates (PWA build). Currently parked.

---

## 7. Risks

| Risk | Mitigation |
|------|------------|
| Breaking Telegram bot during refactor | Shadow implementation + parallel test before cutover |
| Adapter abstraction wrong for Signal/Matrix | Wait until first non-Telegram adapter is needed before finalizing interface |
| 409 Conflict logic hard to normalize | Keep Telegram-specific logic in `TelegramAdapter`, only expose clean `start()`/`stop()` |
| Callback/reaction mismatch between platforms | Map to generic `event_type="callback"` with `callback_data` — adapter handles platform-specific bridging |
