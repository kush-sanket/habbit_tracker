"""
branch_service.py — Branch creation and retrieval.
"""
from datetime import date

from rest_framework.exceptions import PermissionDenied

from tracker.models import Branch, Category, User

DAILY_BRANCH_LIMIT = 2


def create_branch(user: User, category_id: int, name: str, description: str = '') -> Branch:
    today = date.today()
    created_today = Branch.objects.filter(user=user, created_at__date=today).count()
    if created_today >= DAILY_BRANCH_LIMIT:
        raise PermissionDenied(
            f'Daily branch limit reached. You can only create {DAILY_BRANCH_LIMIT} branches per day.'
        )
    category = Category.objects.get(pk=category_id)
    return Branch.objects.create(
        user=user,
        category=category,
        name=name,
        description=description,
    )


def get_user_branches(user: User):
    return Branch.objects.filter(user=user).select_related('category').order_by('-created_at')


def get_branch_detail(user: User, branch_id: int) -> Branch:
    return Branch.objects.select_related('category').get(pk=branch_id, user=user)
