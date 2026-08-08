# SEO NoteBook: SEO Helper

SEO Helper is one clean SEO decision system by Bijay.

It is designed to work two ways:

- global install once on your computer, then use it in future projects
- one-project use when you only want to upload/share the knowledge file

## Fast Start on Windows

```powershell
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook
START_HERE.bat
```

Choose by goal, not by confusing tool names:

```text
1. Recommended: Install once on this computer
   Choose this if you want SEO Helper available in future projects.
   What happens: copies SEO skills to your user-level Codex, Claude, and Cursor skill folders.

2. Use only in one project or Custom GPT
   Choose this for ChatGPT GPT Builder, Claude Project, another account, or one-time sharing.
   What happens: opens/selects the single HTML knowledge file and copies ready instructions.

3. Update SEO Helper everywhere
   Choose this after Bijay pushes new rules or fixes.
   What happens: runs git pull, validates, then re-syncs global skills.

4. Advanced: Claude Code plugin install
   Choose this only if you specifically use Claude Code plugin commands.
   What happens: copies the /plugin install command and tries to open Claude Code.

5. Check setup only
   Choose this if you only want to confirm the plugin works.
   What happens: exits after validation; nothing is installed or changed.

0. Exit
```

## Best Setup

For most people, choose:

```text
1. Install globally on this computer
```

That syncs the SEO skills into common local AI skill folders for this Windows user:

```text
%USERPROFILE%\.codex\skills
%USERPROFILE%\.claude\skills
%USERPROFILE%\.cursor\skills
```

After that, in future projects ask:

```text
Use SEO Helper for this SEO case: [paste problem]
```

## Updating Later

Run:

```powershell
START_HERE.bat
```

Choose:

```text
3. Update SEO Helper everywhere
```

It pulls the latest repo, validates, and syncs the global skills again.

If you uploaded the HTML into a Custom GPT or an AI project, upload the updated HTML again because those systems keep their own copy.

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

## Single Source of Truth

Canonical knowledgebase:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Do not create duplicate knowledgebase copies. This HTML file is the shareable one-file version and the source used by the skills.

## One-Project Use

Choose this in `START_HERE.bat`:

```text
2. Use in one project or Custom GPT
```

The launcher selects the right HTML file and copies the instructions to clipboard.

Use this when:

- you are using a different AI account
- you do not want global install
- you are sharing with someone who only needs the knowledgebase
- you are making a Custom GPT

## Maintainer Flow

Edit new rules in:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Then run:

```powershell
python plugins\seo-helper\scripts\maintain.py rebuild-index
python plugins\seo-helper\scripts\maintain.py validate
```

Commit and push.
