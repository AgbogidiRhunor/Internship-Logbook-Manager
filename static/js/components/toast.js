'use strict';

const Toast = (function () {

  let container;

  const ICONS = {
    success: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#22c55e" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="#22c55e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    warning: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2L14 13H2L8 2z" stroke="#f59e0b" stroke-width="1.5" stroke-linejoin="round"/><path d="M8 7v3M8 11.5v.5" stroke="#f59e0b" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    danger:  `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#ef4444" stroke-width="1.5"/><path d="M6 6l4 4M10 6l-4 4" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    info:    `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#3b82f6" stroke-width="1.5"/><path d="M8 7v5M8 5v.5" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  };

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  function show(type, title, message, duration = 4000) {
    const c = getContainer();
    const id = 'toast-' + Date.now();

    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${ICONS[type] || ICONS.info}</span>
      <div class="toast-content">
        <p class="toast-title">${title}</p>
        ${message ? `<p class="toast-message">${message}</p>` : ''}
      </div>
      <button class="toast-close" aria-label="Dismiss">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => dismiss(toast));
    c.appendChild(toast);

    if (duration > 0) setTimeout(() => dismiss(toast), duration);
    return toast;
  }

  function dismiss(toast) {
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }

  function success(title, message, duration) { return show('success', title, message, duration); }
  function warning(title, message, duration) { return show('warning', title, message, duration); }
  function danger(title, message, duration)  { return show('danger',  title, message, duration); }
  function info(title, message, duration)    { return show('info',    title, message, duration); }

  return { show, success, warning, danger, info };

})();
