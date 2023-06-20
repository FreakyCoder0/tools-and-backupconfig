from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NMSproject.settings')

app = Celery('NMSproject')
app.conf.enable_utc = False

app.conf.update(time = 'Asia/Kolkata')

app.config_from_object(settings, namespace='CELERY')

#celery beat settings
app.conf.beat_schedule = {
    
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {self.request!r}')