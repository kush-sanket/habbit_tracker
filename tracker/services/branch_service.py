"""
branch_service.py — Branch creation and retrieval.
"""
from tracker.models import Branch, Category, User


def create_branch(user: User, category_id: int, name: str, description: str = '') -> Branch:
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
