from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse

from .models import University, Faculty, Department
from .forms import UniversityForm, FacultyForm, DepartmentForm


def _admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            return HttpResponseForbidden('Admin access required.')
        return view_func(request, *args, **kwargs)
    return wrapper


# Universities 
@login_required
@_admin_required
def university_list(request):
    universities = University.objects.prefetch_related('faculties').order_by('name')
    return render(request, 'institutions/university_list.html', {'universities': universities})


@login_required
@_admin_required
def university_create(request):
    form = UniversityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'University added.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/university_form.html', {'form': form, 'action': 'Add University'})


@login_required
@_admin_required
def university_edit(request, pk):
    university = get_object_or_404(University, pk=pk)
    form = UniversityForm(request.POST or None, instance=university)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'University updated.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/university_form.html', {'form': form, 'action': 'Edit University'})


@login_required
@_admin_required
def university_delete(request, pk):
    university = get_object_or_404(University, pk=pk)
    if request.method == 'POST':
        university.delete()
        messages.success(request, 'University deleted.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/confirm_delete.html', {'obj': university, 'type': 'University'})


# Faculties 
@login_required
@_admin_required
def faculty_create(request, university_id):
    university = get_object_or_404(University, pk=university_id)
    form = FacultyForm(request.POST or None, initial={'university': university})
    if request.method == 'POST' and form.is_valid():
        faculty = form.save(commit=False)
        faculty.university = university
        faculty.save()
        messages.success(request, f'Faculty added to {university.name}.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/faculty_form.html', {
        'form': form, 'university': university, 'action': 'Add Faculty'
    })


@login_required
@_admin_required
def faculty_edit(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    form = FacultyForm(request.POST or None, instance=faculty)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Faculty updated.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/faculty_form.html', {
        'form': form, 'university': faculty.university, 'action': 'Edit Faculty'
    })


@login_required
@_admin_required
def faculty_delete(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == 'POST':
        faculty.delete()
        messages.success(request, 'Faculty deleted.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/confirm_delete.html', {'obj': faculty, 'type': 'Faculty'})


# Departments 
@login_required
@_admin_required
def department_create(request, faculty_id):
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    form = DepartmentForm(request.POST or None, initial={'faculty': faculty})
    if request.method == 'POST' and form.is_valid():
        dept = form.save(commit=False)
        dept.faculty = faculty
        dept.save()
        messages.success(request, f'Department added to {faculty.name}.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/department_form.html', {
        'form': form, 'faculty': faculty, 'action': 'Add Department'
    })


@login_required
@_admin_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department updated.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/department_form.html', {
        'form': form, 'faculty': dept.faculty, 'action': 'Edit Department'
    })


@login_required
@_admin_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.delete()
        messages.success(request, 'Department deleted.')
        return redirect('institutions:university_list')
    return render(request, 'institutions/confirm_delete.html', {'obj': dept, 'type': 'Department'})


# AJAX: cascade faculty/department selects 
def get_faculties(request):
    """Return JSON list of faculties for a given university_id (used in registration forms)."""
    university_id = request.GET.get('university_id')
    faculties = Faculty.objects.filter(
        university_id=university_id, is_active=True
    ).values('id', 'name').order_by('name')
    return JsonResponse({'faculties': list(faculties)})


def get_departments(request):
    """Return JSON list of departments for a given faculty_id."""
    faculty_id = request.GET.get('faculty_id')
    departments = Department.objects.filter(
        faculty_id=faculty_id, is_active=True
    ).values('id', 'name').order_by('name')
    return JsonResponse({'departments': list(departments)})
