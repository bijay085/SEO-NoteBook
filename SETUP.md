# SEO Helper Setup

Run one file:

```powershell
START_HERE.bat
```

That is the setup app.

## Choose By Goal

```text
1. Install globally on this computer - use in future projects
2. Use in one project or Custom GPT
3. Update SEO Helper everywhere
4. Advanced: Claude Code plugin install
5. Validate only
0. Exit
```

## 1. Install Globally

Use this if you want SEO Helper available again and again without setting it up for every project.

It installs/syncs SEO Helper skills into common local skill folders for this Windows user:

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
