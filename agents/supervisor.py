from agents.base import BaseAgent
from agents.claude_client import claude_client
from agents.schemas import SupervisorDecision
from agents.sub_agents.availability_optimizer import AvailabilityOptimizer
from agents.sub_agents.preference_learner import PreferenceLearner
from agents.sub_agents.scheduling_agent import SchedulingAgent
import json

class SupervisorAgent(BaseAgent):
    def __init__(self):
        self.sub_agents = {
            'optimize_availability': AvailabilityOptimizer(),
            'learn_preferences': PreferenceLearner(),
            'suggest_schedule': SchedulingAgent(),
        }

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Supervisor Agent. Based on the input state, determine which of the following agents to invoke: "
            "'optimize_availability', 'learn_preferences', 'suggest_schedule'. "
            "Respond with a JSON object containing exactly these fields: "
            '{"selected_agent": "agent_name", "reasoning": "explanation"}'
        )

    def infer(self, state: str):
        output = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=self.system_prompt,
            messages=[
                {"role": "user", "content": state}
            ]
        ).content[0].text
        
        # Try to parse the JSON response
        try:
            # First try direct parsing
            return SupervisorDecision.model_validate_json(output)
        except Exception as e:
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_json = json.loads(json_str)
                    
                    # Handle field mapping
                    if 'agent_to_invoke' in parsed_json:
                        parsed_json['selected_agent'] = parsed_json.pop('agent_to_invoke')
                    if 'rationale' in parsed_json:
                        parsed_json['reasoning'] = parsed_json.pop('rationale')
                    
                    return SupervisorDecision(**parsed_json)
                else:
                    raise ValueError("No JSON found in response")
            except Exception as e2:
                # Fallback: create a default decision
                return SupervisorDecision(selected_agent="optimize_availability", reasoning="Fallback decision due to parsing error")

    def handle_request(self, state: str, **kwargs):
        decision = self.infer(state)
        agent_key = decision.selected_agent

        if agent_key not in self.sub_agents:
            raise ValueError(f"Unknown selected_agent from Supervisor: {agent_key}")

        print(f"Supervisor selected: {agent_key} | Reasoning: {decision.reasoning}")
        return self.sub_agents[agent_key].infer(**kwargs)


# Example usage
if __name__ == "__main__":
    supervisor = SupervisorAgent()

    state = "The clinician has an unbalanced workload this week."
    result = supervisor.handle_request(state, clinician_id=1, current_schedule=["2025-07-25T10:00:00Z"])
    print("Result:", result) 