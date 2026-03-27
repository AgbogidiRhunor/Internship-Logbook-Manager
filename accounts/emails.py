import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send(subject, html_body, recipient_list):
    if not recipient_list:
        return
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'SIWES Logbook <noreply@siwes.edu.ng>')
    try:
        msg = EmailMultiAlternatives(
            subject=subject, body=strip_tags(html_body),
            from_email=from_email, to=recipient_list,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info('Email sent: "%s" -> %s', subject, recipient_list)
    except Exception as exc:
        logger.error('Email failed: "%s" -> %s | %s', subject, recipient_list, exc)


def _site():
    return getattr(settings, 'SITE_URL', '').rstrip('/')


def _wrap(title, body_html):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{title}</title></head>
<body style="margin:0;padding:0;background:#f0f2f8;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f2f8;padding:40px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0"
  style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.09);">
<tr><td style="background:#1a1a2e;padding:28px 36px;">
  <table width="100%" cellpadding="0" cellspacing="0"><tr>
    <td><div style="display:inline-block;background:#e94560;border-radius:8px;padding:6px 14px;
      font-size:18px;font-weight:800;color:#fff;">SL</div></td>
    <td style="text-align:right;color:rgba(255,255,255,.5);font-size:13px;vertical-align:middle;">
      SIWES Logbook Manager</td>
  </tr></table>
</td></tr>
<tr><td style="padding:36px 36px 28px;">{body_html}</td></tr>
<tr><td style="background:#f8fafc;padding:18px 36px;border-top:1px solid #e5e7eb;
  font-size:12px;color:#9ca3af;text-align:center;">
  This is an automated message from SIWES Logbook Manager. Please do not reply.
