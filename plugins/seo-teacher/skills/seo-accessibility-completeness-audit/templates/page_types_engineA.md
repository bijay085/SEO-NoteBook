# Semantic HTML5 Page-Type Templates

## How to use this file

These structures are fallback semantic maps. The current page template supplied by the user takes precedence. Keep its sections, order, and intent unless the user requests restructuring. Omit any fallback region for which no content exists; do not manufacture content to complete a pattern.

The examples describe the content inside `<main>`. Site-wide header, primary navigation, breadcrumbs, and footer belong outside `<main>` when they are supplied by the site template.

## Using these templates for an annotated Miro handoff

When Miro is requested, translate the selected page-type structure into a page-equivalent wireframe rather than copying the code example onto the board. Keep the supplied current page layout recognizable and place the replacement content into its corresponding visual blocks.

Each major wireframe block must show the actual tags on or immediately beside the relevant visual objects:

- Visible section or component name
- Relevant supplied heading or concise content excerpt
- Semantic wrapper such as `header`, `main`, `section`, `article`, `aside`, `nav`, or `footer`
- Internal content elements such as `h1`–`h3`, `p`, `ul`, `ol`, `figure`, `figcaption`, `blockquote`, `form`, `label`, `input`, `details`, `summary`, `a`, or `button`
- Tentative layout such as full-width, two-column, card grid, ordered steps, carousel, or accordion
- Responsive source order when the visual layout uses columns
- CMS or component instruction when existing forms, sliders, menus, blog feeds, or testimonials must be retained

Do not label every visual card as `article`. Use `article` only when the item is independently meaningful. Use `div` for a styling or grid wrapper. Add the compact QA checklist defined in `MIRO_OUTPUT_SCHEMA.md`. A three-column mapping table is optional; the represented webpage must never use a layout table.

## Shared mapping rules

- Use `<article>` when the page is a self-contained editorial, profile, case study, guide, comparison, policy, or other independently distributable composition.
- A commercial service, product, location, about, or contact page may use direct `<section>` children inside `<main>` without an enclosing `<article>`.
- A hero is normally a `<header>` for `<main>` or its primary `<article>`, not a semantic element named `hero`.
- Breadcrumbs use `<nav aria-label="Breadcrumb">` only when breadcrumb links are supplied.
- A table of contents uses `<nav aria-label="Table of contents">` when it links to major sections.
- Related content may use `<aside>` when it is complementary. Use a normal `<section>` when it is part of the primary page purpose.
- A CTA is usually a concluding `<section>` with a heading. It is not automatically an `<aside>`.
- Testimonials are quotations only when they reproduce a person's statement. Do not wrap marketing summaries in `<blockquote>`.
- FAQs may use headed sections or `<details>/<summary>` when disclosure behavior is intended. Do not add FAQ schema unless requested and supported.
- Use `<a href="...">` for “Read More,” “Learn More,” card titles, and other controls that open another resource. Use `<button type="button">` for actions that change the current page.
- Repeated generic control labels need destination or action context. The computed accessible name should contain the visible wording and distinguish each control.
- Interactive components require rendered accessibility-tree checks for computed role, name, state, focus behavior, and source order.
- Hidden, off-canvas, inactive, and modal regions must not leave focusable descendants exposed in a conflicting state.

## Homepage

**Purpose:** Introduce the organization, route users to primary offerings, establish trust, and support a main conversion action.

```html
<main>
  <header><!-- H1, primary value proposition, primary CTA --></header>
  <section><!-- Primary services or products --></section>
  <section><!-- Audience, problems, or use cases --></section>
  <section><!-- Differentiators and trust evidence --></section>
  <section><!-- Process or how it works --></section>
  <section><!-- Testimonials or case evidence --></section>
  <section><!-- Final CTA --></section>
</main>
```

Use `<article>` inside a listing only when each featured item is independently meaningful. Do not wrap the entire homepage in `<article>` by default.

**Miro wireframe pattern:**

