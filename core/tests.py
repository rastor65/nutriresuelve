from django.contrib.auth import get_user_model
from django.test import override_settings
from django.contrib.staticfiles import finders
from rest_framework.test import APITestCase, APIClient
from apps.pacientes.models import Paciente


class CookieAuthenticationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='nutricionista', password='test-password')

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def login(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', response.cookies)
        return self.client.post('/login/', {
            'username': 'nutricionista', 'password': 'test-password',
        }, format='json', HTTP_X_CSRFTOKEN=response.json()['csrfToken'])

    def test_login_requires_csrf_even_for_anonymous_users(self):
        response = self.client.post('/login/', {
            'username': 'nutricionista', 'password': 'test-password',
        }, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertNotIn('sessionid', response.cookies)

    def test_cookie_session_logout_and_csrf_rotation(self):
        old_token = self.client.get('/login/').json()['csrfToken']
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies['sessionid']['httponly'])
        self.assertNotIn('token', response.json())
        self.assertEqual(self.client.get('/session/').json()['username'], 'nutricionista')
        self.assertEqual(self.client.post('/logout/', format='json').status_code, 403)
        self.assertEqual(self.client.post('/logout/', format='json', HTTP_X_CSRFTOKEN=old_token).status_code, 403)
        logout = self.client.post('/logout/', format='json', HTTP_X_CSRFTOKEN=response.json()['csrfToken'])
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(self.client.get('/session/').status_code, 403)

    def test_invalid_credentials_do_not_create_session(self):
        token = self.client.get('/login/').json()['csrfToken']
        response = self.client.post('/login/', {
            'username': 'nutricionista', 'password': 'incorrecta',
        }, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get('/session/').status_code, 403)

    def test_authenticated_writes_require_csrf(self):
        response = self.login()
        data = {'nombre_completo': 'Paciente', 'fecha_nacimiento': '2015-01-01', 'peso_kg': '25.00', 'talla_cm': '130.00'}
        self.assertEqual(self.client.post('/pacientes/', data, format='json').status_code, 403)
        created = self.client.post('/pacientes/', data, format='json', HTTP_X_CSRFTOKEN=response.json()['csrfToken'])
        self.assertEqual(created.status_code, 201)

    def test_private_routes_return_json_without_redirecting(self):
        for url in ['/', '/session/', '/pacientes/', '/pacientes/registrar/', '/pacientes/1/',
                    '/valoracion/valorar/1/', '/valoracion/recomendacion/1/',
                    '/seguimiento/', '/seguimiento/1/', '/recomendaciones/', '/recomendaciones/1/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response['Content-Type'], 'application/json')

    @override_settings(DEBUG=False)
    def test_unknown_routes_and_removed_admin_return_json(self):
        for url in ['/ruta-inexistente/', '/admin/']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response['Content-Type'], 'application/json')


class BrowsableAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='browser-user', password='test-password')
        cls.paciente = Paciente.objects.create(
            nombre_completo='Paciente', fecha_nacimiento='2015-01-01', peso_kg=25, talla_cm=130,
        )

    def test_browser_receives_drf_interface_and_login_link(self):
        response = self.client.get('/pacientes/', HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'rest_framework/css/bootstrap.min.css', status_code=403)
        self.assertContains(response, '/api-auth/login/', status_code=403)
        self.assertTrue(finders.find('rest_framework/css/bootstrap.min.css'))

    def test_authenticated_browser_pages_render_with_forms(self):
        self.client.force_login(self.user)
        urls = ['/', '/session/', '/pacientes/', '/pacientes/registrar/',
                f'/pacientes/{self.paciente.pk}/', f'/valoracion/valorar/{self.paciente.pk}/',
                '/seguimiento/', f'/seguimiento/{self.paciente.pk}/', '/recomendaciones/']
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url, HTTP_ACCEPT='text/html')
                self.assertEqual(response.status_code, 200)
                self.assertIn('text/html', response['Content-Type'])
                self.assertContains(response, 'Django REST framework')
                if url in ['/pacientes/', '/pacientes/registrar/',
                           f'/valoracion/valorar/{self.paciente.pk}/', f'/seguimiento/{self.paciente.pk}/']:
                    self.assertContains(response, 'name="peso_kg"')
                    self.assertContains(response, 'name="talla_cm"')

    def test_browser_login_and_patient_form_use_session_and_csrf(self):
        self.client = APIClient(enforce_csrf_checks=True)
        page = self.client.get('/api-auth/login/', HTTP_ACCEPT='text/html')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="username"')
        self.assertContains(page, 'type="password"')
        response = self.client.post('/api-auth/login/', {
            'username': 'browser-user', 'password': 'test-password',
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        }, format='multipart', HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('sessionid', response.cookies)
        self.assertTrue(response.cookies['sessionid']['httponly'])
        self.assertContains(response, 'browser-user')
        created = self.client.post('/pacientes/', {
            'nombre_completo': 'Paciente desde formulario', 'fecha_nacimiento': '2015-01-01',
            'peso_kg': '25.00', 'talla_cm': '130.00',
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        }, format='multipart', HTTP_ACCEPT='text/html')
        self.assertEqual(created.status_code, 201)
        self.assertContains(created, 'Paciente desde formulario', status_code=201)
        self.assertEqual(self.client.post('/api-auth/logout/', {
            'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
        }, format='multipart').status_code, 204)
        self.assertEqual(self.client.get('/session/').status_code, 403)

    def test_json_clients_and_format_parameter_still_receive_json(self):
        self.client.force_login(self.user)
        response = self.client.get('/pacientes/', HTTP_ACCEPT='application/json')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()[0]['id'], self.paciente.pk)
        response = self.client.get('/pacientes/?format=json', HTTP_ACCEPT='text/html,application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
