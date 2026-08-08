# Master Claims Verification Table

Every checkable claim from "Visual Semantics: The Missing Piece of Topical Authority," in one table. Verdict scale: **(A)** directly supported by a quote · **(B)** plausible interpretation, not explicit · **(C)** unverifiable · **(D)** appears wrong/exaggerated/unsupported. Detail file linked per row.

| # | Claim | Verdict | One-line evidence | Detail |
|---|---|---|---|---|
| 1 | US12393768B2 covers "structured information cards" (product/hotel/real estate/trip/credit card) | D | Patent is about layout-block pretraining; card-type content belongs to a different patent (US11238058B2) | [01](01-patents-verification.md)§1 |
| 2 | US9069855B2 titled "Achieving pseudo-rendering with minimal computational resources" | D | Fabricated title; real title is about hierarchical-data-structure pseudo-rendering | [01](01-patents-verification.md)§2 |
| 3 | US9069855B2 positions against Microsoft's ViPS | B | Mechanism contrast is fair; "ViPS"/"vision-based" never appears in the patent itself | [01](01-patents-verification.md)§2 |
| 4 | WO2020033805A1 classifies sites as "expert/apprentice/amateur" via visual/layout embeddings | Mixed A/D | Expert/apprentice/**layperson** tiers are directly quoted; "visual and layout" framing unsupported — neither word appears in the patent | [01](01-patents-verification.md)§3 |
| 5 | US8498984B1 titled "Classifying search results by their page elements" | D | Fabricated title; real title is "Categorization of search results"; "page element(s)" appears nowhere in the text | [01](01-patents-verification.md)§4 |
| 6 | A "Merging search engine results" patent exists and relates to Twiddlers | D | No such patent exists; article's own link is a leaked internal doc, not a patent, and doesn't mention merging | [01](01-patents-verification.md)§5 |
| 7 | US12536233B1 is the "January 29" patent | D | Real grant date is January 27 | [01](01-patents-verification.md)§6 |
| 8 | US12536233B1's "landing page score" uses click data + explicit user feedback | Mixed A/D | Click-data link is quoted; "user feedback" actually drives a different mechanism (RL asset refinement) | [01](01-patents-verification.md)§6 |
| 9 | US12536233B1 uses "visual segmentation" | D | "Segmentation" is generic ML boilerplate; real mechanism uses page "components," not visual segments | [01](01-patents-verification.md)§6 |
| 10 | US10445328B2 maps entity attributes to visual SERP features | A | Directly quoted (Height→chart, Location→map, Year Built→timeline) | [01](01-patents-verification.md)§7 |
| 11 | A separate patent covers "adjust SERP features based on entity primary attributes" | B (not a separate patent) | Same paragraph, same patent as #10; "primary attribute" language isn't in the text | [01](01-patents-verification.md)§8 |
| 12 | US9916366B1 titled "Query Augmentation," inventors include Bharat & Shukla | A | Exact title match; both confirmed named inventors | [01](01-patents-verification.md)§9 |
| 13 | US9916366B1 = inserting related terms into a query | B | Real mechanism is query-log mining/matching, not term-insertion | [01](01-patents-verification.md)§9 |
| 14 | US20240289407A1 shares inventors/terminology with US9916366B1 | D | Only Shukla overlaps (not Bharat); "augment" appears once, meaning something different | [01](01-patents-verification.md)§10 |
| 15 | Bharat & Shukla are linked to AI Overviews/AI Mode | D (Bharat) / B (Shukla) | Neither is on the real AI Overviews patent (US11769017B1); Shukla is on the AI-Mode-associated patent, but that mapping is industry inference, not Google-confirmed | [01](01-patents-verification.md)§10 |
| 16 | "Neural Design Network" paper shows layouts improving search performance | D | Real Google-co-authored paper, but about magazine/app-UI/banner-ad design, not webpages or search | [02](02-papers-verification.md)§1 |
| 17 | Google's SERP-evaluation paper shows dwell time varies by category, long dwell ≠ quality | D | Paper never mentions "dwell time" at all; no category comparison exists in it | [02](02-papers-verification.md)§2 |
| 18 | "[Rank anything first]" framework increased rankings 20–60% | D | No percentage appears anywhere in the paper; it's an adversarial-attack disclosure the authors warn against, not a ranking-boost technique | [02](02-papers-verification.md)§3 |
| 19 | ViPS represents early layout understanding "also cited" by Google | A (paper), C (citation claim) | Paper identity/description confirmed; no citation record found anywhere | [02](02-papers-verification.md)§4 |
| 20 | "Google Embedding 2" uses generative neural networks to vectorize multimodal content | D | Real paper is called **Gemini Embedding 2**; Google explicitly frames it as embedding-only, not generative | [02](02-papers-verification.md)§5 |
| 21 | "WebRef" = "WebFormer," Google's Web Page Transformer | D | Two distinct, unrelated systems; WebFormer's authors aren't Najork/Bendersky; WebRef is a 2013 ad-matching patent | [02](02-papers-verification.md)§6 |
| 22 | QRG cites "human effort and involvement" / "design effort" as quoted phrases | D | Neither phrase appears verbatim; underlying concepts (effort, design/functionality) are real but separate | [03](03-official-docs-verification.md)§1 |
| 23 | Content Warehouse leak has `GoodocSemanticLabel` for page/PDF semantic labels | A | Confirmed live documentation, genuine semantic-labeling model | [03](03-official-docs-verification.md)§2a |
| 24 | Content Warehouse leak has `WebrefFatcatCategory` for categorical weighting | D | 404/500 on fetch; absent from the full leak index and from independent SEO analyses of the leak | [03](03-official-docs-verification.md)§2b |
| 25 | Neural matching aligns "entity type and entity ID" | D | Google's actual official text says "representations of concepts," not entity type/ID | [03](03-official-docs-verification.md)§3 |
| 26 | DOJ Twiddler doc contains `max_total`/`BlogCategorizer` | B | Well corroborated by independent secondary sources | [03](03-official-docs-verification.md)§4 |
| 27 | Twiddler doc "surfaced via" the DOJ antitrust trial | D | Actually a 2019 Vorhies whistleblower leak; absent from SEL's own roundup of real 2023 trial exhibits | [03](03-official-docs-verification.md)§4 |
| 28 | Martin Splitt calls centerpiece annotation "primary content" at ~28:50 | A/B (substance), C (timestamp) | Substance strongly corroborated by contemporaneous 2021 coverage; exact timestamp unconfirmed | [03](03-official-docs-verification.md)§5 |
| 29 | "Godfather of Topical Authority" is how SEO communities know Koray | B | Real nickname, but third-party (2023 podcast)-originated and self-amplified, not organically universal | [07](07-people-koray-and-google-researchers.md) |
| 30 | Najork & Bendersky are the two engineers currently driving Google's visual/query-semantics direction | Mixed A/D | Najork confirmed current; Bendersky left Google for Databricks ~mid-2025 — a year stale | [07](07-people-koray-and-google-researchers.md) |
| 31 | Grushetsky is "RankLab founder," frequently cited alongside Najork/Bendersky | D | Zero independent corroboration for "RankLab"; only one (not "frequent") collaboration with Bendersky; none with Najork | [07](07-people-koray-and-google-researchers.md) |
| 32 | Article's "centerpiece annotation"/EAV/"query semantics" derive from or map onto Frame Semantics | N/A — article never claims this | Real theory (Fillmore/FrameNet) doesn't mechanically map onto the article's DOM/database/IR concepts | [05](05-frame-semantics.md) |
| 33 | "Hivemind Token Index" is an established concept | Not found | Absent from this article, Koray's other work, all patents checked, academic literature, and the Azure chunking doc you flagged; a second independent research pass reached the same null result | [06](06-hivemind-token-index.md) |
| 34 | "Every 10–20 pixels" introduces an interaction point | D | Unfalsifiable rhetoric — no defined device, viewport, sample, or test anywhere | [10](10-critical-reading-and-methodology.md) |
| 35 | The 19-change, 100K+-page case study proves the calculator/centerpiece move drove the ranking gain | D | No staggered rollout, control URLs, or rollback evidence to isolate one change; CTR fell 34% while impressions rose 99% — a pattern also consistent with ranking for many more, lower-relevance queries, not uniquely proof of the specific change | [10](10-critical-reading-and-methodology.md) |
| 36 | Google reduced the HTML file size limit to 2MB after the December 2025 core update | C | Not confirmed against official documentation by either research pass — flagged, not verified | [10](10-critical-reading-and-methodology.md) |
| 37 | Macro-context (above the fold) = Main Content; micro-context (below the fold) = Supplementary Content | D | QRG defines MC/SC by purpose-relevance, not fold position — a long article body remains MC far below the fold | [03](03-official-docs-verification.md)§1, [10](10-critical-reading-and-methodology.md) |

## Tally

- **(A) directly supported:** 8 of 37
- **(B) plausible but not explicit:** 8 of 37
- **(C) unverifiable:** 4 of 37 (3 fully, 1 partial)
- **(D) wrong/exaggerated/unsupported:** 22 of 37 (several rows carry mixed A/D or B/D verdicts, counted once each here by their dominant/most serious verdict)

**Read on this tally:** this is not a article with a few sloppy citations — a majority of its checkable, specific claims about named patents, papers, and people don't hold up against the primary source when read directly. The core *thesis* (Google increasingly weighs layout/structure/functional design, not just text) is independently well-supported by real material — the 2014 Page Layout algorithm, the QRG's genuine (if misquoted) effort/design language, Splitt's real centerpiece-annotation explanation, and several genuinely-verified patents (US10445328B2, US12536233B1's core mechanism, US9916366B1's inventors). What doesn't hold up is most of the *specific supporting evidence* marshaled for that thesis — titles, numbers, names, and mechanisms that were embellished, conflated, misdated, or in one case inverted from what the source actually says.
