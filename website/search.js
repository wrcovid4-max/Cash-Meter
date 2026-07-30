/* ===== Cash Memer — site-wide search ===== */
(function () {
  'use strict';
  var INDEX = window.__SEARCH__ || [];
  if (!INDEX.length) return;

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }
  function hl(text, q) {
    if (!q) return esc(text);
    var i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + '<mark>' + esc(text.slice(i, i + q.length)) + '</mark>' + esc(text.slice(i + q.length));
  }
  var ICON = {
    page: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v6h6"/></svg>',
    feature: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.2 5.1 1.9-5.1 1.9L12 17l-1.9-5L5 10.1l5.1-1.9z"/></svg>',
    faq: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.4 2.3c-.6.3-.9.8-.9 1.5v.4M12 17h.01"/></svg>',
    support: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 1 0-12 0v4a2 2 0 0 1-2 2M6 8a6 6 0 0 1 12 0v5a3 3 0 0 1-3 3h-3"/></svg>',
    news: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h13v14H5a1 1 0 0 1-1-1z"/><path d="M17 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2M8 9h5M8 13h5"/></svg>'
  };

  var overlay = document.createElement('div');
  overlay.className = 'search-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Search Cash Memer');
  overlay.innerHTML =
    '<div class="search-modal">' +
      '<div class="search-input-wrap">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>' +
        '<input id="siteSearchInput" type="search" placeholder="Search pages, features, FAQs…" aria-label="Search" autocomplete="off" />' +
        '<span class="search-esc">Esc</span>' +
      '</div>' +
      '<div class="search-results" id="siteSearchResults" role="listbox"></div>' +
      '<div class="search-foot"><span><kbd>↑</kbd><kbd>↓</kbd> to navigate</span><span><kbd>↵</kbd> to open</span><span><kbd>Esc</kbd> to close</span></div>' +
    '</div>';
  document.body.appendChild(overlay);

  var input = overlay.querySelector('#siteSearchInput');
  var results = overlay.querySelector('#siteSearchResults');
  var active = -1, flat = [];

  function render(q) {
    q = (q || '').trim();
    var list;
    if (!q) list = INDEX.slice(0, 6);
    else {
      var ql = q.toLowerCase();
      list = INDEX.map(function (it) {
        var t = it.t.toLowerCase(), d = (it.d || '').toLowerCase(), k = (it.k || '').toLowerCase();
        var score = 0;
        if (t.indexOf(ql) === 0) score = 100; else if (t.indexOf(ql) > -1) score = 70;
        else if (k.indexOf(ql) > -1) score = 40; else if (d.indexOf(ql) > -1) score = 25;
        return { it: it, score: score };
      }).filter(function (x) { return x.score > 0; }).sort(function (a, b) { return b.score - a.score; })
        .map(function (x) { return x.it; }).slice(0, 12);
    }
    flat = list; active = list.length ? 0 : -1;
    if (!list.length) {
      results.innerHTML = '<div class="search-empty">No matches for “' + esc(q) + '”. Try “rates”, “backup”, “Face ID” or “Android”.</div>';
      return;
    }
    var html = (q ? '' : '<div class="search-group-label">Suggestions</div>');
    html += list.map(function (it, i) {
      return '<a class="search-item' + (i === 0 ? ' active' : '') + '" role="option" href="' + it.u + '" data-i="' + i + '">' +
        '<span class="si-ico">' + (ICON[it.type] || ICON.page) + '</span>' +
        '<span class="si-body"><span class="si-t">' + hl(it.t, q) + '</span>' +
        (it.d ? '<span class="si-d">' + hl(it.d, q) + '</span>' : '') + '</span>' +
        '<span class="si-c">' + esc(it.c) + '</span></a>';
    }).join('');
    results.innerHTML = html;
  }

  function setActive(n) {
    var items = results.querySelectorAll('.search-item');
    if (!items.length) return;
    active = (n + items.length) % items.length;
    items.forEach(function (el, i) { el.classList.toggle('active', i === active); });
    items[active].scrollIntoView({ block: 'nearest' });
  }

  function open() {
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    input.value = ''; render('');
    setTimeout(function () { input.focus(); }, 30);
    document.dispatchEvent(new CustomEvent('cm-analytics', { detail: { event: 'search_open', ts: Date.now() } }));
  }
  function close() { overlay.classList.remove('open'); document.body.style.overflow = ''; }

  input.addEventListener('input', function () { render(input.value); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive(active + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(active - 1); }
    else if (e.key === 'Enter') {
      var el = results.querySelectorAll('.search-item')[active];
      if (el) { document.dispatchEvent(new CustomEvent('cm-analytics', { detail: { event: 'search_select', q: input.value, url: el.getAttribute('href') } })); location.href = el.getAttribute('href'); }
    }
  });
  overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
  results.addEventListener('mousemove', function (e) { var el = e.target.closest('.search-item'); if (el) setActive(+el.dataset.i); });

  // triggers: nav button + ⌘K / Ctrl-K
  var btn = document.getElementById('navSearch');
  if (btn) btn.addEventListener('click', open);
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); overlay.classList.contains('open') ? close() : open(); }
    else if (e.key === 'Escape' && overlay.classList.contains('open')) close();
  });
})();
