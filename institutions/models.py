from django.db import models


class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    abbreviation = models.CharField(max_length=20, blank=True)
    state = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'University'
        verbose_name_plural = 'Universities'
        ordering = ['name']

    def __str__(self):
        return self.name


class Faculty(models.Model):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faculties',
    )
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculties'
        ordering = ['name']
        unique_together = ('university', 'name')

    def __str__(self):
        return f'{self.name} — {self.university.name}'


class Department(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='departments',
    )
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']
        unique_together = ('faculty', 'name')

    def __str__(self):
        return f'{self.name} — {self.faculty.name}'
