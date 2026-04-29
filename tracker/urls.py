from django.urls import path

from tracker.views.auth_views import login, logout, register
from tracker.views.branch_views import branch_detail, create_branch, list_branches
from tracker.views.category_views import list_categories
from tracker.views.leaderboard_views import leaderboard
from tracker.views.profile_views import get_profile, public_profile, toggle_privacy
from tracker.views.reroute_views import reroute_task
from tracker.views.streak_views import get_streak
from tracker.views.task_views import complete_task, create_task, list_tasks, miss_task, update_task
from tracker.views.tree_views import get_tree, tree_state

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('auth/register/', register, name='auth-register'),
    path('auth/login/', login, name='auth-login'),
    path('auth/logout/', logout, name='auth-logout'),

    # ── Profile ───────────────────────────────────────────────────────────────
    path('profile/', get_profile, name='profile'),
    path('profile/privacy/', toggle_privacy, name='profile-privacy'),
    path('profile/public/<int:user_id>/', public_profile, name='public-profile'),

    # ── Categories ────────────────────────────────────────────────────────────
    path('categories/', list_categories, name='category-list'),

    # ── Branches ──────────────────────────────────────────────────────────────
    path('branches/', list_branches, name='branch-list'),
    path('branches/create/', create_branch, name='branch-create'),
    path('branches/<int:branch_id>/', branch_detail, name='branch-detail'),

    # ── Tasks ─────────────────────────────────────────────────────────────────
    path('tasks/', list_tasks, name='task-list'),
    path('tasks/create/', create_task, name='task-create'),
    path('tasks/<int:task_id>/update/', update_task, name='task-update'),
    path('tasks/<int:task_id>/complete/', complete_task, name='task-complete'),
    path('tasks/<int:task_id>/miss/', miss_task, name='task-miss'),

    # ── Reroute ───────────────────────────────────────────────────────────────
    path('tasks/<int:task_id>/reroute/', reroute_task, name='task-reroute'),

    # ── Streak ────────────────────────────────────────────────────────────────
    path('streak/', get_streak, name='streak'),

    # ── Tree ──────────────────────────────────────────────────────────────────
    path('tree/', get_tree, name='tree'),
    path('tree-state/', tree_state, name='tree-state'),

    # ── Leaderboard ───────────────────────────────────────────────────────────
    path('leaderboard/', leaderboard, name='leaderboard'),
]
