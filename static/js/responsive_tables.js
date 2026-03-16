document.addEventListener('DOMContentLoaded', function () {
  const tables = document.querySelectorAll('.data-table');

  tables.forEach((table) => {
    const headers = Array.from(table.querySelectorAll('thead th')).map((th) => th.textContent.trim());
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach((row) => {
      const cells = row.querySelectorAll('td');
      cells.forEach((cell, index) => {
        if (!cell.hasAttribute('data-label') && headers[index]) {
          cell.setAttribute('data-label', headers[index]);
        }
      });
    });
  });

  const sidebar = document.querySelector('.sidebar');
  const toggle = document.querySelector('.sidebar-toggle');

  if (sidebar && toggle) {
    let overlay = document.querySelector('.sidebar-overlay');

    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'sidebar-overlay';
      document.body.appendChild(overlay);
    }

    const closeSidebar = () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
      document.body.classList.remove('sidebar-open');
    };

    const openSidebar = () => {
      sidebar.classList.add('open');
      overlay.classList.add('show');
      document.body.classList.add('sidebar-open');
    };

    toggle.addEventListener('click', function () {
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    overlay.addEventListener('click', closeSidebar);

    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) {
        closeSidebar();
      }
    });
  }
});
