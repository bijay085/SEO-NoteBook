# Semantic HTML5 Knowledge Base : SEO & Accessibility Reference

This document is generated from `semantic_html_audit.sqlite`, the database of record. Do not hand-edit facts here : update the database and re-run `generate_knowledge_base.py`.

## 1. What "Semantic HTML" Means

> "Semantics refers to the meaning of a piece of code : what purpose or role an element has, rather than what it looks like." : MDN
>
> "Writing semantic HTML means using HTML elements to structure your content based on each element's meaning, not its appearance." : web.dev

A **non-semantic** element (`<div>`, `<span>`) tells the browser, assistive technology, and other developers nothing about the content it wraps : only how it might be styled. A **semantic** element (`<nav>`, `<button>`, `<article>`, `<time>`) declares what the content *is*, so three different consumers can each do their job correctly without extra hints:

- **Browsers** apply correct default behaviour and expose an accessibility tree (e.g. `<button>` gets keyboard focus, `Enter`/`Space` activation, and tab order for free; a `<div onclick>` gets none of it).
- **Assistive technology** (screen readers, switch devices) builds a landmark/heading outline straight from the markup, letting users jump by region instead of reading linearly.
- **Search engines and other machine readers** parse structure to identify the primary content, navigation, and metadata blocks : see Section 2 for exactly what is and isn't confirmed about this.

Semantic HTML is presentation-independent by design: **appearance is CSS's job, meaning is HTML's job.** Choosing an element for how the browser's default stylesheet renders it (e.g. a `<span>` styled to look like a heading) inverts this and produces markup with the right *look* but no real meaning.

## 2. The SEO Relationship : What's Actually Confirmed

SEO blog content routinely asserts that semantic HTML "boosts rankings." The table below grades every such claim collected from the six reference sources against normative (WHATWG) and first-party (Google Search Central) sources, so recommendations can be built on what's actually established rather than repeated folklore.

| Status | Meaning |
|---|---|
| `confirmed` | Directly stated by the HTML spec or a primary engine/search source. |
| `partly-supported` | A real, documented mechanism exists, but the strong version of the claim overreaches it. |
| `unverified` | Asserted by secondary (usually marketing/blog) sources; no primary source confirms it. |
| `contradicted` | A primary source directly conflicts with the claim. |

### CLM-001 : `confirmed` (meaning)

**Claim:** Semantic elements communicate purpose to browsers, developers, and assistive technologies.

**Assessment:** Supported by the HTML standard, MDN, web.dev, WAI, and all requested tutorial sources.

**Evidence:** MDN Web Docs (supports); web.dev (supports)

### CLM-002 : `confirmed` (accessibility)

**Claim:** Native semantic landmarks improve page-region navigation for assistive-technology users.

**Assessment:** W3C WAI documents landmark navigation and test procedures.

**Evidence:** W3C WAI (supports)

### CLM-003 : `unverified` (seo)

**Claim:** Semantic HTML directly improves rankings.

**Assessment:** No supplied primary search-engine source establishes structural tags as independent ranking factors.

**Evidence:** Holistic SEO (asserts); Semrush (asserts); Google Search Central (does-not-confirm)

### CLM-004 : `unverified` (seo)

**Claim:** Search engines give keywords inside semantic elements more weight than keywords inside div elements.

**Assessment:** Webflow asserts this, but Google Search Central does not confirm a general keyword-weighting rule of this form.

**Evidence:** Webflow (asserts); Google Search Central (does-not-confirm)

### CLM-005 : `partly-supported` (performance)

**Claim:** Semantic HTML automatically makes pages lighter and faster.

**Assessment:** Replacing custom widgets or redundant wrappers may reduce code, but element choice alone does not guarantee fewer bytes or better performance.

**Evidence:** Webflow (asserts); WHATWG (qualifies)

### CLM-006 : `partly-supported` (seo)

**Claim:** Semantic HTML increases rich-result eligibility.

**Assessment:** Semantic structure may complement well-formed content, but Google rich results depend on supported structured data and feature-specific rules.

**Evidence:** Holistic SEO (asserts); Semrush (asserts); Google Search Central (qualifies)

### CLM-007 : `partly-supported` (seo)

**Claim:** Collapsed details content is indexable and therefore benefits SEO.

**Assessment:** The content remains in the DOM, but indexing, weighting, rendering, and query relevance are separate matters; no guaranteed benefit follows.

**Evidence:** Holistic SEO (asserts); Google Search Central (does-not-confirm)

### CLM-008 : `confirmed` (machine-interpretation)

**Claim:** Using article, section, nav, and main helps systems distinguish document roles.

**Assessment:** Their meanings and content models are defined by the HTML standard; web.dev explains automated-tool interpretation.

**Evidence:** web.dev (supports); WHATWG (supports)

### CLM-009 : `contradicted` (seo)

**Claim:** Semantic HTML replaces Schema.org structured data.

**Assessment:** Native HTML meaning and structured data vocabularies solve different layers of machine interpretation.

**Evidence:** Google Search Central (contradicts)

### CLM-010 : `confirmed` (engineering)

**Claim:** Correct semantic HTML improves maintainability.

**Assessment:** Meaningful elements expose intent without relying on private class names; requested developer sources consistently support this.

**Evidence:** Semrush (supports); Webflow (supports)

### CLM-011 : `unverified` (seo)

**Claim:** Wrapping navigation links in a nav element causes search engines to weight or value those links differently than links in a generic container.

**Assessment:** Holisticseo.digital asserts nav wrapping affects link weighting; Google's public guidance ties link value to the link graph, anchor text, and page authority rather than the semantic wrapper element, so this is not confirmed as an independent ranking factor.

**Evidence:** Holistic SEO (asserts); Google Search Central (does-not-confirm)

### CLM-012 : `partly-supported` (seo)

**Claim:** The figcaption element helps search engines index and understand the image or figure it describes.

**Assessment:** Figcaption text is genuine crawlable, contextual text adjacent to the image, which plausibly supports topical relevance; Google's image SEO guidance names alt text, filenames, and surrounding page context as documented signals and does not single out figcaption as a distinct ranking input.

**Evidence:** Holistic SEO (asserts); Google Search Central (qualifies)

## 3. Accessibility Tree and Browser-Computed Semantics

Semantic HTML describes author intent. The browser combines that HTML with ARIA, CSS visibility, rendered state, and JavaScript changes to produce an accessibility tree for platform accessibility APIs and assistive technologies.

```text
HTML and rendered DOM
+ native element semantics
+ ARIA roles, names, states, and relationships
+ hidden, inert, and visibility state
+ JavaScript-driven changes
                ↓
Browser accessibility tree
                ↓
Platform accessibility API
                ↓
Screen reader, voice control, switch access, and other assistive technology
```

