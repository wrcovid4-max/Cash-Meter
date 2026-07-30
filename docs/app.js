/* Cash Memer — website behaviour.
   Theme (system/light/dark), language (English/Urdu), mobile nav,
   screenshot tabs and the converter demo. No dependencies. */

(function () {
  "use strict";

  var root = document.documentElement;
  var store = {
    get: function (k, d) { try { return localStorage.getItem(k) || d; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  /* ═══════════ theme ═══════════ */

  var media = window.matchMedia ? matchMedia("(prefers-color-scheme: dark)") : null;

  function resolveTheme(pref) {
    if (pref === "light" || pref === "dark") return pref;
    return media && media.matches ? "dark" : "light";
  }

  function applyTheme(pref) {
    root.setAttribute("data-theme-pref", pref);
    root.setAttribute("data-theme", resolveTheme(pref));
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-theme-btn]"),
      function (b) { b.setAttribute("aria-pressed", String(b.dataset.themeBtn === pref)); }
    );
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-theme-btn]"),
    function (b) {
      b.addEventListener("click", function () {
        var pref = b.dataset.themeBtn;
        store.set("cm-theme", pref);
        applyTheme(pref);
      });
    }
  );

  if (media) {
    var onSchemeChange = function () {
      if (root.getAttribute("data-theme-pref") === "system") applyTheme("system");
    };
    if (media.addEventListener) media.addEventListener("change", onSchemeChange);
    else if (media.addListener) media.addListener(onSchemeChange);
  }

  applyTheme(store.get("cm-theme", "system"));

  /* ═══════════ language ═══════════ */

  var UR = window.CM_UR || {};
  var nodes = document.querySelectorAll("[data-i18n]");
  var english = {};

  // The English copy is the HTML itself — cache it before anything replaces it.
  Array.prototype.forEach.call(nodes, function (el) {
    english[el.dataset.i18n] = el.innerHTML;
  });

  var titles = {
    en: document.title,
    ur: "کیش میمر — کیش میمو بنانا مزے کا کام"
  };

  function applyLang(lang) {
    var ur = lang === "ur";
    root.setAttribute("lang", ur ? "ur" : "en");
    root.setAttribute("dir", ur ? "rtl" : "ltr");
    document.title = titles[ur ? "ur" : "en"];

    Array.prototype.forEach.call(nodes, function (el) {
      var key = el.dataset.i18n;
      var val = ur ? UR[key] : english[key];
      if (val != null) el.innerHTML = val;
    });

    Array.prototype.forEach.call(
      document.querySelectorAll("[data-lang-btn]"),
      function (b) { b.setAttribute("aria-pressed", String(b.dataset.langBtn === (ur ? "ur" : "en"))); }
    );

    render();
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-lang-btn]"),
    function (b) {
      b.addEventListener("click", function () {
        var lang = b.dataset.langBtn;
        store.set("cm-lang", lang);
        applyLang(lang);
      });
    }
  );

  /* ═══════════ mobile nav ═══════════ */

  var toggle = document.querySelector(".nav__toggle");
  var menu = document.getElementById("mobile-menu");

  function closeMenu() {
    if (!menu) return;
    menu.removeAttribute("data-open");
    menu.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
  }

  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      if (menu.hasAttribute("data-open")) return closeMenu();
      menu.hidden = false;
      menu.setAttribute("data-open", "");
      toggle.setAttribute("aria-expanded", "true");
    });
    menu.addEventListener("click", function (e) {
      if (e.target.tagName === "A") closeMenu();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });
  }

  /* ═══════════ screenshot tabs ═══════════ */

  var tabs = document.querySelectorAll("[data-tab]");

  function selectTab(name) {
    Array.prototype.forEach.call(tabs, function (t) {
      var on = t.dataset.tab === name;
      t.setAttribute("aria-selected", String(on));
      var panel = document.getElementById(t.getAttribute("aria-controls"));
      if (panel) panel.hidden = !on;
    });
  }

  Array.prototype.forEach.call(tabs, function (t, i) {
    t.addEventListener("click", function () { selectTab(t.dataset.tab); });
    t.addEventListener("keydown", function (e) {
      var step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      e.preventDefault();
      // Arrow keys follow the reading direction.
      if (root.getAttribute("dir") === "rtl") step = -step;
      var next = tabs[(i + step + tabs.length) % tabs.length];
      selectTab(next.dataset.tab);
      next.focus();
    });
  });

  /* ═══════════ converter ═══════════ */

  // Illustrative rates per 1 USD. The app pulls these live from ExchangeRate-API.
  var RATES = [
    ["USD", 1,          "US Dollar",          "امریکی ڈالر"],
    ["PKR", 277.90,     "Pakistani Rupee",    "پاکستانی روپیہ"],
    ["EUR", 0.8754,     "Euro",               "یورو"],
    ["GBP", 0.7496,     "British Pound",      "برطانوی پاؤنڈ"],
    ["AED", 3.6725,     "UAE Dirham",         "اماراتی درہم"],
    ["SAR", 3.75,       "Saudi Riyal",        "سعودی ریال"],
    ["INR", 95.39,      "Indian Rupee",       "بھارتی روپیہ"],
    ["CAD", 1.42,       "Canadian Dollar",    "کینیڈین ڈالر"],
    ["AUD", 1.45,       "Australian Dollar",  "آسٹریلوی ڈالر"],
    ["CNY", 6.80,       "Chinese Yuan",       "چینی یوآن"],
    ["JPY", 161.33,     "Japanese Yen",       "جاپانی ین"],
    ["CHF", 0.8044,     "Swiss Franc",        "سوئس فرانک"],
    ["SGD", 1.29,       "Singapore Dollar",   "سنگاپور ڈالر"],
    ["TRY", 40.12,      "Turkish Lira",       "ترک لیرا"],
    ["AFN", 65.9217,    "Afghan Afghani",     "افغان افغانی"],
    ["IRR", 1279924.79, "Iranian Rial",       "ایرانی ریال"]
  ];

  var byCode = {};
  RATES.forEach(function (r) { byCode[r[0]] = r[1]; });

  var amountEl = document.getElementById("conv-amount");
  var fromEl   = document.getElementById("conv-from");
  var toEl     = document.getElementById("conv-to");
  var swapEl   = document.getElementById("conv-swap");
  var outEl    = document.getElementById("conv-out");
  var noteEl   = document.getElementById("conv-note");
  var ready    = amountEl && fromEl && toEl && outEl && noteEl;

  function decimals(code) { return byCode[code] > 100 ? 0 : 2; }

  function format(value, code) {
    return value.toLocaleString("en-US", {
      minimumFractionDigits: decimals(code),
      maximumFractionDigits: decimals(code)
    });
  }

  function convert(amount, from, to) {
    return (amount / byCode[from]) * byCode[to];
  }

  function fillOptions() {
    var ur = root.getAttribute("lang") === "ur";
    [fromEl, toEl].forEach(function (sel) {
      var current = sel.value;
      sel.innerHTML = "";
      RATES.forEach(function (r) {
        sel.add(new Option(r[0] + " — " + (ur ? r[3] : r[2]), r[0]));
      });
      if (current) sel.value = current;
    });
  }

  function render() {
    if (!ready) return;
    fillOptions();

    var amount = parseFloat(amountEl.value);
    if (!isFinite(amount) || amount < 0) amount = 0;

    var from = fromEl.value || "PKR";
    var to = toEl.value || "USD";
    var result = convert(amount, from, to);
    var unit = convert(1, from, to);

    outEl.innerHTML = "<b>" + format(result, to) + "</b> <span>" + to + "</span>";
    noteEl.textContent = "1 " + from + " = " + unit.toFixed(unit > 100 ? 2 : 4) + " " + to;
  }

  if (ready) {
    fillOptions();
    fromEl.value = "PKR";
    toEl.value = "USD";

    [amountEl, fromEl, toEl].forEach(function (el) {
      el.addEventListener("input", render);
      el.addEventListener("change", render);
    });

    if (swapEl) {
      swapEl.addEventListener("click", function () {
        var tmp = fromEl.value;
        fromEl.value = toEl.value;
        toEl.value = tmp;
        render();
      });
    }
  }

  /* ═══════════ boot ═══════════ */

  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  applyLang(store.get("cm-lang", "en"));
})();
