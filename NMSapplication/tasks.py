from celery import shared_task
from NMSapplication.utils.backup_launcher import BackupLuancher
from NMSapplication.utils.topology import DiscoverTopology


@shared_task(name ='backup',bind = True)
def backup_launch(self,*args,**kwargs):
    task_id = self.request.id  
    backup_obj = BackupLuancher(task_id)
    backup_obj.main()

@shared_task(name = 'TopologyDiscovery',bind = True)
def topology_discovery(self,*args,**kwargs):
    task_id = self.request.id  
    backup_obj = DiscoverTopology(task_id)
    backup_obj.main()
    
    

   