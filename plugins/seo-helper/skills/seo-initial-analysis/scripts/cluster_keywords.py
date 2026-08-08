#!/usr/bin/env python3
"""Cluster DataForSEO keyword pulls into the engine-run master + clusters TSVs.

Usage:
    python cluster_keywords.py <raw_dir> [out_dir]

<raw_dir> holds the saved DataForSEO MCP responses, one JSON per seed
(engine-run/raw/*.json). Shapes vary by endpoint, so the extractor walks each JSON
recursively and pulls every {keyword, search_volume, difficulty, cpc, intent} it
finds. Keywords dedupe by lowercased text (max search volume wins). Each keyword's
cluster is the seed file (stem) where it carried the most volume — a natural,
deterministic clustering that needs no extra SERP calls. Outputs into out_dir:
  master_by_sv.tsv   keyword  search_volume  kd  cpc  intent  cluster   (SV desc)
  clusters.tsv       cluster  n_keywords  aggregate_sv  top_keyword  top_sv
"""
import sys, os, json, glob

def _num(v):
    try:
        return 0.0 if v is None else float(v)
    except (TypeError, ValueError):
        return 0.0

def _dig(d, path):
    if isinstance(path, str):
        path = (path,)
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur

def walk(obj, stem, rows):
    if isinstance(obj, dict):
        kw = obj.get("keyword")
        if isinstance(kw, str) and kw.strip():
            sv = _num(_dig(obj, "search_volume") or _dig(obj, ("keyword_info", "search_volume")))
            kd = _num(_dig(obj, "keyword_difficulty") or _dig(obj, ("keyword_properties", "keyword_difficulty")))
            cpc = _num(_dig(obj, "cpc") or _dig(obj, ("keyword_info", "cpc")))
            intent = (_dig(obj, ("search_intent_info", "main_intent")) or _dig(obj, "main_intent") or "")
            rows.append((kw.strip(), sv, kd, cpc, intent, stem))
        for v in obj.values():
            walk(v, stem, rows)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, stem, rows)

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python cluster_keywords.py <raw_dir> [out_dir]")
    raw_dir = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else (os.path.dirname(raw_dir.rstrip("/")) or ".")
    rows = []
    for f in sorted(glob.glob(os.path.join(raw_dir, "*.json"))):
        stem = os.path.splitext(os.path.basename(f))[0]
        try:
            data = json.load(open(f, encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"skip {f}: {e}")
            continue
        walk(data, stem, rows)

    # dedupe by lowercased keyword; keep the record with the max search volume,
    # backfilling kd/cpc/intent from whichever record has them.
    best = {}
    for kw, sv, kd, cpc, intent, stem in rows:
        k = kw.lower()
        cur = best.get(k)
        if cur is None or sv > cur[1]:
            if cur:
                kd = kd or cur[2]; cpc = cpc or cur[3]; intent = intent or cur[4]
            best[k] = (kw, sv, kd, cpc, intent, stem)
        else:
            best[k] = (cur[0], cur[1], cur[2] or kd, cur[3] or cpc, cur[4] or intent, cur[5])
    master = sorted(best.values(), key=lambda r: r[1], reverse=True)

    os.makedirs(out_dir, exist_ok=True)
    mpath = os.path.join(out_dir, "master_by_sv.tsv")
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write("keyword\tsearch_volume\tkd\tcpc\tintent\tcluster\n")
        for kw, sv, kd, cpc, intent, stem in master:
            fh.write(f"{kw}\t{int(sv)}\t{kd:g}\t{cpc:g}\t{intent}\t{stem}\n")

    # cluster aggregates (cluster = seed file stem)
    agg = {}
    for kw, sv, kd, cpc, intent, stem in master:
        a = agg.setdefault(stem, {"n": 0, "sv": 0.0, "top": kw, "top_sv": sv})
        a["n"] += 1
        a["sv"] += sv
        if sv > a["top_sv"]:
            a["top"], a["top_sv"] = kw, sv
    clusters = sorted(agg.items(), key=lambda kv: kv[1]["sv"], reverse=True)
    cpath = os.path.join(out_dir, "clusters.tsv")
    with open(cpath, "w", encoding="utf-8") as fh:
        fh.write("cluster\tn_keywords\taggregate_sv\ttop_keyword\ttop_sv\n")
        for stem, a in clusters:
            fh.write(f"{stem}\t{a['n']}\t{int(a['sv'])}\t{a['top']}\t{int(a['top_sv'])}\n")

    print(f"{len(master)} keywords, {len(clusters)} clusters -> {mpath}, {cpath}")

if __name__ == "__main__":
    main()
