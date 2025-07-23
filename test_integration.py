#!/usr/bin/env python3
"""
Test script to demonstrate the integration and show database records created
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_scheduler.settings')
django.setup()

from appointments.models import Appointment, Client
from django.contrib.auth.models import User


def test_integration():
    """Test the integration and show database records."""
    print("=== Testing Appointment Request Agent Integration ===\n")
    
    # Get initial state
    initial_appointments = Appointment.objects.count()
    print(f"Initial appointments in database: {initial_appointments}")
    
    # Test cases
    test_cases = [
        {
            'name': 'Non-urgent morning appointment',
            'data': {
                'is_urgent': False,
                'time_preference': 'morning',
                'preferred_days': ['Monday', 'Tuesday']
            }
        },
        {
            'name': 'Urgent appointment',
            'data': {
                'is_urgent': True,
                'time_preference': 'asap'
            }
        },
        {
            'name': 'Afternoon appointment with specific hour',
            'data': {
                'is_urgent': False,
                'time_preference': 15  # 3 PM
            }
        }
    ]

    base_url = 'http://localhost:8000/api/requests/'
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
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
                
                for j, agent_result in enumerate(agent_results, 1):
                    print(f"  Action {j}: {agent_result['action_taken']}")
                    appointment = agent_result['appointment']
                    print(f"    Appointment ID: {appointment['id']}")
                    print(f"    Client ID: {appointment['client_id']}")
                    print(f"    Clinician ID: {appointment['clinician_id']}")
                    print(f"    Start Time: {appointment['start_time']}")
                    print(f"    Duration: {appointment['duration_in_minutes']} minutes")
                
                # Show updated appointments count
                updated_appointments = result.get('updated_appointments', [])
                print(f"Total appointments after this request: {len(updated_appointments)}")
                
            else:
                print(f"❌ Error! Status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - make sure the Django server is running on localhost:8000")
            return
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 60)
    
    # Show final database state
    print("\n=== Final Database State ===")
    final_appointments = Appointment.objects.count()
    print(f"Final appointments in database: {final_appointments}")
    print(f"New appointments created: {final_appointments - initial_appointments}")
    
    # Show recent appointments
    print("\n=== Recent Appointments Created ===")
    recent_appointments = Appointment.objects.order_by('-id')[:10]
    
    for appt in recent_appointments:
        print(f"ID: {appt.id}")
        print(f"  Client: {appt.client.full_name} (ID: {appt.client.id})")
        print(f"  Clinician: {appt.clinician.username} (ID: {appt.clinician.id})")
        print(f"  Start Time: {appt.start_time}")
        print(f"  Duration: {appt.duration_in_minutes} minutes")
        print(f"  Created: {appt.start_time.strftime('%Y-%m-%d %H:%M')}")
        print()


def show_database_records():
    """Show detailed database records."""
    print("\n=== Detailed Database Records ===")
    
    # Get all appointments ordered by creation time
    appointments = Appointment.objects.select_related('client', 'clinician').order_by('-start_time')
    
    print(f"Total appointments in database: {appointments.count()}")
    print()
    
    # Group by clinician
    clinicians = User.objects.filter(appointments__isnull=False).distinct()
    
    for clinician in clinicians:
        print(f"Clinician: {clinician.username} (ID: {clinician.id})")
        clinician_appointments = appointments.filter(clinician=clinician)
        print(f"  Total appointments: {clinician_appointments.count()}")
        
        # Show appointments for this clinician
        for appt in clinician_appointments[:5]:  # Show first 5
            print(f"    - {appt.client.full_name} at {appt.start_time.strftime('%Y-%m-%d %H:%M')} ({appt.duration_in_minutes}min)")
        
        if clinician_appointments.count() > 5:
            print(f"    ... and {clinician_appointments.count() - 5} more")
        print()


def verify_scheduling_constraints():
    """Verify that all appointments follow the scheduling constraints."""
    print("\n=== Scheduling Constraints Verification ===")
    
    appointments = Appointment.objects.all()
    total_appointments = appointments.count()
    on_hour_count = 0
    business_hours_count = 0
    
    for appt in appointments:
        # Check if on the hour
        if appt.start_time.minute == 0:
            on_hour_count += 1
        
        # Check if within business hours (9 AM - 5 PM)
        if 9 <= appt.start_time.hour < 17:
            business_hours_count += 1
    
    print(f"Total appointments: {total_appointments}")
    print(f"Appointments on the hour: {on_hour_count} ({on_hour_count/total_appointments*100:.1f}%)")
    print(f"Appointments within business hours (9 AM - 5 PM): {business_hours_count} ({business_hours_count/total_appointments*100:.1f}%)")
    
    if on_hour_count == total_appointments:
        print("✅ All appointments are scheduled on the hour!")
    else:
        print("❌ Some appointments are not on the hour")
    
    if business_hours_count == total_appointments:
        print("✅ All appointments are within business hours!")
    else:
        print("❌ Some appointments are outside business hours")


def main():
    """Main test function."""
    print("Starting Integration Test and Database Analysis...")
    
    # Test the integration
    test_integration()
    
    # Show database records
    show_database_records()
    
    # Verify constraints
    verify_scheduling_constraints()
    
    print("\n=== Test Completed! ===")


if __name__ == "__main__":
    main() 