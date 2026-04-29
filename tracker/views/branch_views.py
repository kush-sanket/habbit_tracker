"""
branch_views.py — Create, list, and detail branches.
"""
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.serializers import BranchCreateSerializer, BranchSerializer
from tracker.services import branch_service


@extend_schema(
    summary='Create a new branch (goal)',
    tags=['Branches'],
    request=BranchCreateSerializer,
    responses={201: BranchSerializer},
    examples=[
        OpenApiExample(
            'Example',
            value={'category': 1, 'name': 'Learn DSA', 'description': 'Master data structures'},
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_branch(request):
    serializer = BranchCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        branch = branch_service.create_branch(
            user=request.user,
            category_id=data['category'].pk,
            name=data['name'],
            description=data.get('description', ''),
        )
    except ObjectDoesNotExist:
        return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(BranchSerializer(branch).data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='List all my branches',
    tags=['Branches'],
    responses={200: BranchSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_branches(request):
    branches = branch_service.get_user_branches(request.user)
    serializer = BranchSerializer(branches, many=True)
    return Response(serializer.data)


@extend_schema(
    summary='Get a single branch by ID',
    tags=['Branches'],
    parameters=[
        OpenApiParameter('branch_id', int, OpenApiParameter.PATH, description='Branch ID'),
    ],
    responses={200: BranchSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def branch_detail(request, branch_id):
    try:
        branch = branch_service.get_branch_detail(request.user, branch_id)
    except ObjectDoesNotExist:
        return Response({'detail': 'Branch not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(BranchSerializer(branch).data)