</td></tr>
</table></td></tr></table></body></html>"""


def _h1(t):
    return f'<h1 style="margin:0 0 8px;font-size:22px;font-weight:800;color:#1a1a2e;letter-spacing:-0.5px;">{t}</h1>'

def _p(t):
    return f'<p style="margin:0 0 14px;font-size:15px;color:#374151;line-height:1.65;">{t}</p>'

def _badge(text, color, bg):
    return (f'<span style="display:inline-block;background:{bg};color:{color};'
            f'padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;">{text}</span>')

def _table(rows):
    cells = ''.join(
        f'<tr><td style="padding:9px 14px;font-size:13px;font-weight:600;color:#6b7280;'
        f'width:160px;border-bottom:1px solid #f3f4f6;">{label}</td>'
        f'<td style="padding:9px 14px;font-size:13px;color:#111827;'
        f'border-bottom:1px solid #f3f4f6;">{value}</td></tr>'
        for label, value in rows
    )
    return (f'<table width="100%" cellpadding="0" cellspacing="0" '
            f'style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:18px 0;">'
            f'{cells}</table>')

def _btn(label, url, color='#e94560'):
    return (f'<p style="margin:24px 0 0;">'
            f'<a href="{url}" style="display:inline-block;background:{color};color:#fff;'
            f'padding:12px 28px;border-radius:8px;font-size:14px;font-weight:600;'
            f'text-decoration:none;">{label}</a></p>')


# Coordinator registration to coordinator only 

def notify_coordinator_registration_pending(coordinator_user):
    email = getattr(coordinator_user, 'email', '')
    if not email:
        return
    cp = getattr(coordinator_user, 'coordinator_profile', None)
    full_name = cp.full_name if cp else coordinator_user.username
    body = (
        _h1('Registration Received')
        + _badge('PENDING REVIEW', '#92400e', '#fef3c7') + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Your School Coordinator account has been submitted and is awaiting admin approval.')
        + _table([
            ('Username', coordinator_user.username),
            ('University', str(cp.university) if cp else '-'),
            ('Status', 'Pending Review'),
        ])
        + _p('You will be notified by email once an administrator reviews your registration.')
    )
    _send(
        subject='[SIWES] Your coordinator registration is pending review',
        html_body=_wrap('Registration Pending', body),
        recipient_list=[email],
    )


# Coordinator registration to admin only 

def notify_admins_new_coordinator(coordinator_user):
    from accounts.models import CustomUser, UserRole
    admin_emails = list(
        CustomUser.objects.filter(role=UserRole.ADMIN, is_active=True)
        .exclude(email='').values_list('email', flat=True)
    )
    host_user = getattr(settings, 'EMAIL_HOST_USER', '')
    if host_user and host_user not in admin_emails:
        admin_emails.append(host_user)
    if not admin_emails:
        logger.warning('notify_admins_new_coordinator: no admin emails found.')
        return
    cp = getattr(coordinator_user, 'coordinator_profile', None)
    full_name = cp.full_name if cp else coordinator_user.username
    body = (
        _h1('New School Coordinator Registration')
        + _badge('PENDING APPROVAL', '#92400e', '#fef3c7') + '<br><br>'
        + _p('A new School Coordinator has registered and requires your approval:')
        + _table([
            ('Full Name', full_name),
            ('Username', coordinator_user.username),
            ('Email', getattr(coordinator_user, 'email', '-')),
            ('University', str(cp.university) if cp else '-'),
            ('Registered', coordinator_user.created_at.strftime('%d %b %Y %H:%M')),
        ])
        + _btn('Review in Admin Panel', f'{_site()}/admin/', '#1a1a2e')
    )
    _send(
        subject=f'[SIWES] New Coordinator Registration — {full_name}',
        html_body=_wrap('New Coordinator Registration', body),
        recipient_list=admin_emails,
    )


# Coordinator approved to coordinator only 

def notify_coordinator_approved(coordinator_user):
    email = getattr(coordinator_user, 'email', '')
    if not email:
        return
    cp = getattr(coordinator_user, 'coordinator_profile', None)
    full_name = cp.full_name if cp else coordinator_user.username
    body = (
        _h1('Your Account Has Been Approved')
        + _badge('APPROVED', '#065f46', '#d1fae5') + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Your SIWES Logbook School Coordinator account has been approved. You can now log in and manage your university.')
        + _table([
            ('Username', coordinator_user.username),
            ('University', str(cp.university) if cp else '-'),
        ])
        + _btn('Log In Now', f'{_site()}/accounts/login/')
    )
    _send(
        subject='[SIWES] Your coordinator account has been approved',
        html_body=_wrap('Account Approved', body),
        recipient_list=[email],
    )


# Coordinator rejected to coordinator only 

def notify_coordinator_rejected(coordinator_user):
    email = getattr(coordinator_user, 'email', '')
    if not email:
        return
    cp = getattr(coordinator_user, 'coordinator_profile', None)
    full_name = cp.full_name if cp else coordinator_user.username
    body = (
        _h1('Account Registration Unsuccessful')
        + _badge('NOT APPROVED', '#991b1b', '#fee2e2') + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Unfortunately your School Coordinator registration could not be approved.')
        + _p("Please contact your institution's SIWES office if you believe this is an error.")
    )
    _send(
        subject='[SIWES] Update on your coordinator registration',
        html_body=_wrap('Registration Unsuccessful', body),
        recipient_list=[email],
    )


# Lecturer registration to lecturer only

def notify_lecturer_registration_pending(lecturer_user):
    email = getattr(lecturer_user, 'email', '')
    if not email:
        return
    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username
    body = (
        _h1('Registration Received')
        + _badge('PENDING REVIEW', '#92400e', '#fef3c7') + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Your lecturer account has been submitted and is awaiting approval from your university\'s School Coordinator.')
        + _table([
            ('Username', lecturer_user.username),
            ('University', str(lp.university) if lp else '-'),
            ('Faculty', lp.faculty.name if lp else '-'),
            ('Department', lp.department.name if lp else '-'),
            ('Status', 'Pending Coordinator Review'),
        ])
        + _p('You will be notified by email once a decision is made.')
    )
    _send(
        subject='[SIWES] Your lecturer registration is pending review',
        html_body=_wrap('Registration Pending', body),
        recipient_list=[email],
    )


# Lecturer registration to school coordinator only

def notify_coordinator_new_lecturer(lecturer_user):
    """Find the coordinator for the lecturer's university and notify them."""
    from accounts.models import CustomUser, UserRole, CoordinatorProfile
    lp = getattr(lecturer_user, 'lecturer_profile', None)
    if not lp:
        return
    coordinator_emails = list(
        CoordinatorProfile.objects.filter(
            university=lp.university
        ).select_related('user').filter(
            user__is_active=True,
            user__coordinator_approved=True,
        ).exclude(user__email='').values_list('user__email', flat=True)
    )
    if not coordinator_emails:
        # fallback to admin if no coordinator exists for this university
        admin_emails = list(
            CustomUser.objects.filter(role=UserRole.ADMIN, is_active=True)
            .exclude(email='').values_list('email', flat=True)
        )
        coordinator_emails = admin_emails
    if not coordinator_emails:
        logger.warning('notify_coordinator_new_lecturer: no coordinator/admin emails for university %s', lp.university)
        return
    full_name = lp.full_name
    body = (
        _h1('New Lecturer Registration — Action Required')
        + _badge('PENDING APPROVAL', '#92400e', '#fef3c7') + '<br><br>'
        + _p(f'A new lecturer from your university has registered and is awaiting your approval:')
        + _table([
            ('Full Name', full_name),
            ('Username', lecturer_user.username),
            ('Email', getattr(lecturer_user, 'email', '-')),
            ('University', str(lp.university)),
            ('Faculty', lp.faculty.name),
            ('Department', lp.department.name),
            ('Registered', lecturer_user.created_at.strftime('%d %b %Y %H:%M')),
        ])
        + _btn('Review Pending Lecturers', f'{_site()}/coordinator/pending-lecturers/', '#1a1a2e')
    )
    _send(
        subject=f'[SIWES] New Lecturer Registration — {full_name}',
        html_body=_wrap('New Lecturer Registration', body),
        recipient_list=coordinator_emails,
    )


