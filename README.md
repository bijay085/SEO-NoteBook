# SEO NoteBook — SEO Helper Plugin + Decision System

SEO decision notebook + portable **seo-helper** plugin (skills + optional MCP) by **Bijay**.

## What This Plugin Does

SEO Helper is a single installable SEO decision assistant. It helps an AI agent decide what SEO action to take, which evidence to check, and which deeper audit workflow to use without making the user repeat the same context in every new chat.

It helps with:

- **SEO decisions:** decide what to do next for traffic drops, ranking problems, new websites, local SEO, money pages, topical maps, E-E-A-T, technical SEO, reporting, and content planning.
- **Pasted sources:** clean Reddit threads, article notes, Google/Search Console observations, and other pasted information into compact, useful SEO rules instead of dumping raw text.
- **File analysis:** guide the agent through GSC exports, crawl files, logs, HTML, reports, and audit evidence when a deeper diagnosis is needed.
- **Audit routing:** choose the right included SEO audit skill, such as GSC diagnosis, render audit, CRO audit, topical map, backlink audit, log-file analysis, or cannibalization audit.
- **Token optimization:** load only the entry helper, the needed notebook section, or the specific audit skill instead of loading every SEO rule at once.
- **Consistent answers:** push the agent to answer with practical structure: What / Why / How / Evidence / Priority.

## How It Works

Install **one plugin folder**: `plugins/seo-helper`. Inside it, the agent starts with `seo-decision-helper`, uses the decision notebook for rules, and only opens a deeper `seo-*` audit skill when the task needs measurement or file-based proof. The optional MCP server can route a situation to the right notebook section and suggested audit skill.

| Path | What it is |
|---|---|
| [`SEO_Action_Decision_System.html`](./SEO_Action_Decision_System.html) | Full SEO action / decision rules (open in browser) |
| [`plugins/seo-helper/`](./plugins/seo-helper/) | **Plugin root** — install this folder in Claude / Codex; includes skills + optional MCP |
| [`AGENTS.md`](./AGENTS.md) | Notes for agents working in this repo |

## Share / install links

**Repo:** https://github.com/bijay085/SEO-NoteBook  

**Plugin folder:** https://github.com/bijay085/SEO-NoteBook/tree/main/plugins/seo-helper  

### Claude Code

Clone, then install the plugin folder:

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
# In Claude Code:
# /plugin install <path-to>/SEO-NoteBook/plugins/seo-helper
```

### Cursor / Codex (skills)

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook/plugins/seo-helper
# Windows:
.\install-skills.ps1
# macOS/Linux:
./install-skills.sh
pip install -r requirements.txt
pip install -r mcp/requirements.txt
```

Local MCP config: copy [`plugins/seo-helper/mcp-hosts.example.json`](./plugins/seo-helper/mcp-hosts.example.json) into your host MCP settings and set `ROOT` to the `plugins/seo-helper` path.

### ChatGPT / Grok / Claude Projects

Upload:

- `plugins/seo-helper/skills/seo-decision-helper/` (includes the decision HTML)
- optionally other `plugins/seo-helper/skills/seo-*` audits you need

Prompt:

> Follow `seo-decision-helper/SKILL.md`. Use the decision HTML for rules. Answer with What / Why / How / Evidence / Priority.

## Entry skill

Ask any agent:

> Load **seo-decision-helper**. Traffic dropped on my Shopify store — what should I do first?

Setup guide: [SETUP.md](./SETUP.md)

Full install notes: [`plugins/seo-helper/INSTALL.md`](./plugins/seo-helper/INSTALL.md) · runtime: [`plugins/seo-helper/AGENT_RUNTIME.md`](./plugins/seo-helper/AGENT_RUNTIME.md)

## Note on MCP “link”

The bundled MCP (`plugins/seo-helper/mcp/decision_server.py`) is **local** (runs on the user’s machine after clone). A public one-click MCP URL needs a separate hosted deploy — see `plugins/seo-helper/README.md`.

