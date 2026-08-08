# SEO Decision

Use this when the user gives an SEO situation and wants the right next decision.

The user should be able to write normal language, for example:

`/seo-decision My service pages are indexed but getting no impressions. What should I check first?`

Behavior:

- Use the existing SEO skill set when a specific audit/workflow is needed.
- Use `plugins/seo-helper/knowledge/SEO_Action_Decision_System.html` as the knowledgebase when the answer needs decision logic, similar cases, or source-backed patterns.
- Do not load the whole knowledgebase for every answer. Read only the relevant section or infer from the matching case.
- Keep the answer short unless the user asks for a full audit.
- Explain the situation, the likely reason, the decision, and the next check/action.
- If data is needed, ask only for the exact missing data that changes the decision.

Output shape:

- Situation
- Likely issue
- Do next
- Need data, if any
