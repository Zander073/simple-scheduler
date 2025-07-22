# Client Preference Agent

A sophisticated Django/Python agent that analyzes client scheduling preferences and ranks time slots by acceptance probability. The agent combines both stated preferences (from the memo field) and behavioral patterns from appointment history to provide intelligent scheduling recommendations.

## Features

### 🎯 Core Functionality
- **Preference Text Parsing**: Understands natural language preferences from memo field like "tuesday mornings or Fridays at 2PM"
- **Behavioral Pattern Analysis**: Learns from the last 4-6 weeks of appointment history
- **Time Slot Ranking**: Ranks available time slots by acceptance probability
- **Top 3 Recommendations**: Returns the 3 most likely to be accepted time slots
- **Confidence Scoring**: Provides probability scores for each recommendation
- **Detailed Reasoning**: Explains why each time slot was recommended

### 📊 Analysis Capabilities
- **Day of Week Patterns**: Identifies preferred days (Monday, Tuesday, etc.)
- **Time Period Preferences**: Recognizes morning, afternoon, evening preferences
- **Specific Time Matching**: Handles exact times like "2PM" or "9A"
- **Historical Trend Analysis**: Learns from recent appointment patterns
- **Adaptive Learning**: Updates recommendations based on new data

## Architecture

### Components

1. **ClientPreferenceAgent** (`agents/sub_agents/client_preference_agent.py`)
   - Main agent class inheriting from BaseAgent
   - Handles preference analysis and time slot ranking
   - Integrates with Django models

2. **Client Model** (`appointments/models.py`)
   - Uses existing `memo` field to store client preference text
   - Maintains relationship with appointments for historical analysis

3. **Django Views** (`appointments/views.py`)
   - RESTful API endpoints for preference analysis
   - Web interface integration
   - Appointment scheduling with preference-based recommendations

4. **Management Commands** (`appointments/management/commands/`)
   - Testing and demo functionality
   - Sample data creation

## Usage Examples

### Basic Usage

```python
from agents.sub_agents.client_preference_agent import ClientPreferenceAgent
from datetime import datetime, timedelta

# Initialize the agent
agent = ClientPreferenceAgent()

# Create sample time slots
available_slots = [
    datetime.now() + timedelta(days=1, hours=9),  # Tomorrow 9 AM
    datetime.now() + timedelta(days=1, hours=14), # Tomorrow 2 PM
    datetime.now() + timedelta(days=2, hours=10), # Day after 10 AM
]

# Get ranked recommendations for a client
response = agent.analyze_client_preferences(client_id=1, available_slots=available_slots)

# Display top 3 recommendations
for i, suggestion in enumerate(response.suggestions, 1):
    print(f"{i}. {suggestion.start_time.strftime('%A %H:%M')} "
          f"(Confidence: {suggestion.confidence:.1%})")
    print(f"   Reason: {suggestion.reason}")
```

### Preference Text Parsing

The agent can understand various preference formats from the memo field:

```python
# Examples of supported preference text in memo field:
preferences = [
    "tuesday mornings or Fridays at 2PM",
    "monday afternoons and thursday evenings", 
    "wednesday at 9A or saturday mornings",
    "prefer Monday afternoons or Thursdays at 9A",
    "any time on tuesdays",
    "mornings only",
    "after 5pm on weekdays"
]

# Parse preferences from memo field
parsed = agent._parse_stated_preferences("tuesday mornings or Fridays at 2PM")
print(parsed)
# Output: {
#     'days_of_week': [1, 4],  # Tuesday, Friday
#     'time_periods': [(6, 12)],  # mornings
#     'specific_times': [14],  # 2PM
#     'raw_text': 'tuesday mornings or fridays at 2pm'
# }
```

### Detailed Analysis

```python
# Get comprehensive preference analysis
analysis = agent.get_preference_analysis(client_id=1)

print(f"Client: {analysis['client_name']}")
print(f"Analysis Summary: {analysis['analysis_summary']}")

# Behavioral patterns
patterns = analysis['behavioral_patterns']
print(f"Total appointments (last 6 weeks): {patterns['total_appointments']}")
print(f"Most common day: {patterns['most_common_day']}")
print(f"Most common hour: {patterns['most_common_hour']}")
```

## API Endpoints

