# 01 — Basics: Talking to Claude

You don't need special commands for most things. Just describe what you want
in plain English. Claude reads your files, understands your project, and acts.

---

## Just Ask

```
"Add a dark mode toggle to the settings page"
"Why is this function returning undefined?"
"Refactor this file so it's easier to read"
"What does this code do?"
```

Claude will read the relevant files itself — you don't need to paste code in.

---

## Useful Built-In Slash Commands

These are Claude Code's own commands, always available.

| Command | What It Does |
|---------|-------------|
| `/help` | List all available commands |
| `/clear` | Wipe the conversation and start fresh (keeps files) |
| `/compact` | Summarise the conversation to free up context space |
| `/cost` | Show how many tokens this session has used |
| `/doctor` | Diagnose if something feels broken |
| `/bug` | Report a Claude Code bug to Anthropic |
| `/memory` | Open your saved memory files |
| `/init` | Set up Claude for a new project (creates CLAUDE.md) |
| `/review` | Quick code review of recent changes |

### Example — /compact
When a session gets very long, Claude slows down. Run `/compact` to compress
the history. Claude keeps the important context but frees up space.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + C` | Cancel what Claude is doing right now |
| `Escape` | Soft-cancel (Claude finishes the current step then stops) |
| `↑ Arrow` | Go back to your previous message |
| `Shift + Enter` | New line without sending |
| `Alt + T` | Toggle extended thinking (deeper reasoning) |
| `Ctrl + O` | Show Claude's thinking out loud |

---

## How to Give Good Instructions

**Be specific about what you want, not how to do it.**

```
Bad:  "Fix my code"
Good: "The login button does nothing when clicked — find out why and fix it"

Bad:  "Make it better"
Good: "This function is hard to read. Simplify it without changing what it does"
```

**Mention the file if you know it:**
```
"In auth.py, the token expiry check is wrong — it's comparing timestamps in
different timezones. Fix it."
```

**Describe the outcome you want:**
```
"I want users to see a loading spinner while the API call is in progress.
Add that to the dashboard page."
```

---

## When Claude Gets Lost

If Claude seems confused or goes off-track:

1. `/clear` — start fresh (most effective)
2. Or just say: "Stop. Let's start over. Here's what I actually need: …"

Claude does not take it personally.
