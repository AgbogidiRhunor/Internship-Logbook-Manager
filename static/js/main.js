'use strict';

/* Sidebar toggle */
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

/* Auto-dismiss alerts after 5 s */
document.querySelectorAll('.alert').forEach(function (el) {
  setTimeout(function () {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(function () { el.remove(); }, 400);
  }, 5000);
});

/* Active nav link highlight */
(function () {
  var path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(function (link) {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
})();

/* Live character counter for textareas */
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


/* Log form stepper */
(function () {
  var stepper = document.querySelector('[data-stepper]');
  if (!stepper) return;

  var panels = Array.prototype.slice.call(stepper.querySelectorAll('.step-panel'));
  var pills = Array.prototype.slice.call(stepper.querySelectorAll('.step-pill'));
  var prevBtn = stepper.querySelector('[data-step-prev]');
  var nextBtn = stepper.querySelector('[data-step-next]');
  var submitBtn = stepper.querySelector('[data-step-submit]');
  var progressBar = stepper.querySelector('[data-step-progress]');
  var currentText = stepper.querySelector('[data-step-current]');
  var totalText = stepper.querySelector('[data-step-total]');

  var current = 0;
  var total = panels.length;

  if (totalText) totalText.textContent = total;

  function focusFirstField(panel) {
    if (!panel) return;
    var field = panel.querySelector('input, textarea, select');
    if (field) field.focus();
  }

  function updateStepper(index) {
    current = index;

    panels.forEach(function (panel, i) {
      panel.classList.toggle('is-active', i === current);
    });

    pills.forEach(function (pill, i) {
      pill.classList.toggle('is-active', i === current);
    });

    if (currentText) currentText.textContent = current + 1;
    if (progressBar) progressBar.style.width = (((current + 1) / total) * 100) + '%';

    prevBtn.disabled = current === 0;

    if (current === total - 1) {
      nextBtn.style.display = 'none';
      submitBtn.style.display = 'inline-flex';
    } else {
      nextBtn.style.display = 'inline-flex';
      submitBtn.style.display = 'none';
    }

    focusFirstField(panels[current]);
  }

  function validateCurrentStep() {
    var panel = panels[current];
    if (!panel) return true;

    var fields = panel.querySelectorAll('input, textarea, select');
    for (var i = 0; i < fields.length; i++) {
      var field = fields[i];

      if (field.type === 'hidden' || field.disabled) continue;

      if (!field.checkValidity()) {
        field.reportValidity();
        field.focus();
        return false;
      }
    }

    return true;
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', function () {
      if (!validateCurrentStep()) return;
      if (current < total - 1) updateStepper(current + 1);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', function () {
      if (current > 0) updateStepper(current - 1);
    });
  }

  pills.forEach(function (pill) {
    pill.addEventListener('click', function () {
      var target = parseInt(this.getAttribute('data-step-target'), 10);
      if (isNaN(target)) return;

      if (target <= current) {
        updateStepper(target);
        return;
      }

      if (!validateCurrentStep()) return;
      updateStepper(target);
    });
  });

  updateStepper(0);
})();