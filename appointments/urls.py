from django.urls import path
from . import views

urlpatterns = [
    path('appointments/', views.appointment_list, name='appointment-list'),
    path('appointments/create/', views.create_appointment, name='create-appointment'),
    path('clients/', views.client_list, name='client-list'),
    path('requests/', views.request_appointment, name='request-appointment'),
] 