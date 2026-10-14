from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pacientes.models import Paciente
from apps.pacientes.serializers import PacienteSerializer
from apps.valoracion.serializers import ConsultaSerializer
from .serializers import SeguimientoSerializer


class SeguimientoPacienteAPIView(APIView):
    serializer_class = SeguimientoSerializer

    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        consultas = list(paciente.consultas.order_by('fecha'))
        return Response({
            'paciente': PacienteSerializer(paciente).data,
            'seguimientos': SeguimientoSerializer(paciente.seguimientos.order_by('fecha'), many=True).data,
            'consultas': ConsultaSerializer(consultas, many=True).data,
            'fechas': [str(consulta.fecha.date()) for consulta in consultas],
            'imcs': [float(consulta.imc_calculado) for consulta in consultas],
        })

    def post(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        serializer = SeguimientoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(paciente=paciente)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ListaSeguimientosAPIView(APIView):
    def get(self, request):
        pacientes = Paciente.objects.annotate(total_consultas=Count('consultas')).filter(
            total_consultas__gt=0
        ).order_by('-total_consultas')
        data = []
        for paciente in pacientes:
            item = dict(PacienteSerializer(paciente).data)
            item['total_consultas'] = paciente.total_consultas
            data.append(item)
        return Response({'pacientes': data})
