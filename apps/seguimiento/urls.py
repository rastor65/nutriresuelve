from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaSeguimientosAPIView.as_view(), name='lista_seguimientos'),
    path('<int:paciente_id>/', views.SeguimientoPacienteAPIView.as_view(), name='seguimiento_paciente'),
]
