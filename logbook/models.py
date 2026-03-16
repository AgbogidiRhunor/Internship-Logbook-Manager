import os
import profile
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def log_photo_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    matric = instance.student.student_profile.matric_number.replace('/', '_')
    return f'logbook_photos/{matric}/{instance.entry_date}/{filename}'


class DayOfWeek(models.TextChoices):
    MONDAY = 'Monday', 'Monday'
    TUESDAY = 'Tuesday', 'Tuesday'
    WEDNESDAY = 'Wednesday', 'Wednesday'
    THURSDAY = 'Thursday', 'Thursday'
    FRIDAY = 'Friday', 'Friday'
    SATURDAY = 'Saturday', 'Saturday'
    SUNDAY = 'Sunday', 'Sunday'


class DailyLogEntry(models.Model):
    student = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='log_entries',
        limit_choices_to={'role': 'STUDENT'},
    )
    entry_date = models.DateField(db_index=True)
    work_title = models.CharField(max_length=255)
    activity_description = models.TextField(max_length=5000)
    tools_used = models.TextField(max_length=1000)
    challenges_encountered = models.TextField(max_length=2000, blank=True)
    lessons_learned = models.TextField(max_length=2000, blank=True)
    technical_photo = models.ImageField(
        upload_to=log_photo_upload_path,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
    )

    # Auto-computed fields
    internship_month = models.PositiveSmallIntegerField(editable=False)
    internship_week = models.PositiveSmallIntegerField(editable=False)
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Daily Log Entry'
        verbose_name_plural = 'Daily Log Entries'
        ordering = ['-entry_date']
        unique_together = ('student', 'entry_date')
        indexes = [
            models.Index(fields=['student', 'entry_date']),
            models.Index(fields=['student', 'internship_month']),
            models.Index(fields=['student', 'internship_week']),
        ]

    def __str__(self):
        return f'{self.student.username} — {self.entry_date}'

    def clean(self):
        super().clean()

        if not self.student_id:
            return

        profile = getattr(self.student, 'student_profile', None)
        if profile is None:
            raise ValidationError({'student': 'Selected student does not have a student profile.'})

        if self.entry_date < profile.internship_start_date:
            raise ValidationError({
            'entry_date': (
                f'Entry date cannot be before internship start date '
                f'({profile.internship_start_date}).'
            )
        })

        if self.entry_date > profile.internship_end_date:
             raise ValidationError({
            'entry_date': (
                f'Entry date cannot be after internship end date '
                f'({profile.internship_end_date}).'
            )
        })

    def _compute_internship_fields(self):
        profile = self.student.student_profile
        delta = self.entry_date - profile.internship_start_date
        total_days = delta.days  # 0-indexed from start

        self.internship_month = (total_days // 30) + 1
        self.internship_week = (total_days // 7) + 1
        self.day_of_week = self.entry_date.strftime('%A')

    def save(self, *args, **kwargs):
        self._compute_internship_fields()
        super().save(*args, **kwargs)
