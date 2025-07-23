#!/usr/bin/env python
"""
Script to find available time slots for a clinician between two defined timestamps.
Run this in your Django shell after importing the necessary models.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_scheduler.settings')
django.setup()

from appointments.models import Appointment, Client
from django.contrib.auth.models import User


def find_available_slots(clinician_id, start_timestamp, end_timestamp, slot_duration_minutes=50):
    """
    Find all available time slots for a clinician between two timestamps.
    
    Args:
        clinician_id: ID of the clinician
        start_timestamp: Start datetime (timezone-aware)
        end_timestamp: End datetime (timezone-aware)
        slot_duration_minutes: Duration of each slot in minutes (default 50)
    
    Returns:
        List of available datetime slots
    """
    # Get all appointments for the clinician in the time range
    existing_appointments = Appointment.objects.filter(
        clinician_id=clinician_id,
        start_time__gte=start_timestamp,
        start_time__lt=end_timestamp
    ).order_by('start_time')
    
    print(f"Found {existing_appointments.count()} existing appointments for clinician {clinician_id}")
    
    # Create list of busy time periods
    busy_periods = []
    for appointment in existing_appointments:
        appointment_end = appointment.start_time + timedelta(minutes=appointment.duration_in_minutes)
        busy_periods.append((appointment.start_time, appointment_end))
        print(f"  Busy: {appointment.start_time} to {appointment_end}")
    
    # Generate all possible slots
    available_slots = []
    current_slot = start_timestamp
    
    # Round up to the next hour if not on the hour
    if current_slot.minute != 0:
        current_slot = current_slot.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    # Ensure we're within business hours (9 AM to 5 PM)
    business_start_hour = 9
    business_end_hour = 17
    
    while current_slot < end_timestamp:
        # Skip if outside business hours
        if current_slot.hour < business_start_hour or current_slot.hour >= business_end_hour:
            current_slot += timedelta(hours=1)
            continue
        
        # Check if this slot conflicts with any existing appointment
        slot_end = current_slot + timedelta(minutes=slot_duration_minutes)
        slot_conflicts = False
        
        for busy_start, busy_end in busy_periods:
            # Check for overlap: (slot_start < busy_end) and (busy_start < slot_end)
            if (current_slot < busy_end and busy_start < slot_end):
                slot_conflicts = True
                break
        
        if not slot_conflicts:
            available_slots.append(current_slot)
        
        current_slot += timedelta(hours=1)
    
    return available_slots


def main():
    """Main function to demonstrate finding available slots."""
    # Get the first clinician
    clinician = User.objects.filter(username__startswith='clinician').first()
    if not clinician:
        print("No clinician found. Creating a test clinician...")
        clinician = User.objects.create_user(
            username='clinician1',
            email='clinician1@example.com',
            password='testpass123'
        )
        print(f"Created clinician: {clinician.username}")
    
    print(f"Using clinician: {clinician.username} (ID: {clinician.id})")
    
    # Define time range (next 7 days, business hours only)
    now = timezone.now()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if start_time < now:
        start_time += timedelta(days=1)
    
    end_time = start_time + timedelta(days=7)
    
    print(f"\nSearching for available slots between:")
    print(f"  Start: {start_time}")
    print(f"  End: {end_time}")
    print(f"  Business hours: 9 AM - 5 PM")
    print(f"  Slot duration: 50 minutes")
    
    # Find available slots
    available_slots = find_available_slots(
        clinician_id=clinician.id,
        start_timestamp=start_time,
        end_timestamp=end_time,
        slot_duration_minutes=50
    )
    
    print(f"\nFound {len(available_slots)} available time slots:")
    print("-" * 60)
    
    for i, slot in enumerate(available_slots, 1):
        slot_end = slot + timedelta(minutes=50)
        print(f"{i:2d}. {slot.strftime('%A %Y-%m-%d at %H:%M')} - {slot_end.strftime('%H:%M')}")
    
    if not available_slots:
        print("No available slots found in the specified time range.")
    
    return available_slots


if __name__ == "__main__":
    main() 