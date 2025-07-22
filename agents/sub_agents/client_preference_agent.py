"""
Client Preference Agent
Analyzes client preferences and ranks time slots by acceptance probability
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from collections import defaultdict, Counter
from django.utils import timezone
from django.db.models import Q

from ..base_agent import BaseAgent
from ..response_models import AgentResponse, AppointmentSuggestion
from appointments.models import Client, Appointment


class ClientPreferenceAgent(BaseAgent):
    """Agent specialized in analyzing client scheduling preferences and ranking time slots"""
    
    def __init__(self):
        super().__init__(
            name="Client Preference Agent",
            description="""I specialize in analyzing client scheduling preferences and ranking time slots by acceptance probability. 
I can:
- Parse and understand client preference text from memo field (e.g., 'tuesday mornings or Fridays at 2PM')
- Analyze appointment history to identify patterns and trends
- Learn from the last 4-6 weeks of appointment data
- Rank time slots by probability of client acceptance
- Consider both explicit preferences and behavioral patterns
- Provide top 3 time slots with highest acceptance probability
- Adapt recommendations based on recent scheduling behavior"""
        )
    
    def get_system_prompt(self) -> str:
        return f"""{super().get_system_prompt()}

When analyzing client preferences, I:
1. Parse explicit preference text from memo field for time patterns
2. Analyze recent appointment history (last 4-6 weeks)
3. Identify day-of-week and time-of-day patterns
4. Consider both stated preferences and behavioral patterns
5. Rank time slots by acceptance probability
6. Provide top 3 recommendations with confidence scores
7. Explain reasoning behind each recommendation

IMPORTANT: You MUST respond with valid JSON in this exact format:
{{
    "ranked_slots": [
        {{
            "start_time": "2024-01-15T10:00:00",
            "acceptance_probability": 0.95,
            "reason": "Matches client's stated preference for Tuesday mornings"
        }},
        {{
            "start_time": "2024-01-15T14:00:00", 
            "acceptance_probability": 0.85,
            "reason": "Consistent with recent Friday afternoon appointments"
        }},
        {{
            "start_time": "2024-01-15T09:00:00",
            "acceptance_probability": 0.75,
            "reason": "Morning preference observed in last 6 weeks"
        }}
    ],
    "analysis": {{
        "stated_preferences": ["Tuesday mornings", "Friday 2PM"],
        "behavioral_patterns": ["Morning appointments preferred", "Tuesday is most common day"],
        "confidence_level": "high"
    }},
    "explanation": "Analysis based on stated preferences and recent appointment history"
}}

