'use strict';

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

document.addEventListener('click', function(e) {
  var sidebar = document.getElementById('sidebar');
  var toggle = document.querySelector('.sidebar-toggle');
  if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
    sidebar.classList.remove('open');
  }
});

document.querySelectorAll('.alert').forEach(function(el) {
  setTimeout(function() {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(function() { el.remove(); }, 400);
  }, 5000);
});

document.querySelectorAll('textarea[maxlength]').forEach(function(ta) {
  var max = parseInt(ta.getAttribute('maxlength'));
  var counter = document.createElement('small');
  counter.className = 'field-hint char-counter';
  counter.style.textAlign = 'right';
  counter.style.display = 'block';
  ta.parentNode.insertBefore(counter, ta.nextSibling);
  function update() {
    var left = max - ta.value.length;
    counter.textContent = left + ' characters remaining';
    counter.style.color = left < 50 ? 'var(--danger)' : '';
  }
  ta.addEventListener('input', update);
  update();
});
