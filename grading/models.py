"""
grading/models.py
Holistic grading model — one grade record per student internship.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class LetterGrade(models.TextChoices):
    A = 'A', 'A — Excellent (70–100)'
    B = 'B', 'B — Good (60–69)'
    C = 'C', 'C — Average (50–59)'
    D = 'D', 'D — Below Average (45–49)'
    E = 'E', 'E — Pass (40–44)'
    F = 'F', 'F — Fail (0–39)'


def score_to_letter(score: int) -> str:
    if score >= 70:
        return LetterGrade.A
    elif score >= 60:
        return LetterGrade.B
    elif score >= 50:
        return LetterGrade.C
    elif score >= 45:
        return LetterGrade.D
    elif score >= 40:
        return LetterGrade.E
    else:
        return LetterGrade.F


class GradeRecord(models.Model):
    student = models.OneToOneField(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='grade_record',
    )
    graded_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.PROTECT,
        related_name='grades_given',
        null=True,
        blank=True,
        limit_choices_to={'role': 'LECTURER'},
    )
    overall_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    letter_grade = models.CharField(max_length=2, choices=LetterGrade.choices)
    lecturer_comment = models.TextField(max_length=2000)
    graded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Grade Record'
        verbose_name_plural = 'Grade Records'
        ordering = ['-graded_at']

    def __str__(self):
        return f'{self.student} — {self.letter_grade} ({self.overall_score})'

    def clean(self):
        super().clean()
        # graded_by is assigned in the view after form validation,
        # so it may not exist yet during form.is_valid(). Skip scope
        # check if it hasn't been set.
        try:
            graded_by = self.graded_by
        except Exception:
            return

        if graded_by is None:
            return

        try:
            lp = graded_by.lecturer_profile
        except Exception:
            return

        sp = self.student
        if sp is None:
            return

        if (lp.university_id != sp.university_id or
                lp.faculty_id != sp.faculty_id or
                lp.department_id != sp.department_id):
            raise ValidationError(
                'Lecturer can only grade students from their own '
                'university, faculty, and department.'
            )

    def save(self, *args, **kwargs):
        self.letter_grade = score_to_letter(self.overall_score)
        super().save(*args, **kwargs)