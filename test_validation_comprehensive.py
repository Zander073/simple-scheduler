#!/usr/bin/env python3
"""
Comprehensive validation test for the appointment request agent
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_scheduler.settings')
django.setup()

from appointments.models import Appointment, Client
from django.contrib.auth.models import User
from agents.appointment_request_agent import AppointmentRequestAgent
from agents.schemas import AppointmentRequest, AppointmentAction


def test_conflict_detection():
    """Test that the agent properly detects and handles conflicts."""
    print("=== Testing Conflict Detection ===\n")
    
    # Create test scenario
    clinician, created = User.objects.get_or_create(
        username='conflict_test_clinician',
        defaults={
            'first_name': 'Conflict',
            'last_name': 'Test',
            'email': 'conflict@test.com'
        }
    )
    
    client1, created = Client.objects.get_or_create(
        id=300,
        defaults={
            'first_name': 'Conflict',
            'last_name': 'Client 1',
            'clinician': clinician
        }
    )
    
    client2, created = Client.objects.get_or_create(
        id=301,
        defaults={
            'first_name': 'Conflict',
            'last_name': 'Client 2',
            'clinician': clinician
        }
    )
    
    # Clear existing appointments
    Appointment.objects.filter(clinician=clinician).delete()
    
    # Create an existing appointment at 10 AM
    base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=3)
    existing_appointment = Appointment.objects.create(
        start_time=base_time,
        duration_in_minutes=50,
        client=client1,
        clinician=clinician
    )
    
    print(f"Created existing appointment at {base_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Test the agent's validation
    agent = AppointmentRequestAgent()
    
    # Test 1: Try to create an appointment that conflicts with existing
    print("\n--- Test 1: Conflicting appointment ---")
    request1 = AppointmentRequest(
        client_id=client2.id,
        clinician_id=clinician.id,
        urgency=False,
        time_of_day_preference="morning",
        preferred_days=None
    )
    
    # Manually create a conflicting action to test validation
    conflicting_action = AppointmentAction(
        action="create",
        start_time=base_time.isoformat(),  # Same time as existing appointment
        client_id=client2.id,
        clinician_id=clinician.id
    )
    
    # Test validation
    calendar = agent._get_clinician_calendar(clinician.id)
    validated_actions = agent._validate_actions([conflicting_action], calendar)
    
    print(f"Conflicting action created: {conflicting_action}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 0:
        print("✅ Conflict properly detected and rejected")
    else:
        print("❌ Conflict not detected")
    
    # Test 2: Try to create an appointment that doesn't conflict
    print("\n--- Test 2: Non-conflicting appointment ---")
    non_conflicting_action = AppointmentAction(
        action="create",
        start_time=(base_time + timedelta(hours=2)).isoformat(),  # 2 hours later
        client_id=client2.id,
        clinician_id=clinician.id
    )
    
    validated_actions = agent._validate_actions([non_conflicting_action], calendar)
    print(f"Non-conflicting action created: {non_conflicting_action}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 1:
        print("✅ Non-conflicting action properly accepted")
    else:
        print("❌ Non-conflicting action incorrectly rejected")


def test_update_validation():
    """Test validation of update actions."""
    print("\n=== Testing Update Action Validation ===\n")
    
    # Create test scenario
    clinician, created = User.objects.get_or_create(
        username='update_test_clinician',
        defaults={
            'first_name': 'Update',
            'last_name': 'Test',
            'email': 'update@test.com'
        }
    )
    
    client, created = Client.objects.get_or_create(
        id=302,
        defaults={
            'first_name': 'Update',
            'last_name': 'Client',
            'clinician': clinician
        }
    )
    
    # Clear existing appointments
    Appointment.objects.filter(clinician=clinician).delete()
    
    # Create an appointment to update
    base_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=4)
    appointment = Appointment.objects.create(
        start_time=base_time,
        duration_in_minutes=50,
        client=client,
        clinician=clinician
    )
    
    print(f"Created appointment {appointment.id} at {base_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Test the agent's validation
    agent = AppointmentRequestAgent()
    
    # Test 1: Valid update action
    print("\n--- Test 1: Valid update action ---")
    valid_update_action = AppointmentAction(
        action="update",
        start_time=(base_time + timedelta(hours=1)).isoformat(),  # Move to 3 PM
        client_id=client.id,
        clinician_id=clinician.id,
        appointment_id=appointment.id
    )
    
    calendar = agent._get_clinician_calendar(clinician.id)
    validated_actions = agent._validate_actions([valid_update_action], calendar)
    
    print(f"Valid update action: {valid_update_action}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 1:
        print("✅ Valid update action properly accepted")
    else:
        print("❌ Valid update action incorrectly rejected")
    
    # Test 2: Update non-existent appointment
    print("\n--- Test 2: Update non-existent appointment ---")
    invalid_update_action = AppointmentAction(
        action="update",
        start_time=(base_time + timedelta(hours=1)).isoformat(),
        client_id=client.id,
        clinician_id=clinician.id,
        appointment_id=99999  # Non-existent ID
    )
    
    validated_actions = agent._validate_actions([invalid_update_action], calendar)
    print(f"Invalid update action (non-existent appointment): {invalid_update_action}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 0:
        print("✅ Invalid update action properly rejected")
    else:
        print("❌ Invalid update action incorrectly accepted")


def test_multiple_action_validation():
    """Test validation when multiple actions are proposed."""
    print("\n=== Testing Multiple Action Validation ===\n")
    
    # Create test scenario
    clinician, created = User.objects.get_or_create(
        username='multiple_test_clinician',
        defaults={
            'first_name': 'Multiple',
            'last_name': 'Test',
            'email': 'multiple@test.com'
        }
    )
    
    client1, created = Client.objects.get_or_create(
        id=303,
        defaults={
            'first_name': 'Multiple',
            'last_name': 'Client 1',
            'clinician': clinician
        }
    )
    
    client2, created = Client.objects.get_or_create(
        id=304,
        defaults={
            'first_name': 'Multiple',
            'last_name': 'Client 2',
            'clinician': clinician
        }
    )
    
    # Clear existing appointments
    Appointment.objects.filter(clinician=clinician).delete()
    
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=5)
    
    # Test multiple actions that conflict with each other
    print("--- Test: Multiple conflicting actions ---")
    
    action1 = AppointmentAction(
        action="create",
        start_time=base_time.isoformat(),  # 9 AM
        client_id=client1.id,
        clinician_id=clinician.id
    )
    
    action2 = AppointmentAction(
        action="create",
        start_time=(base_time + timedelta(minutes=30)).isoformat(),  # 9:30 AM (conflicts)
        client_id=client2.id,
        clinician_id=clinician.id
    )
    
    agent = AppointmentRequestAgent()
    calendar = agent._get_clinician_calendar(clinician.id)
    validated_actions = agent._validate_actions([action1, action2], calendar)
    
    print(f"Action 1: {action1}")
    print(f"Action 2: {action2}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 1:
        print("✅ Conflict between actions properly detected")
    else:
        print("❌ Conflict between actions not detected")
    
    # Test multiple actions that don't conflict
    print("\n--- Test: Multiple non-conflicting actions ---")
    
    action3 = AppointmentAction(
        action="create",
        start_time=base_time.isoformat(),  # 9 AM
        client_id=client1.id,
        clinician_id=clinician.id
    )
    
    action4 = AppointmentAction(
        action="create",
        start_time=(base_time + timedelta(hours=1)).isoformat(),  # 10 AM (no conflict)
        client_id=client2.id,
        clinician_id=clinician.id
    )
    
    validated_actions = agent._validate_actions([action3, action4], calendar)
    print(f"Action 3: {action3}")
    print(f"Action 4: {action4}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 2:
        print("✅ Non-conflicting actions properly accepted")
    else:
        print("❌ Non-conflicting actions incorrectly rejected")


def test_edge_cases():
    """Test edge cases in validation."""
    print("\n=== Testing Edge Cases ===\n")
    
    # Create test scenario
    clinician, created = User.objects.get_or_create(
        username='edge_test_clinician',
        defaults={
            'first_name': 'Edge',
            'last_name': 'Test',
            'email': 'edge@test.com'
        }
    )
    
    client, created = Client.objects.get_or_create(
        id=305,
        defaults={
            'first_name': 'Edge',
            'last_name': 'Client',
            'clinician': clinician
        }
    )
    
    # Clear existing appointments
    Appointment.objects.filter(clinician=clinician).delete()
    
    # Create appointments with edge case timing
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=6)
    
    # Appointment 1: 9:00-9:50
    appt1 = Appointment.objects.create(
        start_time=base_time,
        duration_in_minutes=50,
        client=client,
        clinician=clinician
    )
    
    # Appointment 2: 10:00-10:50
    appt2 = Appointment.objects.create(
        start_time=base_time + timedelta(hours=1),
        duration_in_minutes=50,
        client=client,
        clinician=clinician
    )
    
    print(f"Created appointments:")
    print(f"  Appointment 1: {base_time.strftime('%H:%M')} - {(base_time + timedelta(minutes=50)).strftime('%H:%M')}")
    print(f"  Appointment 2: {(base_time + timedelta(hours=1)).strftime('%H:%M')} - {(base_time + timedelta(hours=1, minutes=50)).strftime('%H:%M')}")
    
    agent = AppointmentRequestAgent()
    calendar = agent._get_clinician_calendar(clinician.id)
    
    # Test edge case: appointment exactly at the boundary
    print("\n--- Test: Boundary timing ---")
    
    # Test 1: Appointment at 9:50 (should be allowed - no conflict with 9:00-9:50)
    boundary_action = AppointmentAction(
        action="create",
        start_time=(base_time + timedelta(minutes=50)).isoformat(),  # Exactly at 9:50
        client_id=client.id,
        clinician_id=clinician.id
    )
    
    validated_actions = agent._validate_actions([boundary_action], calendar)
    print(f"Boundary action (9:50): {boundary_action}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 1:
        print("✅ Boundary timing properly handled")
    else:
        print("❌ Boundary timing incorrectly handled")
    
    # Test 2: Appointment at 9:30 (should conflict with 9:00-9:50)
    conflict_action = AppointmentAction(
        action="create",
        start_time=(base_time + timedelta(minutes=30)).isoformat(),  # At 9:30 (conflicts)
        client_id=client.id,
        clinician_id=clinician.id
    )
    
    validated_actions = agent._validate_actions([conflict_action], calendar)
    print(f"Conflict action (9:30): {conflict_action}")
    print(f"Validation result: {len(validated_actions)} valid actions")
    
    if len(validated_actions) == 0:
        print("✅ Conflict timing properly detected")
    else:
        print("❌ Conflict timing not detected")


def main():
    """Main test function."""
    print("Starting Comprehensive Validation Tests...")
    
    # Test conflict detection
    test_conflict_detection()
    
    # Test update validation
    test_update_validation()
    
    # Test multiple action validation
    test_multiple_action_validation()
    
    # Test edge cases
    test_edge_cases()
    
    print("\n=== All Validation Tests Completed! ===")


if __name__ == "__main__":
    main() 