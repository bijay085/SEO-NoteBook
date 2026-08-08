# SEO Helper: Agent Instructions

## Project Context

This is an SEO decision system. When the user pastes SEO information, Reddit discussions, article notes, GSC observations, or other source material and asks to edit/add/update:

- The only SEO decision file is `knowledge/SEO_Action_Decision_System.html`. Do not create copies anywhere else.
- Place updates in the most relevant existing section. Do not create duplicate sections.
- Treat pasted sources as practitioner input unless they are official documentation. Convert to concise operational rules, checklists, tables, or decision logic.
- Keep additions compact: summarize the useful idea, remove noise, avoid long quotes.
- If a pasted source repeats an existing rule, merge or strengthen it instead of adding another version.
- When sources conflict: prefer official search engine docs, then first-party data (GSC/GA4/crawl), then practitioner examples.
- Do not browse the web unless the user asks for current verification.
- After editing, verify the inserted heading exists and do a light HTML structure check.

## Runtime Rules

Use the smallest useful context:

1. Start with `skills/seo-router/SKILL.md`.
2. Route the question to one notebook section.
3. Read only that section from `knowledge/SEO_Action_Decision_System.html`.
4. Load one deeper `seo-*` audit skill only when the task needs measurement, exports, crawling, logs, or a full deliverable.

Do not read the whole knowledgebase for a narrow question.
Do not run every audit skill for one issue.

## Answer Format

1. Mode
2. What
3. Why
4. How
5. Evidence
6. Priority
7. Next skill (only if needed)

For simple definitions, answer simply. If evidence is missing, say what is missing. Do not invent numbers.

## Canonical Files

| File | Purpose |
|---|---|
| `knowledge/SEO_Action_Decision_System.html` | Only editable SEO knowledgebase |
| `skills/seo-router/SKILL.md` | Main entry skill |
| `skills/seo-router/references/section-index.md` | Compact section index |
| `server/seo_router_server.py` | MCP section lookup and situation router |
| `scripts/maintain.py` | Validate, rebuild index, add rules |

## Source Handling

When the user pastes noisy sources:

1. Identify the SEO problem type.
2. Extract durable rules only.
3. Ignore spam, insults, one-off claims, and unsupported shortcuts.
4. Prefer if/then rules over generic tips.
5. Do not store raw Reddit dumps in the knowledgebase.

## Update Workflow

1. Edit `knowledge/SEO_Action_Decision_System.html`.
2. Run `python scripts/maintain.py rebuild-index`.
3. Run `python scripts/maintain.py validate`.
4. Commit and push.

## Writing Rules

- Avoid em dashes and en dashes in user-facing analysis. Use commas, periods, or colons instead.
- Reports credit `Prepared by Bijay`. No logo required.

