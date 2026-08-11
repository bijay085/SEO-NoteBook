# SEO Quick Audit

Use this when the user wants a combined next-step audit, not a routing-only answer.

The user should be able to write normal language, for example:

`/seo-quick-audit Indexed service pages, no impressions, and the homepage dropped.`

Behavior:

- Given the user's situation, call `route_seo_situation` (or follow `${CLAUDE_PLUGIN_ROOT}/skills/seo-router/SKILL.md`).
- If `confidence` is `low`, ask the one clarifying question first. Do not start an audit until the section is confirmed.
- Otherwise, load the returned `section_id` via `get_decision_section`.
- Then run each skill listed in `suggested_skills` in order, carrying findings from one into the next.
- Produce one combined summary at the end instead of stopping after routing.
- Use relative plugin paths only. Do not hardcode drive letters.

Output shape:

- Situation
- Routed section and confidence
- Combined findings
- Do next
- Need data, if any
