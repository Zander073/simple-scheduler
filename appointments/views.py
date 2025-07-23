from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Appointment, Client
from .serializers import AppointmentSerializer, ClientSerializer
from agents.appointment_request_agent import AppointmentRequestAgent
from agents.schemas import AppointmentRequest
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random
from datetime import datetime, time, timedelta
from django.utils import timezone
import pytz

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

@api_view(['GET'])
def client_list(request):
    """
    List all clients for the first clinician (demo endpoint).
    """
    try:
        # Get the first clinician for demo purposes
        clinician = User.objects.filter(username__startswith='clinician').first()
        if not clinician:
            return Response(
                {'error': 'No clinicians found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        clients = Client.objects.filter(clinician=clinician).order_by('first_name', 'last_name')
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Error fetching clients: {str(e)}'},
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
        appointment_request = AppointmentRequest(
            client_id=client.id,
            clinician_id=clinician.id,
            urgency=is_urgent,
            time_of_day_preference=time_preference,
        )

        agent = AppointmentRequestAgent()
        actions_taken = agent.infer(appointment_request)

        from pytz import timezone, UTC
        from dateutil import parser

        start_time = actions_taken[0].start_time


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
                    'client_name': f"{client.first_name} {client.last_name}",
                    'start_time': start_time
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

@api_view(['POST'])
def create_appointment(request):
    """
    Create a new appointment with validation constraints.
    """
    try:
        # Get the first clinician for demo purposes
        clinician = User.objects.filter(username__startswith='clinician').first()
        if not clinician:
            return Response(
                {'error': 'No clinicians found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Extract and validate required fields
        client_id = request.data.get('client')
        start_time_str = request.data.get('start_time')
        
        if not all([client_id, start_time_str]):
            return Response(
                {'error': 'client and start_time are required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate client exists and belongs to clinician
        try:
            client = Client.objects.get(id=client_id, clinician=clinician)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client not found or not associated with current clinician'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parse ISO datetime string
        try:
            # Parse the datetime string
            if 'T' in start_time_str:
                # Handle ISO format with or without timezone
                if start_time_str.endswith('Z'):
                    # UTC time
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                elif '+' in start_time_str or start_time_str.endswith('Z'):
                    # Already has timezone info
                    start_time = datetime.fromisoformat(start_time_str)
                else:
                    # Naive datetime - treat as local time
                    start_time = datetime.fromisoformat(start_time_str)
                    start_time = timezone.make_aware(start_time)
            else:
                # Fallback for other formats
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                start_time = timezone.make_aware(start_time)
        except ValueError:
            return Response(
                {'error': 'Invalid start_time format. Use ISO format (e.g., 2025-01-23T14:00:00)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation: Start time cannot be in the past
        if start_time <= timezone.now():
            return Response(
                {'error': 'Appointment start time cannot be in the past'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation: Time must be on the hour and between 9 AM and 4 PM (Eastern Time)
        et_tz = pytz.timezone('America/New_York')
        start_time_et = start_time.astimezone(et_tz)
        appointment_time = start_time_et.time()
        
        if appointment_time.minute != 0:
            return Response(
                {'error': 'Appointments must start on the hour (00 minutes)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not (time(9, 0) <= appointment_time <= time(16, 0)):
            return Response(
                {'error': 'Appointments must be between 9 AM and 4 PM Eastern Time'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation: Start time can't be on a weekend
        if start_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return Response(
                {'error': 'Appointments cannot be scheduled on weekends'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for scheduling conflicts (optional but recommended)
        existing_appointment = Appointment.objects.filter(
            clinician=clinician,
            start_time__date=start_time.date(),
            start_time__time=start_time.time()
        ).first()
        
        if existing_appointment:
            return Response(
                {'error': 'An appointment already exists at this time'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the appointment
        appointment = Appointment.objects.create(
            start_time=start_time,
            duration_in_minutes=50,  # Default duration
            client=client,
            clinician=clinician
        )
        
        # Serialize and return the created appointment
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error creating appointment: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )