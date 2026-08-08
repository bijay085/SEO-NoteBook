# SEO Helper Setup

Use `START_HERE.bat`. That is the setup flow.

## Windows

```powershell
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook
START_HERE.bat
```

The launcher will check the plugin and show a menu:

```text
1. Claude Code plugin
2. ChatGPT Custom GPT
3. Codex / local skills
4. Update this repo
5. Validate only
0. Exit
```

Pick the tool you use. Do not manually browse random folders first.

## What Each Option Does

### 1. Claude Code Plugin

This is the closest real plugin install.

The launcher copies the correct `/plugin install ...` command to your clipboard and opens Claude Code when the `claude` command exists.

Claude Code still requires the command to be entered inside Claude. That is a Claude limitation, not an SEO Helper file problem.

After install, ask:

```text
Use SEO Helper for this SEO case: [paste problem]
```

### 2. ChatGPT Custom GPT

ChatGPT Custom GPT cannot install a local plugin folder automatically.

The launcher does the practical parts for you:

- opens GPT Builder
- opens File Explorer with the correct knowledge file selected
- copies the GPT instructions to your clipboard

In GPT Builder:

1. Create a GPT.
2. Paste the copied instructions.
3. Upload the selected file: `SEO_Action_Decision_System.html`.
4. Save.

That is the shortest possible Custom GPT setup without building a hosted ChatGPT App.

### 3. Codex / Local Skills

The launcher installs the SEO skills locally and validates the plugin.

After it finishes, ask Codex:

```text
Use seo-router for this SEO case: [paste problem]
```

### 4. Update This Repo

The launcher runs update and validates again.

Use this after Bijay pushes new knowledgebase changes.

### 5. Validate Only

Checks that the plugin files are present and the canonical knowledgebase is readable.

## No Required Connectors

SEO Helper works without connectors.

It uses the built-in knowledgebase plus whatever the user provides:

- pasted notes
- Reddit/source text
- screenshots
- GSC exports
- GA4 exports
- crawl exports
- server logs
- URLs and manual context

Optional connectors such as Semrush, Cloudflare, Google Drive, Notion, or Airtable are not required. Add them only when live external data access is needed.

## Single Source of Truth

The only knowledgebase is:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Do not create duplicate HTML copies. Do not upload the whole repo when one knowledge file is enough.

## Maintainer Update Flow

After adding or editing rules:

```powershell
python plugins\seo-helper\scripts\maintain.py rebuild-index
python plugins\seo-helper\scripts\maintain.py validate
```

Then commit and push.
