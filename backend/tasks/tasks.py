from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import requests
import logging
import pytz

logger = logging.getLogger(__name__)

def send_telegram_notification(telegram_id, message, inline_keyboard=None):
    """Отправка уведомления в Telegram"""
    try:
        bot_token = getattr(settings, 'BOT_TOKEN', None)
        if not bot_token:
            logger.error("BOT_TOKEN not configured in settings")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': telegram_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        if inline_keyboard:
            data['reply_markup'] = {
                'inline_keyboard': inline_keyboard
            }

        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram notification sent to {telegram_id}")
            return True
        else:
            logger.error(f"Failed to send Telegram notification: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        return False

def notify_user_about_due_task(task):
    """Уведомление пользователя о просроченной задаче"""
    try:
        if not task.user or not task.user.telegram_id:
            logger.warning(f"Task {task.id} has no user or telegram_id")
            return False
        # Конвертируем в локальное время America/Adak
        local_tz = pytz.timezone('America/Adak')
        due_date_local = task.due_date.astimezone(local_tz)
        due_date_str = due_date_local.strftime('%Y-%m-%d %H:%M')
        now = timezone.now()
        overdue_duration = now - task.due_date
        hours = int(overdue_duration.total_seconds() // 3600)
        minutes = int((overdue_duration.total_seconds() % 3600) // 60)
        if hours > 0:
            overdue_text = f"{hours}ч {minutes}м"
        else:
            overdue_text = f"{minutes}м"
        message = f"""
🚨 <b>ПРОСРОЧЕННАЯ ЗАДАЧА!</b>

📋 <b>{task.title}</b>
📝 Описание: {task.description or 'Не указано'}
📅 Дедлайн: {due_date_str}
🏷️ Категории: {', '.join([cat.name for cat in task.categories.all()]) or 'Не указаны'}

⏰ Задача просрочена на {overdue_text}
        """.strip()
        inline_keyboard = [[
            {
                'text': '🔕 Не оповещать',
                'callback_data': f'disable_notifications:{task.id}'
            }
        ]]
        return send_telegram_notification(task.user.telegram_id, message, inline_keyboard)
    except Exception as e:
        logger.error(f"Error notifying user about task {task.id}: {e}")
        return False

def notify_user_about_upcoming_task(task):
    """Уведомление пользователя о приближающемся дедлайне"""
    try:
        if not task.user or not task.user.telegram_id:
            logger.warning(f"Task {task.id} has no user or telegram_id")
            return False
        # Конвертируем в локальное время America/Adak
        local_tz = pytz.timezone('America/Adak')
        due_date_local = task.due_date.astimezone(local_tz)
        due_date_str = due_date_local.strftime('%Y-%m-%d %H:%M')
        time_until_due = task.due_date - timezone.now()
        hours_until_due = time_until_due.total_seconds() / 3600
        if hours_until_due <= 1:
            time_text = "менее часа"
        elif hours_until_due <= 24:
            time_text = f"{int(hours_until_due)} часов"
        else:
            days = int(hours_until_due / 24)
            time_text = f"{days} дней"
        message = f"""
⚠️ <b>НАПОМИНАНИЕ О ДЕДЛАЙНЕ</b>

📋 <b>{task.title}</b>
📝 Описание: {task.description or 'Не указано'}
📅 Дедлайн: {due_date_str}
🏷️ Категории: {', '.join([cat.name for cat in task.categories.all()]) or 'Не указаны'}

⏰ До дедлайна осталось: <b>{time_text}</b>
        """.strip()
        inline_keyboard = [[
            {
                'text': '🔕 Не оповещать',
                'callback_data': f'disable_notifications:{task.id}'
            }
        ]]
        return send_telegram_notification(task.user.telegram_id, message, inline_keyboard)
    except Exception as e:
        logger.error(f"Error notifying user about upcoming task {task.id}: {e}")
        return False

@shared_task
def check_due_tasks():
    """Проверка просроченных задач"""
    from .models import Task

    now = timezone.now()
    due_tasks = Task.objects.filter(
        due_date__lte=now,
        is_completed=False,
        notifications_disabled=False  # Исключаем задачи с отключенными уведомлениями
    ).select_related('user').prefetch_related('categories')

    logger.info(f"Found {due_tasks.count()} overdue tasks with notifications enabled")

    for task in due_tasks:
        success = notify_user_about_due_task(task)
        if success:
            logger.info(f"Successfully notified user about overdue task {task.id}")
        else:
            logger.error(f"Failed to notify user about overdue task {task.id}")

@shared_task
def check_upcoming_tasks():
    """Проверка задач с приближающимся дедлайном (за 1 час)"""
    from .models import Task

    now = timezone.now()
    from datetime import timedelta

    # Задачи, дедлайн которых наступит в течение часа
    upcoming_deadline = now + timedelta(hours=1)
    upcoming_tasks = Task.objects.filter(
        due_date__gt=now,
        due_date__lte=upcoming_deadline,
        is_completed=False,
        notifications_disabled=False  # Исключаем задачи с отключенными уведомлениями
    ).select_related('user').prefetch_related('categories')

    logger.info(f"Found {upcoming_tasks.count()} upcoming tasks with notifications enabled")

    for task in upcoming_tasks:
        success = notify_user_about_upcoming_task(task)
        if success:
            logger.info(f"Successfully notified user about upcoming task {task.id}")
        else:
            logger.error(f"Failed to notify user about upcoming task {task.id}")

@shared_task
def send_daily_reminder():
    """Ежедневное напоминание о задачах"""
    from .models import Task, UserProfile
    from datetime import timedelta

    now = timezone.now()
    tomorrow = now + timedelta(days=1)

    users_with_tasks = UserProfile.objects.filter(
        tasks__is_completed=False,
        tasks__due_date__gte=now,
        tasks__due_date__lte=tomorrow
    ).distinct()

    logger.info(f"Sending daily reminders to {users_with_tasks.count()} users")

    for user_profile in users_with_tasks:
        try:
            tomorrow_tasks = user_profile.tasks.filter(
                due_date__gte=now,
                due_date__lte=tomorrow,
                is_completed=False
            ).prefetch_related('categories')

            if tomorrow_tasks.exists():
                message = f"""
📅 <b>ЕЖЕДНЕВНОЕ НАПОМИНАНИЕ</b>

У вас есть задачи на завтра:

"""
                for task in tomorrow_tasks:
                    # Конвертируем в локальное время America/Adak
                    local_tz = pytz.timezone('America/Adak')
                    due_date_local = task.due_date.astimezone(local_tz)
                    due_time_str = due_date_local.strftime('%H:%M')
                    message += f"""
📋 <b>{task.title}</b>
⏰ {due_time_str}
🏷️ {', '.join([cat.name for cat in task.categories.all()]) or 'Без категории'}
"""

                message += f"\nВсего задач на завтра: <b>{tomorrow_tasks.count()}</b>"

                send_telegram_notification(user_profile.telegram_id, message.strip())
                logger.info(f"Sent daily reminder to user {user_profile.telegram_id}")

        except Exception as e:
            logger.error(f"Error sending daily reminder to user {user_profile.telegram_id}: {e}")

@shared_task
def cleanup_old_notifications():
    """Очистка старых уведомлений (если нужно)"""
    # ToDo Можно добавить логику очистки старых уведомлений
    # Например, удаление записей о доставленных уведомлениях
    logger.info("Cleanup old notifications task completed")

@shared_task
def disable_task_notifications(task_id):
    """Отключение уведомлений для конкретной задачи"""
    from .models import Task

    try:
        task = Task.objects.get(id=task_id)
        task.notifications_disabled = True
        task.save()
        logger.info(f"Notifications disabled for task {task_id}")
        return True
    except Task.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error disabling notifications for task {task_id}: {e}")
        return False
