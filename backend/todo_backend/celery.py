import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_backend.settings')

app = Celery('todo_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-due-tasks-every-minute': {
        'task': 'tasks.tasks.check_due_tasks',
        'schedule': 60.0,
    },
    'check-upcoming-tasks-every-5-minutes': {
        'task': 'tasks.tasks.check_upcoming_tasks',
        'schedule': 300.0,
    },
    'send-daily-reminder-at-9am': {
        'task': 'tasks.tasks.send_daily_reminder',
        'schedule': crontab(hour=9, minute=0),
    },
    'cleanup-old-notifications-daily': {
        'task': 'tasks.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
