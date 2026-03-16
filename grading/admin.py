from django.contrib import admin
from .models import GradeRecord


@admin.register(GradeRecord)
class GradeRecordAdmin(admin.ModelAdmin):
    list_display  = ('student', 'overall_score', 'letter_grade', 'graded_by', 'graded_at')
    list_filter   = ('letter_grade',)
    search_fields = ('student__matric_number', 'student__surname')
    readonly_fields = ('graded_at', 'updated_at', 'letter_grade')
