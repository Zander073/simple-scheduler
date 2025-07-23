from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Appointment, Client
from .serializers import AppointmentSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random

@api_view(['GET'])
def appointment_list(request):
    """
    List all appointments for the first clinician (demo endpoint).
    """
    try:
        # Get the first clinician for demo purposes
        clinician = User.objects.filter(username__startswith='clinician').first()
        if not clinician:
            return Response(
                {'error': 'No clinicians found'},
                status=status.HTTP_404_NOT_FOUND
            )
        appointments = Appointment.objects.filter(
            clinician=clinician
        ).select_related('client').order_by('start_time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Error fetching appointments: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def request_appointment(request):
    """
    Create an appointment request (demo endpoint).
    """
    try:
        # Get the first clinician for demo purposes
        clinician = User.objects.filter(username__startswith='clinician').first()
        if not clinician:
            return Response(
                {'error': 'No clinicians found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get a random client associated with the clinician
        clients = Client.objects.filter(clinician=clinician)
        if not clients.exists():
            return Response(
                {'error': 'No clients found for clinician'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        client = random.choice(clients)
        
        # Extract form data
        is_urgent = request.data.get('is_urgent', False)
        time_preference = request.data.get('time_preference')  # Not required
        
        # Validate time_preference if present
        if time_preference is not None:
            if not isinstance(time_preference, int) or time_preference < 9 or time_preference > 16:
                return Response(
                    {'error': 'time_preference must be an integer between 9 and 16 (inclusive)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create request object (to be passed to service later)
        appointment_request = {
            'is_urgent': is_urgent,
            'time_preference': time_preference,
            'client': client,
            'clinician': clinician
        }
        
        # Broadcast notification to WebSocket clients
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "clinician_notifications",
            {
                "type": "appointment_request",
                "message": "New appointment request received",
                "data": {
                    'is_urgent': is_urgent,
                    'time_preference': time_preference,
                    'client_id': client.id,
                    'clinician_id': clinician.id,
                    'client_name': f"{client.first_name} {client.last_name}"
                }
            }
        )
        
        # Return success response
        return Response({
            'message': 'Appointment request received',
            'request_data': {
                'is_urgent': is_urgent,
                'time_preference': time_preference,
                'client_id': client.id,
                'clinician_id': clinician.id
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error processing appointment request: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