The accessibility tree is not a copy of the DOM. Styling wrappers may be ignored, while headings, landmarks, links, buttons, form controls, images, dialogs, lists, and live states produce meaningful accessibility objects.

### 3.1 Properties to validate

For each important rendered object, inspect the properties relevant to its purpose:

- **Role:** the object type exposed by the browser, such as link, button, heading, navigation, main, dialog, image, or textbox.
- **Accessible name:** the label used by assistive technology, calculated from host-language labels, text content, `alt`, `aria-labelledby`, `aria-label`, and other sources according to precedence rules.
- **Accessible description:** supporting text derived from `aria-describedby`, `aria-description`, or eligible host-language features.
- **State and value:** properties such as expanded, selected, checked, pressed, current, invalid, busy, disabled, modal, and current value.
- **Relationships:** labelled-by, described-by, controls, owns, active descendant, and table header relationships.
- **Exposure:** whether the node appears, is ignored, or is excluded from the accessibility tree.
- **Action and focus:** whether the node receives focus and performs the behavior expected from its role.

### 3.2 Source markup does not prove computed output

A correct-looking attribute does not prove the final accessible name, role, or state. Validation must inspect the browser-computed object.

```html
<button aria-label="Submit form">Send</button>
```

This markup may expose a button named “Submit form” while the visible label is “Send.” The mismatch needs review because users of speech input or screen readers may encounter a different label from the one shown visually.

Likewise, the presence of `aria-label`, `aria-labelledby`, `alt`, or `<label>` does not prove that the referenced value is valid, unique, visible, or selected by the name-computation algorithm.

### 3.3 Navigation links and action buttons

Use a link with `href` when the control opens another URL or document location. Use a button when the control performs an action on the current page.

```html
<a href="/service-guide/">Read more about the service guide</a>
```

```html
<button type="button" aria-expanded="false" aria-controls="service-details">
  Show more service details
</button>
```

A visual “Read More” object implemented as an input, div, span, heading, or anchor without `href` may expose the wrong role or no interactive role. Repeated generic labels should identify their destination or action. When a visible label exists, the computed accessible name should contain that visible wording.

### 3.4 Hidden and ignored content

Several mechanisms affect tree exposure differently:

- `hidden`, `display:none`, and `visibility:hidden` normally remove content from rendering and the accessibility tree.
- `aria-hidden="true"` removes an element and its descendants from the accessibility tree but does not remove keyboard focus by itself.
- `inert` removes a subtree from normal focus and interaction while inactive.
- Off-screen visually hidden text may remain available to assistive technology when it is not otherwise hidden.
- Decorative images with `alt=""` are normally omitted from meaningful image exposure.

A focusable descendant inside an `aria-hidden="true"` subtree is an error because keyboard focus may reach an object that assistive technology cannot perceive.

### 3.5 Dynamic state

Interactive components require before-and-after testing. Visual changes must stay synchronized with native or ARIA states.

Examples include:

- disclosure: `aria-expanded`
- tabs: `aria-selected`
- toggle buttons: `aria-pressed`
- form validation: `aria-invalid` and described error text
- dialogs: accessible name, modal state, focus entry, focus containment, and focus return
- carousels and menus: current item, control names, focus order, and hidden-slide exposure

A static DOM audit cannot confirm these transitions.

### 3.6 Reading and focus order

Compare four sequences at every relevant responsive breakpoint:

1. DOM source order
2. visual order
3. keyboard focus order
4. accessibility-tree reading order

CSS grid, flex ordering, absolute positioning, duplicated mobile/desktop components, and JavaScript portals may create conflicting sequences even when each individual element uses a semantic tag.

### 3.7 Evidence levels

Report findings according to the strongest evidence actually collected:

| Level | Evidence |
|---|---|
| `source` | Supplied HTML or page source |
| `rendered-dom` | Post-hydration DOM, computed style, visibility, and responsive source order |
| `computed-tree` | Browser-computed role, name, description, state, relationships, and ignored reason |
| `interaction` | Focus, keyboard command, activation result, and state transition |
| `manual-at` | Selected assistive-technology verification for a critical user path |

Do not describe a computed role, ignored-node reason, state transition, or screen-reader announcement as verified when the relevant evidence was not collected.

### 3.8 Chrome DevTools workflow

1. Load the final rendered page.
2. Open Chrome DevTools and the Elements panel.
3. Enable the full accessibility tree.
4. Review page-level landmarks and headings.
5. Select each important node and inspect computed properties.
6. Review ignored nodes and their reasons.
7. Compare visible labels with computed names.
8. Test responsive source order.
9. Operate dynamic components and confirm state updates.
10. Finish with keyboard and selected assistive-technology checks for critical paths.

DevTools helps inspect markup exposure. It does not replace manual keyboard or assistive-technology testing.

## 4. Element-by-Element Reference

38 elements, grouped by function. Every entry answers the same four questions: what it's for, what non-semantic pattern it replaces, why that replacement is a real improvement (not just a rename), and what is/isn't confirmed about its SEO effect.

### Top-Level Landmarks

_Elements that define the major navigable regions of a page. Assistive tech exposes these directly in a landmark-navigation menu._

#### `<main>`

- **Purpose:** The dominant content of the document body, excluding repeated site-wide material.
- **Common use cases:** Primary article; product detail; service page content; application workspace.
- **Traditional pattern it replaces:** `div id="main"`
- **Why it's better:** Creates a native main landmark without role="main".
- **Accessibility effect:** Provides a direct destination for landmark navigation and skip links.
- **SEO effect:** Separates unique page content from repeated chrome; direct rank improvement is not documented.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Normally one visible main per document; do not nest in article, aside, footer, header, or nav.

```html
<main id="content"><h1>Page topic</h1></main>
```

#### `<search>`

- **Purpose:** A part of a document containing controls or content for performing a search or filtering operation.
- **Common use cases:** Site search; product filter controls; on-page search.
- **Traditional pattern it replaces:** `div class="search" role="search"`
- **Why it's better:** Provides native search landmark semantics without an ARIA role.
- **Accessibility effect:** Exposes a search landmark where supported.
- **SEO effect:** No direct SEO effect established; improves native meaning and accessibility.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use for search/filter functionality, not a section merely discussing search.

```html
<search><form><label for="q">Search</label><input id="q"></form></search>
```

### Page Sectioning

_Elements that carve a document into structural regions with their own outline context._

#### `<article>`

- **Purpose:** A self-contained composition intended to be independently reusable or distributable.
- **Common use cases:** Blog post; news story; forum post; product card with standalone identity; user comment.
- **Traditional pattern it replaces:** `div class="article"`
- **Why it's better:** Exposes independence as native document meaning instead of a private class convention.
- **Accessibility effect:** May create an article structure; headings help users identify the unit.
- **SEO effect:** Helps systems distinguish a standalone content unit; an isolated ranking boost is not documented.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use only when the content makes sense independently; nested articles should relate to the containing article.

