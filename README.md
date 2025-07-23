# simple-scheduler

A Django-based appointment scheduling system with intelligent AI agents for preference analysis and scheduling optimization.

## Features

### 🤖 AI Agents
- **Client Preference Agent**: Analyzes client preferences from memo field and ranks time slots by acceptance probability
- **Scheduling Agent**: Optimizes appointment scheduling based on availability and preferences
- **Availability Optimizer Agent**: Manages clinician availability and scheduling constraints
- **Preference Learner Agent**: Learns and adapts to client and clinician preferences
- **Supervisor Agent**: Coordinates multiple agents for complex scheduling decisions

### 📅 Core Functionality
- Client preference analysis from natural language text in memo field
- Behavioral pattern recognition from appointment history
- Time slot ranking with confidence scores
- Top 3 recommendation system
- RESTful API endpoints for integration
- Django admin interface for data management

## First-time setup
* Run `brew bundle` to install brew packages
* Run `uv sync` to create a virtual environment and install dependencies
* Run `source .venv/bin/activate` to activate the virtual environment
  * Note: The exact command may change depending on which shell you use

## Environment Setup
Set up your environment variables:
```bash
# Required for AI agents
CLAUDE_API_KEY=your_anthropic_api_key_here
```

## Running the app
* Recommended: add the following function definition to your shell config:
```
function dpy() {
  python manage.py "$@"
  return $?
}
```
* Run migrations: `make migrate`
* Seed data: `make seed`
* Start server: `make start`
* Start websocket server: `make websocket`

## Run the agent demo
Note: make sure you have a `CLAUDE_API_KEY` defined in your `.env`

Run the demo:
```
uv run demo_agents.py
```

### Run the client preference agent demo
```bash
python demo_client_preference_agent.py
```

### Test preference agent with management command
```bash
# Create sample data and test
dpy test_preference_agent --create-sample-data

# Test specific client
dpy test_preference_agent --client-id 1
```

## API Usage

### Get Preferred Time Slots
```bash
curl -X POST http://localhost:8000/appointments/client/1/preferred-slots/ \
  -H "Content-Type: application/json" \
  -d '{
    "available_slots": [
      "2024-01-15T10:00:00",
      "2024-01-15T14:00:00"
    ]
  }'
```

### Update Client Memo (Preferences)
```bash
curl -X POST http://localhost:8000/appointments/client/1/update-memo/ \
  -H "Content-Type: application/json" \
  -d '{
    "memo": "tuesday mornings or Fridays at 2PM"
  }'
```

## Documentation

- [Client Preference Agent Documentation](CLIENT_PREFERENCE_AGENT_README.md) - Detailed guide for the preference analysis system
- [Agents Documentation](agents/AGENTS_README.md) - Overview of all AI agents in the system

## Quick Start Example

```python
from agents.sub_agents.client_preference_agent import ClientPreferenceAgent
from datetime import datetime, timedelta

# Initialize agent
agent = ClientPreferenceAgent()

# Create time slots
slots = [
    datetime.now() + timedelta(days=1, hours=9),
    datetime.now() + timedelta(days=1, hours=14),
]

# Get recommendations
response = agent.analyze_client_preferences(client_id=1, available_slots=slots)

# Display results
for suggestion in response.suggestions:
    print(f"Time: {suggestion.start_time}")
    print(f"Confidence: {suggestion.confidence:.1%}")
    print(f"Reason: {suggestion.reason}")
```

## Client Preference Storage

Client preferences are stored in the existing `memo` field of the Client model. The agent can parse natural language preferences like:
- "tuesday mornings or Fridays at 2PM"
- "monday afternoons and thursday evenings"
- "wednesday at 9A or saturday mornings"
- "prefer Monday afternoons or Thursdays at 9A"
