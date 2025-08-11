from django.contrib import admin
from django.urls import path, include
from rest.urls import urlpatterns as rest_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(rest_urls)),
    path("health/", include('health_check.urls')),
]
