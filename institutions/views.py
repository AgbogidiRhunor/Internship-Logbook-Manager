import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q

from .models import University, Faculty, Department
from .forms import UniversityForm, FacultyForm, DepartmentForm

try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


def _admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            return HttpResponseForbidden('Admin access required.')
        return view_func(request, *args, **kwargs)
    return wrapper


def _coordinator_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_coordinator:
            return HttpResponseForbidden('Access denied.')
        if not request.user.coordinator_approved:
            return HttpResponseForbidden('Your coordinator account is not yet approved.')
        return view_func(request, *args, **kwargs)
    return wrapper


# Admin 
@login_required
@_admin_required
def university_list(request):
    universities = University.objects.prefetch_related('faculties__departments').order_by('name')
    return render(request, 'pages/institutions/university_list.html', {'universities': universities})


@login_required
@_admin_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def university_create(request):
    form = UniversityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'University added.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'action': 'Add University',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def university_edit(request, pk):
    university = get_object_or_404(University, pk=pk)
    form = UniversityForm(request.POST or None, instance=university)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'University updated.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'action': 'Edit University',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
def university_delete(request, pk):
    university = get_object_or_404(University, pk=pk)
    if request.method == 'POST':
        university.delete()
        messages.success(request, 'University deleted.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/confirm_delete.html', {
        'obj': university, 'type': 'University',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def faculty_create(request, university_id):
    university = get_object_or_404(University, pk=university_id)
    form = FacultyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        faculty = form.save(commit=False)
        faculty.university = university
        faculty.save()
        messages.success(request, f'Faculty added to {university.name}.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'university': university, 'action': 'Add Faculty',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def faculty_edit(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    form = FacultyForm(request.POST or None, instance=faculty)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Faculty updated.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'university': faculty.university, 'action': 'Edit Faculty',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
def faculty_delete(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == 'POST':
        faculty.delete()
        messages.success(request, 'Faculty deleted.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/confirm_delete.html', {
        'obj': faculty, 'type': 'Faculty',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def department_create(request, faculty_id):
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        dept = form.save(commit=False)
        dept.faculty = faculty
        dept.save()
        messages.success(request, f'Department added to {faculty.name}.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'faculty': faculty, 'action': 'Add Department',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department updated.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'faculty': dept.faculty, 'action': 'Edit Department',
        'cancel_url': 'institutions:university_list',
    })


@login_required
@_admin_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.delete()
        messages.success(request, 'Department deleted.')
        return redirect('institutions:university_list')
    return render(request, 'pages/institutions/confirm_delete.html', {
        'obj': dept, 'type': 'Department',
        'cancel_url': 'institutions:university_list',
    })


# AJAX 
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def get_faculties(request):
    try:
        university_id = int(request.GET.get('university_id', ''))
        if university_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'faculties': []})
    faculties = Faculty.objects.filter(
        university_id=university_id, is_active=True
    ).values('id', 'name').order_by('name')
    return JsonResponse({'faculties': list(faculties)})


@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def get_departments(request):
    try:
        faculty_id = int(request.GET.get('faculty_id', ''))
        if faculty_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'departments': []})
    departments = Department.objects.filter(
        faculty_id=faculty_id, is_active=True
    ).values('id', 'name').order_by('name')
    return JsonResponse({'departments': list(departments)})


# Coordinator 
@login_required
@_coordinator_required
def coordinator_institution_view(request):
    university = request.user.coordinator_profile.university
    faculties  = Faculty.objects.filter(
        university=university
    ).prefetch_related('departments').order_by('name')
    return render(request, 'pages/institutions/coordinator_institution.html', {
        'university': university, 'faculties': faculties,
    })


@login_required
@_coordinator_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def coordinator_faculty_create(request):
    university = request.user.coordinator_profile.university
    form = FacultyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        faculty = form.save(commit=False)
        faculty.university = university
        faculty.save()
        messages.success(request, f'Faculty "{faculty.name}" added.')
        return redirect('institutions:coordinator_institution_view')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'university': university, 'action': 'Add Faculty',
        'cancel_url': 'institutions:coordinator_institution_view',
    })


@login_required
@_coordinator_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def coordinator_faculty_edit(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if faculty.university_id != request.user.coordinator_profile.university_id:
        return HttpResponseForbidden('This faculty does not belong to your university.')
    form = FacultyForm(request.POST or None, instance=faculty)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Faculty updated.')
        return redirect('institutions:coordinator_institution_view')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'university': faculty.university, 'action': 'Edit Faculty',
        'cancel_url': 'institutions:coordinator_institution_view',
    })


