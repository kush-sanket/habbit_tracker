"""
streak_service.py — User streak management.
"""
from datetime import date, timedelta

from django.db import transaction

from tracker.models import Streak, User


def get_or_create_streak(user: User) -> Streak:
    streak, _ = Streak.objects.get_or_create(user=user)
    return streak


@transaction.atomic
def record_activity(user: User, activity_date: date = None) -> Streak:
    """
    Call this after a task is completed.
    Extends streak if consecutive, resets otherwise.
    """
    today = activity_date or date.today()
    streak = get_or_create_streak(user)

    if streak.last_active_date is None:
        streak.current_streak = 1
    elif streak.last_active_date == today:
        # Already recorded today — no change
        return streak
    elif streak.last_active_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        # Gap detected — reset
        streak.current_streak = 1

    if streak.current_streak > streak.highest_streak:
        streak.highest_streak = streak.current_streak

    streak.last_active_date = today
    streak.save(update_fields=['current_streak', 'highest_streak', 'last_active_date'])
    return streak


@transaction.atomic
def reset_streak(user: User) -> Streak:
    streak = get_or_create_streak(user)
    streak.current_streak = 0
    streak.save(update_fields=['current_streak'])
    return streak
