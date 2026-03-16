from django import forms
from django.core.exceptions import ValidationError

from .models import DailyLogEntry
from accounts.validators import validate_image_file


class DailyLogEntryForm(forms.ModelForm):

    class Meta:
        model = DailyLogEntry
        fields = [
            'entry_date',
            'work_title',
            'activity_description',
            'tools_used',
            'challenges_encountered',
            'lessons_learned',
            'technical_photo',
        ]
        widgets = {
            'entry_date': forms.DateInput(attrs={'type': 'date'}),
            'work_title': forms.TextInput(attrs={'maxlength': 255}),
            'activity_description': forms.Textarea(attrs={'rows': 5, 'maxlength': 5000}),
            'tools_used': forms.Textarea(attrs={'rows': 3, 'maxlength': 1000}),
            'challenges_encountered': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000}),
            'lessons_learned': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000}),
        }

    def __init__(self, *args, student_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student_user = student_user
        if student_user:
            profile = student_user.student_profile
            self.fields['entry_date'].widget.attrs['min'] = str(profile.internship_start_date)
            self.fields['entry_date'].widget.attrs['max'] = str(profile.internship_end_date)

    def clean_entry_date(self):
        date = self.cleaned_data['entry_date']
        if self.student_user:
            profile = self.student_user.student_profile
            if date < profile.internship_start_date or date > profile.internship_end_date:
                raise ValidationError(
                    f'Entry date must be within your internship period '
                    f'({profile.internship_start_date} to {profile.internship_end_date}).'
                )
            # Duplicate check (exclude current instance on edit)
            qs = DailyLogEntry.objects.filter(student=self.student_user, entry_date=date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('You have already logged an entry for this date.')
        return date

    def clean_technical_photo(self):
        photo = self.cleaned_data.get('technical_photo')
        if photo and hasattr(photo, 'size'):
            validate_image_file(photo)
        return photo
