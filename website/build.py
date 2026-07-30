#!/usr/bin/env python3
"""Build self-contained HTML pages: inline CSS/JS, embed images as data URIs.
Also generates the News section: index, per-article pages, sitemap, RSS."""
import base64, io, re, json, html as _h
from PIL import Image

SITE = "https://www.cashmemer.com.pk"

# per-asset (format, max_width); default falls back to webp/900
SPEC = {
    "assets/logo.jpg": ("jpeg", 240),
    "assets/phone-scanner.png": ("webp", 560),
    "assets/phone-rates.png": ("webp", 560),
    "assets/phone-settings.png": ("webp", 560),
    "assets/phone-home-urdu.png": ("webp", 560),
    "assets/phone-settings-urdu.png": ("webp", 560),
    "assets/ipad-receipt.png": ("webp", 1100),
    "assets/ipad-receipt-urdu.png": ("webp", 1100),
    "assets/ipad-settings.png": ("webp", 1100),
    "assets/watch-history.png": ("webp", 560),
    "assets/watch-grid.jpg": ("webp", 560),
    "assets/watch-rates.png": ("webp", 560),
    "assets/watch-urdu.png": ("webp", 560),
    "assets/mac-app.png": ("webp", 1320),
    "assets/carplay-home.png": ("webp", 1100),
    "assets/carplay-dash.png": ("webp", 900),
    "assets/carplay-history.png": ("webp", 900),
    "assets/carplay-rates.png": ("webp", 900),
    "assets/aa-home.png": ("webp", 940),
    "assets/aa-dash.png": ("webp", 940),
    "assets/android-home.png": ("webp", 640),
    "assets/android-receipts.png": ("webp", 680),
    "assets/android-history.png": ("webp", 680),
    "assets/android-scanner.png": ("webp", 680),
    "assets/android-rates.png": ("webp", 680),
    "assets/android-signature.png": ("webp", 680),
    "assets/android-backup.png": ("webp", 680),
    "assets/android-settings.png": ("webp", 680),
    "assets/vision-hero.png": ("webp", 1080),
    "assets/vision-panel.png": ("webp", 1080),
    "assets/xr-hero.png": ("webp", 1320),
    "assets/press-banner.jpg": ("webp", 1280),
    "assets/press-trademarks.png": ("webp", 1400),
    "assets/press-webapp.jpg": ("webp", 1400),
    "assets/web-inventory.png": ("webp", 1280),
    "assets/web-pricelist.png": ("webp", 1280),
    "assets/web-receipt.png": ("webp", 1280),
    "assets/web-scanner.png": ("webp", 1280),
    "assets/press-scanner.jpg": ("webp", 620),
    "assets/press-items.jpg": ("webp", 620),
    "assets/press-details.jpg": ("webp", 620),
    "assets/press-signature.jpg": ("webp", 620),
    "assets/press-rates.jpg": ("webp", 620),
    "assets/press-products.jpg": ("webp", 620),
    "assets/press-cloud.jpg": ("webp", 620),
    "assets/press-lock.jpg": ("webp", 620),
    "assets/press-urdu.jpg": ("webp", 620),
}

def ensure_local(path):
    import os, subprocess, time
    if os.path.exists(path):
        return
    d, n = os.path.split(path)
    if os.path.exists(os.path.join(d, f".{n}.icloud")):
        subprocess.run(["brctl", "download", path], capture_output=True)
        for _ in range(60):
            if os.path.exists(path):
                return
            time.sleep(1)
    raise FileNotFoundError(f"{path} missing and could not be restored from iCloud")

_cache = {}
def encode(path):
    if path in _cache:
        return _cache[path]
    fmt, maxw = SPEC.get(path, ("webp", 900))
    try:
        ensure_local(path)
        im = Image.open(path)
    except Exception as e:                 # evicted from iCloud / unreadable — degrade gracefully, don't crash the build
        print(f"  ! asset unavailable, using placeholder: {path} ({e})")
        im = Image.new("RGB", (1280, 720), (24, 32, 48))
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if fmt == "jpeg":
        im.convert("RGB").save(buf, "JPEG", quality=82, optimize=True); mime = "image/jpeg"
    else:
        im.save(buf, "WEBP", quality=80, method=6); mime = "image/webp"
    uri = f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"
    _cache[path] = uri
    return uri

# ============================================================ NEWS
CATEGORIES = [
    ("App Updates", "#0a5fe0"), ("New Features", "#1a9e57"), ("Announcements", "#7c5cff"),
    ("Tips & Tricks", "#0a9fb8"), ("Tutorials", "#d98a12"), ("Security", "#d94452"),
    ("Privacy", "#5a6b8c"), ("Performance", "#e07b1a"), ("Bug Fixes", "#c94b7a"),
    ("Release Notes", "#1a8ed6"), ("Community", "#d05aa0"), ("Behind the Scenes", "#9a6a3c"),
]
CAT_COLOR = {n: c for n, c in CATEGORIES}
def cat_color(n): return CAT_COLOR.get(n, "#0a5fe0")
def xesc(s): return _h.escape(str(s), quote=True)

def shade(hexc, f):
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

def reading_time(content):
    return max(1, round(len(re.sub(r"<[^>]+>", " ", content).split()) / 200))

def word_count(content):
    return len(re.sub(r"<[^>]+>", " ", content).split())

def build_toc(content):
    out = []
    for m in re.finditer(r'<h([23]) id="([^"]+)">(.*?)</h\1>', content, re.S):
        out.append((int(m.group(1)), m.group(2), re.sub(r"<[^>]+>", "", m.group(3))))
    return out

def fmt_date(iso):
    import datetime
    return datetime.date.fromisoformat(iso).strftime("%b %-d, %Y")

def rfc822(iso):
    import datetime
    return datetime.datetime.fromisoformat(iso).strftime("%a, %d %b %Y 09:00:00 +0500")

def hero_svg(a):
    c = cat_color(a["category"]); c2 = shade(c, 0.5)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 750" width="1200" height="750">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{c}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
        '<rect width="1200" height="750" fill="url(#g)"/>'
        '<circle cx="1040" cy="130" r="270" fill="#fff" opacity="0.06"/>'
        '<circle cx="170" cy="650" r="210" fill="#fff" opacity="0.05"/>'
        '<text x="64" y="118" font-family="Inter,Arial,sans-serif" font-size="32" font-weight="800" '
        'fill="#fff" opacity="0.85" letter-spacing="5">CASH MEMER</text>'
        f'<text x="64" y="700" font-family="Inter,Arial,sans-serif" font-size="44" font-weight="800" '
        f'fill="#fff">{xesc(a["category"])}</text>'
        '<text x="1150" y="650" text-anchor="end" font-family="Inter,Arial,sans-serif" font-size="300" '
        'font-weight="900" fill="#fff" opacity="0.10">CM</text></svg>'
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

def initials(name):
    p = name.split()
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper()

# ---- load + enrich ----
raw = json.load(open("news.json", encoding="utf-8"))["articles"]
raw.sort(key=lambda a: a["date"], reverse=True)   # newest first
ART = []
for a in raw:
    a = dict(a)
    a.setdefault("updated", None)
    a["url"] = f"news-{a['slug']}.html"
    a["catColor"] = cat_color(a["category"])
    a["readingTime"] = reading_time(a["content"])
    a["toc"] = build_toc(a["content"])
    if a.get("heroImage"):
        try:
            a["hero"] = encode(a["heroImage"])          # real banner/photo hero
        except Exception:
            a["hero"] = hero_svg(a)                       # fall back if the file isn't there yet
    else:
        a["hero"] = hero_svg(a)
    ART.append(a)
BY_ID = {a["id"]: a for a in ART}

