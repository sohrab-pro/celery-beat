from __future__ import absolute_import, unicode_literals
from celery import Celery, Task
from datetime import timedelta
import os
from django.apps import apps
from django.conf import settings        
from celery.schedules import crontab
import time


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pr_celery.settings")
app = Celery('pr_celery')

app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

app.conf.beat_schedule = {
    'my_nightly_task': {
        'task': 'core.tasks.my_nightly_task',
        # run monthly
        'schedule': crontab(minute=0, hour=0, day_of_month=1),
        # 'schedule': crontab(minute='*/'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))