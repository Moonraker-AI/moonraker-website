// Moonraker marketing site: auto-hide nav + FAQ accordion behavior.
// Loaded site-wide via <script defer src="/assets/site.js">.
(function () {
  // Auto-hide sticky nav: slide up on scroll down, reveal on scroll up.
  var nav = document.querySelector('.site-nav');
  if (nav) {
    var lastY = window.pageYOffset || 0;
    var ticking = false;
    function onScroll() {
      var y = window.pageYOffset || 0;
      if (y > 80) { nav.classList.add('nav-scrolled'); } else { nav.classList.remove('nav-scrolled'); }
      var menuOpen = nav.querySelector('.nav-links.open');
      if (!menuOpen && y > lastY && y > 140) {
        nav.classList.add('nav-up');
      } else if (y < lastY || y <= 140) {
        nav.classList.remove('nav-up');
      }
      lastY = y;
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { window.requestAnimationFrame(onScroll); ticking = true; }
    }, { passive: true });
  }

  // FAQ accordion: one open at a time, then smooth-scroll the opened panel to center.
  Array.prototype.forEach.call(document.querySelectorAll('details'), function (d) {
    d.addEventListener('toggle', function () {
      if (!d.open) return;
      var group = d.getAttribute('name');
      if (group) {
        Array.prototype.forEach.call(document.querySelectorAll('details[name="' + group + '"]'), function (other) {
          if (other !== d) { other.open = false; }
        });
      }
      window.requestAnimationFrame(function () {
        d.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    });
  });
})();
