from NMSapplication.models import Launchscheduler,Scheduler
from django.core.mail import send_mail
from NMSproject import settings

class BackupLuancher:
    def __init__(self,task_id):
        self.logs={}
        self.task_id = task_id

    def main(self):
        self.logs['data']= "123 sdchdshcv shdvgshd vhjs"
        created = Launchscheduler.objects.create(
            task_id=self.task_id,
            scheduler_type='backup',
            logs=self.logs
        )
        email_subject = Scheduler.objects.filter(scheduler_type='backup').last()
        send_mail( 
                subject = email_subject.email_subject, 
                message = self.logs['data'], 
                from_email = settings.EMAIL_HOST_USER, 
                recipient_list=['poasharshtestmail@gmail.com']
        )
    