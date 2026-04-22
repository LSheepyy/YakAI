# 04 — Memory: How Claude Remembers Things

Your setup has two separate memory systems that work together.
Neither replaces the other — they do different things.

---

## System 1: File-Based Memory (Manual)

**What it is:** A folder of markdown files where facts about you and your
projects are saved. Claude reads these at the start of every session.

**Where it lives:**
```
C:\Users\avery\.claude\projects\...\memory\
```

**What gets saved here:**
- Your preferences ("don't add trailing summaries to responses")
- Project context ("this is a healthcare app, PHI compliance is critical")
- Your background ("user is a Python dev, new to React")
- Feedback you've given Claude

**How to use it:**

Tell Claude to remember something:
```
"Remember that I prefer tabs over spaces in this project"
"Remember that the API key is stored in .env, never hardcoded"
"Remember that Tommy is my collaborator on this project"
```

Claude will save it as a memory file automatically.

Tell Claude to forget something:
```
"Forget that I prefer dark mode — I changed my mind"
```

Read your memories:
```
/memory
```

---

## System 2: claude-mem (Automatic)

**What it is:** A background service that silently watches every session,
records what was built/fixed/decided, and injects relevant past context
back into future sessions automatically.

**You don't have to do anything.** It runs passively.

### What It Captures

Every tool call Claude makes gets observed and categorised:

| Type | Example |
|------|---------|
| Feature | "Added OAuth2 login with PKCE flow" |
| Bug Fix | "Fixed token expiry comparing different timezones" |
| Decision | "Chose Zustand over Redux — simpler API for this scale" |
| Discovery | "Found that the API rate-limits at 100 req/min per user" |
| Change | "Updated README with setup instructions" |
| Refactor | "Extracted auth logic into its own module" |

### Searching Past Sessions

```
/mem-search how did we set up the database?
/mem-search what was the decision about auth?
/mem-search login bug
```

This searches everything claude-mem has ever recorded across all sessions.
Extremely useful when returning to a project after weeks away.

### Web Dashboard

Claude-mem has a web UI where you can browse all your memories:
```
http://localhost:37777
```
(Only works when the claude-mem worker is running)

### Starting the Worker Manually

Claude-mem starts automatically when you open Claude Code. If it's not running:
```bash
npx claude-mem start
```

Check if it's running:
```bash
npx claude-mem status
```

---

## How They Work Together

```
File Memory  →  Stores facts YOU tell it to remember
               (preferences, project rules, your background)

claude-mem   →  Records everything Claude DOES automatically
               (what was built, fixed, decided in each session)
```

**Example scenario:**

You come back to a project after 3 weeks away:

1. Claude reads your **file memory** and knows: you prefer TypeScript,
   the project uses Supabase, Tommy is a collaborator.

2. claude-mem **injects context** from past sessions: the last session
   fixed a bug in the payment flow, you decided to use Stripe Webhooks,
   and there's a known issue with the invoice PDF generator.

You pick up right where you left off, even if you've forgotten the details.

---

## Quick Commands Summary

```
"Remember that..."           →  saves to file memory
"Forget that..."             →  removes from file memory
/memory                      →  view file memories
/mem-search [topic]          →  search claude-mem session history
/save-session                →  manually save current session
/resume-session              →  load context from a previous session
http://localhost:37777       →  browse all memories in browser
```
