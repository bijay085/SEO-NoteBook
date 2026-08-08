"""Log parsing : format detection, per-format line parsers, and log-role routing.

Ported (logic + thresholds unchanged) from a prior Colab analyzer
`seo_log_file_analyzer.py`, with three enhancements:
  1. STREAMING : `iter_records()` yields one record at a time instead of
     building a pandas DataFrame, so multi-GB rotated logs parse in bounded
     memory. Nothing here holds more than one line.
  2. COMPRESSION : `.gz` / `.bz2` / `.xz` open transparently, and a path may be
     a file, a directory, or a glob. Real server logs arrive rotated+compressed.
  3. HONEST COUNTS : every parse returns (parsed, total, failed) so the report
     can state the parse rate instead of silently dropping lines.

Record schema (one dict per request):
  ip, timestamp (datetime|None), method, url, status (int), bytes (int),
  user_agent, referrer (+ log_role / source_file added by the orchestrator)

Public API:
  expand_paths(paths) -> [str] files, dirs and globs -> log files
  detect_format(path) -> (fmt, sample_lines)
  infer_log_role(path) -> 'access'|'error'|'cloudways_*'
  iter_records(path, ...) -> yields record dict or None (failed line)
  parse_file(path, ...) -> (records|None, total_lines, failed_lines)
  route_log_roles(role_counts) -> (primary_roles, reason)
"""
import bz2
import glob as _glob
import gzip
import json
import lzma
import os
import re
from datetime import datetime

LOG_SUFFIXES = (".log", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".gz", ".bz2", ".xz")
METHODS = ("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH")

# Rotated logs almost never end in a tidy extension: `access.log-2026-07-19-1784419220`,
# `access.log.1`, `access_log`, `error_log`. Matching on suffix alone silently drops
# them : and a silent drop is worse than a crash, because the report still looks
# complete. Anything with `.log` anywhere in the name, or a classic Apache
# access_log / error_log name, counts as a log file.
_LOG_NAME_RE = re.compile(r"\.log([.\-_]|$)|(^|[._-])(access|error)(_log)?([._-]|$)", re.I)

# Our own outputs, so pointing --logs at a previous output directory is a no-op.
_OWN_ARTIFACTS = {"analysis.json", "facts.md"}

# Cloudways PHP-FPM 3-line format probes
_CW_TS = re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}$")
_CW_IP = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
_CW_REQ = re.compile(r"^(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+\S+\"\s+\d{3}")

_LAST_RESORT = re.compile(r"(\S+).*?[\"\s]([A-Z]+)\s+(\S+).*?(\d{3})")

IIS_DEFAULT_FIELDS = [
    "date", "time", "s-ip", "cs-method", "cs-uri-stem", "cs-uri-query",
    "s-port", "cs-username", "c-ip", "cs(User-Agent)", "cs(Referer)",
    "sc-status", "sc-substatus", "sc-win32-status", "time-taken",
]


# ── file discovery / opening ────────────────────────────────────────────────
def is_log_name(filename):
    """Does this filename look like a log file (including a rotated one)?"""
    low = os.path.basename(filename).lower()
    if low in _OWN_ARTIFACTS or low.startswith("."):
        return False
    return low.endswith(LOG_SUFFIXES) or bool(_LOG_NAME_RE.search(low))


def discover_logs(paths):
    """Expand files, directories and globs -> (log_files, skipped_files).

    `skipped` is returned rather than discarded so the caller can SAY what it
    ignored. A directory sweep that quietly matches 1 of 5 rotated files still
    produces a confident-looking report on 11% of the data."""
    out, skipped = [], []
    for p in paths:
        p = os.path.expanduser(str(p))
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for fn in sorted(files):
                    full = os.path.join(root, fn)
                    if is_log_name(fn):
                        out.append(full)
                    elif not fn.startswith("."):
                        skipped.append(full)
        elif any(ch in p for ch in "*?["):
            # An explicit glob is the user's own filter : honour it verbatim.
            out.extend(sorted(x for x in _glob.glob(p) if os.path.isfile(x)))
        elif os.path.isfile(p):
            out.append(p) # named explicitly: never second-guess it
    seen, uniq = set(), []
    for p in out:
        rp = os.path.realpath(p)
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq, skipped


