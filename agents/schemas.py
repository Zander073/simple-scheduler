from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class AppointmentRequest(BaseModel):
    client_id: int
    clinician_id: int
    urgency: bool
    time_of_day_preference: str
    preferred_days: Optional[List[str]] = None

    def __str__(self):
        return f"AppointmentRequest(client_id={self.client_id}, clinician_id={self.clinician_id}, urgency={self.urgency}, time_of_day_preference={self.time_of_day_preference}, preferred_days={self.preferred_days})"


class AppointmentAction(BaseModel):
    action: Literal["create", "update"]
    start_time: str
    client_id: int
    clinician_id: int
    appointment_id: Optional[int] = None  # Required for update actions


class AppointmentResult(BaseModel):
    action_taken: str
    appointment: dict 