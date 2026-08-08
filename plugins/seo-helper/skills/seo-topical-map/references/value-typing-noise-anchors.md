# Value typing · anchor-pattern library · noise/QA pass

Three mechanical references the map applies before delivery. Value typing gates which
templates a value may take; the anchor library derives topic titles + the "traceable
pattern" signal (QDP rule #4) from real keyword clusters; the noise pass keeps
contaminated rows out of the deliverable.

---

## 1. Value typing → template gating

Every Value gets one **type**. A template is only assigned to a Value if its type
allows it — this is what prevents "How to Unclog a Water Heater"-class nonsense.

| Type | Meaning | Gets | Never gets |
|---|---|---|---|
| FIXTURE | standalone physical unit (Water Heater, Furnace) | Install, Repair, Cost, Types, Problems, Symptoms, Buying/Best, Maintenance | Unclog/Snake (drain-specific) |
| DRAIN | anything that can clog (Drain, Toilet, Sink) | + Unclog, Snake, Flush | — |
| COMPONENT | part of a larger unit (Capacitor, Valve) | Install, Fix, Comparison, Wiring | Unclog, standalone "problems overview" |
| MATERIAL | substance/material choice (Copper Pipe, PEX) | Types, Comparison, Install, Cost | Unclog, Cause, Symptoms |
| SYSTEM | multi-component system (Sewer System, Ductless) | How It Works, Types, Cost, Maintenance, Troubleshooting | — |
| SERVICE | offering whose name IS an action (AC Repair, Repiping) | Cost, Maintenance/Service-hub, General/Guide, Buying/Best (company), Career/Licensing | Fix/Replace/Install/Leak/Noise/Frozen/Symptoms/Unclog — the value already IS that action |
| PROBLEM | a named issue (Frozen Pipe, Low Water Pressure) | Troubleshooting hub, Cause, Cost, Prevent, Symptoms | Install, Buying/Best |
| EMERGENCY | urgent problem variant | PROBLEM set + urgency framing | — |
| TOOL | a physical tool (Plunger, Snake) | Buying/Best, How-to-use, Types, Cost | Install (tools aren't installed) |
| METHOD | a technique/connection method (PEX Crimp) | Guide, Comparison, Buying/Best (tool) | Repair/Symptoms |
| ROLE | a person/job (Journeyman Plumber) | Licensing/Career, Cost (to hire), Signs-of-a-good-one, Requirements | Install/Repair/Cost-to-fix |
| CERT | a certification | Licensing/Career, Cost, Requirements | everything physical |
| STANDARD | a code/requirement | Codes & Requirements guide | everything else |
| SPACE | a room/area (Kitchen, Bathroom) | Room-by-room guide | — |

Extend per niche in Phase 6 — the set above came from a home-services build; a SaaS
or B2B entity needs its own types (FEATURE, INTEGRATION, PRICING_TIER, USE_CASE,
COMPETITOR, ROLE/PERSONA, …).

---

## 2. Anchor-pattern library (derive title + category + the "pattern" signal)

Match each keyword in a value's cluster against these patterns (first match wins) to
bucket it and generate a title. `{V}` = the value's display name. **Use word
boundaries on both sides of short/ambiguous tokens** — an unguarded `\bfix` matches
inside "fixture"; `hum` matches inside "dehumidifier"; `cause` matches inside
"because". Test the pattern against the actual keyword pool before trusting it.

```
install_cost : install.*cost|cost.*install                → Cost      "How Much Does {V} Installation Cost?"
replace_cost : replac.*cost|cost.*replac                  → Cost      "{V} Replacement Cost"
repair_cost  : repair.*cost|cost.*repair                  → Cost      "How Much Does {V} Repair Cost?"
cost         : \bcost\b|\bprice\b|how much|\bcheap\b       → Cost      "How Much Does {V} Cost?"
leak         : \bleak|leaking|dripping                     → Problem   "Why Is My {V} Leaking?"
not_working  : not working|won.?t (start|turn)|stopped     → Trouble   "{V} Not Working: Causes & Fixes"
noise        : \b(noise|loud|rattl\w*|bang\w*|hum(ming|s)?|rumbl\w*|squeal\w*|grind\w*|vibrat\w*)\b → Problem "{V} Making Noise: Causes & Fixes"
frozen       : frozen|freezing|freeze up|ice[ds]? up       → Trouble   "{V} Freezing Up: What to Do"
symptoms     : symptom|\bsigns\b|failing|gone bad|\btest\b → Symptoms  "Signs of a Bad {V} (and How to Test)"
unclog       : unclog|\bclog|blocked|unblock               → Fix       "How to Unclog a {V}"  [DRAIN only]
clean        : \bclean(ing)?\b                             → Maint     "How to Clean a {V}"
maintain     : mainten\w*|tune.?up|\bservice\b             → Maint     "{V} Maintenance Guide"
install      : \binstall\w*|\bmount\b                      → Install   "How to Install a {V}"
replace      : \breplac\w*|\bswap\b                        → Install   "When & How to Replace a {V}"
repair       : \brepair\b|\bfix(ing|ed)?\b|troubleshoot    → Fix       "How to Fix a {V}"
sizing       : \bsizes?\b|dimension|capacity|how many      → Types     "{V} Sizes & Sizing Guide"
comparison   : \bvs\b|versus|difference between            → Types     "{V} vs Alternatives: Which Is Better?"
types        : \btypes?\b|\bkinds?\b                       → Types     "Types of {V}"
best         : \bbest\b|top \d|\brated\b|reviews?          → Buying    "The Best {V}s (Buying Guide)"
efficiency   : efficien\w*|\bseer\b|energy|\bsave\b         → Buying    "Most Efficient {V}s: Are They Worth It?"
prevent      : prevent|avoid|winteriz\w*                   → Maint     "How to Prevent {V} Problems"
cause        : \bcause[sd]?\b|\breason\b|\bwhy\b            → Problem   "What Causes {V} Problems?"
damage       : insurance|warranty|does .* cover|worth it   → Problem   "Is {V} Damage Covered? Costs & Consequences"
how_works    : how (does|do) .* work                       → General   "How Does a {V} Work?"
code         : \bcode\b|regulation|\bpermit\b              → General   "{V} Codes & Requirements"
career       : licens\w*|certif\w*|apprentice|salary       → General   "{V}: Licensing, Training & Career"
brands       : {curated real brand names in this niche}    → Buying    "Best {V} Brands Compared"  [FIXTURE/COMPONENT/MATERIAL/TOOL/DRAIN only]
(no match)   : —                                           → General   "{V}: Complete Guide"
```

A value whose keyword cluster matches a coherent anchor set has a **traceable search
pattern** (QDP rule #4). The page/heading/drop decision itself is then made by QDP —
see [qdp.md](qdp.md). (This replaces the old single-threshold "SV ≥ 30 OR cluster ≥
150" gate; that lives on only as a coarse pre-filter, never as the page decision.)

---

## 3. Noise / QA pass (always run before delivery)

Classify every generated topic row; **never silently delete a flagged row** — route
it to the **Review (Noise Removed)** sheet with a reason, keep it out of the main
deliverable. All checks are evidence-based against the actual generated data.

**a. Duplicate-adjacent-word artifact** — catches "furnace furnace", "AC Repair Repair Cost".
```python
import re
DUPRE = re.compile(r"\b(\w+)\s+\1\b", re.I)
is_dup = bool(DUPRE.search(title) or DUPRE.search(primary_keyword))
```

**b. Cross-product contamination** — a pull for Value A returns a keyword actually
about Value B, or an adjacent accessory that isn't the value. Build the term list per
build by auditing your OWN output (other values' names — esp. FIXTURE/DRAIN concrete
nouns — and near-but-distinct accessory/decor nouns); it is NOT a reusable universal list.
```python
def contaminated(value_name, title, primary_keyword, CONTAM_TERMS):
    vlow = value_name.lower()
    for term in CONTAM_TERMS:
        if term in vlow:            # never flag a value against its own name
            continue
        if term in primary_keyword.lower() or term in title.lower():
            return term
    return None
```

**c. Template / value-type mismatch (SERVICE-type values)** — a value whose name IS
an action ("AC Repair") still anchor-matches physical patterns (repair/leak/noise),
producing "How to Fix a AC Repair". Gate SERVICE-type values to a whitelist:
```python
SERVICE_ANCHOR_OK = {"cost","install_cost","replace_cost","repair_cost","maintain",
                     "best","efficiency","career","code","general","damage","cause","how_works"}
def service_mismatch(value_type, anchor):
    return value_type == "SERVICE" and anchor not in SERVICE_ANCHOR_OK
```
Verify it doesn't over-prune: "Is Repiping Damage Covered?" (anchor=`damage`) is about
insurance/cost, not a physical malfunction — it belongs on the whitelist.

**Applying the pass:** split each value's rows into kept vs noisy; recompute every
downstream count (Blog/Landing, category list, entity totals) from the **kept** set
only; write the noisy set to the Review sheet
(Entity · Attribute · Value · Category · Title · Slug · Keyword · SV · Page Type · Reason).
No API cost — pure local re-processing; safe to re-run whenever clustering changes.
