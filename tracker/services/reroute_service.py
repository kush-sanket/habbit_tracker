"""
reroute_service.py — Reroute logic (one reroute per task, max).
"""
from datetime import datetime

from django.db import transaction
from rest_framework.exceptions import ValidationError

from tracker.models import Task, TaskReroute, User


@transaction.atomic
def reroute_task(user: User, task_id: int, due_date: datetime, reason: str = '', title: str = None) -> TaskReroute:
    """
    Reroutes a missed task by creating a new linked task.
    Only allowed if reroute_count == 0.
    """
    original = Task.objects.select_related('branch').get(pk=task_id, branch__user=user)

    if original.status != 'missed':
        raise ValidationError('Only missed tasks can be rerouted.')

    if original.reroute_count >= 1:
        raise ValidationError('This task has already been rerouted once.')

    new_title = title or original.title
    new_task = Task.objects.create(
        branch=original.branch,
        title=new_title,
        frequency=original.frequency,
        due_date=due_date,
        is_rerouted=True,
        parent_task=original,
        reroute_count=0,
    )

    original.reroute_count = 1
    original.save(update_fields=['reroute_count'])

    reroute_record = TaskReroute.objects.create(
        original_task=original,
        new_task=new_task,
        reason=reason,
    )

    # Rerouted task counts toward total_tasks on the branch
    branch = original.branch
    branch.total_tasks += 1
    branch.recalculate_health()

    return reroute_record
