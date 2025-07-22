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

    # Get current week's appointments
    start_of_week = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_week - timedelta(days=start_of_week.weekday())
    end_of_week = start_of_week + timedelta(days=7)

    current_schedule = list(
        Appointment.objects.filter(
            clinician=clinician,
            start_time__gte=start_of_week,
            start_time__lt=end_of_week
        ).values_list('start_time', flat=True)
    )

    # Convert to ISO format for the agent
    current_schedule_iso = [dt.isoformat() for dt in current_schedule]

    print(f"Current week's appointments: {len(current_schedule)}")
    for appt in current_schedule:
        print(f"  - {appt.strftime('%Y-%m-%d %H:%M')}")

    # Use the supervisor to route to availability optimizer
    state = f"The clinician {clinician.get_full_name()} has an unbalanced workload this week with {len(current_schedule)} appointments."

    supervisor = SupervisorAgent()
    result = supervisor.handle_request(
        state,
        clinician_id=clinician.id,
        current_schedule=current_schedule_iso
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
    
    # Get client's appointment history
    appointments = Appointment.objects.filter(client=client).order_by('start_time')
    
    # Create a history summary
    history_parts = []
    for appt in appointments[:10]:  # Last 10 appointments
        day_name = appt.start_time.strftime('%A')
        time_str = appt.start_time.strftime('%H:%M')
        history_parts.append(f"{day_name} at {time_str}")
    
    history = f"Client has {appointments.count()} total appointments. Recent schedule: {', '.join(history_parts)}. Memo: {client.memo}"
    
    print(f"Client History: {history}")
    
    # Use the supervisor to route to preference learner
    state = f"Client {client.full_name} has been scheduling appointments and we need to understand their preferences."
    
    supervisor = SupervisorAgent()
    result = supervisor.handle_request(
        state, 
        client_id=client.id, 
        history=history
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
    
    # Get available time slots (next week, business hours)
    start_date = timezone.now().date() + timedelta(days=7)  # Next week
    end_date = start_date + timedelta(days=7)
    
    # Generate available slots (9 AM to 5 PM, weekdays)
    available_slots = []
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday
            for hour in range(9, 17):  # 9 AM to 5 PM
                slot_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                slot_time = timezone.make_aware(slot_time)
                
                # Check if slot is available (no existing appointment)
                existing = Appointment.objects.filter(
                    clinician=client.clinician,
                    start_time=slot_time
                ).exists()
                
                if not existing:
                    available_slots.append(slot_time.isoformat())
        
        current_date += timedelta(days=1)
    
    # Get client preferences from memo
    preferences = [client.memo] if client.memo else ["No specific preferences noted"]
    
    print(f"Available slots: {len(available_slots)}")
    print(f"Client preferences: {preferences}")
    
    # Use the supervisor to route to scheduling agent
    state = f"Client {client.full_name} needs to book a new appointment. We have available time slots and know their preferences. We need to suggest the best appointment time."
    
    supervisor = SupervisorAgent()
    result = supervisor.handle_request(
        state, 
        client_id=client.id, 
        availability=available_slots[:10],  # First 10 available slots
        preferences=preferences
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