from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from accounts.models import StudentProfile, LecturerProfile, CustomUser, UserRole
from logbook.models import DailyLogEntry
from grading.models import GradeRecord
from institutions.models import University, Faculty, Department


@login_required
def home(request):
    user = request.user
    if user.is_student:
        return student_dashboard(request)
    elif user.is_lecturer:
        if not user.lecturer_approved:
            return render(request, 'accounts/awaiting_approval.html')
        return lecturer_dashboard(request)
    elif user.is_admin:
        return admin_dashboard(request)
    return redirect('accounts:login')


def student_dashboard(request):
    profile = request.user.student_profile
    today = timezone.now().date()

    recent_entries = DailyLogEntry.objects.filter(
        student=request.user
    ).order_by('-entry_date')[:5]

    grade = getattr(profile, 'grade_record', None)

    context = {
        'profile': profile,
        'today': today,
        'recent_entries': recent_entries,
        'grade': grade,
        'days_logged': profile.days_logged,
        'days_remaining': profile.days_remaining,
        'total_days': profile.total_internship_days,
        'progress': profile.progress_percentage,
    }
    return render(request, 'dashboard/student_dashboard.html', context)


def lecturer_dashboard(request):
    from grading.views import _get_lecturer_students
    students = _get_lecturer_students(request.user)
    total = students.count()
    graded = students.filter(grade_record__isnull=False).count()
    not_graded = total - graded

    context = {
        'profile': request.user.lecturer_profile,
        'total_students': total,
        'graded_count': graded,
        'not_graded_count': not_graded,
        'recent_students': students[:10],
    }
    return render(request, 'dashboard/lecturer_dashboard.html', context)


def admin_dashboard(request):
    total_students = CustomUser.objects.filter(role=UserRole.STUDENT, is_active=True).count()
    total_lecturers = CustomUser.objects.filter(role=UserRole.LECTURER, is_active=True).count()
    pending_approvals = CustomUser.objects.filter(
        role=UserRole.LECTURER, lecturer_approved=False, is_active=True
    ).count()
    total_logs = DailyLogEntry.objects.count()
    total_grades = GradeRecord.objects.count()
    total_universities = University.objects.filter(is_active=True).count()

    context = {
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'pending_approvals': pending_approvals,
        'total_logs': total_logs,
        'total_grades': total_grades,
        'total_universities': total_universities,
        'recent_logs': DailyLogEntry.objects.select_related(
            'student__student_profile'
        ).order_by('-created_at')[:8],
    }
    return render(request, 'dashboard/admin_dashboard.html', context)
