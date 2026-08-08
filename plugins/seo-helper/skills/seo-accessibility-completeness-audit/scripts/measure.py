#!/usr/bin/env python3
"""Deterministic page measurement (stdlib only : no LLM, no eyeballing).
Usage: python measure.py <url-or-file.html> [out.json]
Emits: dom_node_count, max_depth, max_children (+ Lighthouse verdict), headings,
landmarks, semantic5 elements, images(alt/missing), forms(inputs/labels)."""
import sys, json, urllib.request
from html.parser import HTMLParser

VOID={"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
LANDMARKS=["header","nav","main","aside","footer","section","article","form"]
SEMANTIC5=["header","nav","main","aside","footer","section","article","figure",
           "figcaption","time","mark","details","summary","dialog"]

class M(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth=0; self.max_depth=0; self.nodes=0; self.stack=[]; self.max_children=0
        self.tags={}; self.headings={f"h{i}":0 for i in range(1,7)}
        self.img_alt=0; self.img_missing=0; self.labels=0; self.inputs=0
    def handle_starttag(self,tag,attrs):
        self.nodes+=1; self.tags[tag]=self.tags.get(tag,0)+1
        if self.stack: self.stack[-1]+=1; self.max_children=max(self.max_children,self.stack[-1])
        if tag in self.headings: self.headings[tag]+=1
        if tag=="label": self.labels+=1
        if tag=="input": self.inputs+=1
        if tag=="img":
            a=dict(attrs)
            (self.__dict__.__setitem__("img_alt",self.img_alt+1) if "alt" in a
             else self.__dict__.__setitem__("img_missing",self.img_missing+1))
        if tag not in VOID:
            self.depth+=1; self.max_depth=max(self.max_depth,self.depth); self.stack.append(0)
    def handle_endtag(self,tag):
        if tag not in VOID and self.depth>0:
            self.depth-=1
            if self.stack: self.stack.pop()

def load(src):
    if src.startswith(("http://","https://")):
        req=urllib.request.Request(src,headers={"User-Agent":"Mozilla/5.0 seo-audit"})
        return urllib.request.urlopen(req,timeout=30).read().decode("utf-8","replace")
    return open(src,encoding="utf-8",errors="replace").read()

def measure(src):
    p=M(); p.feed(load(src))
    verdict=("pass" if p.nodes<=800 and p.max_depth<=32 and p.max_children<=60
             else "warn" if p.nodes<=1500 else "fail")
    return {"source":src,"dom_node_count":p.nodes,"max_depth":p.max_depth,
            "max_children":p.max_children,"dom_verdict":verdict,
            "headings":p.headings,
            "landmarks":{t:p.tags.get(t,0) for t in LANDMARKS},
            "images":{"with_alt":p.img_alt,"missing_alt":p.img_missing},
            "forms":{"inputs":p.inputs,"labels":p.labels},
            "semantic5":{t:p.tags.get(t,0) for t in SEMANTIC5 if p.tags.get(t)}}

def main():
    if len(sys.argv)<2: print(__doc__); return 2
    m=measure(sys.argv[1]); js=json.dumps(m,indent=2)
    if len(sys.argv)>2: open(sys.argv[2],"w").write(js); print("wrote",sys.argv[2])
    else: print(js)
    return 0
if __name__=="__main__": raise SystemExit(main())
