"""
category_views.py — List system categories.
"""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.models import Category
from tracker.serializers import CategorySerializer


@extend_schema(
    summary='List all system categories',
    tags=['Categories'],
    responses={200: CategorySerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    categories = Category.objects.all().order_by('id')
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)
