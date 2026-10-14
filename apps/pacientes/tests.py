from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from .models import Alergia, EPS, Paciente, RepresentanteLegal


class PacienteAPITests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(get_user_model().objects.create_user(username='test'))
        self.data = {
            'nombre_completo': 'Paciente', 'fecha_nacimiento': '2015-01-01',
            'peso_kg': '25.00', 'talla_cm': '130.00',
            'rep_nombre': 'Representante', 'rep_telefono': '3000000000',
            'rep_parentesco': 'madre', 'alergias': ['Leche', 'Maní'],
        }

    def test_register_list_and_detail(self):
        eps = EPS.objects.create(nombre='EPS de prueba')
        self.data['eps'] = eps.pk
        response = self.client.post('/pacientes/registrar/', self.data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['eps'], eps.pk)
        self.assertEqual(response.json()['representante_detalle']['nombre_completo'], 'Representante')
        self.assertEqual(response.json()['alergias'], ['Leche', 'Maní'])
        self.assertEqual(len(self.client.get('/pacientes/').json()), 1)
        detail = self.client.get(f"/pacientes/{response.json()['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()['consultas'], [])
        self.assertEqual(self.client.get('/pacientes/registrar/').json()['eps_list'][0]['id'], eps.pk)

    def test_invalid_patient_does_not_leave_partial_records(self):
        for invalid in [{'talla_cm': '0'}, {'peso_kg': '-1'}, {'nombre_completo': ''},
                        {'fecha_nacimiento': 'incorrecta'}, {'fecha_nacimiento': '2999-01-01'},
                        {'rep_parentesco': 'inexistente'}, {'alergias': ['a' * 201]}]:
            with self.subTest(invalid=invalid):
                response = self.client.post('/pacientes/registrar/', {**self.data, **invalid}, format='json')
                self.assertEqual(response.status_code, 400)
        self.assertEqual(Paciente.objects.count(), 0)
        self.assertEqual(RepresentanteLegal.objects.count(), 0)
        self.assertEqual(Alergia.objects.count(), 0)

    def test_comma_separated_allergies_and_missing_patient(self):
        response = self.client.post('/pacientes/', {**self.data, 'alergias': 'Leche, Maní'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['alergias'], ['Leche', 'Maní'])
        self.assertEqual(self.client.get('/pacientes/99999/').status_code, 404)

    def test_malformed_json_returns_400(self):
        response = self.client.post('/pacientes/', '{invalid', content_type='application/json')
        self.assertEqual(response.status_code, 400)
