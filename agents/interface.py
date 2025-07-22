"""
Agent Interface
Framework-agnostic interface for the supervisor agent system
"""

from typing import Dict, Any, Optional, List
from .supervisor_agent import SupervisorAgent


class AgentInterface:
    """
    Framework-agnostic interface for the supervisor agent system.
    This can be easily integrated with Django, Flask, FastAPI, or any other framework.
    """

    def __init__(self):
        self.supervisor = SupervisorAgent()

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return self.supervisor.get_agent_status()

    def get_available_actions(self) -> Dict[str, List[str]]:
        """Get available actions for each agent"""
        return self.supervisor.get_available_actions()

    def schedule_appointment(self, request_data: Dict[str, Any], 
                           user: Optional[Dict[str, Any]] = None,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule an appointment using the supervisor agent
        
        Args:
            request_data: Scheduling request data
            user: User information dictionary
            context: Additional context data
            
        Returns:
            Scheduling response from agent
        """
        # Create context
        agent_context = self._create_context(user, context)
        
        return self.supervisor.process_request('schedule', request_data, agent_context)
    
    def optimize_availability(self, request_data: Dict[str, Any], 
                            user: Optional[Dict[str, Any]] = None,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize availability using the supervisor agent
        
        Args:
            request_data: Availability optimization request data
            user: User information dictionary
            context: Additional context data
            
        Returns:
            Optimization response from agent
        """
        agent_context = self._create_context(user, context)
        
        return self.supervisor.process_request('optimize_availability', request_data, agent_context)
    
    def learn_preferences(self, request_data: Dict[str, Any], 
                         user: Optional[Dict[str, Any]] = None,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Learn and adapt preferences using the supervisor agent
        
        Args:
            request_data: Preference learning request data
            user: User information dictionary
            context: Additional context data
            
        Returns:
            Preference learning response from agent
        """
        agent_context = self._create_context(user, context)
        
        return self.supervisor.process_request('learn_preferences', request_data, agent_context)
    
    def _create_context(self, user: Optional[Dict[str, Any]] = None, 
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create context for agent interactions"""
        agent_context = self.supervisor.create_context(user)
        
        # Merge additional context if provided
        if context:
            agent_context.update(context)
        
        return agent_context


# Convenience functions for direct use
def get_agent_status() -> Dict[str, Any]:
    """Get status of all agents"""
    interface = AgentInterface()
    return interface.get_agent_status()


def get_available_actions() -> Dict[str, List[str]]:
    """Get available actions for each agent"""
    interface = AgentInterface()
    return interface.get_available_actions()


def schedule_appointment(request_data: Dict[str, Any], 
                        user: Optional[Dict[str, Any]] = None,
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Schedule an appointment"""
    interface = AgentInterface()
    return interface.schedule_appointment(request_data, user, context)


def optimize_availability(request_data: Dict[str, Any], 
                         user: Optional[Dict[str, Any]] = None,
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Optimize availability"""
    interface = AgentInterface()
    return interface.optimize_availability(request_data, user, context)


def learn_preferences(request_data: Dict[str, Any], 
                     user: Optional[Dict[str, Any]] = None,
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Learn and adapt preferences"""
    interface = AgentInterface()
    return interface.learn_preferences(request_data, user, context) 