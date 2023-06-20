from django.urls import path
from django.urls.conf import include
from . import views

urlpatterns = [
    path('scheduler/', views.scheduler, name = "scheduler"),    
    path("home",views.home,name='home'),
    path("page1",views.page1,name='page1'),
    path("input",views.scheduler,name='input'),
    path("taskpage",views.launchscheduler,name='taskpage')
    
]
