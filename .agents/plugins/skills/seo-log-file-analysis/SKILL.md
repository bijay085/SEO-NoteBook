---
name: seo-log-file-analysis
description: >-
  Run a config-driven SEO forensic analysis of raw server ACCESS LOGS : what search
  crawlers and visitors actually requested, what status they got back, and where crawl
  budget was spent. Parses Apache/nginx combined, IIS W3C, JSON/Cloudflare, Cloudways
  PHP-FPM and aggregated CSV/TSV crawl exports (plain or .gz/.bz2/.xz), verifies bots
  against official published IP ranges instead of trusting User-Agent, segments traffic
  into search bots / SEO crawlers / AI fetchers / infrastructure / suspicious / human,
  and reports evidence-gated findings across HTTP errors, redirects and chains, crawl
  budget waste, indexability, performance and security. Produces a branded SEO deliverable (deep HTML report + master XLSX with URL, bot-crawl, trend and coverage
  tabs). Use whenever the user says "log file analysis", "analyse my server logs",
  "access log audit", "crawl budget analysis", "what is Googlebot actually crawling",
  "is Googlebot getting errors", "log file SEO", "bot traffic analysis", "who is
  scraping my site", "verify Googlebot", "crawl frequency", or drops .log / access.log
  / .log.gz files. Industry-agnostic and config-driven so it works for ANY client.
  Runtime needs NO API keys : the only network calls are the public search-engine IP
  range files, which are cached and can be skipped with --offline. Optional sitemap and
  GSC exports add crawl-coverage cross-reference. Reuse built-in report branding (brand_lib / report_kit).
compatibility: >-
  Agent Skills (SKILL.md). Portable across Claude Code, Cursor, Codex/GPT,
  Gemini CLI, Copilot, and chat UIs via project upload. See pack
  AGENT_RUNTIME.md + INSTALL.md.

---

# Log-File Analysis

A repeatable, config-driven **server log audit**. Every other SEO tool tells you what
*should* happen; the access log is the only source that tells you what **did** happen : 
which URLs Googlebot actually requested, how often, and what the server actually
returned. This skill turns that raw record into a SEO deliverable: one branded HTML
document plus a master XLSX carrying both the authored findings and the measured
URL / bot / trend / coverage tabs.

It is the **server-side sibling** of the page-side skills (`seo-render-audit`,
`seo-after-foundational-setup-audit`). Those ask "what does this page contain?"; this one
asks **"what did the crawler receive, and what did it cost?"**

Every number is **measured, not assumed** : a real hit count, a real status share, a real
byte size. Bot identity is **verified against published IP ranges**, not taken from the
User-Agent string, and when a range file cannot be loaded the report says so rather than
quietly reporting fewer bots.

## When to use
- A site needs its **crawl behaviour** understood: budget waste, crawl frequency, which
  URLs Google ignores, whether Googlebot is hitting errors.
- The user asks: *log file analysis / access log audit / crawl budget / what is Googlebot
  crawling / is Googlebot seeing 404s / who is scraping my site / verify Googlebot / bot
  traffic breakdown / crawl frequency*.
- The user drops `access.log`, `*.log.gz`, a Cloudways log bundle, an IIS `u_ex*.log`, a
  Cloudflare Logpush JSON file, or an aggregated bot-hits CSV.
- A technical audit found a symptom (pages not indexed, slow indexing, a traffic drop) and
  the logs are needed to prove the mechanism.

## Required access : request it before running (do not guess)
At intake, check what is available and **ask for anything missing in one structured
question**, then proceed with what you have, degrading gracefully. See
`references/input-manifest.md`.

Ask for, at minimum:
1. **The log files** : as long a window as possible. **7 days is the practical minimum**,
   30 days is ideal: Googlebot crawl is bursty, so a 24-hour sample cannot support a claim
   about crawl *rate* (the engine downgrades those findings to Low confidence
   automatically, but a short window still makes a weaker deliverable).
2. **Which server/stack** : Apache, nginx, IIS, Cloudflare, Cloudways. It decides which
   log is authoritative (Methodology §1).
3. **The domain** : for the report header and cross-referencing.
4. **Sitemap XML (optional, high value)** : turns "never crawled" into a finding.
5. **GSC Pages export (optional, high value)** : surfaces pages earning impressions that
   Googlebot has not revisited.
6. **Whether a CDN sits in front** : if Cloudflare/Fastly serves cached responses, the
   origin log under-counts real traffic and the report must say so.

