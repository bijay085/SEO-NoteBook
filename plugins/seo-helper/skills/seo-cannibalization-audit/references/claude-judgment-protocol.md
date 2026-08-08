# Claude judgment protocol

Four judgments replace what the original app bought from Gemini. Each is a `*.task.json` you read
and a `*.answer.json` you write beside it. `judgment.py apply` validates and merges them; anything
you omit degrades to a deterministic fallback and is reported in the deliverable's Coverage section.

**The governing rule for all four: under-merging is safe, over-merging causes destructive 301s.**
When you are genuinely unsure, leave the item out. A missed pair costs recall on one audit; a wrong
merge recommendation destroys a live page's traffic.

Write only valid JSON matching the `answer_schema` embedded in each task file. Echo query strings
and URLs **exactly** as given : `apply` matches on the literal string and reports anything it cannot
recognise as `unrecognised_queries`.

---

## 01 : Topics

**Input.** Blocks of brand-normalised queries, each with `pages` (how many URLs it appears on) and
`impressions`. Blocking is deliberately over-inclusive: queries were unioned on any shared
non-ubiquitous token, so a block often mixes genuinely different topics. That is by design : the
mechanical step buys recall, you supply precision.

**Your job.** Partition each block into topics. Two queries share a topic **only when a searcher
typing either one wants the same page**.

```json
{"blocks": [
  {"block_id": 0, "topics": [
    {"topic": "celpip reading practice test",
     "queries": ["celpip reading practice test", "free celpip reading practice",
                 "celpip reading test", "celpip reading sample"]}]},
  {"block_id": 1, "topics": [
    {"topic": "celpip speaking template", "queries": ["celpip speaking template", "celpip speaking task 1"]},
    {"topic": "celpip writing guide", "queries": ["celpip writing guide", "celpip writing task 2"]}]}
]}
```

Block 1 above is the case that matters: the blocker fused speaking and writing because both contain
"task". Splitting them is the entire value of this step : merged, a speaking page and a writing page
would share a topic key and could be reported as competing.

- **Merge:** word order, plurals, stop-word noise, synonyms, and "free"/"online"/"best" modifiers : 
  `"celpip mock test free"` and `"free celpip practice test"` are one search.
- **Do NOT merge:** ordinals and parts (`part 1` vs `part 2`), different modules or sections,
  different products, different intents (`x price` vs `what is x`).
- A topic with one member changes nothing and is skipped : don't pad.
- Omit any query you are unsure about; it keeps its own string and simply pairs less aggressively.

---

## 02 : Entities (peer groups)

**Input.** Batches of pages with slug, top queries, clicks, impressions.

**Your job.** Infer a two-axis taxonomy **from this corpus only** : never category names from prior
knowledge of the industry. `axis_1` is the top-level section; `axis_2` is the content angle within
it. Two pages are cannibalization-eligible **iff they share both axes**, so this is the strongest
filter in the pipeline: get it wrong and you either fuse unrelated pages or hide real duplicates.

```json
{"pages": [
  {"url": "https://example.com/celpip-reading-practice-test/",
   "axis_1": "reading", "axis_2": "practice_test", "is_hub": false, "covers": [], "confidence": 0.95},
  {"url": "https://example.com/celpip-guide/",
   "axis_1": "overview", "axis_2": "overview", "is_hub": true,
   "covers": ["reading", "writing", "speaking"], "confidence": 0.8}
]}
```

- Use `snake_case`. Labels are normalised, so `Practice Tests` and `practice_test` collapse anyway : 
  but stay consistent within a run or near-identical pages land in different groups.
- **Granularity is the whole game.** `axis_1: "celpip"` on every page makes the gate useless.
  `axis_2: "reading_practice_test_part_3"` makes every page its own group and hides real duplicates.
  Aim for the level at which two pages would genuinely compete for the same searcher.
- `is_hub: true` only for a page that genuinely spans sections (a top-level overview linking into
  each). List the `axis_1` values it covers; a hub is eligible against pages in any section it covers.
- `confidence` below `entity_min_confidence` (0.7) is counted and reported, not discarded.
- Omitting a page is allowed : that pair falls through to the statistical tier, which is noisier but
  not wrong.

---

## 03 : Intent

**Input.** The same page batches, each carrying a `rule_intent` prior from the URL-pattern classifier.

**Your job.** Confirm or override. Two pages only cannibalize when they serve the same intent.

```json
{"pages": [
  {"url": "https://example.com/celpip-reading-practice-test/", "intent": "informational", "confidence": "high"}
]}
```

Classes: `transactional`, `commercial`, `informational`, `navigational`, `news`, `unknown`.

- **Keep the prior unless the queries clearly contradict it.** It reads the URL path, which is the
  strongest single signal.
- A `/2026/03/15/slug/` permalink is WordPress URL structure, **not** news : such posts default to
  `informational`, and that default is usually right.
- `unknown` pairs with everything. Use it honestly rather than guessing: dropping a real pair on a
  bad guess is worse than carrying it forward for the parity gates to settle.
- `news`↔`informational` and `commercial`↔`informational` are treated as compatible downstream, so
  you do not need to force those into agreement.

---

## 04 : Duplicates (written after the shortlist)

**Input.** Only the *boundary* pairs : URL twins, or pairs whose topic profile already clears
`dup_twin_topic_min`. Everything else was decided without needing you.

**Your job.** Score how much the two pages are **the same page**, 0.0 to 1.0. Fetch the live pages for
title / H1 / meta description if you can, and say in `why` whether you did.

```json
{"pairs": [
  {"pair_id": "https://example.com/a/||https://example.com/b/", "content_sim": 0.45,
   "why": "fetched both: same template, but B is Test Set 2 with entirely different passages and questions"}
]}
```

Copy `pair_id` verbatim from the task file.

| Score | Meaning | Effect |
|---|---|---|
| ≥ 0.94 | the same page duplicated | immediate `duplicate` → 301 recommendation |
| 0.80 to 0.93 | same topic, genuinely different page | falls through to the time-series detectors |
| 0.50 to 0.79 | related, clearly differentiated | falls through; still allows the URL-twin path |
| < 0.50 | actively different content | **vetoes** the URL-twin duplicate path |

**Be strict at the top of that scale.** A score ≥ 0.94 produces a 301 recommendation without ever
looking at the traffic. `/reading-practice-test/` vs `/reading-practice-tests-3/` are slug twins on
one topic and *look* identical to every mechanical signal : only reading the pages reveals Part 3 is
a different test. That is exactly the call this judgment exists to make.

If you cannot fetch the pages, say so and score conservatively from slug and queries. The pipeline
treats a missing pair as "no signal" and falls back to the URL-twin path, which the differentiate
guard still protects.
