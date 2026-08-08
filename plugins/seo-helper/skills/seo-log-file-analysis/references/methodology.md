# Methodology : how to read a log without lying

## 1. Pick the source of truth before you count anything
A stack emits several logs and they do not agree. Routing (`route_log_roles`):
- **Cloudways**: `backend_*.access.log` is authoritative : it carries the User-Agent.
  The PHP and static logs are supplemental context, summarised on the Log Sources tab
  and never mixed into the SEO totals (double-counting one request as three).
- **Standard hosting**: the access log is primary; error logs are excluded from traffic
  analysis entirely.
- **Behind a CDN**: the origin log is only cache MISSES. Say this on the cover or every
  volume number in the report is wrong by an unknown factor.

## 2. Verify, do not trust
A User-Agent is a free-text field. `curl -A "Googlebot/2.1"` makes anyone Googlebot.
The engine checks the client IP against the ranges Google, Bing, DuckDuckGo, Apple and
OpenAI publish, and that identification **overrides** the UA. Two consequences:
- A "Googlebot" outside Google's ranges is a spoofer, and is classified on its behaviour.
- If a range file did not load, that engine's bots are UA-identified for the run. The
  cover states it. Never write "verified Googlebot" when the table did not load.

## 3. The evidence gate on every rule
A gate is the extra condition that must hold before a pattern becomes a finding, plus
the `evidence` line that states why it survived. The gates, and what they prevent:

| Rule | Gate | Prevents |
|---|---|---|
| 404 | ≥3 hits **or** ≥1 Googlebot hit; scanner probes excluded | typo noise and double-reporting attack probes |
| 5xx | ≥10 hits, or ≥5% of that URL, or ≥1 Googlebot hit | one-off blips filed as P1 |
| 301 | ≥5 hits **and** ≥50% of that URL's requests | two stale hits looking like a systemic problem |
| 302 | content URLs only | flagging correct auth/checkout redirects |
| Trailing slash | skipped if either variant 301s >80% | reporting a working canonical as a bug |
| Redirect chain | referrer present on ≥20% of rows | phantom chains from a sparse referrer column |
| Backend crawl | ≥3 **verified** search-bot hits | generic bot noise |
| Infra traffic | >15% of all traffic | normal cache-preloader baseline |
| Static ratio | >30% of bot requests | normal CDN re-validation |
| Suspicious IP | admin-URL share ≤50% | flagging a logged-in admin as a scraper |
| Googlebot share | <48h window → Low confidence | crying wolf over bursty crawl |

**Do not loosen a gate to produce more findings.** A short report of real problems beats
a long one the client disproves in ten minutes.

## 4. Absence is not evidence
The log records what happened. It cannot record what did not. Every negative claim gets
its window attached: not "Googlebot never crawls /services/", but "Googlebot did not
request /services/ in the 14-day window 1 to 14 Aug". This applies to the whole of
dimension 7 : the crossref block ships that caveat in its own `note` field; keep it.

## 5. Severity mapping and what earns P0
Engine urgency → report severity: P1 - Critical → `critical`, P2 - High → `high`,
P3 - Monitor → `medium`. `good` and `info` are authored, not emitted by the engine.

P0 in the Action Items section is reserved for the two things that stop the site being
crawled or expose it:
- robots.txt or sitemap returning an error (crawl-halting)
- a sensitive file served with 200 (active exposure : credentials must be rotated)
Everything else is P1 or P2, however large the number.

## 6. Recommend the smallest sufficient fix
- **noindex,follow beats a robots.txt Disallow** for parameter and tracking URLs.
  Disallow stops crawling, so the URLs vanish from the logs and from GSC and you lose
  the ability to measure the fix; noindex,follow keeps them visible, un-indexed, and
  still passing equity.
- **Do not nofollow legitimate outbound links** : that is the off-page skill's territory
  and over-tagging is a myth-driven anti-pattern.
- **Do not block an IP without checking it.** `ipinfo.io/<ip>` first: datacenter, block;
  residential, rate-limit instead. A wrong block costs real customers.
- **Crawl budget is a large-site problem.** Under a few thousand URLs, frame waste
  findings as hygiene, not as the reason rankings are flat.

## 7. What good looks like
Report it. A site whose robots.txt always returned 200, whose Googlebot share is 40% of
automated traffic and whose 5xx rate is 0.0% has earned a `good` finding on those
dimensions, with the numbers. A report of only problems is not an audit, it is a sales
document.
