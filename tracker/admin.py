from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Branch, Category, Streak, Task, TaskReroute, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_public', 'is_staff', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_public', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'streak', 'best_streak', 'health_score')
    list_filter = ('category',)
    raw_id_fields = ('user',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'branch', 'status', 'frequency', 'due_date', 'reroute_count')
    list_filter = ('status', 'frequency')
    raw_id_fields = ('branch', 'parent_task')


@admin.register(TaskReroute)
class TaskRerouteAdmin(admin.ModelAdmin):
    list_display = ('original_task', 'new_task', 'created_at')


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'highest_streak', 'last_active_date')