```html
<article><h2>Guide title</h2><p>...</p></article>
```

#### `<footer>`

- **Purpose:** Footer information for its nearest sectioning ancestor or the page.
- **Common use cases:** Author details; copyright; related links; revision data.
- **Traditional pattern it replaces:** `div class="footer"`
- **Why it's better:** Associates closing metadata with the correct page or section.
- **Accessibility effect:** A body-level footer may map to contentinfo; nested footers generally do not.
- **SEO effect:** Helps classify supporting metadata; no isolated ranking benefit is confirmed.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** May appear more than once; its meaning is scoped to the nearest sectioning ancestor.

```html
<footer><small>Updated 2026-07-16</small></footer>
```

#### `<header>`

- **Purpose:** Introductory or navigational aids for a page or section.
- **Common use cases:** Site masthead; article title/byline group; section introduction.
- **Traditional pattern it replaces:** `div class="header"`
- **Why it's better:** Meaning depends on its nearest sectioning context and is not limited to the page top.
- **Accessibility effect:** A body-level header may map to banner; nested headers generally do not.
- **SEO effect:** Clarifies introductions and heading context; no isolated ranking benefit is confirmed.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** May appear several times; do not nest within header or footer, and observe content-model restrictions.

```html
<article><header><h1>Title</h1><p>Byline</p></header></article>
```

#### `<section>`

- **Purpose:** A generic thematic section of a document or application, usually identified by a heading.
- **Common use cases:** Chapters; grouped service details; report sections; tabbed thematic panels.
- **Traditional pattern it replaces:** `div class="section"`
- **Why it's better:** Makes thematic grouping explicit in the HTML vocabulary.
- **Accessibility effect:** A named section may expose a region; excessive unnamed sections create noise.
- **SEO effect:** Supports coherent content structure, but is not a keyword-weighting switch or confirmed ranking factor.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use article, nav, aside, or address when their narrower meaning applies; normally include a heading.

```html
<section><h2>Eligibility</h2><p>...</p></section>
```

### Sectioning Landmarks

_Sectioning elements that also register as ARIA landmarks, giving them a dual structural + navigational role._

#### `<aside>`

- **Purpose:** Content tangentially related to its surrounding content.
- **Common use cases:** Sidebar; related resources; pull quote; author note; advertising.
- **Traditional pattern it replaces:** `div class="sidebar"`
- **Why it's better:** Expresses complementary rather than primary relevance.
- **Accessibility effect:** Usually maps to a complementary landmark when context permits; repeated landmarks need names.
- **SEO effect:** May help separate supplementary material from main content; ranking effects are not documented.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Content must remain related yet non-essential to the surrounding flow.

```html
<aside aria-label="Related guides"><h2>Related guides</h2></aside>
```

#### `<nav>`

- **Purpose:** A section whose purpose is major navigation.
- **Common use cases:** Primary menu; breadcrumbs container; table of contents; pagination or major index.
- **Traditional pattern it replaces:** `div id="nav"`
- **Why it's better:** Creates native navigation meaning and normally an accessibility landmark.
- **Accessibility effect:** Screen-reader users may jump to it; multiple nav landmarks need distinct names.
- **SEO effect:** Clarifies navigational blocks and link context; no confirmed special PageRank weighting follows merely from the tag.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Not every link group belongs in nav. Label repeated navigation landmarks.

```html
<nav aria-label="Primary"><ul><li><a href="/">Home</a></li></ul></nav>
```

### Sectioning : Contact / Text Blocks

_Narrow-purpose sectioning elements for a specific kind of content block._

#### `<address>`

- **Purpose:** Contact information for the nearest article or document body.
- **Common use cases:** Author email; organization contact link; page-owner contact details.
- **Traditional pattern it replaces:** `div class="contact"`
- **Why it's better:** Associates contact data with its responsible author or organization.
- **Accessibility effect:** Supplies semantic contact context but does not replace accessible labels or structured data.
- **SEO effect:** May clarify authorship/contact context; does not replace Organization/Person structured data.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Do not use for arbitrary postal addresses unrelated to the author/owner.

```html
<address>Contact <a href="mailto:editor@example.com">the editor</a></address>
```

### Headings

_Elements that define the document/section outline and its hierarchy._

#### `<h1-h6>`

- **Purpose:** Headings that identify sections and communicate rank.
- **Common use cases:** Page title; major section; nested subsection.
- **Traditional pattern it replaces:** `styled div or p`
- **Why it's better:** Creates a programmatic heading hierarchy independent of visual styling.
- **Accessibility effect:** Screen-reader users navigate and scan by headings.
- **SEO effect:** Google documents headings as useful signals for understanding page structure and title-link context, but mechanical level rules do not guarantee rank.
  **Confirmed** : directly supported by the HTML/ARIA specification or first-party engine documentation.
- **Constraints:** Choose levels by hierarchy, not font size; do not leave headings empty.

```html
<h1>Primary topic</h1><h2>Subtopic</h2>
```

### Grouping Content

_Elements that group related flow content without necessarily creating a new landmark or outline entry._

#### `<figcaption>`

- **Purpose:** Caption or legend for its parent figure.
- **Common use cases:** Chart caption; image explanation; code-sample label.
- **Traditional pattern it replaces:** `p class="caption"`
- **Why it's better:** Creates a native relationship to the entire figure.
- **Accessibility effect:** Adds visible context but is not a substitute for image alternative text.
- **SEO effect:** Provides nearby descriptive context that search systems may process; no ranking guarantee.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Must be inside figure and should be first or last child.

```html
<figure><figcaption>Map of service areas</figcaption><img src="map.png" alt="..."></figure>
```

#### `<figure>`

- **Purpose:** Self-contained content referenced as a unit, optionally with a caption.
- **Common use cases:** Image; diagram; chart; code listing; quotation; data table.
- **Traditional pattern it replaces:** `div class="figure"`
- **Why it's better:** Groups the asset and its caption as one semantic unit.
- **Accessibility effect:** Provides structural association; image alt text remains independently required when applicable.
- **SEO effect:** Improves media-context organization; figure alone does not guarantee image-search gains.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Figcaption, when present, must be the first or last child.

```html
<figure><img src="chart.png" alt="Sales rose"><figcaption>Quarterly sales</figcaption></figure>
```

#### `<p>`

- **Purpose:** A paragraph of text.
- **Common use cases:** Explanatory prose; answer text; description.
- **Traditional pattern it replaces:** `div with text and line breaks`
- **Why it's better:** Exposes paragraph boundaries rather than visual spacing only.
- **Accessibility effect:** Supports coherent reading units.
- **SEO effect:** No independent ranking effect; correct text structure improves parsing and maintenance.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Do not place flow-content blocks inside p.

