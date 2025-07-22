from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User

from agents.base import BaseAgent
from agents.claude_client import claude_client
from agents.schemas import AvailabilityOptimization
from appointments.models import Appointment

class AvailabilityOptimizer(BaseAgent):
    @property
    def system_prompt(self) -> str:
        """
        System prompt for the Availability Optimizer Agent

        Returns:
            str: The system prompt for the Availability Optimizer Agent
        """

        return (
            "You are an Availability Optimizer Agent. Optimize therapist availability and workload distribution. "
            "Respond with a JSON object containing exactly these fields: "
            '{"clinician_id": number, "suggested_availability": ["time1", "time2"], "reasoning": "explanation"}'
        )

    def infer(self, clinician_id: int, current_schedule: list = None) -> AvailabilityOptimization:
        """
        Optimize clinician availability

        Args:
            clinician_id: int
            current_schedule: list

        Returns:
            AvailabilityOptimization: A dictionary containing the optimized availability for the clinician

        Raises:
            ValueError: If the clinician is not found
        """
        if current_schedule is None:
            current_schedule = self.get_clinician_schedule(clinician_id)
        
        workload_stats = self.get_clinician_workload_stats(clinician_id)
        
        prompt = (
            f"Clinician {workload_stats['clinician_name']} (ID: {clinician_id}) has "
            f"{workload_stats['weekly_count']} appointments this week and "
            f"{workload_stats['monthly_count']} this month. "
            f"Current schedule: {current_schedule}. "
            "Suggest optimized availability."
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
            return AvailabilityOptimization.model_validate_json(output)
        except Exception as e:
            raise ValueError(f"No JSON found in response: {e}")

    def get_clinician_schedule(self, clinician_id: int, days_ahead: int = 7) -> list:
        """
        Gather clinician's current schedule for the specified period

        Args:
            clinician_id: int
            days_ahead: int

        Returns:
            list: A list of appointments in the specified period
        """
        clinician = User.objects.get(id=clinician_id)
        
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=days_ahead)
        
        appointments = Appointment.objects.filter(
            clinician=clinician,
            start_time__gte=start_date,
            start_time__lt=end_date
        ).order_by('start_time')
        
        # Convert to ISO format
        schedule = [appt.start_time.isoformat() for appt in appointments]
        
        return schedule

    def get_clinician_workload_stats(self, clinician_id: int) -> dict:
        """
        Gather workload statistics for the clinician
        
        Args:
            clinician_id: int

        Returns:
            dict: A dictionary containing the workload statistics for the clinician
        """
        clinician = User.objects.get(id=clinician_id)

        start_of_week = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_week - timedelta(days=start_of_week.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        
        weekly_appointments = Appointment.objects.filter(
            clinician=clinician,
            start_time__gte=start_of_week,
            start_time__lt=end_of_week
        ).count()
        
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_appointments = Appointment.objects.filter(
            clinician=clinician,
            start_time__gte=start_of_month
        ).count()
        
        return {
            'weekly_count': weekly_appointments,
            'monthly_count': monthly_appointments,
            'clinician_name': clinician.get_full_name()
        }
