"""
Simple Structured Response Models for Agents
Basic Pydantic models for agent responses that align with Django Appointment model
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class AppointmentSuggestion(BaseModel):
    """Simple appointment suggestion with core attributes"""
    start_time: datetime
    client_id: int
    clinician_id: int
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class AgentResponse(BaseModel):
    """Simple structured response from any agent"""
    agent_name: str
    suggestions: List[AppointmentSuggestion]
    explanation: str
    requires_confirmation: bool = True


class SupervisorResponse(BaseModel):
    """Aggregated response from supervisor agent"""
    request_type: str
    sub_agent_responses: List[AgentResponse]
    final_suggestions: List[AppointmentSuggestion]
    overall_explanation: str
    requires_confirmation: bool = True 