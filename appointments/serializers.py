from rest_framework import serializers
from .models import Client, Appointment


class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = ['id', 'first_name', 'last_name', 'full_name', 'memo']


class AppointmentSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'start_time', 'duration_in_minutes', 'client'] 