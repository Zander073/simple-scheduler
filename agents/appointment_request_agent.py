# agents/appointment_request_agent.py
import json
from datetime import timedelta
from agents.base import BaseAgent
from agents.claude_client import claude_client
from agents.schemas import AppointmentRequest, AppointmentAction, AppointmentResult
from appointments.models import Appointment, Client
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime

# @TODO: ask Eitan what he wants the response from the agent to be
class AppointmentRequestAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return """
        You are an Appointment Scheduling Agent. Given an appointment request and the current clinician calendar, 
        you must generate a list of actions to take to accommodate the appointment. Never reject appointments.
        Return your decisions as a JSON array of AppointmentAction objects.

        Appointment scheduling rules:
        - The appointment must be scheduled on or after the current time
        - Never update an existing urgent appointment
        - Incoming urgent appointments should be scheduled to the first open time slot
        - It is okay to update existing non-urgent appointments
        - Non-urgent appointments should be scheduled at first available time slot that takes into consideration the time_of_day_preference and preferred_days
        - You may create one new appointment and update zero or more existing non-urgent appointments
        - All appointments must be scheduled ON THE HOUR (e.g., 9:00, 10:00, 11:00, etc.)
        - All appointments must be between 9:00 AM and 5:00 PM (business hours)
        - All appointments must be 50 minutes in duration

        AppointmentAction schema:
        {
            "action": "create" or "update",
            "start_time": "ISO datetime string (must be on the hour between 9 AM and 5 PM)",
            "client_id": integer,
            "clinician_id": integer,
            "appointment_id": integer (only required for update actions)
        }

        Return a JSON array of AppointmentAction objects.
        """

    def infer(self, request: AppointmentRequest) -> list[AppointmentAction]:
        """Infer the actions needed to accommodate the appointment request."""
        available_time_slots = self.get_available_time_slots(request.clinician_id)

        prompt = f"""
        Given the following appointment request and available time slots, generate a list of actions to take to accommodate the appointment.
        The current appointment request is: {request.__str__()}
        The following time slots are available:
        {available_time_slots}
        """

        output = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text

        # Parse the JSON output to get AppointmentAction objects
        try:
            actions_data = json.loads(output)
            if not isinstance(actions_data, list):
                actions_data = [actions_data]
            
            # Convert to AppointmentAction objects
            actions = []
            for action_data in actions_data:
                action = AppointmentAction(**action_data)
                actions.append(action)
            
            return actions
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON output from Claude: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create AppointmentAction objects: {e}")

    def execute_actions(self, actions: list[AppointmentAction]) -> list[AppointmentResult]:
        """Execute the list of AppointmentAction objects on the appointments database."""
        results = []
        
        for action in actions:
            if action.action == "create":
                # Create a new appointment
                appointment = Appointment.objects.create(
                    client_id=action.client_id,
                    clinician_id=action.clinician_id,
                    start_time=parse_datetime(action.start_time),
                    end_time=parse_datetime(action.start_time) + timedelta(minutes=50)
                )
                
                results.append(AppointmentResult(
                    action_taken="created",
                    appointment={
                        "id": appointment.id,
                        "client_id": appointment.client_id,
                        "clinician_id": appointment.clinician_id,
                        "start_time": appointment.start_time.isoformat(),
                        "end_time": appointment.end_time.isoformat()
                    }
                ))
                
            elif action.action == "update":
                # Update an existing appointment
                if not action.appointment_id:
                    raise ValueError("appointment_id is required for update actions")
                
                appointment = Appointment.objects.get(id=action.appointment_id)
                appointment.start_time = parse_datetime(action.start_time)
                appointment.end_time = parse_datetime(action.start_time) + timedelta(minutes=50)
                appointment.save()
                
                results.append(AppointmentResult(
                    action_taken="updated",
                    appointment={
                        "id": appointment.id,
                        "client_id": appointment.client_id,
                        "clinician_id": appointment.clinician_id,
                        "start_time": appointment.start_time.isoformat(),
                        "end_time": appointment.end_time.isoformat()
                    }
                ))
        
        return results

    def get_weekly_appointments(self, clinician_id: int) -> list[Appointment]:
        """Get available time slots for this week for the clinician (Monday-Friday, 9 AM - 5 PM)."""
        from django.utils import timezone
        from datetime import timedelta        
        # Calculate the start of the current week (Monday)
        now = timezone.now()
        monday_9am = (now - timedelta(days=now.weekday())).replace(hour=9, minute=0, second=0, microsecond=0)
        friday_5pm = (now + timedelta(days=4-now.weekday())).replace(hour=17, minute=0, second=0, microsecond=0)

        weekly_appointments = Appointment.objects.filter(
            clinician_id=clinician_id,
            start_time__gte=monday_9am,
            start_time__lte=friday_5pm
        ).order_by('start_time')

        return weekly_appointments

    def get_available_time_slots(self, clinician_id: int) -> list:
        """Get available time slots for this week for the clinician (Monday-Friday, 9 AM - 5 PM)."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Get all booked appointments for the week
        weekly_appointments = self.get_weekly_appointments(clinician_id)
        
        # Calculate the start and end of the current week
        now = timezone.now()
        monday_9am = (now - timedelta(days=now.weekday())).replace(hour=9, minute=0, second=0, microsecond=0)
        friday_5pm = (now + timedelta(days=4-now.weekday())).replace(hour=17, minute=0, second=0, microsecond=0)
        
        # Generate all possible time slots (on the hour, 50 minutes duration)
        available_slots = []
        current_slot = monday_9am
        
        while current_slot <= friday_5pm:
            # Skip slots that are in the past
            if current_slot < now:
                current_slot += timedelta(hours=1)
                continue
            
            # Skip weekends (Saturday = 5, Sunday = 6)
            if current_slot.weekday() >= 5:
                current_slot += timedelta(hours=1)
                continue
                
            # Skip slots outside business hours (before 9 AM or after 5 PM)
            if current_slot.hour < 9 or current_slot.hour >= 17:
                current_slot += timedelta(hours=1)
                continue
                
            # Check if this slot is available (not booked)
            slot_end = current_slot + timedelta(minutes=50)
            is_booked = weekly_appointments.filter(
                start_time__lt=slot_end,
                start_time__gte=current_slot
            ).exists()
            
            if not is_booked:
                available_slots.append(current_slot)
            
            current_slot += timedelta(hours=1)
        
        return available_slots

    
        