```html
<p>A complete paragraph.</p>
```

#### `<pre>`

- **Purpose:** Preserves whitespace and line breaks exactly as authored, for content where formatting is part of the meaning.
- **Common use cases:** Code snippets (paired with code), ASCII art, terminal or console output.
- **Traditional pattern it replaces:** `div styled with white-space:pre-wrap and manual br tags`
- **Why it's better:** Whitespace preservation is a guaranteed content-level behavior, not a styling choice that silently breaks if CSS fails to load.
- **Accessibility effect:** Screen readers can read preserved line breaks and spacing; pairing pre with code clarifies that the content is source code rather than prose.
- **SEO effect:** No independent ranking effect; correctly marked-up code samples stay crawlable as real text instead of being rendered only through CSS or canvas tricks.
  **Unverified** : commonly claimed by secondary sources but not established by any primary source reviewed.
- **Constraints:** Pair with code for source code; content inside is whitespace-significant.

```html
<pre><code>function greet() { return "hi"; }</code></pre>
```

### Lists : Containers

_Elements that hold a set of related items as a single structure._

#### `<dl>`

- **Purpose:** An association list made of term/name groups and their descriptions/values.
- **Common use cases:** Glossary; metadata; specifications; question-answer pairs where term-description semantics fit.
- **Traditional pattern it replaces:** `two-column div grid`
- **Why it's better:** Creates explicit term-description relationships.
- **Accessibility effect:** Assistive support varies in announcement detail but relationships remain native HTML.
- **SEO effect:** No direct ranking effect; improves machine-readable association.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use dt and dd groups; not merely for visual indentation.

```html
<dl><dt>License</dt><dd>CFC...</dd></dl>
```

#### `<ol>`

- **Purpose:** An ordered list whose sequence matters.
- **Common use cases:** Instructions; rankings; legal steps; chronology.
- **Traditional pattern it replaces:** `numbered div rows`
- **Why it's better:** Exposes order and list-item relationships.
- **Accessibility effect:** Screen readers announce ordered-list structure and count.
- **SEO effect:** No direct ranking boost; clarifies procedural or ranked relationships.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use reversed, start, and value only when their numeric meaning is intended.

```html
<ol><li>Inspect</li><li>Repair</li></ol>
```

#### `<ul>`

- **Purpose:** An unordered list of items.
- **Common use cases:** Feature list; related resources; non-sequential steps.
- **Traditional pattern it replaces:** `div rows with bullets added by CSS`
- **Why it's better:** Exposes list membership and item count.
- **Accessibility effect:** Screen readers announce list structure.
- **SEO effect:** No direct ranking boost; makes enumerated content explicit.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Children are li elements, apart from script-supporting elements.

```html
<ul><li>Repair</li><li>Installation</li></ul>
```

### Lists : Items

_The individual entries inside a list container._

#### `<li>`

- **Purpose:** Represents one item within an ordered, unordered, or menu list.
- **Common use cases:** Navigation links, numbered steps, product feature lists, search result entries.
- **Traditional pattern it replaces:** `div per row inside a div acting as a fake list`
- **Why it's better:** Only valid as a child of ul, ol, or menu, so the browser exposes real list semantics (item count and position) that a div-per-row structure cannot.
- **Accessibility effect:** Announced by screen readers with position and set size (for example "item 2 of 5") only when correctly nested inside ul or ol.
- **SEO effect:** No independent ranking effect; correctly marked-up list items make enumerable content (steps, features) easier for automated systems to extract for rich results.
  **Unverified** : commonly claimed by secondary sources but not established by any primary source reviewed.
- **Constraints:** Must be a direct child of ul, ol, or menu; not valid on its own.

```html
<ul><li>Step one</li><li>Step two</li></ul>
```

### Quotations

_Elements that mark quoted material as quoted, rather than visually italicised text._

#### `<blockquote>`

- **Purpose:** A section quoted from another source.
- **Common use cases:** Long testimonial excerpt; cited passage.
- **Traditional pattern it replaces:** `indented div`
- **Why it's better:** Marks quotation semantics without relying on indentation.
- **Accessibility effect:** Conveys quoted-block meaning.
- **SEO effect:** No direct rank effect; cite attribute is not normally displayed and does not replace a visible source link.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use cite attribute only for a source URL; add visible attribution separately.

```html
<blockquote cite="https://example.com/source"><p>Quoted text.</p></blockquote>
```

#### `<q>`

- **Purpose:** A short inline quotation.
- **Common use cases:** Quoted phrase inside a sentence.
- **Traditional pattern it replaces:** `span with typed quotation marks`
- **Why it's better:** Marks the phrase as quoted while user agents handle punctuation.
- **Accessibility effect:** Conveys inline quotation semantics.
- **SEO effect:** No direct SEO effect.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Do not add quotation marks solely through text when q supplies them; cite may hold a source URL.

```html
<p>The report calls it <q>effective</q>.</p>
```

### Text-Level (Inline) Semantics

_Elements that attach meaning to a run of text inside a block, rather than styling it directly._

#### `<abbr>`

- **Purpose:** An abbreviation or acronym, optionally with its expansion.
- **Common use cases:** Technical acronym; shortened organization name.
- **Traditional pattern it replaces:** `span title="..."`
- **Why it's better:** Marks abbreviated text and may provide its expansion.
- **Accessibility effect:** Title-only expansions are not reliably accessible; provide visible expansion when important.
- **SEO effect:** May clarify language processing, but no direct ranking boost is documented.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Do not rely solely on title for essential information.

```html
<abbr title="Search Engine Optimization">SEO</abbr>
```

#### `<cite>`

- **Purpose:** The title of a creative work.
- **Common use cases:** Book; article; film; research paper title.
- **Traditional pattern it replaces:** `italic span`
- **Why it's better:** Identifies a work title rather than merely styling text.
- **Accessibility effect:** Conveys work-title meaning; default italics are presentation only.
- **SEO effect:** No direct SEO effect.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Not intended for a person name under the HTML standard.

```html
<cite>HTML Living Standard</cite>
```

#### `<code>`

- **Purpose:** A fragment of computer code.
- **Common use cases:** HTML tag; command; function name.
- **Traditional pattern it replaces:** `monospace span`
- **Why it's better:** Identifies code independent of font choice.
- **Accessibility effect:** Screen readers may not announce punctuation adequately; explanatory prose may still be needed.
- **SEO effect:** No direct SEO effect.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use pre with code for preformatted blocks.

```html
<code>&lt;main&gt;</code>
```

#### `<data>`

