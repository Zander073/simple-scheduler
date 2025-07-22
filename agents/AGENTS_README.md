# Supervisor Agent System

A framework-agnostic supervisor agent system that coordinates multiple specialized sub-agents for intelligent appointment scheduling and management.

## Architecture

```
agents/
├── base_agent.py              # Base agent class
├── supervisor_agent.py        # Main supervisor agent
├── interface.py               # Framework-agnostic interface
├── __init__.py                # Package exports
└── sub_agents/                # Specialized sub-agents
    ├── __init__.py
    ├── scheduling_agent.py
    ├── availability_optimizer_agent.py
    ├── client_relationship_agent.py
    ├── conflict_resolver_agent.py
    └── preference_learner_agent.py
```

## Quick Start

### 1. Basic Usage

```python
from agents import schedule_appointment, optimize_availability

# Schedule an appointment
result = schedule_appointment({
    'message': 'Schedule appointment for John Doe next week',
    'client_name': 'John Doe',
    'preferred_time': 'morning'
})

# Optimize availability
result = optimize_availability({
    'message': 'Optimize my calendar for next week',
    'time_period': 'next_week'
})
```

### 2. With User Context

```python
from agents import AgentInterface

interface = AgentInterface()

user_info = {
    'id': 1,
    'username': 'therapist_jane',
    'email': 'jane@therapy.com',
    'role': 'therapist'
}

result = interface.schedule_appointment(request_data, user_info)
```

### 3. With Additional Context

```python
context = {
    'current_appointments': [...],
    'available_slots': [...],
    'client_preferences': {...}
}

result = interface.handle_complex_request(request_data, user_info, context)
```

## Available Functions

### Convenience Functions
- `get_agent_status()` - Get status of all agents
- `get_available_actions()` - Get available actions for each agent
- `schedule_appointment(request_data, user_info=None, context=None)` - Schedule appointments
- `optimize_availability(request_data, user_info=None, context=None)` - Optimize availability
- `manage_client_relationship(request_data, user_info=None, context=None)` - Manage client relationships
- `resolve_conflicts(request_data, user_info=None, context=None)` - Resolve scheduling conflicts
- `learn_preferences(request_data, user_info=None, context=None)` - Learn and adapt preferences
- `handle_complex_request(request_data, user_info=None, context=None)` - Handle complex multi-agent requests

### AgentInterface Class
```python
from agents import AgentInterface

interface = AgentInterface()

# All the same methods as convenience functions
interface.schedule_appointment(request_data, user_info, context)
interface.optimize_availability(request_data, user_info, context)
# ... etc
```

## Agent Types

### 1. Scheduling Agent
- Find optimal appointment slots
- Handle natural language scheduling requests
- Suggest alternative times
- Consider historical patterns

### 2. Availability Optimizer Agent
- Optimize therapist availability
- Manage calendar efficiency
- Balance workload distribution

### 3. Client Relationship Agent
- Handle client communication
- Manage relationship dynamics
- Process rescheduling requests

### 4. Conflict Resolver Agent
- Resolve scheduling conflicts
- Negotiate solutions
- Handle disputes

### 5. Preference Learner Agent
- Learn client and therapist preferences
- Adapt scheduling patterns
- Improve recommendations over time

## Request Types

The supervisor agent can handle different types of requests:

1. **`schedule`** - Appointment scheduling and slot optimization
2. **`availability`** - Therapist availability and calendar optimization
3. **`client`** - Client relationship management and communication
4. **`conflict`** - Scheduling conflict resolution
5. **`preference`** - Learning and adapting to preferences
6. **`complex`** - Multi-agent coordination for complex workflows

## Response Format

All agent responses follow this format:

```python
{
    'success': True/False,
    'agent': 'agent_name',
    'response': 'agent_response_text',
    'request_data': original_request_data,
    'error': 'error_message'  # Only if success=False
}
```

## Environment Setup

Ensure you have the required environment variables:

```bash
export CLAUDE_API_KEY="your-claude-api-key"
```

## Key Features

✅ **Framework Agnostic** - No Django or other framework dependencies  
✅ **Easy Integration** - Simple import and use  
✅ **Context Aware** - Pass user info and additional context  
✅ **Error Handling** - Comprehensive error handling and responses  
✅ **Multi-Agent Coordination** - Supervisor coordinates multiple specialized agents  
✅ **Extensible** - Easy to add new sub-agents  
✅ **Tested** - Comprehensive test suite  

## Best Practices

1. **Use convenience functions** for simple operations
2. **Use AgentInterface class** for object-oriented approach
3. **Pass user context** for better agent responses
4. **Handle errors** - Always check the `success` field
5. **Test thoroughly** - Use the test script to verify functionality
6. **Keep it simple** - Start with basic usage and add complexity as needed 