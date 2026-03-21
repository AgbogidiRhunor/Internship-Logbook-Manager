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
            subject=subject,
            body=strip_tags(html_body),
            from_email=from_email,
            to=recipient_list,
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
        f'<tr>'
        f'<td style="padding:9px 14px;font-size:13px;font-weight:600;color:#6b7280;'
        f'width:160px;border-bottom:1px solid #f3f4f6;">{label}</td>'
        f'<td style="padding:9px 14px;font-size:13px;color:#111827;'
        f'border-bottom:1px solid #f3f4f6;">{value}</td>'
        f'</tr>'
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


# 1. Lecturer registers → email to LECTURER only  

def notify_lecturer_registration_pending(lecturer_user):
    """Sent only to the lecturer who just registered."""
    email = getattr(lecturer_user, 'email', '')
    if not email:
        logger.warning('notify_lecturer_registration_pending: no email for %s', lecturer_user.username)
        return

    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username

    body = (
        _h1('Registration Received')
        + _badge('PENDING REVIEW', '#92400e', '#fef3c7')
        + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Thank you for registering on the SIWES Logbook Manager. Your lecturer account has been submitted and is currently <strong>awaiting admin approval</strong>.')
        + _table([
            ('Username',    lecturer_user.username),
            ('University',  str(lp.university) if lp else '-'),
            ('Faculty',     lp.faculty.name if lp else '-'),
            ('Department',  lp.department.name if lp else '-'),
            ('Status',      'Pending Review'),
        ])
        + _p('You will receive another email once an administrator reviews your registration. This usually takes up to 48 hours.')
    )

    _send(
        subject='[SIWES] Your registration has been received — pending review',
        html_body=_wrap('Registration Pending', body),
        recipient_list=[email],
    )


#  2. Lecturer registers → email to ADMIN only  

def notify_admins_new_lecturer(lecturer_user):
    """Sent only to admin users when a new lecturer registers."""
    from accounts.models import CustomUser, UserRole

    admin_emails = list(
        CustomUser.objects.filter(role=UserRole.ADMIN, is_active=True)
        .exclude(email='').values_list('email', flat=True)
    )
    host_user = getattr(settings, 'EMAIL_HOST_USER', '')
    if host_user and host_user not in admin_emails:
        admin_emails.append(host_user)

    if not admin_emails:
        logger.warning('notify_admins_new_lecturer: no admin email addresses found.')
        return

    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username

    body = (
        _h1('New Lecturer Registration — Action Required')
        + _badge('PENDING APPROVAL', '#92400e', '#fef3c7')
        + '<br><br>'
        + _p('A new lecturer has registered and is awaiting your approval:')
        + _table([
            ('Full Name',   full_name),
            ('Username',    lecturer_user.username),
            ('Email',       getattr(lecturer_user, 'email', '-')),
            ('University',  str(lp.university) if lp else '-'),
            ('Faculty',     lp.faculty.name if lp else '-'),
            ('Department',  lp.department.name if lp else '-'),
            ('Registered',  lecturer_user.created_at.strftime('%d %b %Y %H:%M')),
        ])
        + _btn('Review Pending Approvals', f'{_site()}/accounts/admin/pending-lecturers/', '#1a1a2e')
    )

    _send(
        subject=f'[SIWES] New Lecturer Registration — {full_name}',
        html_body=_wrap('New Lecturer Registration', body),
        recipient_list=admin_emails,
    )


# 3. Admin approves → email to LECTURER only 

def notify_lecturer_approved(lecturer_user):
    """Sent only to the lecturer whose account was approved."""
    email = getattr(lecturer_user, 'email', '')
    if not email:
        logger.warning('notify_lecturer_approved: no email for %s', lecturer_user.username)
        return

    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username

    body = (
        _h1('Your Account Has Been Approved')
        + _badge('APPROVED', '#065f46', '#d1fae5')
        + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Your SIWES Logbook Manager lecturer account has been <strong>approved</strong> by an administrator. You can now log in and begin supervising your students.')
        + _table([
            ('Username',    lecturer_user.username),
            ('University',  str(lp.university) if lp else '-'),
            ('Faculty',     lp.faculty.name if lp else '-'),
            ('Department',  lp.department.name if lp else '-'),
        ])
        + _btn('Log In Now', f'{_site()}/accounts/login/')
    )

    _send(
        subject='[SIWES] Your lecturer account has been approved',
        html_body=_wrap('Account Approved', body),
        recipient_list=[email],
    )


# 4. Admin rejects → email to LECTURER only 

def notify_lecturer_rejected(lecturer_user):
    """Sent only to the lecturer whose account was rejected."""
    email = getattr(lecturer_user, 'email', '')
    if not email:
        logger.warning('notify_lecturer_rejected: no email for %s', lecturer_user.username)
        return

    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username

    body = (
        _h1('Account Registration Unsuccessful')
        + _badge('NOT APPROVED', '#991b1b', '#fee2e2')
        + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p('Unfortunately your SIWES Logbook Manager lecturer registration could not be approved at this time.')
        + _p("If you believe this is an error, please contact your institution's SIWES office.")
    )

    _send(
        subject='[SIWES] Update on your lecturer registration',
        html_body=_wrap('Registration Unsuccessful', body),
        recipient_list=[email],
    )


