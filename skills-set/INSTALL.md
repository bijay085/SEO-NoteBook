# Install on any AI agent

This pack uses the open [Agent Skills](https://agentskills.io) format. One
`skills/seo-*/` folder works everywhere that reads `SKILL.md`.

## 1. Python (once, for scripted skills)

```bash
pip install -r requirements.txt
```

## 2. Coding agents (native skills folders)

Copy **every** folder under `skills/` into the host’s skills directory:

| Agent | Personal (all projects) | Project-only |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` |
| **Cursor** | `~/.cursor/skills/` | `.cursor/skills/` |
| **OpenAI Codex CLI** | `~/.codex/skills/` | `.agents/skills/` or project skills dir |
| **GitHub Copilot** (VS Code) | agent skills dir per Copilot docs | `.github/skills/` when supported |
| **Gemini CLI / OpenCode / Cline / Windsurf** | that product’s skills folder | project skills folder if offered |

### Windows (PowerShell) — install to Claude + Cursor + Codex

From this `skills-set` folder:

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
./install-skills.sh          # claude + cursor + codex
./install-skills.sh cursor   # one host
```

## 3. Chat UIs without a skills folder

Use the same files as project knowledge:

| Product | How |
|---|---|
| **ChatGPT** (GPT / Projects) | Upload the skill folder (or zip) into Project files; in instructions say: “When I name an SEO audit, open that skill’s SKILL.md and follow it.” |
| **Claude** (claude.ai Projects) | Add the skill folders to Project knowledge; same instruction line. |
| **Grok** | Attach / upload `SKILL.md` + needed `references/` and `scripts/` into the project or custom instructions. |

Tip: for chat UIs, start with **one** skill (e.g. `seo-gsc-diagnosis`) so context stays small. Point the agent at `AGENT_RUNTIME.md` for tools/exports.

## 4. Optional MCP connectors

`mcp-servers.json` declares **DataForSEO** (env names only). Add the same block to
your host’s MCP config if you use live SERP/keyword/backlink pulls. GSC, Clarity,
and browser tools are host connectors — authorize them in that product, or pass
CSV/HTML exports instead (see `AGENT_RUNTIME.md`).

## 5. Smoke test

In any agent:

> Load `seo-gsc-diagnosis` and summarize when to use it vs `seo-ecom-decline-investigation`.

If it reads the skill and answers from the methodology, install worked.
