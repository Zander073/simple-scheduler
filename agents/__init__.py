"""
Calendar Management Agents Package
Specialized agents for different calendar management use cases
"""

from .base_agent import BaseAgent
from .supervisor_agent import SupervisorAgent
from .interface import AgentInterface
from .sub_agents import (
    SchedulingAgent,
    AvailabilityOptimizerAgent,
    PreferenceLearnerAgent
)

# Convenience imports
from .interface import (
    get_agent_status,
    get_available_actions,
    schedule_appointment,
    optimize_availability,
    learn_preferences,
    handle_complex_request
)

__all__ = [
    'BaseAgent',
    'SupervisorAgent',
    'AgentInterface',
    'SchedulingAgent',
    'AvailabilityOptimizerAgent',
    'PreferenceLearnerAgent',
    # Convenience functions
    'get_agent_status',
    'get_available_actions',
    'schedule_appointment',
    'optimize_availability',
    'learn_preferences',
    'handle_complex_request'
] 