1. Site header and primary navigation outside `main`
2. `main` start marker
3. Hero as `main > header`, showing H1, introductory paragraphs, media when supplied, and primary actions
4. One full-width wireframe band per thematic section in source order
5. Internal cards or columns positioned inside the corresponding band and labeled with their meaningful child elements
6. Process represented as `ol > li` when sequence matters
7. Testimonials represented with the real review component and `blockquote` only for supplied quotations
8. Related resources represented as `aside` only when complementary to the homepage purpose
9. FAQ section showing the intended static or disclosure pattern
10. `main` end marker followed by the site footer

Do not add separate global implementation-card banks. Put concise implementation notes directly on affected wireframe objects and keep shared validation in the compact QA panel.

## Service page

**Purpose:** Explain one service, its scope, applications, process, proof, and next action.

```html
<main>
  <header><!-- H1, direct service definition, location if supplied, CTA --></header>
  <section><!-- Service overview and customer need --></section>
  <section><!-- Included services, capabilities, or solutions --></section>
  <section><!-- Who the service is for or use cases --></section>
  <section><!-- Process --></section>
  <section><!-- Qualifications, standards, guarantees, or proof --></section>
  <section><!-- FAQs --></section>
  <section><!-- Final CTA --></section>
</main>
```

Use an ordered list for true service steps and an unordered list for features or deliverables.

## Location or service-area page

**Purpose:** Connect a real service offering with a verified geographic market and local customer needs.

```html
<main>
  <header><!-- H1, service and location, direct answer, CTA --></header>
  <section><!-- Local service overview --></section>
  <section><!-- Services available in this location --></section>
  <section><!-- Property, industry, audience, or local-use context --></section>
  <section><!-- Local process, response, or delivery information --></section>
  <section><!-- Credentials and trust evidence --></section>
  <section><!-- Nearby areas only when supplied --></section>
  <section><!-- Local FAQs --></section>
  <section><!-- Contact or final CTA --></section>
</main>
```

Use `<address>` only for supplied contact information, not for every geographic mention. Do not invent local landmarks, travel times, neighborhoods, or service coverage.

## About page

**Purpose:** Explain the organization, history, mission, operating principles, people, and evidence of trust.

```html
<main>
  <header><!-- H1 and concise organization introduction --></header>
  <section><!-- Background or history --></section>
  <section><!-- Mission and purpose --></section>
  <section><!-- Values or operating principles --></section>
  <section><!-- Team or leadership --></section>
  <section><!-- Credentials, milestones, or community evidence --></section>
  <section><!-- CTA --></section>
</main>
```

Represent a verified chronology with an ordered list and machine-readable dates only when exact dates are supplied.

## Company values page

**Purpose:** Define the organization's stated values and show how they affect real work.

```html
<main>
  <header><!-- H1 and direct statement of the values' role --></header>
  <section><!-- One or more value subsections --></section>
  <section><!-- Mission --></section>
  <section><!-- How values appear in practice --></section>
  <section><!-- Customer evidence, when supplied --></section>
  <section><!-- CTA --></section>
</main>
```

Each value may be a subsection with its own heading. Use a list only when the items form a true collection rather than full thematic sections.

## Author, expert, or team-member profile

**Purpose:** Identify a person and establish verified background, expertise, credentials, work, and contact route.

```html
<main>
  <article>
    <header><!-- H1, role, organization, profile image if supplied --></header>
    <section><!-- Background and experience --></section>
    <section><!-- Areas of expertise --></section>
    <section><!-- Credentials and certifications --></section>
    <section><!-- Trust or professional approach --></section>
    <section><!-- Areas served, publications, or reviewed work --></section>
    <section><!-- Testimonials when supplied --></section>
    <footer><!-- Contact route or author-page CTA --></footer>
  </article>
</main>
```

Use `<address>` for the person's relevant professional contact details. Do not infer qualifications, ownership, affiliations, or service areas.

## Blog article, guide, or educational resource

**Purpose:** Deliver a self-contained explanation, answer, tutorial, analysis, or resource.

