from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import CustomUser, StudentProfile, LecturerProfile, UserRole
from .validators import validate_matric_number, validate_username
from institutions.models import University, Faculty, Department


class StudentRegistrationForm(forms.Form):
    # Personal information
    surname = forms.CharField(max_length=100, strip=True)
    other_names = forms.CharField(max_length=150, strip=True)
    matric_number = forms.CharField(
        max_length=30,
        strip=True,
        validators=[validate_matric_number],
    )
    university = forms.ModelChoiceField(queryset=University.objects.filter(is_active=True))
    faculty = forms.ModelChoiceField(queryset=Faculty.objects.filter(is_active=True))
    department = forms.ModelChoiceField(queryset=Department.objects.filter(is_active=True))
    year_of_study = forms.IntegerField(min_value=1, max_value=7)
    company_name = forms.CharField(max_length=200, strip=True)
    industrial_supervisor_name = forms.CharField(max_length=200, strip=True)
    internship_duration = forms.ChoiceField(
        choices=StudentProfile.InternshipDuration.choices,
    )
    internship_start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    internship_end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    # Account credentials
    email = forms.EmailField(
        max_length=254,
        help_text='Used for grade and account notifications.',
    )
    username = forms.CharField(
        max_length=80,
        strip=True,
        validators=[validate_username],
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
    )
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('That username is already taken.')
        return username

    def clean_matric_number(self):
        matric = self.cleaned_data['matric_number'].strip().upper()
        if StudentProfile.objects.filter(matric_number=matric).exists():
            raise ValidationError('A student with this matric number already exists.')
        return matric

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('password_confirm')
        start = cleaned.get('internship_start_date')
        end = cleaned.get('internship_end_date')
        duration = cleaned.get('internship_duration')
        faculty = cleaned.get('faculty')
        department = cleaned.get('department')
        university = cleaned.get('university')

        if password and confirm and password != confirm:
            self.add_error('password_confirm', 'Passwords do not match.')

        if start and end:
            if start >= end:
                self.add_error('internship_end_date', 'End date must be after start date.')
            else:
                days = (end - start).days
                if duration == '3' and not (80 <= days <= 100):
                    self.add_error(
                        'internship_end_date',
                        '3-month internship should span approximately 90 days.',
                    )
                elif duration == '6' and not (170 <= days <= 190):
                    self.add_error(
                        'internship_end_date',
                        '6-month internship should span approximately 180 days.',
                    )

        # Ensure faculty belongs to university
        if faculty and university and faculty.university_id != university.id:
            self.add_error('faculty', 'Selected faculty does not belong to this university.')

        # Ensure department belongs to faculty
        if department and faculty and department.faculty_id != faculty.id:
            self.add_error('department', 'Selected department does not belong to this faculty.')

        return cleaned

    def save(self):
        data = self.cleaned_data
        user = CustomUser.objects.create_user(
            username=data['username'],
            password=data['password'],
            role=UserRole.STUDENT,
            email=data.get('email', ''),
        )
        StudentProfile.objects.create(
            user=user,
            surname=data['surname'],
            other_names=data['other_names'],
            matric_number=data['matric_number'],
            university=data['university'],
            faculty=data['faculty'],
            department=data['department'],
            year_of_study=data['year_of_study'],
            company_name=data['company_name'],
            industrial_supervisor_name=data['industrial_supervisor_name'],
            internship_duration=data['internship_duration'],
            internship_start_date=data['internship_start_date'],
            internship_end_date=data['internship_end_date'],
        )
        return user


class LecturerRegistrationForm(forms.Form):
    surname = forms.CharField(max_length=100, strip=True)
    other_names = forms.CharField(max_length=150, strip=True)
    university = forms.ModelChoiceField(queryset=University.objects.filter(is_active=True))
    faculty = forms.ModelChoiceField(queryset=Faculty.objects.filter(is_active=True))
    department = forms.ModelChoiceField(queryset=Department.objects.filter(is_active=True))
    email = forms.EmailField(
        max_length=254,
        help_text='Used for approval and account notifications.',
    )
    username = forms.CharField(
        max_length=80,
        strip=True,
        validators=[validate_username],
    )
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('That username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('password_confirm')
        faculty = cleaned.get('faculty')
        department = cleaned.get('department')
        university = cleaned.get('university')

        if password and confirm and password != confirm:
            self.add_error('password_confirm', 'Passwords do not match.')

        if faculty and university and faculty.university_id != university.id:
            self.add_error('faculty', 'Selected faculty does not belong to this university.')

        if department and faculty and department.faculty_id != faculty.id:
            self.add_error('department', 'Selected department does not belong to this faculty.')

        return cleaned

    def save(self):
        data = self.cleaned_data
        user = CustomUser.objects.create_user(
            username=data['username'],
            password=data['password'],
            role=UserRole.LECTURER,
            lecturer_approved=False,
            is_active=True,
            email=data.get('email', ''),
        )
        LecturerProfile.objects.create(
            user=user,
            surname=data['surname'],
            other_names=data['other_names'],
            university=data['university'],
            faculty=data['faculty'],
            department=data['department'],
        )
        return user


class SIWESLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    remember_me = forms.BooleanField(required=False)

    error_messages = {
        'invalid_login': 'Incorrect username or password. Please try again.',
        'inactive': 'This account has been suspended.',
    }
