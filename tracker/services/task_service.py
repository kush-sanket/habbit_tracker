"""
task_service.py — Task CRUD and state transitions.
"""
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from tracker.models import Branch, Task, User
from tracker.services import streak_service


def create_task(user: User, branch_id: int, title: str, frequency: str, due_date: datetime) -> Task:
    branch = Branch.objects.get(pk=branch_id, user=user)
    task = Task.objects.create(
        branch=branch,
        title=title,
        frequency=frequency,
        due_date=due_date,
    )
    branch.total_tasks += 1
    branch.recalculate_health()
    return task


def update_task(user: User, task_id: int, **fields) -> Task:
    task = Task.objects.select_related('branch').get(pk=task_id, branch__user=user)
    allowed = {'title', 'frequency', 'due_date'}
    for key, value in fields.items():
        if key in allowed:
            setattr(task, key, value)
    task.save()
    return task


@transaction.atomic
def complete_task(user: User, task_id: int) -> Task:
    task = Task.objects.select_related('branch').get(pk=task_id, branch__user=user)

    if task.status == 'completed':
        return task  # idempotent

    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at'])

    branch = task.branch
    branch.completed_tasks += 1
    branch.streak += 1
    if branch.streak > branch.best_streak:
        branch.best_streak = branch.streak
    branch.recalculate_health()

    streak_service.record_activity(user)
    return task


@transaction.atomic
def miss_task(user: User, task_id: int) -> Task:
    """
    Mark a task as missed. If it's a rerouted task, apply the full penalty.
    If it's an original task, simply mark missed (reroute still available).
    """
    task = Task.objects.select_related('branch').get(pk=task_id, branch__user=user)

    if task.status == 'missed':
        return task

    task.status = 'missed'
    task.save(update_fields=['status'])

    branch = task.branch
    is_rerouted_task = task.is_rerouted  # this task was itself the rerouted replacement

    if is_rerouted_task:
        # Second failure — apply full penalty
        branch.streak = 0
        branch.health_score = max(0.0, round(branch.health_score - 0.1, 4))
        branch.save(update_fields=['streak', 'health_score'])
        streak_service.reset_streak(user)
    else:
        # First miss — reset branch streak but no broader penalty yet
        branch.streak = 0
        branch.save(update_fields=['streak'])

    return task


def get_user_tasks(user: User, branch_id: int = None, status: str = None):
    qs = Task.objects.filter(branch__user=user).select_related('branch')
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-created_at')
