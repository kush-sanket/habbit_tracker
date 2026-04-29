"""
profile_views.py — Get/update profile, toggle privacy, public profile lookup.
"""
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from tracker.models import User
from tracker.serializers import PublicUserSerializer, TreeSerializer, UserSerializer
from tracker.services import auth_service
from tracker.services.tree_service import compute_tree


@extend_schema(
    summary='Get my profile',
    tags=['Profile'],
    responses={200: UserSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@extend_schema(
    summary='Toggle profile public / private',
    tags=['Profile'],
    request=None,
    responses={200: inline_serializer(
        name='PrivacyToggleResponse',
        fields={'is_public': serializers.BooleanField()},
    )},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_privacy(request):
    user = auth_service.toggle_privacy(request.user)
    return Response({'is_public': user.is_public})


@extend_schema(
    summary='View a public profile by user ID (no auth needed)',
    tags=['Profile'],
    auth=[],
    parameters=[
        OpenApiParameter('user_id', int, OpenApiParameter.PATH,
                         description='ID of the public user'),
    ],
    responses={200: inline_serializer(
        name='PublicProfileResponse',
        fields={
            'profile': PublicUserSerializer(),
            'tree': TreeSerializer(),
        },
    )},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def public_profile(request, user_id):
    user = get_object_or_404(User, pk=user_id, is_public=True)
    tree = compute_tree(user)
    return Response(
        {
            'profile': PublicUserSerializer(user).data,
            'tree': TreeSerializer(tree).data,
        }
    )
