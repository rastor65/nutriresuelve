from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.pacientes.models import Alergia, Paciente
from apps.recomendaciones.models import Alimento, CategoriaAlimento, Recomendacion
from .models import Consulta, ReglaExperto


class ValoracionAPITests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user(username='test'))
        self.paciente = Paciente.objects.create(
            nombre_completo='Paciente', fecha_nacimiento='2015-01-01', peso_kg=25, talla_cm=130,
        )
        self.url = f'/valoracion/valorar/{self.paciente.pk}/'
        self.medidas = {'peso_kg': '26.00', 'talla_cm': '130.00'}

    def create_rule(self):
        return ReglaExperto.objects.create(codigo='R-001', descripcion='Prueba', clasificacion='Prueba', observacion='Detalle')

    @patch('apps.valoracion.views.generar_plan_alimentario', return_value='Plan de prueba')
    def test_valuation_creates_consultation_and_recommendation_excluding_allergies(self, generate):
        self.create_rule()
        categoria = CategoriaAlimento.objects.create(nombre='Prueba')
        permitido = Alimento.objects.create(nombre='Arroz', categoria=categoria)
        Alimento.objects.create(nombre='Leche', categoria=categoria)
        Alimento.objects.create(nombre='Otro', categoria=categoria, disponible_pae=False)
        Alergia.objects.create(paciente=self.paciente, descripcion='Leche')
        response = self.client.post(self.url, self.medidas, format='json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(float(data['consulta']['imc_calculado']), 15.38)
        self.assertEqual(data['recomendacion']['detalle_ia'], 'Plan de prueba')
        self.assertEqual([a['id'] for a in data['recomendacion']['alimentos']], [permitido.pk])
        generate.assert_called_once()
        recommendation_id = data['recomendacion']['id']
        for url in [f'/valoracion/recomendacion/{recommendation_id}/', f'/recomendaciones/{recommendation_id}/']:
            self.assertEqual(self.client.get(url).json()['id'], recommendation_id)
        self.assertEqual(len(self.client.get('/recomendaciones/').json()), 1)
        self.assertEqual(self.client.get('/').json()['total_consultas'], 1)

    @patch('apps.valoracion.views.generar_plan_alimentario')
    def test_no_matching_rule_returns_json_error_without_writes(self, generate):
        response = self.client.post(self.url, self.medidas, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.json())
        self.assertEqual(Consulta.objects.count(), 0)
        self.assertEqual(Recomendacion.objects.count(), 0)
        generate.assert_not_called()

    @patch('apps.valoracion.views.generar_plan_alimentario')
    def test_invalid_measurements_rejected_before_generation(self, generate):
        self.create_rule()
        for medidas in [{'peso_kg': '0'}, {'talla_cm': '-1'}, {'peso_kg': 'abc'}, {'talla_cm': '0.01'}]:
            response = self.client.post(self.url, {**self.medidas, **medidas}, format='json')
            self.assertEqual(response.status_code, 400)
        generate.assert_not_called()

    @patch('apps.valoracion.views.generar_plan_alimentario', return_value='Plan')
    @patch('apps.valoracion.views.Recomendacion.objects.create', side_effect=RuntimeError('Prueba'))
    def test_failed_recommendation_rolls_back_consultation(self, create, generate):
        self.create_rule()
        with self.assertRaises(RuntimeError):
            self.client.post(self.url, self.medidas, format='json')
        self.assertEqual(Consulta.objects.count(), 0)
