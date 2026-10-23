/* Tiny progressive enhancement: theme toggle, project filter, scroll reveal, one video at a time. No dependencies, no tracking. */
(function () {
  var root = document.documentElement;
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };

  // theme toggle (the inline script in <head> already applied a saved choice before first paint)
  var btn = document.getElementById('theme-toggle');
  if (btn) btn.addEventListener('click', function () {
    var cur = root.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    var next = cur === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next); store.set('theme', next);
    btn.setAttribute('aria-label', next === 'light' ? 'Switch to dark theme' : 'Switch to light theme');
  });

  // header border once scrolled
  var header = document.querySelector('.site-header');
  if (header) { var onScroll = function () { header.classList.toggle('scrolled', window.scrollY > 8); }; onScroll(); addEventListener('scroll', onScroll, { passive: true }); }

  // project filter
  var chips = document.querySelectorAll('.chip[data-filter]'), cards = document.querySelectorAll('.card[data-cat]');
  var live = document.getElementById('filter-status');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var f = chip.getAttribute('data-filter'), shown = 0;
      chips.forEach(function (c) { c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
      cards.forEach(function (card) { var ok = f === 'all' || card.getAttribute('data-cat') === f; card.classList.toggle('hidden', !ok); if (ok) shown++; });
      if (live) live.textContent = shown + (shown === 1 ? ' project shown' : ' projects shown');
    });
  });

  // scroll reveal (content is visible by default; the .js class only exists when this script runs)
  var items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  } else items.forEach(function (el) { el.classList.add('in'); });

  // play one video at a time
  var vids = document.querySelectorAll('video');
  vids.forEach(function (v) { v.addEventListener('play', function () { vids.forEach(function (o) { if (o !== v) o.pause(); }); }); });
})();
