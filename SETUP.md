# SEO Helper Setup

Run one file:

```powershell
START_HERE.bat
```

That is the setup app. If Python is missing, the launcher asks before installing Python for the current Windows user with `winget`.

## Choose By Goal

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

## 1. Install Globally

Use this if you want SEO Helper available again and again without setting it up for every project.

It installs required Python packages and syncs SEO Helper skills into common local skill folders for this Windows user:

```text
%USERPROFILE%\.codex\skills
%USERPROFILE%\.claude\skills
%USERPROFILE%\.cursor\skills
```

After that, in a new project just ask:

```text
Use SEO Helper for this SEO case: [paste problem]
```

## 2. Use In One Project Or Custom GPT

Use this when you do not want global install or you are using another AI account.

The launcher will:

- select the exact knowledgebase file
- copy instructions to clipboard
- open GPT Builder when you choose Custom GPT

The selected file is:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

For Custom GPT, upload that file in Knowledge and paste the copied instructions.

For Claude/ChatGPT projects, upload that file and paste the copied instructions.

## 3. Update SEO Helper Everywhere

Use this after new rules are pushed.

It runs:

- `git pull`
- plugin validation
- global skill sync again

This keeps local global skills fresh.

Important: if you uploaded the HTML to a Custom GPT or a project, upload the updated HTML again because those products keep their own copy.

## 4. Advanced Claude Code Plugin Install

Use this only if you specifically want Claude Code's plugin install system.

The launcher copies the correct command:

```text
/plugin install [your local plugins/seo-helper path]
```

Claude Code still requires entering that command inside Claude.

## 5. Validate Only

Checks that the repo and canonical knowledgebase are working.

## No Required Connectors

SEO Helper works from provided data first:

- pasted notes
- screenshots
- GSC exports
- GA4 exports
- crawl exports
- logs
- manual context
- the built-in knowledgebase

No connector is required for normal use.

Optional live-data connectors are only useful when a user wants live external data access.

## Single Source Of Truth

The only knowledgebase is:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Keep the system clean. Do not create duplicate knowledgebase files.