Do not include any text before or after the JSON. Only return the JSON object."""

    def analyze_client_preferences(self, client_id: int, available_slots: List[datetime]) -> AgentResponse:
        """
        Analyze client preferences and rank available time slots
        
        Args:
            client_id: Client identifier
            available_slots: List of available time slots to rank
            
        Returns:
            Structured response with top 3 ranked slots
        """
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return self._build_error_response(f"Client with id {client_id} not found")
        
        # Get client data from memo field
        stated_preferences = self._parse_stated_preferences(client.memo)
        behavioral_patterns = self._analyze_appointment_history(client)
        
        # Rank the available slots
        ranked_slots = self._rank_time_slots(available_slots, stated_preferences, behavioral_patterns)
        
        # Get top 3 slots
        top_slots = ranked_slots[:3]
        
        # Build response
        suggestions = []
        for slot in top_slots:
            suggestion = AppointmentSuggestion(
                start_time=slot['start_time'],
                duration_in_minutes=50,  # Default duration
                client_id=client_id,
                clinician_id=1,  # Will be set by caller
                confidence=slot['acceptance_probability'],
                reason=slot['reason']
            )
            suggestions.append(suggestion)
        
        return AgentResponse(
            agent_name="ClientPreferenceAgent",
            suggestions=suggestions,
            explanation=f"Top 3 time slots ranked by client preference analysis for {client.full_name}",
            requires_confirmation=True
        )

    def _parse_stated_preferences(self, memo_text: str) -> Dict[str, Any]:
        """
        Parse client's stated preferences from memo field
        
        Args:
            memo_text: Raw memo text (e.g., "tuesday mornings or Fridays at 2PM")
            
        Returns:
            Structured preference data
        """
        if not memo_text:
            return {}
        
        preferences = {
            'days_of_week': [],
            'time_periods': [],
            'specific_times': [],
            'raw_text': memo_text.lower()
        }
        
        # Day of week patterns
        day_patterns = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tues': 1, 'tue': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thurs': 3, 'thu': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        # Time period patterns
        time_periods = {
            'morning': (6, 12),
            'afternoon': (12, 17),
            'evening': (17, 21),
            'night': (21, 24)
        }
        
        # Extract days
        for day_name, day_num in day_patterns.items():
            if day_name in memo_text.lower():
                preferences['days_of_week'].append(day_num)
        
        # Extract time periods
        for period, (start_hour, end_hour) in time_periods.items():
            if period in memo_text.lower():
                preferences['time_periods'].append((start_hour, end_hour))
        
        # Extract specific times (e.g., "2PM", "9A")
        time_pattern = r'(\d{1,2})(?::\d{2})?\s*(am|pm|a|p)'
        matches = re.findall(time_pattern, memo_text.lower())
        for match in matches:
            hour = int(match[0])
            period = match[1]
            
            # Convert to 24-hour format
            if period in ['pm', 'p'] and hour != 12:
                hour += 12
            elif period in ['am', 'a'] and hour == 12:
                hour = 0
            
            preferences['specific_times'].append(hour)
        
        return preferences

    def _analyze_appointment_history(self, client: Client) -> Dict[str, Any]:
        """
        Analyze client's appointment history for behavioral patterns
        
        Args:
            client: Client object
            
        Returns:
            Behavioral pattern analysis
        """
        # Get appointments from last 6 weeks
        six_weeks_ago = timezone.now() - timedelta(weeks=6)
        recent_appointments = Appointment.objects.filter(
            client=client,
            start_time__gte=six_weeks_ago
        ).order_by('start_time')
        
        patterns = {
            'days_of_week': [],
            'time_periods': [],
            'hour_distribution': [],
            'total_appointments': recent_appointments.count(),
            'most_common_day': None,
            'most_common_hour': None,
            'morning_preference': False,
            'afternoon_preference': False,
            'evening_preference': False
        }
        
        if not recent_appointments.exists():
            return patterns
        
        # Analyze each appointment
        for appointment in recent_appointments:
            # Day of week (0=Monday, 6=Sunday)
            day_of_week = appointment.start_time.weekday()
            patterns['days_of_week'].append(day_of_week)
            
            # Hour of day
            hour = appointment.start_time.hour
            patterns['hour_distribution'].append(hour)
            
            # Time period
            if 6 <= hour < 12:
                patterns['time_periods'].append('morning')
            elif 12 <= hour < 17:
                patterns['time_periods'].append('afternoon')
            elif 17 <= hour < 21:
                patterns['time_periods'].append('evening')
            else:
                patterns['time_periods'].append('night')
        
        # Calculate most common patterns
        if patterns['days_of_week']:
            day_counter = Counter(patterns['days_of_week'])
            patterns['most_common_day'] = day_counter.most_common(1)[0][0]
        
        if patterns['hour_distribution']:
            hour_counter = Counter(patterns['hour_distribution'])
            patterns['most_common_hour'] = hour_counter.most_common(1)[0][0]
        
        # Determine time period preferences
        period_counter = Counter(patterns['time_periods'])
        if period_counter:
            most_common_period = period_counter.most_common(1)[0][0]
            if most_common_period == 'morning':
                patterns['morning_preference'] = True
            elif most_common_period == 'afternoon':
                patterns['afternoon_preference'] = True
            elif most_common_period == 'evening':
                patterns['evening_preference'] = True
        
        return patterns

    def _rank_time_slots(self, available_slots: List[datetime], 
                        stated_preferences: Dict[str, Any], 
                        behavioral_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank time slots by acceptance probability
        
        Args:
            available_slots: List of available time slots
            stated_preferences: Parsed stated preferences
            behavioral_patterns: Behavioral pattern analysis
            
        Returns:
            List of ranked slots with probability scores
        """
        ranked_slots = []
        
        for slot in available_slots:
            probability = self._calculate_acceptance_probability(
                slot, stated_preferences, behavioral_patterns
            )
            
            reason = self._generate_reason(slot, stated_preferences, behavioral_patterns)
            
            ranked_slots.append({
                'start_time': slot,
                'acceptance_probability': probability,
                'reason': reason
            })
        
        # Sort by probability (highest first)
        ranked_slots.sort(key=lambda x: x['acceptance_probability'], reverse=True)
        
        return ranked_slots

    def _calculate_acceptance_probability(self, slot: datetime, 
                                        stated_preferences: Dict[str, Any], 
                                        behavioral_patterns: Dict[str, Any]) -> float:
        """
        Calculate acceptance probability for a time slot
        
        Args:
            slot: Time slot to evaluate
            stated_preferences: Parsed stated preferences
            behavioral_patterns: Behavioral pattern analysis
            
        Returns:
            Probability score between 0.0 and 1.0
        """
        probability = 0.5  # Base probability
        
        # Check stated preferences
        if stated_preferences:
            # Day of week match
            if slot.weekday() in stated_preferences.get('days_of_week', []):
                probability += 0.2
            
            # Time period match
            hour = slot.hour
            for start_hour, end_hour in stated_preferences.get('time_periods', []):
                if start_hour <= hour < end_hour:
                    probability += 0.15
                    break
            
            # Specific time match
            if hour in stated_preferences.get('specific_times', []):
                probability += 0.25
        
        # Check behavioral patterns
        if behavioral_patterns:
            # Day of week pattern
            if (behavioral_patterns.get('most_common_day') is not None and 
                slot.weekday() == behavioral_patterns['most_common_day']):
                probability += 0.15
            
            # Hour pattern
            if (behavioral_patterns.get('most_common_hour') is not None and 
                abs(slot.hour - behavioral_patterns['most_common_hour']) <= 1):
                probability += 0.1
            
            # Time period preference
            hour = slot.hour
            if (6 <= hour < 12 and behavioral_patterns.get('morning_preference')):
                probability += 0.1
            elif (12 <= hour < 17 and behavioral_patterns.get('afternoon_preference')):
                probability += 0.1
            elif (17 <= hour < 21 and behavioral_patterns.get('evening_preference')):
                probability += 0.1
        
        # Cap probability at 1.0
        return min(probability, 1.0)

    def _generate_reason(self, slot: datetime, 
                        stated_preferences: Dict[str, Any], 
                        behavioral_patterns: Dict[str, Any]) -> str:
        """
        Generate explanation for why a slot was ranked
        
        Args:
            slot: Time slot
            stated_preferences: Parsed stated preferences
            behavioral_patterns: Behavioral pattern analysis
            
        Returns:
            Explanation string
        """
        reasons = []
        
        # Day of week
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = day_names[slot.weekday()]
        
        # Check stated preferences
        if stated_preferences:
            if slot.weekday() in stated_preferences.get('days_of_week', []):
                reasons.append(f"Matches stated preference for {day_name}")
            
            hour = slot.hour
            for start_hour, end_hour in stated_preferences.get('time_periods', []):
                if start_hour <= hour < end_hour:
                    period_name = {6: 'morning', 12: 'afternoon', 17: 'evening'}.get(start_hour, '')
                    if period_name:
                        reasons.append(f"Matches stated preference for {period_name}")
                    break
            
            if hour in stated_preferences.get('specific_times', []):
                reasons.append(f"Matches stated preference for {hour}:00")
        
        # Check behavioral patterns
        if behavioral_patterns:
            if (behavioral_patterns.get('most_common_day') is not None and 
                slot.weekday() == behavioral_patterns['most_common_day']):
                reasons.append(f"Consistent with recent {day_name} appointments")
            
            if (behavioral_patterns.get('most_common_hour') is not None and 
                abs(slot.hour - behavioral_patterns['most_common_hour']) <= 1):
                reasons.append(f"Similar to preferred appointment time")
            
            hour = slot.hour
            if (6 <= hour < 12 and behavioral_patterns.get('morning_preference')):
                reasons.append("Consistent with morning preference")
            elif (12 <= hour < 17 and behavioral_patterns.get('afternoon_preference')):
                reasons.append("Consistent with afternoon preference")
            elif (17 <= hour < 21 and behavioral_patterns.get('evening_preference')):
                reasons.append("Consistent with evening preference")
        
        if not reasons:
            return f"Available {day_name} slot"
        
        return "; ".join(reasons)

    def _build_error_response(self, error_message: str) -> AgentResponse:
        """Build error response"""
        return AgentResponse(
            agent_name="ClientPreferenceAgent",
            suggestions=[],
            explanation=f"Error: {error_message}",
            requires_confirmation=True
        )

    def get_preference_analysis(self, client_id: int) -> Dict[str, Any]:
        """
        Get detailed preference analysis for a client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Detailed preference analysis
        """
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return {"error": f"Client with id {client_id} not found"}
        
        stated_preferences = self._parse_stated_preferences(client.memo)
        behavioral_patterns = self._analyze_appointment_history(client)
        
        return {
            "client_name": client.full_name,
            "stated_preferences": stated_preferences,
            "behavioral_patterns": behavioral_patterns,
            "analysis_summary": self._generate_analysis_summary(stated_preferences, behavioral_patterns)
        }

    def _generate_analysis_summary(self, stated_preferences: Dict[str, Any], 
                                 behavioral_patterns: Dict[str, Any]) -> str:
        """Generate a summary of the preference analysis"""
        summary_parts = []
        
        if stated_preferences.get('days_of_week'):
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            days = [day_names[day] for day in stated_preferences['days_of_week']]
            summary_parts.append(f"Stated preference for: {', '.join(days)}")
        
        if stated_preferences.get('time_periods'):
            periods = []
            for start_hour, end_hour in stated_preferences['time_periods']:
                if start_hour == 6:
                    periods.append('mornings')
                elif start_hour == 12:
                    periods.append('afternoons')
                elif start_hour == 17:
                    periods.append('evenings')
            summary_parts.append(f"Preferred time periods: {', '.join(periods)}")
        
        if behavioral_patterns.get('total_appointments', 0) > 0:
            summary_parts.append(f"Recent appointment pattern: {behavioral_patterns['total_appointments']} appointments in last 6 weeks")
            
            if behavioral_patterns.get('most_common_day') is not None:
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                most_common = day_names[behavioral_patterns['most_common_day']]
                summary_parts.append(f"Most common day: {most_common}")
            
            if behavioral_patterns.get('morning_preference'):
                summary_parts.append("Shows preference for morning appointments")
            elif behavioral_patterns.get('afternoon_preference'):
                summary_parts.append("Shows preference for afternoon appointments")
            elif behavioral_patterns.get('evening_preference'):
                summary_parts.append("Shows preference for evening appointments")
        
        if not summary_parts:
            return "No clear preference patterns identified"
        
        return "; ".join(summary_parts) 