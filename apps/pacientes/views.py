from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.valoracion.serializers import ConsultaSerializer
from .models import EPS, Paciente
from .serializers import EPSSerializer, PacienteSerializer


class ListaPacientesAPIView(APIView):
    serializer_class = PacienteSerializer

    def get(self, request):
        pacientes = Paciente.objects.select_related('representante').prefetch_related('alergias', 'restricciones')
        return Response(PacienteSerializer(pacientes, many=True).data)

    def post(self, request):
        serializer = PacienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegistrarPacienteAPIView(ListaPacientesAPIView):
    def get(self, request):
        return Response({'eps_list': EPSSerializer(EPS.objects.all(), many=True).data})


class DetallePacienteAPIView(APIView):
    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        data = dict(PacienteSerializer(paciente).data)
        data['consultas'] = ConsultaSerializer(paciente.consultas.all(), many=True).data
        return Response(data)
