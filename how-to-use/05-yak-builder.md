# 05 — YakAI Skill Builder

The Skill Builder is a custom tool you built in this project.
It lets you teach Claude new knowledge by giving it a file.

---

## What It Does

1. You pick any file (PDF, Word doc, text file, code file, etc.)
2. It reads and parses the content
3. It sends the content to Claude API
4. Claude turns it into a **skill** — a reusable knowledge file
5. The skill gets saved to `~/.claude/agents/`
6. From that point on, Claude uses that knowledge automatically

---

## How to Run It

```bash
python yak_skill_builder.py
```

A window opens with three steps.

---

## Step-by-Step

### Step 1: Enter Your API Key

Paste your Anthropic API key (`sk-ant-...`) into the first field.

If you set the `ANTHROPIC_API_KEY` environment variable, it fills in
automatically every time.

To set it permanently on Windows:
```
System Properties → Environment Variables → New
Name: ANTHROPIC_API_KEY
Value: sk-ant-your-key-here
```

### Step 2: Pick a File

Click **Browse…** and select any file. Supported formats:
- `.txt` `.md` — plain text or markdown
- `.pdf` — PDF documents
- `.docx` — Word documents
- `.py` `.js` `.ts` `.json` `.yaml` `.csv` — code and data files
- Most other text-based formats

The skill name auto-fills from the filename. You can change it.

The **Save To** path defaults to `~/.claude/agents/` — the right place.
Don't change this unless you have a reason.

### Step 3: Generate and Save

Click **⚡ Generate Skill**. Claude reads the file and writes the skill.

The result appears in the preview box. **You can edit it** before saving.

When happy, click **💾 Save Skill**.

---

## Real Examples of What to Feed It

### API or service documentation
Drop in a company's API spec or usage guide. Claude will know exactly
how to use that API in future sessions without you explaining it.

### Your coding standards doc
If your team has a style guide or architecture decisions document,
feed it in. Claude will follow your exact standards going forward.

### A tutorial or course notes
Paste in notes from a course you took. Claude can use that knowledge
when helping you apply what you learned.

### A README from a library you use
If you work with a specific library, feed it the README. Claude learns
the exact APIs and patterns for that library.

### Your own project documentation
Feed it architecture docs, decision logs, or design specs for your project.

---

## What a Generated Skill Looks Like

```markdown
---
name: stripe-webhooks
description: Handles Stripe webhook integration patterns. Use when
             working with payment events, webhook verification, or
             Stripe event processing.
---

## Overview
Stripe webhooks deliver real-time event notifications...

## Verification
Always verify the webhook signature using the signing secret...

## Common Events
- payment_intent.succeeded
- customer.subscription.updated
...
```

This file gets saved to `~/.claude/agents/stripe-webhooks.md`.
Claude reads it automatically in future sessions when relevant.

---

## Tips

- The skill is editable in the preview before saving — clean it up if
  Claude added anything irrelevant.
- Use a descriptive skill name so you can find it later.
- You can regenerate a skill from an updated document by running the
  tool again and saving over the existing file.
- View all your saved skills at `~/.claude/agents/`
