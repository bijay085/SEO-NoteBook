# SEO Helper Install Guide

This folder is the plugin root:

```text
plugins/seo-helper
```

## Fast Test After Clone

From repo root:

```powershell
cd plugins\seo-helper
python scripts\maintain.py validate
```

If validation passes, the plugin files are present and the MCP router can read the knowledgebase.

## Claude Code Plugin Install

In Claude Code:

```text
/plugin install C:\path\to\SEO-NoteBook\plugins\seo-helper
```

If you installed from a local repo path, future updates are simple:

```powershell
git pull
cd plugins\seo-helper
python scripts\maintain.py validate
```

Reinstall only if Claude copied the plugin instead of referencing the repo path.

## Codex / Cursor Skills Install

From `plugins/seo-helper`:

```powershell
.\install-skills.ps1
pip install -r requirements.txt
pip install -r server\requirements.txt
python scripts\maintain.py validate
```

## Chat UI Setup

Upload these two files first:

```text
skills/seo-router/SKILL.md
knowledge/SEO_Action_Decision_System.html
```

Then add this instruction:

```text
Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html for rules. Answer with What, Why, How, Evidence, and Priority. Keep answers compact and load deeper audit material only when needed.
```

Upload extra `seo-*` skill folders only when you want that specific deep audit available.

## MCP Setup

Use `mcp-hosts.example.json` as the template. Replace `ROOT` with the absolute path to this folder.

The local router command is:

```powershell
python server\seo_router_server.py
```

Smoke test:

```powershell
python server\seo_router_server.py --self-test
```

## Updating the Knowledgebase

1. Edit `knowledge/SEO_Action_Decision_System.html`.
2. Run `python scripts\maintain.py rebuild-index`.
3. Run `python scripts\maintain.py validate`.
4. Commit and push.

Do not create another `SEO_Action_Decision_System.html` anywhere else.
