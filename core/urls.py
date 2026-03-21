from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home_redirect

admin.site.site_header = "SIWES Logbook — Admin"
admin.site.site_title = "SIWES Admin"
admin.site.index_title = "Platform Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('institutions/', include('institutions.urls', namespace='institutions')),
    path('logbook/', include('logbook.urls', namespace='logbook')),
    path('grading/', include('grading.urls', namespace='grading')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
