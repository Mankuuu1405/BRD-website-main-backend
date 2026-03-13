import jwt
import datetime
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .serializers import (
    LoginSerializer, RegisterSerializer,
    UserSerializer, TokenPayloadSerializer
)

REDIRECT_MAP = {
    'master_admin':    'https://admin.brd.com',
    'tenant_admin':    'https://tenant.brd.com',
    'dashboard_admin': 'https://dash.brd.com',
    'borrower':        'https://app.brd.com',
}

DEV_REDIRECT_MAP = {
    'master_admin':    'http://localhost:3001',
    'tenant_admin':    'http://localhost:3002',
    'dashboard_admin': 'http://localhost:3003',
    'borrower':        'http://localhost:3004',
}


def sign_jwt(user: User) -> str:
    payload = {
        'sub':     str(user.id),
        'email':   user.email,
        'role':    user.role,
        'role_id': user.role_id,        # ← role_id instead of tenant_id
        'iat':     datetime.datetime.utcnow(),
        'exp':     datetime.datetime.utcnow() + datetime.timedelta(hours=8),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])


def _get_token(request):
    return (
        request.COOKIES.get('brd_token') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        None
    )


def _set_token_cookie(response, token: str):
    response.set_cookie(
        key      = 'brd_token',
        value    = token,
        max_age  = 8 * 60 * 60,
        httponly = True,
        secure   = not settings.DEBUG,
        samesite = 'Lax',
        domain   = None if settings.DEBUG else '.brd.com',
    )


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email    = serializer.validated_data['email'].lower()
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        token       = sign_jwt(user)
        redirect_map = DEV_REDIRECT_MAP if settings.DEBUG else REDIRECT_MAP
        destination  = redirect_map.get(user.role)

        if not destination:
            return Response(
                {'error': f'No portal configured for role: {user.role}'},
                status=status.HTTP_403_FORBIDDEN
            )

        accept     = request.headers.get('Accept', '')
        is_browser = 'text/html' in accept

        if is_browser:
            response = HttpResponseRedirect(destination)
            _set_token_cookie(response, token)
            return response
        else:
            response = Response({
                'token':        token,
                'redirect_url': destination,
                'user':         UserSerializer(user).data,
            }, status=status.HTTP_200_OK)
            _set_token_cookie(response, token)
            return response


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user  = serializer.save()
        token = sign_jwt(user)

        response = Response({
            'token': token,
            'user':  UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
        _set_token_cookie(response, token)
        return response


class VerifyTokenView(APIView):
    def get(self, request):
        token = _get_token(request)

        if not token:
            return Response({'error': 'No token provided'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = decode_jwt(token)
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenPayloadSerializer(data={
            'valid':   True,
            'sub':     payload['sub'],
            'email':   payload['email'],
            'role':    payload['role'],
            'role_id': payload['role_id'],
        })
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        response = Response({'message': 'Logged out successfully'})
        response.delete_cookie(
            'brd_token',
            domain=None if settings.DEBUG else '.brd.com'
        )
        return response