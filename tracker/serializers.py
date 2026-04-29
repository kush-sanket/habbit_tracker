from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Branch, Category, Streak, Task, TaskReroute, User


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_public', 'created_at')
        read_only_fields = ('id', 'created_at')


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_public', 'created_at')


# ─── Category ─────────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'icon', 'color')


# ─── Branch ───────────────────────────────────────────────────────────────────

class BranchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ('id', 'category', 'name', 'description')

    def validate_category(self, value):
        if not Category.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError('Category does not exist.')
        return value


class BranchSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Branch
        fields = (
            'id', 'category', 'name', 'description',
            'total_tasks', 'completed_tasks', 'streak',
            'best_streak', 'health_score', 'created_at',
        )
        read_only_fields = (
            'id', 'total_tasks', 'completed_tasks', 'streak',
            'best_streak', 'health_score', 'created_at',
        )


# ─── Task ─────────────────────────────────────────────────────────────────────

class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'branch', 'title', 'frequency', 'due_date')

    def validate_branch(self, value):
        request = self.context.get('request')
        if request and value.user != request.user:
            raise serializers.ValidationError('Branch does not belong to you.')
        return value


class TaskSerializer(serializers.ModelSerializer):
    parent_task_id = serializers.PrimaryKeyRelatedField(
        source='parent_task', read_only=True
    )

    class Meta:
        model = Task
        fields = (
            'id', 'branch', 'title', 'frequency', 'status',
            'due_date', 'completed_at', 'is_rerouted',
            'parent_task_id', 'reroute_count', 'created_at',
        )
        read_only_fields = (
            'id', 'status', 'completed_at', 'is_rerouted',
            'parent_task_id', 'reroute_count', 'created_at',
        )


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'frequency', 'due_date')


# ─── TaskReroute ──────────────────────────────────────────────────────────────

class RerouteCreateSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='')
    due_date = serializers.DateTimeField()
    title = serializers.CharField(max_length=200, required=False)


class TaskRerouteSerializer(serializers.ModelSerializer):
    original_task = TaskSerializer(read_only=True)
    new_task = TaskSerializer(read_only=True)

    class Meta:
        model = TaskReroute
        fields = ('id', 'original_task', 'new_task', 'reason', 'created_at')


# ─── Streak ───────────────────────────────────────────────────────────────────

class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = ('current_streak', 'highest_streak', 'last_active_date')


# ─── Tree (computed, no model) ────────────────────────────────────────────────

class CategoryDistributionSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    branch_count = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()


class TreeSerializer(serializers.Serializer):
    total_leaves = serializers.IntegerField()
    total_branches = serializers.IntegerField()
    active_categories = serializers.IntegerField()
    stem_strength = serializers.FloatField()
    current_streak = serializers.IntegerField()
    highest_streak = serializers.IntegerField()
    category_distribution = CategoryDistributionSerializer(many=True)


# ─── Leaderboard ──────────────────────────────────────────────────────────────

class LeaderboardEntrySerializer(serializers.Serializer):
    rank             = serializers.IntegerField()
    user_id          = serializers.IntegerField()
    username         = serializers.CharField()
    total_completed  = serializers.IntegerField()
    total_tasks      = serializers.IntegerField()
    highest_streak   = serializers.IntegerField()
    current_streak   = serializers.IntegerField()
    branch_count     = serializers.IntegerField()
    score            = serializers.FloatField()


# ─── Tree State (full nested, used by frontend dashboard) ─────────────────────

class TaskInTreeSerializer(serializers.ModelSerializer):
    parent_task_id = serializers.PrimaryKeyRelatedField(source='parent_task', read_only=True)

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'frequency', 'status',
            'due_date', 'completed_at', 'is_rerouted',
            'parent_task_id', 'reroute_count', 'created_at',
        )


class BranchInTreeSerializer(serializers.ModelSerializer):
    tasks = TaskInTreeSerializer(many=True, read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = Branch
        fields = (
            'id', 'name', 'description',
            'category_id', 'category_name', 'category_icon', 'category_color',
            'total_tasks', 'completed_tasks', 'streak',
            'best_streak', 'health_score', 'created_at',
            'tasks',
        )


class CategoryInTreeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    icon = serializers.CharField()
    color = serializers.CharField()
    branches = BranchInTreeSerializer(many=True)


class TreeStatsSerializer(serializers.Serializer):
    total_leaves = serializers.IntegerField()
    total_branches = serializers.IntegerField()
    active_categories = serializers.IntegerField()
    stem_strength = serializers.FloatField()
    tree_stage = serializers.CharField()
    current_streak = serializers.IntegerField()
    highest_streak = serializers.IntegerField()
    last_active_date = serializers.DateField(allow_null=True)


class TreeStateSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    stats = TreeStatsSerializer()
    categories = CategoryInTreeSerializer(many=True)

    def get_user(self, obj):
        u = obj['user']
        return {'id': u.id, 'username': u.username, 'email': u.email, 'is_public': u.is_public}
