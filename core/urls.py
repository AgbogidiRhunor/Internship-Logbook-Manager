from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

admin.site.site_header = "SIWES Logbook — Admin"
admin.site.site_title  = "SIWES Admin"
admin.site.index_title = "Platform Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.landing, name='home'),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('institutions/', include(('institutions.urls', 'institutions'), namespace='institutions')),
    path('logbook/', include(('logbook.urls', 'logbook'), namespace='logbook')),
    path('grading/', include(('grading.urls', 'grading'), namespace='grading')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)