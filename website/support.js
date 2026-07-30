/* ===== Cash Memer — Support / FAQ ===== */
(function () {
  'use strict';
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  var items = $$('.faq-item');
  var groups = $$('.faq-group');
  var searchEl = $('#faqSearch'), clearEl = $('#faqClear'), emptyEl = $('#faqEmpty'), catsEl = $('#faqCats');
  var state = { q: '', cat: 'All' };

  // build category chips from the groups present (skip search-only "behind the scenes" groups)
  var cats = ['All'].concat(groups.filter(function (g) { return !g.dataset.secret; }).map(function (g) { return g.dataset.group; }));
  catsEl.innerHTML = cats.map(function (c) {
    return '<button class="cat-chip' + (c === 'All' ? ' active' : '') + '" role="tab" data-cat="' + c + '" aria-selected="' + (c === 'All') + '">' + c + '</button>';
  }).join('');

  function apply() {
    var q = state.q.toLowerCase().trim(), shown = 0;
    items.forEach(function (it) {
      var text = it.textContent.toLowerCase();
      var hit = !!q && text.indexOf(q) > -1;
      var vis;
      if (it.dataset.secret === '1') {
        vis = hit;                                   // behind-the-scenes: only surface on a matching search
      } else {
        var inCat = state.cat === 'All' || it.dataset.cat === state.cat;
        vis = inCat && (!q || hit);
      }
      it.classList.toggle('faq-hidden', !vis);
      if (vis) { shown++; if (hit) it.open = true; else if (!q) it.open = false; }
    });
    // hide empty group headings
    groups.forEach(function (g) {
      var any = $$('.faq-item', g).some(function (it) { return !it.classList.contains('faq-hidden'); });
      var title = $('.faq-group-title', g);
      if (title) title.style.display = any ? '' : 'none';
      g.style.display = any ? '' : 'none';
    });
    emptyEl.hidden = shown > 0;
    document.dispatchEvent(new CustomEvent('cm-analytics', { detail: { event: 'faq_filter', q: state.q, cat: state.cat, results: shown } }));
  }

  searchEl.addEventListener('input', function () { state.q = searchEl.value; clearEl.classList.toggle('show', !!state.q); apply(); });
  clearEl.addEventListener('click', function () { state.q = ''; searchEl.value = ''; clearEl.classList.remove('show'); apply(); searchEl.focus(); });
  catsEl.addEventListener('click', function (e) {
    var b = e.target.closest('[data-cat]'); if (!b) return;
    state.cat = b.dataset.cat;
    $$('.cat-chip', catsEl).forEach(function (c) { var on = c === b; c.classList.toggle('active', on); c.setAttribute('aria-selected', on); });
    apply();
  });

  apply(); // initial pass — hides the search-only "behind the scenes" answers until searched

  // back to top
  var toTop = $('#toTop');
  if (toTop) {
    window.addEventListener('scroll', function () { toTop.classList.toggle('show', window.scrollY > 600); }, { passive: true });
    toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }
})();
