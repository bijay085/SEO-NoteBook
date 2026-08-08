# SEO Helper Plugin

**One plugin** for Claude, Cursor, Codex/GPT, and chat UIs:

1. **`seo-decision-helper`** — SEO helper / “what should I do next?” coach  
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
    seo-decision-helper/      ← start here for helping / decisions
    seo-gsc-diagnosis/
    ...
```

Why not one flat file? Agents load **skills by folder**. The teacher skill is the
single entry point; audits stay separate so the model only pulls what it needs.

## Install

**GitHub:** https://github.com/bijay085/SEO-NoteBook/tree/main/skills-set

### Claude Code (plugin)

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
```

Then in Claude Code:

```text
/plugin install <path-to>/SEO-NoteBook/skills-set
```

### Cursor / Codex (skills + MCP)

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook/skills-set
```

```powershell
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


