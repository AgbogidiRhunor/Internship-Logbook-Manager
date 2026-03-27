import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q

try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .forms import StudentRegistrationForm, LecturerRegistrationForm, CoordinatorRegistrationForm, SIWESLoginForm
from .models import CustomUser, UserRole, AuditLog, CoordinatorProfile
from .emails import (
    notify_lecturer_registration_pending,
    notify_coordinator_new_lecturer,
    notify_lecturer_approved,
    notify_lecturer_rejected,
    notify_coordinator_registration_pending,
    notify_admins_new_coordinator,
    notify_coordinator_approved,
    notify_coordinator_rejected,
    notify_student_suspended,
    notify_student_reactivated,
    notify_lecturer_suspended,
    notify_lecturer_reactivated,
)

logger = logging.getLogger(__name__)


def _get_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _log_audit(actor, action, target_model='', target_id='', details='', request=None):
    AuditLog.objects.create(
        actor=actor, action=action, target_model=target_model,
        target_id=str(target_id), details=details,
        ip_address=_get_ip(request) if request else None,
    )


def _require_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


def _require_coordinator(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_coordinator:
            return HttpResponseForbidden('Access denied.')
        if not request.user.coordinator_approved:
            return render(request, 'accounts/awaiting_approval.html')
        return view_func(request, *args, **kwargs)
    return wrapper


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return redirect('accounts:login')


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@ratelimit(key='post:username', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = SIWESLoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        username_raw = request.POST.get('username', '').strip().lower()
        try:
            candidate = CustomUser.objects.get(username=username_raw)
            if candidate.is_locked:
                remaining = int((candidate.locked_until - timezone.now()).total_seconds() // 60)
                messages.error(request, f'Account locked. Try again in {remaining} minute(s).')
                _log_audit(None, 'login_blocked_locked', details=f'ip={_get_ip(request)}', request=request)
                return render(request, 'accounts/login.html', {'form': form})
        except CustomUser.DoesNotExist:
            candidate = None

        if form.is_valid():
            user = form.get_user()
            if user.is_lecturer and not user.lecturer_approved:
                _log_audit(user, 'login_blocked_unapproved', request=request)
                return render(request, 'accounts/awaiting_approval.html', {'user': user})
            if user.is_coordinator and not user.coordinator_approved:
                _log_audit(user, 'login_blocked_coordinator_unapproved', request=request)
                return render(request, 'accounts/awaiting_approval.html', {'user': user})
            if not user.is_active:
                _log_audit(user, 'login_blocked_suspended', request=request)
                messages.error(request, 'Your account has been suspended.')
                return redirect('accounts:login')
            user.reset_failed_login()
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            login(request, user)
            _log_audit(user, 'login_success', request=request)
            return redirect('dashboard:home')
        else:
            ip = _get_ip(request)
            logger.warning('Failed login | ip=%s | hint=%s', ip, username_raw[:3] + '***' if username_raw else '')
            if candidate:
                candidate.record_failed_login()
                if candidate.is_locked:
                    _log_audit(None, 'account_locked', 'CustomUser', candidate.pk, details=f'ip={ip}', request=request)
            _log_audit(None, 'login_failed', details=f'ip={ip}', request=request)
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        _log_audit(request.user, 'logout', request=request)
    logout(request)
    return redirect('accounts:login')


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def student_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = StudentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        _log_audit(user, 'student_registered', request=request)
        messages.success(request, 'Account created successfully. Welcome!')
        return redirect('dashboard:home')
    return render(request, 'accounts/student_register.html', {'form': form})


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def lecturer_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = LecturerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lecturer_user = form.save()
        _log_audit(lecturer_user, 'lecturer_registered_pending', request=request)
        notify_lecturer_registration_pending(lecturer_user)
        notify_coordinator_new_lecturer(lecturer_user)
        messages.info(request, 'Registration submitted. Your School Coordinator will review your account.')
        return redirect('accounts:awaiting_approval')
    return render(request, 'accounts/lecturer_register.html', {'form': form})


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def coordinator_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = CoordinatorRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        coordinator_user = form.save()
        _log_audit(coordinator_user, 'coordinator_registered_pending', request=request)
        notify_coordinator_registration_pending(coordinator_user)
        notify_admins_new_coordinator(coordinator_user)
        messages.info(request, 'Registration submitted. An administrator will review your account.')
        return redirect('accounts:awaiting_approval')
    return render(request, 'accounts/coordinator_register.html', {'form': form})


def awaiting_approval_view(request):
    return render(request, 'accounts/awaiting_approval.html')


# Admin: Coordinator management 
@login_required
@_require_admin
def pending_coordinators(request):
    pending = CustomUser.objects.filter(
        role=UserRole.COORDINATOR, coordinator_approved=False, is_active=True,
    ).select_related('coordinator_profile__university')
    return render(request, 'accounts/pending_coordinators.html', {'pending': pending})


@login_required
@_require_admin
def approve_coordinator(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.COORDINATOR)
    user.coordinator_approved = True
    user.save(update_fields=['coordinator_approved'])
    _log_audit(request.user, 'approve_coordinator', 'CustomUser', user_id, request=request)
    notify_coordinator_approved(user)
    messages.success(request, f'Coordinator {user.username} approved.')
    return redirect('accounts:pending_coordinators')


@login_required
@_require_admin
def reject_coordinator(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.COORDINATOR)
    user.is_active = False
    user.save(update_fields=['is_active'])
    _log_audit(request.user, 'reject_coordinator', 'CustomUser', user_id, request=request)
    notify_coordinator_rejected(user)
    messages.warning(request, f'Coordinator {user.username} rejected.')
    return redirect('accounts:pending_coordinators')


# Admin: Lecturer management 
@login_required
@_require_admin
def pending_lecturers(request):
    pending = CustomUser.objects.filter(
        role=UserRole.LECTURER, lecturer_approved=False, is_active=True,
    ).select_related('lecturer_profile__university', 'lecturer_profile__faculty', 'lecturer_profile__department')
    return render(request, 'accounts/pending_lecturers.html', {'pending': pending})


@login_required
@_require_admin
def approve_lecturer(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.LECTURER)
    user.lecturer_approved = True
    user.save(update_fields=['lecturer_approved'])
    _log_audit(request.user, 'approve_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_approved(user)
    messages.success(request, f'Lecturer {user.username} approved.')
    return redirect('accounts:pending_lecturers')


@login_required
@_require_admin
def reject_lecturer(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.LECTURER)
    user.is_active = False
    user.save(update_fields=['is_active'])
    _log_audit(request.user, 'reject_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_rejected(user)
    messages.warning(request, f'Lecturer {user.username} rejected.')
    return redirect('accounts:pending_lecturers')


@login_required
@_require_admin
def suspend_lecturer(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.LECTURER)
    user.is_active = False
    user.save(update_fields=['is_active'])
    _log_audit(request.user, 'suspend_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_suspended(user)
    messages.warning(request, f'Lecturer {user.username} suspended.')
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))


@login_required
@_require_admin
def reactivate_lecturer(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.LECTURER)
    user.is_active = True
    user.failed_login_count = 0
    user.locked_until = None
    user.save(update_fields=['is_active', 'failed_login_count', 'locked_until'])
    _log_audit(request.user, 'reactivate_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_reactivated(user)
    messages.success(request, f'Lecturer {user.username} reinstated.')
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))


@login_required
@_require_admin
def admin_lecturer_list(request):
    q = request.GET.get('q', '').strip()[:100]
    lecturers = CustomUser.objects.filter(role=UserRole.LECTURER).select_related(
        'lecturer_profile__university', 'lecturer_profile__faculty', 'lecturer_profile__department',
    ).order_by('username')
    if q:
        lecturers = lecturers.filter(
            Q(username__icontains=q) | Q(lecturer_profile__surname__icontains=q) |
            Q(lecturer_profile__other_names__icontains=q) | Q(email__icontains=q)
        )
    return render(request, 'accounts/admin_lecturer_list.html', {'lecturers': lecturers, 'q': q})


# Coordinator: Lecturer approval 
@login_required
@_require_coordinator
def coordinator_pending_lecturers(request):
    cp = request.user.coordinator_profile
    pending = CustomUser.objects.filter(
        role=UserRole.LECTURER, lecturer_approved=False, is_active=True,
        lecturer_profile__university=cp.university,
    ).select_related('lecturer_profile__university', 'lecturer_profile__faculty', 'lecturer_profile__department')
    return render(request, 'accounts/coordinator_pending_lecturers.html', {'pending': pending})


@login_required
@_require_coordinator
def coordinator_approve_lecturer(request, user_id):
    cp = request.user.coordinator_profile
    user = get_object_or_404(
        CustomUser, pk=user_id, role=UserRole.LECTURER,
        lecturer_profile__university=cp.university,
    )
    user.lecturer_approved = True
    user.save(update_fields=['lecturer_approved'])
    _log_audit(request.user, 'coordinator_approve_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_approved(user)
    messages.success(request, f'Lecturer {user.username} approved.')
    return redirect('accounts:coordinator_pending_lecturers')


@login_required
@_require_coordinator
def coordinator_reject_lecturer(request, user_id):
    cp = request.user.coordinator_profile
    user = get_object_or_404(
        CustomUser, pk=user_id, role=UserRole.LECTURER,
        lecturer_profile__university=cp.university,
    )
    user.is_active = False
    user.save(update_fields=['is_active'])
    _log_audit(request.user, 'coordinator_reject_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_rejected(user)
    messages.warning(request, f'Lecturer {user.username} rejected.')
    return redirect('accounts:coordinator_pending_lecturers')


# Lecturer: Student suspension 
def _lecturer_can_manage_student(lecturer_user, student_user):
    try:
        lp = lecturer_user.lecturer_profile
        sp = student_user.student_profile
        return (lp.university_id == sp.university_id and
                lp.faculty_id == sp.faculty_id and
                lp.department_id == sp.department_id)
    except Exception:
        return False


@login_required
def suspend_student(request, user_id):
    if not request.user.is_lecturer or not request.user.lecturer_approved:
        return HttpResponseForbidden('Access denied.')
    student = get_object_or_404(CustomUser, pk=user_id, role=UserRole.STUDENT)
    if not _lecturer_can_manage_student(request.user, student):
        _log_audit(request.user, 'idor_attempt_suspend_student', 'CustomUser', user_id, request=request)
        return HttpResponseForbidden('This student is outside your scope.')
    student.is_active = False
    student.save(update_fields=['is_active'])
    _log_audit(request.user, 'suspend_student', 'CustomUser', user_id, request=request)
    notify_student_suspended(student)
    messages.warning(request, f'Student {student.username} suspended.')
    return redirect(request.META.get('HTTP_REFERER', '/grading/students/'))


@login_required
def reactivate_student(request, user_id):
    if not request.user.is_lecturer or not request.user.lecturer_approved:
        return HttpResponseForbidden('Access denied.')
    student = get_object_or_404(CustomUser, pk=user_id, role=UserRole.STUDENT)
    if not _lecturer_can_manage_student(request.user, student):
        _log_audit(request.user, 'idor_attempt_reactivate_student', 'CustomUser', user_id, request=request)
        return HttpResponseForbidden('This student is outside your scope.')
    student.is_active = True
    student.failed_login_count = 0
    student.locked_until = None
    student.save(update_fields=['is_active', 'failed_login_count', 'locked_until'])
    _log_audit(request.user, 'reactivate_student', 'CustomUser', user_id, request=request)
    notify_student_reactivated(student)
    messages.success(request, f'Student {student.username} reinstated.')
    return redirect(request.META.get('HTTP_REFERER', '/grading/students/'))