### Get Preferred Time Slots
```http
POST /appointments/client/{client_id}/preferred-slots/
Content-Type: application/json

{
    "available_slots": [
        "2024-01-15T10:00:00",
        "2024-01-15T14:00:00",
        "2024-01-16T09:00:00"
    ]
}
```

**Response:**
```json
{
    "client_name": "Alice Johnson",
    "suggestions": [
        {
            "start_time": "2024-01-15T10:00:00",
            "confidence": 0.95,
            "reason": "Matches stated preference for Tuesday mornings",
            "duration_in_minutes": 50
        }
    ],
    "explanation": "Top 3 time slots ranked by client preference analysis",
    "requires_confirmation": true
}
```

### Update Client Memo (Preferences)
```http
POST /appointments/client/{client_id}/update-memo/
Content-Type: application/json

{
    "memo": "monday afternoons or thursday evenings"
}
```

## Installation & Setup

### 1. Environment Variables
Ensure you have the required environment variables:
```bash
CLAUDE_API_KEY=your_anthropic_api_key_here
```

### 2. Test the Agent
```bash
# Run the demo script
python demo_client_preference_agent.py

# Or use the management command
python manage.py test_preference_agent --create-sample-data
```

## Algorithm Details

### Preference Scoring System

The agent uses a weighted scoring system to calculate acceptance probability:

1. **Base Probability**: 50% (neutral starting point)

2. **Stated Preferences** (up to +60%):
   - Day of week match: +20%
   - Time period match: +15%
   - Specific time match: +25%

3. **Behavioral Patterns** (up to +35%):
   - Most common day match: +15%
   - Similar hour (±1 hour): +10%
   - Time period preference: +10%

4. **Final Score**: Capped at 100%

### Pattern Recognition

The agent analyzes appointment history to identify:

- **Day of Week Patterns**: Which days the client typically schedules
- **Time Period Preferences**: Morning (6-12), Afternoon (12-17), Evening (17-21)
- **Hour Distribution**: Most common appointment hours
- **Trend Analysis**: Changes in preferences over time

### Natural Language Processing

The preference parser handles:

- **Day Recognition**: Monday, Tuesday, Wed, Thu, Fri, Sat, Sun
- **Time Periods**: morning, afternoon, evening, night
- **Specific Times**: 9A, 2PM, 14:00, etc.
- **Flexible Formatting**: Case-insensitive, various formats

## Integration with Existing System

The Client Preference Agent integrates seamlessly with the existing scheduling system:

1. **Base Agent Inheritance**: Extends the existing BaseAgent class
2. **Response Models**: Uses standardized AgentResponse and AppointmentSuggestion models
3. **Django ORM**: Leverages existing Client and Appointment models
4. **Memo Field Usage**: Uses the existing memo field for preference storage
5. **Supervisor Integration**: Can be coordinated by the SupervisorAgent

## Testing

### Unit Tests
```bash
python manage.py test appointments.tests
```

### Demo Script
```bash
python demo_client_preference_agent.py
```

### Management Command
```bash
# Test with sample data
python manage.py test_preference_agent --create-sample-data

# Test specific client
python manage.py test_preference_agent --client-id 1
```

## Performance Considerations

- **Caching**: Consider caching preference analysis results for frequently accessed clients
- **Database Queries**: Optimized queries for appointment history analysis
- **Memory Usage**: Efficient data structures for pattern analysis
- **Scalability**: Agent can handle large numbers of time slots and clients

## Future Enhancements

1. **Machine Learning Integration**: Use ML models for more sophisticated pattern recognition
2. **Real-time Learning**: Update preferences based on appointment outcomes
3. **Multi-factor Analysis**: Consider external factors (weather, holidays, etc.)
4. **Preference Evolution**: Track how preferences change over time
5. **Conflict Resolution**: Handle conflicting preferences intelligently

## Troubleshooting

### Common Issues

1. **No Preferences Found**: Ensure client has either memo text or appointment history
2. **Low Confidence Scores**: May indicate insufficient data or conflicting patterns
3. **API Key Issues**: Verify CLAUDE_API_KEY is set correctly
4. **Database Errors**: Check database connectivity

### Debug Mode

Enable debug logging to see detailed analysis:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to the Client Preference Agent:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure backward compatibility
5. Test with various preference formats and edge cases

## License

This implementation is part of the Simple Scheduler project and follows the same licensing terms. 