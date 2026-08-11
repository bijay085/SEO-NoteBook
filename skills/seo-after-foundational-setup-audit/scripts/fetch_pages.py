"""Forensic page-fetch engine for the After-Foundational-Setup deep audit.

Niche-agnostic. Fetches every target URL from config.json and emits measured
metrics used by report_data.py / build_html.py / build_xlsx.py. Never estimates : 
every number here is measured from the live HTML.

Usage: python fetch_pages.py [config.json]
Outputs (next to config): pages_metrics.json, sections.json

Metrics per page: raw/gzip bytes, inline CSS bytes (+ blocks), inline JS bytes,
external css/js counts, DOM node count, inline-SVG count, JSON-LD @types, native
<form> count, tracker-pattern hits, title/meta lengths, H1/H2, word count, the
heaviest top-level body sections (node/byte/word + label), and a cross-page
templated ratio within the money set and the location set.

Dependencies: Python stdlib; `requests` if available (falls back to urllib).
"""
import sys, os, json, re, gzip
from html.parser import HTMLParser

try:
    import requests
except Exception:
    requests = None
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36")
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}


def fetch(url):
    """Return decoded HTML text, or '' on failure."""
    try:
        if requests:
            r = requests.get(url, headers={'User-Agent': UA}, timeout=30)
            return r.text if r.status_code == 200 else ''
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', 'replace') if resp.status == 200 else ''
    except Exception as e:
        print(" fetch failed", url, e)
        return ''


class Node:
    __slots__ = ('tag', 'attrs', 'children', 'parent', 'start', 'end', 'words')

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.parent = parent
        self.start = 0
        self.end = 0
        self.words = 0


