from django.urls import path
from . import views
from apps.recomendaciones.views import DetalleRecomendacionAPIView

urlpatterns = [
    path('valorar/<int:paciente_id>/', views.ValorarPacienteAPIView.as_view(), name='valorar_paciente'),
    path('recomendacion/<int:recomendacion_id>/', DetalleRecomendacionAPIView.as_view(), name='ver_recomendacion'),
]
