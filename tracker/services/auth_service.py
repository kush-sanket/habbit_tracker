"""
auth_service.py — Registration and profile management helpers.
"""
from django.db import transaction

from tracker.models import Streak, User


@transaction.atomic
def register_user(username: str, email: str, password: str) -> User:
    """Create a new User and seed their Streak record."""
    user = User.objects.create_user(username=username, email=email, password=password)
    Streak.objects.create(user=user)
    return user


def toggle_privacy(user: User) -> User:
    user.is_public = not user.is_public
    user.save(update_fields=['is_public'])
    return user
