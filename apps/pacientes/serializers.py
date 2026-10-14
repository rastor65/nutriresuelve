from datetime import date
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers
from .models import Alergia, EPS, Paciente, RepresentanteLegal, RestriccionMedica


class MedidasSerializer(serializers.Serializer):
    peso_kg = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))
    talla_cm = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))


class EPSSerializer(serializers.ModelSerializer):
    class Meta:
        model = EPS
        fields = ['id', 'nombre']


class RepresentanteLegalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepresentanteLegal
        fields = ['id', 'nombre_completo', 'telefono', 'parentesco']


class RestriccionMedicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestriccionMedica
        fields = ['id', 'descripcion', 'medico_tratante']


class AlergiasField(serializers.ListField):
    child = serializers.CharField(max_length=200)

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = [item.strip() for item in data.split(',') if item.strip()]
        return super().to_internal_value(data)

    def to_representation(self, value):
        return list(value.values_list('descripcion', flat=True))


class PacienteSerializer(serializers.ModelSerializer):
    edad = serializers.IntegerField(read_only=True)
    imc = serializers.SerializerMethodField()
    peso_kg = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))
    talla_cm = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0.01'))
    representante_detalle = RepresentanteLegalSerializer(source='representante', read_only=True)
    restricciones = RestriccionMedicaSerializer(many=True, read_only=True)
    alergias = AlergiasField(required=False)
    rep_nombre = serializers.CharField(max_length=200, required=False, write_only=True)
    rep_telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, write_only=True)
    rep_parentesco = serializers.ChoiceField(
        choices=RepresentanteLegal._meta.get_field('parentesco').choices,
        required=False, write_only=True,
    )

    class Meta:
        model = Paciente
        fields = [
            'id', 'nombre_completo', 'fecha_nacimiento', 'peso_kg', 'talla_cm',
            'eps', 'representante', 'nivel_socioeconomico', 'nivel_actividad',
            'institucion', 'fecha_registro', 'edad', 'imc', 'representante_detalle',
            'alergias', 'restricciones', 'rep_nombre', 'rep_telefono', 'rep_parentesco',
        ]
        read_only_fields = ['fecha_registro']

    def get_imc(self, paciente):
        return paciente.imc if paciente.peso_kg and paciente.talla_cm and paciente.talla_cm > 0 else None

    def validate_fecha_nacimiento(self, value):
        if value > date.today():
            raise serializers.ValidationError('La fecha de nacimiento no puede estar en el futuro.')
        return value

    def validate(self, attrs):
        rep_fields = {'rep_nombre', 'rep_telefono', 'rep_parentesco'}
        if rep_fields.intersection(attrs):
            if 'representante' in attrs:
                raise serializers.ValidationError('Envía representante o los campos rep_, no ambos.')
            if not attrs.get('rep_nombre'):
                raise serializers.ValidationError({'rep_nombre': 'Este campo es obligatorio.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        alergias = validated_data.pop('alergias', [])
        rep_nombre = validated_data.pop('rep_nombre', None)
        rep_telefono = validated_data.pop('rep_telefono', '')
        rep_parentesco = validated_data.pop('rep_parentesco', 'otro')
        if rep_nombre:
            validated_data['representante'] = RepresentanteLegal.objects.create(
                nombre_completo=rep_nombre, telefono=rep_telefono, parentesco=rep_parentesco,
            )
        paciente = super().create(validated_data)
        Alergia.objects.bulk_create([
            Alergia(paciente=paciente, descripcion=descripcion) for descripcion in alergias
        ])
        return paciente
