"""
task_views.py — Create, update, complete, miss tasks (with pagination).
"""
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tracker.serializers import TaskCreateSerializer, TaskSerializer, TaskUpdateSerializer
from tracker.services import task_service


class TaskPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(
    summary='Create a new task',
    tags=['Tasks'],
    request=TaskCreateSerializer,
    responses={201: TaskSerializer},
    examples=[
        OpenApiExample(
            'Daily task example',
            value={
                'branch': 1,
                'title': 'Solve 2 LeetCode problems',
                'frequency': 'daily',
                'due_date': '2026-04-30T23:59:00Z',
            },
            request_only=True,
        )
    ],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task(request):
    serializer = TaskCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        task = task_service.create_task(
            user=request.user,
            branch_id=data['branch'].pk,
            title=data['title'],
            frequency=data['frequency'],
            due_date=data['due_date'],
        )
    except ObjectDoesNotExist:
        return Response({'detail': 'Branch not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='List my tasks (paginated)',
    tags=['Tasks'],
    parameters=[
        OpenApiParameter(
            'branch_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Filter by branch ID',
        ),
        OpenApiParameter(
            'status', OpenApiTypes.STR, OpenApiParameter.QUERY,
            required=False, description='Filter by status',
            enum=['pending', 'completed', 'missed'],
        ),
        OpenApiParameter(
            'page', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Page number',
        ),
        OpenApiParameter(
            'page_size', OpenApiTypes.INT, OpenApiParameter.QUERY,
            required=False, description='Results per page (max 100)',
        ),
    ],
    responses={200: TaskSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tasks(request):
    branch_id = request.query_params.get('branch_id')
    task_status = request.query_params.get('status')
    tasks = task_service.get_user_tasks(request.user, branch_id=branch_id, status=task_status)

    paginator = TaskPagination()
    page = paginator.paginate_queryset(tasks, request)
    serializer = TaskSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(
    summary='Update a task (title / frequency / due_date)',
    tags=['Tasks'],
    parameters=[
        OpenApiParameter('task_id', int, OpenApiParameter.PATH, description='Task ID'),
    ],
    request=TaskUpdateSerializer,
    responses={200: TaskSerializer},
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_task(request, task_id):
    serializer = TaskUpdateSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    try:
        task = task_service.update_task(request.user, task_id, **serializer.validated_data)
    except ObjectDoesNotExist:
        return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(TaskSerializer(task).data)


@extend_schema(
    summary='Mark a task as completed',
    tags=['Tasks'],
    parameters=[
        OpenApiParameter('task_id', int, OpenApiParameter.PATH, description='Task ID'),
    ],
    request=None,
    responses={200: TaskSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task(request, task_id):
    try:
        task = task_service.complete_task(request.user, task_id)
    except ObjectDoesNotExist:
        return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(TaskSerializer(task).data)


@extend_schema(
    summary='Mark a task as missed',
    tags=['Tasks'],
    parameters=[
        OpenApiParameter('task_id', int, OpenApiParameter.PATH, description='Task ID'),
    ],
    request=None,
    responses={200: TaskSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def miss_task(request, task_id):
    try:
        task = task_service.miss_task(request.user, task_id)
    except ObjectDoesNotExist:
        return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(TaskSerializer(task).data)
