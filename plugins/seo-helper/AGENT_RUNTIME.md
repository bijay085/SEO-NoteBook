# Agent Runtime Guide

SEO Helper is a portable plugin built around one canonical knowledgebase and one router skill.

## Runtime Rule

Use the smallest useful context.

1. Start with `skills/seo-router/SKILL.md`.
2. Route the question to one notebook section.
3. Read only that section from `knowledge/SEO_Action_Decision_System.html`.
4. Load one deeper `seo-*` audit skill only when the task needs measurement, exports, crawling, logs, or a full deliverable.

Do not read the whole knowledgebase for a narrow question.
Do not run every audit skill for one issue.
Do not copy the knowledgebase into another file.

## Canonical Files

| File | Purpose |
|---|---|
| `knowledge/SEO_Action_Decision_System.html` | Only editable SEO decision knowledgebase |
| `skills/seo-router/SKILL.md` | Main entry skill and answer format |
| `skills/seo-router/references/section-index.md` | Generated compact section index |
| `server/seo_router_server.py` | Optional MCP section lookup and situation router |
| `scripts/maintain.py` | Validate, rebuild index, and add simple rules |

## Update Workflow

When adding pasted sources or new SEO lessons:

1. Extract only reusable decision logic.
2. Add it to the most relevant section in `knowledge/SEO_Action_Decision_System.html`.
3. Keep it compact: trigger, decision, evidence, action, priority.
4. Rebuild the index:

```bash
python scripts/maintain.py rebuild-index
```

5. Validate the plugin:

```bash
python scripts/maintain.py validate
```

6. Commit and push.

Existing users should update with `git pull`. They do not need a fresh reinstall unless their AI host copied the plugin files instead of reading from the repo path.

## Source Handling

When the user pastes noisy sources, do this:

1. Identify the SEO problem type.
2. Extract durable rules only.
3. Ignore comments that are spam, insults, one-off claims, or unsupported shortcuts.
4. Prefer if/then rules over generic tips.
5. Cite source context only when the user asks or when attribution matters.
6. Do not store raw Reddit dumps in the knowledgebase.

## Answer Format

Default helper answers should include:

1. Mode
2. What
3. Why
4. How
5. Evidence
6. Priority
7. Next skill, only if needed

For simple definitions, answer simply.

## Evidence Rules

Official docs and first-party data beat opinion.
GSC, GA4, crawl exports, logs, live SERP checks, page HTML, and screenshots are evidence.
If evidence is missing, say what is missing. Do not invent numbers.

## Branding

Reports use text mark `SEO` and credit `Prepared by Bijay`.
No logo is required.

## Writing Rule

Avoid em dashes and en dashes in user-facing analysis. Use commas, periods, colons, or `to` for ranges. Hyphens are fine in file names, URLs, ids, and commands.
