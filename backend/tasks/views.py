from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Task, Category, UserProfile
from .serializers import TaskSerializer, CategorySerializer, UserProfileSerializer
from django.contrib.auth.models import User
from django.utils import timezone


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_completed', 'user', 'categories']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        telegram_id = self.request.query_params.get('telegram_id')
        if telegram_id:
            return Task.objects.filter(user__telegram_id=telegram_id)
        return Task.objects.all()

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Отметить задачу как выполненную"""
        task = self.get_object()
        task.is_completed = True
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def uncomplete(self, request, pk=None):
        """Отметить задачу как невыполненную"""
        task = self.get_object()
        task.is_completed = False
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Получить просроченные задачи"""
        overdue_tasks = Task.objects.filter(
            due_date__lt=timezone.now(),
            is_completed=False
        )
        serializer = self.get_serializer(overdue_tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Получить выполненные задачи"""
        completed_tasks = Task.objects.filter(is_completed=True)
        serializer = self.get_serializer(completed_tasks, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Получить все задачи в категории"""
        category = self.get_object()
        tasks = category.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Удалить категорию (только если в ней нет задач)"""
        category = self.get_object()
        if category.tasks.exists():
            return Response(
                {'error': 'Cannot delete category with existing tasks'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['telegram_username', 'user__first_name', 'user__last_name']
    ordering_fields = ['telegram_username', 'user__first_name']
    ordering = ['telegram_username']

    def create(self, request, *args, **kwargs):
        telegram_id = request.data.get('telegram_id')
        telegram_username = request.data.get('telegram_username', f'tg_{telegram_id}')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        if not telegram_id:
            return Response({'error': 'telegram_id required'}, status=status.HTTP_400_BAD_REQUEST)
        # Проверяем, есть ли уже профиль
        profile = UserProfile.objects.filter(telegram_id=telegram_id).first()
        if profile:
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Создаём User
        user, _ = User.objects.get_or_create(
            username=f'tg_{telegram_id}',
            defaults={
                'email': f'{telegram_id}@tg.local',
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        # Создаём профиль
        profile = UserProfile.objects.create(
            user=user,
            telegram_id=telegram_id,
            telegram_username=telegram_username
        )
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Получить все задачи пользователя"""
        profile = self.get_object()
        tasks = profile.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Получить статистику пользователя"""
        profile = self.get_object()
        total_tasks = profile.tasks.count()
        completed_tasks = profile.tasks.filter(is_completed=True).count()
        overdue_tasks = profile.tasks.filter(
            due_date__lt=timezone.now(),
            is_completed=False
        ).count()

        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        })
