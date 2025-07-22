from agents.base import BaseAgent
from agents.claude_client import claude_client
from agents.schemas import AvailabilityOptimization
import json

class AvailabilityOptimizer(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return (
            "You are an Availability Optimizer Agent. Optimize therapist availability and workload distribution. "
            "Respond with a JSON object containing exactly these fields: "
            '{"clinician_id": number, "suggested_availability": ["time1", "time2"], "reasoning": "explanation"}'
        )

    def infer(self, clinician_id: int, current_schedule: list):
        prompt = f"Clinician {clinician_id} has schedule: {current_schedule}. Suggest optimized availability."
        output = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text
        
        try:
            return AvailabilityOptimization.model_validate_json(output)
        except Exception as e:
            try:
                import re
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_json = json.loads(json_str)
                    
                    # Handle field mapping
                    if 'clinicianId' in parsed_json:
                        parsed_json['clinician_id'] = parsed_json.pop('clinicianId')
                    if 'suggestedAvailability' in parsed_json:
                        parsed_json['suggested_availability'] = parsed_json.pop('suggestedAvailability')
                    
                    return AvailabilityOptimization(**parsed_json)
                else:
                    raise ValueError("No JSON found in response")
            except Exception as e2:
                raise ValueError(f"Failed to parse JSON response: {e2}") 