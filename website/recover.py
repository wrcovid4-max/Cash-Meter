#!/usr/bin/env python3
"""Recover assets/ and the inlined scripts from the built pages.

build.py inlines every image as a data URI. That is reversible: an <img> keeps
its alt text through the rewrite, so the template's asset name and the built
page's data URI can be matched on alt rather than on position (position drifts,
because build.py also injects nav, footer and disclaimer markup).

Run from the website/ folder. Safe to re-run — it never overwrites.
"""
import base64, os, re

PAIRS = [
    ("index.template.html",      "index.html"),
    ("languages.template.html",  "languages.html"),
    ("driving.template.html",    "driving.html"),
    ("trademarks.template.html", "trademarks.html"),
    ("web-app.template.html",    "web-app.html"),
    ("privacy.template.html",    "privacy.html"),
    ("news.template.html",       "news.html"),
    ("mobile.template.html",     None),   # no built page — names only
]

IMG = re.compile(r"<img\b[^>]*>", re.I)
SRC = re.compile(r'src="([^"]*)"', re.I)
ALT = re.compile(r'alt="([^"]*)"', re.I)
ICON = re.compile(r'<link\b[^>]*rel="(?:icon|apple-touch-icon)"[^>]*>', re.I)
HREF = re.compile(r'href="([^"]*)"', re.I)

EXT = {"image/webp": ".webp", "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif"}


def imgs(text):
    """[(src, alt)] for every <img> in the document."""
    out = []
    for tag in IMG.findall(text):
        s, a = SRC.search(tag), ALT.search(tag)
        out.append((s.group(1) if s else "", a.group(1) if a else ""))
    return out


def recover_assets():
    os.makedirs("assets", exist_ok=True)
    found = {}          # assets/name.png -> data uri
    wanted = set()      # every asset name any template references

    for tpl, built in PAIRS:
        if not os.path.exists(tpl):
            continue
        t_text = open(tpl, encoding="utf-8").read()
        for s, _ in imgs(t_text):
            if s.startswith("assets/"):
                wanted.add(s)
        for tag in ICON.findall(t_text):
            h = HREF.search(tag)
            if h and h.group(1).startswith("assets/"):
                wanted.add(h.group(1))

        if not built or not os.path.exists(built):
            continue
        b_text = open(built, encoding="utf-8").read()

        # alt text -> data uri, from the built page
        by_alt = {}
        for s, a in imgs(b_text):
            if s.startswith("data:") and a:
                by_alt.setdefault(a, s)

        matched = 0
        for s, a in imgs(t_text):
            if not s.startswith("assets/") or not a:
                continue
            uri = by_alt.get(a)
            if uri:
                found.setdefault(s, uri)
                matched += 1

        # the favicon has no alt — take it from the <link rel="icon">
        for tag in ICON.findall(t_text):
            h = HREF.search(tag)
            if not (h and h.group(1).startswith("assets/")):
                continue
            for btag in ICON.findall(b_text):
                bh = HREF.search(btag)
                if bh and bh.group(1).startswith("data:"):
                    found.setdefault(h.group(1), bh.group(1))
                    matched += 1
                    break

        print(f"  {built}: matched {matched}")

    # News articles aren't built from templates — their body HTML lives in
    # news.json, and the generated page carries the same alt text.
    if os.path.exists("news.json"):
        import json
        arts = json.load(open("news.json", encoding="utf-8"))["articles"]
        for a in arts:
            page = a.get("url") or f"news-{a.get('slug', '')}.html"
            body = a.get("content", "") + a.get("summary", "")
            # the hero is a separate field, not part of the body HTML
            hero, hero_alt = a.get("heroImage", ""), a.get("heroAlt", "")
            if hero.startswith("assets/"):
                wanted.add(hero)
            for s_, _ in imgs(body):
                if s_.startswith("assets/"):
                    wanted.add(s_)
            if not page or not os.path.exists(page):
                continue
            b_text = open(page, encoding="utf-8").read()
            by_alt = {}
            for s_, al in imgs(b_text):
                if s_.startswith("data:") and al:
                    by_alt.setdefault(al, s_)
            n = 0
            for s_, al in imgs(body):
                if s_.startswith("assets/") and al and al in by_alt:
                    found.setdefault(s_, by_alt[al])
                    n += 1
            if hero.startswith("assets/") and hero_alt in by_alt:
                found.setdefault(hero, by_alt[hero_alt])
                n += 1
            print(f"  {page}: matched {n}")

    written = skipped = 0
    for name, uri in sorted(found.items()):
        head, _, b64 = uri.partition(",")
        # Keep the original filename even though the bytes are now WebP —
        # build.py opens these with PIL, which sniffs the format from content,
        # and the templates and SPEC both refer to the original names.
        out = name
        if os.path.exists(out):
            skipped += 1
            continue
        try:
            open(out, "wb").write(base64.b64decode(b64))
        except Exception as e:
            print(f"  ! {name}: {e}")
            continue
        written += 1

    print(f"\nassets: {written} recovered, {skipped} already present")
    missing = sorted(wanted - set(found))
    if missing:
        print(f"still missing ({len(missing)}):")
        for m in missing:
            print("  ", m)
    return found, wanted


if __name__ == "__main__":
    print("Recovering assets from built pages...")
    recover_assets()
    print("\nDone. Inspect assets/, then try:  python3 build.py")
