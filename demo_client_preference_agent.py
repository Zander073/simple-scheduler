#!/usr/bin/env python3
"""
Demo script for Client Preference Agent
Shows how the agent analyzes client preferences and ranks time slots
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_scheduler.settings')
django.setup()

from appointments.models import Client, Appointment
from django.contrib.auth.models import User
from agents.sub_agents.client_preference_agent import ClientPreferenceAgent


def create_demo_data():
    """Create demo clients and appointments"""
    print("Creating demo data...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='demo_clinician',
        defaults={
            'first_name': 'Dr. Demo',
            'last_name': 'Clinician',
            'email': 'demo@example.com'
        }
    )
    
    # Create demo clients with different preference patterns in memo field
    clients_data = [
        {
            'name': 'Alice Johnson',
            'memo': 'tuesday mornings or Fridays at 2PM',
            'pattern': 'tuesday_morning_friday_afternoon'
        },
        {
            'name': 'Bob Smith', 
            'memo': 'monday afternoons and thursday evenings',
            'pattern': 'monday_afternoon_thursday_evening'
        },
        {
            'name': 'Carol Davis',
            'memo': 'wednesday at 9A or saturday mornings',
            'pattern': 'wednesday_morning_saturday_morning'
        },
        {
            'name': 'David Wilson',
            'memo': '',  # No stated preferences
            'pattern': 'mixed_pattern'
        }
    ]
    
    clients = []
    for data in clients_data:
        first_name, last_name = data['name'].split(' ')
        client, created = Client.objects.get_or_create(
            first_name=first_name,
            last_name=last_name,
            defaults={
                'memo': data['memo'],
                'clinician': user
            }
        )
        clients.append(client)
        print(f"✓ Created client: {client.full_name}")
    
    # Create appointment history
    create_appointment_history(clients, user)
    
    return clients


def create_appointment_history(clients, user):
    """Create appointment history for the last 6 weeks"""
    now = datetime.now()
    
    # Define appointment patterns for each client
    patterns = {
        'tuesday_morning_friday_afternoon': [
            (1, 9), (1, 10), (1, 11),  # Tuesday mornings
            (4, 14), (4, 15), (4, 16),  # Friday afternoons
        ],
        'monday_afternoon_thursday_evening': [
            (0, 13), (0, 14), (0, 15),  # Monday afternoons
            (3, 17), (3, 18), (3, 19),  # Thursday evenings
        ],
        'wednesday_morning_saturday_morning': [
            (2, 9), (2, 10), (2, 11),  # Wednesday mornings
            (5, 9), (5, 10), (5, 11),  # Saturday mornings
        ],
        'mixed_pattern': [
            (0, 10), (2, 14), (4, 16),  # Mixed pattern
        ]
    }
    
    client_patterns = ['tuesday_morning_friday_afternoon', 'monday_afternoon_thursday_evening', 
                      'wednesday_morning_saturday_morning', 'mixed_pattern']
    
    for i, client in enumerate(clients):
        pattern_name = client_patterns[i]
        pattern = patterns[pattern_name]
        
        for week in range(6):  # Last 6 weeks
            for day_of_week, hour in pattern:
                # Calculate the date for this week and day
                target_date = now - timedelta(weeks=week)
                days_ahead = day_of_week - target_date.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = target_date + timedelta(days=days_ahead)
                
                # Set the time
                appointment_time = target_date.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                
                # Create appointment
                appointment, created = Appointment.objects.get_or_create(
                    start_time=appointment_time,
                    client=client,
                    clinician=user,
                    defaults={'duration_in_minutes': 50}
                )
                
                if created:
                    print(f"  ✓ Created appointment: {client.first_name} on {appointment_time.strftime('%A %Y-%m-%d at %H:%M')}")


def demo_preference_analysis():
    """Demonstrate preference analysis for each client"""
    print("\n" + "="*80)
    print("CLIENT PREFERENCE ANALYSIS DEMO")
    print("="*80)
    
    # Initialize the agent
    agent = ClientPreferenceAgent()
    
    # Get all clients
    clients = Client.objects.all()
    
    for client in clients:
        print(f"\n{'='*60}")
        print(f"Client: {client.full_name}")
        print(f"{'='*60}")
        
        # Get preference analysis
        analysis = agent.get_preference_analysis(client.id)
        
        if 'error' in analysis:
            print(f"Error: {analysis['error']}")
            continue
        
        # Display analysis
        print(f"Memo (Preferences): {client.memo or 'None'}")
        print(f"Analysis Summary: {analysis['analysis_summary']}")
        
        # Display behavioral patterns
        patterns = analysis['behavioral_patterns']
        if patterns['total_appointments'] > 0:
            print(f"\nBehavioral Patterns (Last 6 weeks):")
            print(f"  Total appointments: {patterns['total_appointments']}")
            
            if patterns.get('most_common_day') is not None:
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                print(f"  Most common day: {day_names[patterns['most_common_day']]}")
            
            if patterns.get('most_common_hour') is not None:
                print(f"  Most common hour: {patterns['most_common_hour']}:00")
            
            if patterns.get('morning_preference'):
                print("  Shows preference for morning appointments")
            elif patterns.get('afternoon_preference'):
                print("  Shows preference for afternoon appointments")
            elif patterns.get('evening_preference'):
                print("  Shows preference for evening appointments")


def demo_time_slot_ranking():
    """Demonstrate time slot ranking functionality"""
    print("\n" + "="*80)
    print("TIME SLOT RANKING DEMO")
    print("="*80)
    
    # Initialize the agent
    agent = ClientPreferenceAgent()
    
    # Create sample time slots for next week
    now = datetime.now()
    sample_slots = []
    
    for day in range(7):  # Next 7 days
        for hour in [9, 10, 11, 14, 15, 16, 17]:  # Common appointment hours
            slot_time = now + timedelta(days=day)
            slot_time = slot_time.replace(
                hour=hour, minute=0, second=0, microsecond=0
            )
            sample_slots.append(slot_time)
    
    # Test with each client
    clients = Client.objects.all()
    
    for client in clients:
        print(f"\n{'='*60}")
        print(f"Time Slot Ranking for: {client.full_name}")
        print(f"{'='*60}")
        
        # Get ranked slots
        response = agent.analyze_client_preferences(client.id, sample_slots)
        
        if response.suggestions:
            print("\nTop 3 Recommended Time Slots:")
            for i, suggestion in enumerate(response.suggestions, 1):
                confidence_pct = suggestion.confidence * 100
                print(f"  {i}. {suggestion.start_time.strftime('%A %Y-%m-%d at %H:%M')} "
                      f"(Confidence: {confidence_pct:.1f}%)")
                print(f"     Reason: {suggestion.reason}")
        else:
            print("No suggestions generated")
        
        print(f"\nExplanation: {response.explanation}")


def demo_preference_parsing():
    """Demonstrate preference text parsing"""
    print("\n" + "="*80)
    print("PREFERENCE TEXT PARSING DEMO")
    print("="*80)
    
    # Initialize the agent
    agent = ClientPreferenceAgent()
    
    # Test preference texts
    test_preferences = [
        "tuesday mornings or Fridays at 2PM",
        "monday afternoons and thursday evenings",
        "wednesday at 9A or saturday mornings",
        "prefer Monday afternoons or Thursdays at 9A",
        "any time on tuesdays",
        "mornings only",
        "after 5pm on weekdays"
    ]
    
    for preference_text in test_preferences:
        print(f"\nParsing: '{preference_text}'")
        parsed = agent._parse_stated_preferences(preference_text)
        
        print(f"  Days of week: {parsed.get('days_of_week', [])}")
        print(f"  Time periods: {parsed.get('time_periods', [])}")
        print(f"  Specific times: {parsed.get('specific_times', [])}")


def main():
    """Main demo function"""
    print("Client Preference Agent Demo")
    print("="*50)
    
    # Check if demo data exists
    if not Client.objects.exists():
        print("No clients found. Creating demo data...")
        create_demo_data()
    else:
        print("Demo data already exists.")
    
    # Run demos
    demo_preference_parsing()
    demo_preference_analysis()
    demo_time_slot_ranking()
    
    print("\n" + "="*80)
    print("DEMO COMPLETED!")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("✓ Preference text parsing from memo field (days, times, periods)")
    print("✓ Behavioral pattern analysis from appointment history")
    print("✓ Time slot ranking by acceptance probability")
    print("✓ Top 3 recommendations with confidence scores")
    print("✓ Detailed reasoning for each recommendation")


if __name__ == "__main__":
    main() 