- **Purpose:** Human-readable content paired with a machine-readable value.
- **Common use cases:** Product identifier; internal code; machine value for a label.
- **Traditional pattern it replaces:** `span data-value="..."`
- **Why it's better:** Uses a standard value attribute for machine-readable equivalence.
- **Accessibility effect:** Limited direct accessibility effect; visible label remains necessary.
- **SEO effect:** No direct SEO effect; does not replace structured data vocabulary.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use time instead when the value is a date or time.

```html
<data value="SKU-42">Blue model</data>
```

#### `<dfn>`

- **Purpose:** The defining instance of a term.
- **Common use cases:** Glossary definition; first formal definition.
- **Traditional pattern it replaces:** `bold or italic span`
- **Why it's better:** Identifies where a term is being defined.
- **Accessibility effect:** Provides semantic definition context.
- **SEO effect:** No direct SEO effect established.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** The nearest paragraph, dt/dd group, or section should contain the definition.

```html
<p><dfn>Semantic HTML</dfn> is meaning-based markup.</p>
```

#### `<em>`

- **Purpose:** Stress emphasis that changes sentence meaning.
- **Common use cases:** Contrastive stress; verbal emphasis.
- **Traditional pattern it replaces:** `i or italic span`
- **Why it's better:** Encodes stress rather than appearance.
- **Accessibility effect:** May alter spoken emphasis depending on assistive technology.
- **SEO effect:** No proven keyword-weighting benefit.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use CSS for italics without stress; nesting increases emphasis level.

```html
<p>You must submit it <em>today</em>.</p>
```

#### `<mark>`

- **Purpose:** Text marked as relevant in the current context.
- **Common use cases:** Search-result match; referenced passage; review highlight.
- **Traditional pattern it replaces:** `span class="highlight"`
- **Why it's better:** Encodes contextual relevance rather than yellow background.
- **Accessibility effect:** Color alone must not be the sole cue; announcement support varies.
- **SEO effect:** No direct ranking effect; it is not an SEO keyword-highlighting mechanism.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Do not use merely for decorative highlighting or general importance.

```html
<p>Match: <mark>semantic HTML</mark></p>
```

#### `<strong>`

- **Purpose:** Strong importance, seriousness, or urgency.
- **Common use cases:** Warning; critical instruction; important phrase.
- **Traditional pattern it replaces:** `b or bold span`
- **Why it's better:** Encodes importance rather than appearance.
- **Accessibility effect:** May expose importance, though screen-reader voicing varies.
- **SEO effect:** No proven keyword-weighting benefit.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use b or CSS when only visual offset is intended.

```html
<strong>Shut off the water first.</strong>
```

#### `<time>`

- **Purpose:** A machine-readable date, time, time-zone offset, or duration.
- **Common use cases:** Publication date; event time; opening duration.
- **Traditional pattern it replaces:** `span class="date"`
- **Why it's better:** The datetime attribute disambiguates human date formats.
- **Accessibility effect:** Supports unambiguous programmatic interpretation.
- **SEO effect:** May help systems parse dates, but does not replace structured data required for search features.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** datetime must use a valid HTML date/time or duration syntax.

```html
<time datetime="2026-07-16">16 July 2026</time>
```

### Links

_The core interactive element for navigating between resources._

#### `<a>`

- **Purpose:** A hyperlink to a URL or document location.
- **Common use cases:** Internal link; external citation; email or telephone link.
- **Traditional pattern it replaces:** `clickable div`
- **Why it's better:** Creates native link semantics, focus behavior, URL handling, and crawlable relationships when href is present.
- **Accessibility effect:** Keyboard and screen-reader link navigation work natively.
- **SEO effect:** Google explicitly uses crawlable links and anchor text to discover pages and understand linked content.
  **Confirmed** : directly supported by the HTML/ARIA specification or first-party engine documentation.
- **Constraints:** Use href for hyperlinks; buttons are for actions that do not navigate.

```html
<a href="/semantic-html">Semantic HTML guide</a>
```

### Forms : Structure

_Elements that structure a submittable group of controls._

#### `<form>`

- **Purpose:** Groups interactive controls into a single submittable unit tied to one user action.
- **Common use cases:** Search boxes, sign-up and login forms, checkout flows, contact forms, on-page filters.
- **Traditional pattern it replaces:** `div wrapper with a JS click handler simulating submission`
- **Why it's better:** Provides native submission, keyboard Enter-to-submit, and built-in validation; only exposes a form or search landmark role when it has an accessible name.
- **Accessibility effect:** Exposed as a form (or search) landmark to assistive tech only when labelled with aria-label or aria-labelledby; unlabelled forms are not distinguishable from each other in landmark navigation.
- **SEO effect:** No direct ranking effect; a labelled form clarifies page purpose (e.g. distinguishing a search form from a contact form) for automated interpretation.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Needs an accessible name to register as a landmark (SEM-006); avoid nesting one form inside another.

```html
<form role="search"><label for="q">Search</label><input id="q" name="q" type="search"></form>
```

#### `<label>`

- **Purpose:** A caption associated with a form control.
- **Common use cases:** Input name; checkbox label; select label.
- **Traditional pattern it replaces:** `adjacent span`
- **Why it's better:** Creates a programmatic name relationship and a larger activation target.
- **Accessibility effect:** Essential for control identification and speech/assistive input.
- **SEO effect:** No direct SEO effect.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Associate with for/id or by nesting; placeholder is not a label replacement.

```html
<label for="email">Email</label><input id="email" type="email">
```

### Forms : Interactive Controls

_Native interactive controls with built-in keyboard, focus, and activation behaviour._

#### `<button>`

- **Purpose:** An actionable button.
- **Common use cases:** Submit; expand; open dialog; run command.
- **Traditional pattern it replaces:** `div or span with click handler`
- **Why it's better:** Provides keyboard activation, focusability, role, disabled state, and form behavior natively.
- **Accessibility effect:** Major accessibility gain over scripted generic containers.
- **SEO effect:** No direct ranking effect; improves usable interaction and crawl-independent page quality.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Set type explicitly in forms; give an accessible name.

```html
<button type="button">Open filters</button>
```

### Interactive Disclosure Widgets

_Elements that provide native show/hide interactivity without custom JavaScript._

#### `<details>`

- **Purpose:** Native disclosure widget whose additional content may be expanded or collapsed.
- **Common use cases:** FAQ answer; specifications; optional explanation; disclosure panel.
- **Traditional pattern it replaces:** `div plus JavaScript accordion`
- **Why it's better:** Supplies built-in state, activation, and keyboard behavior with less custom scripting.
- **Accessibility effect:** Native disclosure semantics and focus behavior reduce custom-widget failure risk.
- **SEO effect:** Collapsed content remains in the DOM; indexing or ranking treatment is not guaranteed by the element.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Use summary as the label; test browser and assistive-technology behavior.

