# agents/appointment_request_agent.py
import json
from typing import List
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

    def infer(self, request: AppointmentRequest) -> List[AppointmentResult]:
        """
        Generate actions based on the appointment request and current calendar,
        apply those actions, and return the results.
        """
        current_calendar = self._get_clinician_calendar(request.clinician_id)
        
        # Generate actions using Claude
        actions = self._generate_actions(request, current_calendar)
        
        # Validate all actions before applying them
        validated_actions = self._validate_actions(actions, current_calendar)
        
        # Apply each validated action and collect results
        results = []
        for action in validated_actions:
            result = self._apply_action(action, request)
            if result:
                results.append(result)
        
        return results

    def _validate_actions(self, actions: List[AppointmentAction], current_calendar: List[str]) -> List[AppointmentAction]:
        """Validate that all actions are valid and don't create conflicts."""
        if not actions:
            return []
        
        # Parse current calendar times
        existing_times = []
        for appt_time_str in current_calendar:
            try:
                appt_time = parse_datetime(appt_time_str)
                if appt_time:
                    existing_times.append(appt_time)
            except:
                continue
        
        # Collect all proposed times from actions
        proposed_times = []
        for action in actions:
            try:
                proposed_time = parse_datetime(action.start_time)
                if proposed_time:
                    proposed_times.append((action, proposed_time))
            except:
                continue
        
        # Check for conflicts
        valid_actions = []
        conflicts = []
        
        # First pass: check conflicts with existing appointments
        for action, proposed_time in proposed_times:
            # Check if this time conflicts with existing appointments
            if self._has_conflict(proposed_time, existing_times):
                conflicts.append(f"Action {action.action} at {proposed_time} conflicts with existing appointment")
                continue
            
            # Check if this is an update action and the appointment exists
            if action.action == "update" and action.appointment_id:
                try:
                    appointment = Appointment.objects.get(id=action.appointment_id)
                    # Don't allow updating urgent appointments
                    if hasattr(appointment, 'urgency') and appointment.urgency:
                        conflicts.append(f"Cannot update urgent appointment {action.appointment_id}")
                        continue
                except Appointment.DoesNotExist:
                    conflicts.append(f"Appointment {action.appointment_id} does not exist")
                    continue
            
            valid_actions.append((action, proposed_time))
        
        # Second pass: check conflicts between proposed actions
        final_valid_actions = []
        for action, proposed_time in valid_actions:
            # Check if this time conflicts with other proposed times
            other_proposed_times = [pt for pt in valid_actions if pt[0] != action]
            if self._has_conflict(proposed_time, [pt[1] for pt in other_proposed_times]):
                conflicts.append(f"Action {action.action} at {proposed_time} conflicts with another proposed action")
                continue
            
            final_valid_actions.append(action)
        
        # Log conflicts if any
        if conflicts:
            print(f"Validation conflicts found: {conflicts}")
        
        return final_valid_actions

    def _has_conflict(self, proposed_time, existing_times):
        """Check if a proposed time conflicts with existing times."""
        from datetime import timedelta
        from django.utils import timezone
        
        # Ensure proposed_time is timezone-aware
        if timezone.is_naive(proposed_time):
            proposed_time = timezone.make_aware(proposed_time)
        
        for existing_time in existing_times:
            # Ensure existing_time is timezone-aware
            if timezone.is_naive(existing_time):
                existing_time = timezone.make_aware(existing_time)
            
            # Check if slots overlap (50-minute appointments)
            # A 9:00-9:50 appointment should not conflict with a 9:50-10:40 appointment
            proposed_end = proposed_time + timedelta(minutes=50)
            existing_end = existing_time + timedelta(minutes=50)
            
            # Debug output for boundary cases
            if abs((proposed_time - existing_end).total_seconds()) < 60 or abs((existing_time - proposed_end).total_seconds()) < 60:
                print(f"DEBUG: Checking boundary - Proposed: {proposed_time} to {proposed_end}, Existing: {existing_time} to {existing_end}")
            
            if (proposed_time < existing_end and existing_time < proposed_end):
                return True
        return False

    def _generate_actions(self, request: AppointmentRequest, calendar: List[str]) -> List[AppointmentAction]:
        """Generate a list of actions to take based on the request and current calendar."""
        
        prompt = f"""
        Appointment Request:
        - Client ID: {request.client_id}
        - Clinician ID: {request.clinician_id}
        - Urgency: {request.urgency}
        - Time of day preference: {request.time_of_day_preference}
        - Preferred days: {request.preferred_days}
        
        Current Clinician Calendar (ISO datetime strings):
        {calendar}
        
        Generate actions to accommodate this appointment request. You may:
        1. Create a new appointment
        2. Update existing non-urgent appointments to make room
        
        Return a JSON array of AppointmentAction objects.
        """
        
        try:
            output = claude_client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            ).content[0].text
            
            try:
                # Extract JSON from the response (Claude often wraps JSON in markdown)
                import re
                json_match = re.search(r'```json\s*(\[.*?\])\s*```', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Try to find JSON array without markdown
                    json_match = re.search(r'\[.*?\]', output, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        # Try to parse the entire response as JSON
                        json_str = output
                
                actions_data = json.loads(json_str)
                if isinstance(actions_data, dict):
                    actions_data = [actions_data]  # Handle single action case
                
                actions = []
                for action_data in actions_data:
                    action = AppointmentAction.model_validate(action_data)
                    actions.append(action)
                
                return actions
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback: create a simple appointment
                fallback_action = AppointmentAction(
                    action="create",
                    start_time=self._find_next_available_time(request, calendar),
                    client_id=request.client_id,
                    clinician_id=request.clinician_id
                )
                return [fallback_action]
        except Exception as e:
            # Fallback: create a simple appointment
            fallback_action = AppointmentAction(
                action="create",
                start_time=self._find_next_available_time(request, calendar),
                client_id=request.client_id,
                clinician_id=request.clinician_id
            )
            return [fallback_action]

    def _apply_action(self, action: AppointmentAction, request: AppointmentRequest) -> AppointmentResult:
        """Apply a single action and return the result."""
        
        if action.action == "create":
            return self._create_appointment(action, request)
        elif action.action == "update":
            return self._update_appointment(action, request)
        
        return None

    def _create_appointment(self, action: AppointmentAction, request: AppointmentRequest) -> AppointmentResult:
        """Create a new appointment."""
        try:
            scheduled_datetime = parse_datetime(action.start_time)
            if not scheduled_datetime:
                return None
            
            # Get the client and clinician objects
            try:
                client = Client.objects.get(id=action.client_id)
                clinician = User.objects.get(id=action.clinician_id)
            except (Client.DoesNotExist, User.DoesNotExist) as e:
                return None
                
            appointment = Appointment.objects.create(
                start_time=scheduled_datetime,
                duration_in_minutes=50,
                client=client,
                clinician=clinician
            )
            
            result = AppointmentResult(
                action_taken="created",
                appointment=self.serialize_appointment(appointment)
            )
            return result
        except Exception as e:
            return None

    def _update_appointment(self, action: AppointmentAction, request: AppointmentRequest) -> AppointmentResult:
        """Update an existing appointment."""
        try:
            if not action.appointment_id:
                return None
                
            appointment = Appointment.objects.get(id=action.appointment_id)
            
            # Don't update urgent appointments (if urgency field exists)
            if hasattr(appointment, 'urgency') and appointment.urgency:
                return None
                
            scheduled_datetime = parse_datetime(action.start_time)
            if not scheduled_datetime:
                return None
                
            appointment.start_time = scheduled_datetime
            appointment.save()
            
            return AppointmentResult(
                action_taken="updated",
                appointment=self.serialize_appointment(appointment)
            )
        except Appointment.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error updating appointment: {e}")
            return None

    def _get_clinician_calendar(self, clinician_id: int) -> List[str]:
        """Get the current clinician's calendar as a list of ISO datetime strings."""
        appointments = Appointment.objects.filter(clinician_id=clinician_id).order_by('start_time')
        return [appt.start_time.isoformat() for appt in appointments]

    def _find_next_available_time(self, request: AppointmentRequest, calendar: List[str]) -> str:
        """Find the next available time slot for the appointment."""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Get current time (timezone-aware)
        now = timezone.now()
        
        # Start from the next hour, rounded up
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        # Ensure we're within business hours (9 AM to 5 PM)
        business_start = next_hour.replace(hour=9, minute=0, second=0, microsecond=0)
        business_end = next_hour.replace(hour=17, minute=0, second=0, microsecond=0)
        
        # If next_hour is before business hours, start at 9 AM
        if next_hour.hour < 9:
            next_hour = business_start
        # If next_hour is after business hours, start at 9 AM the next day
        elif next_hour.hour >= 17:
            next_hour = business_start + timedelta(days=1)
        
        # Parse existing appointments to find conflicts
        existing_times = []
        for appt_time_str in calendar:
            try:
                appt_time = parse_datetime(appt_time_str)
                if appt_time:
                    # Ensure timezone awareness
                    if timezone.is_naive(appt_time):
                        appt_time = timezone.make_aware(appt_time)
                    existing_times.append(appt_time)
            except:
                continue
        
        # Find the next available slot
        current_slot = next_hour
        max_attempts = 7 * 8  # 7 days * 8 hours per day
        
        for _ in range(max_attempts):
            # Check if this slot conflicts with existing appointments
            slot_conflicts = False
            for existing_time in existing_times:
                # Check if slots overlap (50-minute appointments)
                if (current_slot <= existing_time < current_slot + timedelta(minutes=50) or
                    existing_time <= current_slot < existing_time + timedelta(minutes=50)):
                    slot_conflicts = True
                    break
            
            if not slot_conflicts:
                return current_slot.isoformat()
            
            # Move to next hour
            current_slot += timedelta(hours=1)
            
            # If we've moved past business hours, go to next day at 9 AM
            if current_slot.hour >= 17:
                current_slot = current_slot.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Fallback: return 9 AM tomorrow
        return (business_start + timedelta(days=1)).isoformat()

    def serialize_appointment(self, appointment: Appointment) -> dict:
        """Serialize an appointment object to a dictionary."""
        return {
            'id': appointment.id,
            'client_id': appointment.client.id,
            'clinician_id': appointment.clinician.id,
            'start_time': appointment.start_time.isoformat(),
            'duration_in_minutes': appointment.duration_in_minutes
        }