# data injected into the news index (trimmed to what the client needs)
def client_obj(a):
    return {k: a[k] for k in ("id", "slug", "url", "title", "subtitle", "summary", "category",
            "catColor", "tags", "author", "date", "updated", "featured", "popularity",
            "heroAlt", "readingTime", "hero")}
NEWS_JS = "<script>window.__NEWS__=%s;window.__NEWS_CATS__=%s;</script>" % (
    json.dumps([client_obj(a) for a in ART], ensure_ascii=False),
    json.dumps([{"name": n, "color": c} for n, c in CATEGORIES], ensure_ascii=False),
)

# ---- shared nav / footer ----
def nav(active):
    def cur(x): return ' aria-current="page"' if x == active else ""
    return f'''<header class="nav" id="nav"><div class="nav-inner">
    <a href="index.html" class="brand"><img src="assets/logo.jpg" alt="Cash Memer logo" class="brand-logo" /><span class="brand-name">Cash Memer</span></a>
    <nav class="nav-links">
      <a href="index.html#features">Features</a>
      <a href="index.html#showcase">Screens</a>
      <a href="index.html#platforms">Platforms</a>
      <a href="languages.html">Languages</a>
      <a href="index.html#download">Download</a>
    </nav>
    <a href="index.html#download" class="btn btn-sm btn-primary nav-cta">Get the App</a>
    <button class="nav-toggle" id="navToggle" aria-label="Toggle menu"><span></span><span></span><span></span></button>
  </div></header>'''

FOOTER = '''<footer class="footer"><div class="footer-inner">
  <div class="footer-brand"><a href="index.html" class="brand"><img src="assets/logo.jpg" alt="Cash Memer logo" class="brand-logo" /><span class="brand-name">Cash Memer</span></a>
  <p class="footer-tag">Smart receipts, live rates &amp; a pocket POS — كیش میمر.</p></div>
  <div class="footer-cols">
    <div class="footer-col"><h4>Product</h4><a href="index.html#features">Features</a><a href="mobile.html">iPhone &amp; Android</a><a href="wearables.html">Watch &amp; Mac</a><a href="news.html">News</a><a href="support.html">Support</a><a href="languages.html">Languages</a></div>
    <div class="footer-col"><h4>Contact</h4>
      <a href="mailto:support@cashmemer.com" class="icon-link"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg> support@cashmemer.com</a>
      <a href="https://twitter.com/cashmemerapp" target="_blank" rel="noopener" class="icon-link"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zM17.083 19.77h1.833L7.084 4.126H5.117z"/></svg> @cashmemerapp</a>
      <a href="https://www.cashmemer.com.pk" class="icon-link"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.6 2.4 2.6 15.6 0 18M12 3c-2.6 2.4-2.6 15.6 0 18"/></svg> www.cashmemer.com.pk</a></div>
    <div class="footer-col"><h4>Legal</h4><a href="#">Privacy Policy</a><a href="#">Terms of Service</a></div>
  </div></div>
  <div class="footer-bottom"><span>© 2026 Cash Memer. All rights reserved.</span><span>Made with care for shopkeepers everywhere.</span></div>
</footer>'''

# ---- Apple-style small print: numbered, per-page footnotes ----
# reusable trademark / attribution lines — each brand called out on its own
TM_APPLE = ("Apple, the Apple logo, iPhone, iPad, Mac, macOS, Apple Watch, watchOS, Apple Vision Pro, visionOS, "
    "Face ID, Touch ID, Siri and CarPlay are trademarks of Apple Inc., registered in the U.S. and other countries.")
TM_APPSTORE = "App Store is a service mark of Apple Inc."
TM_GOOGLE = ("Google, Android, Google Play, the Google Play logo, Wear OS, Android Auto and Android XR are trademarks "
    "of Google LLC.")
TM_GEMINI = ("Gemini and Firebase are trademarks of Google LLC. AI-generated results may be inaccurate and should "
    "always be reviewed before use.")
ATTR_RATES = ("Currency rates are provided by ExchangeRate-API (exchangerate-api.com) and are indicative only — not "
    "for accounting, tax or trading decisions.")
TM_OTHERS = "All other product and company names mentioned herein are the trademarks of their respective owners."
FREE_NOTE = ("Cash Memer is free to download and use, with no ads. Some features and platforms may vary by region, "
    "language and device, and are subject to change without notice.")

GENERIC_DISCLAIMER = [FREE_NOTE, TM_APPLE, TM_APPSTORE, TM_GOOGLE, TM_OTHERS]
DISCLAIMERS = {
    "index.html": [FREE_NOTE, ATTR_RATES,
        "AI receipt scanning is powered by Google Gemini; scanning accuracy depends on image quality and results should always be reviewed before saving.",
        "iPhone, iPad, Mac and Apple Watch apps are in development. Vision Pro, Android XR, CarPlay and Android Auto support is planned and not yet available.",
        TM_APPLE, TM_APPSTORE, TM_GOOGLE, TM_GEMINI, TM_OTHERS],
    "mobile.html": [
        "Cash Memer is available now on Google Play. iPhone and iPad apps are in development and not yet available.",
        "Some features require a compatible device and the latest operating system.",
        "AI receipt scanning is powered by Google Gemini; results may be inaccurate and should be reviewed before saving.",
        TM_APPLE, TM_APPSTORE, TM_GOOGLE, TM_GEMINI, TM_OTHERS],
    "wearables.html": [
        "The Apple Watch and Wear OS companions require a paired phone with Cash Memer installed.",
        "Feature availability varies by watch model and operating-system version.",
        TM_APPLE, TM_GOOGLE, TM_OTHERS],
    "spatial.html": [
        "The visionOS and Android XR apps are in development and not yet available.",
        "Images shown are illustrative mockups of work in progress and may not reflect the final product.",
        TM_APPLE, TM_GOOGLE, TM_OTHERS],
    "driving.html": [
        "CarPlay and Android Auto support is coming soon and is not yet available.",
        "Interact with your vehicle's display only when it is safe and legal to do so; always obey local laws and keep your attention on the road.",
        TM_APPLE, TM_GOOGLE, TM_OTHERS],
    "languages.html": [
        "Cash Memer ships in English and Urdu with full right-to-left support.",
        "Some translated content may vary, and additional languages may be added over time.",
        TM_OTHERS],
    "support.html": [
        "Support response times may vary and are not guaranteed.",
        "Cash Memer is provided “as is”, without warranty of any kind; see our Terms of Service for details.",
        "Cloud backup uses Google Firebase; you remain responsible for keeping your own exported backups.",
        TM_APPLE, TM_GOOGLE, TM_GEMINI, TM_OTHERS],
    "news.html": [
        "Product plans and release dates mentioned in news posts are subject to change and are not commitments to deliver any feature or functionality.",
        "Screenshots and images are illustrative.",
        TM_APPLE, TM_GOOGLE, TM_OTHERS],
    "download.html": [
        "Cash Memer is available now on Google Play and is free to download.",
        "iPhone, iPad, Mac and Apple Watch apps, along with Vision, XR and in-car support, are in development and not yet available — the download buttons for those platforms are placeholders.",
        "AI receipt scanning is powered by Google Gemini; results should be reviewed before saving.",
        "Requires a recent version of your device's operating system. An internet connection is needed for live rates and sync.",
        ATTR_RATES, TM_APPLE, TM_APPSTORE, TM_GOOGLE, TM_GEMINI, TM_OTHERS],
}

def add_disclaimer(html, out):
    items = DISCLAIMERS.get(out, GENERIC_DISCLAIMER)
    lis = "".join(f'<li>{xesc(t)}</li>' for t in items)
    block = f'<ol class="page-notes" aria-label="Legal disclaimers and trademarks">{lis}</ol>\n'
    return html.replace('<footer class="footer"', block + '<footer class="footer"', 1)

ARROW = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

CLOCK_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/></svg>')