@login_required
@_coordinator_required
def coordinator_faculty_delete(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if faculty.university_id != request.user.coordinator_profile.university_id:
        return HttpResponseForbidden('This faculty does not belong to your university.')
    if request.method == 'POST':
        faculty.delete()
        messages.success(request, 'Faculty deleted.')
        return redirect('institutions:coordinator_institution_view')
    return render(request, 'pages/institutions/confirm_delete.html', {
        'obj': faculty, 'type': 'Faculty',
        'cancel_url': 'institutions:coordinator_institution_view',
    })


@login_required
@_coordinator_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def coordinator_department_create(request, faculty_id):
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    if faculty.university_id != request.user.coordinator_profile.university_id:
        return HttpResponseForbidden('This faculty does not belong to your university.')
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        dept = form.save(commit=False)
        dept.faculty = faculty
        dept.save()
        messages.success(request, f'Department "{dept.name}" added.')
        return redirect('institutions:coordinator_institution_view')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'faculty': faculty, 'action': 'Add Department',
        'cancel_url': 'institutions:coordinator_institution_view',
    })


@login_required
@_coordinator_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def coordinator_department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if dept.faculty.university_id != request.user.coordinator_profile.university_id:
        return HttpResponseForbidden('This department does not belong to your university.')
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department updated.')
        return redirect('institutions:coordinator_institution_view')
    return render(request, 'pages/institutions/form.html', {
        'form': form, 'faculty': dept.faculty, 'action': 'Edit Department',
        'cancel_url': 'institutions:coordinator_institution_view',
    })


@login_required
@_coordinator_required
def coordinator_department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if dept.faculty.university_id != request.user.coordinator_profile.university_id:
        return HttpResponseForbidden('This department does not belong to your university.')
    if request.method == 'POST':
        dept.delete()
        messages.success(request, 'Department deleted.')
        return redirect('institutions:coordinator_institution_view')
    return render(request, 'pages/institutions/confirm_delete.html', {
        'obj': dept, 'type': 'Department',
        'cancel_url': 'institutions:coordinator_institution_view',
    })


@login_required
@_coordinator_required
def coordinator_lecturer_list(request):
    from accounts.models import CustomUser, UserRole
    university = request.user.coordinator_profile.university
    q = request.GET.get('q', '').strip()[:100]
    lecturers = CustomUser.objects.filter(
        role=UserRole.LECTURER,
        lecturer_profile__university=university,
    ).select_related(
        'lecturer_profile__faculty',
        'lecturer_profile__department',
    ).order_by('lecturer_profile__surname', 'lecturer_profile__other_names')
    if q:
        lecturers = lecturers.filter(
            Q(username__icontains=q) |
            Q(lecturer_profile__surname__icontains=q) |
            Q(lecturer_profile__other_names__icontains=q) |
            Q(email__icontains=q)
        )
    return render(request, 'pages/institutions/coordinator_lecturer_list.html', {
        'lecturers': lecturers, 'q': q, 'university': university,
    })


@login_required
@_coordinator_required
def coordinator_suspend_lecturer(request, user_id):
    from accounts.models import CustomUser, UserRole
    from accounts.emails import notify_lecturer_suspended
    university = request.user.coordinator_profile.university
    lecturer = get_object_or_404(
        CustomUser, pk=user_id, role=UserRole.LECTURER,
        lecturer_profile__university=university,
    )
    lecturer.is_active = False
    lecturer.save(update_fields=['is_active'])
    notify_lecturer_suspended(lecturer)
    messages.warning(request, f'Lecturer {lecturer.username} suspended.')
    return redirect(request.META.get('HTTP_REFERER', '/institutions/coordinator/lecturers/'))


@login_required
@_coordinator_required
def coordinator_reactivate_lecturer(request, user_id):
    from accounts.models import CustomUser, UserRole
    from accounts.emails import notify_lecturer_reactivated
    university = request.user.coordinator_profile.university
    lecturer = get_object_or_404(
        CustomUser, pk=user_id, role=UserRole.LECTURER,
        lecturer_profile__university=university,
    )
    lecturer.is_active = True
    lecturer.failed_login_count = 0
    lecturer.locked_until = None
    lecturer.save(update_fields=['is_active', 'failed_login_count', 'locked_until'])
    notify_lecturer_reactivated(lecturer)
    messages.success(request, f'Lecturer {lecturer.username} reinstated.')
    return redirect(request.META.get('HTTP_REFERER', '/institutions/coordinator/lecturers/'))