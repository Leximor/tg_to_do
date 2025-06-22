from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import TaskViewSet, CategoryViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]
