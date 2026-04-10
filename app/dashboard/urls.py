from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("traslados/", views.vista_traslados, name="vista_traslados"),
    path("analisis/region/<int:codregion>/", views.analisis_region, name="analisis_region"),
    path("analisis/comuna/<int:cod_comuna>/", views.analisis_comuna, name="analisis_comuna"),
    path("analisis/hospital/<int:cod_hospital>/", views.analisis_hospital, name="analisis_hospital"),
    path("api/comunas/<int:codregion>/", views.api_comunas, name="api_comunas"),
    path("api/traslados/", views.api_traslados, name="api_traslados"),
    path("analisis/pais/", views.analisis_pais, name="analisis_pais"),
]