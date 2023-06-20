from rest_framework import serializers
from NMSapplication.models import *

class LaunchschedulerSerilaizers(serializers.ModelSerializer):
    class Meta:
        model = Launchscheduler
        fields = ['task_id','logs','created_at','scheduler_type']
        
        
class SchedulerSerilaizers(serializers.ModelSerializer):
    logs_data = serializers.SerializerMethodField()
    class Meta:
        model = Scheduler
        fields = ['name','email_subject','report_type','created_by','is_on','task_status','task','is_default','scheduler_type', 'logs_data']
    def get_logs_data(self, obj):
        ord = LaunchschedulerSerilaizers(Launchscheduler.objects.filter(scheduler_type=obj.scheduler_type)[:5],many=True).data
        return ord
