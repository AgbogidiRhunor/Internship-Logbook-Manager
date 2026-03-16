/* cascade_selects.js
   Dynamically populates Faculty and Department dropdowns
   based on University and Faculty selections in registration forms.
*/
'use strict';

(function () {
  var universitySelect  = document.querySelector('[name="university"]');
  var facultySelect     = document.querySelector('[name="faculty"]');
  var departmentSelect  = document.querySelector('[name="department"]');

  if (!universitySelect || !facultySelect) return;

  function setSelectOptions(select, items, placeholder) {
    var current = select.value;
    select.innerHTML = '<option value="">' + placeholder + '</option>';
    items.forEach(function (item) {
      var opt = document.createElement('option');
      opt.value = item.id;
      opt.textContent = item.name;
      if (String(item.id) === current) opt.selected = true;
      select.appendChild(opt);
    });
  }

  function loadFaculties(universityId) {
    if (!universityId) {
      setSelectOptions(facultySelect, [], '— Select Faculty —');
      if (departmentSelect) setSelectOptions(departmentSelect, [], '— Select Department —');
      return;
    }
    fetch('/institutions/ajax/faculties/?university_id=' + universityId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        setSelectOptions(facultySelect, data.faculties, '— Select Faculty —');
        if (departmentSelect) setSelectOptions(departmentSelect, [], '— Select Department —');
      });
  }

  function loadDepartments(facultyId) {
    if (!facultyId || !departmentSelect) return;
    fetch('/institutions/ajax/departments/?faculty_id=' + facultyId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        setSelectOptions(departmentSelect, data.departments, '— Select Department —');
      });
  }

  universitySelect.addEventListener('change', function () {
    loadFaculties(this.value);
  });

  facultySelect.addEventListener('change', function () {
    loadDepartments(this.value);
  });

  // On page load with pre-selected values (edit / error redisplay)
  if (universitySelect.value) loadFaculties(universitySelect.value);
  if (facultySelect.value && departmentSelect) loadDepartments(facultySelect.value);
})();
