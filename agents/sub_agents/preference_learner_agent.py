"""
Preference Learner Agent
Learns and adapts to client and therapist preferences
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from ..base_agent import BaseAgent
from ..response_models import AgentResponse, AppointmentSuggestion

class PreferenceLearnerAgent(BaseAgent):
    """Agent specialized in learning and adapting to preferences"""
    
    def __init__(self):
        super().__init__(
            name="Preference Learner Agent",
            description="""I specialize in learning and adapting to client and therapist preferences. 
I can:
- Analyze scheduling patterns and preferences over time
- Learn from feedback and satisfaction data
- Adapt recommendations based on learned preferences
- Predict future preferences and needs
- Optimize scheduling based on historical patterns
- Identify preference changes and trends
- Suggest personalized scheduling strategies
- Improve satisfaction through preference matching"""
        )
    
    def get_system_prompt(self) -> str:
        return f"""{super().get_system_prompt()}

When learning preferences, I:
1. Analyze historical scheduling patterns and feedback
2. Identify preference trends and changes over time
3. Learn from satisfaction data and outcomes
4. Adapt recommendations based on learned patterns
5. Predict future preferences and needs
6. Optimize scheduling strategies based on preferences
7. Improve satisfaction through better preference matching

I return structured JSON responses with appointment suggestions."""

    def analyze_therapist_preferences(self, therapist_id: str, appointment_data: List[Dict[str, Any]]) -> AgentResponse:
        """
        Analyze therapist preferences from appointment data
        
        Args:
            therapist_id: Therapist identifier
            appointment_data: Historical appointment and satisfaction data
            
        Returns:
            Structured preference analysis response
        """
        context = {
            "therapist_id": therapist_id,
            "appointment_data": appointment_data,
            "task": "analyze_preferences",
            "response_format": "structured_json"
        }
        
        request = f"Analyze preferences for therapist {therapist_id} based on appointment patterns."
        return self._process_preference_request(request, context)
    
    def update_preferences_from_feedback(self, new_data: Dict[str, Any], current_understanding: Dict[str, Any]) -> AgentResponse:
        """
        Update preferences based on new feedback and data
        
        Args:
            new_data: New feedback and preference data
            current_understanding: Current understanding of preferences
            
        Returns:
            Structured preference update response
        """
        context = {
            "new_data": new_data,
            "current_understanding": current_understanding,
            "task": "update_preferences",
            "response_format": "structured_json"
        }
        
        request = "Update preferences based on new feedback and data."
        return self._process_preference_request(request, context)
    
    def predict_future_preferences(self, historical_patterns: List[Dict[str, Any]], external_factors: Dict[str, Any]) -> AgentResponse:
        """
        Predict future preferences based on patterns and factors
        
        Args:
            historical_patterns: Historical preference patterns
            external_factors: External factors affecting preferences
            
        Returns:
            Structured preference prediction response
        """
        context = {
            "historical_patterns": historical_patterns,
            "external_factors": external_factors,
            "task": "predict_preferences",
            "response_format": "structured_json"
        }
        
        request = "Predict future preferences based on historical patterns and external factors."
        return self._process_preference_request(request, context)
    
    def suggest_preference_optimization(self, current_preferences: Dict[str, Any], performance_metrics: Dict[str, Any]) -> AgentResponse:
        """
        Suggest optimizations based on learned preferences
        
        Args:
            current_preferences: Current preference understanding
            performance_metrics: Performance and satisfaction metrics
            
        Returns:
            Structured optimization suggestion response
        """
        context = {
            "current_preferences": current_preferences,
            "performance_metrics": performance_metrics,
            "task": "optimize_preferences",
            "response_format": "structured_json"
        }
        
        request = "Suggest optimizations based on learned preferences and performance metrics."
        return self._process_preference_request(request, context)
    
    def _process_preference_request(self, request: str, context: Dict[str, Any]) -> AgentResponse:
        """Process preference request and return structured response"""
        # Get AI response
        ai_response = self.chat(request, context)
        
        # Parse the response into structured format
        try:
            structured_data = self._parse_ai_response(ai_response)
            return self._build_structured_response(structured_data, context)
        except Exception as e:
            return self._build_fallback_response(request, ai_response, context)
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response to extract structured data"""
        try:
            # Try to find JSON block in the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = ai_response[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        # If no JSON found, create structured data from text
        return self._extract_structured_data_from_text(ai_response)
    
    def _extract_structured_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured data from natural language text"""
        data = {
            "suggestions": [],
            "explanation": text,
            "requires_confirmation": True
        }
        
        # Try to extract preference information from text
        if "preference" in text.lower() or "pattern" in text.lower():
            # Create a placeholder suggestion
            data["suggestions"].append({
                "start_time": datetime.now(),
                "duration_in_minutes": 50,
                "client_id": 1,  # Placeholder
                "clinician_id": 1,  # Placeholder
                "confidence": 0.7,
                "reason": "Suggested based on preference analysis"
            })
        
        return data
    
    def _build_structured_response(self, data: Dict[str, Any], context: Dict[str, Any]) -> AgentResponse:
        """Build structured response from parsed data"""
        suggestions = []
        
        for suggestion_data in data.get("suggestions", []):
            try:
                # Convert string datetime to datetime object if needed
                start_time = suggestion_data.get("start_time")
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                
                suggestion = AppointmentSuggestion(
                    start_time=start_time,
                    duration_in_minutes=suggestion_data.get("duration_in_minutes", 50),
                    client_id=suggestion_data.get("client_id"),
                    clinician_id=suggestion_data.get("clinician_id"),
                    confidence=suggestion_data.get("confidence", 0.7),
                    reason=suggestion_data.get("reason", "Preference learning recommendation")
                )
                suggestions.append(suggestion)
            except Exception as e:
                # Skip invalid suggestions
                continue
        
        return AgentResponse(
            agent_name="PreferenceLearnerAgent",
            suggestions=suggestions,
            explanation=data.get("explanation", "Preference analysis completed"),
            requires_confirmation=data.get("requires_confirmation", True)
        )
    
    def _build_fallback_response(self, request: str, ai_response: str, context: Dict[str, Any]) -> AgentResponse:
        """Build fallback response when parsing fails"""
        return AgentResponse(
            agent_name="PreferenceLearnerAgent",
            suggestions=[],
            explanation=f"AI Analysis: {ai_response}",
            requires_confirmation=True
        ) 