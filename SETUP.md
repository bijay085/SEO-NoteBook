# SEO Helper Plugin Setup

This repo contains Bijay's SEO Helper plugin: SEO router, knowledgebase, audit modules, and an optional local MCP router server.

## 1. Clone or Update the Repo

First get the repo onto your machine:

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
```

If you already have it:

```bash
cd SEO-NoteBook
git pull
```

The main plugin folder is:

```text
plugins/seo-helper
```


## 2. Install in Claude Code

Open Claude Code and run:

```text
/plugin install <path-to>/SEO-NoteBook/plugins/seo-helper
```

Example on Windows:

```text
/plugin install D:\SEO NoteBook\plugins\seo-helper
```

After updating the repo with `git pull`, restart or open a new Claude Code session so the latest plugin files are loaded.

## 3. Install in Codex / GPT Plugin Flow

The Codex plugin manifest is here:

```text
plugins/seo-helper/.codex-plugin/plugin.json
```

The repo-local marketplace file is here:

```text
.agents/plugins/marketplace.json
```

In Codex, use the plugin view/share flow for `seo-helper`, or install from the marketplace entry that points to:

```text
./plugins/seo-helper
```

When the plugin changes, update from Git and reinstall/refresh the plugin if your Codex app does not pick up local changes automatically.

## 4. Install Skills Only

If an AI tool supports Agent Skills but not plugins, copy every folder under:

```text
plugins/seo-helper/skills
```

into that tool's skills folder. For seo-router, also provide plugins/seo-helper/knowledge/SEO_Action_Decision_System.html, because the knowledgebase is intentionally not duplicated inside the skill folder.

Common personal skill folders:

| Tool | Skills Folder |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Cursor | `~/.cursor/skills/` |

On Windows, from the plugin folder you can run:

```powershell
cd "D:\SEO NoteBook\plugins\seo-helper"
.\install-skills.ps1
```

## 5. Optional MCP Setup

The local MCP server is:

```text
plugins/seo-helper/server/seo_router_server.py
```

Install Python requirements:

```bash
cd plugins/seo-helper
pip install -r requirements.txt
pip install -r server/requirements.txt
```

Then add the MCP config from:

```text
plugins/seo-helper/mcp-hosts.example.json
```

Set the root/path value to your local `plugins/seo-helper` folder.

Smoke test:

```bash
python server/seo_router_server.py --self-test
```

## 6. What to Ask After Install

Try:

```text
Load seo-router. Traffic dropped on my Shopify store. What should I do first?
```

Or:

```text
Use SEO Helper to clean this pasted SEO source and add only the useful decision rules.
```

## 7. Updating

To get future improvements:

```bash
cd SEO-NoteBook
git pull
```

Then start a new chat/session or refresh the plugin. For local plugin hosts, a new session is the safest way to make sure updated skills and MCP tools are loaded.


