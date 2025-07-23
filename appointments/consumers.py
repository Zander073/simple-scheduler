import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User


class AppointmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # For demo purposes, we'll use a simple group for the first clinician
        # In a real app, you'd get the clinician from authentication
        self.clinician_group = "clinician_notifications"
        
        # Join the clinician group
        await self.channel_layer.group_add(
            self.clinician_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send a welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to appointment notifications'
        }))

    async def disconnect(self, close_code):
        # Leave the clinician group
        await self.channel_layer.group_discard(
            self.clinician_group,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle any messages from the client (if needed)
        pass

    async def appointment_request(self, event):
        # Send appointment request notification to the client
        await self.send(text_data=json.dumps({
            'type': 'appointment_request',
            'message': event['message'],
            'data': event.get('data', {})
        }))