```html
<details><summary>Warranty</summary><p>Coverage details...</p></details>
```

#### `<dialog>`

- **Purpose:** A dialog box or other interactive component presented over or apart from the page flow.
- **Common use cases:** Modal confirmation; settings panel; non-modal dialog.
- **Traditional pattern it replaces:** `div role="dialog" plus custom scripting`
- **Why it's better:** Native dialog API supports modal display and focus-management primitives.
- **Accessibility effect:** Correct use improves focus containment and dialog announcement; accessible naming remains required.
- **SEO effect:** No direct SEO benefit; hidden modal content should not carry essential primary-page information.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Supply an accessible name; use showModal() for modal behavior; do not misuse for ordinary layout.

```html
<dialog aria-labelledby="d-title"><h2 id="d-title">Confirm</h2></dialog>
```

#### `<summary>`

- **Purpose:** Visible label and activation control for a parent details element.
- **Common use cases:** FAQ question; disclosure title.
- **Traditional pattern it replaces:** `div class="accordion-title"`
- **Why it's better:** Creates the native interactive label for details.
- **Accessibility effect:** Keyboard-operable control semantics are supplied by the browser.
- **SEO effect:** No direct SEO effect established.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Must be the first summary child of details to act as its summary.

```html
<details><summary>What is covered?</summary><p>...</p></details>
```

### Tabular Data

_Elements for representing genuinely tabular (row/column) data._

#### `<table>`

- **Purpose:** Data with relationships across rows and columns.
- **Common use cases:** Pricing matrix; specifications; comparison; report data.
- **Traditional pattern it replaces:** `CSS grid or nested divs`
- **Why it's better:** Creates native row, column, header, caption, and cell relationships.
- **Accessibility effect:** Correct th/scope/caption markup supports table navigation and comprehension.
- **SEO effect:** May clarify data relationships; no rich-result eligibility follows from table markup alone.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Do not use for page layout. Use caption and header cells where needed.

```html
<table><caption>Plans</caption><tr><th>Plan</th><th>Price</th></tr></table>
```

### Embedded Content

_Elements that embed an external resource into the document._

#### `<img>`

- **Purpose:** Embeds an image and, through the alt attribute, supplies a text alternative that stands in for the image's meaning.
- **Common use cases:** Product photography, illustrative diagrams and charts, logos, purely decorative graphics (alt="").
- **Traditional pattern it replaces:** `CSS background-image applied to a div`
- **Why it's better:** alt text is exposed to screen readers and image-search crawlers; a CSS background-image carries no accessible name or indexable text alternative.
- **Accessibility effect:** alt is the image's accessible name; an empty alt="" correctly hides purely decorative images from assistive technology instead of announcing a meaningless filename.
- **SEO effect:** alt text is a confirmed input to Google Image Search relevance and a documented accessibility requirement; it is not established as a general web-ranking factor on its own.
  **Supported (indirect)** : plausible and consistent with how engines/assistive tech are documented to work, but not a named, isolated ranking factor.
- **Constraints:** Always set alt (empty string for decorative images); do not keyword-stuff alt text.

```html
<img src="chart.png" alt="Quarterly revenue grew 12% year over year">
```

## 5. Audit Rulebook

22 rules for auditing semantic HTML, rendered DOM structure, browser-computed accessibility output, and critical interaction behavior. Each rule maps to rows in `audit_rules`; running an audit means inserting a row into `audit_runs`, one row per URL into `audited_pages`, then one `findings` row per (page, rule) pair : see Section 6.

| Rule | Name | Severity | Applies to |
|---|---|---|---|
| SEM-001 | Exactly one visible main landmark | error | main |
| SEM-002 | Main has valid ancestry | error | main |
| SEM-003 | Sections are named | warning | section |
| SEM-004 | Articles stand independently | warning | article |
| SEM-005 | Nav is reserved for major navigation | warning | nav |
| SEM-006 | Repeated landmarks have distinct names | error | nav, aside, form/search, region |
| SEM-007 | Headings encode hierarchy | warning | h1-h6 |
| SEM-008 | Figure captions are structurally associated | warning | figure, figcaption |
| SEM-009 | Dates use valid datetime values | warning | time |
| SEM-010 | Disclosure widgets use details and summary correctly | warning | details, summary |
| SEM-011 | Native interactive elements are used | error | interactive controls |
| SEM-012 | Tables represent data, not layout | error | table |
| SEM-013 | Semantic choice follows meaning | warning | all |
| SEM-014 | ARIA does not conflict with native semantics | error | all semantic elements |
| SEM-015 | Rendered DOM preserves semantic structure | warning | client-rendered pages |
| SEM-016 | Computed role matches intended purpose | error | landmarks, controls, images, widgets, and structural elements |
| SEM-017 | Accessible name and description resolve correctly | error | controls, landmarks, images, dialogs, frames, and form fields |
| SEM-018 | Hidden and ignored-node exposure is intentional | error | hidden, collapsed, off-canvas, inactive, and decorative content |
| SEM-019 | Dynamic states remain synchronized | error | accordions, tabs, menus, dialogs, carousels, forms, and custom widgets |
| SEM-020 | Focus, keyboard behavior, and exposed action agree | error | interactive controls |
| SEM-021 | DOM, visual, focus, and accessibility order remain logical | warning | grids, split layouts, responsive sections, and reordered components |
| SEM-022 | Critical paths receive manual accessibility verification | warning | page-level validation and key user journeys |

#### SEM-001 : Exactly one visible main landmark (`error`)
- **Applies to:** main
- **Test method:** DOM query plus visibility check
- **Pass condition:** One non-hidden main contains the page-specific primary content.
- **Failure reason:** Missing or duplicate main landmarks obscure the dominant content region.
- **Remediation:** Add one main around unique content; remove, hide correctly, or refactor duplicates.

#### SEM-002 : Main has valid ancestry (`error`)
- **Applies to:** main
- **Test method:** Check ancestors
- **Pass condition:** Main is not descended from article, aside, footer, header, or nav.
- **Failure reason:** The structure violates main content-model constraints.
- **Remediation:** Move main to the document body level outside those elements.

#### SEM-003 : Sections are named (`warning`)
- **Applies to:** section
- **Test method:** Find heading or accessible name
- **Pass condition:** Each meaningful section has a heading, or a justified accessible label.
- **Failure reason:** An unnamed section may add no useful structure and may produce an unnamed region.
- **Remediation:** Add a descriptive heading or use div when no thematic section exists.

#### SEM-004 : Articles stand independently (`warning`)
- **Applies to:** article
- **Test method:** Editorial review
- **Pass condition:** Each article is intelligible and reusable outside the immediate page.
- **Failure reason:** A layout wrapper has been mislabeled as independent content.
- **Remediation:** Use section or div unless the block is a standalone composition.