```html
<main>
  <article>
    <header><!-- H1, summary, author and publication details when supplied --></header>
    <nav aria-label="Table of contents"><!-- Optional major-section links --></nav>
    <section><!-- Main explanatory sections in source order --></section>
    <section><!-- Examples, steps, comparisons, evidence, or risks --></section>
    <section><!-- FAQs when supplied --></section>
    <footer><!-- Sources, reviewer, update date, or related CTA --></footer>
  </article>
  <aside><!-- Related resources only when complementary --></aside>
</main>
```

Use `<figure>` for independently referenced media, `<cite>` for the title of a cited work where appropriate, and `<time>` only with known machine-readable values.

## News article or announcement

**Purpose:** Report a dated event, release, change, or company announcement.

```html
<main>
  <article>
    <header><!-- H1, summary, dateline, author, publication date --></header>
    <section><!-- Main announcement or event details --></section>
    <section><!-- Context, impact, or supporting details --></section>
    <section><!-- Quotations when supplied --></section>
    <footer><!-- Organization contact, source, or update note --></footer>
  </article>
</main>
```

Do not generate dates, datelines, spokesperson quotations, or press contacts.

## Product page

**Purpose:** Describe one product, its supported specifications, applications, purchase information, and related evidence.

```html
<main>
  <header><!-- Product name, concise description, image, price/CTA if supplied --></header>
  <section><!-- Product overview --></section>
  <section><!-- Features and benefits --></section>
  <section><!-- Specifications or options --></section>
  <section><!-- Applications, fit, compatibility, or instructions --></section>
  <section><!-- Shipping, warranty, safety, or care when supplied --></section>
  <section><!-- Reviews or FAQs --></section>
  <section><!-- Purchase CTA --></section>
</main>
```

Use a definition list for specification pairs or a table for genuine option comparisons. Do not manufacture price, availability, SKU, ratings, or Product schema.

## Product or service category page

**Purpose:** Introduce a collection and help users evaluate or navigate its members.

```html
<main>
  <header><!-- H1 and category definition --></header>
  <section><!-- Category overview and selection context --></section>
  <section><!-- Product or service listing --></section>
  <section><!-- Selection criteria, applications, or comparison guidance --></section>
  <section><!-- FAQs --></section>
  <section><!-- CTA --></section>
</main>
```

Each listing item may use `<article>` when it has an independent heading, description, and destination. Pagination or filtering controls retain their actual interactive semantics.

## Comparison page

**Purpose:** Compare named alternatives against disclosed criteria and help the reader make a decision.

```html
<main>
  <article>
    <header><!-- H1, compared entities, scope, and concise finding --></header>
    <section><!-- Comparison criteria or methodology --></section>
    <section><!-- Summary comparison --></section>
    <section><!-- Criterion-by-criterion analysis --></section>
    <section><!-- Best fit by use case --></section>
    <section><!-- Limitations or decision factors --></section>
    <section><!-- FAQs --></section>
    <footer><!-- Recommendation or CTA --></footer>
  </article>
</main>
```

Use a table only when the same attributes are compared across alternatives. Keep qualifications and exceptions in nearby text rather than forcing complex conclusions into cells.

## Listicle, directory, or “top providers” page

**Purpose:** Present a disclosed set or ranking of entities with consistent information.

```html
<main>
  <article>
    <header><!-- H1, scope, inclusion basis, and reader intent --></header>
    <section><!-- Methodology or selection criteria --></section>
    <section>
      <ol><!-- One list item per ranked entity; each may contain an article --></ol>
    </section>
    <section><!-- Comparison guidance or choosing criteria --></section>
    <section><!-- FAQs --></section>
    <footer><!-- Conclusion or next action --></footer>
  </article>
</main>
```

Use `<ol>` only when order or ranking is meaningful. Do not invent rankings, review scores, company attributes, or selection methodology.

## Case study

**Purpose:** Document a verified situation, work performed, evidence, and result.

