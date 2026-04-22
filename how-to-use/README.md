# YakAI — How to Use This Setup

Welcome. This folder is your cheat sheet for everything installed into this AI.
Read these in order the first time, then use them as a quick reference.

---

## Files in This Folder

| File | What It Covers |
|------|----------------|
| [01-basics.md](01-basics.md) | Everyday commands, how to talk to Claude |
| [02-agents.md](02-agents.md) | Sub-agents that do specialised work for you |
| [03-skills.md](03-skills.md) | Slash-command skills (the biggest library) |
| [04-memory.md](04-memory.md) | How Claude remembers things between sessions |
| [05-yak-builder.md](05-yak-builder.md) | Your custom Skill Builder GUI tool |
| [06-tips.md](06-tips.md) | Power tips and combinations |

---

## 30-Second Cheat Sheet

```
Ask naturally         →  just type what you want
Review my code        →  /code-review
Plan a feature        →  /plan  or  /feature-dev
Fix a broken build    →  /build-fix
Write tests first     →  /tdd
Search past sessions  →  /mem-search
Look up docs          →  /docs  (e.g. "/docs how do I use useEffect?")
Teach Claude new info →  run  python yak_skill_builder.py
```

---

## The Big Picture

Your setup has four layers:

1. **Claude itself** — the core AI. Just talk to it.
2. **Agents** — specialist AIs Claude spins up for specific tasks (code review, security, planning…).
3. **Skills** — pre-written playbooks Claude follows when you use a slash command.
4. **Memory** — two systems that help Claude remember your work across sessions.

Each layer is explained in its own file above.
