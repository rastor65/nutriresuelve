from django.contrib.auth import login, logout
from django.db.models import Count
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pacientes.models import Paciente
from apps.pacientes.serializers import PacienteSerializer
from apps.recomendaciones.models import Recomendacion
from apps.valoracion.models import Consulta
from .serializers import LoginSerializer


class DashboardAPIView(APIView):
    def get(self, request):
        imcs = [p.imc for p in Paciente.objects.filter(peso_kg__gt=0, talla_cm__gt=0)]
        return Response({
            'total_pacientes': Paciente.objects.count(),
            'total_consultas': Consulta.objects.count(),
            'total_recomendaciones': Recomendacion.objects.count(),
            'ultimos_pacientes': PacienteSerializer(
                Paciente.objects.order_by('-fecha_registro')[:5], many=True
            ).data,
            'desnutricion_severa': sum(imc < 16 for imc in imcs),
            'desnutricion_moderada': sum(16 <= imc < 18.5 for imc in imcs),
            'normal': sum(18.5 <= imc <= 24.9 for imc in imcs),
            'sobrepeso': sum(imc > 24.9 for imc in imcs),
            'institucion_top': Paciente.objects.values('institucion').annotate(
                total=Count('id')
            ).order_by('-total').first(),
        })


@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def get(self, request):
        return Response({'csrfToken': get_token(request)})

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({
            'id': user.pk,
            'username': user.get_username(),
            'csrfToken': get_token(request),
        })


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionAPIView(APIView):
    def get(self, request):
        return Response({'id': request.user.pk, 'username': request.user.get_username()})


# Django invokes error handlers outside APIView.
def error_404(request, exception):
    return JsonResponse({'detail': 'Ruta no encontrada.'}, status=404)


def error_500(request):
    return JsonResponse({'detail': 'Error interno del servidor.'}, status=500)


def error_400(request, exception):
    return JsonResponse({'detail': 'Solicitud incorrecta.'}, status=400)


def error_403(request, exception):
    return JsonResponse({'detail': 'No tienes permiso para esta solicitud.'}, status=403)


def csrf_failure(request, reason=''):
    return JsonResponse({'detail': 'Token CSRF ausente o incorrecto.'}, status=403)
