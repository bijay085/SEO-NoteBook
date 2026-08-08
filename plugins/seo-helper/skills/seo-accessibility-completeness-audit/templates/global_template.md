# Global Page Template and Shared-Element Audit Profile

This profile applies to every indexable HTML page. It covers the document shell and shared elements surrounding the page-type-specific body.

## Document model

```text
html[lang]
├── head
│   ├── title and metadata
│   ├── canonical/indexing directives
│   └── required resources
└── body
    ├── skip link
    ├── header
    │   ├── brand/home link
    │   └── primary navigation
    ├── breadcrumb navigation (when useful)
    ├── main
    │   └── page-type body
    ├── complementary/related regions (when useful)
    └── footer
```

## Shared-element requirements

| Region | Required condition | Audit focus |
|---|---|---|
| Document | Valid document language and recoverable text | `lang`, encoding, source/render parity |
| Head | Unique descriptive title and consistent index signals | title, canonical, robots, conflicting directives |
| Skip link | Keyboard route to primary content | visible on focus, valid target |
| Header | Distinct site identity and shared controls | landmark scope, repeated content |
| Navigation | Links grouped and named by purpose | native `nav`, accessible name, current state |
| Breadcrumbs | Hierarchy represented as navigation | ordered path, current page, visible/schema agreement |
| Main | One coherent page-specific primary region | one `<main>`, task and H1 containment |
| Headings | Logical content hierarchy | one page-level H1, no styling-only levels |
| Sections | Boundaries recoverable without CSS | headings or accessible labels, coherent containment |
| Links | Navigation uses meaningful destinations | purpose, anchor context, no button impersonation |
| Buttons | Actions expose names and state | native button, keyboard behavior, state changes |
| Forms | Inputs have labels, instructions, errors, and outcomes | association, units, required state, announcements |
| Images | Purpose represented according to role | informative `alt`, empty decorative `alt` |
| Figures | Media and caption form one unit | `figure`, `figcaption`, native critical data |
| Tables | Row/column relationships remain recoverable | caption, headers, scope, responsive access |
| Lists | Repeated peer items retain list semantics | `ul`, `ol`, `dl` as appropriate |
| Aside | Complementary material stays outside the primary flow | label, relevance, no primary content displaced |
| Related content | Clearly secondary and destination-specific | labelled region, contextual links |
| Footer | Shared legal/contact/navigation content is identifiable | footer scope, NAP consistency when present |
| Structured data | Matches visible facts and page type | entity identity, values, dates, URLs |
| Dynamic content | Content and state remain available and understandable | DOM insertion, focus, live announcements |
| Responsive layout | Meaning and reading order survive breakpoints | mobile/desktop order, hidden content, overlap |
| Extraction | Flattened text preserves sentence and region coherence | boilerplate intrusion, interrupted prose |

## ARIA policy

Use native elements first. Add ARIA only when native semantics do not express the required name, relationship, state, or live update. Every `aria-labelledby` and `aria-describedby` reference must resolve to an existing unique ID. An `aria-label` must describe the control's function and must not conflict with visible text. Do not add roles that duplicate or contradict native semantics.

## Boilerplate boundary

Header, site navigation, promotional bars, sharing controls, related links, ads, cookie controls, and footer content must not interrupt paragraph text or become children of the primary article prose when they are separate functions. CSS may position sibling regions without corrupting DOM order.

## Global inheritance

Page-type templates inherit every applicable global rule. A page-type template may refine a global requirement but must not disable accessibility, truthfulness, evidence, or cross-representation consistency rules.
