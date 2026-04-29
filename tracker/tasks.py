"""
tasks.py — Celery periodic tasks for the tracker app.

Schedule (set up via django-celery-beat or crontab):
  - process_overdue_tasks: runs daily at 00:05 UTC
"""
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, name='tracker.process_overdue_tasks')
def process_overdue_tasks(self):
    """
    1. Mark all pending tasks whose due_date has passed as 'missed'.
    2. For each newly-missed task that was a rerouted task, apply penalty.
    3. Check each user's streak — if last_active_date is more than 1 day
       ago, reset their current streak to 0.
    """
    from tracker.models import Streak, Task, User
    from tracker.services import streak_service
    from tracker.services.task_service import miss_task as service_miss_task

    now = timezone.now()

    # ── Step 1 & 2: expire overdue tasks ──────────────────────────────────────
    overdue = Task.objects.filter(status='pending', due_date__lt=now).select_related(
        'branch__user'
    )

    processed = 0
    for task in overdue:
        try:
            service_miss_task(task.branch.user, task.pk)
            processed += 1
        except Exception:
            pass  # log in production

    # ── Step 3: reset stale streaks ───────────────────────────────────────────
    from datetime import date, timedelta

    yesterday = date.today() - timedelta(days=1)
    stale_streaks = Streak.objects.filter(
        current_streak__gt=0,
        last_active_date__lt=yesterday,
    )
    reset_count = stale_streaks.update(current_streak=0)

    return {
        'tasks_marked_missed': processed,
        'streaks_reset': reset_count,
    }
