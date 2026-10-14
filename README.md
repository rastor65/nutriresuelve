# NutriGuajira — API de valoración nutricional

Backend Django y Django REST Framework para registrar pacientes, realizar valoraciones, generar recomendaciones con Groq y consultar seguimientos. Los endpoints usan `APIView`: los clientes de la API reciben JSON y el navegador muestra la interfaz navegable de DRF. La autenticación utiliza cookies de sesión de Django. La interfaz utiliza las plantillas incorporadas en DRF; no hay templates personalizados ni panel Django Admin.

## Interfaz navegable de Django REST Framework

Abre `http://127.0.0.1:8000/pacientes/` para ver la interfaz de DRF con sus botones y formularios. Usa **Log in** (o `/api-auth/login/`) para iniciar sesión con las mismas cookies de la API. Después del login vuelve a `/pacientes/` para consultar o registrar pacientes. También puedes abrir `/login/` y enviar sus campos `username` y `password` desde el formulario de DRF.

El navegador solicita `text/html` y recibe la interfaz navegable. Para obtener JSON usa `Accept: application/json` o añade `?format=json` a la URL. Los formularios admiten datos de formulario y JSON desde la pestaña **Raw data**, siguiendo la [documentación de la API navegable](https://www.django-rest-framework.org/topics/browsable-api/).

En desarrollo, `runserver` sirve automáticamente el CSS y JavaScript de DRF. En producción ejecuta `python manage.py collectstatic` y configura el servidor para servir `/static/` desde `staticfiles/`.

## Instalación

Requiere Python 3.10 o superior.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crea `.env` en la raíz:

```dotenv
SECRET_KEY=una_clave_secreta_django
DEBUG=True
GROQ_API_KEY=tu_clave_de_groq
```

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

El usuario creado permite iniciar sesión en la API. Los datos de EPS, alimentos y reglas expertas se pueden cargar mediante fixtures (`python manage.py loaddata archivo.json`) o desde `python manage.py shell`. Una valoración necesita al menos una regla experta compatible con el paciente.

## Autenticación con cookies

1. `GET /login/` establece la cookie `csrftoken` y devuelve `csrfToken`.
2. `POST /login/` recibe `username` y `password` en JSON, con el encabezado `X-CSRFToken`. Establece la cookie `sessionid` (`HttpOnly`) y devuelve un nuevo `csrfToken`, porque Django rota el token al iniciar sesión.
3. Envía las cookies en las siguientes peticiones y el nuevo token CSRF en las peticiones que modifican datos.
4. `GET /session/` devuelve el usuario autenticado; `POST /logout/` cierra la sesión y responde `204`.

Ejemplo desde un frontend servido en el mismo origen que la API:

```javascript
let response = await fetch('/login/', { credentials: 'include' });
let { csrfToken } = await response.json();

response = await fetch('/login/', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
  body: JSON.stringify({ username: 'tu_usuario', password: 'tu_contraseña' }),
});
if (!response.ok) throw new Error('No se pudo iniciar sesión');
({ csrfToken } = await response.json());

const pacientes = await fetch('/pacientes/', { credentials: 'include' });

await fetch('/logout/', {
  method: 'POST',
  credentials: 'include',
  headers: { 'X-CSRFToken': csrfToken },
});
```

Todas las rutas de datos requieren sesión. La ausencia de sesión o un token CSRF incorrecto devuelve `403` en JSON. Los datos inválidos devuelven `400`; los recursos inexistentes, `404`. El login también exige CSRF para usuarios anónimos. Este comportamiento sigue la [documentación de SessionAuthentication](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication).

Con `DEBUG=False`, las cookies requieren HTTPS. Configura `ALLOWED_HOSTS` para el dominio del despliegue. Para desarrollo local mediante HTTP usa `DEBUG=True`. El ejemplo presupone el mismo origen; un frontend con origen diferente necesita configuración adicional de CORS y `CSRF_TRUSTED_ORIGINS`.

## Endpoints

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/` | Estadísticas y últimos pacientes |
| GET | `/pacientes/` | Lista de pacientes |
| POST | `/pacientes/` o `/pacientes/registrar/` | Registrar paciente (`201`) |
| GET | `/pacientes/registrar/` | Catálogo de EPS |
| GET | `/pacientes/<id>/` | Paciente, representante, alergias, restricciones y consultas |
| GET | `/valoracion/valorar/<paciente_id>/` | Datos del paciente para valoración |
| POST | `/valoracion/valorar/<paciente_id>/` | Crear consulta y recomendación (`201`) |
| GET | `/valoracion/recomendacion/<id>/` | Recomendación y alimentos |
| GET | `/recomendaciones/` | Lista de recomendaciones |
| GET | `/recomendaciones/<id>/` | Detalle de recomendación |
| GET | `/seguimiento/` | Pacientes con consultas y total de consultas |
| GET | `/seguimiento/<paciente_id>/` | Seguimientos, consultas, fechas e IMC para gráficas |
| POST | `/seguimiento/<paciente_id>/` | Registrar seguimiento (`201`) |

Registro de paciente:

```json
{
  "nombre_completo": "Paciente de ejemplo",
  "fecha_nacimiento": "2015-01-01",
  "peso_kg": "25.00",
  "talla_cm": "130.00",
  "nivel_socioeconomico": "bajo",
  "nivel_actividad": "baja",
  "institucion": "Colegio",
  "rep_nombre": "Representante de ejemplo",
  "rep_telefono": "3000000000",
  "rep_parentesco": "madre",
  "alergias": ["Leche", "Maní"]
}
```

`eps` y `representante` aceptan IDs existentes y son opcionales. Para crear un representante usa los campos `rep_`; no combines estos campos con `representante`. `alergias` acepta una lista de textos o un texto separado por comas.

Valoración:

```json
{ "peso_kg": "26.00", "talla_cm": "130.00" }
```

La respuesta contiene `consulta` y `recomendacion`, con los alimentos y el plan generado por Groq. Si no existe una regla aplicable, no se crean registros. Consulta y recomendación se guardan juntas en una transacción. El servicio de IA conserva su comportamiento: si no puede generar el plan, devuelve el mensaje de error en `detalle_ia` y mantiene la recomendación base.

Seguimiento:

```json
{
  "fecha": "2026-10-14",
  "peso_kg": "26.00",
  "talla_cm": "130.00",
  "observaciones": "Control de seguimiento"
}
```

El paciente del seguimiento se obtiene de la ruta. Peso y talla deben ser positivos. Los clientes pueden enviar `Content-Type: application/json`; los formularios de la interfaz navegable también admiten `application/x-www-form-urlencoded` y `multipart/form-data`.

## Verificación

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Las pruebas usan una base de datos temporal y simulan Groq sin llamadas externas.
