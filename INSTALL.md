# SEO Helper Install Guide

This folder is the plugin root:

```text
plugins/seo-helper
```

If you are viewing this inside the repo, the main full setup guide is:

```text
../../SETUP.md
```

## Fast Validation

From this folder:

```powershell
python scripts\maintain.py validate
```

Expected result:

```text
SEO Helper validation passed
```

## ChatGPT Custom GPT

Use this when creating a GPT in ChatGPT.

1. Open ChatGPT.
2. Go to `Explore GPTs`.
3. Click `Create`.
4. Open `Configure`.
5. Upload this file in Knowledge:

```text
knowledge/SEO_Action_Decision_System.html
```

6. Paste this in Instructions:

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

If evidence is missing, say what data is needed instead of guessing. Keep answers concise and actionable.
```

7. Save and test:

```text
A page is indexed but has no impressions. What should I check first?
```

## ChatGPT Project

Upload:

```text
skills/seo-router/SKILL.md
knowledge/SEO_Action_Decision_System.html
```

Project instruction:

```text
Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html as the SEO knowledgebase. Answer only the relevant part of the user's question with What, Why, How, Evidence, and Priority. Load deeper audit material only when needed.
```

## Claude Code

Install the whole plugin folder:

```text
/plugin install C:\path\to\SEO-NoteBook\plugins\seo-helper
```

Example:

```text
/plugin install E:\SEO-NoteBook\plugins\seo-helper
```

Test:

```text
Load seo-router. Traffic dropped on my Shopify store. What should I check first?
```

Update later:

```powershell
cd E:\SEO-NoteBook
git pull
```

Then start a new Claude Code chat.

## Claude Project

Upload:

```text
skills/seo-router/SKILL.md
knowledge/SEO_Action_Decision_System.html
```

Project instruction:

```text
Use SEO Helper. Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html for SEO rules. Answer with Mode, What, Why, How, Evidence, and Priority. Do not dump the whole knowledgebase. Use only the relevant rule.
```

## Codex or Cursor

Windows:

```powershell
cd SEO-NoteBook\plugins\seo-helper
.\install-skills.ps1
pip install -r requirements.txt
pip install -r server\requirements.txt
python scripts\maintain.py validate
```

macOS or Linux:

```bash
cd SEO-NoteBook/plugins/seo-helper
chmod +x install-skills.sh
./install-skills.sh
pip install -r requirements.txt
pip install -r server/requirements.txt
python scripts/maintain.py validate
```

Test:

```text
Load seo-router. I have high impressions but low CTR. What should I do first?
```

## Other AI Tools

If the tool supports uploads but not plugins, upload:

```text
skills/seo-router/SKILL.md
knowledge/SEO_Action_Decision_System.html
```

Instruction:

```text
You are SEO Helper. Follow seo-router/SKILL.md. Use SEO_Action_Decision_System.html as the knowledgebase. Answer the exact SEO question with What, Why, How, Evidence, and Priority. Use only the relevant rule. Ask for missing evidence instead of guessing.
```

Upload extra `seo-*` skill folders only when you need those audits.

## Optional MCP

Use MCP only if your AI tool supports MCP.

1. Open:

```text
mcp-hosts.example.json
```

2. Copy the `seo-helper-router` block.
3. Replace `ROOT` with the absolute path to this folder.
4. Test:

```powershell
python server\seo_router_server.py --self-test
```

MCP tools:

```text
list_decision_sections
get_decision_section
route_seo_situation
list_seo_audit_skills
```

## Updating Knowledge

Edit only:

```text
knowledge/SEO_Action_Decision_System.html
```

Then run:

```powershell
python scripts\maintain.py rebuild-index
python scripts\maintain.py validate
```

Do not create another `SEO_Action_Decision_System.html` anywhere else.
