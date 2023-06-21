from django.http import HttpResponse, Http404
import subprocess
from django.shortcuts import redirect, render
from rest_framework.response import Response
from .models import *
from rest_framework import status
from .tasks import test_func
from django.db.models import Subquery, OuterRef
from .serializers import LaunchschedulerSerilaizers, SchedulerSerilaizers


def ping(IPAddress, count):
    print("******in function ping", IPAddress)
    result = subprocess.run(['ping', '-c', str(count), IPAddress], capture_output=True, text=True)
    return result.stdout

def traceroute(IPAddress):
    print("******in function traceroute", IPAddress)
    result = subprocess.run(['traceroute', IPAddress], capture_output=True, text=True)
    return result.stdout

def snmpwalk(IPAddress, option_SNMP, OID, SNMPPORT, CommStr=None, SNMP_Cred=None, SecName=None, Apassword=None, Aprotocol=None, Pprotocol=None, Ppassphrase=None):
    if option_SNMP == 'v1':
        if CommStr is None:
            result = 'Community string not provided!'
        else:
            result = subprocess.run(['snmpwalk', '-v1', '-c', CommStr, IPAddress], capture_output=True, text=True)
            result = result.stdout
    elif option_SNMP == 'v2c':
        print('**************IPAddress:',IPAddress)
        print('**************OID:',OID)
        print('**************SNMPPORT:',SNMPPORT)
        print('**************CommStr:',CommStr)
        print('**************SNMP_Cred:',SNMP_Cred)
        print('**************SecName:',SecName)
        if CommStr is None:
            result = 'Community string not provided!'
        else:
            result = subprocess.run(['snmpwalk', '-v2c', '-c', CommStr, IPAddress], capture_output=True, text=True)
            result = result.stdout
    elif option_SNMP == 'v3':
        if SNMP_Cred == 'woAP':
            if SecName is None:
                result = 'Security name not provided!'
            else:
                result = subprocess.run(['snmpwalk', '-v3', '-l', 'noAuthNoPriv', '-u', SecName, IPAddress, OID], capture_output=True, text=True)
                result = result.stdout
        elif SNMP_Cred == 'wAwoP':
            if SecName is None or Apassword is None or Aprotocol is None:
                result = 'Incomplete authentication details!'
            else:
                result = subprocess.run(['snmpwalk', '-v3', '-l', 'authnoPriv', '-u', SecName, '-a', Aprotocol, '-A', Apassword, IPAddress, OID], capture_output=True, text=True)
                result = result.stdout
        elif SNMP_Cred == 'wAP':
            if SecName is None or Apassword is None or Aprotocol is None or Pprotocol is None or Ppassphrase is None:
                result = 'Incomplete authentication or privacy details!'
            else:
                result = subprocess.run(['snmpwalk', '-v3', '-l', 'authPriv', '-u', SecName, '-a', Aprotocol, '-A', Apassword, '-x', Pprotocol, '-X', Ppassphrase, IPAddress, OID], capture_output=True, text=True)
                result = result.stdout
        else:
            result = 'Invalid SNMP credentials selected!'
    else:
        result = 'Invalid SNMP version selected!'
    return result


def home(request):
    if request.method == "POST":

        option    = request.POST.get('option')
        IPAddress = request.POST.get('IPAddress')

        if option == 'ping':
            CountRange = int(request.POST.get('CountRange') or 0)

            if CountRange == 0:
                result = ping(IPAddress, 4)
            else:
                result = ping(IPAddress, CountRange)
            return render(request, 'home.html', {'result': result})
       
        elif option == 'traceroute':
            result = traceroute(IPAddress)
            return render(request, 'home.html', {'result': result})
        
        elif option == 'snmpwalk':

            option_SNMP = request.POST.get('option_SNMP')
            OID = request.POST.get('OID')
            SNMPPORT = request.POST.get('SNMPPORT')
            CommStr = request.POST.get('CommStr')
            SNMP_Cred = request.POST.get('SNMP_Cred')
            SecName = request.POST.get('SecName')
            Apassword = request.POST.get('Apassword')
            Aprotocol = request.POST.get('Aprotocol')
            Pprotocol = request.POST.get('Pprotocol')
            Ppassphrase = request.POST.get('Ppassphrase')

            result = snmpwalk(IPAddress, option_SNMP, OID, SNMPPORT, CommStr, SNMP_Cred, SecName, Apassword, Aprotocol, Pprotocol, Ppassphrase)
            return render(request, 'home.html', {'result': result})
        else:
            return render(request, 'home.html', {'result': 'Option not selected!'})
        
    else:
        return render(request, 'home.html')


