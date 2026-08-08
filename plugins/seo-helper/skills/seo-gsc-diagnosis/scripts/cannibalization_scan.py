#!/usr/bin/env python3
"""cannibalization_scan.py — find cannibalization CANDIDATES from a GSC query x page export.

The GSC query_search_analytics call with dimensions ["query","page"] is usually too large to read
inline and gets saved to a file shaped like:

    query | page | Clicks | Impressions | CTR | Position

This script groups by query and reports queries served by 2+ distinct site URLs (anchors like
#toc-3 and ?utm_* params are stripped so the same page isn't double-counted), ranked by number of
competing pages, then by total impressions.

IMPORTANT: the output is a CANDIDATE list, not a finding. A query showing N pages is only real
cannibalization if those pages are live 200s that self-canonical. Feed the competing URLs into
check_urls.sh to verify before claiming anything. Brand/navigational queries naturally surface many
URLs (sitelinks) and are usually NOT a problem — eyeball the query.

Usage:
    cannibalization_scan.py <gsc_query_page_export.txt> [--min-pages 2] [--top 40]
"""
import argparse
import re
import sys
from collections import defaultdict


def normalize(url: str) -> str:
    return re.split(r"[?#]", url.strip(), maxsplit=1)[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min-pages", type=int, default=2,
                    help="minimum distinct pages for a query to be flagged (default 2)")
    ap.add_argument("--top", type=int, default=40, help="rows to print (default 40)")
    args = ap.parse_args()

    pages = defaultdict(set)       # query -> set(normalized page)
    impressions = defaultdict(int) # query -> total impressions

    with open(args.file, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6 or not parts[1].startswith("http"):
                continue  # skip headers / separators / malformed rows
            query, page = parts[0], normalize(parts[1])
            try:
                imp = int(parts[3].replace(",", ""))
            except ValueError:
                continue
            pages[query].add(page)
            impressions[query] += imp

    flagged = [(q, ps, impressions[q]) for q, ps in pages.items()
               if len(ps) >= args.min_pages]
    flagged.sort(key=lambda x: (len(x[1]), x[2]), reverse=True)

    if not flagged:
        print("No queries served by %d+ distinct pages. No cannibalization candidates." % args.min_pages)
        return 0

    print("CANNIBALIZATION CANDIDATES (verify with check_urls.sh before claiming!)\n")
    print("%-6s %-10s  %s" % ("#pages", "impr", "query"))
    print("-" * 70)
    for q, ps, imp in flagged[: args.top]:
        print("%-6d %-10d  %s" % (len(ps), imp, q))
        for p in sorted(ps):
            print("           - %s" % p)
    print("\n%d candidate quer%s total. Next step: check_urls.sh on each set."
          % (len(flagged), "y" if len(flagged) == 1 else "ies"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
