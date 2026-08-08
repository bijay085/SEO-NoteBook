# Lean Annotated Miro Semantic HTML5 Handoff Schema

## Purpose

Create a compact, editable designer/developer handoff that shows how the supplied page design and replacement content should use semantic HTML5. The wireframe carries the implementation guidance; the board is not a report and is not a page-wide Custom HTML snippet.

## Inputs

- Replacement content or content outline
- Existing page HTML for current DOM evidence
- Existing screenshot, saved page, or live URL for visual evidence
- Known URLs, media, forms, dynamic components, and CMS constraints
- `elements.csv` for element selection, `accessibility_mappings.csv` for computed semantics, and `audit_rules.csv` for QA

When HTML is missing, describe tag choices as proposed rather than observed. Never infer DOM structure from a screenshot alone.

## Required output

### A. Annotated page wireframe - mandatory

Build one recognizable vertical page wireframe based on the supplied current design. Preserve replacement-content order and show enough real content for a designer to identify every region.

Place the actual tag on or immediately beside the object it describes. Annotate both the parent and meaningful children, for example:

```text
<section aria-labelledby="services-heading">
  <h2>Our Retirement Planning Services in San Diego</h2>
  <p>Section introduction</p>
  <div>visual card grid</div>
    <div><h3>Service name</h3><p>Description</p></div>
```

This notation explains the structure. It is not a full code fragment for direct insertion.

The wireframe must show, when supplied:

- `header`, named primary `nav`, and their real link/button/image objects
- exactly one `main` boundary
- hero content with its actual `h1`, paragraphs, actions, and media
- each thematic `section` with its real `h2` and meaningful child structure
- `article` only for independently reusable or distributable content
- layout-only `div` wrappers where no semantic element applies
- `figure` and `figcaption` for captioned media
- `ol`/`ul` and `li` for sequences and collections
- `blockquote` plus attribution for verified testimonials
- `form`, `label`, native controls, and submit `button`
- `details` with first-child `summary` for disclosures or FAQs
- complementary `aside` only when content is truly secondary
- site `footer`, `address`, and distinctly named footer `nav`
- navigation controls such as “Read More” as `<a href>` with destination context
- in-page actions such as “Show More” as `<button>` with required state and controlled-target notes
- dynamic objects with their required accessible name source and state, such as `aria-expanded`, `aria-selected`, `aria-pressed`, or dialog naming

For grids and split layouts, show desktop placement and preserve the intended DOM reading order. Add one short note on an affected object when a URL, form action, asset, alternative text, quotation, or dynamic behavior remains unresolved.

### B. Semantic QA - mandatory

Use one compact checklist, grouped only when useful:

- Exactly one visible `main`, with valid ancestry
- Thematic sections have accessible names
- `article` is reserved for independent content
- `nav` is reserved for major navigation; repeated landmarks have distinct names
- Heading levels follow content hierarchy
- `figure` and `figcaption` remain associated
- `time` uses a valid `datetime` value when present
- Every `details` begins with `summary`
- Links, buttons, lists, forms, and disclosures use native controls
- Tables represent data, never layout
- Semantic elements are selected by meaning
- No redundant or conflicting ARIA
- Rendered CMS DOM preserves the planned structure and reading order
- Browser-computed role matches the intended object purpose
- Computed accessible name contains the visible control wording and identifies repeated controls
- Hidden or inactive content is not unexpectedly focusable or exposed
- Dynamic controls expose the correct current state after interaction
- DOM, visual, focus, and accessibility-tree order remain logical
- Final implementation receives keyboard and selected assistive-technology verification for critical paths

### C. Semantic mapping table - optional

Include the table only when the user requests it or when the wireframe cannot carry a dense mapping legibly. Use exactly these columns:

| Page region | Required semantic structure | Developer instruction |
| --- | --- | --- |
| Human-readable region name | Actual tag and nesting pattern | One concise CMS, behavior, or accessibility instruction |

Do not add region IDs, status fields, evidence columns, design columns, content excerpts, or decision-matrix fields by default.

## Board layout

- Make the annotated wireframe the largest and first object.
- Place QA in a narrow panel beside or below the wireframe.
- Place the optional table after the wireframe, not before it.
- Keep tags readable at normal board zoom and visually attached to their objects.
- Use light category color cues only when they improve scanning; a separate legend is not required.
- Use one board per page unless the user requests a system map.

## Default exclusions

Do not include these unless explicitly requested:

- Current-state audit zone
- Keep/repair/replace/move decision matrix
- Separate designer instruction cards
- Separate developer instruction cards
- Dependency card bank
- Component-ID inventory
- Large tag glossary or color legend
- Cover page, executive summary, SEO narrative, or source appendix

## Acceptance criteria

The Miro handoff passes when:

- The current design remains recognizable.
- All supplied replacement content appears in the intended page order.
- Actual tags are mapped to the relevant visible objects, including meaningful children.
- Layout wrappers are not mislabeled as semantic sections.
- The compact QA checklist is present and matches `audit_rules.csv`.
- Interactive annotations distinguish navigation links from action buttons.
- Required computed names, controlled targets, and dynamic states appear beside affected objects without creating a separate report zone.
- Any optional table uses the approved three-column schema and agrees with the wireframe.
- Missing values are marked without inventing data.
- The board contains no unrequested report zones.

## Response after board creation

Return only:

1. Direct editable Miro board link
2. Short list of unresolved implementation dependencies, if any
