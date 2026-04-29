"""
tree_views.py — Return dynamically computed tree state.
"""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.serializers import TreeSerializer, TreeStateSerializer
from tracker.services.tree_service import compute_tree, compute_tree_state


@extend_schema(
    summary='Get my full tree state (leaves, branches, stem strength)',
    tags=['Tree'],
    request=None,
    responses={200: TreeSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tree(request):
    tree_data = compute_tree(request.user)
    serializer = TreeSerializer(tree_data)
    return Response(serializer.data)


@extend_schema(
    summary='Get full nested tree state — categories → branches → tasks (used by dashboard)',
    tags=['Tree'],
    request=None,
    responses={200: TreeStateSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tree_state(request):
    data = compute_tree_state(request.user)
    serializer = TreeStateSerializer(data)
    return Response(serializer.data)
