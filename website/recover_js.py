#!/usr/bin/env python3
"""Pull script.js / news.js / support.js back out of the built pages.

build.py replaces <script src="X.js"></script> with an inline <script> block.
The templates still show which page carried which script, so the blocks can be
identified by which built pages they appear in.

Run from the website/ folder. Never overwrites an existing file.
"""
import os, re
from collections import defaultdict

BUILT = ["index.html", "news.html", "support.html", "languages.html",
         "driving.html", "web-app.html", "trademarks.html", "privacy.html",
         "download.html", "wearables.html"]

INLINE = re.compile(r"<script>(.*?)</script>", re.S)

known = {}
for f in ("article.js", "search.js"):
    if os.path.exists(f):
        known[f] = open(f, encoding="utf-8").read().strip()

blocks = defaultdict(list)
for page in BUILT:
    if not os.path.exists(page):
        continue
    html = open(page, encoding="utf-8").read()
    for body in INLINE.findall(html):
        body = body.strip()
        if len(body) < 300:                       # theme-init shim, JSON-LD, etc.
            continue
        if body.startswith("{") or body.startswith("["):
            continue
        if any(body == v for v in known.values()):
            continue
        blocks[body].append(page)

print(f"{len(blocks)} distinct inline blocks\n")
for body, pages in sorted(blocks.items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(body)//1024:>4} KB  on {len(pages):>2} page(s): {', '.join(sorted(pages))}")
    print(f"          starts: {body[:90].replace(chr(10),' ')!r}")

# script.js is linked from every page; the other two from exactly one each.
for body, pages in blocks.items():
    if len(pages) >= 5:
        name = "script.js"
    elif pages == ["support.html"]:
        name = "support.js"
    elif pages == ["news.html"]:
        name = "news.js"
    else:
        continue
    if os.path.exists(name):
        print(f"\n{name} already present — leaving it")
        continue
    open(name, "w", encoding="utf-8").write(body + "\n")
    print(f"\nwrote {name} ({len(body)//1024} KB) from {', '.join(pages)}")
