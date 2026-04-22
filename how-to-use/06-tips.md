# 06 — Tips, Combos, and Power Moves

A collection of the most useful patterns once you're comfortable with the basics.

---

## The Best Workflows

### Starting a New Feature (the right way)
```
1. /plan [describe the feature]
      → Claude thinks through the approach, lists the files to touch,
        identifies risks, breaks it into steps

2. Review the plan and say "looks good, let's build it"

3. /tdd
      → Claude writes tests first, then the implementation

4. /code-review
      → Catches anything missed

5. /prp-commit
      → Clean, well-formatted commit message
```

### Coming Back to a Project After a Break
```
1. Open Claude Code in the project folder

2. /mem-search [what you were working on]
      → claude-mem surfaces your recent session history

3. /resume-session
      → Loads the last session's context

4. "What was I working on and what's left to do?"
      → Claude reconstructs the state from memory
```

### Cleaning Up Messy Code
```
1. /refactor-clean
      → Finds dead code, unused imports, duplication

2. /simplify
      → Rewrites complex functions to be cleaner

3. /code-review
      → Final check
```

### Deep-Diving an Unfamiliar Codebase
```
"Use the code-explorer agent to map out how authentication works in this repo"
      → Claude traces the full execution path and explains it
```

### Looking Up Docs Without Leaving Claude
```
/docs how do I use React Query's useMutation with optimistic updates?
/docs what's the syntax for SQLAlchemy relationship back_populates?
/docs Anthropic SDK streaming responses
```
This fetches live documentation — the answer is always current.

---

## Useful Phrases

**When you want Claude to think before acting:**
```
"Think through this carefully before doing anything"
"What are the tradeoffs here?"
"What could go wrong with this approach?"
```

**When you want multiple options:**
```
"Give me three different ways to approach this"
"What's the simplest solution? What's the most scalable one?"
```

**When something feels wrong:**
```
"I don't think that's right — explain your reasoning"
"What assumptions are you making here?"
"Double-check that against the actual file"
```

**When you want Claude to slow down:**
```
"Don't write any code yet — just explain what you'd do"
"Show me a plan first before making any changes"
```

---

## Things Worth Knowing

### Context Window
Claude can only hold so much in memory at once. In a long session:
- Use `/compact` to compress the history
- Start a `/new` session for an unrelated task
- The bigger the codebase Claude reads, the less conversation history it can hold

### Claude-mem Runs Passively
You don't manage it. Every session is recorded automatically. The only
time you interact with it is when searching past sessions with `/mem-search`
or browsing the dashboard at `http://localhost:37777`.

### Agents Run in the Background
When Claude spins up an agent, it happens silently. You'll see the result,
not the process. This is normal — it's just Claude delegating to a specialist.

### The Rules System
Your setup has coding standards, security rules, and workflow guidelines
saved in `~/.claude/rules/`. Claude follows these automatically. They cover:
- Code style (immutable patterns, small functions, no deep nesting)
- Security (no hardcoded keys, input validation, OWASP checks)
- Testing (80% coverage, TDD first)
- Git (conventional commits format)

You don't need to re-explain these — they're always active.

### Teaching Claude New Skills
Any time you have a document, tutorial, or spec you want Claude to know:
```
python yak_skill_builder.py
```
Feed it the file. The knowledge is available in every future session.

---

## When Things Go Wrong

| Problem | Fix |
|---------|-----|
| Claude seems confused | `/clear` and start fresh |
| Responses getting slow | `/compact` to free up context |
| Claude forgot something important | "Remember that…" to save it |
| Build is broken | `/build-fix` |
| Claude is going in the wrong direction | "Stop. Let's back up. What I actually need is…" |
| Something seems off about the code | `/code-review` or `/verify` |
| Security concern | "Review this for security issues" |

---

## The Most Underused Features

1. **`/docs`** — Most people just Google things. Ask Claude instead and get
   answers in the context of your actual project.

2. **`/mem-search`** — Incredibly useful when returning to a project.
   People forget it exists.

3. **`/council`** — Gets multiple AI perspectives on a hard decision.
   Great for architecture choices.

4. **`/plan` before coding** — Skipping this is the most common mistake.
   A 2-minute plan prevents hours of refactoring.

5. **YakAI Skill Builder** — Every external API, framework, or standard
   you work with regularly should have its own skill. Feed it the docs once,
   benefit forever.
