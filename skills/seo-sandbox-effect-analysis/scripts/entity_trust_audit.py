#!/usr/bin/env python3
"""entity_trust_audit.py : score the homepage's ENTITY/brand-trust signals, the #1 invisible
sandbox cause ("dead brand entity trap": Google has indexed the site but has NOT established the
business as a trusted entity, so it will not rank it for non-brand demand).

Reads the homepage HTML (live via --url, or a saved snapshot via --file) and extracts the
Organization / LocalBusiness JSON-LD plus a few HTML signals, then reports what's PRESENT vs
MISSING against the entity-establishment checklist. It does NOT invent facts : every line is
either found in the markup or flagged absent.

Also sanity-checks aggregateRating (a fabricated/hardcoded 5.0 across the site is a spam-policy
risk found in real audits : see references/methodology.md), which actively suppresses trust.

Usage: python3 entity_trust_audit.py --url https://site/ [--out entity.json]
       python3 entity_trust_audit.py --file homepage.html
Stdlib only (urllib). For anti-bot sites, pass --file with a snapshot fetched via the
SCRAPINGBEE_KEY path (see references/data-sources-and-tools.md)."""
import argparse, json, re, sys, urllib.request

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
def fetch(url):
    req=urllib.request.Request(url, headers={'User-Agent':UA,'Cache-Control':'no-cache'})
    return urllib.request.urlopen(req, timeout=25).read().decode('utf-8','ignore')

def jsonld_blocks(html):
    out=[]
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S|re.I):
        raw=m.group(1).strip()
        try: out.append(json.loads(raw))
        except Exception:
            # tolerate trailing commas / unescaped newlines
            try: out.append(json.loads(re.sub(r',\s*([}\]])', r'\1', raw.replace('\n',' '))))
            except Exception: out.append({'_parse_error':raw[:200]})
    return out

def flatten(objs):
    for o in objs:
        if isinstance(o, dict):
            if '@graph' in o and isinstance(o['@graph'], list):
                for g in o['@graph']: yield g
            else: yield o
        elif isinstance(o, list):
            for g in o: yield g

ORG_TYPES={'organization','localbusiness','store','corporation','onlinestore'}
def is_org(t):
    if isinstance(t, list): return any(str(x).lower() in ORG_TYPES or 'business' in str(x).lower() for x in t)
    return str(t).lower() in ORG_TYPES or 'business' in str(t).lower()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--url'); ap.add_argument('--file'); ap.add_argument('--out')
    a=ap.parse_args()
    if a.file: html=open(a.file, encoding='utf-8', errors='ignore').read()
    elif a.url: html=fetch(a.url)
    else: ap.error('pass --url or --file')

    blocks=jsonld_blocks(html); nodes=list(flatten(blocks))
    org=next((n for n in nodes if isinstance(n,dict) and is_org(n.get('@type'))), None)
    res={'source': a.url or a.file, 'jsonld_blocks': len(blocks),
         'org_schema_found': bool(org), 'signals': {}, 'flags': []}
    def sig(k, present, detail=''): res['signals'][k]={'present':bool(present),'detail':detail}

    if org:
        sig('name', org.get('name'), str(org.get('name') or ''))
        same=org.get('sameAs'); sig('sameAs', bool(same), f"{len(same) if isinstance(same,list) else (1 if same else 0)} profile link(s)")
        sig('logo', org.get('logo'), '')
        sig('founder', org.get('founder') or org.get('founders'), '')
        sig('alternateName', org.get('alternateName'), str(org.get('alternateName') or ''))
        addr=org.get('address'); sig('address(NAP)', bool(addr), '')
        sig('telephone', org.get('telephone') or org.get('contactPoint'), '')
        # aggregateRating sanity
        ar=org.get('aggregateRating')
        if ar and isinstance(ar, dict):
            rv=str(ar.get('ratingValue','')); rc=str(ar.get('reviewCount') or ar.get('ratingCount') or '')
            sig('aggregateRating', True, f"{rv} / {rc}")
            if rv in ('5','5.0') :
                res['flags'].append(f"aggregateRating is a perfect {rv} ({rc}) : verify it is REAL and per-entity, "
                                    "not a hardcoded sitewide value (fabricated ratings are a spam-policy / trust risk).")
        else:
            sig('aggregateRating', False, '')
        # missing-signal flags
        if not same: res['flags'].append("No sameAs : the entity has no declared links to its own social/authoritative profiles (KG starvation).")
        if not org.get('founder') and not org.get('founders'):
            res['flags'].append("No founder/person entity : weak for E-E-A-T, especially YMYL.")
    else:
        res['flags'].append("NO Organization/LocalBusiness JSON-LD on the homepage : Google has no structured "
                            "entity anchor. This is the classic 'dead brand entity trap' starting point.")
    # HTML-level corroboration (independent of schema, which is authorable)
    title_m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S|re.I)
    title_txt = (title_m.group(1) if title_m else "") or ""
    res['html_signals']={
        'title': title_txt.strip()[:140],
        'has_about_link': bool(re.search(r'href=["\'][^"\']*about', html, re.I)),
        'mentions_founded_or_since': bool(re.search(r'\b(founded|established|since)\b\s*\d{4}', html, re.I)),
    }
    print(json.dumps(res, indent=2))
    if a.out: json.dump(res, open(a.out,'w'), indent=2); print(f"\nWROTE {a.out}", file=sys.stderr)

if __name__=='__main__': main()