#### SEM-005 : Nav is reserved for major navigation (`warning`)
- **Applies to:** nav
- **Test method:** Editorial and link-block review
- **Pass condition:** Each nav represents a major navigation block.
- **Failure reason:** Too many nav landmarks reduce navigational value.
- **Remediation:** Use ordinary containers for minor link groups.

#### SEM-006 : Repeated landmarks have distinct names (`error`)
- **Applies to:** nav, aside, form/search, region
- **Test method:** Full accessibility-tree and computed-name inspection
- **Pass condition:** Landmarks of the same type have unique browser-computed accessible names when distinction is required.
- **Failure reason:** Users cannot distinguish repeated landmarks in landmark navigation.
- **Remediation:** Use aria-labelledby with a visible heading or a concise aria-label; verify the computed name rather than the attribute alone.

#### SEM-007 : Headings encode hierarchy (`warning`)
- **Applies to:** h1-h6
- **Test method:** Heading-tree review
- **Pass condition:** Headings identify content sections and levels follow nesting intent.
- **Failure reason:** Styling-driven headings distort programmatic structure.
- **Remediation:** Select levels for hierarchy and use CSS for size.

#### SEM-008 : Figure captions are structurally associated (`warning`)
- **Applies to:** figure, figcaption
- **Test method:** DOM child-order check
- **Pass condition:** Figcaption is the first or last child of figure.
- **Failure reason:** Caption meaning may not be associated as intended.
- **Remediation:** Move figcaption inside figure at the first or last position.

#### SEM-009 : Dates use valid datetime values (`warning`)
- **Applies to:** time
- **Test method:** Attribute syntax validation
- **Pass condition:** Datetime is absent only when text is machine-readable, or contains a valid HTML date/time/duration.
- **Failure reason:** Ambiguous or invalid values defeat machine readability.
- **Remediation:** Add a valid datetime value while keeping human-readable text.

#### SEM-010 : Disclosure widgets use details and summary correctly (`warning`)
- **Applies to:** details, summary
- **Test method:** DOM and keyboard test
- **Pass condition:** Each details begins with a usable summary and works with keyboard input.
- **Failure reason:** The disclosure lacks a native name or interaction behavior.
- **Remediation:** Add summary as the first child or implement an accessible custom pattern only when necessary.

#### SEM-011 : Native interactive elements are used (`error`)
- **Applies to:** interactive controls
- **Test method:** DOM, computed accessibility tree, focus, keyboard, and activation test
- **Pass condition:** Links navigate; buttons perform actions; native controls expose the expected role, name, focus behavior, keyboard behavior, and state.
- **Failure reason:** Generic containers or mismatched controls lack dependable role, keyboard, focus, state, or action behavior.
- **Remediation:** Replace the control with the matching native element; preserve a useful computed name and verify interaction behavior.

#### SEM-012 : Tables represent data, not layout (`error`)
- **Applies to:** table
- **Test method:** Content and header association review
- **Pass condition:** Every table represents row-column data and uses caption/th associations as needed.
- **Failure reason:** Layout tables create misleading navigation and relationships.
- **Remediation:** Use CSS layout for presentation; repair data-table headers and caption.

#### SEM-013 : Semantic choice follows meaning (`warning`)
- **Applies to:** all
- **Test method:** DOM and CSS review
- **Pass condition:** Elements are chosen for purpose; CSS supplies presentation.
- **Failure reason:** Appearance-driven element choice corrupts document meaning.
- **Remediation:** Replace misused elements and preserve visuals through CSS.

#### SEM-014 : ARIA does not conflict with native semantics (`error`)
- **Applies to:** all semantic elements
- **Test method:** Compare native semantics, ARIA attributes, and browser-computed role/state
- **Pass condition:** ARIA supplements native semantics without changing the computed role or state to an inaccurate value.
- **Failure reason:** Redundant or conflicting ARIA produces an inaccurate accessibility object.
- **Remediation:** Remove redundant or conflicting ARIA, prefer native HTML, and recheck the computed accessibility node.

#### SEM-015 : Rendered DOM preserves semantic structure (`warning`)
- **Applies to:** client-rendered pages
- **Test method:** Compare initial HTML, rendered DOM, full accessibility tree, and responsive source order
- **Pass condition:** Rendering does not remove, duplicate, hide, or reorder essential headings, landmarks, controls, names, states, and content relationships.
- **Failure reason:** Users, assistive technologies, and crawlers may receive inconsistent structures or interaction states.
- **Remediation:** Correct templates, hydration, CSS ordering, or component state; retest the rendered DOM and full accessibility tree.

#### SEM-016 : Computed role matches intended purpose (`error`)
- **Applies to:** landmarks, controls, images, widgets, and structural elements
- **Test method:** Full accessibility-tree and computed-role inspection
- **Pass condition:** The browser-computed role matches the element purpose and expected interaction.
- **Failure reason:** Native or ARIA semantics expose the wrong object type.
- **Remediation:** Use the correct native element or remove the conflicting role; recheck the computed node.

#### SEM-017 : Accessible name and description resolve correctly (`error`)
- **Applies to:** controls, landmarks, images, dialogs, frames, and form fields
- **Test method:** Computed name and description inspection plus visible-label comparison
- **Pass condition:** Required objects have accurate, non-empty, non-conflicting names; the computed name contains the visible control wording where a visible label exists.
- **Failure reason:** A name or description is absent, duplicated, misleading, or disconnected from the visible label or purpose.
- **Remediation:** Repair label, alt, aria-labelledby, aria-label, aria-describedby, or host-language naming relationships; verify computed output.

#### SEM-018 : Hidden and ignored-node exposure is intentional (`error`)
- **Applies to:** hidden, collapsed, off-canvas, inactive, and decorative content
- **Test method:** Compare rendered visibility, focusability, DOM state, and accessibility-tree exposure
- **Pass condition:** Hidden or inactive content is excluded as intended; visible meaningful content remains exposed; excluded subtrees contain no focusable descendants.
- **Failure reason:** Meaningful content is ignored, or a focusable object remains inside an excluded subtree.
- **Remediation:** Repair hidden, inert, aria-hidden, CSS visibility, or focus handling and inspect the ignored-node reason.

#### SEM-019 : Dynamic states remain synchronized (`error`)
- **Applies to:** accordions, tabs, menus, dialogs, carousels, forms, and custom widgets
- **Test method:** Interact with the component and compare visual state with computed accessibility state
- **Pass condition:** Expanded, selected, checked, pressed, current, invalid, busy, disabled, and modal states match the visible interface before and after interaction.
- **Failure reason:** The visual state changes without the corresponding native or ARIA state update.
- **Remediation:** Update the native state or correct ARIA property during the same interaction; retest every state transition.

