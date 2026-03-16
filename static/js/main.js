/* SIWES Logbook Manager — Main JS */

'use strict';

/* ── Sidebar toggle ─────────────────────────────────────────────── */
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}
document.addEventListener('click', function (e) {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.sidebar-toggle');
  if (sidebar && sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) && e.target !== toggle) {
    sidebar.classList.remove('open');
  }
});

/* ── Auto-dismiss alerts after 5 s ─────────────────────────────── */
document.querySelectorAll('.alert').forEach(function (el) {
  setTimeout(function () {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(function () { el.remove(); }, 400);
  }, 5000);
});

/* ── Active nav link highlight ──────────────────────────────────── */
(function () {
  var path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(function (link) {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
})();

/* ── Live character counter for textareas ───────────────────────── */
document.querySelectorAll('textarea[maxlength]').forEach(function (ta) {
  var max = parseInt(ta.getAttribute('maxlength'));
  var counter = document.createElement('small');
  counter.className = 'field-hint char-counter';
  counter.style.textAlign = 'right';
  counter.style.display = 'block';
  ta.parentNode.insertBefore(counter, ta.nextSibling);
  function update() {
    var left = max - ta.value.length;
    counter.textContent = left + ' characters remaining';
    counter.style.color = left < 50 ? 'var(--warning)' : '';
  }
  ta.addEventListener('input', update);
  update();
});
