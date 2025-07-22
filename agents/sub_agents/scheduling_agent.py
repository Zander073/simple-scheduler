"""
Scheduling Agent
Handles appointment scheduling and slot optimization
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from ..base_agent import BaseAgent
from ..response_models import AgentResponse, AppointmentSuggestion

class SchedulingAgent(BaseAgent):
    """Agent specialized in appointment scheduling and slot optimization"""
    
    def __init__(self):
        super().__init__(
            name="Scheduling Agent",
            description="I find optimal appointment slots, consider preferences and availability, and suggest alternative times when needed."
        )
    
    def get_system_prompt(self) -> str:
        return f"""{super().get_system_prompt()}

I specialize in appointment scheduling and slot optimization. I analyze requests, consider preferences and availability, and suggest optimal time slots with confidence levels."""

    def schedule_appointment(self, request: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Handle a scheduling request and return structured response
        
        Args:
            request: Natural language scheduling request
            context: Calendar context, preferences, availability
            
        Returns:
            Structured scheduling response with suggestions
        """
        # Create enhanced context for structured response
        enhanced_context = {
            "request": request,
            "context": context or {},
            "task": "schedule_appointment",
            "response_format": "structured_json"
        }
        
        # Get AI response
        ai_response = self.chat(request, enhanced_context)
        
        # Parse the response into structured format
        try:
            structured_data = self._parse_ai_response(ai_response)
            return self._build_structured_response(structured_data, context)
        except Exception as e:
            # Fallback to basic response if parsing fails
            return self._build_fallback_response(request, ai_response, context)
    
    def find_optimal_slots(self, preferences: Dict[str, Any], availability: List[Dict[str, Any]]) -> AgentResponse:
        """
        Find optimal appointment slots based on preferences and availability
        
        Args:
            preferences: Client and therapist preferences
            availability: Available time slots
            
        Returns:
            Structured response with optimal slot suggestions
        """
        context = {
            "preferences": preferences,
            "available_slots": availability,
            "task": "find_optimal_slots",
            "response_format": "structured_json"
        }
        
        request = "Find the best appointment slots based on the provided preferences and availability."
        return self.schedule_appointment(request, context)
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response to extract structured data"""
        # Look for JSON in the response
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
        
        # Try to extract appointment information from text
        # This is a basic implementation - you'd want more sophisticated parsing
        if "schedule" in text.lower() or "appointment" in text.lower():
            # Create a placeholder suggestion
            data["suggestions"].append({
                "start_time": datetime.now() + timedelta(days=1),
                "duration_in_minutes": 50,
                "client_id": 1,  # Placeholder
                "clinician_id": 1,  # Placeholder
                "confidence": 0.7,
                "reason": "Suggested based on AI analysis"
            })
        
        return data
    
    def _build_structured_response(self, data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> AgentResponse:
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
                    reason=suggestion_data.get("reason", "Scheduling recommendation")
                )
                suggestions.append(suggestion)
            except Exception as e:
                # Skip invalid suggestions
                continue
        
        return AgentResponse(
            agent_name="SchedulingAgent",
            suggestions=suggestions,
            explanation=data.get("explanation", "Scheduling analysis completed"),
            requires_confirmation=data.get("requires_confirmation", True)
        )
    
    def _build_fallback_response(self, request: str, ai_response: str, context: Optional[Dict[str, Any]]) -> AgentResponse:
        """Build fallback response when parsing fails"""
        return AgentResponse(
            agent_name="SchedulingAgent",
            suggestions=[],
            explanation=f"AI Analysis: {ai_response}",
            requires_confirmation=True
        ) 