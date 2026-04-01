'use strict';

const SIWES = (function () {

  // ── Theme ───────────────────────────────────────────────────────
  const Theme = {
    STORAGE_KEY: 'siwes-theme',

    get() {
      return localStorage.getItem(this.STORAGE_KEY)
        || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    },

    set(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem(this.STORAGE_KEY, theme);
      document.dispatchEvent(new CustomEvent('siwes:themechange', { detail: { theme } }));
    },

    toggle() {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      this.set(current === 'dark' ? 'light' : 'dark');
    },

    init() {
      this.set(this.get());
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(this.STORAGE_KEY)) {
          this.set(e.matches ? 'dark' : 'light');
        }
      });
    }
  };

  // ── Sidebar ─────────────────────────────────────────────────────
  const Sidebar = {
    STORAGE_KEY: 'siwes-sidebar',
    el: null,

    init() {
      this.el = document.querySelector('.sidebar');
      if (!this.el) return;

      const collapsed = localStorage.getItem(this.STORAGE_KEY) === 'true';
      if (collapsed) this.collapse(false);

      const toggleBtn = document.querySelector('[data-sidebar-toggle]');
      if (toggleBtn) toggleBtn.addEventListener('click', () => this.toggle());

      const mobileBtn = document.querySelector('[data-sidebar-mobile]');
      if (mobileBtn) mobileBtn.addEventListener('click', () => this.mobileOpen());

      const overlay = document.querySelector('.sidebar-mobile-overlay');
      if (overlay) overlay.addEventListener('click', () => this.mobileClose());
    },

    collapse(save = true) {
      this.el.classList.add('collapsed');
      document.body.classList.add('sidebar-collapsed');
      if (save) localStorage.setItem(this.STORAGE_KEY, 'true');
    },

    expand(save = true) {
      this.el.classList.remove('collapsed');
      document.body.classList.remove('sidebar-collapsed');
      if (save) localStorage.setItem(this.STORAGE_KEY, 'false');
    },

    toggle() {
      if (this.el.classList.contains('collapsed')) this.expand();
      else this.collapse();
    },

    mobileOpen() {
      this.el.classList.add('mobile-open');
      document.querySelector('.sidebar-mobile-overlay')?.classList.add('active');
    },

    mobileClose() {
      this.el.classList.remove('mobile-open');
      document.querySelector('.sidebar-mobile-overlay')?.classList.remove('active');
    }
  };

  // ── Router helpers ──────────────────────────────────────────────
  const Router = {
    init() {
      const path = window.location.pathname;
      document.querySelectorAll('.sidebar-item[href]').forEach(link => {
        if (link.getAttribute('href') === path || path.startsWith(link.getAttribute('href') + '/')) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      });
    }
  };

  // ── Init ────────────────────────────────────────────────────────
  function init() {
    Theme.init();
    document.addEventListener('DOMContentLoaded', () => {
      Sidebar.init();
      Router.init();

      // Theme toggle buttons
      document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
        btn.addEventListener('click', () => Theme.toggle());
      });

      // Mark page as loaded
      document.body.classList.add('loaded');
    });
  }

  init();

  return { Theme, Sidebar, Router };

})();
