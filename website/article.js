/* ===== Cash Memer — article page ===== */
(function () {
  'use strict';
  var A = window.__ARTICLE__ || {};
  var LS = window.localStorage;
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function getLS(k, d) { try { return JSON.parse(LS.getItem(k)) || d; } catch (e) { return d; } }
  function setLS(k, v) { try { LS.setItem(k, JSON.stringify(v)); } catch (e) {} }

  function track(event, data) {
    var p = Object.assign({ event: event, ts: Date.now(), id: A.id }, data || {});
    document.dispatchEvent(new CustomEvent('cm-analytics', { detail: p }));
    if (window.dataLayer) window.dataLayer.push(p);
    if (window.__CM_DEBUG__) console.log('[analytics]', p);
  }

  /* theme (shared with news index) */
  (function () {
    var t = null; try { t = JSON.parse(LS.getItem('cm-theme')); } catch (e) {}
    if (t) document.documentElement.dataset.theme = t;
    else if (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches) document.documentElement.dataset.theme = 'dark';
    var btn = $('#themeToggle');
    if (btn) btn.addEventListener('click', function () {
      var n = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = n; setLS('cm-theme', n); track('theme_toggle', { theme: n });
    });
  })();

  /* record recently viewed */
  (function () { var r = getLS('cm-news-recent', []).filter(function (x) { return x !== A.id; }); r.unshift(A.id); setLS('cm-news-recent', r.slice(0, 12)); })();

  /* reading progress bar */
  var bar = $('#readProgress'), content = $('#articleContent');
  function onScroll() {
    if (!content) return;
    var top = content.offsetTop, h = content.offsetHeight - window.innerHeight;
    var p = Math.min(1, Math.max(0, (window.scrollY - top + 120) / (h > 0 ? h : 1)));
    if (bar) bar.style.width = (p * 100).toFixed(1) + '%';
    var tt = $('#toTop'); if (tt) tt.classList.toggle('show', window.scrollY > 600);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* reveal every screenshot/image on scroll — same fade-and-rise as the homepage cards */
  (function () {
    // figure blocks, plus any bare image in the body not already inside a figure
    var targets = $$('.article-content .a-fig').concat(
      $$('.article-content img').filter(function (im) { return !im.closest('.a-fig'); })
    );
    if (!targets.length) return;
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return; // respect reduced motion — leave visible
    targets.forEach(function (f) { f.classList.add('reveal'); });
    if (!('IntersectionObserver' in window)) { targets.forEach(function (f) { f.classList.add('in'); }); return; }
    // toggle (not one-shot) so it re-animates every time it scrolls into view — up or down
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) { en.target.classList.toggle('in', en.isIntersecting); });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
    targets.forEach(function (f) { io.observe(f); });
  })();

  /* end-of-article tools: download all images + copy all text */
  (function () {
    var dlBtn = $('#dlAllImgs'), copyBtn = $('#copyAllText');
    function flash(btn, msg) {
      var span = btn.querySelector('span'), orig = span ? span.textContent : '';
      btn.classList.add('done'); if (span) span.textContent = msg;
      setTimeout(function () { btn.classList.remove('done'); if (span) span.textContent = orig; }, 1900);
    }
    var dls = $$('.article-content .a-fig .a-dl');
    if (dlBtn) {
      if (!dls.length) { dlBtn.style.display = 'none'; }
      else dlBtn.addEventListener('click', function () {
        dls.forEach(function (a, i) {
          setTimeout(function () {
            var t = document.createElement('a');
            t.href = a.getAttribute('href');
            t.download = a.getAttribute('download') || ('cash-memer-image-' + (i + 1) + '.webp');
            document.body.appendChild(t); t.click(); t.remove();
          }, i * 350);
        });
        flash(dlBtn, 'Downloading ' + dls.length + ' images…');
        track('download_all_images', { count: dls.length });
      });
    }
    if (copyBtn) copyBtn.addEventListener('click', function () {
      var parts = [A.title];
      $$('#articleContent h2, #articleContent h3, #articleContent p, #articleContent blockquote, #articleContent .a-cap')
        .forEach(function (el) { var t = (el.innerText || el.textContent || '').trim(); if (t) parts.push(t); });
      var text = parts.join('\n\n');
      (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
        .then(function () { flash(copyBtn, 'Copied!'); toast('Article text copied to clipboard'); },
              function () { toast('Copy failed — select and copy manually'); });
      track('copy_all_text', { chars: text.length });
    });
  })();

  /* TOC scrollspy + smooth scroll */
  var links = $$('.toc a'), heads = links.map(function (l) { return document.getElementById(l.getAttribute('href').slice(1)); });
  links.forEach(function (l) {
    l.addEventListener('click', function (e) {
      var id = l.getAttribute('href').slice(1), tgt = document.getElementById(id);
      if (tgt) { e.preventDefault(); window.scrollTo({ top: tgt.offsetTop - 84, behavior: 'smooth' }); history.replaceState(null, '', '#' + id); track('toc_click', { section: id }); }
    });
  });
  function spy() {
    var y = window.scrollY + 110, active = -1;
    heads.forEach(function (h, i) { if (h && h.offsetTop <= y) active = i; });
    links.forEach(function (l, i) { l.classList.toggle('active', i === active); });
  }
  window.addEventListener('scroll', spy, { passive: true }); spy();

  /* bookmark */
  var bm = $('#bmBtn');
  function saved() { return getLS('cm-news-bookmarks', []).indexOf(A.id) > -1; }
  function paintBm() {
    if (!bm) return; var s = saved();
    bm.classList.toggle('saved', s); bm.setAttribute('aria-pressed', s);
    bm.querySelector('svg').setAttribute('fill', s ? 'currentColor' : 'none');
    var lbl = bm.querySelector('.lbl'); if (lbl) lbl.textContent = s ? 'Saved' : 'Save';
  }
  if (bm) bm.addEventListener('click', function () {
    var b = getLS('cm-news-bookmarks', []), i = b.indexOf(A.id);
    if (i > -1) { b.splice(i, 1); track('bookmark_remove'); } else { b.push(A.id); track('bookmark_add'); }
    setLS('cm-news-bookmarks', b); paintBm(); toast(saved() ? 'Saved to bookmarks' : 'Removed from bookmarks');
  });
  paintBm();

  /* copy link + share */
  var toastEl;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'copied-toast'; toastEl.setAttribute('role', 'status'); document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add('show');
    clearTimeout(toastEl._t); toastEl._t = setTimeout(function () { toastEl.classList.remove('show'); }, 1800);
  }
  var url = location.href.split('#')[0];
  var copyBtn = $('#copyLink');
  if (copyBtn) copyBtn.addEventListener('click', function () {
    (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { toast('Link copied to clipboard'); }, function () { toast('Copy failed — ' + url); });
    track('copy_link');
  });
  var shareBtn = $('#shareBtn');
  if (shareBtn) shareBtn.addEventListener('click', function () {
    track('share', { method: navigator.share ? 'native' : 'copy' });
    if (navigator.share) navigator.share({ title: A.title, text: A.summary, url: url }).catch(function () {});
    else { navigator.clipboard && navigator.clipboard.writeText(url); toast('Link copied to clipboard'); }
  });
  $$('[data-share]').forEach(function (a) { a.addEventListener('click', function () { track('share', { network: a.dataset.share }); }); });

  /* back to top */
  var toTop = $('#toTop'); if (toTop) toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  track('article_view', { category: A.category });
})();
