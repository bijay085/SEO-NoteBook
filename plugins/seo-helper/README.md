# SEO Helper Plugin

One clean plugin for Claude, Cursor, Codex/GPT, and chat UIs.

Install this folder:

```text
plugins/seo-helper
```

Author credit on reports: `Prepared by Bijay`.

## What It Does

SEO Helper helps an AI agent give exact SEO decisions instead of generic advice.

It helps with:

- choosing the next SEO action for ranking drops, indexed pages with no impressions, local SEO, money pages, AI visibility, reporting, and new sites
- turning pasted SEO sources into compact decision rules
- analyzing files such as GSC exports, crawls, logs, HTML, and keyword files
- routing deeper work to the right included audit skill
- saving tokens by loading only the router, one notebook section, or one audit skill when needed

## How It Works

The plugin starts from one skill: `seo-router`.

The router finds the right section in the canonical knowledgebase, answers the exact question, and only loads a deeper audit skill when evidence is needed.

Canonical knowledgebase:

```text
knowledge/SEO_Action_Decision_System.html
```

That is the only decision HTML. Do not create copies in the repo root or inside skill folders.

## Layout

```text
plugins/seo-helper/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  .mcp.json
  AGENT_RUNTIME.md
  INSTALL.md
  README.md
  knowledge/
    SEO_Action_Decision_System.html
  scripts/
    maintain.py
  server/
    seo_router_server.py
  skills/
    seo-router/
    seo-gsc-diagnosis/
    seo-render-audit/
    seo-topical-map/
    ...
```

## Install

### Claude Code

```text
/plugin install D:\SEO NoteBook\plugins\seo-helper
```

For a cloned repo on another machine, use that machine's path to `plugins/seo-helper`.

### Cursor / Codex Skills

From this folder:

```powershell
.\install-skills.ps1
pip install -r requirements.txt
pip install -r server\requirements.txt
python scripts\maintain.py validate
```

### ChatGPT / Claude / Grok Project Knowledge

For a basic chat UI setup, upload only:

```text
skills/seo-router/SKILL.md
knowledge/SEO_Action_Decision_System.html
```

Instruction:

```text
You are SEO Helper. Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html as the main knowledgebase. Answer the exact SEO question with What, Why, How, Evidence, and Priority. Load deeper audit material only when needed.
```

## Updating Knowledge

Edit one file:

```text
knowledge/SEO_Action_Decision_System.html
```

Then run:

```powershell
python scripts\maintain.py rebuild-index
python scripts\maintain.py validate
git add knowledge\SEO_Action_Decision_System.html skills\seo-router\references\section-index.md
git commit -m "Update SEO helper knowledgebase"
git push
```

Existing users update with:

```powershell
git pull
python scripts\maintain.py validate
```

They do not need to reinstall if their AI app points to this repo folder. Reinstall is only needed if their app copied the plugin files during install.

## Useful Commands

Validate everything:

```powershell
python scripts\maintain.py validate
```

Rebuild section index:

```powershell
python scripts\maintain.py rebuild-index
```

Add a tiny simple rule before an existing heading:

```powershell
python scripts\maintain.py add-rule --title "Example Rule" --body "Use this when..." --decision "Do X before Y." --before "Underrated SEO Action Rule"
```

MCP smoke test:

```powershell
python server\seo_router_server.py --self-test
```

## Optional MCP

The MCP server is local and optional. It exposes:

- `list_decision_sections`
- `get_decision_section`
- `route_seo_situation`
- `list_seo_audit_skills`

Use `mcp-hosts.example.json` as the copy/paste template for hosts that support MCP.
