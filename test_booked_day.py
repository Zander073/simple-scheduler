#!/usr/bin/env python3
"""
Test script for booked day scenario and conflict validation
"""
import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_scheduler.settings')
django.setup()

from appointments.models import Appointment, Client
from django.contrib.auth.models import User
from agents.appointment_request_agent import AppointmentRequestAgent
from agents.schemas import AppointmentRequest


def create_booked_day_scenario():
    """Create a scenario where a specific day is fully booked."""
    print("=== Creating Booked Day Scenario ===\n")
    
    # Get or create a test clinician
    clinician, created = User.objects.get_or_create(
        username='booked_day_clinician',
        defaults={
            'first_name': 'Booked',
            'last_name': 'Day',
            'email': 'booked@test.com'
        }
    )
    
    # Get or create test clients
    clients = []
    for i in range(8):  # We'll need 8 clients to book a full day
        client, created = Client.objects.get_or_create(
            id=100 + i,
            defaults={
                'first_name': f'Booked',
                'last_name': f'Client {i+1}',
                'clinician': clinician
            }
        )
        clients.append(client)
    
    # Clear existing appointments for this clinician
    Appointment.objects.filter(clinician=clinician).delete()
    
    # Book the entire day (9 AM to 5 PM, 8 hours)
    target_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    appointments_created = []
    for i, client in enumerate(clients):
        appointment_time = target_date + timedelta(hours=i)
        appointment = Appointment.objects.create(
            start_time=appointment_time,
            duration_in_minutes=50,
            client=client,
            clinician=clinician
        )
        appointments_created.append(appointment)
        print(f"Created appointment: {client.full_name} at {appointment_time.strftime('%Y-%m-%d %H:%M')}")
    
    print(f"\n✅ Created {len(appointments_created)} appointments for {target_date.strftime('%Y-%m-%d')}")
    print("The day is now fully booked from 9 AM to 5 PM")
    
    return clinician.id, target_date


def test_booked_day_request():
    """Test requesting an appointment for a fully booked day."""
    print("\n=== Testing Booked Day Request ===\n")
    
    # Create the booked day scenario
    clinician_id, booked_date = create_booked_day_scenario()
    
    # Test requesting an appointment for the booked day
    test_cases = [
        {
            'name': 'Non-urgent request for booked day',
            'data': {
                'is_urgent': False,
                'time_preference': 'morning',
                'preferred_days': [booked_date.strftime('%A')]  # e.g., 'Monday'
            }
        },
        {
            'name': 'Urgent request for booked day',
            'data': {
                'is_urgent': True,
                'time_preference': 'asap'
            }
        }
    ]
    
    base_url = 'http://localhost:8000/api/requests/'
    
    for test_case in test_cases:
        print(f"\n--- Test: {test_case['name']} ---")
        print(f"Request data: {test_case['data']}")
        
        try:
            response = requests.post(base_url, json=test_case['data'])
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Status: {response.status_code}")
                print(f"Message: {result.get('message')}")
                
                # Show agent results
                agent_results = result.get('agent_results', [])
                print(f"Agent results: {len(agent_results)} actions")
                
                for i, agent_result in enumerate(agent_results, 1):
                    print(f"  Action {i}: {agent_result['action_taken']}")
                    appointment = agent_result['appointment']
                    print(f"    Appointment ID: {appointment['id']}")
                    print(f"    Start Time: {appointment['start_time']}")
                    print(f"    Duration: {appointment['duration_in_minutes']} minutes")
                
                # Check if the appointment was scheduled for the booked day
                for agent_result in agent_results:
                    appointment_time = datetime.fromisoformat(agent_result['appointment']['start_time'].replace('Z', '+00:00'))
                    if appointment_time.date() == booked_date.date():
                        print(f"⚠️  WARNING: Appointment scheduled for booked day at {appointment_time.strftime('%H:%M')}")
                    else:
                        print(f"✅ Appointment scheduled for different day: {appointment_time.strftime('%Y-%m-%d %H:%M')}")
                
            else:
                print(f"❌ Error! Status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - make sure the Django server is running on localhost:8000")
            return
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 60)


def test_agent_validation():
    """Test the agent's validation logic directly."""
    print("\n=== Testing Agent Validation Logic ===\n")
    
    # Create a test scenario
    clinician, created = User.objects.get_or_create(
        username='validation_test_clinician',
        defaults={
            'first_name': 'Validation',
            'last_name': 'Test',
            'email': 'validation@test.com'
        }
    )
    
    client, created = Client.objects.get_or_create(
        id=200,
        defaults={
            'first_name': 'Validation',
            'last_name': 'Client',
            'clinician': clinician
        }
    )
    
    # Create some existing appointments
    Appointment.objects.filter(clinician=clinician).delete()
    
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2)
    
    # Create appointments at 9 AM and 11 AM
    Appointment.objects.create(
        start_time=base_time,
        duration_in_minutes=50,
        client=client,
        clinician=clinician
    )
    
    Appointment.objects.create(
        start_time=base_time + timedelta(hours=2),
        duration_in_minutes=50,
        client=client,
        clinician=clinician
    )
    
    print(f"Created appointments at {base_time.strftime('%H:%M')} and {(base_time + timedelta(hours=2)).strftime('%H:%M')}")
    
    # Test the agent
    agent = AppointmentRequestAgent()
    request = AppointmentRequest(
        client_id=client.id,
        clinician_id=clinician.id,
        urgency=False,
        time_of_day_preference="morning",
        preferred_days=None
    )
    
    results = agent.infer(request)
    print(f"\nAgent results: {len(results)} actions")
    
    for i, result in enumerate(results, 1):
        print(f"  Action {i}: {result.action_taken}")
        appointment = result.appointment
        print(f"    Appointment ID: {appointment['id']}")
        print(f"    Start Time: {appointment['start_time']}")
        print(f"    Duration: {appointment['duration_in_minutes']} minutes")
    
    # Verify no conflicts
    calendar = agent._get_clinician_calendar(clinician.id)
    print(f"\nFinal calendar has {len(calendar)} appointments")
    
    # Check for any overlapping appointments
    appointment_times = []
    for appt_time_str in calendar:
        try:
            appt_time = datetime.fromisoformat(appt_time_str.replace('Z', '+00:00'))
            appointment_times.append(appt_time)
        except:
            continue
    
    # Sort by time and check for overlaps
    appointment_times.sort()
    overlaps = []
    for i in range(len(appointment_times) - 1):
        if appointment_times[i] + timedelta(minutes=50) > appointment_times[i + 1]:
            overlaps.append(f"Overlap between {appointment_times[i]} and {appointment_times[i + 1]}")
    
    if overlaps:
        print(f"❌ Found overlaps: {overlaps}")
    else:
        print("✅ No overlapping appointments found")


def main():
    """Main test function."""
    print("Starting Booked Day and Validation Tests...")
    
    # Test booked day scenario
    test_booked_day_request()
    
    # Test agent validation logic
    test_agent_validation()
    
    print("\n=== Tests Completed! ===")


if __name__ == "__main__":
    main() 