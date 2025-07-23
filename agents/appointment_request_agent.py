# agents/appointment_request_agent.py
import json
import re
from django.utils import timezone
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
        - An appointment is urgent if the urgency field in the AppointmentRequest is True
        - Assume all existing appointments are NOT urgent!
        - A clinician can only have one appointment per client at a time (i.e. no overlapping appointments)
        - The appointment must be scheduled on or after the current time
        - All appointments must be scheduled ON THE HOUR (e.g., 9:00, 10:00, 11:00, etc.)
        - All appointments must be between 9:00 AM and 5:00 PM (business hours)
        - All appointments must be 60 minutes in duration
        - The response must be a JSON format with no new lines or extra spaces
    
        Handle urgent appointments with the following rules:
        - Urgent appointments should be always scheduled as close to the current time as possible
        - If an existing appointment is blocking a potential urgent appointment time slot, identify the next available time slot and schedule the existing appointment there (i.e. update the existing appointment)

        Handle non-urgent appointments with the following rules:
        - The appointment must be booked by preference
        - Book at the soonest available time in the future
        - Never update an existing urgent appointment

        You should return a list of AppointmentAction objects. With the following format:
        [
            {
                "action": "create" or "update",
                "start_time": "ISO datetime string (must be on the hour between 9 AM and 5 PM)",
                "client_id": integer,
                "clinician_id": integer,
                "appointment_id": integer (only required for update actions)
            }
        ]
        """

    def infer(self, request: AppointmentRequest) -> list[AppointmentAction]:
        """Infer the actions needed to accommodate the appointment request."""
        available_time_slots = self.get_available_time_slots(request.clinician_id)

        prompt = f"""
        The current time is {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}.
        Given the following appointment request and available time slots, generate a list of actions to take to accommodate the appointment.
        The current appointment request is: {request.__str__()}
        The following time slots are available:
        {available_time_slots}
        """
        print(prompt)

        output = claude_client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text

        print(output)

        # Parse the JSON output to get AppointmentAction objects
        try:
            actions_data = self.extract_json_array_from_claude(output)

            print(actions_data)

            self.execute_actions(actions_data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON output from Claude: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create AppointmentAction objects: {e}")

        return actions_data
   
    def execute_actions(self, actions: list[AppointmentAction]) -> list[AppointmentResult]:
        """Execute the list of AppointmentAction objects on the appointments database."""
        results = []
        
        for action in actions:
            if action.action == "create":
                # Get the Client and User objects
                client = Client.objects.get(id=action.client_id)
                clinician = User.objects.get(id=action.clinician_id)
                
                # Create a new appointment
                appointment = Appointment.objects.create(
                    client=client,
                    clinician=clinician,
                    start_time=parse_datetime(action.start_time),
                )
                
                results.append(AppointmentResult(
                    action_taken="created",
                    appointment={
                        "id": appointment.id,
                        "client_id": appointment.client.id,
                        "clinician_id": appointment.clinician.id,
                        "start_time": appointment.start_time.isoformat(),
                        "duration_in_minutes": appointment.duration_in_minutes
                    }
                ))
                
            elif action.action == "update":
                # Update an existing appointment
                if not action.appointment_id:
                    raise ValueError("appointment_id is required for update actions")
                
                appointment = Appointment.objects.get(id=action.appointment_id)
                appointment.start_time = parse_datetime(action.start_time)
                appointment.save()

                results.append(AppointmentResult(
                    action_taken="updated",
                    appointment={
                        "id": appointment.id,
                        "client_id": appointment.client.id,
                        "clinician_id": appointment.clinician.id,
                        "start_time": appointment.start_time.isoformat(),
                        "duration_in_minutes": appointment.duration_in_minutes
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
        
        # Generate all possible time slots (on the hour, 60 minutes duration)
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
            slot_end = current_slot + timedelta(minutes=60)
            is_booked = weekly_appointments.filter(
                start_time__lt=slot_end,
                start_time__gte=current_slot
            ).exists()
            
            if not is_booked:
                available_slots.append(current_slot)
            
            current_slot += timedelta(hours=1)
        
        # Convert datetime objects to human readable strings
        readable_slots = [slot.strftime("%A, %B %d at %I:%M %p") for slot in available_slots]
        return readable_slots

    def extract_json_array_from_claude(self, response_text: str) -> list[AppointmentAction]:
        """
        Extract the first valid JSON array from the Claude response and convert it into AppointmentAction objects.
        """
        # Regex to extract only the first top-level array of objects
        match = re.search(r'(\[\s*{.*?}\s*\])', response_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON array found in response")

        json_str = match.group(1)

        try:
            raw_list = json.loads(json_str)
            return [AppointmentAction.model_validate(obj) for obj in raw_list]
        except Exception as e:
            raise ValueError(f"Error parsing JSON array: {e}")