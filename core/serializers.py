from django.contrib.auth import authenticate
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, style={'input_type': 'password'},
    )

    def validate(self, attrs):
        user = authenticate(request=self.context['request'], **attrs)
        if user is None:
            raise serializers.ValidationError('Credenciales incorrectas.')
        return {'user': user}
