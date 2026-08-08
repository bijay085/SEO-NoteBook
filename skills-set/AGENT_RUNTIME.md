# Agent runtime (portable)

These skills follow the open **Agent Skills** format (`SKILL.md` + optional `scripts/`,
`references/`). Same folders work in Claude Code, Cursor, Codex/GPT CLI, Gemini CLI,
Copilot, and similar agents. Chat UIs (ChatGPT Projects, Grok, Claude Projects) use the
same files as **uploaded knowledge** — see [INSTALL.md](INSTALL.md).

## Skill root

Never hardcode `~/.claude/skills/...`. Resolve paths in this order:

1. The folder that contains this skill’s `SKILL.md` (preferred).
2. A sibling folder under the same `skills/` pack (`../seo-<name>/`).
3. Any host install path listed in [INSTALL.md](INSTALL.md).

In shell examples, treat `$SKILL_DIR` as that folder.

## Capabilities (use whatever the host provides)

Skills need **capabilities**, not a specific vendor tool name. Prefer the first
available option in each row.

| Need | Prefer | Fallback |
|---|---|---|
| Fetch a live page / DOM | Agent browser / Playwright / Cursor browser | `WebFetch`, curl, or saved HTML |
| Read local files | Host filesystem tools | User paste / upload |
| Write reports | Host filesystem tools | Return HTML/XLSX in chat for download |
| Google Search Console | GSC MCP / connector | Official GSC CSV/XLSX exports |
| Keyword / SERP / backlinks | DataForSEO MCP (see `mcp-servers.json`) | Ahrefs/Semrush CSV, or skip that layer |
| Clarity behavior | Clarity MCP / connector | Clarity CSV export |
| Secrets | Host env vars / project `.env` | Ask the user (never bake secrets into skills) |
| Parallel audits | Host parallel agents / Task / subagents | Run audits **sequentially**, then merge |

Claude-style names like `mcp__dataforseo__*` or `mcp__google-search-console__*` are
**examples** of MCP tool ids — if your host names them differently, call the equivalent.

## Cache & temp

Prefer `<workspace>/.cache/<skill-name>/`. If the host blocks that, use the OS temp dir.
Do not require `~/.claude/cache/`.

## Branding

Reports use a text **SEO** mark and **Prepared by Bijay**. No logo required.
Config `brand.agency` defaults to `Bijay`.

## Honesty rule

If a connector or export is missing, **degrade** that dimension and say so in the
report. Never invent GSC rows, backlinks, or Clarity sessions.
