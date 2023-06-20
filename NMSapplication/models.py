from django.db import models
from django_celery_beat.models import PeriodicTask
# Create your models here.
class Scheduler(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email_subject = models.CharField(max_length=200, null=True, blank=True)
    report_type = models.CharField(max_length=50, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    is_on = models.BooleanField(default=True)
    task_status = models.CharField(max_length=50, default='Success', null=True, blank=True)
    task = models.OneToOneField(PeriodicTask, on_delete=models.CASCADE, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    scheduler_type = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Launchscheduler(models.Model):
    task_id = models.CharField(max_length=100)
    logs = models.TextField()
    created_at = models.DateTimeField(auto_now=True)
    scheduler_type = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.task_id