# 5. Student graded → email to STUDENT only 

def notify_student_graded(student_profile):
    """Sent only to the student when their logbook is graded."""
    email = getattr(student_profile.user, 'email', '')
    if not email:
        logger.warning('notify_student_graded: no email for student %s', student_profile.matric_number)
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
        + _p('Your SIWES internship logbook has been reviewed and graded by your supervising lecturer.')
        + _table([
            ('Score',       f'{grade.overall_score} / 100'),
            ('Grade',       _badge(grade.letter_grade, fg, bg)),
            ('Graded By',   grade.graded_by.get_full_name()),
            ('Graded On',   grade.graded_at.strftime('%d %b %Y')),
            ('Company',     student_profile.company_name),
            ('Duration',    student_profile.get_internship_duration_display()),
        ])
        + f'<div style="background:#f8fafc;border-left:4px solid #e94560;padding:14px 18px;'
          f'margin:18px 0;border-radius:0 8px 8px 0;">'
          f'<p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#6b7280;'
          f'text-transform:uppercase;letter-spacing:.5px;">Lecturer Comment</p>'
          f'<p style="margin:0;font-size:14px;color:#111827;line-height:1.65;">'
          f'{grade.lecturer_comment}</p></div>'
        + _btn('View Your Dashboard', f'{_site()}/dashboard/')
    )

    _send(
        subject=f'[SIWES] Your internship grade: {grade.letter_grade} ({grade.overall_score}/100)',
        html_body=_wrap('Internship Graded', body),
        recipient_list=[email],
    )


# 6. Student suspended by lecturer → email to STUDENT only 

def notify_student_suspended(student_user):
    """Sent only to a student whose account was suspended by their lecturer."""
    email = getattr(student_user, 'email', '')
    if not email:
        return

    body = (
        _h1('Your Account Has Been Suspended')
        + _badge('SUSPENDED', '#991b1b', '#fee2e2')
        + '<br><br>'
        + _p(f'Dear {student_user.get_full_name()},')
        + _p('Your SIWES Logbook Manager student account has been <strong>suspended</strong> by your supervising lecturer. You will not be able to log in or create new log entries until your account is reinstated.')
        + _p("If you believe this is a mistake, please contact your lecturer or your institution's SIWES coordinator.")
    )

    _send(
        subject='[SIWES] Your student account has been suspended',
        html_body=_wrap('Account Suspended', body),
        recipient_list=[email],
    )


# 7. Student unsuspended by lecturer → email to STUDENT only

def notify_student_reactivated(student_user):
    """Sent only to a student whose suspension was lifted."""
    email = getattr(student_user, 'email', '')
    if not email:
        return

    body = (
        _h1('Your Account Has Been Reinstated')
        + _badge('ACTIVE', '#065f46', '#d1fae5')
        + '<br><br>'
        + _p(f'Dear {student_user.get_full_name()},')
        + _p('Your SIWES Logbook Manager student account has been <strong>reinstated</strong>. You can now log in and continue logging your internship activities.')
        + _btn('Log In Now', f'{_site()}/accounts/login/')
    )

    _send(
        subject='[SIWES] Your student account has been reinstated',
        html_body=_wrap('Account Reinstated', body),
        recipient_list=[email],
    )


# 8. Lecturer suspended by admin → email to LECTURER only

def notify_lecturer_suspended(lecturer_user):
    """Sent only to a lecturer whose account was suspended by an admin."""
    email = getattr(lecturer_user, 'email', '')
    if not email:
        return

    body = (
        _h1('Your Account Has Been Suspended')
        + _badge('SUSPENDED', '#991b1b', '#fee2e2')
        + '<br><br>'
        + _p(f'Dear {lecturer_user.get_full_name()},')
        + _p('Your SIWES Logbook Manager lecturer account has been <strong>suspended</strong> by an administrator. You will not be able to log in until your account is reinstated.')
        + _p("If you believe this is a mistake, please contact your institution's SIWES coordinator.")
    )

    _send(
        subject='[SIWES] Your lecturer account has been suspended',
        html_body=_wrap('Account Suspended', body),
        recipient_list=[email],
    )


# 9. Lecturer unsuspended by admin → email to LECTURER only 

def notify_lecturer_reactivated(lecturer_user):
    """Sent only to a lecturer whose suspension was lifted."""
    email = getattr(lecturer_user, 'email', '')
    if not email:
        return

    body = (
        _h1('Your Account Has Been Reinstated')
        + _badge('ACTIVE', '#065f46', '#d1fae5')
        + '<br><br>'
        + _p(f'Dear {lecturer_user.get_full_name()},')
        + _p('Your SIWES Logbook Manager lecturer account has been <strong>reinstated</strong>. You can now log in and resume supervising your students.')
        + _btn('Log In Now', f'{_site()}/accounts/login/')
    )

    _send(
        subject='[SIWES] Your lecturer account has been reinstated',
        html_body=_wrap('Account Reinstated', body),
        recipient_list=[email],
    )
