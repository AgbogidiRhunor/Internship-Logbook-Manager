from django.urls import path
from . import views

app_name = 'logbook'

urlpatterns = [
    path('', views.log_list, name='log_list'),
    path('create/', views.log_create, name='log_create'),
    path('<int:pk>/', views.log_detail, name='log_detail'),
    path('<int:pk>/edit/', views.log_edit, name='log_edit'),
    path('<int:pk>/delete/', views.log_delete, name='log_delete'),
]
