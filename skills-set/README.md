# SEO Skills — Portable Export

Personal SEO audit skill pack (authored by Bijay). Uses the open
[Agent Skills](https://agentskills.io) format (`SKILL.md`) so the **same folders**
work in Claude, Cursor, Codex/GPT, Gemini CLI, Copilot, and chat UIs (ChatGPT /
Claude / Grok Projects) via upload.

Reports use a neutral **SEO** text mark and **Prepared by Bijay** credit — no company logo.

Start here:

- **[INSTALL.md](INSTALL.md)** — install paths for every major agent + chat UIs  
- **[AGENT_RUNTIME.md](AGENT_RUNTIME.md)** — portable tools, exports, cache, branding  
- `install-skills.ps1` / `install-skills.sh` — one-shot copy into Claude + Cursor + Codex

## What's inside

- `skills/` — 15 self-contained `seo-*` skills (`SKILL.md` + scripts/references/templates)
- `requirements.txt` — consolidated Python deps for skill scripts
- `mcp-servers.json` — DataForSEO MCP declaration (env **names** only, no secrets)

| Skill | Purpose |
|---|---|
| seo-accessibility-completeness-audit | Accessibility + completeness / topical-coverage audit |
| seo-affiliate-and-review-audit | Affiliate-link health + review-content/schema audit |
| seo-after-foundational-setup-audit | Deep per-page forensic SEO / technical / content audit |
| seo-cro-conversion-audit | CRO audit with Clarity behavioral corroboration |
| seo-ecom-decline-investigation | Ecommerce organic-decline investigation (GSC decomposition) |
| seo-eeat-authorship-audit | E-E-A-T + authorship audit (42-item checklist) |
| seo-initial-analysis | First-engagement SEO analysis deliverable set |
| seo-off-page-audit | Inbound backlink + outbound link audit |
| seo-parallel-audit | Run multiple seo-* audits and merge one deliverable |
| seo-render-audit | Raw HTML vs rendered DOM + robots/llms bot-access audit |
| seo-sandbox-effect-analysis | Indexed-but-not-graduating diagnosis |
| seo-gsc-diagnosis | Fact-first GSC-led ecommerce SEO diagnosis |
| seo-topical-map | Topical authority map + demand-gated page plan |
| seo-cannibalization-audit | Keyword cannibalization verdicts from GSC time series |
| seo-log-file-analysis | Server log forensic crawl / budget / indexability audit |

## Quick setup

```powershell
# Windows — install into Claude + Cursor + Codex personal skills dirs
.\install-skills.ps1
pip install -r requirements.txt
```

```bash
# macOS / Linux
./install-skills.sh
pip3 install -r requirements.txt
```

Then open [INSTALL.md](INSTALL.md) for ChatGPT / Grok project upload and optional MCP connectors.

## Honest limits

- **Native skills folders** (Claude Code, Cursor, Codex, etc.): best experience — agent auto-discovers `SKILL.md`.
- **Chat UIs**: upload the skill (or zip) into project knowledge and tell the agent to follow that `SKILL.md`.
- **Live data**: GSC / DataForSEO / Clarity / browser are optional. Missing connector → degrade that layer and say so; never invent metrics.
- Secrets stay in host env / project `.env`, never inside this pack.
