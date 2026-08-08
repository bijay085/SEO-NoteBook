# SEO Helper Setup

This guide is for a new user who found the GitHub repo and wants to use SEO Helper without guessing what to install.

Repo:

```text
https://github.com/bijay085/SEO-NoteBook
```

The only plugin folder is:

```text
SEO-NoteBook/plugins/seo-helper
```

The only knowledgebase HTML is:

```text
SEO-NoteBook/plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

## 1. Download the Repo

### Windows

Open Command Prompt or PowerShell, then run:

```powershell
cd /d E:\
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook
START_HERE.bat
```

If you cloned somewhere else, open that folder and double-click:

```text
START_HERE.bat
```

That file checks the plugin and shows the exact local plugin path.

### macOS or Linux

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook/plugins/seo-helper
python scripts/maintain.py validate
```

If validation says `SEO Helper validation passed`, the files are ready.

## 2. ChatGPT Custom GPT Setup

Use this when you want a normal GPT inside ChatGPT.

1. Open ChatGPT.
2. Go to `Explore GPTs`.
3. Click `Create`.
4. Open the `Configure` tab.
5. Name it:

```text
SEO Helper
```

6. In `Instructions`, paste:

```text
You are SEO Helper, a practical SEO decision assistant.

Use the uploaded SEO_Action_Decision_System.html file as the main knowledgebase.

Answer the exact SEO question. Do not give generic SEO advice unless the user asks for basics.

Use if/then decision logic. Prefer the most relevant rule from the knowledgebase instead of reading or summarizing everything.

Default answer format:
Mode:
What:
Why:
How:
Evidence:
Priority:

If the user pastes Reddit threads, articles, notes, or files, extract only reusable decision rules. Ignore spam, insults, repeated opinions, and unsupported shortcuts.

If evidence is missing, say what data is needed instead of guessing. Keep answers concise and actionable.
```

7. In `Knowledge`, upload this file:

```text
SEO-NoteBook/plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

8. Save the GPT.

Test prompt:

```text
A service page is indexed but has no impressions. What should I check first?
```

Use this setup if you only need the decision helper. Do not upload the whole repo for a basic GPT.

## 3. ChatGPT Project Setup

Use this when you want SEO Helper inside a ChatGPT Project instead of a custom GPT.

1. Create or open a Project.
2. Upload these files:

```text
SEO-NoteBook/plugins/seo-helper/skills/seo-router/SKILL.md
SEO-NoteBook/plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

3. Add this Project instruction:

```text
Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html as the SEO knowledgebase. Answer only the relevant part of the user's question with What, Why, How, Evidence, and Priority. Load or request deeper audit files only when the task needs measurement.
```

4. Optional: upload extra `seo-*` skill folders only when you need that deep audit.

Test prompt:

```text
Use SEO Helper. Organic clicks dropped but impressions stayed stable. What does that mean?
```

## 4. Claude Code Plugin Setup

Use this when you want the full plugin in Claude Code.

1. Clone the repo:

```powershell
git clone https://github.com/bijay085/SEO-NoteBook.git
```

2. Copy the full path to this folder:

```text
SEO-NoteBook/plugins/seo-helper
```

Example Windows path:

```text
E:\SEO-NoteBook\plugins\seo-helper
```

3. In Claude Code, run:

```text
/plugin install E:\SEO-NoteBook\plugins\seo-helper
```

4. Start a new Claude Code chat.

Test prompt:

```text
Load seo-router. Traffic dropped on my Shopify store. What should I check first?
```

Future updates:

```powershell
cd E:\SEO-NoteBook
git pull
```

Start a new Claude Code chat after pulling updates. Reinstall only if Claude copied the plugin instead of using the local repo folder.

## 5. Claude Project Setup

Use this when you are using claude.ai Projects, not Claude Code.

1. Create or open a Claude Project.
2. Upload these two files first:

