# Cash Memer

Smart receipts, exchange rates and POS in your pocket — for iPhone, iPad, Mac,
Apple Watch, Android, Wear OS, and the web.

*Make cash memos fun.*

This repository is the backup of the **cashmemer.com.pk** website. The original
copy was lost; what's here was restored from the recovered files.

## Layout

| Path | What it is |
| --- | --- |
| `website/` | The whole site — pages, templates, build script |
| `Start Website Sharing.command` | Double-click on a Mac to serve `website/` and get a public link |

## Running the site

The built `.html` files are **completely self-contained** — CSS and JavaScript are
inlined and every image is embedded as a data URI. No build step, no `assets/`
folder, no internet connection needed. Open `website/index.html` in a browser and
it works.

To serve it properly:

```sh
python3 -m http.server 8901 --directory website
# then open http://localhost:8901
```

Or double-click **Start Website Sharing.command**. It serves `website/` on port
8901 and, if `cloudflared` is installed, prints a public `trycloudflare.com` link
you can share with anyone.

## What's here

**Pages that load and work:**

`index.html` · `wearables.html` · `driving.html` · `languages.html` ·
`news.html` · `support.html` · `download.html` · `web-app.html` ·
`privacy.html` · `trademarks.html` ·
`news-cash-memer-launches-on-the-web.html` ·
`news-cash-memer-trademark-portfolio.html`

Plus `sitemap.xml` and `rss.xml`.

**Build system:** `build.py`, `styles.css`, `article.js`, `search.js`,
`news.json`, `news.sample.json`, and the templates
`index` · `mobile` · `languages` · `driving` · `privacy` · `trademarks` ·
`web-app` · `news`.

## Still missing

These were part of the site but weren't among the recovered files. The links to
them in the navigation currently 404:

| Missing | Notes |
| --- | --- |
| `mobile.html` | Template survived — only the built page is gone |
| `spatial.html` | visionOS / Android XR page. Template gone too |
| `terms.html` | Template gone too |
| `news-cash-memer-launches-on-google-play.html` | Listed in `sitemap.xml` |
| `assets/` | ~50 source images. Only needed to re-run `build.py` |
| `script.js`, `news.js`, `support.js` | Inlined in the built pages; needed to re-run `build.py` |
| `updates.json` | Needed to re-run `build.py` |

If any of these turn up, drop them in `website/` and commit. The build script
lists everything it expects at the top of `build.py`.

## Rebuilding

`build.py` regenerates every page from the templates, inlining CSS/JS and
embedding images. It needs the `assets/` folder and the missing scripts above, so
it won't run until those are recovered — the built pages in this repo are the
canonical copy for now.

```sh
cd website && python3 build.py
```

## Back this up

This repository is the only copy. Anything not committed and pushed does not
exist anywhere else.

```sh
git add -A && git commit -m "what changed" && git push
```

## Credits

Exchange rates are provided by ExchangeRate-API; liability for any incorrect
information lies with them. All trademarks, logos and names remain the property
of their respective owners.

Support: [support@cashmemer.com](mailto:support@cashmemer.com) · @cashmemerapp
