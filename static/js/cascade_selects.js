'use strict';

(function () {
  var uniSelect  = document.querySelector('[name="university"]');
  var facSelect  = document.querySelector('[name="faculty"]');
  var deptSelect = document.querySelector('[name="department"]');

  if (!uniSelect || !facSelect) return;

  // Store the values Django re-rendered after a validation error
  var savedFacultyId    = facSelect.value;
  var savedDeptId       = deptSelect ? deptSelect.value : '';

  function clearSelect(sel, placeholder) {
    sel.innerHTML = '<option value="">' + placeholder + '</option>';
    sel.disabled = true;
  }

  function populateSelect(sel, items, placeholder, restoreId) {
    sel.innerHTML = '<option value="">' + placeholder + '</option>';
    items.forEach(function (item) {
      var opt = document.createElement('option');
      opt.value = item.id;
      opt.textContent = item.name;
      if (String(item.id) === String(restoreId)) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
    sel.disabled = items.length === 0;
  }

  function loadFaculties(universityId, restoreFacultyId, restoreDeptId) {
    clearSelect(facSelect, '— Select Faculty —');
    if (deptSelect) clearSelect(deptSelect, '— Select Department —');
    if (!universityId) return;

    fetch('/institutions/ajax/faculties/?university_id=' + encodeURIComponent(universityId), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (r) {
        if (!r.ok) throw new Error('server error');
        return r.json();
      })
      .then(function (data) {
        populateSelect(facSelect, data.faculties || [], '— Select Faculty —', restoreFacultyId);
        // After restoring faculty, load its departments if needed
        if (restoreFacultyId && facSelect.value) {
          loadDepartments(facSelect.value, restoreDeptId);
        }
      })
      .catch(function () {
        facSelect.innerHTML = '<option value="">— Failed to load, refresh page —</option>';
        facSelect.disabled = false;
      });
  }

  function loadDepartments(facultyId, restoreDeptId) {
    if (!deptSelect) return;
    clearSelect(deptSelect, '— Select Department —');
    if (!facultyId) return;

    fetch('/institutions/ajax/departments/?faculty_id=' + encodeURIComponent(facultyId), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (r) {
        if (!r.ok) throw new Error('server error');
        return r.json();
      })
      .then(function (data) {
        populateSelect(deptSelect, data.departments || [], '— Select Department —', restoreDeptId || '');
      })
      .catch(function () {
        deptSelect.innerHTML = '<option value="">— Failed to load, refresh page —</option>';
        deptSelect.disabled = false;
      });
  }

  // User interaction events
  uniSelect.addEventListener('change', function () {
    loadFaculties(this.value, '', '');
  });

  facSelect.addEventListener('change', function () {
    loadDepartments(this.value, '');
  });

  // On page load: restore previously selected values (after form validation error)
  if (uniSelect.value) {
    loadFaculties(uniSelect.value, savedFacultyId, savedDeptId);
  } else {
    // Nothing selected yet — disable dependents
    facSelect.disabled = true;
    if (deptSelect) deptSelect.disabled = true;
  }
})();
