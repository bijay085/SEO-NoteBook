# SEO NoteBook — Teacher Plugin + Decision System

SEO decision notebook + portable **seo-teacher** plugin (skills + optional MCP) by **Bijay**.

| Path | What it is |
|---|---|
| [`SEO_Action_Decision_System.html`](./SEO_Action_Decision_System.html) | Full SEO action / decision rules (open in browser) |
| [`plugins/seo-teacher/`](./plugins/seo-teacher/) | **Plugin root** — install this folder in Claude / Codex; includes skills + optional MCP |
| [`AGENTS.md`](./AGENTS.md) | Notes for agents working in this repo |

## Share / install links

**Repo:** https://github.com/bijay085/SEO-NoteBook  

**Plugin folder:** https://github.com/bijay085/SEO-NoteBook/tree/main/plugins/seo-teacher  

### Claude Code

Clone, then install the plugin folder:

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
# In Claude Code:
# /plugin install <path-to>/SEO-NoteBook/plugins/seo-teacher
```

### Cursor / Codex (skills)

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook/plugins/seo-teacher
# Windows:
.\install-skills.ps1
# macOS/Linux:
./install-skills.sh
pip install -r requirements.txt
pip install -r mcp/requirements.txt
```

Local MCP config: copy [`plugins/seo-teacher/mcp-hosts.example.json`](./plugins/seo-teacher/mcp-hosts.example.json) into your host MCP settings and set `ROOT` to the `plugins/seo-teacher` path.

### ChatGPT / Grok / Claude Projects

Upload:

- `plugins/seo-teacher/skills/seo-decision-teacher/` (includes the decision HTML)
- optionally other `plugins/seo-teacher/skills/seo-*` audits you need

Prompt:

> Follow `seo-decision-teacher/SKILL.md`. Use the decision HTML for rules. Answer with What / Why / How / Evidence / Priority.

## Entry skill

Ask any agent:

> Load **seo-decision-teacher**. Traffic dropped on my Shopify store — what should I do first?

Setup guide: [SETUP.md](./SETUP.md)

Full install notes: [`plugins/seo-teacher/INSTALL.md`](./plugins/seo-teacher/INSTALL.md) · runtime: [`plugins/seo-teacher/AGENT_RUNTIME.md`](./plugins/seo-teacher/AGENT_RUNTIME.md)

## Note on MCP “link”

The bundled MCP (`plugins/seo-teacher/mcp/decision_server.py`) is **local** (runs on the user’s machine after clone). A public one-click MCP URL needs a separate hosted deploy — see `plugins/seo-teacher/README.md`.




