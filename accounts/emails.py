import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _get_admin_notification_emails() -> list:
    configured = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [])

    if isinstance(configured, str):
        emails = [email.strip() for email in configured.split(',') if email.strip()]
    elif isinstance(configured, (list, tuple, set)):
        emails = [str(email).strip() for email in configured if str(email).strip()]
    else:
        emails = []

    return list(dict.fromkeys(emails))


def _send_via_smtp(subject: str, html_body: str, recipient_list: list):
    from_email = getattr(
        settings,
        'DEFAULT_FROM_EMAIL',
        f'SIWES Logbook <{getattr(settings, "EMAIL_HOST_USER", "")}>',
    )
    plain_body = strip_tags(html_body)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=from_email,
        to=recipient_list,
    )
    msg.attach_alternative(html_body, 'text/html')

    sent_count = msg.send(fail_silently=True)

    if sent_count:
        logger.info('Email sent via SMTP: "%s" -> %s', subject, recipient_list)
    else:
        logger.error('Email not sent via SMTP: "%s" -> %s', subject, recipient_list)


def _send_via_resend_api(subject: str, html_body: str, recipient_list: list):
    import resend

    resend.api_key = settings.RESEND_API_KEY

    payload = {
        'from': settings.DEFAULT_FROM_EMAIL,
        'to': recipient_list,
        'subject': subject,
        'html': html_body,
        'text': strip_tags(html_body),
    }

    response = resend.Emails.send(payload)
    logger.info('Email sent via Resend API: "%s" -> %s | %s', subject, recipient_list, response)


def _send(subject: str, html_body: str, recipient_list: list):
    if not recipient_list:
        return

    cleaned_recipients = [
        email.strip()
        for email in recipient_list
        if isinstance(email, str) and email.strip() and '@' in email
    ]

    if not cleaned_recipients:
        logger.warning('No valid email recipients found for subject "%s".', subject)
        return

    try:
        email_provider = getattr(settings, 'EMAIL_PROVIDER', 'smtp').lower()

        if email_provider == 'resend_api':
            _send_via_resend_api(subject, html_body, cleaned_recipients)
        else:
            _send_via_smtp(subject, html_body, cleaned_recipients)

    except Exception as exc:
        logger.error('Email failed: "%s" -> %s | %s', subject, cleaned_recipients, exc)


