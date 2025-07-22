from agents.base import BaseAgent
from agents.claude_client import claude_client
from agents.schemas import PreferenceLearning
from appointments.models import Client, Appointment

class PreferenceLearner(BaseAgent):
    @property
    def system_prompt(self) -> str:
        """
        System prompt for the Preference Learner Agent

        Returns:
            str: The system prompt for the Preference Learner Agent
        """

        return (
            "You are a Preference Learner Agent. Learn and adapt to client and therapist preferences. "
            "Respond with a JSON object containing exactly these fields: "
            '{"client_id": number, "learned_preferences": ["pref1", "pref2"], "reasoning": "explanation"}'
        )

    def infer(self, client_id: int, history: str = None) -> PreferenceLearning:
        """
        Learn client scheduling preferences

        Args:
            client_id: int
            history: str
        
        Returns:
            PreferenceLearning: A dictionary containing the learned preferences

        Raises:
            ValueError: If the client is not found or if the history is not found
        """

        if history is None:
            appointments = self.get_client_appointment_history(client_id)
            patterns = self.analyze_appointment_patterns(appointments)
            client_info = self.get_client_info(client_id)
            
            history_parts = []
            if patterns['recent_schedule']:
                history_parts.append(f"Recent schedule: {', '.join(patterns['recent_schedule'])}")
            
            if client_info['memo']:
                history_parts.append(f"Memo: {client_info['memo']}")
            
            history = f"Client {client_info['name']} has {patterns['total_count']} total appointments. {' '.join(history_parts)}"
        
        prompt = f"Client {client_id} has history: {history}. Learn their scheduling preferences."
        output = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text

        try:
            return PreferenceLearning.model_validate_json(output)
        except Exception as e:
            raise ValueError(f"No JSON found in response: {e}")

    def get_client_appointment_history(self, client_id: int, limit: int = 20) -> list:
        """
        Gather client's appointment history

        Args:
            client_id: int
            limit: int

        Returns:
            list: A list of appointments
        """
        appointments = Appointment.objects.filter(
            client_id=client_id
        ).order_by('-start_time')[:limit]
        
        return list(appointments)

    def analyze_appointment_patterns(self, appointments: list) -> dict:
        """
        Analyze appointment patterns to extract preferences

        Args:
            appointments: list

        Returns:
            dict: A dictionary containing the appointment patterns
        """

        if not appointments:
            return {'patterns': [], 'total_count': 0, 'recent_schedule': []}
        
        day_counts = {}
        time_counts = {}
        recent_schedule = []
        
        for appt in appointments:
            day_name = appt.start_time.strftime('%A')
            time_str = appt.start_time.strftime('%H:%M')
            
            day_counts[day_name] = day_counts.get(day_name, 0) + 1
            time_counts[time_str] = time_counts.get(time_str, 0) + 1
            
            if len(recent_schedule) < 10:
                recent_schedule.append(f"{day_name} at {time_str}")
        
        preferred_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        preferred_times = sorted(time_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'patterns': {
                'preferred_days': preferred_days,
                'preferred_times': preferred_times
            },
            'total_count': len(appointments),
            'recent_schedule': recent_schedule
        }

    def get_client_info(self, client_id: int) -> dict:
        """
        Get client information and memo

        Args:
            client_id: int

        Returns:
            dict: A dictionary containing the client information and memo
        """

        client = Client.objects.get(id=client_id)
        return {
            'name': client.full_name,
            'memo': client.memo,
            'clinician_name': client.clinician.get_full_name() if client.clinician else None
        }
