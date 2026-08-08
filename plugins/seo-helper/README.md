# SEO Helper Plugin

**One plugin** for Claude, Cursor, Codex/GPT, and chat UIs:

1. **`seo-decision-helper`** — SEO helper / “what should I do next?” coach  
2. **Decision notebook** — `assets/SEO_Action_Decision_System.html`  
3. **15 audit skills** — `skills/seo-*` (GSC, CRO, render, topical map, …)  
4. **Optional MCP** — `mcp/decision_server.py` (section lookup + situation router)

Author credit on reports: **Prepared by Bijay** (text **SEO** mark, no logo).

## What It Helps With

SEO Helper gives an AI agent a reusable SEO operating system instead of one-off generic advice.

Use it for:

- **Choosing the next SEO action:** traffic drops, weak rankings, new site planning, local/GBP, money pages, content refreshes, technical gates, and reporting.
- **Turning pasted sources into rules:** summarize noisy Reddit posts, article notes, docs, and observations into compact decision rules, tables, or checklists.
- **Analyzing files:** work from GSC exports, crawls, server logs, HTML, page lists, keyword files, and audit evidence.
- **Routing audits:** select the correct included audit workflow when the issue needs deeper proof.
- **Reducing token waste:** start small, load only the relevant notebook section or audit skill, and avoid repeating the full SEO knowledge base in every chat.
- **Keeping output useful:** answer with What / Why / How / Evidence / Priority, then recommend the next measurable step.

## How It Works

The installed plugin has one entry point: `seo-decision-helper`. The agent uses it to understand the situation, consults `assets/SEO_Action_Decision_System.html` for decision rules, and then loads a specific `seo-*` audit skill only if the task needs deeper analysis. If the MCP server is connected, it can list sections, fetch a notebook section, and route a short SEO situation to the most relevant audit skills.

## Layout (this is the plugin root)

```
plugins/seo-helper/           <- install THIS folder as the plugin
  .claude-plugin/plugin.json   ← Claude Code plugin
  .codex-plugin/plugin.json    ← Codex / GPT plugin
  .mcp.json                    ← MCP for Claude plugin load
  assets/SEO_Action_Decision_System.html
  mcp/decision_server.py
  skills/
    seo-decision-helper/      ← start here for teaching / decisions
    seo-gsc-diagnosis/
    ...
```

Why not one flat file? Agents load **skills by folder**. The decision helper skill is the
single entry point; audits stay separate so the model only pulls what it needs.

## Install

### Claude Code (plugin)

From a Claude session (path adjusted to your machine):

```text
/plugin install D:\SEO NoteBook\plugins\seo-helper
```

Or add as a local marketplace/plugin directory per Claude Code docs, then enable **seo-helper**.

### Cursor / Codex (skills + MCP)

```powershell
cd "D:\SEO NoteBook\plugins\seo-helper"
.\install-skills.ps1
pip install -r requirements.txt
pip install -r mcp\requirements.txt
```

Add MCP from `mcp-hosts.example.json` (set `ROOT` to this folder) into Cursor / Codex MCP settings.

### ChatGPT / Grok / Claude Projects (chat UI)

Upload at least:

- `skills/seo-decision-helper/SKILL.md`
- `assets/SEO_Action_Decision_System.html`
- (optional) any `seo-*` audit you need

Instruction line:

> You are my SEO helper. Follow `seo-decision-helper/SKILL.md`. Use the decision HTML for rules. Answer with What / Why / How / Evidence / Priority. Only run a deep audit skill when measurement is required.

Full detail: [INSTALL.md](INSTALL.md) · runtime rules: [AGENT_RUNTIME.md](AGENT_RUNTIME.md)

## Smoke tests

```powershell
python mcp\decision_server.py --self-test
```

In any agent:

> Load seo-decision-helper. Traffic dropped on my Shopify store — what should I do first?

## Optional DataForSEO

See `mcp-servers.json` / `mcp-hosts.example.json`. Env names only — no secrets in the pack.

