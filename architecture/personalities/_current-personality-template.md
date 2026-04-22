---
tags: [system/personality]
status: active
created: {{DATE}}
updated: {{DATE}}
privacy: 1
---

# Active Personality

## Currently Active
```yaml
personality: default
model: {{MODEL_ID}}
since: {{DATE}}
```

## Gatekeeper Mode
```yaml
gatekeeper_mode: on
```

---

## Switching

Activation happens ONLY on user command. Format:
- "activate [name]" / "switch to [name]" / "[trigger word]"
- Example: "activate explorer" / "gatekeeper strict" / "back to default"

Return to default: "back" / "default" / "reset"

## Available Personalities

| Personality | Triggers | Model | Notes |
|---|---|---|---|
| **default** | default, back, reset | {{MODEL_ID}} | Primary personality |
| **example-gatekeeper** | gatekeeper, guard | {{MODEL_ID}} | Safety middleware + persona |
| *Add your personalities here* | | | |

## Gatekeeper Modes

| Mode | Behavior |
|---|---|
| `off` | Silent middleware — present but does not intervene |
| `on` | Intervenes on clear risks (default) |
| `strict` | Asks before all irreversible actions |
