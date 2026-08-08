#!/usr/bin/env python3
"""backlink_trust.py : turn a backlinks export into the off-page TRUST picture that explains
suppression: over-optimized exact-match anchors, spam-directory clusters, and a conservative
DOMAIN-level disavow candidate list.

Input is a CSV export from Ahrefs, Semrush, OR the DataForSEO backlinks MCP (column names are
matched case-insensitively). The direct AHREFS_API_KEY / SEMRUSH_API_KEY in .env are EMPTY, so
this reads a CSV the user provides OR one saved from the DataForSEO MCP : it does NOT call
Ahrefs/Semrush directly (see references/data-sources-and-tools.md).

Heuristics only (a starting point for human review, NEVER an auto-disavow):
  - exact-match anchor share (brand term supplied via --brand) -> over-optimization signal
  - referring-domain toxicity from spam patterns + (optional) a spam-score/DR column
  - disavow candidates emitted at DOMAIN level (domain:) : the safe granularity

Usage: python3 backlink_trust.py --csv backlinks.csv --brand "brand name" \
          --money "aluminium windows,sliding doors" [--out backlinks_analysis.json] [--disavow disavow.txt]
Stdlib only."""
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from urllib.parse import urlparse

def _norm(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
ALIASES={'source_url':{'sourceurl','referringpageurl','urlfrom','pagefrom','source','referringpage'},
         'anchor':{'anchor','anchortext','anchors'},
         'domain':{'domain','referringdomain','sourcedomain','domainfrom'},
         'score':{'domainrating','dr','authorityscore','as','spamscore','domaininlinkrank','rank'},
         'dofollow':{'dofollow','follow','nofollow','type','linktype'}}
def colmap(h):
    m={}
    for i,c in enumerate(h):
        n=_norm(c)
        for k,al in ALIASES.items():
            if n in al and k not in m: m[k]=i
    return m
def reg_domain(u):
    if not u: return ''
    if '://' not in u: u='http://'+u
    net=urlparse(u).netloc.lower().lstrip('www.')
    return net
SPAM_PAT=re.compile(r'(seo|directory|backlink|linklist|bookmark|articledir|guestpost|casino|porn|replica|'
                    r'\.xyz$|\.top$|\.buzz$|\.click$|forum.*profile|/tag/|pastebin|000webhost)', re.I)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--csv', required=True); ap.add_argument('--brand', default='')
    ap.add_argument('--money', default=''); ap.add_argument('--out'); ap.add_argument('--disavow')
    a=ap.parse_args()
    money=[m.strip().lower() for m in a.money.split(',') if m.strip()]
    brand_rx=re.compile('|'.join(re.escape(b.strip()) for b in a.brand.split('|') if b.strip()), re.I) if a.brand else None
    rows=list(csv.reader(open(a.csv, newline='', encoding='utf-8-sig')))
    hi=0
    for i,r in enumerate(rows[:5]):
        if colmap(r): hi=i; break
    cm=colmap(rows[hi]); data=rows[hi+1:]
    anchors=Counter(); dom_links=defaultdict(int); dom_score={}; toxic=set(); classes=Counter()
    total=0
    for r in data:
        if not any(c.strip() for c in r): continue
        total+=1
        anc=(r[cm['anchor']] if 'anchor' in cm and cm['anchor']<len(r) else '').strip()
        dom=(r[cm['domain']] if 'domain' in cm and cm['domain']<len(r) else '')
        if not dom and 'source_url' in cm and cm['source_url']<len(r): dom=reg_domain(r[cm['source_url']])
        dom=reg_domain(dom) if dom and '.' in dom else dom
        if anc: anchors[anc.lower()]+=1
        if dom: dom_links[dom]+=1
        sc=None
        if 'score' in cm and cm['score']<len(r):
            try: sc=float(re.sub(r'[^0-9.]','',r[cm['score']]) or 'nan')
            except: sc=None
        if sc is not None and dom: dom_score[dom]=sc
        # classify anchor
        al=anc.lower()
        if brand_rx and brand_rx.search(al): classes['brand']+=1
        elif any(m in al for m in money): classes['exact_money']+=1
        elif al in ('','click here','here','read more','link','website','visit','this website'): classes['generic']+=1
        elif re.match(r'^https?://|^www\.', al): classes['url']+=1
        else: classes['other']+=1
        src=(r[cm['source_url']] if 'source_url' in cm and cm['source_url']<len(r) else dom)
        if dom and (SPAM_PAT.search(src or '') or SPAM_PAT.search(dom)): toxic.add(dom)
        if dom and sc is not None and sc <= 5: toxic.add(dom) # very low authority
    exact_share=round(100*classes.get('exact_money',0)/total,1) if total else 0
    brand_share=round(100*classes.get('brand',0)/total,1) if total else 0
    res={'total_backlinks_rows':total,'referring_domains':len(dom_links),
         'anchor_classes':dict(classes),'exact_match_money_anchor_pct':exact_share,
         'brand_anchor_pct':brand_share,
         'top_anchors':anchors.most_common(20),
         'toxic_domain_count':len(toxic),
         'toxic_domain_share_pct':round(100*len(toxic)/len(dom_links),1) if dom_links else 0,
         'disavow_candidates_sample':sorted(toxic)[:50],
         'flags':[]}
    if exact_share>=15: res['flags'].append(f"Exact-match money anchors {exact_share}% : over-optimized (natural profiles are brand/URL/generic heavy). Manipulation signal that suppresses trust.")
    if brand_share<30 and total>20: res['flags'].append(f"Brand anchors only {brand_share}% : a trusted entity's profile is brand-dominant; this looks built, not earned.")
    if res['toxic_domain_share_pct']>=20: res['flags'].append(f"{res['toxic_domain_share_pct']}% of referring domains match spam/low-authority patterns : an active suppression risk; review for disavow.")
    print(json.dumps({k:v for k,v in res.items() if k!='disavow_candidates_sample'}, indent=2))
    print(f"\n[disavow] {len(toxic)} domain-level candidates (review before use).")
    if a.disavow and toxic:
        with open(a.disavow,'w') as f:
            f.write("# Conservative DOMAIN-level disavow candidates : REVIEW MANUALLY before submitting.\n")
            for d in sorted(toxic): f.write(f"domain:{d}\n")
        print(f"WROTE {a.disavow}")
    if a.out: json.dump(res, open(a.out,'w'), indent=2); print(f"WROTE {a.out}")

if __name__=='__main__': main()
