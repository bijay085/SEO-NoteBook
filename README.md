# SEO NoteBook: SEO Helper

SEO Helper is one clean SEO decision plugin by Bijay.

It helps AI tools answer SEO questions with practical decision logic instead of generic advice.

## Fast Start on Windows

```powershell
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook
START_HERE.bat
```

`START_HERE.bat` is the main setup launcher. It validates the plugin, then lets you choose:

- Claude Code plugin setup
- ChatGPT Custom GPT setup
- Codex / local skills setup
- update with `git pull`
- validate only

## No Required Connectors

SEO Helper does not require GitHub, Semrush, Cloudflare, Google Drive, Airtable, or any other connector to answer SEO cases.

The core works from:

- pasted text
- uploaded files
- GSC exports
- GA4 exports
- crawl exports
- screenshots
- manual notes
- the built-in HTML knowledgebase

Optional connectors are only for live external data. Do not install them unless the workflow actually needs live data.

## What It Does

SEO Helper helps with:

- traffic drops and ranking diagnosis
- indexed but no impressions
- local SEO and GBP decisions
- money pages, service pages, product pages, and location pages
- internal linking, cannibalization, canonical, robots, rendering, migration, and technical SEO issues
- AI visibility, AEO, GEO, citations, and brand presence
- source cleanup from Reddit threads, article notes, and case studies
- routing to deeper audit skills only when needed
- token optimization by using only the relevant rule or section

## Main Files

Installable plugin folder:

```text
plugins/seo-helper
```

Canonical knowledgebase:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Do not use duplicate knowledgebase copies. This HTML file is the single source of truth.

## For Maintainers

Edit only the canonical knowledgebase for new SEO rules:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Then run:

```powershell
python plugins\seo-helper\scripts\maintain.py rebuild-index
python plugins\seo-helper\scripts\maintain.py validate
```

Users update with:

```powershell
git pull
START_HERE.bat
```

## Important Reality

Claude Code can install the local plugin folder.

ChatGPT Custom GPT cannot auto-install a local GitHub repo from a `.bat` file. The launcher opens GPT Builder, selects the exact HTML file, and copies the instructions to the clipboard so setup is as close to plug-and-play as ChatGPT currently allows.
