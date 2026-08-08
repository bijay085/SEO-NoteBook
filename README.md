# SEO Helper

## What It Is

SEO Helper is a practical SEO decision system built by Bijay. It is a structured knowledgebase, a set of audit skills, and an optional MCP router — all in one repo.

It is not an SEO tool that crawls, buys data, or connects to APIs by default. It works from what you already have: GSC exports, GA4 exports, crawl files, screenshots, pasted notes, and live pages.

## What It Is For

Use SEO Helper when you have an SEO problem and need a clear next action — not a generic checklist.

It covers:

- Traffic drops and ranking loss diagnosis
- GSC indexed-but-no-impressions issues
- Topical map and content gap planning
- Keyword cannibalization detection
- Rendering and JavaScript SEO issues
- Log file analysis and crawl budget
- E-E-A-T and authorship signals
- Off-page and backlink audit
- CRO and conversion page review
- Local SEO and GBP decisions
- Ecom decline investigation
- Sandbox effect analysis
- Affiliate and review site audits
- Accessibility and completeness audit

It is not for: live rank tracking, bulk keyword research, automated site crawling, or replacing a full SEO platform.

## How to Set Up

### Windows — one command, no clone needed

```powershell
irm https://raw.githubusercontent.com/bijay085/SEO-NoteBook/main/install.ps1 | iex
```

Clones to `%LOCALAPPDATA%\seo-helper`, installs skills, commands, and MCP tools for Claude, Codex, and Cursor. Run the same command again to update.

### Mac / Linux

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook
bash install-skills.sh
```

### Claude Code marketplace

In Claude Code → Plugins → Add → enter:

```
bijay085/SEO-NoteBook
```

### Codex marketplace

In Codex → Plugins → Add plugin marketplace:

| Field | Value |
|---|---|
| Source | `bijay085/SEO-NoteBook` |
| Git ref | `main` |
| Sparse paths | `.codex-plugin` |

### Web chat or Custom GPT (no install needed)

Upload this file directly to your Claude project, ChatGPT project, or Custom GPT knowledge:

```
knowledge/SEO_Action_Decision_System.html
```

For Custom GPT, add this instruction:

```
You are SEO Helper. Use SEO_Action_Decision_System.html as the knowledgebase.
Answer the exact SEO question. Use only the relevant section.
Format: Mode / What / Why / How / Evidence / Priority.
Ask for missing data instead of guessing.
```

## What Gets Installed

| Location | What |
|---|---|
| `~/.claude/skills/seo-*/` | 17 audit skills for Claude |
| `~/.codex/skills/seo-*/` | Same skills for Codex |
| `~/.cursor/skills/seo-*/` | Same for Cursor |
| `~/.claude/commands/seo-helper/` | `/seo-helper:*` slash commands |
| Claude Desktop MCP | `seo-helper-router` with 4 tools |
| Codex MCP | Same MCP in `~/.codex/config.toml` |

## When to Use

| Situation | What to do |
|---|---|
| Traffic dropped | Use `seo-gsc-diagnosis` or ask the router |
| Page indexed but no impressions | Use GSC diagnosis skill |
| Planning content for a new site | Use `seo-topical-map` |
| Pages competing with each other | Use `seo-cannibalization-audit` |
| JavaScript-heavy site with ranking issues | Use `seo-render-audit` |
| Want a full technical picture | Use `seo-initial-analysis` |
| One-off question | Just paste the problem in chat |

## How to Use

**In Claude Code or Cursor:**

```
/seo-helper:<command>
```

Example: `/seo-helper:gsc-diagnosis`

**In Codex:**

Type `/seo-helper` to see all skills.

**In Claude Desktop or Codex chat:**

Paste your SEO problem. If the MCP is registered, the router handles it. Otherwise paste the problem and ask the relevant skill to analyse it.

**Anywhere (no install):**

Upload `knowledge/SEO_Action_Decision_System.html` and paste your problem.

## Updating

```powershell
irm https://raw.githubusercontent.com/bijay085/SEO-NoteBook/main/install.ps1 | iex
```

Same command — it pulls latest and re-syncs.

Or via `START_HERE.bat` → option 3.

---

## Disclaimer

> **This is an AI-assisted decision system, not a certified SEO audit tool.**
>
> SEO Helper provides structured decision logic based on practitioner knowledge, documented search engine behaviour, and evidence-based rules. It does not replace professional SEO judgement or a formal site audit.
>
> Always verify recommendations against your own GSC data, GA4 data, live pages, and search engine documentation before making changes. Rankings, indexing behaviour, and algorithm signals change over time — rules in this system reflect knowledge up to the point it was last updated.
>
> Use this as a starting point and thinking aid, not as the final word. Manual verification is always required before acting on any SEO recommendation.
