'use strict';

document.addEventListener("DOMContentLoaded", function () {

  // Sidebar toggle
  window.toggleSidebar = function () {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
  };

  // Close sidebar when clicking outside
  document.addEventListener('click', function(e) {
    var sidebar = document.getElementById('sidebar');
    var toggle = document.querySelector('.sidebar-toggle');

    if (
      sidebar &&
      sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      !toggle.contains(e.target)
    ) {
      sidebar.classList.remove('open');
    }
  });

  // Auto-hide alerts
  document.querySelectorAll('.alert').forEach(function(el) {
    setTimeout(function() {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity = '0';
      setTimeout(function() { el.remove(); }, 400);
    }, 5000);
  });

  // Character counter
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

});