## The deliverable
1. **`<Client>_<Period>_Log-File-Analysis.html`** : one branded document: header, sticky
   nav, contents grid, then every dimension with measured evidence, inline SVG charts and
   collapsible Issue·Evidence·Solution·Execution cards.
2. **`<Client>_<Period>_Log-File-Analysis.xlsx`** : led by **`Issue Analysis`**: every
   finding across **16 columns** (# · Category · Issue · Detail · Affected URL/Scope ·
   Segment · Status · Hits · Urgency · Confidence · Evidence · Root Cause · Business
   Impact · Step-by-Step Action · Effort · Verification Steps), colour-coded and
   filterable. Then `Findings Summary` (one row per pattern), `Health Scorecard`,
   `Traffic Breakdown`, `URL Detail`, `Bot Crawl Detail`, `Crawl Trend`, `Log Sources`,
   `Crawl Coverage`, `Decision Guide` : plus one tab per authored dimension.
3. **`analysis.json` + `facts.md`** : the full fact-pack. `facts.md` expands each finding
   with its root cause, business impact, step-by-step action and verification steps.
Both report formats use SEO report branding and stay at **parity**.

**The engine alone produces BOTH complete deliverables.** There is no format switch to
configure : every run writes all four files, and each format has its own wired path to
`analysis.json`:

| File | Written by | Source |
|---|---|---|
| `analysis.json`, `facts.md` | `analyze_logs.py` | the engine |
| `.xlsx` | `build_xlsx.py` | `analysis.json` (via `build_data_tabs.py`) + authored |
| `.html` | `build_html.py` | `analysis.json` (via `auto_report.py`) + authored |

Authoring `report_data.py` ADDS the interpretation layer; it is never a prerequisite.
Parity means **same facts, format-appropriate shape**: the HTML is the narrative view
(Issue·Evidence·Solution·Execution cards, charts, jump-nav), the XLSX the working view
(one filterable `Issue Analysis` grid, not the same findings retyped across nine tabs).
Un-authored sections and any `‹EXAMPLE›` placeholder are stripped by both builders rather
than shipped, and an unfilled `‹Client›` never reaches a filename : the site and date
range from `analysis.json` are used instead.

## How it works (the loop)
A **hybrid**: deterministic Python parses, classifies and applies the gated detection
rules; **you (Claude) author the findings** : the interpretation and the executable
step : grounded strictly in the measured numbers.

```
1. INTAKE → load config.json; locate the logs; REQUEST missing inputs (one question)
2. PARSE → analyze_logs.py: format detection per file, log-role routing, two-pass
             streaming parse (.gz/.bz2/.xz, directories and globs supported)
3. VERIFY → bot_verification.py: load official bot IP ranges (cached, --offline safe);
             the report discloses which sources were live / cached / unavailable
4. CLASSIFY→ traffic_classify.py: 6 segments; URL purpose gates the suspicious rule
5. DETECT → detect_issues.py: the evidence-gated rules; each finding carries the gate
             it passed in its `evidence` line
6. AUTHOR → report_data.py: every finding = Issue · Evidence · Solution · Execution
7. BUILD → build_html.py + build_xlsx.py; the XLSX appends the measured data tabs
8. VALIDATE→ tabs carry real ROWS (not just headers), counts match analysis.json, HTML
             tags balanced, and no number appears that analysis.json does not contain
9. DELIVER → copy to the output folder, send all files, summarize honestly
10. MEMORY → save durable client facts (log source of truth, crawl profile, blocks made)
```

Run the engine:

```bash
python3 scripts/analyze_logs.py --logs ./logs --site example.com --out ./Log-Analysis --sitemap ./sitemap.xml
```

Then author `scripts/report_data.py` from `facts.md`, and build both formats:

```bash
python3 scripts/build_html.py ./Log-Analysis && python3 scripts/build_xlsx.py ./Log-Analysis
```

## The 8 dimensions
See `references/report-catalog.md`. In short:

