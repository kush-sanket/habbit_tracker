"""
analytics_service.py — Dashboard analytics aggregation.
"""
from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from tracker.models import Branch, LoginLog, Streak, Task, User


def get_dashboard_analytics(user: User) -> dict:
    today = date.today()

    # ── Branch stats ──────────────────────────────────────────────────────────
    branches = Branch.objects.filter(user=user)
    total_branches = branches.count()

    # ── Task stats ────────────────────────────────────────────────────────────
    tasks = Task.objects.filter(branch__user=user)
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    missed_tasks = tasks.filter(status='missed').count()
    pending_tasks = tasks.filter(status='pending').count()
    completion_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks else 0.0

    # ── Today's tasks ─────────────────────────────────────────────────────────
    today_start = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.min.time())
    )
    today_end = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.max.time())
    )
    todays_tasks_qs = tasks.filter(due_date__gte=today_start, due_date__lte=today_end)
    todays_total = todays_tasks_qs.count()
    todays_completed = todays_tasks_qs.filter(status='completed').count()
    todays_pending = todays_tasks_qs.filter(status='pending').count()

    # ── Streak ────────────────────────────────────────────────────────────────
    streak_obj, _ = Streak.objects.get_or_create(user=user)
    current_streak = streak_obj.current_streak
    highest_streak = streak_obj.highest_streak
    last_active_date = streak_obj.last_active_date

    # ── 30-day activity calendar ──────────────────────────────────────────────
    thirty_days_ago = today - timedelta(days=29)
    # Build a dict: date_str -> {total, completed}
    daily_qs = (
        tasks.filter(
            due_date__date__gte=thirty_days_ago,
            due_date__date__lte=today,
        )
        .values('due_date__date', 'status')
        .annotate(cnt=Count('id'))
    )

    daily_map: dict[str, dict] = {}
    for row in daily_qs:
        ds = str(row['due_date__date'])
        if ds not in daily_map:
            daily_map[ds] = {'total': 0, 'completed': 0, 'missed': 0}
        daily_map[ds]['total'] += row['cnt']
        if row['status'] == 'completed':
            daily_map[ds]['completed'] += row['cnt']
        elif row['status'] == 'missed':
            daily_map[ds]['missed'] += row['cnt']

    calendar = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        ds = str(d)
        entry = daily_map.get(ds, {'total': 0, 'completed': 0, 'missed': 0})
        rate = round(entry['completed'] / entry['total'] * 100) if entry['total'] else 0
        calendar.append({
            'date': ds,
            'total': entry['total'],
            'completed': entry['completed'],
            'missed': entry['missed'],
            'rate': rate,
        })

    # ── Per-branch summary ────────────────────────────────────────────────────
    branch_summaries = []
    for b in branches.select_related('category'):
        branch_summaries.append({
            'id': b.pk,
            'name': b.name,
            'category': b.category.name if b.category else None,
            'category_icon': b.category.icon if b.category else '🌱',
            'category_color': b.category.color if b.category else '#4CAF50',
            'health_score': round(b.health_score * 100, 1),
            'streak': b.streak,
            'best_streak': b.best_streak,
            'total_tasks': b.total_tasks,
            'completed_tasks': b.completed_tasks,
        })

    # ── Daily creation limits (remaining) ────────────────────────────────────
    branches_created_today = branches.filter(created_at__date=today).count()
    tasks_created_today = tasks.filter(created_at__date=today).count()

    # ── Login calendar — all days from account creation to today ─────────────
    account_created = user.created_at.date()
    cal_start = account_created  # start from signup day
    login_dates = set(
        LoginLog.objects
        .filter(user=user, login_date__gte=cal_start, login_date__lte=today)
        .values_list('login_date', flat=True)
    )
    login_calendar = []
    delta_days = (today - cal_start).days + 1
    for i in range(delta_days):
        d = cal_start + timedelta(days=i)
        if d > today:
            status_val = 'future'
        elif d in login_dates:
            status_val = 'logged_in'
        else:
            status_val = 'missed'
        login_calendar.append({'date': str(d), 'status': status_val})

    # Login streak stats from the calendar
    login_streak_current = 0
    login_streak_highest = 0
    _run = 0
    for entry in login_calendar:
        if entry['status'] == 'logged_in':
            _run += 1
            login_streak_highest = max(login_streak_highest, _run)
        elif entry['status'] == 'missed':
            _run = 0
    # Current login streak: count backwards from today
    login_streak_current = 0
    for entry in reversed(login_calendar):
        if entry['status'] == 'logged_in':
            login_streak_current += 1
        elif entry['status'] == 'missed':
            break

    return {
        'overview': {
            'total_branches': total_branches,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'missed_tasks': missed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': completion_rate,
        },
        'today': {
            'total': todays_total,
            'completed': todays_completed,
            'pending': todays_pending,
            'date': str(today),
        },
        'streak': {
            'current': current_streak,
            'highest': highest_streak,
            'last_active_date': str(last_active_date) if last_active_date else None,
        },
        'calendar': calendar,
        'login_calendar': login_calendar,
        'login_streak': {
            'current': login_streak_current,
            'highest': login_streak_highest,
        },
        'branches': branch_summaries,
        'limits': {
            'branches_created_today': branches_created_today,
            'branches_remaining_today': max(0, 2 - branches_created_today),
            'tasks_created_today': tasks_created_today,
            'tasks_remaining_today': max(0, 10 - tasks_created_today),
        },
    }
