"""
analytics_views.py — Dashboard analytics endpoint.
"""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.services.analytics_service import get_dashboard_analytics


@extend_schema(
    summary='Get dashboard analytics',
    tags=['Analytics'],
    request=None,
    responses={200: {}},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_analytics(request):
    data = get_dashboard_analytics(request.user)
    return Response(data)