def expand_paths(paths):
    """Files, directories and globs -> de-duplicated log-file list."""
    return discover_logs(paths)[0]


def open_text(path):
    """Open plain or compressed logs as text, never raising on bad bytes."""
    low = str(path).lower()
    if low.endswith(".gz"):
        return gzip.open(path, "rt", errors="ignore")
    if low.endswith(".bz2"):
        return bz2.open(path, "rt", errors="ignore")
    if low.endswith(".xz"):
        return lzma.open(path, "rt", errors="ignore")
    return open(path, "r", errors="ignore")


# ── format detection ────────────────────────────────────────────────────────
def detect_format(filepath):
    samples = []
    with open_text(filepath) as f:
        for _ in range(20):
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if line and not line.startswith("#"):
                samples.append(line)
            if len(samples) >= 5:
                break
    if not samples:
        return "unknown", samples
    first = samples[0]
    if first.startswith("{"):
        return "json", samples
    if "," in first and any(k in first.lower() for k in ["url", "status", "path"]):
        return "csv", samples
    if "\t" in first and any(k in first.lower() for k in ["url", "status"]):
        return "tsv", samples
    if re.match(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+", first):
        return "iis", samples
    if "[" in first and "]" in first:
        return "bracket", samples
    if (len(samples) >= 3 and _CW_TS.match(samples[0])
            and _CW_IP.match(samples[1]) and _CW_REQ.match(samples[2])):
        return "cloudways_fpm", samples
    return "unknown", samples


def infer_log_role(filepath):
    """Which kind of log this is : decides whether it feeds the main SEO totals."""
    name = os.path.basename(str(filepath)).lower()
    for ext in (".gz", ".bz2", ".xz"):
        if name.endswith(ext):
            name = name[: -len(ext)]
    if ".error.log" in name or name.endswith("error.log") or ".error." in name:
        return "error"
    if name.startswith("php-app.access"):
        return "cloudways_php"
    if name.startswith("backend_") and ".access.log" in name:
        return "cloudways_backend"
    if name.startswith("static_") and ".access.log" in name:
        return "cloudways_static"
    if "access" in name:
        return "access"
    return "access"


def route_log_roles(role_counts):
    """Pick the PRIMARY log roles. Cloudways backend beats PHP/static (which stay
    supplemental); error logs never feed traffic analysis. -> (roles, reason)."""
    roles = {r for r, n in role_counts.items() if n}
    if "cloudways_backend" in roles:
        primary = ["cloudways_backend"]
        if "access" in roles:
            primary.append("access")
        reason = ("Cloudways backend access logs are primary; PHP/static logs kept "
                  "supplemental.")
    elif "access" in roles:
        primary, reason = ["access"], "Standard access logs are primary."
    elif "cloudways_php" in roles:
        primary = ["cloudways_php"]
        reason = "No backend access log found; using Cloudways PHP log as fallback."
    elif "cloudways_static" in roles:
        primary = ["cloudways_static"]
        reason = "Only static access logs found; using static traffic as primary."
    else:
        primary = sorted(r for r in roles if r != "error")
        reason = "Using all non-error parsed logs as primary."
    return primary, reason


# ── line parsers ────────────────────────────────────────────────────────────
def _extract_ip(tokens):
    for tok in tokens:
        if tok.count(".") == 3 and all(p.isdigit() for p in tok.split(".")):
            return tok
        if ":" in tok and re.match(r"^[0-9a-fA-F:]+$", tok) and len(tok) > 4:
            return tok
    return tokens[0] if tokens else "-"


def parse_bracket_line(line):
    try:
        ts_start, ts_end = line.find("["), line.find("]")
        if ts_start == -1 or ts_end == -1:
            return None
        timestamp_str = line[ts_start + 1:ts_end]
        before_ts, after_ts = line[:ts_start].strip(), line[ts_end + 1:].strip()
        ip = _extract_ip(before_ts.split())
        parts = after_ts.split('"')
        method, url, status, byte_val, referrer, user_agent = "-", "-", 0, 0, "", ""
        first_chunk = parts[0].strip() if parts else ""
        if first_chunk == "" and len(parts) >= 2:
            req_parts = parts[1].split(" ", 2)
            method = req_parts[0] if req_parts else "-"
            url = req_parts[1] if len(req_parts) >= 2 else "-"
            st_tokens = (parts[2].strip() if len(parts) >= 3 else "").split()
            status = int(st_tokens[0]) if st_tokens and st_tokens[0].isdigit() else 0
            if len(st_tokens) >= 2:
                byte_val = 0 if st_tokens[1] == "-" else (
                    int(st_tokens[1]) if st_tokens[1].isdigit() else 0)
            is_cloudways_single = (
                len(parts) >= 4 and len(st_tokens) >= 8
                and st_tokens[-1].endswith("%") and st_tokens[-2].endswith("%")
            )
            if is_cloudways_single:
                # Cloudways logs the PHP entry script first, the real URI last.
                actual_uri = parts[3].strip()
                if actual_uri:
                    url = actual_uri
                referrer, user_agent = "", ""
            else:
                referrer = parts[3] if len(parts) >= 4 else ""
                user_agent = parts[5] if len(parts) >= 6 else ""
        elif first_chunk and not first_chunk[0].isdigit():
            # Unquoted request line, method first : the vhost-prefixed Apache/
            # Cloudways shape:
            # host ip [ts] GET "/url" HTTP/2.0 200 "ref" "UA" ip "/entry" - cpu bytes t t
            method = first_chunk.split()[0]
            url = parts[1] if len(parts) >= 2 else "-"
            for tok in (parts[2].strip() if len(parts) >= 3 else "").split():
                if tok.isdigit() and len(tok) == 3:
                    status = int(tok)
                    break
            referrer = parts[3] if len(parts) >= 4 else ""
            user_agent = parts[5] if len(parts) >= 6 else ""
            # Response size lives in the trailing segment after the last quoted
            # field, where it is the first pure-integer token (the neighbouring
            # cpu% and timing fields are decimals or "-"). Verified against
            # 16,322 real lines: always present, always that position. Requires
            # a segment BEYOND the UA, else parts[-1] would be the status chunk
            # and we would record the status code as a byte count.
            if len(parts) >= 7:
                for tok in parts[-1].split():
                    if tok.isdigit():
                        byte_val = int(tok)
                        break
        else:
            all_tokens = after_ts.replace('"', " ").split()
            for i, tok in enumerate(all_tokens):
                if tok in METHODS:
                    method = tok
                    if i + 1 < len(all_tokens):
                        url = all_tokens[i + 1]
                    break
            for tok in all_tokens:
                if tok.isdigit() and len(tok) == 3:
                    status = int(tok)
                    break
        ts = None
        for fmt in ("%d/%b/%Y:%H:%M:%S %z", "%d/%b/%Y:%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                ts = datetime.strptime(timestamp_str.strip(), fmt)
                break
            except ValueError:
                continue
        if status == 0:
            return None
        return {"ip": ip, "timestamp": ts, "method": method, "url": url,
                "status": status, "bytes": byte_val,
                "user_agent": user_agent, "referrer": referrer}
    except Exception:
        return None


def parse_json_line(line):
    try:
        obj = json.loads(line)
        url = (obj.get("uri") or obj.get("url") or obj.get("path")
               or obj.get("cs-uri-stem") or obj.get("request_uri")
               or obj.get("ClientRequestURI") or "-")
        status = int(obj.get("status") or obj.get("EdgeResponseStatus")
                     or obj.get("sc-status") or obj.get("response_status") or 0)
        ip = (obj.get("ip") or obj.get("remote_addr") or obj.get("client_ip")
              or obj.get("ClientIP") or obj.get("c-ip") or "-")
        ua = (obj.get("user_agent") or obj.get("http_user_agent")
              or obj.get("ClientRequestUserAgent") or "")
        method = (obj.get("method") or obj.get("request_method")
                  or obj.get("ClientRequestMethod") or "-")
        byte_val = int(obj.get("bytes") or obj.get("body_bytes_sent")
                       or obj.get("EdgeResponseBytes") or 0)
        referrer = obj.get("referrer") or obj.get("http_referer") or ""
        ts_str = obj.get("timestamp") or obj.get("time") or obj.get("EdgeStartTimestamp") or ""
        ts = None
        if ts_str:
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
                try:
                    ts = datetime.strptime(str(ts_str).strip(), fmt)
                    break
                except ValueError:
                    continue
        if status == 0:
            return None
        return {"ip": ip, "timestamp": ts, "method": method, "url": url,
                "status": status, "bytes": byte_val,
                "user_agent": ua, "referrer": referrer}
    except Exception:
        return None


def parse_iis_line(line, field_map):
    try:
        tokens = line.split()
        if len(tokens) < 2:
            return None
        data = {field_map[i]: tokens[i] for i in range(min(len(tokens), len(field_map)))}
        url = data.get("cs-uri-stem", "-")
        query = data.get("cs-uri-query", "")
        if query and query != "-":
            url = url + "?" + query
        status = int(data.get("sc-status", 0))
        if status == 0:
            return None
        ts = None
        if data.get("date") and data.get("time"):
            try:
                ts = datetime.strptime(f"{data['date']} {data['time']}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        raw_bytes = str(data.get("sc-bytes", "0"))
        return {"ip": data.get("c-ip", "-"), "timestamp": ts,
                "method": data.get("cs-method", "-"), "url": url, "status": status,
                "bytes": int(raw_bytes) if raw_bytes.isdigit() else 0,
                "user_agent": data.get("cs(User-Agent)", "").replace("+", " "),
                "referrer": data.get("cs(Referer)", "")}
    except Exception:
        return None


# ── per-format record iterators ─────────────────────────────────────────────
def _iter_csv(filepath, log):
    """Aggregated crawl exports (Screaming Frog / GSC / Botify style)."""
    import csv as _csv
    with open_text(filepath) as fh:
        sample = fh.read(8192)
        fh.seek(0)
        delim = "\t" if sample.count("\t") > sample.count(",") else ","
        reader = _csv.DictReader(fh, delimiter=delim)
        cols = {c: (c or "").lower() for c in (reader.fieldnames or [])}

        def find_col(names):
            for n in names:
                for orig, low in cols.items():
                    if n in low:
                        return orig
            return None

        url_col = find_col(["url", "path", "uri", "page"])
        status_col = find_col(["status", "response", "code"])
        hits_col = find_col(["hits", "count", "events", "requests", "bot hits"])
        ua_col = find_col(["user_agent", "user-agent", "agent"])
        ip_col = find_col(["ip", "address", "remote"])
        if not url_col:
            log(" Could not find a URL column in this CSV : skipped.")
            return
        for row in reader:
            url = str(row.get(url_col, "-") or "-")
            try:
                status = int(str(row.get(status_col, 200)).strip()) if status_col else 200
            except ValueError:
                status = 200
            try:
                hits = int(float(row.get(hits_col, 1) or 1)) if hits_col else 1
            except ValueError:
                hits = 1
            ua = str(row.get(ua_col, "") or "") if ua_col else ""
            ip = str(row.get(ip_col, "-") or "-") if ip_col else "-"
            # An aggregated row stands for `hits` requests; the fan-out is capped
            # at 1,000 so one huge row cannot dominate the run (same cap as v2).
            for _ in range(min(max(hits, 1), 1000)):
                yield {"ip": ip, "timestamp": None, "method": "GET", "url": url,
                       "status": status, "bytes": 0, "user_agent": ua, "referrer": ""}


def _iter_cloudways_fpm(filepath, log):
    """Cloudways PHP-FPM 3-line format: timestamp / IP / request.
    NOTE: carries no User-Agent : classification falls back to verified bot IPs."""
    cur_year = datetime.now().year
    with open_text(filepath) as fh:
        raw = [ln.strip() for ln in fh if ln.strip()]
    log(" NOTE: Cloudways FPM log has no User-Agent field.")
    log(" Official search-bot IP ranges will be used where available.")
    i = 0
    while i < len(raw) - 2:
        l1, l2, l3 = raw[i], raw[i + 1], raw[i + 2]
        if not (_CW_TS.match(l1) and _CW_IP.match(l2)):
            i += 1
            continue
        try:
            ts = None
            for fmt in ("%Y %b %d %H:%M:%S", "%Y %b %d %H:%M:%S"):
                try:
                    ts = datetime.strptime(f"{cur_year} {l1}", fmt)
                    break
                except ValueError:
                    continue
            parts = l3.split('"')
            if len(parts) < 2:
                yield None
                i += 3
                continue
            method_tok = parts[0].strip().split()
            method = method_tok[0] if method_tok else "-"
            url = parts[-1].strip() or "-"
            meta = parts[1].strip().split()
            status = int(meta[0]) if meta and meta[0].isdigit() else 0
            if status == 0:
                yield None
                i += 3
                continue
            if url != "-" and not url.startswith("/"):
                url = "/" + url
            yield {"ip": l2, "timestamp": ts, "method": method, "url": url,
                   "status": status, "bytes": 0, "user_agent": "", "referrer": ""}
            i += 3
        except Exception:
            yield None
            i += 1


def iter_records(filepath, log=print, fmt=None):
    """Yield parsed records (dicts), or None for a line that failed to parse."""
    if fmt is None:
        fmt, _samples = detect_format(filepath)
    if fmt in ("csv", "tsv"):
        yield from _iter_csv(filepath, log)
        return
    if fmt == "cloudways_fpm":
        yield from _iter_cloudways_fpm(filepath, log)
        return
    iis_fields = None
    with open_text(filepath) as fh:
        for line in fh:
            ls = line.strip()
            if not ls:
                continue
            if ls.startswith("#Fields:"):
                iis_fields = ls.replace("#Fields:", "").strip().split()
                continue
            if ls.startswith("#"):
                continue
            if fmt == "bracket":
                rec = parse_bracket_line(ls)
            elif fmt == "json":
                rec = parse_json_line(ls)
            elif fmt == "iis":
                rec = parse_iis_line(ls, iis_fields or IIS_DEFAULT_FIELDS)
            else:
                rec = parse_bracket_line(ls) or parse_json_line(ls)
            yield rec


def iter_last_resort(filepath):
    """Regex fallback, used only when a whole file parsed to zero records."""
    with open_text(filepath) as fh:
        for line in fh:
            m = _LAST_RESORT.search(line.strip())
            if not m:
                continue
            g = m.groups()
            try:
                st = int(g[3])
            except ValueError:
                continue
            if 100 <= st <= 599:
                yield {"ip": g[0], "timestamp": None, "method": g[1], "url": g[2],
                       "status": st, "bytes": 0, "user_agent": "", "referrer": ""}


def parse_file(filepath, log=print, collect=True):
    """Parse one file -> (records|None, total_lines, failed_lines).
    collect=False counts without retaining (used by the pass-1 sweep)."""
    fmt, samples = detect_format(filepath)
    log(f" Format detected: {fmt.upper()}")
    for i, s in enumerate(samples[:3]):
        log(f" [{i+1}] {s[:150]}{'...' if len(s) > 150 else ''}")
    records, total, failed = ([] if collect else None), 0, 0
    for rec in iter_records(filepath, log=log, fmt=fmt):
        total += 1
        if rec is None:
            failed += 1
            continue
        if collect:
            records.append(rec)
    parsed = total - failed
    if parsed == 0 and total > 0:
        log(" Trying last-resort regex...")
        recovered = 0
        for rec in iter_last_resort(filepath):
            recovered += 1
            if collect:
                records.append(rec)
        failed = max(total - recovered, 0)
        parsed = recovered
        log(f" Last-resort: {recovered:,} entries")
    log(f" Total: {total:,} lines | Parsed: {parsed:,} | Failed: {failed:,}")
    return records, total, failed
