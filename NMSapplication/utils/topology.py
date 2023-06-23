from NMSapplication.models import Launchscheduler,Scheduler
from django.core.mail import send_mail
from NMSproject import settings

class Topology_Discovery:
    def __init__(self,task_id):
        self.logs={}
        self.task_id = task_id

    def main(self):
        self.logs['data']= "Topology Discovery xjiceisvbciebc wnnxiw" 
        created = Launchscheduler.objects.create(
            task_id=self.task_id,
            scheduler_type='TopologyDiscovery',
            logs=self.logs
        )
        email_subject = Scheduler.objects.filter(scheduler_type='TopologyDiscovery').last()
        send_mail( 
                subject = email_subject.email_subject, 
                message = self.logs['data'], 
                from_email = settings.EMAIL_HOST_USER, 
                recipient_list=['poasharshtestmail@gmail.com']
        )
    