| # | Dimension | Source | Mode |
|---|---|---|---|
| 0 | **Crawl Summary** : volume, window, parse rate, segment mix, verified-bot coverage | engine | script+author |
| 1 | **HTTP Errors** : 404s and 5xx, split by whether Googlebot saw them | engine | script+author |
| 2 | **Redirects & Chains** : persistent 301 crawling, content 302s, multi-hop chains | engine | script+author |
| 3 | **Crawl Budget Waste** : backend endpoints, parameter explosion, static ratio, taxonomy, infra traffic | engine | script+author |
| 4 | **Indexability & Discovery** : robots.txt/sitemap health, trailing-slash duplicates, mobile-first split, Googlebot share | engine | script+author |
| 5 | **Performance** : served response weight per URL | engine | script+author |
| 6 | **Security & Suspicious Traffic** : sensitive-file exposure/probing, scraper IPs | engine | script+author |
| 7 | **Crawl Coverage** : sitemap URLs never crawled; GSC pages with impressions but no crawl | sitemap/GSC | script+author |
| 8 | **Action Items** : P0 crawl-blocking + security · P1 budget/redirects · P2 monitoring | all | author |

Scale to inputs: no sitemap and no GSC export → drop 7; no byte size in the log format →
drop 5 and say why; no User-Agent field (Cloudways FPM) → dimensions 1-4 run on
verified-IP identification only, and the cover states that limitation.

## Author findings (the quality bar)
Every finding = **{issue, sev, evidence, solution, execution}**. `evidence` is a measured
value from `analysis.json` : a hit count, a status share, a percentage of traffic, the
verbatim URL. `execution` is literal (e.g. *"Add `Disallow: /wp-admin` to robots.txt, then
GSC ▸ Settings ▸ robots.txt ▸ confirm Blocked"*). Severity Critical/High/Medium/Low +
Good/Info, mapped from the engine's urgency (P1→critical, P2→high, P3→medium). See
`references/methodology.md`.

## Methodology (the non-obvious rules)
Read `references/methodology.md` before authoring. Load-bearing:
- **A log proves presence, never absence.** "Googlebot never crawled X" is only true for
  *this window*. State the window every time you make a negative claim.
- **Verify bots by IP, not User-Agent.** Anyone can send `Googlebot/2.1`. Only an IP in
  Google's published range proves it. If the range file did not load, the finding says
  "UA-identified", not "verified".
- **Admin polling is not scraping.** `admin-ajax.php`, `wp-cron.php`, heartbeat and
  service-worker traffic looks exactly like a scraper. An IP whose traffic is >50%
  admin-like is a logged-in admin : never flagged, at any volume.
- **One Googlebot error outweighs a hundred human ones.** A single verified-Googlebot 404
  or 5xx is an indexing event; the same status seen only by humans is link hygiene.
- **Crawl is bursty : short windows lie about rate.** Under 48h, crawl-rate findings drop
  to Low confidence automatically. Do not override that.
- **A CDN hides traffic.** With Cloudflare in front, the origin log shows only cache
  misses. Never present origin-log volume as total traffic without saying so.
- **Blocking is a scalpel, not a hammer.** Before recommending an IP or ASN block, confirm
  the IP is a datacenter, not residential : a wrong block costs real customers.
- **Crawl budget only bites at scale.** On a 200-page site Google has budget to spare;
  frame waste findings as hygiene there, and as a real constraint only on large sites.

## Data sources & tool routing
`references/input-manifest.md` has the details. **The engine needs no API keys.** Its only
network calls are the public search-engine IP range files (Google, Bing, DuckDuckGo,
Apple, OpenAI, Ahrefs); they are cached for 7 days under
`<workspace>/.cache/seo-log-file-analysis/` and `--offline` skips them entirely. Client log
files are read from disk (use local filesystem tools if the path is TCC-blocked).
GSC (`mcp__google-search-console__*`) is optional context for dimension 7.

## Guardrails
- **Never fabricate.** Every count comes from `analysis.json`. If it is not in there, it
  does not go in the report.
- **Disclose the parse rate.** If 12% of lines failed to parse, say so on the cover : a
  finding drawn from 88% of the data is still valid, but the reader must know.
- **Disclose bot-verification coverage.** If Bing's range file failed to load, Bingbot in
  that run is UA-identified only, and the report says so.
- **Honesty over spin.** A clean crawl profile is a `Good` finding : say it.
- **Degrade gracefully.** Missing input → drop its dimension, note it on the cover.
- **Parity.** Any new measured layer goes into both the HTML and the XLSX.
- **The skill produces analysis; the human applies the block.** It never edits robots.txt,
  never submits to Search Console, and never blocks an IP on the user's behalf.

## Output location
Write everything to `<output_dir>/` from config (default `./Log-Analysis/`). Keep
`analysis.json` and `facts.md` alongside the two reports : they are the evidence trail.
