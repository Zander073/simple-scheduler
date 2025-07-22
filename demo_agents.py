#!/usr/bin/env python3
"""
Demo script showcasing the multi-agent system in action with seed data.
This script demonstrates each agent's capabilities using realistic scenarios.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_scheduler.settings')
django.setup()

from appointments.models import Client, Appointment
from agents.supervisor import SupervisorAgent


def demo_availability_optimizer():
    """Demo 1: Availability Optimizer - Optimize clinician workload"""
    print("\n" + "="*60)
    print("DEMO 1: AVAILABILITY OPTIMIZER")
    print("="*60)

    # Get a clinician with appointments
    clinician = Client.objects.first().clinician
    print(f"Analyzing workload for: {clinician.get_full_name()}")

    # Use the supervisor to route to availability optimizer
    state = f"The clinician {clinician.get_full_name()} has an unbalanced workload this week."

    supervisor = SupervisorAgent()
    result = supervisor.handle_request(
        state,
        clinician_id=clinician.id
    )

    print(f"\nOptimization Result:")
    print(f"  Clinician ID: {result.clinician_id}")
    print(f"  Suggested Availability: {result.suggested_availability}")
    print(f"  Reasoning: {result.reasoning}")


def demo_preference_learner():
    """Demo 2: Preference Learner - Learn client scheduling patterns"""
    print("\n" + "="*60)
    print("DEMO 2: PREFERENCE LEARNER")
    print("="*60)
    
    # Get a client with appointment history
    client = Client.objects.first()
    print(f"Learning preferences for: {client.full_name}")
    
    # Use the supervisor to route to preference learner
    state = f"Client {client.full_name} has been scheduling appointments and we need to understand their preferences."
    
    supervisor = SupervisorAgent()
    result = supervisor.handle_request(
        state, 
        client_id=client.id
    )
    
    print(f"\nPreference Learning Result:")
    print(f"  Client ID: {result.client_id}")
    print(f"  Learned Preferences: {result.learned_preferences}")
    print(f"  Reasoning: {result.reasoning}")


def demo_scheduling_agent():
    """Demo 3: Scheduling Agent - Suggest optimal appointment times"""
    print("\n" + "="*60)
    print("DEMO 3: SCHEDULING AGENT")
    print("="*60)
    
    # Get a client and their preferences
    client = Client.objects.first()
    print(f"Scheduling for: {client.full_name}")
    
    # Use the supervisor to route to scheduling agent
    state = f"Client {client.full_name} needs to book a new appointment. We have available time slots and want to suggest the best appointment time for them to book."
    
    supervisor = SupervisorAgent()
    result = supervisor.handle_request(
        state, 
        client_id=client.id
    )
    
    print(f"\nScheduling Result:")
    print(f"  Client ID: {result.client_id}")
    print(f"  Proposed Time: {result.proposed_time}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Reasoning: {result.reasoning}")


def main():
    """Run all demos"""
    print("🤖 MULTI-AGENT SCHEDULING SYSTEM DEMO")
    print("="*60)
    print("This demo showcases three specialized agents working together:")
    print("1. Availability Optimizer - Optimizes clinician workload")
    print("2. Preference Learner - Learns client scheduling patterns") 
    print("3. Scheduling Agent - Suggests optimal appointment times")
    print("="*60)
    
    # Check if we have seed data
    if not Client.objects.exists():
        print("❌ No seed data found! Please run the seed command first:")
        print("   uv run python manage.py seed_data")
        return
    
    print(f"✅ Found {Client.objects.count()} clients and {Appointment.objects.count()} appointments")
    
    try:
        # Run all demos
        demo_availability_optimizer()
        demo_preference_learner()
        demo_scheduling_agent()
        
        print("\n" + "="*60)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("The multi-agent system successfully:")
        print("• Analyzed clinician workload and suggested optimizations")
        print("• Learned client preferences from appointment history")
        print("• Suggested optimal appointment times based on availability and preferences")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 