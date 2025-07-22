from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Appointment
from .serializers import AppointmentSerializer


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
