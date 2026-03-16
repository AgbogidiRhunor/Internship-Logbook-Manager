from django.urls import path
from . import views

app_name = 'institutions'

urlpatterns = [
    path('', views.university_list, name='university_list'),
    path('university/add/', views.university_create, name='university_create'),
    path('university/<int:pk>/edit/', views.university_edit, name='university_edit'),
    path('university/<int:pk>/delete/', views.university_delete, name='university_delete'),
    path('university/<int:university_id>/faculty/add/', views.faculty_create, name='faculty_create'),
    path('faculty/<int:pk>/edit/', views.faculty_edit, name='faculty_edit'),
    path('faculty/<int:pk>/delete/', views.faculty_delete, name='faculty_delete'),
    path('faculty/<int:faculty_id>/department/add/', views.department_create, name='department_create'),
    path('department/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('department/<int:pk>/delete/', views.department_delete, name='department_delete'),
    # AJAX
    path('ajax/faculties/', views.get_faculties, name='ajax_faculties'),
    path('ajax/departments/', views.get_departments, name='ajax_departments'),
]
