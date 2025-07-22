from pydantic import BaseModel
from typing import List, Optional


class AvailabilityOptimization(BaseModel):
    clinician_id: int
    suggested_availability: List[str]
    reasoning: Optional[str] = None


class PreferenceLearning(BaseModel):
    client_id: int
    learned_preferences: List[str]
    reasoning: Optional[str] = None


class ScheduleSuggestion(BaseModel):
    client_id: int
    proposed_time: str
    confidence: float
    reasoning: Optional[str] = None


class SupervisorDecision(BaseModel):
    selected_agent: str
    reasoning: Optional[str] = None 