from django.contrib import admin
from .models import University, Faculty, Department


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'state', 'is_active', 'created_at')
    search_fields = ('name', 'abbreviation', 'state')
    list_filter = ('is_active', 'state')
    ordering = ('name',)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'university', 'is_active', 'created_at')
    search_fields = ('name', 'university__name')
    list_filter = ('is_active', 'university')
    ordering = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'get_university', 'is_active', 'created_at')
    search_fields = ('name', 'faculty__name', 'faculty__university__name')
    list_filter = ('is_active', 'faculty', 'faculty__university')
    ordering = ('name',)

    def get_university(self, obj):
        return obj.faculty.university.name

    get_university.short_description = 'University'
    get_university.admin_order_field = 'faculty__university__name'