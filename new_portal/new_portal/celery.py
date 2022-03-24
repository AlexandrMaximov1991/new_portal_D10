import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'new_portal.settings')

app = Celery('new_portal')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send_message_weekly_digest': {
        'task': 'news_portal.tasks.email_weekly',
        'schedule': crontab(hour=8, minute=0, day_of_week='monday'),
    },
}

