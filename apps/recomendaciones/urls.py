from django.urls import path
from .views import DetalleRecomendacionAPIView, ListaRecomendacionesAPIView

urlpatterns = [
    path('', ListaRecomendacionesAPIView.as_view(), name='lista_recomendaciones'),
    path('<int:recomendacion_id>/', DetalleRecomendacionAPIView.as_view(), name='detalle_recomendacion'),
]
