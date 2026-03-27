from django.utils import timezone
from django.db.models import Count, Q, FloatField, ExpressionWrapper
from datetime import timedelta

from accounts.models import StudentProfile, CustomUser, UserRole
from logbook.models import DailyLogEntry
from institutions.models import Faculty, Department


def _today():
    return timezone.now().date()


def _week_start():
    today = _today()
    return today - timedelta(days=today.weekday())


def _month_start():
    today = _today()
    return today.replace(day=1)


# Coordinator Analytics 
def get_coordinator_analytics(coordinator_user):
    university = coordinator_user.coordinator_profile.university
    today = _today()
    week_start = _week_start()
    month_start = _month_start()

    students = StudentProfile.objects.filter(university=university).select_related(
        'user', 'faculty', 'department'
    )
    total_students = students.count()

    # Log counts
    uni_log_qs = DailyLogEntry.objects.filter(
        student__student_profile__university=university
    )
    logs_today = uni_log_qs.filter(entry_date=today).count()
    logs_week  = uni_log_qs.filter(entry_date__gte=week_start).count()
    logs_month = uni_log_qs.filter(entry_date__gte=month_start).count()

    # Submission compliance this week
    # A student is "compliant" if they have at least one log this week
    active_students = students.filter(user__is_active=True)
    active_count = active_students.count()
    submitted_this_week = active_students.filter(
        user__log_entries__entry_date__gte=week_start
    ).distinct().count()
    compliance_pct = round((submitted_this_week / active_count * 100) if active_count else 0)

    # Faculty-level analytics
    faculties = Faculty.objects.filter(
        university=university, is_active=True
    ).prefetch_related('students__user__log_entries')

    faculty_stats = []
    for faculty in faculties:
        fac_students = students.filter(faculty=faculty, user__is_active=True)
        fac_count = fac_students.count()
        if fac_count == 0:
            continue
        fac_submitted = fac_students.filter(
            user__log_entries__entry_date__gte=week_start
        ).distinct().count()
        fac_compliance = round(fac_submitted / fac_count * 100)
        total_logs = DailyLogEntry.objects.filter(
            student__student_profile__faculty=faculty
        ).count()
        avg_logs = round(total_logs / fac_count, 1) if fac_count else 0
        faculty_stats.append({
            'faculty': faculty,
            'student_count': fac_count,
            'submitted_this_week': fac_submitted,
            'compliance_pct': fac_compliance,
            'avg_logs_per_student': avg_logs,
        })

    faculty_stats.sort(key=lambda x: x['compliance_pct'], reverse=True)
    best_faculty  = faculty_stats[0]  if faculty_stats else None
    worst_faculty = faculty_stats[-1] if len(faculty_stats) > 1 else None

    # Department-level breakdown
    departments = Department.objects.filter(
        faculty__university=university, is_active=True
    ).select_related('faculty')

    dept_stats = []
    for dept in departments:
        dept_students = students.filter(department=dept, user__is_active=True)
        dept_count = dept_students.count()
        if dept_count == 0:
            continue
        dept_submitted = dept_students.filter(
            user__log_entries__entry_date__gte=week_start
        ).distinct().count()
        dept_compliance = round(dept_submitted / dept_count * 100)
        dept_stats.append({
            'department': dept,
            'faculty_name': dept.faculty.name,
            'student_count': dept_count,
            'submitted_this_week': dept_submitted,
            'compliance_pct': dept_compliance,
        })
    dept_stats.sort(key=lambda x: x['compliance_pct'], reverse=True)

    return {
        'university': university,
        'total_students': total_students,
        'active_count': active_count,
        'logs_today': logs_today,
        'logs_week': logs_week,
        'logs_month': logs_month,
        'submitted_this_week': submitted_this_week,
        'compliance_pct': compliance_pct,
        'faculty_stats': faculty_stats,
        'best_faculty': best_faculty,
        'worst_faculty': worst_faculty,
        'dept_stats': dept_stats,
        'week_start': week_start,
        'today': today,
    }


