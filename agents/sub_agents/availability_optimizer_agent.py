"""
Availability Optimizer Agent
Optimizes therapist availability and workload distribution
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from ..base_agent import BaseAgent
from ..response_models import AgentResponse, AppointmentSuggestion

class AvailabilityOptimizerAgent(BaseAgent):
    """Agent specialized in optimizing therapist availability and workload"""
    
    def __init__(self):
        super().__init__(
            name="Availability Optimizer Agent",
            description="I optimize therapist schedules, balance workloads, predict demand patterns, and maximize efficiency while maintaining quality."
        )
    
    def get_system_prompt(self) -> str:
        return f"""{super().get_system_prompt()}

I optimize therapist availability and workload distribution. I analyze efficiency patterns, balance workloads, predict demand, and suggest optimal schedules."""

    def optimize_therapist_schedule(self, therapist_profile: Dict[str, Any], current_schedule: Dict[str, Any]) -> AgentResponse:
        """
        Optimize a therapist's schedule for maximum efficiency
        
        Args:
            therapist_profile: Therapist's preferences and constraints
            current_schedule: Current schedule configuration
            
        Returns:
            Structured optimization response with appointment suggestions
        """
        context = {
            "therapist_profile": therapist_profile,
            "current_schedule": current_schedule,
            "task": "optimize_therapist_schedule",
            "response_format": "structured_json"
        }
        
        request = "Optimize this therapist's schedule for maximum efficiency and satisfaction."
        return self._process_optimization_request(request, context)
    
    def balance_workload(self, therapists: List[Dict[str, Any]], demand_forecast: Dict[str, Any]) -> AgentResponse:
        """
        Balance workload across multiple therapists
        
        Args:
            therapists: List of therapist profiles and current workloads
            demand_forecast: Predicted demand patterns
            
        Returns:
            Structured workload balancing response
        """
        context = {
            "therapists": therapists,
            "demand_forecast": demand_forecast,
            "task": "balance_workload",
            "response_format": "structured_json"
        }
        
        request = "Suggest how to balance workload across all therapists based on demand forecast."
        return self._process_optimization_request(request, context)
    
    def predict_demand_patterns(self, historical_data: List[Dict[str, Any]], external_factors: Dict[str, Any]) -> AgentResponse:
        """
        Predict demand patterns to optimize availability
        
        Args:
            historical_data: Historical scheduling and demand data
            external_factors: External factors affecting demand (seasons, events, etc.)
            
        Returns:
            Structured demand prediction response
        """
        context = {
            "historical_data": historical_data,
            "external_factors": external_factors,
            "task": "predict_demand",
            "response_format": "structured_json"
        }
        
        request = "Analyze historical data and predict demand patterns to optimize therapist availability."
        return self._process_optimization_request(request, context)
    
    def suggest_break_optimization(self, current_breaks: List[Dict[str, Any]], therapist_preferences: Dict[str, Any]) -> AgentResponse:
        """
        Optimize break times and admin periods
        
        Args:
            current_breaks: Current break schedule
            therapist_preferences: Therapist's break preferences
            
        Returns:
            Structured break optimization response
        """
        context = {
            "current_breaks": current_breaks,
            "therapist_preferences": therapist_preferences,
            "task": "optimize_breaks",
            "response_format": "structured_json"
        }
        
        request = "Optimize break times and admin periods for maximum productivity and satisfaction."
        return self._process_optimization_request(request, context)
    
    def recommend_availability_changes(self, current_availability: Dict[str, Any], performance_metrics: Dict[str, Any]) -> AgentResponse:
        """
        Recommend changes to therapist availability based on performance
        
        Args:
            current_availability: Current availability schedule
            performance_metrics: Performance and satisfaction metrics
            
        Returns:
            Structured availability recommendation response
        """
        context = {
            "current_availability": current_availability,
            "performance_metrics": performance_metrics,
            "task": "recommend_changes",
            "response_format": "structured_json"
        }
        
        request = "Recommend changes to therapist availability based on performance metrics and satisfaction."
        return self._process_optimization_request(request, context)
    
    def _process_optimization_request(self, request: str, context: Dict[str, Any]) -> AgentResponse:
        """Process optimization request and return structured response"""
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
        
        # Try to extract optimization information from text
        if "optimize" in text.lower() or "schedule" in text.lower():
            # Create a placeholder suggestion
            data["suggestions"].append({
                "start_time": datetime.now(),
                "duration_in_minutes": 50,
                "client_id": 1,  # Placeholder
                "clinician_id": 1,  # Placeholder
                "confidence": 0.7,
                "reason": "Suggested based on optimization analysis"
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
                    reason=suggestion_data.get("reason", "Optimization recommendation")
                )
                suggestions.append(suggestion)
            except Exception as e:
                # Skip invalid suggestions
                continue
        
        return AgentResponse(
            agent_name="AvailabilityOptimizerAgent",
            suggestions=suggestions,
            explanation=data.get("explanation", "Optimization analysis completed"),
            requires_confirmation=data.get("requires_confirmation", True)
        )
    
    def _build_fallback_response(self, request: str, ai_response: str, context: Dict[str, Any]) -> AgentResponse:
        """Build fallback response when parsing fails"""
        return AgentResponse(
            agent_name="AvailabilityOptimizerAgent",
            suggestions=[],
            explanation=f"AI Analysis: {ai_response}",
            requires_confirmation=True
        ) 