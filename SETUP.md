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
   What happens: copies SEO skills and registers SEO Helper for app/plugin pickers and installs all `/seo-*` command files for tools that support local command folders.

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

It installs required Python packages and syncs SEO Helper skills into common local skill folders and registers the plugin picker entry and `/seo-decision` command for this Windows user:

```text
%USERPROFILE%\.codex\skills
%USERPROFILE%\.codex\commands\seo-*.md  (18 commands)
%USERPROFILE%\.claude\skills
%USERPROFILE%\.claude\commands\seo-*.md  (18 commands)
%USERPROFILE%\.cursor\skills
%USERPROFILE%\.agents\plugins
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
- Python package install/update
- global skill sync again
- plugin picker registration refresh

This keeps local global skills fresh.

Important: if you uploaded the HTML to a Custom GPT or a project, upload the updated HTML again because those products keep their own copy.

## 4. Advanced Claude Code Plugin Install

Use this only if you specifically want Claude Code's plugin install system.

The launcher copies the correct command:

```text
/plugin install [your local plugins/seo-helper path]
```

Claude Code still requires entering that command inside Claude.

## 5. Where Can I Use This?

Shows which setup method to use for GPT, Claude, Cursor, Antigravity, and other AI apps.

## 6. Validate Only

Checks that the repo and canonical knowledgebase are working.

## Where You Can Use SEO Helper

SEO Helper can be used in different places, but the setup method depends on what the app supports.

| Place | Best Method | Notes |
|---|---|---|
| GPT classic / normal ChatGPT chat | One-project file upload | Upload or attach `SEO_Action_Decision_System.html` when the chat/project supports files. |
| New GPT with Codex integrated | Global install for Codex + project file when needed | Use option 1 for Codex skills; use option 2 if the GPT side needs the HTML uploaded. |
| New GPT normal chat | One-project file upload | Use option 2. ChatGPT chats cannot install local skill folders globally. |
| GPT cowork / collaborative project | One-project file upload | Use option 2 and upload the HTML to that shared project/workspace. |
| New GPT Codex | Global install | Use option 1. It syncs the Codex skill and `/seo-decision` command. |
| GPT web | Custom GPT or project upload | Use option 2. For Custom GPT, upload the HTML as Knowledge. |
| GPT web cowork | Project upload | Use option 2 and upload the HTML to the shared project/workspace. |
| Claude web chat | One-project file upload | Use option 2. Claude web chat cannot use local Windows skill folders directly. |
| Claude web Project / cowork | Project upload | Use option 2 and upload the HTML to the project. |
| Claude desktop app chat | Global install if the app reads local skills, otherwise project/file upload | Use option 1 first; if not detected by Claude, use option 2. |
| Claude desktop cowork | Project/file upload | Use option 2 unless that workspace supports local skills. |
| Claude Code desktop/local | Claude Code plugin or global skills | Use option 4 for `/plugin install`, or option 1 for skill folders. |
| Claude web Claude Code | Claude Code plugin path if supported; otherwise project upload | Use option 4 when Claude Code accepts plugin commands. |
| Cursor | Global install | Use option 1. It syncs to `%USERPROFILE%\.cursor\skills` and registers the plugin in `%USERPROFILE%\.agents\plugins`. |
| Antigravity or other AI coding tools | Local skill folder or one-file knowledge upload | If it supports local skills, point it to `plugins/seo-helper/skills` or copied global skills. If not, use the HTML file. |
| Any AI with file upload | One-file knowledge upload | Upload `plugins/seo-helper/knowledge/SEO_Action_Decision_System.html`. |

Rule of thumb:

- If the tool supports local skills/plugins, use option 1 or option 4.
- If the tool is web chat, shared project, cowork, or another account, use option 2.
- If you want updates with less stress, keep the repo and use option 3.
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