# Lecturer approved to lecturer only 

def notify_lecturer_approved(lecturer_user):
    email = getattr(lecturer_user, 'email', '')
    if not email:
        return
    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username
    body = (
        _h1('Your Account Has Been Approved')
        + _badge('APPROVED', '#065f46', '#d1fae5') + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Your SIWES Logbook lecturer account has been approved. You can now log in and begin supervising your students.')
        + _table([
            ('Username', lecturer_user.username),
            ('University', str(lp.university) if lp else '-'),
            ('Faculty', lp.faculty.name if lp else '-'),
            ('Department', lp.department.name if lp else '-'),
        ])
        + _btn('Log In Now', f'{_site()}/accounts/login/')
    )
    _send(
        subject='[SIWES] Your lecturer account has been approved',
        html_body=_wrap('Account Approved', body),
        recipient_list=[email],
    )


# Lecturer rejected to lecturer only 

def notify_lecturer_rejected(lecturer_user):
    email = getattr(lecturer_user, 'email', '')
    if not email:
        return
    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username
    body = (
        _h1('Account Registration Unsuccessful')
        + _badge('NOT APPROVED', '#991b1b', '#fee2e2') + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Unfortunately your SIWES Logbook lecturer registration could not be approved.')
        + _p("Please contact your institution's SIWES coordinator if you believe this is an error.")
    )
    _send(
        subject='[SIWES] Update on your lecturer registration',
        html_body=_wrap('Registration Unsuccessful', body),
        recipient_list=[email],
    )


# Student graded to student only 

