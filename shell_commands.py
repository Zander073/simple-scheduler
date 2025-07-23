# Copy and paste these commands into your Django shell

from datetime import datetime, timedelta
from django.utils import timezone
from appointments.models import Appointment, Client
from django.contrib.auth.models import User

# Get the first clinician
clinician = User.objects.filter(username__startswith='clinician').first()
print(f"Using clinician: {clinician.username} (ID: {clinician.id})")

# Define your time range (modify these as needed)
start_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
if start_time < timezone.now():
    start_time += timedelta(days=1)  # Start tomorrow if today is already past 9 AM

end_time = start_time + timedelta(days=7)  # Search for next 7 days

print(f"Searching between {start_time} and {end_time}")

# Get existing appointments for this clinician in the time range
existing_appointments = Appointment.objects.filter(
    clinician=clinician,
    start_time__gte=start_time,
    start_time__lt=end_time
).order_by('start_time')

print(f"Found {existing_appointments.count()} existing appointments:")

# Show existing appointments
for appt in existing_appointments:
    appt_end = appt.start_time + timedelta(minutes=appt.duration_in_minutes)
    print(f"  {appt.start_time.strftime('%A %Y-%m-%d at %H:%M')} - {appt_end.strftime('%H:%M')} ({appt.client.full_name})")

# Find available slots
available_slots = []
current_slot = start_time

# Business hours: 9 AM to 5 PM
business_start_hour = 9
business_end_hour = 17
slot_duration = 50  # minutes

while current_slot < end_time:
    # Skip if outside business hours
    if current_slot.hour < business_start_hour or current_slot.hour >= business_end_hour:
        current_slot += timedelta(hours=1)
        continue
    
    # Check if this slot conflicts with any existing appointment
    slot_end = current_slot + timedelta(minutes=slot_duration)
    slot_conflicts = False
    
    for appt in existing_appointments:
        appt_end = appt.start_time + timedelta(minutes=appt.duration_in_minutes)
        # Check for overlap: (slot_start < appt_end) and (appt_start < slot_end)
        if (current_slot < appt_end and appt.start_time < slot_end):
            slot_conflicts = True
            break
    
    if not slot_conflicts:
        available_slots.append(current_slot)
    
    current_slot += timedelta(hours=1)

print(f"\nFound {len(available_slots)} available time slots:")
print("-" * 60)

for i, slot in enumerate(available_slots, 1):
    slot_end = slot + timedelta(minutes=slot_duration)
    print(f"{i:2d}. {slot.strftime('%A %Y-%m-%d at %H:%M')} - {slot_end.strftime('%H:%M')}")

if not available_slots:
    print("No available slots found in the specified time range.")

# Optional: Save the available slots to a variable for further use
available_slots_list = available_slots 