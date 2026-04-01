'use strict';

const Dropdown = (function () {

  const openMenus = new Set();

  function open(id) {
    const menu = document.getElementById(id);
    if (!menu) return;
    closeAll();
    menu.classList.add('open');
    openMenus.add(id);
  }

  function close(id) {
    const menu = document.getElementById(id);
    if (!menu) return;
    menu.classList.remove('open');
    openMenus.delete(id);
  }

  function toggle(id) {
    if (openMenus.has(id)) close(id);
    else open(id);
  }

  function closeAll() {
    openMenus.forEach(id => close(id));
  }

  function init() {
    document.addEventListener('click', (e) => {
      const trigger = e.target.closest('[data-dropdown-trigger]');
      if (trigger) {
        e.stopPropagation();
        toggle(trigger.dataset.dropdownTrigger);
        return;
      }
      if (!e.target.closest('.dropdown-menu')) closeAll();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeAll();
    });
  }

  init();
  return { open, close, toggle, closeAll };

})();
