from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from pay.tests.test_views import index

urlpatterns = [
    url(r'^$', index),
    url(r'^pay/', include('pay.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