def feat_time(a):
    return f'<div class="feat-time" data-date="{a["date"]}">{CLOCK_SVG}<span>{fmt_date(a["date"])}</span></div>'

def card(a):
    return (f'<a class="news-card" href="{a["url"]}">'
      f'<div class="news-card-media"><img src="{a["hero"]}" loading="lazy" decoding="async" '
      f'width="640" height="360" alt="{xesc(a["heroAlt"])}"></div>'
      f'<div class="news-card-body"><span class="feat-eyebrow">{xesc(a["category"])}</span>'
      f'<h3>{xesc(a["title"])}</h3>{feat_time(a)}</div></a>')

def featured_card(a):
    return (f'<a class="featured-card" href="{a["url"]}" style="grid-column:1/-1">'
      f'<div class="featured-media"><img src="{a["hero"]}" loading="eager" decoding="async" '
      f'width="1200" height="750" alt="{xesc(a["heroAlt"])}"></div>'
      f'<div class="featured-body"><span class="feat-eyebrow">{xesc(a["category"])}</span>'
      f'<h2>{xesc(a["title"])}</h2>{feat_time(a)}</div></a>')

SHARE_ICONS = {
  "x": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zM17.083 19.77h1.833L7.084 4.126H5.117z"/></svg>',
  "whatsapp": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.5 15.2L2 22l4.9-1.4A10 10 0 1 0 12 2zm0 18a8 8 0 0 1-4.1-1.1l-.3-.2-2.9.8.8-2.8-.2-.3A8 8 0 1 1 12 20zm4.4-6c-.2-.1-1.4-.7-1.6-.8s-.4-.1-.5.1-.6.8-.8 1-.3.2-.5.1a6.5 6.5 0 0 1-1.9-1.2 7.3 7.3 0 0 1-1.4-1.7c-.1-.2 0-.4.1-.5l.4-.4.2-.4a.4.4 0 0 0 0-.4l-.8-1.8c-.2-.5-.4-.4-.5-.4h-.5a.9.9 0 0 0-.7.3 2.8 2.8 0 0 0-.9 2.1 4.9 4.9 0 0 0 1 2.6 11 11 0 0 0 4.3 3.8c2 .8 2 .5 2.4.5a2.5 2.5 0 0 0 1.6-1.1 2 2 0 0 0 .1-1.1c0-.1-.2-.2-.4-.3z"/></svg>',
  "facebook": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.2c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/></svg>',
  "linkedin": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zM3 9h4v12H3zM10 9h3.8v1.7h.05c.53-1 1.8-2 3.7-2 4 0 4.7 2.6 4.7 6V21h-4v-5.3c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9V21h-4z"/></svg>',
  "email": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
}

def share_row(a):
    import urllib.parse as up
    url = f"{SITE}/{a['url']}"; t = up.quote(a["title"]); u = up.quote(url)
    links = {
      "x": f"https://twitter.com/intent/tweet?text={t}&url={u}",
      "whatsapp": f"https://wa.me/?text={t}%20{u}",
      "facebook": f"https://www.facebook.com/sharer/sharer.php?u={u}",
      "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={u}",
      "email": f"mailto:?subject={t}&body={u}",
    }
    btns = "".join(
      f'<a class="icon-btn" data-share="{k}" href="{v}" target="_blank" rel="noopener" '
      f'aria-label="Share on {k}">{SHARE_ICONS[k]}</a>' for k, v in links.items())
    return (f'<div class="article-share"><span class="lbl">Share</span>{btns}'
      f'<button class="icon-btn" id="copyLink" aria-label="Copy link">'
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg></button></div>')

def render_article(a, prev, nxt, related):
    toc_html = "".join(
      f'<a href="#{hid}" class="lvl{lvl}">{xesc(txt)}</a>' for lvl, hid, txt in a["toc"])
    toc = (f'<nav class="toc" aria-label="Table of contents"><h4>On this page</h4>{toc_html}</nav>'
           if a["toc"] else "")
    tags = "".join(f'<a href="news.html?tag={xesc(t)}">#{xesc(t)}</a>' for t in a["tags"])
    updated_meta = (f'<span class="dot"></span><span class="edited">Updated {fmt_date(a["updated"])}</span>'
                    if a.get("updated") else "")

    ld = {
      "@context": "https://schema.org", "@type": "NewsArticle",
      "headline": a["title"], "description": a["summary"], "image": [a["hero"]],
      "datePublished": a["date"], "dateModified": a.get("updated") or a["date"],
      "author": {"@type": "Person", "name": a["author"], "jobTitle": a.get("authorRole", "")},
      "publisher": {"@type": "Organization", "name": "Cash Memer",
                    "logo": {"@type": "ImageObject", "url": SITE + "/logo.png"}},
      "mainEntityOfPage": {"@type": "WebPage", "@id": f"{SITE}/{a['url']}"},
      "articleSection": a["category"], "keywords": ", ".join(a["tags"]),
      "wordCount": word_count(a["content"]), "inLanguage": "en",
    }

    def pn(x, side, label):
      if not x: return f'<span></span>'
      ico = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>'
             if side == "prev" else
             '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>')
      dl = (ico + label) if side == "prev" else (label + ico)
      return f'<a class="pn-card {side}" href="{x["url"]}"><span class="dir">{dl}</span><h4>{xesc(x["title"])}</h4></a>'

    rel = "".join(card(r) for r in related)

    head = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{xesc(a.get("seoTitle") or a["title"])}</title>
<meta name="description" content="{xesc(a.get("seoDescription") or a["summary"])}" />
<meta name="author" content="{xesc(a["author"])}" />
<meta name="theme-color" content="#0a5fe0" />
<link rel="canonical" href="{SITE}/{a['url']}" />
<meta property="og:type" content="article" />
<meta property="og:title" content="{xesc(a["title"])}" />
<meta property="og:description" content="{xesc(a["summary"])}" />
<meta property="og:url" content="{SITE}/{a['url']}" />
<meta property="og:image" content="{a['hero']}" />
<meta property="og:site_name" content="Cash Memer" />
<meta property="article:published_time" content="{a['date']}" />
<meta property="article:modified_time" content="{a.get('updated') or a['date']}" />
<meta property="article:section" content="{xesc(a['category'])}" />
{"".join(f'<meta property="article:tag" content="{xesc(t)}" />' for t in a["tags"])}
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{xesc(a["title"])}" />
<meta name="twitter:description" content="{xesc(a["summary"])}" />
<meta name="twitter:image" content="{a['hero']}" />
<link rel="alternate" type="application/rss+xml" title="Cash Memer News" href="rss.xml" />
<link rel="icon" type="image/jpeg" href="assets/logo.jpg" />
<link rel="apple-touch-icon" href="assets/logo.jpg" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="styles.css" />
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<div class="read-progress" id="readProgress" role="progressbar" aria-label="Reading progress"></div>
{nav('news')}
<main id="main" style="--cat:{a['catColor']}">
<nav class="breadcrumbs" aria-label="Breadcrumb">
  <a href="index.html">Home</a><span class="sep">/</span>
  <a href="news.html">News</a><span class="sep">/</span>
  <a href="news.html?cat={xesc(a['category'])}">{xesc(a['category'])}</a><span class="sep">/</span>
  <span aria-current="page">{xesc(a['title'])}</span>
