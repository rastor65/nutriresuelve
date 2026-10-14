from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.pacientes.models import Paciente
from apps.valoracion.models import Consulta
from .models import Seguimiento


class SeguimientoAPITests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user(username='test'))
        self.paciente = Paciente.objects.create(
            nombre_completo='Paciente', fecha_nacimiento='2015-01-01', peso_kg=25, talla_cm=130,
        )
        self.url = f'/seguimiento/{self.paciente.pk}/'

    def test_create_follow_up_and_return_chart_data(self):
        consulta = Consulta.objects.create(
            paciente=self.paciente, peso_kg=25, talla_cm=130, imc_calculado='14.79', clasificacion='Prueba',
        )
        response = self.client.post(self.url, {
            'fecha': '2026-10-14', 'peso_kg': '26.00', 'talla_cm': '130.00', 'observaciones': 'Prueba',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['paciente'], self.paciente.pk)
        data = self.client.get(self.url).json()
        self.assertEqual(len(data['seguimientos']), 1)
        self.assertEqual(data['imcs'], [14.79])
        self.assertEqual(data['fechas'], [str(consulta.fecha.date())])
        self.assertEqual(self.client.get('/seguimiento/').json()['pacientes'][0]['total_consultas'], 1)

    def test_invalid_follow_up_and_missing_patient(self):
        response = self.client.post(self.url, {'fecha': 'incorrecta', 'peso_kg': '25', 'talla_cm': '0'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Seguimiento.objects.count(), 0)
        self.assertEqual(self.client.get('/seguimiento/99999/').status_code, 404)
