from django.utils import timezone
from .models import CustomUser, UserRole, AuditLog


def get_client_ip(request) -> str:
    """Extract real client IP, handling proxies."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def log_admin_action(actor: CustomUser, action: str, target_model: str = '',
                     target_id=None, details: str = '', request=None):
    """Create an AuditLog entry for any significant admin action."""
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_model=target_model,
        target_id=str(target_id) if target_id else '',
        details=details,
        ip_address=get_client_ip(request) if request else None,
    )


def approve_lecturer(lecturer_user: CustomUser, admin_user: CustomUser, request=None):
    """
    Approve a lecturer account.
    Returns True on success, False if user is not a pending lecturer.
    """
    if lecturer_user.role != UserRole.LECTURER:
        return False
    lecturer_user.lecturer_approved = True
    lecturer_user.save(update_fields=['lecturer_approved'])
    log_admin_action(
        actor=admin_user,
        action='approve_lecturer',
        target_model='CustomUser',
        target_id=lecturer_user.pk,
        details=f'Approved lecturer: {lecturer_user.username}',
        request=request,
    )
    return True


def reject_lecturer(lecturer_user: CustomUser, admin_user: CustomUser, request=None):
    """
    Reject a lecturer account by deactivating it.
    Returns True on success.
    """
    if lecturer_user.role != UserRole.LECTURER:
        return False
    lecturer_user.is_active = False
    lecturer_user.save(update_fields=['is_active'])
    log_admin_action(
        actor=admin_user,
        action='reject_lecturer',
        target_model='CustomUser',
        target_id=lecturer_user.pk,
        details=f'Rejected lecturer: {lecturer_user.username}',
        request=request,
    )
    return True


def suspend_user_account(target_user: CustomUser, admin_user: CustomUser, request=None):
    """Suspend any user account."""
    target_user.is_active = False
    target_user.save(update_fields=['is_active'])
    log_admin_action(
        actor=admin_user,
        action='suspend_user',
        target_model='CustomUser',
        target_id=target_user.pk,
        details=f'Suspended user: {target_user.username} (role={target_user.role})',
        request=request,
    )


def reactivate_user_account(target_user: CustomUser, admin_user: CustomUser, request=None):
    """Reactivate a suspended user."""
    target_user.is_active = True
    target_user.save(update_fields=['is_active'])
    log_admin_action(
        actor=admin_user,
        action='reactivate_user',
        target_model='CustomUser',
        target_id=target_user.pk,
        details=f'Reactivated user: {target_user.username}',
        request=request,
    )


def get_system_stats() -> dict:
    """Aggregate platform-wide statistics for the admin dashboard."""
    from logbook.models import DailyLogEntry
    from grading.models import GradeRecord
    from institutions.models import University

    return {
        'total_students': CustomUser.objects.filter(role=UserRole.STUDENT, is_active=True).count(),
        'total_lecturers': CustomUser.objects.filter(role=UserRole.LECTURER, is_active=True).count(),
        'pending_approvals': CustomUser.objects.filter(
            role=UserRole.LECTURER, lecturer_approved=False, is_active=True
        ).count(),
        'total_logs': DailyLogEntry.objects.count(),
        'total_grades': GradeRecord.objects.count(),
        'total_universities': University.objects.filter(is_active=True).count(),
    }