#### SEM-020 : Focus, keyboard behavior, and exposed action agree (`error`)
- **Applies to:** interactive controls
- **Test method:** Computed role inspection plus Tab, Enter, Space, arrow-key, and Escape testing where relevant
- **Pass condition:** Role, focusability, keyboard command, state, and resulting action follow the native element or documented widget pattern.
- **Failure reason:** An element claims an interactive role without matching focus or keyboard behavior, or navigation and action semantics are confused.
- **Remediation:** Use a native link for navigation and a native button for actions; implement the complete keyboard pattern only when a custom widget is unavoidable.

#### SEM-021 : DOM, visual, focus, and accessibility order remain logical (`warning`)
- **Applies to:** grids, split layouts, responsive sections, and reordered components
- **Test method:** Compare DOM order, visual order, keyboard focus order, and full accessibility-tree order at each relevant breakpoint
- **Pass condition:** Reading and focus sequences remain meaningful and equivalent enough to preserve relationships at each tested viewport.
- **Failure reason:** CSS or JavaScript reordering creates conflicting visual, reading, or focus sequences.
- **Remediation:** Correct source order first and use layout CSS without changing the meaningful sequence.

#### SEM-022 : Critical paths receive manual accessibility verification (`warning`)
- **Applies to:** page-level validation and key user journeys
- **Test method:** DevTools tree review, keyboard test, and selected assistive-technology spot check
- **Pass condition:** Critical navigation, forms, disclosures, dialogs, and conversion actions work beyond static markup and automated checks.
- **Failure reason:** Approval relies only on source markup, a crawler, Lighthouse, or the DevTools tree.
- **Remediation:** Complete keyboard testing and a relevant browser and assistive-technology spot check; record the environment and result.

## 6. Sources

| ID | Publisher | Class | Accessed | URL |
|---|---|---|---|---|
| SRC-GOOGLE | Google Search Central | authoritative-guidance | 2026-07-16 | https://developers.google.com/search/docs/fundamentals/seo-starter-guide |
| SRC-MDN | MDN Web Docs | authoritative-guidance | 2026-07-16 | https://developer.mozilla.org/en-US/docs/Glossary/Semantics |
| SRC-WAI-H101 | W3C WAI | authoritative-guidance | 2026-07-16 | https://www.w3.org/WAI/WCAG21/Techniques/html/H101 |
| SRC-WEBDEV | web.dev | authoritative-guidance | 2026-07-16 | https://web.dev/learn/html/semantic-html |
| SRC-WHATWG | WHATWG | normative | 2026-07-16 | https://html.spec.whatwg.org/multipage/ |
| SRC-HOLISTIC | Holistic SEO | secondary | 2026-07-16 | https://www.holisticseo.digital/technical-seo/html/style-and-semantic-tag/ |
| SRC-SEMRUSH | Semrush | secondary | 2026-07-16 | https://www.semrush.com/blog/semantic-html5-guide/ |
| SRC-W3S | W3Schools | secondary | 2026-07-16 | https://www.w3schools.com/html/html5_semantic_elements.asp |
| SRC-WEBFLOW | Webflow | secondary | 2026-07-16 | https://help.webflow.com/hc/en-us/articles/33961369965715-Semantic-HTML5-tags |
| SRC-CHROME-AXTREE | Chrome for Developers | authoritative-guidance | 2026-07-27 | https://developer.chrome.com/blog/full-accessibility-tree |
| SRC-CHROME-A11Y-REF | Chrome for Developers | authoritative-guidance | 2026-07-27 | https://developer.chrome.com/docs/devtools/accessibility/reference |
| SRC-HTML-AAM | W3C | normative-draft | 2026-07-27 | https://www.w3.org/TR/html-aam-1.0/ |
| SRC-ACCNAME | W3C | normative-draft | 2026-07-27 | https://www.w3.org/TR/accname-1.2/ |
| SRC-CORE-AAM | W3C | normative-draft | 2026-07-27 | https://www.w3.org/TR/core-aam-1.2/ |
| SRC-WAI-ARIA | W3C | normative | 2026-07-27 | https://www.w3.org/TR/wai-aria/ |
| SRC-WAI-EVALUATION | W3C WAI | authoritative-guidance | 2026-07-27 | https://www.w3.org/WAI/test-evaluate/ |
| SRC-WAI-EASY-CHECKS | W3C WAI | authoritative-guidance | 2026-07-27 | https://www.w3.org/WAI/test-evaluate/preliminary/ |
| SRC-MDN-ARIA-HIDDEN | MDN Web Docs | authoritative-guidance | 2026-07-27 | https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-hidden |
| SRC-MDN-INERT | MDN Web Docs | authoritative-guidance | 2026-07-27 | https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/inert |

`normative` = a stable standards-track specification. `normative-draft` = a current standards-track draft that may change. `authoritative-guidance` = official docs from the platform owner (MDN, web.dev, W3C WAI, Google Search Central). `secondary` = third-party tutorials/blogs : useful for common use-cases and phrasing, but their SEO claims are treated as assertions to verify, not as facts, per Section 2.

## 7. Using the Database

```sql
-- Every element with confirmed (not just claimed) SEO relevance
SELECT tag, seo_effect FROM elements WHERE seo_confidence = 'confirmed';

-- Every SEO claim that is NOT safe to repeat to a client as fact
SELECT claim_text, assessment FROM claims WHERE evidence_status IN ('unverified','contradicted');

-- Full reference view (denormalized, one row per element)
SELECT * FROM v_element_audit_reference;

-- Start a real audit run against a site
INSERT INTO audit_runs (audit_run_id, site_or_project, started_at, auditor)
VALUES (1, 'example.com', '2026-07-16', 'your-name');

INSERT INTO audited_pages (page_id, audit_run_id, url, page_type)
VALUES (1, 1, 'https://example.com/', 'homepage');

-- Log one finding per rule you checked on that page
INSERT INTO findings (page_id, rule_id, status, selector_or_location, observed_value, recommendation)
VALUES (1, 'SEM-001', 'fail', 'body', 'zero <main> elements found', 'Wrap the primary content in one <main>');

-- Pull every open (fail/needs-review) finding across all runs
SELECT * FROM v_open_findings;

-- Pull accessibility mapping guidance for a control pattern
SELECT * FROM accessibility_mappings
WHERE tag_or_pattern IN ('a[href]', 'button', 'Read More / Learn More control');

-- Store computed evidence with an audited finding
-- Fields are defined in audit_finding_fields.csv and should be added to the
-- database schema or a related finding_evidence table before import.

```

CSV exports of every table live in `exports/` for spreadsheet use : re-run this script after any database change to regenerate both.
