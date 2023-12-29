import json
from django.db import models
from django.contrib.auth.models import User
from celery.result import AsyncResult
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class UserSchedule(models.Model):
    MINUTE = 'minute'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    EVERY_14_DAYS = 'every_14_days'
    EVERY_MONTH = 'every_month'

    SCHEDULE_CHOICES = [
        (MINUTE, 'Minute'),
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (EVERY_14_DAYS, 'Every 14 Days'),
        (EVERY_MONTH, 'Every Month'),
    ]

    CRONTAB_SCHEDULES = {
        MINUTE: {'minute': '*/1'},
        DAILY: {'hour': 7, 'minute': 0, 'day_of_week': '*'},
        WEEKLY: {'hour': 7, 'minute': 0, 'day_of_week': '1-5'},
        EVERY_14_DAYS: {'hour': 0, 'minute': 0, 'day_of_month': 14},
        EVERY_MONTH: {'hour': 0, 'minute': 0, 'day_of_month': 1},
    }

    lead = models.OneToOneField(User, on_delete=models.CASCADE)
    schedule = models.CharField(
        max_length=20, choices=SCHEDULE_CHOICES, default=DAILY)
    message = models.TextField(default="Hello World")
    task_id = models.CharField(max_length=255, null=True, blank=True)

    SEND_TEXT_MESSAGE_TASK_NAME = 'send_text_message'

    def get_task_name(self):
        return f'{self.SEND_TEXT_MESSAGE_TASK_NAME}_{self.lead.id}'

    def save(self, *args, **kwargs):
        schedule_params = self.CRONTAB_SCHEDULES.get(self.schedule)
        if schedule_params is not None:
            schedule, created = CrontabSchedule.objects.get_or_create(
                **schedule_params)

        task_name = self.get_task_name()
        task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'task': 'core.tasks.send_text_message',
                'crontab': schedule,
                'args': json.dumps([self.lead.id, self.message]),
            }
        )

        self.task_id = task.id
        super().save(*args, **kwargs)

    def deactivate_periodic_task(self):
        task_name = self.get_task_name()

        try:
            periodic_task = PeriodicTask.objects.get(name=task_name)
        except PeriodicTask.DoesNotExist:
            return

        periodic_task.enabled = False
        periodic_task.save()

        if self.task_id:
            result = AsyncResult(self.task_id)
            if result and result.state in ('PENDING', 'STARTED'):
                result.revoke()

    def activate_periodic_task(self):
        task_name = self.get_task_name()

        try:
            periodic_task = PeriodicTask.objects.get(name=task_name)
        except PeriodicTask.DoesNotExist:
            return

        periodic_task.enabled = True
        periodic_task.save()

    def __str__(self):
        return f'{self.lead.username} - {self.schedule}'
