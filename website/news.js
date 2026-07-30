/* ===== Cash Memer — News index ===== */
(function () {
  'use strict';
  var NEWS = (window.__NEWS__ || []).slice();
  var CATS = window.__NEWS_CATS__ || [];
  var LS = window.localStorage;
  var PAGE = 6;

  /* ---------- tiny helpers ---------- */
  function $(s, r) { return (r || document).querySelector(s); }
  function el(html) { var d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstElementChild; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }
  function fmtDate(iso) { if (!iso) return ''; var d = new Date(iso + 'T00:00:00'); return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
  function getLS(k, def) { try { return JSON.parse(LS.getItem(k)) || def; } catch (e) { return def; } }
  function setLS(k, v) { try { LS.setItem(k, JSON.stringify(v)); } catch (e) {} }

  /* ---------- analytics hooks (dispatch + console) ---------- */
  function track(event, data) {
    var payload = Object.assign({ event: event, ts: Date.now() }, data || {});
    document.dispatchEvent(new CustomEvent('cm-analytics', { detail: payload }));
    if (window.dataLayer) window.dataLayer.push(payload);
    if (window.__CM_DEBUG__) console.log('[analytics]', payload);
  }

  /* ---------- theme (persisted, respects system) ---------- */
  var themeBtn = $('#themeToggle');
  function applyTheme(t) { document.documentElement.dataset.theme = t; setLS('cm-theme', t); }
  (function initTheme() {
    var stored = null; try { stored = JSON.parse(LS.getItem('cm-theme')); } catch (e) {}
    if (stored) document.documentElement.dataset.theme = stored;
    else if (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches) document.documentElement.dataset.theme = 'dark';
  })();
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    applyTheme(next); track('theme_toggle', { theme: next });
  });

  /* ---------- bookmarks / recently viewed ---------- */
  function bookmarks() { return getLS('cm-news-bookmarks', []); }
  function isSaved(id) { return bookmarks().indexOf(id) > -1; }
  function toggleSave(id) {
    var b = bookmarks(), i = b.indexOf(id);
    if (i > -1) { b.splice(i, 1); track('bookmark_remove', { id: id }); }
    else { b.push(id); track('bookmark_add', { id: id }); }
    setLS('cm-news-bookmarks', b); return i === -1;
  }
  function recordView(id) {
    var r = getLS('cm-news-recent', []); r = r.filter(function (x) { return x !== id; }); r.unshift(id);
    setLS('cm-news-recent', r.slice(0, 12));
  }

  /* ---------- share ---------- */
  function shareArticle(a) {
    var url = location.origin + '/' + a.url;
    track('share', { id: a.id });
    if (navigator.share) { navigator.share({ title: a.title, text: a.summary, url: url }).catch(function () {}); }
    else { navigator.clipboard && navigator.clipboard.writeText(url); toast('Link copied to clipboard'); }
  }
  var toastEl;
  function toast(msg) {
    if (!toastEl) { toastEl = el('<div class="copied-toast" role="status" aria-live="polite"></div>'); document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add('show');
    clearTimeout(toastEl._t); toastEl._t = setTimeout(function () { toastEl.classList.remove('show'); }, 1800);
  }

  /* ---------- state (reflected in the URL) ---------- */
  var state = { q: '', cat: 'All', tag: '', sort: 'newest', saved: false, page: 1 };
  function readURL() {
    var p = new URLSearchParams(location.search);
    state.q = p.get('q') || ''; state.cat = p.get('cat') || 'All'; state.tag = p.get('tag') || '';
    state.sort = p.get('sort') || 'newest'; state.saved = p.get('saved') === '1';
  }
  function writeURL() {
    var p = new URLSearchParams();
    if (state.q) p.set('q', state.q); if (state.cat !== 'All') p.set('cat', state.cat);
    if (state.tag) p.set('tag', state.tag); if (state.sort !== 'newest') p.set('sort', state.sort);
    if (state.saved) p.set('saved', '1');
    history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : ''));
  }

  /* ---------- filtering + sorting ---------- */
  function filtered() {
    var q = state.q.toLowerCase().trim();
    var list = NEWS.filter(function (a) {
      if (state.saved && !isSaved(a.id)) return false;
      if (state.cat !== 'All' && a.category !== state.cat) return false;
      if (state.tag && a.tags.indexOf(state.tag) < 0) return false;
      if (q) {
        var hay = (a.title + ' ' + a.summary + ' ' + a.subtitle + ' ' + a.tags.join(' ') + ' ' + a.category).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
    list.sort(function (a, b) {
      if (state.sort === 'oldest') return a.date.localeCompare(b.date);
      if (state.sort === 'popular') return b.popularity - a.popularity;
      if (state.sort === 'updated') return (b.updated || b.date).localeCompare(a.updated || a.date);
      return b.date.localeCompare(a.date); // newest
    });
    return list;
  }

  /* ---------- card + featured markup ---------- */
  function metaHTML(a) {
    var parts = ['<span>' + fmtDate(a.date) + '</span>'];
    if (a.updated) parts.push('<span class="edited">Updated ' + fmtDate(a.updated) + '</span>');
    parts.push('<span>' + a.readingTime + ' min read</span>');
    return parts.join('<span class="dot"></span>');
  }
  function actionsHTML(a) {
    var saved = isSaved(a.id);
    return '<div class="card-actions">' +
      '<button class="icon-btn share" aria-label="Share ' + esc(a.title) + '" data-id="' + a.id + '"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg></button>' +
      '<button class="icon-btn bookmark' + (saved ? ' saved' : '') + '" aria-pressed="' + saved + '" aria-label="' + (saved ? 'Remove bookmark' : 'Save article') + '" data-id="' + a.id + '"><svg viewBox="0 0 24 24" fill="' + (saved ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z"/></svg></button>' +
      '</div>';
  }
  function fmtRel(iso) {
    // Posts carry a date (no clock time), so report accurate day-level relative time.
    if (!iso) return '';
    var d = new Date(iso + 'T00:00:00'), now = new Date();
    var that = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var days = Math.round((today - that) / 86400000);
    if (days <= 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return days + ' days ago';
    return fmtDate(iso);
  }
  var CLOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/></svg>';
  function timeHTML(a) {
    return '<div class="feat-time">' + CLOCK + '<span>' + fmtRel(a.updated || a.date) + '</span></div>';
  }
  function cardHTML(a) {
    return '<a class="news-card reveal" href="' + a.url + '" data-id="' + a.id + '" data-track="card_click">' +
      '<div class="news-card-media">' +
        '<img src="' + a.hero + '" loading="lazy" decoding="async" width="640" height="360" alt="' + esc(a.heroAlt) + '"></div>' +
      '<div class="news-card-body">' +
        '<span class="feat-eyebrow">' + esc(a.category) + '</span>' +
        '<h3>' + esc(a.title) + '</h3>' +
        timeHTML(a) +
      '</div></a>';
  }
  function featuredHTML(a) {
    return '<a class="featured-card" href="' + a.url + '" data-id="' + a.id + '" data-track="featured_click">' +
      '<div class="featured-media">' +
        '<img src="' + a.hero + '" loading="eager" decoding="async" width="1200" height="750" alt="' + esc(a.heroAlt) + '"></div>' +
      '<div class="featured-body">' +
        '<span class="feat-eyebrow">' + esc(a.category) + '</span>' +
        '<h2>' + esc(a.title) + '</h2>' +
        timeHTML(a) +
      '</div></a>';
  }

  /* ---------- render pipeline ---------- */
  var grid = $('#newsGrid'), featuredWrap = $('#newsFeatured'), emptyWrap = $('#newsEmpty'),
      countEl = $('#newsCount'), moreWrap = $('#newsMore');

  function renderChrome() {
    // category chips
    var chipWrap = $('#newsCats');
    var chips = ['All'].concat(CATS.map(function (c) { return c.name; }));
    chipWrap.innerHTML = chips.map(function (c) {
      return '<button class="cat-chip' + (state.cat === c ? ' active' : '') + '" role="tab" aria-selected="' + (state.cat === c) + '" data-cat="' + esc(c) + '">' + esc(c) + '</button>';
    }).join('') + '<button class="cat-chip' + (state.saved ? ' active' : '') + '" data-saved="1" aria-pressed="' + state.saved + '">★ Saved</button>';
    // sort + search reflect state
    $('#newsSort').value = state.sort;
    $('#newsSearch').value = state.q;
    $('#newsSearchClear').classList.toggle('show', !!state.q);
    // active tag pill
    var tagWrap = $('#activeTag');
    tagWrap.innerHTML = state.tag ? '<span class="active-tag">#' + esc(state.tag) + '<button aria-label="Clear tag filter" data-cleartag="1">&times;</button></span>' : '';
  }

  function renderFeatured(list) {
    // Only show the featured hero on the default view (no filters/search) — always the newest post
    var isDefault = !state.q && state.cat === 'All' && !state.tag && !state.saved;
    var feat = isDefault && NEWS.slice().sort(function (a, b) {
      return a.date < b.date ? 1 : a.date > b.date ? -1 : 0;
    })[0];
    featuredWrap.innerHTML = feat ? featuredHTML(feat) : '';
    featuredWrap.style.display = feat ? '' : 'none';
    var lbl = $('#newsNewestLabel'); if (lbl) lbl.hidden = !feat;
    return feat;
  }

  function renderGrid() {
    var list = filtered();
    var feat = renderFeatured(list);
    var body = feat ? list.filter(function (a) { return a.id !== feat.id; }) : list;
    var shown = body.slice(0, state.page * PAGE);

    countEl.textContent = body.length + (body.length === 1 ? ' article' : ' articles');
    var latestSec = grid.closest('.news-section');
    var latestHead = latestSec ? latestSec.querySelector('.news-section-head') : null;
    if (!body.length) {
      grid.innerHTML = ''; moreWrap.innerHTML = '';
      if (feat) {
        // The only story is the featured hero — no separate "Latest articles" list to show.
        emptyWrap.hidden = true;
        if (latestHead) latestHead.style.display = 'none';
      } else {
        if (latestHead) latestHead.style.display = '';
        emptyWrap.hidden = false;
        emptyWrap.querySelector('.es-msg').textContent = state.saved
          ? "You haven't saved any articles yet — tap the bookmark on any story."
          : 'No articles match your search. Try a different keyword or category.';
      }
    } else {
      if (latestHead) latestHead.style.display = '';
      emptyWrap.hidden = true;
      grid.innerHTML = shown.map(cardHTML).join('');
      revealIn(grid);
      moreWrap.innerHTML = shown.length < body.length
        ? '<button class="btn btn-ghost" id="loadMore">Load more articles (' + (body.length - shown.length) + ' more)</button>'
        : '';
    }
    writeURL();
  }

  function revealIn(scope) {
    var els = scope.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) { els.forEach(function (e) { e.classList.add('in'); }); return; }
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { threshold: 0.08 });
    els.forEach(function (e) { io.observe(e); });
  }

  /* ---------- trending + popular tags (static, from data) ---------- */
  function renderExtras() {
    var trendEl = $('#newsTrending');
    if (trendEl) {
      var trend = NEWS.slice().sort(function (a, b) { return b.popularity - a.popularity; }).slice(0, 4);
      trendEl.innerHTML = trend.map(function (a, i) {
        return '<a class="trend-item" href="' + a.url + '" data-id="' + a.id + '" data-track="trending_click">' +
          '<span class="trend-rank">' + (i + 1) + '</span><div><h4>' + esc(a.title) + '</h4>' +
          '<span class="m">' + esc(a.category) + ' · ' + a.readingTime + ' min</span></div></a>';
      }).join('');
    }
    var cloudEl = $('#newsTagCloud');
    if (cloudEl) {
      var counts = {};
      NEWS.forEach(function (a) { a.tags.forEach(function (t) { counts[t] = (counts[t] || 0) + 1; }); });
      var tags = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }).slice(0, 12);
      cloudEl.innerHTML = tags.map(function (t) {
        return '<button data-tag="' + esc(t) + '">#' + esc(t) + '<span class="n">' + counts[t] + '</span></button>';
      }).join('');
    }
  }

  /* ---------- events ---------- */
  var debounce;
  function on(sel, ev, fn) { document.addEventListener(ev, function (e) { var t = e.target.closest(sel); if (t) fn(e, t); }); }

  $('#newsSearch').addEventListener('input', function (e) {
    clearTimeout(debounce);
    debounce = setTimeout(function () { state.q = e.target.value; state.page = 1; $('#newsSearchClear').classList.toggle('show', !!state.q); track('search', { q: state.q }); renderGrid(); }, 160);
  });
  $('#newsSearchClear').addEventListener('click', function () { state.q = ''; state.page = 1; renderChrome(); renderGrid(); $('#newsSearch').focus(); });
  $('#newsSort').addEventListener('change', function (e) { state.sort = e.target.value; state.page = 1; track('sort', { sort: state.sort }); renderGrid(); });

  on('[data-cat]', 'click', function (e, t) { state.cat = t.dataset.cat; state.saved = false; state.tag = ''; state.page = 1; track('filter_category', { cat: state.cat }); renderChrome(); renderGrid(); });
  on('[data-saved]', 'click', function () { state.saved = !state.saved; state.cat = 'All'; state.tag = ''; state.page = 1; renderChrome(); renderGrid(); });
  on('[data-tag]', 'click', function (e, t) { state.tag = t.dataset.tag; state.page = 1; track('filter_tag', { tag: state.tag }); window.scrollTo({ top: $('#newsToolbar').offsetTop - 70, behavior: 'smooth' }); renderChrome(); renderGrid(); });
  on('[data-cleartag]', 'click', function () { state.tag = ''; state.page = 1; renderChrome(); renderGrid(); });
  on('#loadMore', 'click', function () { state.page++; track('load_more', { page: state.page }); renderGrid(); });
  on('.icon-btn.bookmark', 'click', function (e, t) {
    e.preventDefault(); var saved = toggleSave(t.dataset.id);
    t.classList.toggle('saved', saved); t.setAttribute('aria-pressed', saved);
    t.querySelector('svg').setAttribute('fill', saved ? 'currentColor' : 'none');
    toast(saved ? 'Saved to bookmarks' : 'Removed from bookmarks');
    if (state.saved) renderGrid();
  });
  on('.icon-btn.share', 'click', function (e, t) { e.preventDefault(); var a = NEWS.filter(function (x) { return x.id === t.dataset.id; })[0]; if (a) shareArticle(a); });
  on('[data-track]', 'click', function (e, t) { if (t.dataset.id) recordView(t.dataset.id); track(t.dataset.track || 'click', { id: t.dataset.id }); });
  on('#newsTagCloud button', 'click', function (e, t) { state.tag = t.dataset.tag; state.page = 1; track('filter_tag', { tag: state.tag, from: 'cloud' }); window.scrollTo({ top: $('#newsToolbar').offsetTop - 70, behavior: 'smooth' }); renderChrome(); renderGrid(); });

  /* newsletter */
  var nlForm = $('#newsletterForm');
  if (nlForm) nlForm.addEventListener('submit', function (e) {
    e.preventDefault(); var email = $('#nlEmail').value; track('newsletter_subscribe', { email: email });
    nlForm.style.display = 'none'; $('#nlOk').hidden = false;
  });

  /* back to top */
  var toTop = $('#toTop');
  window.addEventListener('scroll', function () { toTop.classList.toggle('show', window.scrollY > 600); }, { passive: true });
  toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* keyboard: "/" focuses search */
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') { e.preventDefault(); $('#newsSearch').focus(); }
  });

  /* ---------- empty newsroom (no articles at all) ---------- */
  function emptySite() {
    var sk = $('#newsSkeleton'); if (sk) sk.remove();
    ['#newsToolbar', '[aria-label="Featured article"]', '[aria-label="Trending"]', '[aria-label="Popular tags"]']
      .forEach(function (s) { var e = document.querySelector(s); if (e) e.style.display = 'none'; });
    var head = $('#newsCount') && $('#newsCount').closest('.news-section-head');
    if (head) head.style.display = 'none';
    $('#newsGrid').innerHTML = ''; $('#newsMore').innerHTML = '';
    var e = $('#newsEmpty'); e.hidden = false;
    e.querySelector('.ico').innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a1 1 0 0 1 1-1h11a1 1 0 0 1 1 1v13a2 2 0 0 0 2 2H6a2 2 0 0 1-2-2z"/><path d="M17 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2"/><path d="M8 8h5M8 12h5M8 16h3"/></svg>';
    e.querySelector('h3').textContent = 'No news… yet!';
    e.querySelector('.es-msg').textContent = "We're busy building. Product updates, release notes and stories from behind the counter will land right here — check back soon.";
    var btn = e.querySelector('.btn');
    if (btn) { btn.textContent = 'Back to home'; btn.setAttribute('onclick', "location.href='index.html'"); }
    track('news_view', { empty: true });
  }

  /* ---------- boot (with skeleton → content) ---------- */
  readURL();
  if (!NEWS.length) { emptySite(); return; }
  renderChrome();
  renderExtras();
  // brief skeleton for perceived performance, then render
  setTimeout(function () {
    var sk = $('#newsSkeleton'); if (sk) sk.remove();
    renderGrid();
    track('news_view', {});
  }, 260);
})();
