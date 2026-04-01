'use strict';

const FormUtils = (function () {

  const RULES = {
    required: (v) => v.trim() !== '' || 'This field is required.',
    email:    (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Please enter a valid email address.',
    minLen:   (n) => (v) => v.length >= n || `Must be at least ${n} characters.`,
    maxLen:   (n) => (v) => v.length <= n || `Must be ${n} characters or fewer.`,
    match:    (other) => (v, form) => {
      const otherVal = form.querySelector(`[name="${other}"]`)?.value || '';
      return v === otherVal || 'Passwords do not match.';
    },
    pattern:  (re, msg) => (v) => re.test(v) || msg,
  };

  function validate(form, schema) {
    let valid = true;
    clearErrors(form);

    Object.entries(schema).forEach(([name, rules]) => {
      const field = form.querySelector(`[name="${name}"]`);
      if (!field) return;
      const value = field.value;

      for (const rule of rules) {
        const fn = typeof rule === 'function' ? rule : RULES[rule];
        if (!fn) continue;
        const result = fn(value, form);
        if (result !== true) {
          showError(field, result);
          valid = false;
          break;
        }
      }
    });

    return valid;
  }

  function showError(field, message) {
    field.classList.add('error');
    const existing = field.parentElement.querySelector('.form-error');
    if (!existing) {
      const err = document.createElement('span');
      err.className = 'form-error';
      err.textContent = message;
      field.parentElement.appendChild(err);
    }
  }

  function clearErrors(form) {
    form.querySelectorAll('.form-control').forEach(f => f.classList.remove('error', 'success'));
    form.querySelectorAll('.form-error').forEach(e => e.remove());
  }

  function clearFieldError(field) {
    field.classList.remove('error');
    field.parentElement.querySelector('.form-error')?.remove();
  }

  function initLiveValidation(form, schema) {
    Object.keys(schema).forEach(name => {
      const field = form.querySelector(`[name="${name}"]`);
      if (!field) return;
      field.addEventListener('blur', () => {
        clearFieldError(field);
        const rules = schema[name];
        for (const rule of rules) {
          const fn = typeof rule === 'function' ? rule : RULES[rule];
          if (!fn) continue;
          const result = fn(field.value, form);
          if (result !== true) {
            showError(field, result);
            break;
          } else {
            field.classList.add('success');
          }
        }
      });
    });
  }

  function serializeForm(form) {
    const data = {};
    new FormData(form).forEach((value, key) => {
      if (data[key] !== undefined) {
        if (!Array.isArray(data[key])) data[key] = [data[key]];
        data[key].push(value);
      } else {
        data[key] = value;
      }
    });
    return data;
  }

  function setLoading(btn, loading) {
    if (loading) {
      btn.dataset.originalText = btn.innerHTML;
      btn.innerHTML = `<span class="spinner spinner-sm"></span><span>${btn.dataset.loadingText || 'Loading...'}</span>`;
      btn.disabled = true;
    } else {
      btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
      btn.disabled = false;
    }
  }

  return { validate, showError, clearErrors, initLiveValidation, serializeForm, setLoading, RULES };

})();
