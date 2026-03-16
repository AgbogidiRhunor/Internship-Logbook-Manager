from django import forms
from .models import GradeRecord


class GradeRecordForm(forms.ModelForm):

    class Meta:
        model = GradeRecord
        fields = ['overall_score', 'lecturer_comment']
        widgets = {
            'overall_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'lecturer_comment': forms.Textarea(attrs={'rows': 5, 'maxlength': 2000}),
        }
        labels = {
            'overall_score': 'Overall Score (0 – 100)',
            'lecturer_comment': 'Lecturer Comment',
        }
