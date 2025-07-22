"""
Supervisor Agent
Coordinates all sub-agents for the scheduling system
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from .sub_agents import (
    SchedulingAgent,
    AvailabilityOptimizerAgent,
    PreferenceLearnerAgent
)
from .response_models import SupervisorResponse, AgentResponse, AppointmentSuggestion

class SupervisorAgent(BaseAgent):
    """Supervisor agent that coordinates all sub-agents for the scheduling system"""

    def __init__(self):
        super().__init__(
            name="Supervisor Scheduling Agent",
            description="I coordinate specialized sub-agents for appointment management, providing a unified interface for scheduling, optimization, and preference learning."
        )
        
        # Initialize sub-agents
        self.scheduling_agent = SchedulingAgent()
        self.availability_optimizer = AvailabilityOptimizerAgent()
        self.preference_learner = PreferenceLearnerAgent()

    def get_system_prompt(self) -> str:
        return f"""{super().get_system_prompt()}

I coordinate specialized sub-agents for appointment management. I aggregate responses, prioritize suggestions, and provide unified interfaces for external systems."""

    def process_request(self, request_type: str, request_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> SupervisorResponse:
        """
        Process a request by coordinating with relevant sub-agents
        
        Args:
            request_type: Type of request (schedule, optimize, learn_preferences)
            request_data: Request data and parameters
            context: Additional context for the request
            
        Returns:
            Aggregated response from all relevant sub-agents
        """
        sub_agent_responses = []
        all_suggestions = []
        
        try:
            # Route to appropriate sub-agents based on request type
            if request_type == "schedule":
                response = self.scheduling_agent.schedule_appointment(
                    request_data.get("description", ""), 
                    context
                )
                sub_agent_responses.append(response)
                all_suggestions.extend(response.suggestions)
                
            elif request_type == "optimize_availability":
                response = self.availability_optimizer.optimize_therapist_schedule(
                    request_data.get("therapist_profile", {}),
                    request_data.get("current_schedule", {})
                )
                if hasattr(response, 'suggestions'):
                    sub_agent_responses.append(response)
                    all_suggestions.extend(response.suggestions)
                
            elif request_type == "learn_preferences":
                response = self.preference_learner.analyze_therapist_preferences(
                    request_data.get("therapist_id", ""),
                    request_data.get("appointment_data", [])
                )
                if hasattr(response, 'suggestions'):
                    sub_agent_responses.append(response)
                    all_suggestions.extend(response.suggestions)
            
            # Create overall explanation
            overall_explanation = self._create_overall_explanation(sub_agent_responses)
            
            # Determine if confirmation is required
            requires_confirmation = any(response.requires_confirmation for response in sub_agent_responses)
            
            return SupervisorResponse(
                request_type=request_type,
                sub_agent_responses=sub_agent_responses,
                final_suggestions=all_suggestions,
                overall_explanation=overall_explanation,
                requires_confirmation=requires_confirmation
            )
            
        except Exception as e:
            # Return error response
            return SupervisorResponse(
                request_type=request_type,
                sub_agent_responses=[],
                final_suggestions=[],
                overall_explanation=f"Error processing request: {str(e)}",
                requires_confirmation=True
            )

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "supervisor_agent": "active",
            "scheduling_agent": "active",
            "availability_optimizer": "active", 
            "preference_learner": "active"
        }

    def get_available_actions(self) -> Dict[str, List[str]]:
        """Get available actions for each agent"""
        return {
            "supervisor": ["process_request", "get_agent_status", "get_available_actions"],
            "scheduling": ["schedule_appointment", "find_optimal_slots"],
            "availability_optimizer": ["optimize_therapist_schedule", "balance_workload"],
            "preference_learner": ["analyze_therapist_preferences", "update_preferences_from_feedback"]
        }

    def create_context(self, user: Optional[Dict[str, Any]] = None, models: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create context for agent interactions

        Args:
            user: User information dictionary
            models: Dictionary of relevant model data

        Returns:
            Context dictionary
        """
        context = {
            'user': user,
            'models': models or {},
            'environment': 'framework_agnostic'
        }

        if user:
            context['user_info'] = user

        return context

    def _create_overall_explanation(self, sub_agent_responses: List[AgentResponse]) -> str:
        """Create overall explanation from sub-agent responses"""
        if not sub_agent_responses:
            return "No sub-agents were consulted for this request."
        
        explanations = []
        for response in sub_agent_responses:
            explanations.append(f"{response.agent_name}: {response.explanation}")
        
        return " | ".join(explanations) 