"""
auth_views.py — Register, Login (JWT), Logout.
"""
from django.contrib.auth import authenticate
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from tracker.models import LoginLog
from tracker.serializers import RegisterSerializer, UserSerializer
from tracker.services import auth_service

_TokenResponseSerializer = inline_serializer(
    name='TokenResponse',
    fields={
        'user': UserSerializer(),
        'access': serializers.CharField(help_text='Short-lived JWT access token'),
        'refresh': serializers.CharField(help_text='Long-lived JWT refresh token'),
    },
)


@extend_schema(
    summary='Register a new user',
    tags=['Auth'],
    auth=[],
    request=RegisterSerializer,
    responses={201: _TokenResponseSerializer},
    examples=[
        OpenApiExample(
            'Example',
            value={'username': 'john', 'email': 'john@example.com',
                   'password': 'StrongPass1!', 'password2': 'StrongPass1!'},
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = auth_service.register_user(
        username=serializer.validated_data['username'],
        email=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
    )
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    summary='Login — obtain JWT tokens',
    tags=['Auth'],
    auth=[],
    request=inline_serializer(
        name='LoginRequest',
        fields={
            'email': serializers.EmailField(),
            'password': serializers.CharField(),
        },
    ),
    responses={200: _TokenResponseSerializer},
    examples=[
        OpenApiExample(
            'Example',
            value={'email': 'john@example.com', 'password': 'StrongPass1!'},
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'detail': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Record today as a login day (idempotent — unique_together prevents duplicates)
    from django.utils import timezone
    LoginLog.objects.get_or_create(user=user, login_date=timezone.now().date())

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    )


@extend_schema(
    summary='Logout — blacklist the refresh token',
    tags=['Auth'],
    request=inline_serializer(
        name='LogoutRequest',
        fields={'refresh': serializers.CharField(help_text='The refresh token to blacklist')},
    ),
    responses={200: inline_serializer(
        name='LogoutResponse',
        fields={'detail': serializers.CharField()},
    )},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
