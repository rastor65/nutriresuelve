from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pacientes.models import Paciente
from apps.pacientes.serializers import MedidasSerializer, PacienteSerializer
from apps.recomendaciones.models import Alimento, Recomendacion
from apps.recomendaciones.serializers import RecomendacionSerializer
from .groq_ia import generar_plan_alimentario
from .inferencia import calcular_imc, evaluar_reglas
from .models import Consulta
from .serializers import ConsultaSerializer


class ValorarPacienteAPIView(APIView):
    serializer_class = MedidasSerializer

    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        return Response({'paciente': PacienteSerializer(paciente).data})

    def post(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        serializer = MedidasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        medidas = serializer.validated_data
        imc = calcular_imc(**medidas)
        if imc >= 1000:
            raise serializers.ValidationError({'imc': 'Las medidas producen un IMC fuera del rango admitido.'})
        regla = evaluar_reglas(
            imc=imc, edad=paciente.edad, nivel_se=paciente.nivel_socioeconomico,
            nivel_actividad=paciente.nivel_actividad,
        )
        if not regla:
            raise serializers.ValidationError({'detail': 'No se encontró una regla para este paciente.'})

        alergias = paciente.alergias.values_list('descripcion', flat=True)
        alimentos = list(Alimento.objects.filter(disponible_pae=True).exclude(nombre__in=alergias))
        plan_ia = generar_plan_alimentario(paciente, regla.clasificacion, alimentos)
        with transaction.atomic():
            consulta = Consulta.objects.create(
                paciente=paciente, **medidas, imc_calculado=imc,
                clasificacion=regla.clasificacion, regla_activada=regla,
                observaciones=regla.observacion,
            )
            recomendacion = Recomendacion.objects.create(
                consulta=consulta, grupos_alimentarios=regla.clasificacion,
                detalle=regla.observacion, detalle_ia=plan_ia,
            )
            recomendacion.alimentos.set(alimentos)
        return Response({
            'consulta': ConsultaSerializer(consulta).data,
            'recomendacion': RecomendacionSerializer(recomendacion).data,
        }, status=status.HTTP_201_CREATED)