```text
SEO-NoteBook/plugins/seo-helper/skills/seo-router/SKILL.md
SEO-NoteBook/plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

3. Add this Project instruction:

```text
Use SEO Helper. Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html for SEO rules. Answer with Mode, What, Why, How, Evidence, and Priority. Do not dump the whole knowledgebase. Use only the relevant rule for the user's question.
```

4. Optional: upload specific audit skill folders only when you need them.

Test prompt:

```text
A new website is indexed but not ranking after months. What should I diagnose first?
```

## 6. Codex or Cursor Skills Setup

Use this when your AI coding tool supports local skills.

### Windows

```powershell
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook\plugins\seo-helper
.\install-skills.ps1
pip install -r requirements.txt
pip install -r server\requirements.txt
python scripts\maintain.py validate
```

### macOS or Linux

```bash
git clone https://github.com/bijay085/SEO-NoteBook.git
cd SEO-NoteBook/plugins/seo-helper
chmod +x install-skills.sh
./install-skills.sh
pip install -r requirements.txt
pip install -r server/requirements.txt
python scripts/maintain.py validate
```

Test prompt inside the AI tool:

```text
Load seo-router. I have high impressions but low CTR. What should I do first?
```

## 7. Optional MCP Setup

Use MCP only if your AI tool supports MCP and you want section lookup or routing as tools.

1. Open this file:

```text
SEO-NoteBook/plugins/seo-helper/mcp-hosts.example.json
```

2. Copy the `seo-helper-router` block into your AI tool's MCP settings.
3. Replace every `ROOT` with your full plugin folder path.

Example Windows value:

```text
E:\SEO-NoteBook\plugins\seo-helper
```

4. Test locally:

```powershell
cd E:\SEO-NoteBook\plugins\seo-helper
python server\seo_router_server.py --self-test
```

If it works, the MCP exposes:

```text
list_decision_sections
get_decision_section
route_seo_situation
list_seo_audit_skills
```

## 8. Other AI Tools

If your AI tool has file uploads but no plugin system:

Upload these two files:

```text
SEO-NoteBook/plugins/seo-helper/skills/seo-router/SKILL.md
SEO-NoteBook/plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

Paste this instruction:

```text
You are SEO Helper. Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html as the knowledgebase. Answer the exact SEO question with What, Why, How, Evidence, and Priority. Use only the relevant rule. Ask for missing evidence instead of guessing.
```

If the tool supports folders, upload extra `SEO-NoteBook/plugins/seo-helper/skills/seo-*` folders only for the specific audits you want.

## 9. How to Use After Setup

Ask direct questions like:

```text
Use SEO Helper. My page is indexed but has no impressions. What should I check first?
```

```text
Use SEO Helper. My rankings dropped yesterday after 4 months of growth. What is the triage order?
```

```text
Use SEO Helper. Clean this pasted Reddit SEO thread and add only reusable decision rules.
```

```text
Use SEO Helper. Which audit skill should I use for a traffic decline with GSC data?
```

## 10. Updating Later

Users update with Git:

```powershell
cd E:\SEO-NoteBook
git pull
cd plugins\seo-helper
python scripts\maintain.py validate
```

If using ChatGPT or Claude Project uploads, upload the new `SEO_Action_Decision_System.html` again after pulling updates.

If using Claude Code from the local plugin path, usually `git pull` plus a new chat is enough.

## 11. Maintainer Update Flow

When adding new SEO knowledge:

1. Edit only:

```text
plugins/seo-helper/knowledge/SEO_Action_Decision_System.html
```

2. Run:

```powershell
cd plugins\seo-helper
python scripts\maintain.py rebuild-index
python scripts\maintain.py validate
```

3. Commit:

```powershell
git add knowledge\SEO_Action_Decision_System.html skills\seo-router\references\section-index.md
git commit -m "Update SEO helper knowledgebase"
git push
```

Do not create another knowledgebase copy.
