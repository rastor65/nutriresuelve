from rest_framework import serializers
from .models import Consulta


class ConsultaSerializer(serializers.ModelSerializer):
    recomendacion = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Consulta
        fields = [
            'id', 'paciente', 'fecha', 'peso_kg', 'talla_cm', 'imc_calculado',
            'clasificacion', 'regla_activada', 'observaciones',
            'validado_por_nutricionista', 'recomendacion',
        ]
        read_only_fields = fields
