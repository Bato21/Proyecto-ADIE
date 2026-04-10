from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("traslados/", views.vista_traslados, name="vista_traslados"),
    path("api/comunas/<int:codregion>/", views.api_comunas, name="api_comunas"),
    path("api/traslados/", views.api_traslados, name="api_traslados"),
]