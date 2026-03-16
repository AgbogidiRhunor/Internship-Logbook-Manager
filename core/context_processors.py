"""
core/context_processors.py
Global template context processors for SIWES Logbook Manager.
"""


def pending_approvals_count(request):
    """
    Injects `pending_approvals` count into every template context.
    Only performs the query if the user is an authenticated admin.
    """
    count = 0
    if request.user.is_authenticated and getattr(request.user, 'is_admin', False):
        from accounts.models import CustomUser, UserRole
        count = CustomUser.objects.filter(
            role=UserRole.LECTURER,
            lecturer_approved=False,
            is_active=True,
        ).count()
    return {'pending_approvals': count}


def user_profile(request):
    """
    Inject role-specific profile into every template.
    Avoids repeated attribute lookups in templates.
    """
    context = {}
    if request.user.is_authenticated:
        if getattr(request.user, 'is_student', False):
            context['student_profile'] = getattr(request.user, 'student_profile', None)
        elif getattr(request.user, 'is_lecturer', False):
            context['lecturer_profile'] = getattr(request.user, 'lecturer_profile', None)
    return context
