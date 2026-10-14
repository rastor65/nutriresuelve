from decimal import Decimal

from rest_framework import serializers
from .models import Seguimiento


class SeguimientoSerializer(serializers.ModelSerializer):
    imc = serializers.ReadOnlyField()
    peso_kg = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))
    talla_cm = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))

    class Meta:
        model = Seguimiento
        fields = ['id', 'paciente', 'fecha', 'peso_kg', 'talla_cm', 'observaciones', 'imc']
        read_only_fields = ['paciente']