# Lecturer Analytics 
def get_lecturer_analytics(lecturer_user):
    lp = lecturer_user.lecturer_profile
    today = _today()
    week_start = _week_start()
    inactive_threshold = today - timedelta(days=3)

    students = StudentProfile.objects.filter(
        university=lp.university,
        faculty=lp.faculty,
        department=lp.department,
    ).select_related('user').order_by('surname', 'other_names')

    total_students = students.count()
    active_students   = students.filter(user__is_active=True)
    inactive_students = students.filter(user__is_active=False)
    active_count   = active_students.count()
    inactive_count = inactive_students.count()

    # Students who haven't logged in 3+ days (inactive by submission)
    submitted_recently = active_students.filter(
        user__log_entries__entry_date__gte=inactive_threshold
    ).distinct().values_list('user_id', flat=True)

    not_submitted_3days = active_students.exclude(
        user_id__in=submitted_recently
    )
    alert_count = not_submitted_3days.count()

    # Submitted today vs not
    submitted_today_ids = DailyLogEntry.objects.filter(
        entry_date=today,
        student__student_profile__university=lp.university,
        student__student_profile__faculty=lp.faculty,
        student__student_profile__department=lp.department,
    ).values_list('student_id', flat=True)
    submitted_today_count = len(set(submitted_today_ids))
    not_submitted_today   = active_count - submitted_today_count

    # Daily trend — last 7 days
    daily_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = DailyLogEntry.objects.filter(
            entry_date=day,
            student__student_profile__university=lp.university,
            student__student_profile__faculty=lp.faculty,
            student__student_profile__department=lp.department,
        ).count()
        daily_trend.append({'date': day, 'count': count, 'label': day.strftime('%a')})

    # Weekly trend — last 4 weeks
    weekly_trend = []
    for i in range(3, -1, -1):
        w_start = week_start - timedelta(weeks=i)
        w_end   = w_start + timedelta(days=6)
        count = DailyLogEntry.objects.filter(
            entry_date__gte=w_start,
            entry_date__lte=w_end,
            student__student_profile__university=lp.university,
            student__student_profile__faculty=lp.faculty,
            student__student_profile__department=lp.department,
        ).count()
        weekly_trend.append({
            'week': f"W/E {w_end.strftime('%d %b')}",
            'count': count,
        })

    # Per-student insights
    student_insights = []
    for sp in active_students:
        last_entry = sp.user.log_entries.order_by('-entry_date').first()
        last_date  = last_entry.entry_date if last_entry else None
        days_since = (today - last_date).days if last_date else None
        total_logs = sp.user.log_entries.count()
        # Irregular: any day with more than 1 log
        has_irregular = sp.user.log_entries.values('entry_date').annotate(
            c=Count('id')
        ).filter(c__gt=1).exists()
        submitted_today_flag = sp.user_id in submitted_today_ids
        student_insights.append({
            'profile': sp,
            'total_logs': total_logs,
            'last_log_date': last_date,
            'days_since_log': days_since,
            'is_flagged': days_since is not None and days_since >= 3,
            'has_irregular': has_irregular,
            'submitted_today': submitted_today_flag,
        })

    # Students with irregular patterns
    irregular_students = [s for s in student_insights if s['has_irregular']]
    flagged_students   = [s for s in student_insights if s['is_flagged']]

    return {
        'department': lp.department,
        'faculty': lp.faculty,
        'university': lp.university,
        'total_students': total_students,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'alert_count': alert_count,
        'submitted_today_count': submitted_today_count,
        'not_submitted_today': not_submitted_today,
        'daily_trend': daily_trend,
        'weekly_trend': weekly_trend,
        'student_insights': student_insights,
        'flagged_students': flagged_students,
        'irregular_students': irregular_students,
        'today': today,
        'week_start': week_start,
    }