</nav>
<article>
<header class="article-hero">
  <span class="cat-badge"><span class="cat-dot"></span>{xesc(a['category'])}</span>
  <h1>{xesc(a['title'])}</h1>
  <p class="subtitle">{xesc(a.get('subtitle',''))}</p>
  <div class="art-meta">
    <span class="author-row"><span class="avatar">{initials(a['author'])}</span><span class="name">{xesc(a['author'])}</span></span>
    <span class="dot"></span><span>{fmt_date(a['date'])}</span>{updated_meta}
    <span class="dot"></span><span>{a['readingTime']} min read</span>
  </div>
  <div class="article-actions">
    <button class="btn btn-sm btn-ghost" id="bmBtn" aria-pressed="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z"/></svg> <span class="lbl">Save</span></button>
    <button class="btn btn-sm btn-ghost" id="shareBtn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg> Share</button>
    <button class="btn btn-sm btn-ghost" id="copyLink2" onclick="document.getElementById('copyLink').click()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg> Copy link</button>
  </div>
</header>
<div class="article-cover"><img src="{a['hero']}" loading="eager" decoding="async" width="1200" height="600" alt="{xesc(a['heroAlt'])}"></div>
<div class="article-layout">
  {toc}
  <div class="article-content" id="articleContent">
    {a['content']}
    <div class="article-tools" id="articleTools">
      <button type="button" class="at-btn" id="dlAllImgs"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg> <span>Download all images</span></button>
      <button type="button" class="at-btn" id="copyAllText"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg> <span>Copy all text</span></button>
    </div>
    {share_row(a)}
    <div class="article-tags">{tags}</div>
    <div class="author-card"><span class="avatar">{initials(a['author'])}</span><div><h4>{xesc(a['author'])}</h4><div class="role">{xesc(a.get('authorRole',''))}</div><p>{xesc(a.get('authorBio',''))}</p></div></div>
    <div class="comments-ph"><div class="comments-box">💬 Comments are coming soon. Have thoughts? <a href="mailto:support@cashmemer.com" style="color:var(--blue);font-weight:700">Email us</a>.</div></div>
  </div>
