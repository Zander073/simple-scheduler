from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random
from appointments.models import Client, Appointment


class Command(BaseCommand):
    help = 'Seed the database with sample clients and appointments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clinicians',
            type=int,
            default=3,
            help='Number of clinicians to create'
        )
        parser.add_argument(
            '--clients-per-clinician',
            type=int,
            default=8,
            help='Number of clients per clinician'
        )

    def handle(self, *args, **options):
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        User.objects.filter(username__startswith='clinician').delete()
        Client.objects.all().delete()
        Appointment.objects.all().delete()

        self.stdout.write('Seeding database...')

        # Create clinicians
        clinicians = self.create_clinicians(options['clinicians'])

        # Create clients for each clinician
        all_clients = []
        for clinician in clinicians:
            clients = self.create_clients_for_clinician(clinician, options['clients_per_clinician'])
            all_clients.extend(clients)

        # Create appointments
        self.create_appointments(clinicians, all_clients)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded database with {len(clinicians)} clinicians, {len(all_clients)} clients, and appointments')
        )

    def create_clinicians(self, count):
        """Create sample clinicians"""
        clinicians = []
        for i in range(count):
            username = f'clinician{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': f'Dr. {["Smith", "Johnson", "Williams", "Brown", "Jones"][i % 5]}',
                    'last_name': f'{"ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i % 26]}',
                    'email': f'{username}@therapyclinic.com',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            clinicians.append(user)
            self.stdout.write(f'Created clinician: {user.get_full_name()}')
        return clinicians

    def create_clients_for_clinician(self, clinician, count):
        """Create sample clients for a clinician"""
        first_names = ['Alice', 'Bob', 'Carol', 'David', 'Eva', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack']
        last_names = ['Anderson', 'Baker', 'Clark', 'Davis', 'Evans', 'Fisher', 'Garcia', 'Harris', 'Ivanov', 'Johnson']

        clients = []
        for i in range(count):
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]

            client, created = Client.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                clinician=clinician,
                defaults={
                    'memo': f'Sample client {i+1} for {clinician.get_full_name()}'
                }
            )
            if created:
                clients.append(client)
                self.stdout.write(f'Created client: {client.full_name} for {clinician.get_full_name()}')

        return clients

    def create_appointments(self, clinicians, clients):
        """Create recurring weekly appointments"""
        # Start 5 weeks ago, go 2 weeks into the future (7 weeks total)
        start_date = timezone.now().date() - timedelta(weeks=5)
        end_date = timezone.now().date() + timedelta(weeks=2)

        # Business hours: 9 AM to 5 PM
        business_hours = [9, 10, 11, 12, 13, 14, 15, 16]  # 9 AM to 4 PM (last appointment starts at 4 PM)

        # Common client preferences (day of week, time preferences)
        # Note: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday (no weekends)
        client_preferences = [
            {'days': [0, 1], 'times': [9, 10, 11], 'description': 'Prefers Monday/Tuesday mornings'},
            {'days': [1, 2], 'times': [14, 15, 16], 'description': 'Prefers Tuesday/Wednesday afternoons'},
            {'days': [2, 3], 'times': [10, 11, 12], 'description': 'Prefers Wednesday/Thursday mid-morning'},
            {'days': [3, 4], 'times': [13, 14, 15], 'description': 'Prefers Thursday/Friday afternoons'},
            {'days': [0, 4], 'times': [9, 10, 16], 'description': 'Prefers Monday/Friday bookends'},
            {'days': [1, 3], 'times': [11, 12, 13], 'description': 'Prefers Tuesday/Thursday lunch time'},
            {'days': [0, 2, 4], 'times': [10, 11, 14], 'description': 'Prefers Monday/Wednesday/Friday mixed'},
            {'days': [1, 2, 3], 'times': [9, 10, 11, 14, 15], 'description': 'Prefers Tuesday/Wednesday/Thursday flexible'},
        ]

        appointments_created = 0
        client_preferences_map = {}  # Track preferences for each client

        for client in clients:
            # Assign random preferences to each client
            preferences = random.choice(client_preferences)
            client_preferences_map[client.id] = preferences

            # Create 15-30 appointments per client over the 7-week period
            num_appointments = random.randint(15, 30)

            # Generate appointment times based on client preferences
            appointment_times = []
            current_date = start_date

            while current_date <= end_date and len(appointment_times) < num_appointments:
                # Check if this day matches client preferences
                if current_date.weekday() in preferences['days']:
                    # Pick a random preferred time
                    hour = random.choice(preferences['times'])

                    # Skip if outside business hours
                    if hour in business_hours:
                        appointment_time = datetime.combine(
                            current_date,
                            datetime.min.time().replace(hour=hour)
                        )
                        appointment_time = timezone.make_aware(appointment_time)
                        appointment_times.append(appointment_time)

                current_date += timedelta(days=1)

            # Create appointments
            for appointment_time in appointment_times:
                # Check if this time slot is available (simple check - could be more sophisticated)
                existing_appointment = Appointment.objects.filter(
                    clinician=client.clinician,
                    start_time=appointment_time
                ).first()

                if not existing_appointment:
                    appointment = Appointment.objects.create(
                        start_time=appointment_time,
                        duration_in_minutes=60,  # 1 hour appointments
                        client=client,
                        clinician=client.clinician
                    )
                    appointments_created += 1

        # Update client memos with their scheduling preferences
        for client in clients:
            if client.id in client_preferences_map:
                preferences = client_preferences_map[client.id]
                client.memo = preferences['description']
                client.save()

        self.stdout.write(f'Created {appointments_created} appointments')

        # Print some statistics
        for clinician in clinicians:
            clinician_appointments = Appointment.objects.filter(clinician=clinician).count()
            clinician_clients = Client.objects.filter(clinician=clinician).count()
            self.stdout.write(f'{clinician.get_full_name()}: {clinician_clients} clients, {clinician_appointments} appointments')
