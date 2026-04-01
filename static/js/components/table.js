'use strict';

class SIWESTable {
  constructor(selector, opts = {}) {
    this.table = typeof selector === 'string' ? document.querySelector(selector) : selector;
    if (!this.table) return;

    this.opts = { sortable: true, searchable: true, pageSize: 0, ...opts };
    this.originalRows = [];
    this.sortState = { col: -1, dir: 'asc' };
    this.filterText = '';

    this._captureRows();
    if (this.opts.sortable) this._initSort();
    if (this.opts.searchable) this._initSearch();
    if (this.opts.pageSize > 0) this._initPagination();
  }

  _captureRows() {
    this.tbody = this.table.querySelector('tbody');
    if (!this.tbody) return;
    this.originalRows = [...this.tbody.querySelectorAll('tr')];
  }

  _initSort() {
    const ths = this.table.querySelectorAll('th.sortable');
    ths.forEach((th, i) => {
      const actualIndex = [...th.parentElement.children].indexOf(th);
      th.addEventListener('click', () => this._sort(th, actualIndex));

      if (!th.querySelector('.sort-icon')) {
        th.insertAdjacentHTML('beforeend', `
          <span class="sort-icon" aria-hidden="true">
            <span class="asc-arrow"></span>
            <span class="desc-arrow"></span>
          </span>
        `);
      }
    });
  }

  _sort(th, colIndex) {
    const thead = this.table.querySelector('thead');
    thead.querySelectorAll('th').forEach(t => {
      t.classList.remove('sort-asc', 'sort-desc');
    });

    if (this.sortState.col === colIndex) {
      this.sortState.dir = this.sortState.dir === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortState.col = colIndex;
      this.sortState.dir = 'asc';
    }

    th.classList.add(`sort-${this.sortState.dir}`);

    const rows = [...this.tbody.querySelectorAll('tr')];
    rows.sort((a, b) => {
      const aVal = a.cells[colIndex]?.textContent.trim() || '';
      const bVal = b.cells[colIndex]?.textContent.trim() || '';
      const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
      const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
      const compare = isNaN(aNum) || isNaN(bNum)
        ? aVal.localeCompare(bVal)
        : aNum - bNum;
      return this.sortState.dir === 'asc' ? compare : -compare;
    });

    rows.forEach(row => this.tbody.appendChild(row));
    this._checkEmpty();
  }

  _initSearch() {
    const searchInput = document.querySelector(`[data-table-search="${this.table.id}"]`);
    if (!searchInput) return;
    searchInput.addEventListener('input', (e) => {
      this.filterText = e.target.value.toLowerCase().trim();
      this._filter();
    });
  }

  _filter() {
    this.originalRows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = (!this.filterText || text.includes(this.filterText)) ? '' : 'none';
    });
    this._checkEmpty();
  }

  _checkEmpty() {
    const visibleRows = this.originalRows.filter(r => r.style.display !== 'none');
    let emptyRow = this.tbody.querySelector('.table-empty-row');
    if (visibleRows.length === 0) {
      if (!emptyRow) {
        emptyRow = document.createElement('tr');
        emptyRow.className = 'table-empty-row';
        emptyRow.innerHTML = `<td colspan="99" class="table-empty">
          <div class="table-empty-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <rect width="48" height="48" rx="12" fill="currentColor" opacity="0.05"/>
              <path d="M16 20h16M16 28h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <p style="margin-top:12px;font-size:14px;font-weight:600;color:var(--text-primary)">No results found</p>
          <p style="font-size:13px;color:var(--text-tertiary);margin-top:4px">Try adjusting your search or filters</p>
        </td>`;
        this.tbody.appendChild(emptyRow);
      }
    } else if (emptyRow) {
      emptyRow.remove();
    }
  }

  _initPagination() {
    // Simple pagination — can be extended
    let page = 0;
    const pageSize = this.opts.pageSize;
    const totalPages = () => Math.ceil(this.originalRows.length / pageSize);

    const showPage = (p) => {
      page = Math.max(0, Math.min(p, totalPages() - 1));
      this.originalRows.forEach((row, i) => {
        row.style.display = (i >= page * pageSize && i < (page + 1) * pageSize) ? '' : 'none';
      });
      this._updatePaginationUI();
    };

    this._updatePaginationUI = () => {
      const ctrl = document.querySelector(`[data-table-pagination="${this.table.id}"]`);
      if (!ctrl) return;
      ctrl.innerHTML = `
        <button class="btn btn-secondary btn-sm" ${page === 0 ? 'disabled' : ''} onclick="this.dispatchEvent(new CustomEvent('prev', {bubbles:true}))">←</button>
        <span style="font-size:13px;color:var(--text-secondary)">Page ${page + 1} of ${totalPages()}</span>
        <button class="btn btn-secondary btn-sm" ${page >= totalPages() - 1 ? 'disabled' : ''} onclick="this.dispatchEvent(new CustomEvent('next', {bubbles:true}))">→</button>
      `;
    };

    showPage(0);
  }
}
