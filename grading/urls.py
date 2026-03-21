from django.urls import path
from . import views

app_name = 'grading'

urlpatterns = [
    path('students/', views.student_list, name='student_list'),
    path('students/<int:student_id>/', views.student_profile_view, name='student_profile'),
    path('students/<int:student_id>/grade/', views.grade_student, name='grade_student'),
    path('students/<int:student_id>/entries/<int:entry_id>/', views.student_entry_detail, name='entry_detail'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]
