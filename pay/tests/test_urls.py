from django.urls import path, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from pay.tests.test_views import index

urlpatterns = [
    path('', index),
    path('pay/', include('pay.urls')),
    path('admin/', admin.site.urls),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
