# SEO Helper

Practical SEO decision system by Bijay. Routes traffic drops, GSC issues, topical maps, and technical audits to the right action — no guessing.

## Install (Windows)

```powershell
irm https://raw.githubusercontent.com/bijay085/SEO-NoteBook/main/install.ps1 | iex
```

Clones to `%LOCALAPPDATA%\seo-helper`, installs skills, commands, and registers MCP tools. Re-run to update.

**Mac/Linux:** clone the repo and run `bash install-skills.sh`.

## What gets installed

| Location | What |
|---|---|
| `~/.claude/skills/seo-*/` | 17 SEO audit skills for Claude |
| `~/.codex/skills/seo-*/` | Same skills for Codex (ChatGPT desktop) |
| `~/.cursor/skills/seo-*/` | Same for Cursor |
| `~/.claude/commands/seo-helper/` | `/seo-helper:*` commands for Claude Code |
| Claude Desktop MCP | `seo-helper-router` MCP server (4 tools) |
| Codex MCP | Same MCP server registered in `~/.codex/config.toml` |

## Usage

In **Claude Code**: type `/seo-helper` to see all commands.

In **Codex**: type `/seo-helper` to see all skills.

In **Claude Desktop / Codex chat**: paste your SEO problem. The MCP tools route it automatically.

For **web chat or Custom GPT**: upload `knowledge/SEO_Action_Decision_System.html` directly to the project or conversation.

## Add from GitHub (Claude Code marketplace)

In Claude Code → Plugins → Add → enter:

```
bijay085/SEO-NoteBook
```

## Add from GitHub (Codex marketplace)

In Codex → Plugins → Add plugin marketplace:

- **Source:** `bijay085/SEO-NoteBook`
- **Git ref:** `main`
- **Sparse paths:** `.codex-plugin`

## Covers

Traffic drops · GSC diagnosis · indexed but no impressions · topical maps · cannibalization · rendering · log files · E-E-A-T · off-page · CRO · local SEO · sandbox effect · ecom decline · accessibility · affiliate/review audits

## Single source of truth

```
knowledge/SEO_Action_Decision_System.html
```

Do not create duplicate copies of this file.