```html
<main>
  <article>
    <header><!-- H1, client/project identification permitted by source --></header>
    <section><!-- Situation or background --></section>
    <section><!-- Problem or objective --></section>
    <section><!-- Approach or implementation --></section>
    <section><!-- Results with supplied evidence --></section>
    <section><!-- Lessons, implications, or next steps --></section>
    <footer><!-- Testimonial, project details, or CTA --></footer>
  </article>
</main>
```

Use `<data>` or a table only when exact values are supplied and their meaning is clear. Do not turn correlation into causation or strengthen reported outcomes.

## FAQ page

**Purpose:** Answer a coherent collection of user questions about one topic, service, product, or organization.

```html
<main>
  <header><!-- H1 and scope of the questions --></header>
  <section><!-- FAQ collection --></section>
  <section><!-- Contact or next-step CTA --></section>
</main>
```

For static answers, use headed question sections. For expandable answers, use one `<details>` per question with the question in `<summary>`. Do not use `<details>` merely to hide weak or excessive content.

## Contact page

**Purpose:** Provide verified contact methods, availability, location, service context, and a usable inquiry route.

```html
<main>
  <header><!-- H1 and response purpose --></header>
  <section><!-- Contact methods --></section>
  <section><!-- Address, hours, service area, or directions when supplied --></section>
  <section><!-- Contact form --></section>
  <section><!-- Expectations, emergency instructions, or FAQs --></section>
</main>
```

Wrap relevant contact details in `<address>`. A form requires real labels, control names, and a known submission implementation; otherwise preserve a stated placeholder rather than inventing an endpoint.

## Testimonial or reviews page

**Purpose:** Present authentic supplied customer statements and relevant attribution.

```html
<main>
  <header><!-- H1 and review context --></header>
  <section><!-- Review collection --></section>
  <section><!-- Supporting trust information --></section>
  <section><!-- CTA --></section>
</main>
```

Use `<blockquote>` for each supplied testimonial and place attribution outside the quotation. Do not create names, ratings, dates, review text, or aggregate statistics.

## Portfolio, gallery, or project page

**Purpose:** Present verified work examples with useful project or media context.

```html
<main>
  <header><!-- H1 and collection/project scope --></header>
  <section><!-- Gallery or project collection --></section>
  <section><!-- Process, capabilities, or project details --></section>
  <section><!-- CTA --></section>
</main>
```

Use `<figure>` only when media and caption form a self-contained referenced unit. Use `<article>` for an independently described project with its own destination or complete narrative.

## Pricing page

**Purpose:** Explain supplied plans, inclusions, exclusions, billing conditions, and selection guidance.

```html
<main>
  <header><!-- H1 and pricing scope --></header>
  <section><!-- Plans or pricing options --></section>
  <section><!-- Feature comparison --></section>
  <section><!-- Billing terms, inclusions, or exclusions --></section>
  <section><!-- Selection guidance --></section>
  <section><!-- FAQs --></section>
  <section><!-- CTA --></section>
</main>
```

Use a comparison table when plans share the same features. Preserve currency, billing period, conditions, and qualifiers exactly as supplied.

## Legal, policy, or terms page

**Purpose:** Publish a self-contained policy, agreement, disclosure, or legal notice without changing its meaning.

```html
<main>
  <article>
    <header><!-- H1, effective/update date when supplied --></header>
    <nav aria-label="Table of contents"><!-- Optional section links --></nav>
    <section><!-- Policy clauses in supplied order --></section>
    <footer><!-- Contact or revision information when supplied --></footer>
  </article>
</main>
```

Preserve numbering, definitions, exceptions, and wording. Do not simplify or rewrite legal content unless expressly requested.

## Fallback for an unlisted page type

When no named pattern fits, derive structure from the current template:

```html
<main>
  <header><!-- Page identity and direct introductory answer --></header>
  <section><!-- One thematic section per supplied H2-level topic --></section>
  <section><!-- Supporting evidence, questions, or conversion section --></section>
</main>
```

Choose `<article>` only after confirming that the complete page forms an independent composition. Record the inferred page type or structural decision briefly if it materially affects the output.
