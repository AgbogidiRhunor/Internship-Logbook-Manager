import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .forms import StudentRegistrationForm, LecturerRegistrationForm, SIWESLoginForm
from .models import CustomUser, UserRole, AuditLog
from .emails import (
    notify_admins_new_lecturer,
    notify_lecturer_approved,
    notify_lecturer_rejected,
    notify_user_suspended,
)

logger = logging.getLogger(__name__)

_LOCKOUT_THRESHOLD = 10
_LOCKOUT_MINUTES = 30


def _get_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _log_audit(actor, action, target_model='', target_id='', details='', request=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_model=target_model,
        target_id=str(target_id),
        details=details,
        ip_address=_get_ip(request) if request else None,
    )


def _require_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            return HttpResponseForbidden('Access denied.')
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

        # Check account lockout before validating credentials
        try:
            candidate = CustomUser.objects.get(username=username_raw)
            if candidate.is_locked:
                remaining = int((candidate.locked_until - timezone.now()).total_seconds() // 60)
                messages.error(
                    request,
                    f'Account temporarily locked due to too many failed attempts. '
                    f'Try again in {remaining} minute(s).'
                )
                _log_audit(None, 'login_blocked_locked', details=f'username={username_raw[:3]}*** ip={_get_ip(request)}', request=request)
                return render(request, 'accounts/login.html', {'form': form})
        except CustomUser.DoesNotExist:
            candidate = None

        if form.is_valid():
            user = form.get_user()

            if user.is_lecturer and not user.lecturer_approved:
                _log_audit(user, 'login_blocked_unapproved', request=request)
                return render(request, 'accounts/awaiting_approval.html', {'user': user})

            if not user.is_active:
                _log_audit(user, 'login_blocked_suspended', request=request)
                messages.error(request, 'Your account has been suspended. Contact your SIWES coordinator.')
                return redirect('accounts:login')

            # Successful login — clear lockout counter
            user.reset_failed_login()

            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)

            login(request, user)
            _log_audit(user, 'login_success', request=request)
            return redirect('dashboard:home')
        else:
            # Failed login — increment counter on the account if it exists
            ip = _get_ip(request)
            logger.warning(
                'Failed login | ip=%s | hint=%s',
                ip,
                username_raw[:3] + '***' if username_raw else '',
            )
            if candidate:
                candidate.record_failed_login()
                if candidate.is_locked:
                    _log_audit(None, 'account_locked', 'CustomUser', candidate.pk,
                               details=f'ip={ip}', request=request)
                    logger.warning('Account locked: %s*** after repeated failures from %s',
                                   username_raw[:3], ip)
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
        messages.success(request, 'Account created successfully. Welcome to SIWES Logbook!')
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
        notify_admins_new_lecturer(lecturer_user)
        messages.info(
            request,
            'Registration submitted. Your account is pending admin approval. '
            'You will be notified by email once a decision is made.',
        )
        return redirect('accounts:awaiting_approval')
    return render(request, 'accounts/lecturer_register.html', {'form': form})


def awaiting_approval_view(request):
    return render(request, 'accounts/awaiting_approval.html')


@login_required
@_require_admin
def pending_lecturers(request):
    pending = CustomUser.objects.filter(
        role=UserRole.LECTURER, lecturer_approved=False, is_active=True,
    ).select_related(
        'lecturer_profile__university',
        'lecturer_profile__faculty',
        'lecturer_profile__department',
    )
    return render(request, 'accounts/pending_lecturers.html', {'pending': pending})


@login_required
@_require_admin
def approve_lecturer(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.LECTURER)
    user.lecturer_approved = True
    user.save(update_fields=['lecturer_approved'])
    _log_audit(request.user, 'approve_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_approved(user)
    messages.success(request, f'Lecturer {user.username} approved and notified by email.')
    return redirect('accounts:pending_lecturers')


@login_required
@_require_admin
def reject_lecturer(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id, role=UserRole.LECTURER)
    user.is_active = False
    user.save(update_fields=['is_active'])
    _log_audit(request.user, 'reject_lecturer', 'CustomUser', user_id, request=request)
    notify_lecturer_rejected(user)
    messages.warning(request, f'Lecturer {user.username} rejected and notified by email.')
    return redirect('accounts:pending_lecturers')


@login_required
@_require_admin
def suspend_user(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    user.is_active = False
    user.save(update_fields=['is_active'])
    _log_audit(request.user, 'suspend_user', 'CustomUser', user_id, request=request)
    notify_user_suspended(user)
    messages.warning(request, f'User {user.username} suspended.')
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))


@login_required
@_require_admin
def reactivate_user(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    user.is_active = True
    user.failed_login_count = 0
    user.locked_until = None
    user.save(update_fields=['is_active', 'failed_login_count', 'locked_until'])
    _log_audit(request.user, 'reactivate_user', 'CustomUser', user_id, request=request)
    messages.success(request, f'User {user.username} reactivated.')
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))
