from rest_framework import serializers
from apps.valoracion.serializers import ConsultaSerializer
from .models import Alimento, Recomendacion


class AlimentoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model = Alimento
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre', 'disponible_pae', 'alergeno', 'descripcion']


class RecomendacionSerializer(serializers.ModelSerializer):
    consulta_detalle = ConsultaSerializer(source='consulta', read_only=True)
    alimentos = AlimentoSerializer(many=True, read_only=True)

    class Meta:
        model = Recomendacion
        fields = ['id', 'consulta', 'consulta_detalle', 'alimentos', 'grupos_alimentarios', 'detalle', 'detalle_ia', 'fecha_generacion']
        read_only_fields = fields
