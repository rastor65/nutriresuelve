from django.urls import include, path
from core import views
from apps.pacientes.views import (
    DetalleEPSAPIView, DetalleRepresentanteAPIView,
    ListaEPSAPIView, ListaRepresentantesAPIView,
)

urlpatterns = [
    path('', views.DashboardAPIView.as_view(), name='dashboard'),
    path('pacientes/', include('apps.pacientes.urls')),
    path('eps/', ListaEPSAPIView.as_view(), name='lista_eps'),
    path('eps/<int:eps_id>/', DetalleEPSAPIView.as_view(), name='detalle_eps'),
    path('representantes/', ListaRepresentantesAPIView.as_view(), name='lista_representantes'),
    path('representantes/<int:representante_id>/', DetalleRepresentanteAPIView.as_view(), name='detalle_representante'),
    path('valoracion/', include('apps.valoracion.urls')),
    path('seguimiento/', include('apps.seguimiento.urls')),
    path('recomendaciones/', include('apps.recomendaciones.urls')),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('session/', views.SessionAPIView.as_view(), name='session'),
    path('api-auth/', include(([
        path('login/', views.LoginAPIView.as_view(), name='login'),
        path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    ], 'rest_framework'), namespace='rest_framework')),
]

handler400 = 'core.views.error_400'
handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
