# Cash Memer

Smart receipts, exchange rates and POS in your pocket — for iPhone, iPad, Mac,
Apple Watch, Android, Wear OS, and the web.

*Make cash memos fun.*

This repository is the backup of the **cashmemer.com.pk** website. The original
copy was lost; what's here was restored from the recovered files, plus more that
was reverse-engineered back out of the built pages.

## Running the site

```sh
./serve.sh
```

That prints two links:

- `http://localhost:8901` — this machine
- `http://<your-ip>:8901` — open this one on a phone or tablet on the same Wi-Fi

Pass a different port with `./serve.sh 9000`. Stop with Ctrl+C.

On a Mac you can also **double-click `Start Website Sharing.command`**. It does
the same thing, and if `cloudflared` is installed (`brew install cloudflared`) it
also prints a public `trycloudflare.com` link that works from any network.

The built `.html` files are **completely self-contained** — CSS and JavaScript
inlined, every image embedded as a data URI. You can open `website/index.html`
straight off disk with no server at all.

## Putting it online (a shareable link)

`.github/workflows/pages.yml` publishes `website/` to GitHub Pages on every push
to `main`. Two things have to be true first, and both are settings only the repo
owner can change:

1. **The repo must be eligible for Pages.** It's currently private, and Pages on
   a private repo needs a paid GitHub plan. On the free plan, make the repo
   public: *Settings → General → Danger Zone → Change visibility*.
2. **Turn Pages on:** *Settings → Pages → Build and deployment → Source →
   **GitHub Actions***.

Then re-run the workflow (Actions tab → *Deploy website to GitHub Pages* → *Run
workflow*), and the site is live at:

```
https://wrcovid4-max.github.io/Cash-Meter/
```

That URL is permanent and shareable. Every later `git push` redeploys it.

The workflow already asks to enable Pages itself, but the Actions token isn't
allowed to create a Pages site — it fails with *"Resource not accessible by
integration"*. Step 2 is unavoidable.

## Pages

All of these load and work:

| | |
| --- | --- |
| `index.html` | Home |
| `mobile.html` | iPhone & Android |
| `wearables.html` | Apple Watch, Wear OS, Mac |
| `driving.html` | CarPlay & Android Auto |
| `languages.html` | English & اردو |
| `news.html` | News index |
| `support.html` | Support & FAQs |
| `download.html` | Download |
| `web-app.html` | Web app |
| `privacy.html` | Privacy policy |
| `trademarks.html` | Trademarks |
| 3 × `news-*.html` | The news articles |

Plus `sitemap.xml` and `rss.xml`.

### Still missing

Two pages could not be recovered — no built copy and no template survived. The
nav links to them 404:

- `spatial.html` — the visionOS / Android XR page
- `terms.html` — terms of service

Eleven images are also gone, because the only pages that referenced them were
the ones that were lost. `build.py` substitutes a flat grey placeholder for each,
so nothing crashes: `android-home.png` and `press-{banner,cloud,details,items,`
`lock,products,rates,scanner,signature,urdu}.jpg`.

## Rebuilding

`build.py` regenerates every page from the templates, inlining the CSS and JS and
embedding the images.

```sh
cd website && python3 build.py
```

It writes the pages in place and assembles a clean `dist/` folder you can drag
onto any static host.

Two changes were made to it during the restore: it now skips a page whose
template is missing rather than crashing, and it leaves a missing file out of
`dist/` instead of failing. Both print a warning so you can see what was skipped.

**A caution.** Rebuilding re-encodes every image from `assets/`, and those assets
were themselves recovered *from* the built pages — so they have already been
through one compression pass. Rebuilding compresses them again and the pages get
visibly smaller each time. The committed `.html` files are the best copy that
exists. Only rebuild when you've actually changed a template, and check the
result before committing.

### How the recovery worked

`recover.py` pulls assets back out of the built pages. build.py inlines each
image as a data URI but leaves the `alt` text alone, so the template's asset name
and the built page's data URI can be paired on alt. It recovered 27 of 38 images.

The scripts came back the same way — `script.js`, `news.js` and `support.js` were
lifted out of the inline `<script>` blocks, and `updates.json` was reconstructed
from the markup of the homepage update cards.

`recover.py` and `recover_js.py` are kept in the repo in case any of this is ever
needed again. Neither overwrites an existing file.

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
