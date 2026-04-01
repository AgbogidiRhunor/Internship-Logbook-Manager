import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q

from accounts.models import StudentProfile, CustomUser
from accounts.views import _log_audit
from logbook.models import DailyLogEntry
from .models import GradeRecord
from .forms import GradeRecordForm
from .exports import export_grades_csv, export_grades_pdf
from accounts.emails import notify_student_graded

try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)

_ALLOWED_GRADED_FILTERS = {'yes', 'no', ''}
_MAX_SEARCH_LEN = 100


def _lecturer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Login required.')
        if not request.user.is_lecturer or not request.user.lecturer_approved:
            return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_lecturer_students(lecturer_user):
    lp = lecturer_user.lecturer_profile
    return StudentProfile.objects.filter(
        university=lp.university,
        faculty=lp.faculty,
        department=lp.department,
    ).select_related(
        'user', 'university', 'faculty', 'department'
    ).prefetch_related('grade_record').order_by('surname', 'other_names')


def _in_scope(student, lecturer_user):
    lp = lecturer_user.lecturer_profile
    return (
        student.university_id == lp.university_id and
        student.faculty_id    == lp.faculty_id and
        student.department_id == lp.department_id
    )


@login_required
@_lecturer_required
def student_list(request):
    students = _get_lecturer_students(request.user)
    q = request.GET.get('q', '').strip()[:_MAX_SEARCH_LEN]
    if q:
        students = students.filter(
            Q(surname__icontains=q) |
            Q(other_names__icontains=q) |
            Q(matric_number__icontains=q)
        )
    graded_filter = request.GET.get('graded', '')
    if graded_filter not in _ALLOWED_GRADED_FILTERS:
        graded_filter = ''
    if graded_filter == 'yes':
        students = students.filter(grade_record__isnull=False)
    elif graded_filter == 'no':
        students = students.filter(grade_record__isnull=True)
    return render(request, 'pages/grading/student_list.html', {
        'students': students, 'q': q, 'graded_filter': graded_filter,
    })


@login_required
@_lecturer_required
def student_profile_view(request, student_id):
    student = get_object_or_404(StudentProfile, pk=student_id)
    if not _in_scope(student, request.user):
        logger.warning('IDOR: lecturer %s tried to view student %s', request.user.username, student_id)
        _log_audit(request.user, 'idor_attempt_view_student', 'StudentProfile', student_id, request=request)
        return HttpResponseForbidden('This student is outside your scope.')
    entries = DailyLogEntry.objects.filter(student=student.user).order_by('-entry_date')
    grade = getattr(student, 'grade_record', None)
    return render(request, 'pages/grading/student_profile.html', {
        'student': student, 'entries': entries, 'grade': grade,
    })


@login_required
@_lecturer_required
def student_entry_detail(request, student_id, entry_id):
    student = get_object_or_404(StudentProfile, pk=student_id)
    if not _in_scope(student, request.user):
        _log_audit(request.user, 'idor_attempt_view_entry', 'DailyLogEntry', entry_id, request=request)
        return HttpResponseForbidden('This student is outside your scope.')
    entry = get_object_or_404(DailyLogEntry, pk=entry_id, student=student.user)
    return render(request, 'pages/grading/entry_detail.html', {
        'student': student, 'entry': entry,
    })


@login_required
@_lecturer_required
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def grade_student(request, student_id):
    student = get_object_or_404(StudentProfile, pk=student_id)
    if not _in_scope(student, request.user):
        _log_audit(request.user, 'idor_attempt_grade_student', 'StudentProfile', student_id, request=request)
        return HttpResponseForbidden('This student is outside your scope.')
    existing_grade = getattr(student, 'grade_record', None)
    form = GradeRecordForm(request.POST or None, instance=existing_grade)
    if request.method == 'POST' and form.is_valid():
        is_new_grade = existing_grade is None
        grade = form.save(commit=False)
        grade.student   = student
        grade.graded_by = request.user
        grade.save()
        _log_audit(request.user, 'grade_submitted', 'StudentProfile', student_id,
                   details=f'score={grade.overall_score} letter={grade.letter_grade}', request=request)
        if is_new_grade:
            notify_student_graded(student)
        messages.success(request, f'{student.full_name} graded successfully.')
        return redirect('grading:student_profile', student_id=student_id)
    return render(request, 'pages/grading/grade_form.html', {
        'form': form, 'student': student, 'existing_grade': existing_grade,
    })


@login_required
@_lecturer_required
@ratelimit(key='ip', rate='10/m', method='GET', block=True)
def export_csv(request):
    students = _get_lecturer_students(request.user).filter(grade_record__isnull=False)
    _log_audit(request.user, 'export_csv', request=request)
    return export_grades_csv(students, request.user)


@login_required
@_lecturer_required
@ratelimit(key='ip', rate='6/m', method='GET', block=True)
def export_pdf(request):
    students = _get_lecturer_students(request.user).filter(grade_record__isnull=False)
    _log_audit(request.user, 'export_pdf', request=request)
    return export_grades_pdf(students, request.user)