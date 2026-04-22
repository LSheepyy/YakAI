# 03 — Skills: Slash Commands

Skills are pre-written playbooks that tell Claude exactly how to approach
a specific type of task. You invoke them with a `/` prefix.

Think of them as shortcuts that give Claude expert-level instructions
for common jobs so you don't have to explain the process every time.

---

## How to Use a Skill

Just type the slash command in the chat:

```
/tdd
/plan build a user authentication system
/code-review
/docs
```

Some skills work on their own. Others work better if you describe the task
after the command.

---

## The Most Useful Skills

### Development Workflow

| Command | What It Does | Example |
|---------|-------------|---------|
| `/plan` | Creates a full implementation plan before coding | `/plan add OAuth login` |
| `/feature-dev` | Guides you through building a feature end-to-end | `/feature-dev user profile page` |
| `/tdd` | Test-driven development: write tests first | `/tdd add the cart checkout flow` |
| `/build-fix` | Diagnoses and fixes build/compile errors | `/build-fix` (then paste the error) |
| `/code-review` | Reviews recent code changes | `/code-review` |
| `/verify` | Checks if everything is working correctly | `/verify` |

### Code Quality

| Command | What It Does |
|---------|-------------|
| `/refactor-clean` | Removes dead code, cleans up duplication |
| `/prune` | Strips out unused imports, variables, exports |
| `/simplify` | Rewrites code to be simpler and cleaner |
| `/quality-gate` | Full quality check: tests, types, linting |

### Testing

| Command | What It Does |
|---------|-------------|
| `/tdd` | Write tests first, then implementation |
| `/test-coverage` | Check and improve test coverage |
| `/e2e` | Write end-to-end tests for user flows |

### Documentation

| Command | What It Does | Example |
|---------|-------------|---------|
| `/docs` | Look up how to use any library or API | `/docs how do I debounce in lodash?` |
| `/update-docs` | Sync your README and docs with the code | `/update-docs` |

### Git & PRs

| Command | What It Does |
|---------|-------------|
| `/prp-plan` | Plan a pull request before writing code |
| `/prp-implement` | Implement a planned PR |
| `/prp-commit` | Create a well-formatted commit |
| `/prp-pr` | Draft the PR description |
| `/review-pr` | Review an open pull request |
| `/checkpoint` | Save a checkpoint of your current progress |

### Memory

| Command | What It Does |
|---------|-------------|
| `/mem-search` | Search everything claude-mem has recorded |
| `/save-session` | Manually save the current session summary |
| `/resume-session` | Load context from a previous session |
| `/sessions` | List past sessions |

### Project Setup

| Command | What It Does |
|---------|-------------|
| `/init` | Initialise Claude for a new project |
| `/projects` | Manage multiple projects |
| `/learn` | Teach Claude about a codebase or concept |

### Design & Frontend

| Command | What It Does | Example |
|---------|-------------|---------|
| `/design` | Get UI/UX design direction | `/design a settings page` |
| `/ui-styling` | Improve visual styling | `/ui-styling make this look modern` |
| `/frontend-design` | Full frontend design guidance | |

### Language-Specific

| Command | Language |
|---------|---------|
| `/python-review` | Python |
| `/go-review` | Go |
| `/go-test` | Go testing |
| `/rust-review` | Rust |
| `/rust-test` | Rust testing |
| `/kotlin-review` | Kotlin |
| `/flutter-review` | Flutter |
| `/cpp-review` | C++ |

### Fun / Utility

| Command | What It Does |
|---------|-------------|
| `/council` | Gets multiple AI perspectives on a problem |
| `/orchestrate` | Runs a complex multi-step workflow |
| `/prompt-optimize` | Improves a prompt you've written |
| `/skill-create` | Creates a new skill from scratch |
| `/hookify` | Sets up automatic hooks for your workflow |

---

## Pattern: Plan → Build → Review

The best workflow for a new feature:

```
Step 1:  /plan add a notification system
         (Claude thinks through the approach first)

Step 2:  /tdd
         (Build it with tests)

Step 3:  /code-review
         (Catch any issues)

Step 4:  /prp-commit
         (Clean commit message)
```

---

## Tips

- Skills work best with **context**. The more Claude knows about your project,
  the better the output.
- You can combine them: `"Use TDD to build the feature from the plan you just made"`
- Not sure which skill to use? Just describe what you want in plain English —
  Claude often picks the right skill automatically.
- Use `/docs [topic]` whenever you're unsure about a library or API.
  It fetches live documentation so the answer is always up to date.
