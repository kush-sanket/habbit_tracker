"""
streak_views.py — Retrieve user streak data.
"""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.serializers import StreakSerializer
from tracker.services.streak_service import get_or_create_streak


@extend_schema(
    summary='Get my current and highest streak',
    tags=['Streak'],
    request=None,
    responses={200: StreakSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_streak(request):
    streak = get_or_create_streak(request.user)
    serializer = StreakSerializer(streak)
    return Response(serializer.data)
