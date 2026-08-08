# SEO Teacher Plugin

**One plugin** for Claude, Cursor, Codex/GPT, and chat UIs:

1. **`seo-decision-teacher`** — SEO teacher / “what should I do next?” coach  
2. **Decision notebook** — `assets/SEO_Action_Decision_System.html`  
3. **15 audit skills** — `skills/seo-*` (GSC, CRO, render, topical map, …)  
4. **Optional MCP** — `mcp/decision_server.py` (section lookup + situation router)

Author credit on reports: **Prepared by Bijay** (text **SEO** mark, no logo).

## Layout (this is the plugin root)

```
skills-set/                    ← install THIS folder as the plugin
  .claude-plugin/plugin.json   ← Claude Code plugin
  .codex-plugin/plugin.json    ← Codex / GPT plugin
  .mcp.json                    ← MCP for Claude plugin load
  assets/SEO_Action_Decision_System.html
  mcp/decision_server.py
  skills/
    seo-decision-teacher/      ← start here for teaching / decisions
    seo-gsc-diagnosis/
    ...
```

Why not one flat file? Agents load **skills by folder**. The teacher skill is the
single entry point; audits stay separate so the model only pulls what it needs.

## Install

### Claude Code (plugin)

From a Claude session (path adjusted to your machine):

```text
/plugin install D:\SEO NoteBook\skills-set
```

Or add as a local marketplace/plugin directory per Claude Code docs, then enable **seo-teacher**.

### Cursor / Codex (skills + MCP)

```powershell
cd "D:\SEO NoteBook\skills-set"
.\install-skills.ps1
pip install -r requirements.txt
pip install -r mcp\requirements.txt
```

Add MCP from `mcp-hosts.example.json` (set `ROOT` to this folder) into Cursor / Codex MCP settings.

### ChatGPT / Grok / Claude Projects (chat UI)

Upload at least:

- `skills/seo-decision-teacher/SKILL.md`
- `assets/SEO_Action_Decision_System.html`
- (optional) any `seo-*` audit you need

Instruction line:

> You are my SEO teacher. Follow `seo-decision-teacher/SKILL.md`. Use the decision HTML for rules. Answer with What / Why / How / Evidence / Priority. Only run a deep audit skill when measurement is required.

Full detail: [INSTALL.md](INSTALL.md) · runtime rules: [AGENT_RUNTIME.md](AGENT_RUNTIME.md)

## Smoke tests

```powershell
python mcp\decision_server.py --self-test
```

In any agent:

> Load seo-decision-teacher. Traffic dropped on my Shopify store — what should I do first?

## Optional DataForSEO

See `mcp-servers.json` / `mcp-hosts.example.json`. Env names only — no secrets in the pack.
