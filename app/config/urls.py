from django.contrib import admin
from django.urls import path, include
from dashboard.views import api_comunas, home


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("", home),
    path("api/comunas/<int:codregion>/", api_comunas),
]