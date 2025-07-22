from django.urls import path
from . import views

urlpatterns = [
    path('', views.SchedulerView.as_view(), name='scheduler'),
]
