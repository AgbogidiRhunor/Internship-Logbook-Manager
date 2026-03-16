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
    path('admin/pending-lecturers/', views.pending_lecturers, name='pending_lecturers'),
    path('admin/approve/<int:user_id>/', views.approve_lecturer, name='approve_lecturer'),
    path('admin/reject/<int:user_id>/', views.reject_lecturer, name='reject_lecturer'),
    path('admin/suspend/<int:user_id>/', views.suspend_user, name='suspend_user'),
    path('admin/reactivate/<int:user_id>/', views.reactivate_user, name='reactivate_user'),
]