class Analyzer(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.raw = raw
        # line-start offsets so getpos() -> absolute char index
        self._lineidx = [0]
        for i, ch in enumerate(raw):
            if ch == '\n':
                self._lineidx.append(i + 1)
        self.root = Node('#root', [], None)
        self.cur = self.root
        self.nodes = 0
        self.inline_css = 0
        self.style_blocks = []
        self.inline_js = 0
        self.script_blocks = 0
        self.ext_css = 0
        self.ext_js = 0
        self.svg = 0
        self.forms = 0
        self.ldjson = []
        self.title = ''
        self.meta_desc = ''
        self.h1 = []
        self.h2 = []
        self._cap = None
        self._buf = []
        self._grab = None
        self._gbuf = []

    def _off(self):
        ln, col = self.getpos()
        return self._lineidx[ln - 1] + col if ln - 1 < len(self._lineidx) else len(self.raw)

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == 'link' and 'stylesheet' in (ad.get('rel', '') or '').lower():
            self.ext_css += 1
        if tag == 'meta' and (ad.get('name', '') or '').lower() == 'description':
            self.meta_desc = ad.get('content', '') or ''
        if tag == 'script':
            if ad.get('src'):
                self.ext_js += 1
            else:
                t = (ad.get('type') or '').lower()
                self._cap = 'ldjson' if 'ld+json' in t else 'script'
                self._buf = []
        if tag == 'style':
            self._cap = 'style'
            self._buf = []
        if tag == 'svg':
            self.svg += 1
        if tag == 'form':
            self.forms += 1
        if tag in ('title', 'h1', 'h2'):
            self._grab = tag
            self._gbuf = []
        self.nodes += 1
        node = Node(tag, attrs, self.cur)
        node.start = self._off()
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        ad = dict(attrs)
        if tag == 'link' and 'stylesheet' in (ad.get('rel', '') or '').lower():
            self.ext_css += 1
        if tag == 'script' and ad.get('src'):
            self.ext_js += 1
        if tag == 'meta' and (ad.get('name', '') or '').lower() == 'description':
            self.meta_desc = ad.get('content', '') or ''
        if tag == 'svg':
            self.svg += 1
        self.nodes += 1
        n = Node(tag, attrs, self.cur)
        n.start = n.end = self._off()
        self.cur.children.append(n)

    def handle_endtag(self, tag):
        if self._cap and tag in ('style', 'script'):
            data = ''.join(self._buf)
            if self._cap == 'style':
                self.inline_css += len(data)
                self.style_blocks.append(len(data))
            elif self._cap == 'script':
                self.inline_js += len(data)
                self.script_blocks += 1
            elif self._cap == 'ldjson':
                try:
                    self.ldjson.append(json.loads(data))
                except Exception:
                    pass
            self._cap = None
            self._buf = []
        if self._grab and tag == self._grab:
            txt = ''.join(self._gbuf).strip()
            if tag == 'title':
                self.title = txt
            elif tag == 'h1':
                self.h1.append(txt)
            elif tag == 'h2':
                self.h2.append(txt)
            self._grab = None
        if tag in VOID:
            return
        node = self.cur
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None:
            node.end = self._off() + len(tag) + 3 # approx incl </tag>
            if node.parent is not None:
                self.cur = node.parent

    def handle_data(self, data):
        if self._cap is not None:
            self._buf.append(data)
            return
        if self._grab is not None:
            self._gbuf.append(data)
        t = data.strip()
        if t:
            self.cur.words += len(t.split())


def subtree(node):
    """Return (node_count, word_count) for a subtree."""
    nc, wc = 1, node.words
    for c in node.children:
        a, b = subtree(c)
        nc += a
        wc += b
    return nc, wc


def find_body(root):
    stack = [root]
    while stack:
        n = stack.pop()
        if n.tag == 'body':
            return n
        stack.extend(n.children)
    return root


def label_of(node, raw):
    # first heading text inside, else a class token, else the tag
    queue = list(node.children)
    while queue:
        n = queue.pop(0)
        if n.tag in ('h1', 'h2', 'h3'):
            txt = raw[n.start:n.end]
            m = re.sub('<[^>]+>', '', txt).strip()
            if m:
                return m[:60]
        queue = n.children + queue
    cls = node.attrs.get('class', '')
    return (cls.split()[0] if cls else node.tag)[:60]


def sentences(raw):
    text = re.sub('<script[^>]*>.*?</script>', ' ', raw, flags=re.S | re.I)
    text = re.sub('<style[^>]*>.*?</style>', ' ', text, flags=re.S | re.I)
    text = re.sub('<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 40]


def slug_of(url):
    from urllib.parse import urlparse
    path = urlparse(url).path.strip('/')
    if not path:
        return 'homepage'
    s = path.split('/')[-1]
    return re.sub(r'[^a-z0-9\-]', '', s.lower()) or 'homepage'


def analyze(url, cfg):
    raw = fetch(url)
    if not raw:
        return None
    az = Analyzer(raw)
    try:
        az.feed(raw)
    except Exception as e:
        print(" parse warn", url, e)
    body = find_body(az.root)
    secs = []
    for child in body.children:
        if child.tag in ('script', 'style', '#root'):
            continue
        nc, wc = subtree(child)
        if nc < 5:
            continue
        secs.append({
            'label': label_of(child, raw),
            'cls': child.attrs.get('class', '')[:60],
            'nodes': nc,
            'words': wc,
            'kb': round(max(0, child.end - child.start) / 1024, 1),
        })
    secs.sort(key=lambda s: -s['nodes'])
    types = []
    for block in az.ldjson:
        items = block if isinstance(block, list) else [block]
        for it in items:
            if isinstance(it, dict):
                t = it.get('@type')
                if isinstance(t, list):
                    types.extend(t)
                elif t:
                    types.append(t)
    trackers = {}
    for pat in cfg.get('taxonomy', {}).get('tracker_patterns', []):
        trackers[pat] = len(re.findall(re.escape(pat), raw))
    return {
        'url': url,
        'raw': len(raw.encode('utf-8')),
        'gzip': len(gzip.compress(raw.encode('utf-8'))),
        'dom': az.nodes,
        'inline_css': az.inline_css,
        'style_blocks': len(az.style_blocks),
        'largest_style': max(az.style_blocks) if az.style_blocks else 0,
        'inline_js': az.inline_js,
        'inline_js_blocks': az.script_blocks,
        'ext_css': az.ext_css,
        'ext_js': az.ext_js,
        'svg': az.svg,
        'forms': az.forms,
        'schema': types,
        'trackers': trackers,
        'title': az.title,
        'title_len': len(az.title),
        'meta_len': len(az.meta_desc),
        'h1': az.h1,
        'h2': az.h2,
        'h2_n': len(az.h2),
        'words': sum(s['words'] for s in secs),
        'sections': secs[:12],
        '_sentences': sentences(raw),
    }


def templated_ratio(group):
    """For each page, fraction of its sentences that appear on >= half of peers."""
    n = len(group)
    if n < 2:
        return
    allsents = [set(p['_sentences']) for p in group]
    for i, p in enumerate(group):
        if not p['_sentences']:
            p['templated_ratio'] = 0.0
            continue
        shared = 0
        for s in p['_sentences']:
            hits = sum(1 for j, ss in enumerate(allsents) if j != i and s in ss)
            if hits >= (n - 1) / 2.0:
                shared += 1
        p['templated_ratio'] = round(shared / len(p['_sentences']), 3)
        p['unique_sents'] = len(p['_sentences']) - shared


def main():
    cfgpath = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    cfg = json.load(open(cfgpath))
    inp = cfg.get('inputs', {})
    money = inp.get('money_pages', []) or []
    loc = inp.get('location_pages', []) or []
    if not money and not loc and inp.get('sitemap'):
        sm = fetch(inp['sitemap'])
        urls = re.findall(r'<loc>([^<]+)</loc>', sm)
        money = [u for u in urls if inp.get('sitemap') not in u][:60]
        print("crawled sitemap:", len(money), "urls")

    pages, sections = {}, {}
    for url in money + loc:
        print("fetch", url)
        d = analyze(url, cfg)
        if not d:
            continue
        d['cat'] = 'location' if url in loc else 'money'
        slug = slug_of(url)
        sections[slug] = {
            'name': (d['h1'][0] if d['h1'] else slug)[:60],
            'cat': d['cat'],
            'total_nodes': d['dom'],
            'total_bytes': d['raw'],
            'sections': d['sections'],
            'svg_count': d['svg'],
        }
        d.pop('sections', None)
        pages[slug] = d

    templated_ratio([pages[slug_of(u)] for u in money if slug_of(u) in pages])
    templated_ratio([pages[slug_of(u)] for u in loc if slug_of(u) in pages])
    for p in pages.values():
        p.pop('_sentences', None)

    out = os.path.dirname(os.path.abspath(cfgpath))
    json.dump(pages, open(os.path.join(out, 'pages_metrics.json'), 'w'), indent=1)
    json.dump(sections, open(os.path.join(out, 'sections.json'), 'w'), indent=1)
    print("\nSAVED pages_metrics.json (%d pages) + sections.json" % len(pages))


if __name__ == '__main__':
    main()
