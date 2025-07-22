from django.urls import path
from . import views
 
urlpatterns = [
    path('appointments/', views.appointment_list, name='appointment-list'),
    path('requests/', views.request_appointment, name='request-appointment'),
] 