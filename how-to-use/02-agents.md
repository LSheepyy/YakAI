# 02 — Agents: Specialist AIs

Agents are separate AI instances that Claude spins up to do specific jobs.
Think of them as hiring a specialist for a task — a security expert, a
test engineer, an architect — instead of asking a generalist to do everything.

You don't always invoke agents manually. Many are triggered automatically
based on what you're doing.

---

## How Agents Work

When Claude needs specialised help, it launches an agent in the background.
The agent reads the relevant code, does its job, and reports back. You see the
result without having to manage it yourself.

---

## The Most Useful Agents

### For Everyday Coding

| Agent | When to Use | How It's Triggered |
|-------|------------|-------------------|
| `code-reviewer` | After writing or changing code | Auto, or just say "review this" |
| `security-reviewer` | Before committing auth, API, or user-input code | Auto on risky code, or ask manually |
| `tdd-guide` | When starting a new feature or fixing a bug | Say "use TDD" or `/tdd` |
| `build-error-resolver` | When a build or compile fails | Auto on errors, or ask manually |
| `planner` | Before building something complex | Say "plan this" or `/plan` |

### For Code Quality

| Agent | What It Does |
|-------|-------------|
| `refactor-cleaner` | Finds and removes dead/duplicate code |
| `code-simplifier` | Rewrites messy code to be cleaner |
| `performance-optimizer` | Spots slow code and suggests fixes |
| `silent-failure-hunter` | Finds errors that are being swallowed silently |
| `type-design-analyzer` | Reviews your data types and interfaces |

### For Specific Languages

| Agent | Language |
|-------|---------|
| `typescript-reviewer` | TypeScript / JavaScript |
| `python-reviewer` | Python |
| `rust-reviewer` | Rust |
| `go-reviewer` | Go |
| `java-reviewer` | Java / Spring Boot |
| `kotlin-reviewer` | Kotlin / Android |
| `flutter-reviewer` | Flutter / Dart |

### For Docs & Testing

| Agent | What It Does |
|-------|-------------|
| `doc-updater` | Keeps your README and docs in sync with code |
| `e2e-runner` | Writes and runs end-to-end tests |
| `pr-test-analyzer` | Reviews how well your PR is tested |
| `database-reviewer` | Reviews SQL queries and schema design |

### Specialised

| Agent | What It Does |
|-------|-------------|
| `architect` | Designs system architecture for new features |
| `code-architect` | Maps out file structure and implementation plan |
| `code-explorer` | Deep-dives into an existing codebase to understand it |
| `seo-specialist` | SEO audit and fixes |
| `a11y-architect` | Accessibility (WCAG compliance) review |
| `healthcare-reviewer` | Checks medical/clinical code for safety |

---

## Examples

### "Review my code after I write it"
Just write the code and Claude will automatically use `code-reviewer`.
Or say: `"Review the changes I just made to api.py"`

### "I want to do this the right way with tests"
```
"I need to add a user search feature. Help me build it test-first."
```
Claude will use `tdd-guide` to walk you through writing tests before code.

### "My build is failing"
Paste the error or just say:
```
"The build is failing. Here's the error: [paste error]"
```
Claude uses `build-error-resolver` to find the root cause and fix it.

### "Is this safe to ship?"
```
"Review this auth code for security issues before I commit it"
```
Claude uses `security-reviewer` to check for vulnerabilities.

---

## Tips

- You **don't need to name the agent**. Just describe what you want.
  Claude picks the right one automatically.
- For big tasks, Claude often uses **multiple agents in parallel**
  (e.g., security review + code review at the same time).
- If you want a specific agent: `"Use the architect agent to design this"`
