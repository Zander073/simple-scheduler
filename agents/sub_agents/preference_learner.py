from agents.base import BaseAgent
from agents.claude_client import claude_client
from agents.schemas import PreferenceLearning
import json

class PreferenceLearner(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return (
            "You are a Preference Learner Agent. Learn and adapt to client and therapist preferences. "
            "Respond with a JSON object containing exactly these fields: "
            '{"client_id": number, "learned_preferences": ["pref1", "pref2"], "reasoning": "explanation"}'
        )

    def infer(self, client_id: int, history: str):
        prompt = f"Client {client_id} has history: {history}. Learn their scheduling preferences."
        output = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text

        try:
            return PreferenceLearning.model_validate_json(output)
        except Exception as e:
            try:
                import re
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_json = json.loads(json_str)
                    
                    # Handle field mapping
                    if 'clientId' in parsed_json:
                        parsed_json['client_id'] = parsed_json.pop('clientId')
                    if 'learnedPreferences' in parsed_json:
                        parsed_json['learned_preferences'] = parsed_json.pop('learnedPreferences')
                    
                    return PreferenceLearning(**parsed_json)
                else:
                    raise ValueError("No JSON found in response")
            except Exception as e2:
                raise ValueError(f"Failed to parse JSON response: {e2}") 