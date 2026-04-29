"""
reroute_views.py — Reroute a missed task (once only).
"""
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.serializers import RerouteCreateSerializer, TaskRerouteSerializer
from tracker.services import reroute_service


@extend_schema(
    summary='Reroute a missed task (allowed once per task)',
    tags=['Reroute'],
    parameters=[
        OpenApiParameter('task_id', int, OpenApiParameter.PATH,
                         description='ID of the missed task to reroute'),
    ],
    request=RerouteCreateSerializer,
    responses={201: TaskRerouteSerializer},
    examples=[
        OpenApiExample(
            'Reroute example',
            value={
                'due_date': '2026-05-02T23:59:00Z',
                'reason': 'Was sick, rescheduling to next week',
                'title': 'Solve 2 LeetCode problems (rerouted)',
            },
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reroute_task(request, task_id):
    serializer = RerouteCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        reroute = reroute_service.reroute_task(
            user=request.user,
            task_id=task_id,
            due_date=data['due_date'],
            reason=data.get('reason', ''),
            title=data.get('title'),
        )
    except ObjectDoesNotExist:
        return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as exc:
        return Response({'detail': exc.detail}, status=status.HTTP_400_BAD_REQUEST)

    return Response(TaskRerouteSerializer(reroute).data, status=status.HTTP_201_CREATED)
