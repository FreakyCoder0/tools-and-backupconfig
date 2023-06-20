from celery import shared_task
from time import sleep
from .models import Launchscheduler

@shared_task(name = 'backup',bind = True)
def test_func(*args,**kwargs):
    print("****************************hcdscdjs*")
    sleep(5)
    print("****************************dncbds*")
    #operations
    for i in range(10):
        print(i)
    print("Done tasks here")
    task_id = request.GET.get('task_id')
    
    return task_id