from django.db import models
from django.contrib.auth.models import User
import hashlib
import time


class Category(models.Model):
    # PK: hash от имени категории и времени создания
    id = models.CharField(primary_key=True, max_length=32, editable=False)
    name = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if not self.id:
            raw = f'{self.name}{time.time()}'
            self.id = hashlib.md5(raw.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    # PK: hash от username/email и времени создания
    id = models.CharField(primary_key=True, max_length=32, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            raw = f'{self.user.username}{self.user.email}{time.time()}'
            self.id = hashlib.md5(raw.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

class Task(models.Model):
    # PK: hash от заголовка, пользователя и времени создания
    id = models.CharField(primary_key=True, max_length=32, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='tasks')
    categories = models.ManyToManyField(Category, related_name='tasks')
    is_completed = models.BooleanField(default=False)
    notifications_disabled = models.BooleanField(default=False, help_text="Отключить уведомления для этой задачи")

    def save(self, *args, **kwargs):
        if not self.id:
            raw = f'{self.title}{self.user.id}{time.time()}'
            self.id = hashlib.md5(raw.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