def _base_html(title: str, body_html: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:12px;overflow:hidden;
                      box-shadow:0 4px 16px rgba(0,0,0,.08);">
          <tr>
            <td style="background:#0a2240;padding:28px 36px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <div style="display:inline-block;background:#0d9488;
                                border-radius:8px;padding:6px 14px;
                                font-size:18px;font-weight:800;color:#fff;
                                letter-spacing:1px;">SL</div>
                  </td>
                  <td style="text-align:right;color:rgba(255,255,255,.6);
                             font-size:13px;vertical-align:middle;">
                    SIWES Logbook Manager
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:36px 36px 28px;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="background:#f8fafc;padding:18px 36px;
                       border-top:1px solid #e2e8f0;
                       font-size:12px;color:#94a3b8;text-align:center;">
              This is an automated message from SIWES Logbook Manager.
              Please do not reply to this email.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _h1(text: str) -> str:
    return f'<h1 style="margin:0 0 8px;font-size:22px;color:#0a2240;">{text}</h1>'


def _p(text: str) -> str:
    return f'<p style="margin:0 0 14px;font-size:15px;color:#334155;line-height:1.6;">{text}</p>'


def _info_table(rows: list) -> str:
    cells = ''.join(
        f"""<tr>
              <td style="padding:8px 12px;font-size:13px;font-weight:600;
                         color:#64748b;width:160px;border-bottom:1px solid #f1f5f9;">
                {label}
              </td>
              <td style="padding:8px 12px;font-size:13px;color:#1e293b;
                         border-bottom:1px solid #f1f5f9;">
                {value}
              </td>
            </tr>"""
        for label, value in rows
    )
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid #e2e8f0;border-radius:8px;
                  overflow:hidden;margin:18px 0;">
      {cells}
    </table>"""


def _button(label: str, url: str, color: str = '#0d9488') -> str:
    return f"""
    <p style="margin:24px 0 0;">
      <a href="{url}"
         style="display:inline-block;background:{color};color:#fff;
                padding:12px 28px;border-radius:7px;font-size:14px;
                font-weight:600;text-decoration:none;letter-spacing:.3px;">
        {label}
      </a>
    </p>"""


def _badge(text: str, color: str, bg: str) -> str:
    return (
        f'<span style="display:inline-block;background:{bg};color:{color};'
        f'padding:3px 12px;border-radius:20px;font-size:12px;'
        f'font-weight:700;">{text}</span>'
    )


def notify_admins_new_lecturer(lecturer_user):
    from accounts.models import CustomUser, UserRole

    admin_emails = list(
        CustomUser.objects.filter(
            role=UserRole.ADMIN,
            is_active=True,
        ).exclude(
            email='',
        ).values_list('email', flat=True)
    )

    configured_admin_emails = _get_admin_notification_emails()

    for email in configured_admin_emails:
        if email not in admin_emails:
            admin_emails.append(email)

    admin_emails = [email for email in admin_emails if email and '@' in email]

    if not admin_emails:
        logger.warning(
            'notify_admins_new_lecturer: no admin email addresses found. '
            'Add emails to admin accounts or set ADMIN_NOTIFICATION_EMAILS.'
        )
        return

    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username

    body = (
        _h1('New Lecturer Registration')
        + _p('A new lecturer has registered and is awaiting your approval:')
        + _info_table([
            ('Full Name', full_name),
            ('Username', lecturer_user.username),
            ('University', str(lp.university) if lp else '—'),
            ('Faculty', lp.faculty.name if lp else '—'),
            ('Department', lp.department.name if lp else '—'),
            ('Registered', lecturer_user.created_at.strftime('%d %b %Y %H:%M')),
        ])
        + _p('Log in to the admin panel to review and approve or reject this account.')
        + _button(
            'Review Pending Approvals',
            f"{getattr(settings, 'SITE_URL', '')}/accounts/admin/pending-lecturers/",
            '#0a2240',
        )
    )

    _send(
        subject=f'[SIWES] New Lecturer Registration — {full_name}',
        html_body=_base_html('New Lecturer Registration', body),
        recipient_list=admin_emails,
    )


def notify_lecturer_approved(lecturer_user):
    email = getattr(lecturer_user, 'email', '')
    if not email:
        logger.warning(
            'notify_lecturer_approved: lecturer %s has no email address.',
            lecturer_user.username,
        )
        return

    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username

    body = (
        _h1('Your Account Has Been Approved')
        + _badge('APPROVED', '#166534', '#dcfce7')
        + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p(
            'Your SIWES Logbook Manager lecturer account has been approved by an administrator. '
            'You can now log in and begin supervising your students.'
        )
        + _info_table([
            ('Username', lecturer_user.username),
            ('University', str(lp.university) if lp else '—'),
            ('Faculty', lp.faculty.name if lp else '—'),
            ('Department', lp.department.name if lp else '—'),
        ])
        + _button('Log In Now', f"{getattr(settings, 'SITE_URL', '')}/accounts/login/")
    )

    _send(
        subject='[SIWES] Your lecturer account has been approved',
        html_body=_base_html('Account Approved', body),
        recipient_list=[email],
    )


def notify_lecturer_rejected(lecturer_user):
    email = getattr(lecturer_user, 'email', '')
    if not email:
        logger.warning(
            'notify_lecturer_rejected: lecturer %s has no email address.',
            lecturer_user.username,
        )
        return

    lp = getattr(lecturer_user, 'lecturer_profile', None)
    full_name = lp.full_name if lp else lecturer_user.username

    body = (
        _h1('Account Registration Unsuccessful')
        + _badge('NOT APPROVED', '#991b1b', '#fee2e2')
        + '<br><br>'
        + _p(f'Dear {full_name},')
        + _p(
            'Unfortunately, your SIWES Logbook Manager lecturer registration could not be approved '
            'at this time. This may be because the details provided could not be verified by '
            "your institution's SIWES coordinator."
        )
        + _p(
            "If you believe this is an error, please contact your institution's SIWES office "
            'and ask them to register you directly.'
        )
    )

    _send(
        subject='[SIWES] Update on your lecturer registration',
        html_body=_base_html('Registration Unsuccessful', body),
        recipient_list=[email],
    )


def notify_student_graded(student_profile):
    email = getattr(student_profile.user, 'email', '')
    if not email:
        logger.warning(
            'notify_student_graded: student %s has no email address.',
            student_profile.matric_number,
        )
        return

    grade = getattr(student_profile, 'grade_record', None)
    if not grade:
        return

    grade_colors = {
        'A': ('#166534', '#dcfce7'),
        'B': ('#1d4ed8', '#dbeafe'),
        'C': ('#92400e', '#fef3c7'),
        'D': ('#c2410c', '#ffedd5'),
        'E': ('#be185d', '#fce7f3'),
        'F': ('#991b1b', '#fee2e2'),
    }
    fg, bg = grade_colors.get(grade.letter_grade, ('#1e293b', '#f1f5f9'))

    body = (
        _h1('Your Internship Has Been Graded')
        + _p(f'Dear {student_profile.full_name},')
        + _p('Your SIWES internship logbook has been reviewed and graded by your supervising lecturer.')
        + _info_table([
            ('Score', f'{grade.overall_score} / 100'),
            ('Grade', _badge(grade.letter_grade, fg, bg)),
            ('Graded By', grade.graded_by.get_full_name()),
            ('Graded On', grade.graded_at.strftime('%d %b %Y')),
            ('Company', student_profile.company_name),
            ('Duration', student_profile.get_internship_duration_display()),
        ])
        + f'<div style="background:#f8fafc;border-left:4px solid #0d9488;'
          f'padding:14px 18px;margin:18px 0;border-radius:0 6px 6px 0;">'
          f'<p style="margin:0 0 6px;font-size:12px;font-weight:700;'
          f'color:#64748b;text-transform:uppercase;">Lecturer Comment</p>'
          f'<p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">'
          f'{grade.lecturer_comment}</p></div>'
        + _button('View Your Dashboard', f"{getattr(settings, 'SITE_URL', '')}/dashboard/")
    )

    _send(
        subject=f'[SIWES] Your internship grade: {grade.letter_grade} ({grade.overall_score}/100)',
        html_body=_base_html('Internship Graded', body),
        recipient_list=[email],
    )


def notify_user_suspended(user):
    email = getattr(user, 'email', '')
    if not email:
        return

    body = (
        _h1('Your Account Has Been Suspended')
        + _badge('SUSPENDED', '#991b1b', '#fee2e2')
        + '<br><br>'
        + _p(f'Dear {user.get_full_name()},')
        + _p(
            'Your SIWES Logbook Manager account has been suspended by an administrator. '
            'You will not be able to log in until your account is reactivated.'
        )
        + _p(
            "If you believe this is a mistake, please contact your institution's "
            'SIWES coordinator.'
        )
    )

    _send(
        subject='[SIWES] Your account has been suspended',
        html_body=_base_html('Account Suspended', body),
        recipient_list=[email],
    )