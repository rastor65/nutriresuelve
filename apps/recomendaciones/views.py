from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Recomendacion
from .serializers import RecomendacionSerializer


class ListaRecomendacionesAPIView(APIView):
    def get(self, request):
        recomendaciones = Recomendacion.objects.select_related('consulta').prefetch_related('alimentos__categoria')
        return Response(RecomendacionSerializer(recomendaciones, many=True).data)


class DetalleRecomendacionAPIView(APIView):
    def get(self, request, recomendacion_id):
        recomendacion = get_object_or_404(Recomendacion, pk=recomendacion_id)
        return Response(RecomendacionSerializer(recomendacion).data)
