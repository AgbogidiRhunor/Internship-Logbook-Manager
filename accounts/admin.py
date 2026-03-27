from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, StudentProfile, LecturerProfile, CoordinatorProfile, AuditLog
from .emails import (
    notify_lecturer_suspended, notify_lecturer_reactivated, notify_lecturer_approved,
    notify_coordinator_approved, notify_coordinator_rejected,
)


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


class CoordinatorProfileInline(admin.StackedInline):
    model = CoordinatorProfile
    can_delete = False
    verbose_name_plural = 'Coordinator Profile'
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'role', 'is_active', 'lecturer_approved', 'coordinator_approved', 'created_at')
    list_filter   = ('role', 'is_active', 'lecturer_approved', 'coordinator_approved')
    search_fields = ('username', 'email')
    ordering      = ('-created_at',)
    fieldsets = (
        (None,            {'fields': ('username', 'email', 'password')}),
        ('Role & Access', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'lecturer_approved', 'coordinator_approved')}),
        ('Security',      {'fields': ('failed_login_count', 'locked_until')}),
        ('Permissions',   {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active'),
        }),
    )
    readonly_fields = ('failed_login_count', 'locked_until', 'created_at')

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.role == 'STUDENT':
            return [StudentProfileInline]
        if obj.role == 'LECTURER':
            return [LecturerProfileInline]
        if obj.role == 'COORDINATOR':
            return [CoordinatorProfileInline]
        return []

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return
        try:
            old = CustomUser.objects.get(pk=obj.pk)
        except CustomUser.DoesNotExist:
            super().save_model(request, obj, form, change)
            return

        super().save_model(request, obj, form, change)

        if obj.role == 'LECTURER':
            if old.is_active and not obj.is_active:
                notify_lecturer_suspended(obj)
            elif not old.is_active and obj.is_active:
                notify_lecturer_reactivated(obj)
            elif not old.lecturer_approved and obj.lecturer_approved:
                notify_lecturer_approved(obj)

        if obj.role == 'COORDINATOR':
            if not old.coordinator_approved and obj.coordinator_approved:
                notify_coordinator_approved(obj)
            elif old.is_active and not obj.is_active:
                pass  # could add notify_coordinator_suspended if needed


@admin.register(CoordinatorProfile)
class CoordinatorProfileAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'university', 'user')
    search_fields = ('surname', 'other_names', 'user__username')
    list_filter   = ('university',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display    = ('actor', 'action', 'target_model', 'ip_address', 'created_at')
    list_filter     = ('action', 'target_model')
    search_fields   = ('actor__username', 'action', 'details', 'ip_address')
    readonly_fields = ('actor', 'action', 'target_model', 'target_id', 'details', 'ip_address', 'created_at')
    ordering        = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
