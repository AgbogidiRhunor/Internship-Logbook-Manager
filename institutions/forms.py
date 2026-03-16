from django import forms
from .models import University, Faculty, Department


class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'abbreviation', 'state', 'is_active']


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['name', 'is_active']


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'is_active']
