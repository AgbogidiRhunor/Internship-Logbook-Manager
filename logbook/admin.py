from django.contrib import admin
from .models import DailyLogEntry


@admin.register(DailyLogEntry)
class DailyLogEntryAdmin(admin.ModelAdmin):
    list_display  = ('student', 'entry_date', 'work_title', 'internship_month', 'internship_week', 'day_of_week')
    list_filter   = ('day_of_week', 'internship_month')
    search_fields = ('student__username', 'work_title')
    date_hierarchy = 'entry_date'
    readonly_fields = ('internship_month', 'internship_week', 'day_of_week', 'created_at', 'updated_at')
