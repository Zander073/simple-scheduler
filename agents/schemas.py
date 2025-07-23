from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class AppointmentRequest(BaseModel):
    client_id: int
    clinician_id: int
    urgency: bool
    time_of_day_preference: Optional[int] = None

    @property
    def time_period(self) -> Optional[str]:
        if self.time_of_day_preference is None:
            return None
        if 9 <= self.time_of_day_preference <= 11:
            return "morning"
        if 12 <= self.time_of_day_preference <= 14:
            return "afternoon" 
        if 15 <= self.time_of_day_preference <= 17:
            return "evening"
        return None

    def __str__(self):
        return f"AppointmentRequest(client_id={self.client_id}, clinician_id={self.clinician_id}, urgency={self.urgency}, time_of_day_preference={self.time_of_day_preference}, time_period={self.time_period})"


class AppointmentAction(BaseModel):
    action: Literal["create", "update"]
    start_time: str
    client_id: int
    clinician_id: int
    appointment_id: Optional[int] = None  # Required for update actions


class AppointmentResult(BaseModel):
    action_taken: str
    appointment: dict 