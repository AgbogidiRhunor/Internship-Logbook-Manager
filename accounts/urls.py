from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/lecturer/', views.lecturer_register, name='lecturer_register'),
    path('register/coordinator/', views.coordinator_register, name='coordinator_register'),
    path('awaiting-approval/', views.awaiting_approval_view, name='awaiting_approval'),
    # Admin — coordinator management
    path('admin/pending-coordinators/', views.pending_coordinators, name='pending_coordinators'),
    path('admin/coordinator/approve/<int:user_id>/', views.approve_coordinator, name='approve_coordinator'),
    path('admin/coordinator/reject/<int:user_id>/', views.reject_coordinator, name='reject_coordinator'),
    # Admin — lecturer management
    path('admin/pending-lecturers/', views.pending_lecturers, name='pending_lecturers'),
    path('admin/approve/<int:user_id>/', views.approve_lecturer, name='approve_lecturer'),
    path('admin/reject/<int:user_id>/', views.reject_lecturer, name='reject_lecturer'),
    path('admin/lecturer/suspend/<int:user_id>/', views.suspend_lecturer, name='suspend_lecturer'),
    path('admin/lecturer/reactivate/<int:user_id>/', views.reactivate_lecturer, name='reactivate_lecturer'),
    path('admin/lecturers/', views.admin_lecturer_list, name='admin_lecturer_list'),
    # Coordinator — lecturer approval
    path('coordinator/pending-lecturers/', views.coordinator_pending_lecturers, name='coordinator_pending_lecturers'),
    path('coordinator/approve/<int:user_id>/', views.coordinator_approve_lecturer, name='coordinator_approve_lecturer'),
    path('coordinator/reject/<int:user_id>/', views.coordinator_reject_lecturer, name='coordinator_reject_lecturer'),
    # Lecturer — student suspension
    path('student/suspend/<int:user_id>/', views.suspend_student, name='suspend_student'),
    path('student/reactivate/<int:user_id>/', views.reactivate_student, name='reactivate_student'),
]
