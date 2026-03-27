def pending_approvals_count(request):
    context = {'pending_approvals': 0, 'pending_coordinators': 0, 'pending_lecturers_count': 0}
    if not request.user.is_authenticated:
        return context
    from accounts.models import CustomUser, UserRole
    if getattr(request.user, 'is_admin', False):
        context['pending_approvals'] = CustomUser.objects.filter(
            role=UserRole.LECTURER, lecturer_approved=False, is_active=True,
        ).count()
        context['pending_coordinators'] = CustomUser.objects.filter(
            role=UserRole.COORDINATOR, coordinator_approved=False, is_active=True,
        ).count()
    if getattr(request.user, 'is_coordinator', False) and getattr(request.user, 'coordinator_approved', False):
        try:
            cp = request.user.coordinator_profile
            context['pending_lecturers_count'] = CustomUser.objects.filter(
                role=UserRole.LECTURER, lecturer_approved=False, is_active=True,
                lecturer_profile__university=cp.university,
            ).count()
        except Exception:
            pass
    return context


def user_profile(request):
    context = {}
    if not request.user.is_authenticated:
        return context
    if getattr(request.user, 'is_student', False):
        context['student_profile'] = getattr(request.user, 'student_profile', None)
    elif getattr(request.user, 'is_lecturer', False):
        context['lecturer_profile'] = getattr(request.user, 'lecturer_profile', None)
    elif getattr(request.user, 'is_coordinator', False):
        context['coordinator_profile'] = getattr(request.user, 'coordinator_profile', None)
    return context
