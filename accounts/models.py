from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    STUDENT = 'STUDENT', 'Student'
    LECTURER = 'LECTURER', 'Lecturer'
    COORDINATOR = 'COORDINATOR', 'School Coordinator'
    ADMIN = 'ADMIN', 'Admin'


class CustomUserManager(BaseUserManager):

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required.')
        user = self.model(username=username.strip().lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('lecturer_approved', True)
        extra_fields.setdefault('coordinator_approved', True)
        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=80, unique=True, db_index=True)
    email = models.EmailField(max_length=254, blank=True, db_index=True)
    role = models.CharField(
        max_length=15,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    lecturer_approved = models.BooleanField(default=False)
    coordinator_approved = models.BooleanField(default=False)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.username} ({self.role})'

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT

    @property
    def is_lecturer(self):
        return self.role == UserRole.LECTURER

    @property
    def is_coordinator(self):
        return self.role == UserRole.COORDINATOR

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def can_access(self):
        if self.is_lecturer:
            return self.lecturer_approved and self.is_active
        if self.is_coordinator:
            return self.coordinator_approved and self.is_active
        return self.is_active

    @property
    def is_locked(self):
        if self.locked_until is None:
            return False
        return timezone.now() < self.locked_until

    def record_failed_login(self):
        self.failed_login_count += 1
        if self.failed_login_count >= 10:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=['failed_login_count', 'locked_until'])

    def reset_failed_login(self):
        if self.failed_login_count > 0 or self.locked_until:
            self.failed_login_count = 0
            self.locked_until = None
            self.save(update_fields=['failed_login_count', 'locked_until'])

    def get_full_name(self):
        if self.is_student and hasattr(self, 'student_profile'):
            return f'{self.student_profile.surname} {self.student_profile.other_names}'
        if self.is_lecturer and hasattr(self, 'lecturer_profile'):
            return f'{self.lecturer_profile.surname} {self.lecturer_profile.other_names}'
        if self.is_coordinator and hasattr(self, 'coordinator_profile'):
            return f'{self.coordinator_profile.surname} {self.coordinator_profile.other_names}'
        return self.username

    def get_short_name(self):
        return self.username


class StudentProfile(models.Model):

    class InternshipDuration(models.TextChoices):
        THREE_MONTHS = '3', '3 Months'
        SIX_MONTHS = '6', '6 Months'

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='student_profile',
    )
    surname = models.CharField(max_length=100)
    other_names = models.CharField(max_length=150)
    matric_number = models.CharField(max_length=30, unique=True, db_index=True)
    university = models.ForeignKey(
        'institutions.University', on_delete=models.PROTECT, related_name='students',
    )
    faculty = models.ForeignKey(
        'institutions.Faculty', on_delete=models.PROTECT, related_name='students',
    )
    department = models.ForeignKey(
        'institutions.Department', on_delete=models.PROTECT, related_name='students',
    )
    year_of_study = models.PositiveSmallIntegerField()
    company_name = models.CharField(max_length=200)
    industrial_supervisor_name = models.CharField(max_length=200)
    internship_duration = models.CharField(max_length=1, choices=InternshipDuration.choices)
    internship_start_date = models.DateField()
    internship_end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        indexes = [
            models.Index(fields=['university', 'faculty', 'department']),
        ]

    def __str__(self):
        return f'{self.surname} {self.other_names} ({self.matric_number})'

    @property
    def full_name(self):
        return f'{self.surname} {self.other_names}'

    @property
    def total_internship_days(self):
        return (self.internship_end_date - self.internship_start_date).days + 1

    @property
    def days_logged(self):
        return self.user.log_entries.count()

    @property
    def days_remaining(self):
        today = timezone.now().date()
        if today > self.internship_end_date:
            return 0
        return max(0, (self.internship_end_date - today).days)

    @property
    def progress_percentage(self):
        if self.total_internship_days == 0:
            return 0
        return min(100, round((self.days_logged / self.total_internship_days) * 100))

    @property
    def is_graded(self):
        return hasattr(self, 'grade_record') and self.grade_record is not None

    @property
    def last_log_date(self):
        entry = self.user.log_entries.order_by('-entry_date').first()
        return entry.entry_date if entry else None

    @property
    def is_inactive(self):
        if not self.last_log_date:
            return True
        return (timezone.now().date() - self.last_log_date).days >= 3

    @property
    def has_duplicate_logs(self):
        from django.db.models import Count
        return self.user.log_entries.values('entry_date').annotate(
            c=Count('id')
        ).filter(c__gt=1).exists()


class LecturerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='lecturer_profile',
    )
    surname = models.CharField(max_length=100)
    other_names = models.CharField(max_length=150)
    university = models.ForeignKey(
        'institutions.University', on_delete=models.PROTECT, related_name='lecturers',
    )
    faculty = models.ForeignKey(
        'institutions.Faculty', on_delete=models.PROTECT, related_name='lecturers',
    )
    department = models.ForeignKey(
        'institutions.Department', on_delete=models.PROTECT, related_name='lecturers',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lecturer Profile'
        verbose_name_plural = 'Lecturer Profiles'
        indexes = [
            models.Index(fields=['university', 'faculty', 'department']),
        ]

    def __str__(self):
        return f'{self.surname} {self.other_names}'

    @property
    def full_name(self):
        return f'{self.surname} {self.other_names}'

    def get_students(self):
        return StudentProfile.objects.filter(
            university=self.university,
            faculty=self.faculty,
            department=self.department,
        ).select_related('user', 'university', 'faculty', 'department')


class CoordinatorProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='coordinator_profile',
    )
    surname = models.CharField(max_length=100)
    other_names = models.CharField(max_length=150)
    university = models.ForeignKey(
        'institutions.University', on_delete=models.PROTECT, related_name='coordinators',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Coordinator Profile'
        verbose_name_plural = 'School Coordinator Profiles'

    def __str__(self):
        return f'{self.surname} {self.other_names} — {self.university}'

    @property
    def full_name(self):
        return f'{self.surname} {self.other_names}'


class AuditLog(models.Model):
    actor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='audit_logs',
    )
    action = models.CharField(max_length=200, db_index=True)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=50, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]

    def __str__(self):
        return f'{self.actor} - {self.action} @ {self.created_at:%Y-%m-%d %H:%M}'