def scheduler(request):
    if request.method == "POST":
        nameinput   = request.POST.get('name')
        option      = request.POST.get('option')
        includehost = request.POST.get('includehost')
        emailsub    = request.POST.get('emailsub')
        emailid     = request.POST.get('emailid')
        notigrp     = request.POST.get('notigrp')
        minutes     = request.POST.get('minutes')
        hours       = request.POST.get('hours')
        daysweek    = request.POST.get('daysweek')
        daysmonth   = request.POST.get('daysmonth')
        monthyear   = request.POST.get('monthyear')
        scheduler_type = request.POST.get('scheduler_type')
        print('********nameinput:', nameinput)
        print('********option:', option)
        print('********includehost:', includehost)
        print('********emailsub:', emailsub)
        print('********emailid:', emailid)
        print('********notigrp:', notigrp)
        print('********minutes:', minutes)
        print('********hours:', hours)
        print('********daysweek:', daysweek)
        print('********daysmonth:', daysmonth)
        print('********monthyear:', monthyear)
        print('********scheduler_type:', scheduler_type)
        # Create an instance of YourModel
        data, created = Scheduler.objects.get_or_create(
            name = nameinput,   # backuphost
            email_subject= emailsub,  # Backup Compliance Data        
            created_by= emailid, # harsh@gmail.com
            scheduler_type = scheduler_type # backup        
        ) 
        if created:       
            return render(request, 'input.html', {'result': "data input created!"})
        else:
            return render(request, 'input.html', {'result': "data already exist!"})
    else:
        return render(request, 'input.html')


def page1(request):
    sche = Scheduler.objects.all()
    # Check if the request method is POST
    serializers_data = SchedulerSerilaizers(sche, many=True)
    print('****************serializers_data', serializers_data.data)
    task_counts = {}
    for index, data in enumerate(serializers_data.data, start=1):
        logs_data = data.get('logs_data')
        if logs_data:
            task_ids = [log['task_id'] for log in logs_data]
            task_counts[index] = len(task_ids)
        else:
            task_counts[index] = 0

    dictionary = task_counts
    value = dictionary[1]
    if request.method == 'POST':
        launchscheduler(request)
        return render(request, 'page1.html', {'st': serializers_data.data,'task_counts': value})
    print('**********taskcount:', value)
    return render(request, 'page1.html', {'st': serializers_data.data,'task_counts': value})


def launchscheduler(request):
    print("*************1")
    task_id = test_func.apply_async()
    print("*************2", task_id)
    created = Launchscheduler.objects.create(
        task_id=task_id,
        scheduler_type='backup',
        logs="dcjbdhv dsvhd vjhgdv fhgvfhvfhv djj"
    )
  
def taskpage(request):
    if request.method == 'POST':
        print('******************request:',request)
        task_id = request.POST.get('task_id')
        print('******************taskid:',task_id)
        # Check if the request method is POST
        serializers_data = Launchscheduler.objects.filter(scheduler_type='backup', id=task_id)
        print('**********serializers_data', serializers_data)
        # Do something with the task_id, such as passing it to a Python function or storing it in a database
        return render(request, 'taskpage.html', {'st': serializers_data})
    return render(request, 'taskpage.html')
# from .tasks import test_func
# def test(request):
#     test_func.delay()
#     return HttpResponse("done here in views")
