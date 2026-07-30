# Cash Memer

Professional Receipt Organizer — scan a paper receipt, let Gemini fill in the form,
add products by barcode, sign on screen, and print or share a two-page cash memo.
Live exchange rates from ExchangeRate-API, Google Sign-In with Firebase sync, offline
backups and app lock. English and Urdu, on iOS, iPadOS, macOS, watchOS, Android and
Wear OS.

*Make cash memos fun.*

## This repository

| Path | What it is |
| --- | --- |
| `docs/` | The Cash Memer website — static HTML, CSS and JS, no build step |
| `docs/screenshots/` | Screenshots used on the site |
| `Start Website Sharing.command` | Double-click on a Mac to serve `docs/` and get a public link |

The Android Studio project lives alongside this once it's added.

## The website

Plain static files. Nothing to install, nothing to compile.

```sh
python3 -m http.server 8901 --directory docs
# then open http://localhost:8901
```

Or double-click **Start Website Sharing.command** on a Mac. It serves `docs/` on port
8901 and, if `cloudflared` is available, prints a public `trycloudflare.com` link you
can share with anyone.

### Publishing with GitHub Pages

Settings → Pages → Source: **Deploy from a branch**, branch `main`, folder `/docs`.

### How it's put together

| File | Role |
| --- | --- |
| `docs/index.html` | The whole page. English copy lives here, in the markup |
| `docs/styles.css` | Light and dark themes as CSS custom properties, plus RTL support |
| `docs/app.js` | Theme switch, language switch, nav, screenshot tabs, converter demo |
| `docs/i18n.js` | Urdu strings, keyed to the `data-i18n` attributes in the HTML |
| `docs/icon.svg` | App icon, used as the favicon and in the header |
| `docs/privacy.html` | Privacy policy |

**Theme** follows System / Light / Dark, mirroring the app's Appearance setting, and
is remembered in `localStorage`. **Language** switches the entire page between English
and Urdu, flipping the document to RTL.

### Editing content

- **Copy** — edit the English directly in `index.html`, then update the matching key in
  `i18n.js`. Every translatable element carries a `data-i18n` attribute; the English text
  is read from the DOM on load, so the two must stay in step.
- **News** — add an `<li class="news__item">` at the top of the `<ol class="news">` list
  in the news section, and its Urdu keys in `i18n.js`.
- **Screenshots** — drop the image into `docs/screenshots/` and add a `<figure>` to the
  relevant tab panel in the screens section.
- **Store links** — when the App Store and Google Play listings go live, replace the two
  buttons in the `#get` section.

## Credits

Exchange rates are provided by ExchangeRate-API; liability for any incorrect information
lies with them. All trademarks, logos and names remain the property of their respective
owners.

Support: [support@cashmemer.com](mailto:support@cashmemer.com) · @cashmemerapp
