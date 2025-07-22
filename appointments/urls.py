from django.urls import path
from . import views

urlpatterns = [
    path('api/appointments/', views.appointment_list, name='appointment-list'),
] 