# ChatGPT project context

This directory is a local mirror of the ChatGPT project "My Notes".

- Treat every file under `sources/` as read-only reference material.
- Do not edit, rename, move, or delete synced project files.
- These files may be replaced the next time a task is created from this ChatGPT project.

## Project instructions

This project is an SEO notebook. When the user pastes SEO information, Reddit discussions, article notes, Google/Search Console observations, or other source material and asks to edit/add/update:

- The canonical plugin notebook is `plugins/seo-helper/assets/SEO_Action_Decision_System.html`. The root `SEO_Action_Decision_System.html` is a standalone share/export copy for people who do not use AI tools. Keep those two aligned, but do not create any extra notebook copies inside skills.
- First check the canonical plugin notebook and place the update in the most relevant existing section instead of creating a confusing duplicate section.
- Treat pasted sources as practitioner input unless they are official documentation. Convert them into concise operational rules, checklists, tables, or decision logic.
- Keep additions compact and low-token: summarize the useful idea, remove navigation/noise, avoid long quotes, and do not paste raw source text unless the user explicitly asks.
- Preserve the notebook style: short explanation, practical rule, table when comparison helps, and bullets for action steps or myths.
- If the pasted source repeats an existing rule, merge or strengthen the existing section instead of adding another version.
- When sources conflict, prefer official search engine documentation, then measured site data such as GSC/GA4/crawl evidence, then practitioner examples.
- Add source context briefly, for example "Added from a user-supplied Reddit discussion as practitioner input," without over-explaining.
- Do not browse the web unless the user asks for current verification or the claim needs up-to-date confirmation.
- After editing, verify the inserted heading exists and do a light HTML structure check such as matching table/list counts.

## SEO Helper plugin goal

The `plugins/seo-helper` plugin should optimize for speed, accuracy, and low token use:

- Use `seo-decision-helper` as the single entry point for SEO decisions.
- Route the user request first, then load only the matching notebook section or one needed `seo-*` audit skill.
- Answer the exact part the user asked for with What / Why / How / Evidence / Priority.
- Add related surrounding context only when it changes the decision or prevents a wrong recommendation.
- Do not read the whole notebook, all skills, or all source files for a narrow question.
- Do not include random SEO facts, generic filler, or broad audits unless the user asked for them.
- If files/data are supplied, analyze the relevant file columns/pages/evidence first and mark missing evidence as not tested instead of guessing.
- Keep pasted-source additions compact and operational: one useful rule beats a long copied thread.