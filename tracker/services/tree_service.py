"""
tree_service.py — Dynamically computes the user's tree state.
"""
from django.db.models import Count, Sum

from tracker.models import Branch, Category, Streak, Task, User


def _get_tree_stage(stem_strength: float) -> str:
    if stem_strength == 0:
        return 'seed'
    elif stem_strength < 20:
        return 'seedling'
    elif stem_strength < 60:
        return 'sapling'
    elif stem_strength < 120:
        return 'young_tree'
    return 'mature_tree'


def compute_tree(user: User) -> dict:
    branches = Branch.objects.filter(user=user).select_related('category')

    total_leaves = sum(b.completed_tasks for b in branches)
    total_branches = branches.count()

    active_category_ids = branches.values_list('category_id', flat=True).distinct()
    active_categories = len(set(active_category_ids))

    streak, _ = Streak.objects.get_or_create(user=user)
    highest_streak = streak.highest_streak
    current_streak = streak.current_streak

    stem_strength = round(
        (total_leaves * 0.6) + (active_categories * 5) + (highest_streak * 2),
        2,
    )

    distribution = {}
    for branch in branches:
        if branch.category_id is None:
            continue
        key = branch.category_id
        if key not in distribution:
            distribution[key] = {
                'category_id': key,
                'category_name': branch.category.name,
                'branch_count': 0,
                'completed_tasks': 0,
            }
        distribution[key]['branch_count'] += 1
        distribution[key]['completed_tasks'] += branch.completed_tasks

    return {
        'total_leaves': total_leaves,
        'total_branches': total_branches,
        'active_categories': active_categories,
        'stem_strength': stem_strength,
        'current_streak': current_streak,
        'highest_streak': highest_streak,
        'category_distribution': list(distribution.values()),
    }


def compute_tree_state(user: User) -> dict:
    """
    Full nested tree state for the frontend dashboard.
    Returns: user info, stats, categories → branches → tasks.
    """
    branches_qs = (
        Branch.objects
        .filter(user=user)
        .select_related('category')
        .prefetch_related('tasks')
        .order_by('category_id', 'created_at')
    )

    streak, _ = Streak.objects.get_or_create(user=user)

    total_leaves = sum(b.completed_tasks for b in branches_qs)
    total_branches = branches_qs.count()

    active_category_ids = set(b.category_id for b in branches_qs if b.category_id)
    active_categories_count = len(active_category_ids)

    stem_strength = round(
        (total_leaves * 0.6) + (active_categories_count * 5) + (streak.highest_streak * 2),
        2,
    )

    # Build categories dict preserving order
    categories_map = {}
    for branch in branches_qs:
        if branch.category_id is None:
            continue
        cat_id = branch.category_id
        if cat_id not in categories_map:
            categories_map[cat_id] = {
                'id': cat_id,
                'name': branch.category.name,
                'icon': branch.category.icon,
                'color': branch.category.color,
                'branches': [],
            }
        categories_map[cat_id]['branches'].append(branch)

    return {
        'user': user,
        'stats': {
            'total_leaves': total_leaves,
            'total_branches': total_branches,
            'active_categories': active_categories_count,
            'stem_strength': stem_strength,
            'tree_stage': _get_tree_stage(stem_strength),
            'current_streak': streak.current_streak,
            'highest_streak': streak.highest_streak,
            'last_active_date': streak.last_active_date,
        },
        'categories': list(categories_map.values()),
    }
    branches = Branch.objects.filter(user=user).select_related('category')

    total_leaves = sum(b.completed_tasks for b in branches)
    total_branches = branches.count()

    # Active categories = categories that have at least one branch
    active_category_ids = branches.values_list('category_id', flat=True).distinct()
    active_categories = len(set(active_category_ids))

    # Streak data
    streak, _ = Streak.objects.get_or_create(user=user)
    highest_streak = streak.highest_streak
    current_streak = streak.current_streak

    # Stem strength formula
    stem_strength = round(
        (total_leaves * 0.6) + (active_categories * 5) + (highest_streak * 2),
        2,
    )

    # Category distribution
    distribution = {}
    for branch in branches:
        if branch.category_id is None:
            continue
        key = branch.category_id
        if key not in distribution:
            distribution[key] = {
                'category_id': key,
                'category_name': branch.category.name,
                'branch_count': 0,
                'completed_tasks': 0,
            }
        distribution[key]['branch_count'] += 1
        distribution[key]['completed_tasks'] += branch.completed_tasks

    return {
        'total_leaves': total_leaves,
        'total_branches': total_branches,
        'active_categories': active_categories,
        'stem_strength': stem_strength,
        'current_streak': current_streak,
        'highest_streak': highest_streak,
        'category_distribution': list(distribution.values()),
    }
