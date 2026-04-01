from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from accounts.models import StudentProfile, LecturerProfile, CustomUser, UserRole, CoordinatorProfile
from logbook.models import DailyLogEntry
from grading.models import GradeRecord
from institutions.models import University, Faculty, Department
from .analytics import get_coordinator_analytics, get_lecturer_analytics


@login_required
def home(request):
    user = request.user
    if user.is_student:
        return student_dashboard(request)
    elif user.is_lecturer:
        if not user.lecturer_approved:
            return render(request, 'pages/auth/awaiting_approval.html')
        return lecturer_dashboard(request)
    elif user.is_coordinator:
        if not user.coordinator_approved:
            return render(request, 'pages/auth/awaiting_approval.html')
        return coordinator_dashboard(request)
    elif user.is_admin:
        return admin_dashboard(request)
    return redirect('accounts:login')


def _time_of_day():
    hour = timezone.now().hour
    if hour < 12:
        return 'morning'
    elif hour < 17:
        return 'afternoon'
    return 'evening'


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
        'time_of_day': _time_of_day(),
        'recent_entries': recent_entries,
        'grade': grade,
        'days_logged': profile.days_logged,
        'days_remaining': profile.days_remaining,
        'total_days': profile.total_internship_days,
        'progress': profile.progress_percentage,
    }
    return render(request, 'pages/dashboard/student_dashboard.html', context)


def lecturer_dashboard(request):
    data = get_lecturer_analytics(request.user)
    data['profile'] = request.user.lecturer_profile
    return render(request, 'pages/dashboard/lecturer_dashboard.html', data)


def coordinator_dashboard(request):
    data = get_coordinator_analytics(request.user)
    data['profile'] = request.user.coordinator_profile
    cp = request.user.coordinator_profile
    data['pending_lecturers_count'] = CustomUser.objects.filter(
        role=UserRole.LECTURER, lecturer_approved=False, is_active=True,
        lecturer_profile__university=cp.university,
    ).count()
    return render(request, 'pages/dashboard/coordinator_dashboard.html', data)


def admin_dashboard(request):
    total_students = CustomUser.objects.filter(role=UserRole.STUDENT, is_active=True).count()
    total_lecturers = CustomUser.objects.filter(role=UserRole.LECTURER, is_active=True).count()
    total_coordinators = CustomUser.objects.filter(role=UserRole.COORDINATOR, is_active=True).count()
    pending_approvals = CustomUser.objects.filter(
        role=UserRole.LECTURER, lecturer_approved=False, is_active=True
    ).count()
    pending_coordinators = CustomUser.objects.filter(
        role=UserRole.COORDINATOR, coordinator_approved=False, is_active=True
    ).count()
    total_logs = DailyLogEntry.objects.count()
    total_grades = GradeRecord.objects.count()
    total_universities = University.objects.filter(is_active=True).count()
    context = {
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'total_coordinators': total_coordinators,
        'pending_approvals': pending_approvals,
        'pending_coordinators': pending_coordinators,
        'total_logs': total_logs,
        'total_grades': total_grades,
        'total_universities': total_universities,
        'recent_logs': DailyLogEntry.objects.select_related(
            'student__student_profile'
        ).order_by('-created_at')[:8],
    }
    return render(request, 'pages/dashboard/admin_dashboard.html', context)