"""
leaderboard_views.py — Public leaderboard with sortable ranking.

Sort options (query param ?sort=):
  score          — composite score (default, highest first)
  completed      — total completed tasks (highest first)
  total_tasks    — total tasks created (highest first)
  streak         — highest streak (highest first)
  completed_asc  — total completed tasks (lowest first)
  total_asc      — total tasks created (lowest first)
  streak_asc     — highest streak (lowest first)
  score_asc      — score (lowest first)
"""
from django.db.models import Count, Sum, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from tracker.models import Branch, Streak, User
from tracker.serializers import LeaderboardEntrySerializer

VALID_SORTS = {
    'score':         ('score',           True),
    'completed':     ('total_completed', True),
    'total_tasks':   ('total_tasks',     True),
    'streak':        ('highest_streak',  True),
    'completed_asc': ('total_completed', False),
    'total_asc':     ('total_tasks',     False),
    'streak_asc':    ('highest_streak',  False),
    'score_asc':     ('score',           False),
}


@extend_schema(
    summary='Public leaderboard',
    tags=['Leaderboard'],
    auth=[],
    parameters=[
        OpenApiParameter(
            'sort', str, OpenApiParameter.QUERY,
            description='Sort key. One of: score, completed, total_tasks, streak, '
                        'completed_asc, total_asc, streak_asc, score_asc',
            required=False,
            default='score',
        ),
        OpenApiParameter(
            'limit', int, OpenApiParameter.QUERY,
            description='Max entries to return (default 50, max 100)',
            required=False,
        ),
    ],
    responses={200: LeaderboardEntrySerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard(request):
    sort_key = request.query_params.get('sort', 'score')
    if sort_key not in VALID_SORTS:
        sort_key = 'score'

    try:
        limit = min(int(request.query_params.get('limit', 50)), 100)
    except (ValueError, TypeError):
        limit = 50

    # Only public accounts appear on the leaderboard
    public_users = User.objects.filter(is_public=True, is_active=True)

    # Aggregate branch stats per user
    branch_agg = (
        Branch.objects
        .filter(user__is_public=True, user__is_active=True)
        .values('user_id')
        .annotate(
            total=Sum('total_tasks'),
            completed=Sum('completed_tasks'),
            branches=Count('id'),
        )
    )
    branch_map = {row['user_id']: row for row in branch_agg}

    # Streak per user
    streak_map = {
        s.user_id: s
        for s in Streak.objects.filter(user__is_public=True, user__is_active=True)
    }

    entries = []
    for user in public_users:
        agg    = branch_map.get(user.id, {'total': 0, 'completed': 0, 'branches': 0})
        streak = streak_map.get(user.id)
        total_completed = agg['completed'] or 0
        total_tasks     = agg['total']     or 0
        branch_count    = agg['branches']  or 0
        highest_streak  = streak.highest_streak  if streak else 0
        current_streak  = streak.current_streak  if streak else 0

        # Composite score: weighted sum
        score = round(
            total_completed * 3
            + highest_streak * 5
            + current_streak * 2
            + branch_count   * 4,
            2,
        )

        entries.append({
            'user_id':         user.id,
            'username':        user.username,
            'total_completed': total_completed,
            'total_tasks':     total_tasks,
            'highest_streak':  highest_streak,
            'current_streak':  current_streak,
            'branch_count':    branch_count,
            'score':           score,
        })

    # Sort
    field, descending = VALID_SORTS[sort_key]
    entries.sort(key=lambda e: e[field], reverse=descending)
    entries = entries[:limit]

    # Assign ranks after sorting
    for i, entry in enumerate(entries, start=1):
        entry['rank'] = i

    serializer = LeaderboardEntrySerializer(entries, many=True)
    return Response(serializer.data)
