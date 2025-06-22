from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Category, UserProfile
from datetime import datetime
from django.utils import timezone
import pytz

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CategorySerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'task_count']

    def get_task_count(self, obj):
        return obj.tasks.count()

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'telegram_id', 'telegram_username', 'task_count']

    def get_task_count(self, obj):
        return obj.tasks.count()

class TaskSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all())
    category_names = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'created_at', 'due_date',
            'user', 'categories', 'is_completed', 'category_names',
            'user_info', 'is_overdue', 'notifications_disabled'
        ]

    def to_internal_value(self, data):
        value = data.get('due_date')
        # Формат: 'YYYY-MM-DD HH:MM'   :
        if value and isinstance(value, str) and len(value) == 16:
            local_tz = pytz.timezone('America/Adak')
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M')
            aware_dt = local_tz.localize(dt)
            data['due_date'] = aware_dt.isoformat()
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Всегда возвращаем due_date в формате 'YYYY-MM-DD HH:MM'
        if instance.due_date:
            rep['due_date'] = instance.due_date.astimezone(pytz.timezone('America/Adak')).strftime('%Y-%m-%d %H:%M')
        return rep

    def get_category_names(self, obj):
        return [cat.name for cat in obj.categories.all()]

    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'telegram_id': obj.user.telegram_id,
            'telegram_username': obj.user.telegram_username
        }

    def get_is_overdue(self, obj):
        return not obj.is_completed and obj.due_date < timezone.now()