</div>
</article>
<nav class="prev-next" aria-label="More articles">{pn(prev,'prev','Previous')}{pn(nxt,'next','Next')}</nav>
<section class="related"><div class="news-section-head" style="max-width:var(--maxw);margin:0 auto 22px"><h2>Related articles</h2></div><div class="news-grid">{rel}</div></section>
<a class="back-news" href="news.html"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 18l-6-6 6-6"/></svg> Back to all news</a>
</main>
<button class="to-top" id="toTop" aria-label="Back to top"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button>
{FOOTER}
<script>window.__ARTICLE__={json.dumps({"id":a["id"],"slug":a["slug"],"title":a["title"],"summary":a["summary"],"category":a["category"]}, ensure_ascii=False)};</script>
<script src="article.js"></script>
</body>
</html>'''
    return head

# ============================================================ WRITE
css = open("styles.css", encoding="utf-8").read()
js = open("script.js", encoding="utf-8").read()
newsjs = open("news.js", encoding="utf-8").read()
artjs = open("article.js", encoding="utf-8").read()
supportjs = open("support.js", encoding="utf-8").read()
searchjs = open("search.js", encoding="utf-8").read()

THEME_INIT = ("<script>(function(){try{var t=JSON.parse(localStorage.getItem('cm-theme'));"
    "if(!t&&window.matchMedia&&matchMedia('(prefers-color-scheme:dark)').matches)t='dark';"
    "if(t)document.documentElement.dataset.theme=t;}catch(e){}})();</script>")

THEME_BTN = ('<button class="nav-theme" id="themeToggle" aria-label="Toggle dark mode" title="Toggle dark mode">'
    '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
    '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>')

SEARCH_BTN = ('<button class="nav-theme" id="navSearch" aria-label="Search the site" title="Search (Ctrl/⌘ K)">'
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg></button>')

SEARCH_INDEX = [
    {"t": "Home", "d": "Overview of Cash Memer", "u": "index.html", "c": "Page", "type": "page", "k": "home overview start"},
    {"t": "iPhone & Android apps", "d": "The full counter in your pocket", "u": "mobile.html", "c": "Page", "type": "page", "k": "ios android google play phone mobile download"},
    {"t": "Watch & Mac", "d": "Apple Watch, Wear OS and the Mac app", "u": "wearables.html", "c": "Page", "type": "page", "k": "apple watch wear os watchos macos wrist desktop"},
    {"t": "Vision & XR", "d": "Spatial — visionOS & Android XR", "u": "spatial.html", "c": "Page", "type": "page", "k": "vision pro visionos android xr spatial headset"},
    {"t": "In the Car", "d": "Apple CarPlay & Android Auto", "u": "driving.html", "c": "Page", "type": "page", "k": "carplay android auto car dashboard driving"},
    {"t": "Languages", "d": "English & Urdu, full right-to-left", "u": "languages.html", "c": "Page", "type": "page", "k": "urdu english language rtl right to left bilingual"},
    {"t": "News", "d": "Updates, release notes and stories", "u": "news.html", "c": "Page", "type": "news", "k": "news blog updates release notes"},
    {"t": "Support & FAQs", "d": "Help and frequently asked questions", "u": "support.html", "c": "Page", "type": "support", "k": "support help faq contact email"},
    {"t": "AI Receipt Scanner", "d": "Gemini-powered OCR fills your memo", "u": "index.html#features", "c": "Feature", "type": "feature", "k": "ocr scan gemini ai camera bulk import receipt"},
    {"t": "Live currency rates", "d": "150+ currencies via ExchangeRate-API", "u": "index.html#features", "c": "Feature", "type": "feature", "k": "rates currency exchange usd pkr eur gbp"},
    {"t": "Sales dashboard", "d": "Today's sales, revenue and scans", "u": "index.html#features", "c": "Feature", "type": "feature", "k": "dashboard sales revenue analytics weather"},
    {"t": "Cloud sync & backup", "d": "Google sync; export JSON/SQLite", "u": "support.html", "c": "Feature", "type": "feature", "k": "backup sync firebase google restore json sqlite export"},
    {"t": "App Lock & Face ID", "d": "Biometric lock and custom passcode", "u": "support.html", "c": "Feature", "type": "feature", "k": "security face id touch id passcode lock privacy biometric"},
    {"t": "Barcode, NFC & scanners", "d": "Ring up products fast", "u": "index.html#features", "c": "Feature", "type": "feature", "k": "barcode nfc scanner external hardware products"},
    {"t": "Digital signatures", "d": "Sign memos, save a default", "u": "support.html", "c": "Feature", "type": "feature", "k": "signature sign default authorize"},
    {"t": "Siri & Spotlight (App Intents)", "d": "Start a memo by voice or search", "u": "index.html#smart", "c": "Feature", "type": "feature", "k": "siri spotlight app intents shortcuts voice"},
    {"t": "Powered by Apple Intelligence", "d": "Smart, private, on-device", "u": "index.html#smart", "c": "Feature", "type": "feature", "k": "apple intelligence ai writing tools"},
    {"t": "Is Cash Memer free?", "d": "Yes — free and ad-free", "u": "support.html", "c": "FAQ", "type": "faq", "k": "free price cost ads pricing"},
    {"t": "How do I back up my receipts?", "d": "Google sync or export a file", "u": "support.html", "c": "FAQ", "type": "faq", "k": "backup export restore sqlite json sync"},
    {"t": "Can I use it in Urdu?", "d": "Yes, full right-to-left Urdu", "u": "languages.html", "c": "FAQ", "type": "faq", "k": "urdu language rtl"},
    {"t": "How do I lock the app?", "d": "Face ID, Touch ID or a passcode", "u": "support.html", "c": "FAQ", "type": "faq", "k": "lock security face id passcode"},
    {"t": "Download Cash Memer", "d": "Get it on Google Play / Android", "u": "download.html", "c": "Action", "type": "page", "k": "download install google play app store get"},
]
SEARCH_SCRIPT = ("<script>window.__SEARCH__=" + json.dumps(SEARCH_INDEX, ensure_ascii=False)
    + ";</script>\n<script>\n" + searchjs + "\n</script>")

_NAV_SUB = ('<a href="languages.html">Languages</a>\n      <a href="index.html#download">Download</a>',
    '<a href="news.html">News</a>\n      <a href="support.html">Support</a>\n      <a href="languages.html">Languages</a>\n      <a href="download.html">Download</a>')
_NAV_HOME = ('<a href="languages.html">Languages</a>\n      <a href="#download">Download</a>',
    '<a href="news.html">News</a>\n      <a href="support.html">Support</a>\n      <a href="languages.html">Languages</a>\n      <a href="download.html">Download</a>')

# site-wide mobile menu toggle (works on every page, incl. news/article which don't load script.js)
NAV_JS = '''<script>
(function(){
  var nav=document.getElementById('nav'), t=document.getElementById('navToggle');
  if(!nav||!t)return;
  function set(open){ nav.classList.toggle('open', open); t.setAttribute('aria-expanded', open?'true':'false'); }
  set(false);
  t.addEventListener('click', function(){ set(!nav.classList.contains('open')); });
  nav.querySelectorAll('.nav-links a').forEach(function(a){ a.addEventListener('click', function(){ set(false); }); });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape' && nav.classList.contains('open')){ set(false); t.focus(); } });
  window.addEventListener('scroll', function(){ nav.classList.toggle('scrolled', window.scrollY>8); }, {passive:true});
})();
</script>'''

# site-wide image lightbox — click any content picture to view it full screen, with smooth zoom/pan
LIGHTBOX_JS = r'''<script>
(function(){
  function ok(im){
    if(!im||im.tagName!=='IMG')return false;
    if(im.closest('.nav')||im.closest('.footer')||im.closest('a')||im.closest('.brand')||im.closest('.update-card')||im.closest('.lightbox'))return false;
    if(im.classList.contains('cta-logo')||im.classList.contains('brand-logo'))return false;
    return true;
  }
  document.querySelectorAll('img').forEach(function(im){if(ok(im))im.classList.add('zoomable');});

  var box,img,scale=1,tx=0,ty=0,closeBtn,lastFocus;
  var ptrs={},lastDist=0,lastMid=null,panStart=null,moved=false;
  function apply(smooth){
    img.style.transition=smooth?'transform .2s ease':'none';
    img.style.transform='translate('+tx+'px,'+ty+'px) scale('+scale+')';
    img.style.cursor=scale>1?'grab':'zoom-in';
    box.classList.toggle('is-zoomed',scale>1);
  }
  function clampScale(){ if(scale<1)scale=1; if(scale>5)scale=5; if(scale===1){tx=0;ty=0;} }
  function zoomAt(cx,cy,k){
    var prev=scale; scale=prev*k; clampScale(); var kk=scale/prev;
    var vx=cx-window.innerWidth/2, vy=cy-window.innerHeight/2;
    tx=vx-kk*(vx-tx); ty=vy-kk*(vy-ty);
    if(scale===1){tx=0;ty=0;}
  }
  function vals(){return Object.keys(ptrs).map(function(k){return ptrs[k];});}
  function d2(a,b){return Math.hypot(a.x-b.x,a.y-b.y);}
  function mid(a,b){return{x:(a.x+b.x)/2,y:(a.y+b.y)/2};}
  function build(){
    box=document.createElement('div');box.className='lightbox';box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label','Image viewer');
    img=document.createElement('img');img.className='lb-img';img.draggable=false;
    var close=document.createElement('button');close.className='lightbox-close';close.type='button';close.setAttribute('aria-label','Close image');close.innerHTML='×';closeBtn=close;
    var hint=document.createElement('div');hint.className='lb-hint';hint.textContent='Scroll or pinch to zoom · drag to pan · Esc to close';
    box.appendChild(img);box.appendChild(close);box.appendChild(hint);document.body.appendChild(box);
    close.addEventListener('click',function(e){e.stopPropagation();hide();});
    box.addEventListener('wheel',function(e){e.preventDefault();zoomAt(e.clientX,e.clientY,e.deltaY<0?1.12:1/1.12);apply(false);},{passive:false});
    box.addEventListener('pointerdown',function(e){
      if(box.setPointerCapture){try{box.setPointerCapture(e.pointerId);}catch(err){}}
      ptrs[e.pointerId]={x:e.clientX,y:e.clientY};moved=false;
      var n=Object.keys(ptrs).length;
      if(n===1)panStart={x:e.clientX,y:e.clientY,tx:tx,ty:ty};
      else if(n===2){var p=vals();lastDist=d2(p[0],p[1]);lastMid=mid(p[0],p[1]);}
    });
    box.addEventListener('pointermove',function(e){
      if(!ptrs[e.pointerId])return;
      ptrs[e.pointerId]={x:e.clientX,y:e.clientY};
      var n=Object.keys(ptrs).length;
      if(n>=2){
        var p=vals();var dd=d2(p[0],p[1]);var m=mid(p[0],p[1]);
        if(lastDist){ tx+=m.x-lastMid.x; ty+=m.y-lastMid.y; zoomAt(m.x,m.y,dd/lastDist); apply(false); }
        lastDist=dd;lastMid=m;moved=true;
      } else if(panStart&&scale>1){
        tx=panStart.tx+(e.clientX-panStart.x); ty=panStart.ty+(e.clientY-panStart.y); apply(false);
        if(Math.abs(e.clientX-panStart.x)+Math.abs(e.clientY-panStart.y)>6)moved=true;
      } else if(panStart){
        if(Math.abs(e.clientX-panStart.x)+Math.abs(e.clientY-panStart.y)>6)moved=true;
      }
    });
    function up(e){ delete ptrs[e.pointerId]; var n=Object.keys(ptrs).length; if(n<2){lastDist=0;lastMid=null;} if(n===0)panStart=null; }
    box.addEventListener('pointerup',up);box.addEventListener('pointercancel',up);
    box.addEventListener('click',function(e){
      if(moved)return;
      if(e.target===img){ if(scale>1){scale=1;tx=0;ty=0;apply(true);} else {zoomAt(e.clientX,e.clientY,2.5);apply(true);} }
      else if(e.target===box){ hide(); }
    });
  }
  function show(im){ if(!box)build(); lastFocus=document.activeElement; scale=1;tx=0;ty=0; img.src=im.currentSrc||im.src; img.alt=im.alt||''; apply(false); box.classList.add('open'); document.documentElement.style.overflow='hidden'; if(closeBtn)closeBtn.focus(); }
  function hide(){ if(box){box.classList.remove('open');document.documentElement.style.overflow=''; if(lastFocus&&lastFocus.focus)lastFocus.focus(); } }
  document.addEventListener('click',function(e){var im=e.target.closest?e.target.closest('img.zoomable'):null;if(!im)return;e.preventDefault();show(im);});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')hide();});
})();
</script>'''

# one standardized footer link set for every page (correct Download/Support links)
NEW_FOOTER_COLS = '''<div class="footer-cols">
      <div class="footer-col">
        <h4>Platforms</h4>
        <a href="web-app.html">Web App</a>
        <a href="mobile.html">iPhone &amp; Android</a>
        <a href="wearables.html">Watch &amp; Mac</a>
        <a href="spatial.html">Vision &amp; XR</a>
        <a href="driving.html">In the Car</a>
      </div>
      <div class="footer-col">
        <h4>Explore</h4>
        <a href="index.html#features">Features</a>
        <a href="languages.html">Languages</a>
        <a href="news.html">News</a>
        <a href="support.html">Support</a>
        <a href="download.html">Download</a>
      </div>
      <div class="footer-col">
        <h4>Contact</h4>
        <a href="https://twitter.com/cashmemerapp" target="_blank" rel="noopener" class="icon-link"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zM17.083 19.77h1.833L7.084 4.126H5.117z"/></svg> @cashmemerapp</a>
        <a href="https://www.cashmemer.com.pk" class="icon-link"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.6 2.4 2.6 15.6 0 18M12 3c-2.6 2.4-2.6 15.6 0 18"/></svg> www.cashmemer.com.pk</a>
        <a href="mailto:support@cashmemer.com" class="icon-link"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg> support@cashmemer.com</a>
      </div>
      <div class="footer-col">
        <h4>Legal</h4>
        <a href="privacy.html">Privacy Policy</a>
        <a href="terms.html">Terms of Service</a>
        <a href="trademarks.html">Trademarks</a>
      </div>
    </div>'''

def inline_common(html):
    html = html.replace('<link rel="stylesheet" href="styles.css" />', THEME_INIT + f"<style>\n{css}\n</style>")
    # standardize every page's footer columns (fixes Download link, adds Support + all pages)
    html = re.sub(r'<div class="footer-cols">.*?</div>\s*</div>\s*<div class="footer-bottom"',
                  NEW_FOOTER_COLS + '\n  </div>\n  <div class="footer-bottom"', html, flags=re.S, count=1)
    html = html.replace('<button class="nav-toggle" id="navToggle" aria-label="Toggle menu">',
                        SEARCH_BTN + THEME_BTN + '\n    <button class="nav-toggle" id="navToggle" aria-label="Toggle menu">')
    html = html.replace(*_NAV_SUB).replace(*_NAV_HOME)   # add News + Support to the nav
    # point the nav "Get the App" button at the dedicated download page
    html = html.replace('href="index.html#download" class="btn btn-sm btn-primary nav-cta"',
                        'href="download.html" class="btn btn-sm btn-primary nav-cta"')
    html = html.replace('href="#download" class="btn btn-sm btn-primary nav-cta"',
                        'href="download.html" class="btn btn-sm btn-primary nav-cta"')
    # every remaining CTA / "get the app" / experience button that pointed at the bottom widget → the real download page
    html = html.replace('href="index.html#download"', 'href="download.html"')
    html = html.replace('href="#download"', 'href="download.html"')
    # ---- accessibility (skip link, main landmark, aria, language tagging) ----
    html = html.replace('<header class="nav" id="nav">',
                        '<a class="skip-link" href="#main">Skip to main content</a>\n<header class="nav" id="nav">', 1)
    html = html.replace('<nav class="nav-links">', '<nav class="nav-links" id="navLinks" aria-label="Primary">', 1)
    html = html.replace('id="navToggle" aria-label="Toggle menu"',
                        'id="navToggle" aria-label="Toggle menu" aria-expanded="false" aria-controls="navLinks"', 1)
    if 'id="main"' in html:
        html = html.replace('<main id="main">', '<main id="main" tabindex="-1">', 1)
    else:   # marketing pages have no <main> — wrap the content between the nav and the footer
        html = html.replace('</header>', '</header>\n<main id="main" tabindex="-1">', 1)
        html = html.replace('<footer class="footer"', '</main>\n<footer class="footer"', 1)
    html = html.replace('كیش میمر', '<span lang="ur" dir="rtl">كیش میمر</span>')  # VoiceOver reads it as Urdu
    html = html.replace('</body>', NAV_JS + SEARCH_SCRIPT + LIGHTBOX_JS + '\n</body>')  # menu + search + lightbox
    return html

def embed_assets_blanket(html):
    for path in sorted(set(re.findall(r'assets/[a-zA-Z0-9._-]+', html)), key=len, reverse=True):
        html = html.replace(path, encode(path))
    return html

def report(out, html):
    leftover = re.findall(r'(?:src|href)="assets/[^"]+"', html)
    print(f"{out:26s} {len(html.encode())//1024:5d} KB  leftover={leftover or 'none'}")

# ---- article pages (logo replaced by attribute, so absolute URLs survive) ----
logo_uri = encode("assets/logo.jpg")
for i, a in enumerate(ART):
    prev = ART[i + 1] if i + 1 < len(ART) else None          # older
    nxt = ART[i - 1] if i - 1 >= 0 else None                 # newer
    same = [x for x in ART if x["category"] == a["category"] and x["id"] != a["id"]]
    others = [x for x in ART if x["id"] != a["id"] and x not in same]
    related = (same + others)[:3]
    html = render_article(a, prev, nxt, related)
    html = inline_common(html)
    html = add_disclaimer(html, a["url"])
    html = html.replace('<script src="article.js"></script>', f"<script>\n{artjs}\n</script>")
    html = html.replace('src="assets/logo.jpg"', f'src="{logo_uri}"').replace('href="assets/logo.jpg"', f'href="{logo_uri}"')
    html = embed_assets_blanket(html)          # embed body images + download links as data URIs
    open(a["url"], "w", encoding="utf-8").write(html)
    report(a["url"], html)

# ---- homepage latest cards (newest story as a wide featured card, rest as a grid) ----
if ART:
    _feat = ART[0]                       # ART is sorted newest-first
    _rest = ART[1:4]
    LATEST = featured_card(_feat) + "".join(card(a) for a in _rest)
else:
    LATEST = ('<div class="news-state" style="grid-column:1/-1;margin:0 auto">'
      '<span class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
      'stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a1 1 0 0 1 1-1h11a1 1 0 0 1 1 1v13a2 2 0 0 0 2 2H6a2 2 0 0 1-2-2z"/>'
      '<path d="M17 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2"/><path d="M8 8h5M8 12h5M8 16h3"/></svg></span>'
      '<h3>No news… yet!</h3><p>We\'re busy building. Updates, release notes and stories will land here soon.</p></div>')

# ---- updates carousel data (homepage): image front, "+" flips to text ----
updates_data = json.load(open("updates.json", encoding="utf-8"))["updates"]

UPDATE_ICONS = {
    "Live rates": '<path d="M3 16l5-5 4 4 8-9"/><path d="M17 6h4v4"/>',
    "Status": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
    "New": '<path d="M12 2.5l1.9 6.6 6.6 1.9-6.6 1.9L12 19.5l-1.9-6.6L3.5 11l6.6-1.9z"/>',
    "Tip": '<path d="M9.5 18.5h5"/><path d="M10 21h4"/><path d="M12 3a6 6 0 0 0-3.8 10.6c.7.6 1.3 1.4 1.3 2.4h5c0-1 .6-1.8 1.3-2.4A6 6 0 0 0 12 3z"/>',
    "Android": '<path d="M6 11a6 6 0 0 1 12 0v6H6z"/><line x1="6" y1="17" x2="6" y2="20"/><line x1="18" y1="17" x2="18" y2="20"/><line x1="6.5" y1="6" x2="8.5" y2="8.2"/><line x1="17.5" y1="6" x2="15.5" y2="8.2"/>',
    "Fix": '<path d="M15.5 7.5a3.5 3.5 0 0 1-4.6 4.6L5 18l1 1 5.9-5.9a3.5 3.5 0 0 0 4.6-4.6l-2.2 2.2-2-2z"/>',
}
DEFAULT_UPDATE_ICON = '<rect x="6" y="3" width="12" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>'

def update_poster(u):
    c = u["color"]; c2 = shade(c, 0.5)
    icon = UPDATE_ICONS.get(u["tag"], DEFAULT_UPDATE_ICON)
    s = 15; tx = 450 - 12 * s; ty = 470 - 12 * s
    glyph = (f'<g transform="translate({tx} {ty}) scale({s})" fill="none" stroke="#fff" '
             f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.9">{icon}</g>')
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1200" width="900" height="1200">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c}"/>'
        f'<stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
        '<rect width="900" height="1200" fill="url(#g)"/>'
        '<circle cx="760" cy="210" r="250" fill="#fff" opacity="0.07"/>'
        '<circle cx="120" cy="1060" r="190" fill="#fff" opacity="0.05"/>'
        '<text x="70" y="112" font-family="Inter,Arial,sans-serif" font-size="30" font-weight="800" '
        'fill="#fff" opacity="0.85" letter-spacing="4">CASH MEMER</text>'
        + glyph +
        f'<text x="70" y="1120" font-family="Inter,Arial,sans-serif" font-size="42" font-weight="800" '
        f'fill="#fff" opacity="0.95" letter-spacing="2">{xesc(u["tag"].upper())}</text></svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

def update_card(u):
    return (
        f'<div class="update-card" style="--u:{u["color"]}"><div class="uc-inner">'
        f'<div class="uc-face uc-front"><img src="{update_poster(u)}" loading="lazy" decoding="async" alt="{xesc(u["title"])}" />'
        f'<button class="uc-flip" aria-label="More about {xesc(u["title"])}" aria-pressed="false">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg></button></div>'
        f'<div class="uc-face uc-back"><div class="uc-back-top"><span class="u-tag">{xesc(u["tag"])}</span><span class="u-time">{xesc(u["time"])}</span></div>'
        f'<h3>{xesc(u["title"])}</h3><p>{xesc(u["note"])}</p>'
        '<button class="uc-flip uc-close" aria-label="Flip back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>'
        '</div></div>')

UPDATES_HTML = "".join(update_card(u) for u in updates_data)

# self-contained flip + arrow behaviour for pages that don't load script.js (e.g. news)
CAROUSEL_JS = '''<script>
(function(){
  document.addEventListener('click',function(e){
    var btn=e.target.closest&&e.target.closest('.update-card .uc-flip');if(!btn)return;e.preventDefault();
    var card=btn.closest('.update-card');var f=card.classList.toggle('flipped');
    var fb=card.querySelector('.uc-front .uc-flip');if(fb)fb.setAttribute('aria-pressed',f?'true':'false');
  });
  var t=document.getElementById('updatesTrack');
  if(!t||!t.children.length)return;
  var row=document.createElement('div');row.className='updates-row';
  while(t.firstChild)row.appendChild(t.firstChild);
  var originals=Array.prototype.slice.call(row.children);
  originals.forEach(function(node){var c=node.cloneNode(true);c.setAttribute('aria-hidden','true');
    c.querySelectorAll('button').forEach(function(b){b.tabIndex=-1;});row.appendChild(c);});
  t.appendChild(row);
  var GAP=18,loopW=0;
  function measure(){loopW=row.children[originals.length].offsetLeft-row.children[0].offsetLeft;}
  measure();window.addEventListener('resize',measure);window.addEventListener('load',measure);
  var offset=0,speed=0.5,userPaused=false,nudging=false;
  if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)userPaused=true;
  function moving(){return !userPaused&&!nudging&&loopW>0&&!row.querySelector('.update-card.flipped');}
  function render(){row.style.transform='translateX('+(-offset)+'px)';}
  function loop(){if(loopW<=0)measure();if(moving()){offset+=speed;if(offset>=loopW)offset-=loopW;render();}requestAnimationFrame(loop);}
  requestAnimationFrame(loop);
  var play=document.getElementById('uPlay');
  function paint(){if(!play)return;play.classList.toggle('paused',userPaused);
    play.setAttribute('aria-pressed',userPaused?'true':'false');
    play.setAttribute('aria-label',userPaused?'Play auto-scroll':'Pause auto-scroll');}
  if(play)play.addEventListener('click',function(){userPaused=!userPaused;paint();});paint();
  function nudge(dir){if(loopW<=0)return;var cardW=row.children[0].getBoundingClientRect().width+GAP;
    offset=(((offset+dir*cardW)%loopW)+loopW)%loopW;nudging=true;
    row.style.transition='transform .45s ease';render();
    setTimeout(function(){row.style.transition='';nudging=false;},470);}
  var p=document.getElementById('uPrev'),n=document.getElementById('uNext');
  if(p)p.addEventListener('click',function(){nudge(-1);});
  if(n)n.addEventListener('click',function(){nudge(1);});
})();
</script>'''

# ---- news index (built after UPDATES_HTML so the carousel can be injected) ----
html = open("news.template.html", encoding="utf-8").read()
html = inline_common(html)
html = add_disclaimer(html, "news.html")
html = html.replace("<!--UPDATES-->", UPDATES_HTML)
html = html.replace('<script src="news.js"></script>', f"<script>\n{newsjs}\n</script>" + CAROUSEL_JS)
html = html.replace("<!--NEWS_DATA-->", NEWS_JS)
html = embed_assets_blanket(html)
open("news.html", "w", encoding="utf-8").write(html)
report("news.html", html)

# ---- main pages (marketing + support) ----
PAGES = [
    ("index.template.html", "index.html"),
    ("wearables.template.html", "wearables.html"),
    ("spatial.template.html", "spatial.html"),
    ("languages.template.html", "languages.html"),
    ("driving.template.html", "driving.html"),
    ("mobile.template.html", "mobile.html"),
    ("support.template.html", "support.html"),
    ("download.template.html", "download.html"),
    ("web-app.template.html", "web-app.html"),
    ("terms.template.html", "terms.html"),
    ("privacy.template.html", "privacy.html"),
    ("trademarks.template.html", "trademarks.html"),
]
# ---- extra support FAQs (from the technical guide): a few visible, the rest search-only ----
def _faq(q, a, cat, secret=False):
    cls = "faq-item faq-secret" if secret else "faq-item"
    ds = ' data-secret="1"' if secret else ''
    return (f'<details class="{cls}" data-cat="{cat}"{ds}><summary>{xesc(q)}'
            '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg></summary>'
            f'<div class="faq-a">{a}</div></details>')

FAQ_VISIBLE = [
    ("AI Receipt Scanner is stuck on “Scanning”",
     "<p>If the scanner stays on the scanning screen for more than a minute, first check that your device has a stable "
     "internet connection — AI processing needs online services, and poor Wi-Fi, unstable mobile data, a VPN or a "
     "temporary server interruption can delay it.</p><p>Close the scanner, reconnect to the internet and try again. If it "
     "continues, restart the app and retry with a different, clearer receipt image.</p>"),
    ("Cloud Backup failed",
     "<p>Cloud Backup needs an internet connection, a signed-in Google Account and Firebase to be available.</p>"
     "<ul><li>Check your internet connection.</li><li>Confirm you’re signed into the correct Google Account.</li>"
     "<li>Reconnect and retry the backup.</li></ul>"),
    ("Cash Memer keeps crashing",
     "<p>Restart your device, then install the latest version from Google Play and make sure your Android version is "
     "supported.</p><p>If it keeps happening, email support with your device model, Android version, Cash Memer version, "
     "the steps to reproduce it and any screenshots.</p>"),
    ("The barcode scanner doesn’t detect products",
     "<p>Make sure the barcode is fully visible and well lit. If it already exists in your Product Catalog, Cash Memer "
     "retrieves the stored product automatically; if it’s new, you can create a product and link it to that barcode.</p>"),
    ("How do I report a technical issue?",
     "<p>Email <a href=\"mailto:wr.covid.4@gmail.com\">wr.covid.4@gmail.com</a> with your device manufacturer and model, "
     "Android version, Cash Memer version, screenshots or a screen recording, the exact steps to reproduce, and whether it "
     "happens every time or only occasionally. The more detail, the faster we can help.</p>"),
]

FAQ_SEARCH_ONLY = [
    ("What is Cash Memer?",
     "<p>Cash Memer is an Android app that simplifies receipt and expense management for individuals, freelancers, students "
     "and businesses. It brings AI receipt recognition, manual receipts, cloud sync, barcode &amp; NFC support, inventory, "
     "financial insights, multi-currency support and secure storage into one place — every receipt can hold customer "
     "info, items, payment methods, taxes, discounts, notes and GPS location.</p>"),
    ("Does the AI Receipt Scanner work offline?",
     "<p>No — AI processing needs an internet connection. Offline you can still create and manage receipts manually; "
     "once you’re back online, AI scanning becomes available again.</p>"),
    ("The AI keeps saying “Something went wrong”",
     "<p>This usually means a temporary network interruption, an unavailable AI service or an unsupported receipt image. "
     "Check your connection, make sure Google Play Services are working and confirm the receipt is clear and fully visible. "
     "If it persists, wait a few minutes and try again.</p>"),
    ("The AI recognized incorrect information",
     "<p>Recognition accuracy depends on receipt quality — faded ink, wrinkles, shadows, handwriting, unusual layouts "
     "or poor lighting can all cause mistakes. Review every extracted field before saving; you can edit anything manually.</p>"),
    ("My receipt image is blurry",
     "<p>Clean the camera lens, place the receipt on a flat surface with good lighting, and avoid shadows, glare, folded "
     "paper or moving the phone while capturing. Sharper images give better AI results.</p>"),
    ("Restore from Cloud is not working",
     "<p>Make sure you’re signed into the same Google Account that created the backup. If no backup exists, there’s "
     "nothing to restore. If a sync was interrupted, wait a few minutes and try again.</p>"),
    ("My backup is taking too long",
     "<p>Large receipt libraries take longer to upload, and slow connections or temporary cloud delays add to it. Keep Cash "
     "Memer open until synchronization finishes.</p>"),
    ("My data disappeared",
     "<p>First confirm you’re signed into the correct Google Account, and check whether an older backup was restored by "
     "accident. If the data existed only locally and the app was uninstalled or storage erased, it may no longer be "
     "recoverable.</p>"),
    ("Google Sign-In is not working",
     "<p>Check that you’re online, Google Play Services are updated, your Google Account is healthy and automatic date "
     "&amp; time are enabled. Restart the app after checking these.</p>"),
    ("My external barcode scanner isn’t working",
     "<p>Make sure it’s connected properly. Most supported scanners work in HID (keyboard) mode — if yours supports "
     "multiple modes, set it to Keyboard/HID before using Cash Memer.</p>"),
    ("NFC scanning doesn’t work",
     "<p>Confirm your device supports NFC, NFC is enabled in Android settings, the tag is compatible, and you’re holding "
     "it close to the device. Some phones place the NFC antenna in a different spot.</p>"),
    ("Weather information is unavailable",
     "<p>Weather needs an internet connection and the weather service to be available. If location permission is denied, "
     "enable it for location-based weather. Temporary service outages can also happen.</p>"),
    ("GPS location cannot be found",
     "<p>Move outdoors if you can, enable Location Services and grant Cash Memer location permission. Some buildings reduce "
     "GPS accuracy.</p>"),
    ("Exchange rates are outdated",
     "<p>Rates update only when you’re online — pull down to refresh the Rates page. If ExchangeRate-API is "
     "temporarily unavailable, your previously downloaded rates keep showing.</p>"),
    ("Exchange rates look incorrect",
     "<p>Different institutions use different rates. Cash Memer shows informational rates from its provider, which "
     "shouldn’t be treated as official banking rates.</p>"),
    ("The app feels slow",
     "<p>Performance can drop when storage is nearly full, many apps are running, or Android is updating in the background. "
     "Close unused apps, restart Cash Memer, and keep it updated.</p>"),
    ("Cash Memer freezes during startup",
     "<p>Force close and reopen it, and restart your device if needed. If it started after an update, reinstalling the "
     "latest version can help — cloud users should make sure their latest backup completed first.</p>"),
]

SUPPORT_EXTRA = (
    '  <div class="faq-group" data-group="Troubleshooting">\n'
    '    <h3 class="faq-group-title">Troubleshooting</h3>\n    '
    + "\n    ".join(_faq(q, a, "Troubleshooting") for q, a in FAQ_VISIBLE)
    + '\n  </div>\n'
    '  <div class="faq-group faq-group-secret" data-group="More answers" data-secret="1">\n'
    '    <h3 class="faq-group-title">More answers</h3>\n    '
    + "\n    ".join(_faq(q, a, "Troubleshooting", secret=True) for q, a in FAQ_SEARCH_ONLY)
    + '\n  </div>'
)

import os.path as _osp
_skipped_pages = []
for src, out in PAGES:
    if not _osp.exists(src):          # template lost — keep the built page as-is
        _skipped_pages.append((src, out))
        print(f"  ! template missing, keeping existing {out}: {src}")
        continue
    html = open(src, encoding="utf-8").read()
    if out == "support.html":
        html = html.replace("<!--FAQ_EXTRA-->", SUPPORT_EXTRA)
    if out == "index.html":
        html = html.replace("<!--LATEST_NEWS-->", LATEST).replace("<!--UPDATES-->", UPDATES_HTML)
    html = inline_common(html)
    if out not in ("terms.html", "privacy.html", "trademarks.html"):   # legal pages carry their own terms, no marketing fine print
        html = add_disclaimer(html, out)
    html = html.replace('<script src="script.js"></script>', f"<script>\n{js}\n</script>")
    html = html.replace('<script src="support.js"></script>', f"<script>\n{supportjs}\n</script>")
    html = embed_assets_blanket(html)
    open(out, "w", encoding="utf-8").write(html)
    report(out, html)

# ---- sitemap.xml ----
pages_all = ["index.html", "mobile.html", "wearables.html", "spatial.html", "driving.html",
             "languages.html", "news.html", "support.html", "download.html", "web-app.html",
             "terms.html", "privacy.html", "trademarks.html"] + [a["url"] for a in ART]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for p in pages_all:
    lm = ""
    for a in ART:
        if a["url"] == p:
            lm = f"<lastmod>{a.get('updated') or a['date']}</lastmod>"
    sm.append(f"<url><loc>{SITE}/{p}</loc>{lm}</url>")
sm.append("</urlset>")
open("sitemap.xml", "w", encoding="utf-8").write("\n".join(sm))

# ---- rss.xml ----
items = []
for a in ART:
    items.append(
      f"<item><title>{xesc(a['title'])}</title><link>{SITE}/{a['url']}</link>"
      f"<guid>{SITE}/{a['url']}</guid><category>{xesc(a['category'])}</category>"
      f"<pubDate>{rfc822(a['date'])}</pubDate>"
      f"<description>{xesc(a['summary'])}</description></item>")
rss = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<rss version="2.0"><channel>'
       '<title>Cash Memer News</title>'
       f'<link>{SITE}/news.html</link>'
       '<description>App updates, new features and release notes from Cash Memer.</description>'
       '<language>en</language>' + "".join(items) + '</channel></rss>')
open("rss.xml", "w", encoding="utf-8").write(rss)

print(f"\nGenerated {len(ART)} articles + news.html + sitemap.xml + rss.xml")

# ---- assemble a clean, deployable folder (drag this onto any static host) ----
import os, shutil
os.makedirs("dist", exist_ok=True)
for f in os.listdir("dist"):
    p = os.path.join("dist", f)
    if os.path.isfile(p):
        os.remove(p)
deploy = ["index.html", "mobile.html", "wearables.html", "spatial.html", "driving.html",
          "languages.html", "news.html", "support.html", "download.html", "web-app.html", "terms.html", "privacy.html",
          "trademarks.html", "sitemap.xml", "rss.xml"] + [a["url"] for a in ART]
_absent = []
for f in deploy:
    if not os.path.exists(f):
        _absent.append(f)
        continue
    shutil.copy(f, os.path.join("dist", f))
if _absent:
    print("  ! not in dist (file missing): " + ", ".join(_absent))
open("dist/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
print(f"dist/ ready for deploy — {len(deploy)} pages + robots.txt")