def notify_student_graded(student_profile):
    email = getattr(student_profile.user, 'email', '')
    if not email:
        return
    grade = getattr(student_profile, 'grade_record', None)
    if not grade:
        return
    grade_colors = {
        'A': ('#065f46', '#d1fae5'), 'B': ('#0c4a6e', '#e0f2fe'),
        'C': ('#78350f', '#fef3c7'), 'D': ('#7c2d12', '#ffedd5'),
        'E': ('#581c87', '#f3e8ff'), 'F': ('#991b1b', '#fee2e2'),
    }
    fg, bg = grade_colors.get(grade.letter_grade, ('#111827', '#f9fafb'))
    body = (
        _h1('Your Internship Has Been Graded')
        + _p(f'Dear {student_profile.full_name},')
        + _p('Your SIWES internship logbook has been reviewed and graded.')
        + _table([
            ('Score', f'{grade.overall_score} / 100'),
            ('Grade', _badge(grade.letter_grade, fg, bg)),
            ('Graded By', grade.graded_by.get_full_name()),
            ('Graded On', grade.graded_at.strftime('%d %b %Y')),
        ])
        + f'<div style="background:#f8fafc;border-left:4px solid #e94560;padding:14px 18px;margin:18px 0;border-radius:0 8px 8px 0;">'
          f'<p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;">Lecturer Comment</p>'
          f'<p style="margin:0;font-size:14px;color:#111827;line-height:1.65;">{grade.lecturer_comment}</p></div>'
        + _btn('View Dashboard', f'{_site()}/dashboard/')
    )
    _send(
        subject=f'[SIWES] Your grade: {grade.letter_grade} ({grade.overall_score}/100)',
        html_body=_wrap('Internship Graded', body),
        recipient_list=[email],
    )


# Student suspended/reinstated to student only 

def notify_student_suspended(student_user):
    email = getattr(student_user, 'email', '')
    if not email:
        return
    body = (
        _h1('Your Account Has Been Suspended')
        + _badge('SUSPENDED', '#991b1b', '#fee2e2') + '<br><br>'
        + _p(f'Dear {student_user.get_full_name()},')
        + _p('Your SIWES Logbook student account has been suspended by your supervising lecturer.')
        + _p("Contact your lecturer or SIWES coordinator if you believe this is a mistake.")
    )
    _send(subject='[SIWES] Your student account has been suspended',
          html_body=_wrap('Account Suspended', body), recipient_list=[email])


def notify_student_reactivated(student_user):
    email = getattr(student_user, 'email', '')
    if not email:
        return
    body = (
        _h1('Your Account Has Been Reinstated')
        + _badge('ACTIVE', '#065f46', '#d1fae5') + '<br><br>'
        + _p(f'Dear {student_user.get_full_name()},')
        + _p('Your SIWES Logbook student account has been reinstated. You can now log in.')
        + _btn('Log In Now', f'{_site()}/accounts/login/')
    )
    _send(subject='[SIWES] Your student account has been reinstated',
          html_body=_wrap('Account Reinstated', body), recipient_list=[email])


# Lecturer suspended/reinstated → to lecturer only

def notify_lecturer_suspended(lecturer_user):
    email = getattr(lecturer_user, 'email', '')
    if not email:
        return
    body = (
        _h1('Your Account Has Been Suspended')
        + _badge('SUSPENDED', '#991b1b', '#fee2e2') + '<br><br>'
        + _p(f'Dear {lecturer_user.get_full_name()},')
        + _p('Your SIWES Logbook lecturer account has been suspended by an administrator.')
        + _p("Contact your institution's SIWES coordinator if you believe this is a mistake.")
    )
    _send(subject='[SIWES] Your lecturer account has been suspended',
          html_body=_wrap('Account Suspended', body), recipient_list=[email])


def notify_lecturer_reactivated(lecturer_user):
    email = getattr(lecturer_user, 'email', '')
    if not email:
        return
    body = (
        _h1('Your Account Has Been Reinstated')
        + _badge('ACTIVE', '#065f46', '#d1fae5') + '<br><br>'
        + _p(f'Dear {lecturer_user.get_full_name()},')
        + _p('Your SIWES Logbook lecturer account has been reinstated. You can now log in.')
        + _btn('Log In Now', f'{_site()}/accounts/login/')
    )
    _send(subject='[SIWES] Your lecturer account has been reinstated',
          html_body=_wrap('Account Reinstated', body), recipient_list=[email])
