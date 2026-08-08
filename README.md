# SEO NoteBook: SEO Helper Plugin + Decision System

SEO Helper is one clean SEO decision plugin by Bijay.

It helps AI tools answer SEO questions with practical decision logic instead of generic advice.

## Start Here

Full setup guide:

```text
SETUP.md
```

GitHub users should start there. It has exact steps for:

- ChatGPT Custom GPT
- ChatGPT Projects
- Claude Code
- Claude Projects
- Codex
- Cursor
- other AI tools with file uploads
- optional MCP setup
- future updates with `git pull`

## Download

```powershell
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook
START_HERE.bat
```

On Windows, double-click `START_HERE.bat` after cloning. It validates the plugin and shows the exact plugin path.

## What This Plugin Does

SEO Helper is a single installable SEO decision assistant. It helps an AI agent decide what SEO action to take, what evidence to check, and which deeper audit workflow to use.

It helps with:

- SEO decisions for traffic drops, ranking problems, new sites, local SEO, money pages, topical maps, E-E-A-T, technical SEO, AI visibility, and reporting
- pasted source cleanup, turning Reddit threads, article notes, and observations into compact reusable rules
- file analysis guidance for GSC exports, crawl files, logs, HTML, reports, and audit evidence
- audit routing to the right included SEO skill
- token optimization by loading only the relevant rule, notebook section, or audit skill
- consistent answers using What, Why, How, Evidence, and Priority

## One Plugin Folder

Install only this folder when your AI tool supports plugins:

```text
plugins/seo-helper
```

The canonical knowledgebase is:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Do not use copied duplicate HTML files. This is the only decision knowledgebase.

## Basic ChatGPT Custom GPT Setup

For a normal custom GPT, upload only this file as Knowledge:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Use the full instructions in `SETUP.md`.

## How It Works

The AI starts with:

```text
plugins/seo-helper/skills/seo-router/SKILL.md
```

Then it reads only the relevant section from the knowledgebase. It loads deeper `seo-*` audit skills only when the question needs measurement, files, or a full audit.

## Updating the Knowledgebase

Maintainers edit only:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Then run:

```powershell
cd plugins\seo-helper
python scripts\maintain.py rebuild-index
python scripts\maintain.py validate
```

Existing users update with:

```powershell
git pull
```

If they uploaded files to ChatGPT or Claude Projects, they should upload the new HTML again.

## Links

Repo:

```text
https://github.com/bijay085/SEO-NoteBook
```

Plugin folder:

```text
https://github.com/bijay085/SEO-NoteBook/tree/main/plugins/seo-helper
```

Detailed setup:

```text
SETUP.md
```
