// ===== Cash Memer landing interactions =====
// (mobile menu toggle + sticky nav shadow are handled globally by NAV_JS injected on every page)
(function () {
  // Reveal-on-scroll for sections
  var revealEls = document.querySelectorAll(
    '.feature-card, .trio-card, .section-head, .split-copy, .split-visual, .gallery figure, .platform-card, .shot, .mini-feat, .frame-shot, .frame-pair figure, .cta-inner'
  );
  revealEls.forEach(function (el) { el.classList.add('reveal'); });

  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  // Relative day-level timestamps for news cards (e.g. "Yesterday")
  (function () {
    function rel(iso) {
      if (!iso) return '';
      var d = new Date(iso + 'T00:00:00'), now = new Date();
      var that = new Date(d.getFullYear(), d.getMonth(), d.getDate());
      var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      var days = Math.round((today - that) / 86400000);
      if (days <= 0) return 'Today';
      if (days === 1) return 'Yesterday';
      if (days < 7) return days + ' days ago';
      return null; // keep the printed date
    }
    document.querySelectorAll('.feat-time[data-date]').forEach(function (el) {
      var r = rel(el.getAttribute('data-date')), span = el.querySelector('span');
      if (r && span) span.textContent = r;
    });
  })();

  // Updates carousel: auto-scroll marquee, "+" flips a card, play/pause
  setupUpdatesCarousel();

  // Theme toggle (nav). Initial theme is applied pre-render by an inline head script.
  var themeBtn = document.getElementById('themeToggle');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('cm-theme', JSON.stringify(next)); } catch (e) {}
  });

  // Platforms "Explore every platform" dropdown
  var pfDd = document.getElementById('pfDropdown');
  if (pfDd) {
    var pfToggle = document.getElementById('pfDdToggle');
    pfToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = pfDd.classList.toggle('open');
      pfToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function (e) {
      if (!pfDd.contains(e.target)) {
        pfDd.classList.remove('open');
        pfToggle.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { pfDd.classList.remove('open'); pfToggle.setAttribute('aria-expanded', 'false'); }
    });
  }

  // Tactile bounce on click for feature cards (incl. the blue accent card)
  document.querySelectorAll('.feature-card').forEach(function (card) {
    card.addEventListener('click', function () {
      card.classList.remove('bounce');
      void card.offsetWidth; // reflow so the animation can retrigger
      card.classList.add('bounce');
    });
    card.addEventListener('animationend', function () {
      card.classList.remove('bounce');
    });
  });

  // ===== Updates carousel: transform-based marquee + flip + play/pause =====
  function setupUpdatesCarousel() {
    // Flip on "+" (delegated so cloned cards work too)
    document.addEventListener('click', function (e) {
      var btn = e.target.closest && e.target.closest('.update-card .uc-flip');
      if (!btn) return;
      e.preventDefault();
      var card = btn.closest('.update-card');
      var flipped = card.classList.toggle('flipped');
      var frontBtn = card.querySelector('.uc-front .uc-flip');
      if (frontBtn) frontBtn.setAttribute('aria-pressed', flipped ? 'true' : 'false');
    });

    var track = document.getElementById('updatesTrack');
    if (!track || !track.children.length) return;

    // Move cards into an inner row we translate — robust across browsers, no scroll needed
    var row = document.createElement('div');
    row.className = 'updates-row';
    while (track.firstChild) row.appendChild(track.firstChild);
    var originals = Array.prototype.slice.call(row.children);
    originals.forEach(function (node) {          // duplicate once for a seamless loop
      var c = node.cloneNode(true);
      c.setAttribute('aria-hidden', 'true');
      c.querySelectorAll('button').forEach(function (b) { b.tabIndex = -1; });
      row.appendChild(c);
    });
    track.appendChild(row);

    var GAP = 18, loopW = 0;
    function measure() { loopW = row.children[originals.length].offsetLeft - row.children[0].offsetLeft; }
    measure();
    window.addEventListener('resize', measure);
    window.addEventListener('load', measure);

    var offset = 0, speed = 0.5, userPaused = false, nudging = false;
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) userPaused = true;
    // pauses only when a card is flipped open, or when the user hits pause — resumes as soon as the card is closed
    function moving() { return !userPaused && !nudging && loopW > 0 && !row.querySelector('.update-card.flipped'); }
    function render() { row.style.transform = 'translateX(' + (-offset) + 'px)'; }
    function loop() {
      if (loopW <= 0) measure();   // keep retrying until layout gives a real width
      if (moving()) { offset += speed; if (offset >= loopW) offset -= loopW; render(); }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);

    var play = document.getElementById('uPlay');
    function paintPlay() {
      if (!play) return;
      play.classList.toggle('paused', userPaused);
      play.setAttribute('aria-pressed', userPaused ? 'true' : 'false');
      play.setAttribute('aria-label', userPaused ? 'Play auto-scroll' : 'Pause auto-scroll');
    }
    if (play) play.addEventListener('click', function () { userPaused = !userPaused; paintPlay(); });
    paintPlay();

    function nudge(dir) {
      if (loopW <= 0) return;
      var cardW = row.children[0].getBoundingClientRect().width + GAP;
      offset = (((offset + dir * cardW) % loopW) + loopW) % loopW;
      nudging = true;
      row.style.transition = 'transform .45s ease';
      render();
      setTimeout(function () { row.style.transition = ''; nudging = false; }, 470);
    }
    var prev = document.getElementById('uPrev'), next = document.getElementById('uNext');
    if (prev) prev.addEventListener('click', function () { nudge(-1); });
    if (next) next.addEventListener('click', function () { nudge(1); });
  }
})();
