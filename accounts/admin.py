from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, StudentProfile, LecturerProfile, AuditLog


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    extra = 0


class LecturerProfileInline(admin.StackedInline):
    model = LecturerProfile
    can_delete = False
    verbose_name_plural = 'Lecturer Profile'
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'role', 'is_active', 'lecturer_approved', 'created_at')
    list_filter   = ('role', 'is_active', 'lecturer_approved')
    search_fields = ('username', 'email')
    ordering      = ('-created_at',)
    fieldsets = (
        (None,            {'fields': ('username', 'email', 'password')}),
        ('Role & Access', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'lecturer_approved')}),
        ('Permissions',   {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active'),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.role == 'STUDENT':
            return [StudentProfileInline]
        if obj.role == 'LECTURER':
            return [LecturerProfileInline]
        return []

    def save_model(self, request, obj, form, change):
        if change and obj.role == 'LECTURER':
            from .emails import notify_lecturer_approved, notify_lecturer_rejected
            try:
                old = CustomUser.objects.get(pk=obj.pk)
            except CustomUser.DoesNotExist:
                old = None

            super().save_model(request, obj, form, change)

            if old:
                # Was not approved, now is — send approval email
                if not old.lecturer_approved and obj.lecturer_approved:
                    notify_lecturer_approved(obj)
                # Was active, now suspended — send suspension email
                elif old.is_active and not obj.is_active:
                    from .emails import notify_user_suspended
                    notify_user_suspended(obj)
        else:
            super().save_model(request, obj, form, change)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display    = ('actor', 'action', 'target_model', 'ip_address', 'created_at')
    list_filter     = ('action', 'target_model')
    search_fields   = ('actor__username', 'action', 'details')
    readonly_fields = ('actor', 'action', 'target_model', 'target_id', 'details', 'ip_address', 'created_at')
    ordering        = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False