'use strict';

const Helpers = (function () {

  function debounce(fn, delay) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function throttle(fn, limit) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        fn.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  function formatDate(dateStr, opts = {}) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    const defaults = { day: '2-digit', month: 'short', year: 'numeric' };
    return date.toLocaleDateString('en-NG', { ...defaults, ...opts });
  }

  function timeAgo(dateStr) {
    if (!dateStr) return '';
    const seconds = Math.floor((new Date() - new Date(dateStr)) / 1000);
    const intervals = [
      [31536000, 'year'],
      [2592000,  'month'],
      [604800,   'week'],
      [86400,    'day'],
      [3600,     'hour'],
      [60,       'minute'],
    ];
    for (const [s, label] of intervals) {
      const count = Math.floor(seconds / s);
      if (count >= 1) return `${count} ${label}${count > 1 ? 's' : ''} ago`;
    }
    return 'just now';
  }

  function truncate(str, n) {
    return str && str.length > n ? str.slice(0, n) + '…' : str;
  }

  function initials(name) {
    if (!name) return '?';
    return name.trim().split(/\s+/).slice(0, 2).map(w => w[0].toUpperCase()).join('');
  }

  function copyToClipboard(text) {
    if (navigator.clipboard) {
      return navigator.clipboard.writeText(text);
    }
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    return Promise.resolve();
  }

  function animateCounter(el, to, duration = 1000) {
    const from = parseFloat(el.textContent.replace(/[^0-9.-]/g, '')) || 0;
    const startTime = performance.now();
    const update = (time) => {
      const elapsed = time - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(from + (to - from) * eased).toLocaleString();
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  function observeIntersection(els, callback, opts = {}) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          callback(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, ...opts });

    (Array.isArray(els) ? els : [els]).forEach(el => observer.observe(el));
    return observer;
  }

  return {
    debounce, throttle, formatDate, timeAgo, truncate,
    initials, copyToClipboard, animateCounter, observeIntersection,
  };

})();
