from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task, UserProfile, Category
from tasks.tasks import notify_user_about_due_task, notify_user_about_upcoming_task, send_telegram_notification


class Command(BaseCommand):
    help = 'Test notification system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['due', 'upcoming', 'daily', 'test'],
            default='test',
            help='Type of notification to test'
        )
        parser.add_argument(
            '--telegram-id',
            type=str,
            help='Telegram ID to send test notification'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        telegram_id = options['telegram_id']

        if notification_type == 'test':
            if telegram_id:
                # Отправляем тестовое уведомление
                message = """
🧪 <b>ТЕСТОВОЕ УВЕДОМЛЕНИЕ</b>

Это тестовое уведомление от системы ToDo Bot.

✅ Если вы видите это сообщение, система уведомлений работает корректно!
                """.strip()

                success = send_telegram_notification(telegram_id, message)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'Test notification sent to {telegram_id}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to send test notification to {telegram_id}')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR('Please provide --telegram-id for test notification')
                )

        elif notification_type == 'due':
            # Тестируем уведомления о просроченных задачах
            due_tasks = Task.objects.filter(
                due_date__lte=timezone.now(),
                is_completed=False
            ).select_related('user').prefetch_related('categories')

            self.stdout.write(f'Found {due_tasks.count()} overdue tasks')

            for task in due_tasks:
                success = notify_user_about_due_task(task)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'Due notification sent for task {task.id}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to send due notification for task {task.id}')
                    )

        elif notification_type == 'upcoming':
            # Тестируем уведомления о приближающихся дедлайнах
            upcoming_deadline = timezone.now() + timedelta(hours=1)
            upcoming_tasks = Task.objects.filter(
                due_date__gt=timezone.now(),
                due_date__lte=upcoming_deadline,
                is_completed=False
            ).select_related('user').prefetch_related('categories')

            self.stdout.write(f'Found {upcoming_tasks.count()} upcoming tasks')

            for task in upcoming_tasks:
                success = notify_user_about_upcoming_task(task)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'Upcoming notification sent for task {task.id}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to send upcoming notification for task {task.id}')
                    )

        elif notification_type == 'daily':
            # Тестируем ежедневные напоминания
            from tasks.tasks import send_daily_reminder
            send_daily_reminder.delay()
            self.stdout.write(
                self.style.SUCCESS('Daily reminder task queued')
            )
