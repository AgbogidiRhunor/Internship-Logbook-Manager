'use strict';

const Modal = (function () {

  const openModals = new Set();

  function trapFocus(el) {
    const focusable = el.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last  = focusable[focusable.length - 1];
    if (!first) return;
    first.focus();
    el.addEventListener('keydown', function handler(e) {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last)  { e.preventDefault(); first.focus(); }
      }
    });
  }

  function open(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.add('open');
    openModals.add(id);
    document.body.style.overflow = 'hidden';
    const modal = overlay.querySelector('.modal');
    if (modal) setTimeout(() => trapFocus(modal), 50);
    overlay.dispatchEvent(new CustomEvent('modal:open'));
  }

  function close(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.remove('open');
    openModals.delete(id);
    if (openModals.size === 0) document.body.style.overflow = '';
    overlay.dispatchEvent(new CustomEvent('modal:close'));
  }

  function closeAll() {
    openModals.forEach(id => close(id));
  }

  function confirm(opts) {
    const id = 'confirm-modal-' + Date.now();
    const { title, message, confirmText = 'Confirm', cancelText = 'Cancel', onConfirm, danger = false } = opts;
    const html = `
      <div id="${id}" class="modal-overlay">
        <div class="modal modal-sm animate-scaleIn">
          <div class="modal-header">
            <div>
              <p class="modal-title">${title}</p>
              ${message ? `<p class="modal-subtitle">${message}</p>` : ''}
            </div>
            <button class="modal-close" data-modal-close="${id}" aria-label="Close">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" data-modal-close="${id}">${cancelText}</button>
            <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="${id}-confirm">${confirmText}</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
    const overlay = document.getElementById(id);
    const confirmBtn = document.getElementById(`${id}-confirm`);
    confirmBtn.addEventListener('click', () => {
      if (onConfirm) onConfirm();
      close(id);
      overlay.addEventListener('transitionend', () => overlay.remove(), { once: true });
    });
    overlay.addEventListener('modal:close', () => {
      setTimeout(() => overlay.remove(), 300);
    });
    setTimeout(() => open(id), 10);
  }

  function init() {
    document.addEventListener('click', (e) => {
      const trigger = e.target.closest('[data-modal-open]');
      if (trigger) {
        e.preventDefault();
        open(trigger.dataset.modalOpen);
        return;
      }
      const closer = e.target.closest('[data-modal-close]');
      if (closer) {
        e.preventDefault();
        close(closer.dataset.modalClose);
        return;
      }
      const overlay = e.target.closest('.modal-overlay');
      if (overlay && e.target === overlay) {
        const id = overlay.id;
        if (id) close(id);
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && openModals.size > 0) {
        const last = [...openModals].pop();
        close(last);
      }
    });
  }

  init();

  return { open, close, closeAll, confirm };

})();
