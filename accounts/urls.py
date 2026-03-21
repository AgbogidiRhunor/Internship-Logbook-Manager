from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/lecturer/', views.lecturer_register, name='lecturer_register'),
    path('awaiting-approval/', views.awaiting_approval_view, name='awaiting_approval'),

    # Admin — lecturer management
    path('admin/pending-lecturers/', views.pending_lecturers, name='pending_lecturers'),
    path('admin/approve/<int:user_id>/', views.approve_lecturer, name='approve_lecturer'),
    path('admin/reject/<int:user_id>/', views.reject_lecturer, name='reject_lecturer'),
    path('admin/lecturer/suspend/<int:user_id>/', views.suspend_lecturer, name='suspend_lecturer'),
    path('admin/lecturer/reactivate/<int:user_id>/', views.reactivate_lecturer, name='reactivate_lecturer'),
    path('admin/lecturers/', views.admin_lecturer_list, name='admin_lecturer_list'),
    
    # Lecturer — student suspension
    path('student/suspend/<int:user_id>/', views.suspend_student, name='suspend_student'),
    path('student/reactivate/<int:user_id>/', views.reactivate_student, name='reactivate_student'),
]
