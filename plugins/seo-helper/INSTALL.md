# Install on any AI agent

This folder is the **seo-helper plugin** root. In this repo the canonical path is `plugins/seo-helper` (Claude + Codex manifests, skills,
knowledgebase, optional MCP server). Skills use the open [Agent Skills](https://agentskills.io)
format.

## 0. Claude Code : install as a plugin (recommended)

```text
/plugin install D:\SEO NoteBook\plugins\seo-helper
```

That loads `.claude-plugin/plugin.json`, all `skills/`, and `.mcp.json` (`seo-helper-router`).

Codex/GPT: use `.codex-plugin/plugin.json` with your Codex plugin/marketplace flow,
or copy skills via `install-skills.ps1` below.

## 1. Python (once, for scripted skills + MCP)

```bash
pip install -r requirements.txt
pip install -r server/requirements.txt
```

## 2. Coding agents (native skills folders)

Copy **every** folder under `skills/` into the host skills directory. Also keep this plugin folder available if you want `seo-router` to read the shared `knowledge/SEO_Action_Decision_System.html` file. Full plugin install is cleaner than skills-only install:

| Agent | Personal (all projects) | Project-only |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` |
| **Cursor** | `~/.cursor/skills/` | `.cursor/skills/` |
| **OpenAI Codex CLI** | `~/.codex/skills/` | `.agents/skills/` or project skills dir |
| **GitHub Copilot** (VS Code) | agent skills dir per Copilot docs | `.github/skills/` when supported |
| **Gemini CLI / OpenCode / Cline / Windsurf** | that product’s skills folder | project skills folder if offered |

### Windows (PowerShell) : install to Claude + Cursor + Codex

From this `plugins/seo-helper` folder:

```powershell
.\install-skills.ps1
```

Or pick targets:

```powershell
.\install-skills.ps1 -Targets cursor,claude,codex
```

### macOS / Linux

```bash
chmod +x install-skills.sh
./install-skills.sh # claude + cursor + codex
./install-skills.sh cursor # one host
```

## 3. Chat UIs without a skills folder

Use the same files as project knowledge:

| Product | How |
|---|---|
| **ChatGPT** (GPT / Projects) | Upload the skill folder (or zip) into Project files; in instructions say: “When I name an SEO audit, open that skill’s SKILL.md and follow it.” |
| **Claude** (claude.ai Projects) | Add the skill folders to Project knowledge; same instruction line. |
| **Grok** | Attach / upload `SKILL.md` + needed `references/` and `scripts/` into the project or custom instructions. |

Tip: for chat UIs, start with `seo-router/SKILL.md` plus `knowledge/SEO_Action_Decision_System.html`. Add one audit skill only when needed so context stays small. Point the agent at `AGENT_RUNTIME.md` for tools/exports.

## 4. Optional MCP connectors

`mcp-servers.json` declares **DataForSEO** (env names only). Add the same block to
your host’s MCP config if you use live SERP/keyword/backlink pulls. GSC, Clarity,
and browser tools are host connectors : authorize them in that product, or pass
CSV/HTML exports instead (see `AGENT_RUNTIME.md`).

## 5. Smoke test

In any agent:

> Load `seo-router`. Traffic dropped on my Shopify store. What should I check first?

If it reads the skill and answers from the methodology, install worked.


