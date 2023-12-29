from celery import shared_task
from datetime import datetime
import time
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.contrib.auth.models import User
from .models import UserSchedule

# start celery worker for all tasks saved in UserSchedule model


@shared_task
def send_text_message(user_id, message):
    user = User.objects.get(id=user_id)


@shared_task
def my_nightly_task():
    print("Hello World")
    print(datetime.now())