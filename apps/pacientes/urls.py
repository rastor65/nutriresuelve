from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListaPacientesAPIView.as_view(), name='lista_pacientes'),
    path('registrar/', views.RegistrarPacienteAPIView.as_view(), name='registrar_paciente'),
    path('<int:paciente_id>/', views.DetallePacienteAPIView.as_view(), name='detalle_paciente'),
]
