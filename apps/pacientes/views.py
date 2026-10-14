from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.valoracion.serializers import ConsultaSerializer
from .models import EPS, Paciente, RepresentanteLegal
from .serializers import EPSSerializer, PacienteSerializer, RepresentanteLegalSerializer


class ListaEPSAPIView(APIView):
    serializer_class = EPSSerializer

    def get(self, request):
        return Response(self.serializer_class(EPS.objects.order_by('nombre', 'id'), many=True).data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetalleEPSAPIView(APIView):
    def get(self, request, eps_id):
        eps = get_object_or_404(EPS, pk=eps_id)
        return Response(EPSSerializer(eps).data)


class ListaRepresentantesAPIView(APIView):
    serializer_class = RepresentanteLegalSerializer

    def get(self, request):
        representantes = RepresentanteLegal.objects.order_by('nombre_completo', 'id')
        return Response(self.serializer_class(representantes, many=True).data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetalleRepresentanteAPIView(APIView):
    def get(self, request, representante_id):
        representante = get_object_or_404(RepresentanteLegal, pk=representante_id)
        return Response(RepresentanteLegalSerializer(representante).data)


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
        return Response({
            'eps_list': EPSSerializer(EPS.objects.order_by('nombre', 'id'), many=True).data,
            'representantes_list': RepresentanteLegalSerializer(
                RepresentanteLegal.objects.order_by('nombre_completo', 'id'), many=True,
            ).data,
        })


class DetallePacienteAPIView(APIView):
    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        data = dict(PacienteSerializer(paciente).data)
        data['consultas'] = ConsultaSerializer(paciente.consultas.all(), many=True).data
        return Response(data)
