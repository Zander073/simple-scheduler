from datetime import datetime, timedelta
from django.utils import timezone

from agents.base import BaseAgent
from agents.claude_client import claude_client
from agents.schemas import ScheduleSuggestion
from appointments.models import Client, Appointment

class SchedulingAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        """
        System prompt for the Scheduling Agent

        Returns:
            str: The system prompt for the Scheduling Agent
        """

        return (
            "You are a Scheduling Agent. Specialize in appointment scheduling and slot optimization. "
            "Respond with a JSON object containing exactly these fields: "
            '{"client_id": number, "proposed_time": "time", "confidence": number, "reasoning": "explanation"}'
        )

    def infer(self, client_id: int, availability: list = None, preferences: list = None) -> ScheduleSuggestion:
        """
        Suggest optimal appointment time

        Args:
            client_id: int
            availability: list
            preferences: list

        Returns:
            ScheduleSuggestion: A dictionary containing the suggested appointment time

        Raises:
            ValueError: If the client is not found or if the availability or preferences are not found
        """

        if availability is None:
            availability = self.get_available_slots(client_id)
        
        if preferences is None:
            preferences = self.get_client_preferences(client_id)
        
        client_info = self.get_client_info(client_id)
        
        prompt = (
            f"Client {client_info['name']} (ID: {client_id}) is available at {availability[:10]}. "
            f"Preferences: {preferences}. "
            "Suggest the best time slot with confidence."
        )

        output = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text

        try:
            return ScheduleSuggestion.model_validate_json(output)
        except Exception as e:
            raise ValueError(f"No JSON found in response: {e}")

    def get_available_slots(self, client_id: int, days_ahead: int = 14, business_hours: tuple = (9, 17)) -> list:
        """
        Generate available time slots for a client

        Args:
            client_id: int
            days_ahead: int
            business_hours: tuple

        Returns:
            list: A list of available time slots
        """

        client = Client.objects.get(id=client_id)
        clinician = client.clinician
        
        if not clinician:
            return []
        
        # Calculate date range
        start_date = timezone.now().date() + timedelta(days=1)  # Start tomorrow
        end_date = start_date + timedelta(days=days_ahead)
        
        available_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday to Friday
                for hour in range(business_hours[0], business_hours[1]):
                    slot_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                    slot_time = timezone.make_aware(slot_time)
                    
                    # Check if slot is available (no existing appointment)
                    existing = Appointment.objects.filter(
                        clinician=clinician,
                        start_time=slot_time
                    ).exists()
                    
                    if not existing:
                        available_slots.append(slot_time.isoformat())
            
            current_date += timedelta(days=1)
        
        return available_slots

    def get_client_preferences(self, client_id: int) -> list:
        """
        Gather client preferences from memo and appointment history

        Args:
            client_id: int

        Returns:
            list: A list of client preferences
        """

        client = Client.objects.get(id=client_id)
        preferences = []
        
        # Get preferences from memo
        if client.memo:
            preferences.append(client.memo)
        
        # Analyze recent appointment patterns for additional preferences
        from .preference_learner import PreferenceLearner
        preference_learner = PreferenceLearner()
        try:
            learned_prefs = preference_learner.infer(client_id)
            preferences.extend(learned_prefs.learned_preferences)
        except Exception:
            # If preference learning fails, continue with memo only
            pass
        
        return preferences if preferences else ["No specific preferences noted"]

    def get_client_info(self, client_id: int) -> dict:
        """
        Get client information

        Args:
            client_id: int

        Returns:
            dict: A dictionary containing the client information
        """

        client = Client.objects.get(id=client_id)
        return {
            'name': client.full_name,
            'clinician_name': client.clinician.get_full_name() if client.clinician else None
        }
