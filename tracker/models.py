from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        indexes = [models.Index(fields=['username'])]

    def __str__(self):
        return self.email


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='🌱')
    color = models.CharField(max_length=20, default='#4CAF50')

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Branch(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='branches', db_index=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name='branches'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    health_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'branches'
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f'{self.name} ({self.user.username})'

    def recalculate_health(self):
        if self.total_tasks > 0:
            self.health_score = round(self.completed_tasks / self.total_tasks, 4)
        else:
            self.health_score = 0.0
        self.save(update_fields=['health_score'])


class Task(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ]

    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='tasks', db_index=True
    )
    title = models.CharField(max_length=200)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_rerouted = models.BooleanField(default=False)
    parent_task = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rerouted_tasks',
    )
    reroute_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tasks'
        indexes = [
            models.Index(fields=['branch']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.title} [{self.status}]'


class TaskReroute(models.Model):
    original_task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='reroute_records'
    )
    new_task = models.OneToOneField(
        Task, on_delete=models.CASCADE, related_name='reroute_source'
    )
    reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_reroutes'

    def __str__(self):
        return f'Reroute: {self.original_task_id} → {self.new_task_id}'


class Streak(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='streak', db_index=True
    )
    current_streak = models.PositiveIntegerField(default=0)
    highest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'streaks'

    def __str__(self):
        return f'{self.user.username}: {self.current_streak} days'


class LoginLog(models.Model):
    """Records each unique calendar day a user logs in."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='login_logs', db_index=True
    )
    login_date = models.DateField(db_index=True)

    class Meta:
        db_table = 'login_logs'
        unique_together = ('user', 'login_date')

    def __str__(self):
        return f'{self.user.username} logged in on {self.login_date}'
