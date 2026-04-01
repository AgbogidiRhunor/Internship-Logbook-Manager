'use strict';

const API = (function () {

  function getCsrfToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    if (cookie) return cookie.split('=')[1].trim();
    const meta = document.querySelector('[name=csrfmiddlewaretoken]');
    return meta?.value || '';
  }

  async function request(url, opts = {}) {
    const { method = 'GET', data, json = true, headers = {} } = opts;
    const fetchOpts = {
      method,
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
        ...headers,
      },
      credentials: 'same-origin',
    };

    if (data) {
      if (data instanceof FormData) {
        fetchOpts.body = data;
      } else if (json) {
        fetchOpts.body = JSON.stringify(data);
        fetchOpts.headers['Content-Type'] = 'application/json';
      }
    }

    try {
      const resp = await fetch(url, fetchOpts);
      if (!resp.ok) {
        const error = await resp.json().catch(() => ({ message: resp.statusText }));
        throw new Error(error.message || `HTTP ${resp.status}`);
      }
      return await resp.json();
    } catch (err) {
      throw err;
    }
  }

  const get    = (url, opts) => request(url, { method: 'GET', ...opts });
  const post   = (url, data, opts) => request(url, { method: 'POST', data, ...opts });
  const put    = (url, data, opts) => request(url, { method: 'PUT', data, ...opts });
  const del    = (url, opts) => request(url, { method: 'DELETE', ...opts });

  return { request, get, post, put, delete: del };

})();
