// Moonraker marketing site: auto-hide nav + tap/click dropdowns + FAQ accordion.
// Loaded site-wide via <script defer src="/assets/site.js">.
(function () {
  var nav = document.querySelector('.site-nav');

  // Nav dropdowns: open on tap/click (and keyboard), so menus do not flash away
  // on touch and do not flicker across a hover gap. CSS :hover still opens them
  // for mouse users.
  var dropdowns = nav ? nav.querySelectorAll('.nav-dropdown') : [];
  function closeDropdowns(except) {
    Array.prototype.forEach.call(dropdowns, function (dd) {
      if (dd === except) return;
      dd.classList.remove('open');
      var t = dd.querySelector(':scope > a');
      if (t) { t.setAttribute('aria-expanded', 'false'); }
    });
  }
  Array.prototype.forEach.call(dropdowns, function (dd) {
    var trigger = dd.querySelector(':scope > a');
    if (!trigger) return;
    trigger.setAttribute('aria-expanded', 'false');
    function toggle(e) {
      e.preventDefault();
      var willOpen = !dd.classList.contains('open');
      closeDropdowns(dd);
      dd.classList.toggle('open', willOpen);
      trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    }
    trigger.addEventListener('click', toggle);
    trigger.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') { toggle(e); }
    });
  });
  if (nav) {
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.nav-dropdown')) { closeDropdowns(null); }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { closeDropdowns(null); }
    });
  }

  // Mobile-only Book a Free Strategy Call CTA at the bottom of the open nav menu.
  var navLinks = document.getElementById('navLinks');
  if (navLinks && !navLinks.querySelector('.nav-cta-mobile')) {
    var ctaLi = document.createElement('li');
    ctaLi.className = 'nav-cta-mobile';
    var ctaA = document.createElement('a');
    ctaA.href = '/free-strategy-call';
    ctaA.textContent = 'Book a Free Strategy Call';
    ctaLi.appendChild(ctaA);
    navLinks.appendChild(ctaLi);
  }

  // Auto-hide sticky nav: slide up on scroll down, reveal on scroll up. A small
  // delta threshold keeps tiny scroll jitter from toggling it (no twitch), and it
  // never hides while a menu or dropdown is open.
  if (nav) {
    var lastY = window.pageYOffset || 0;
    var ticking = false;
    function onScroll() {
      var y = window.pageYOffset || 0;
      if (y > 80) { nav.classList.add('nav-scrolled'); } else { nav.classList.remove('nav-scrolled'); }
      var delta = y - lastY;
      if (Math.abs(delta) > 6) {
        var pinned = nav.querySelector('.nav-links.open, .nav-dropdown.open');
        if (!pinned && delta > 0 && y > 140) {
          nav.classList.add('nav-up');
        } else if (delta < 0 || y <= 140) {
          nav.classList.remove('nav-up');
        }
        lastY = y;
      }
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
