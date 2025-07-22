from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    """
    Simple client model for hackathon demo.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    memo = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(models.Model):
    """
    Simple appointment model for hackathon demo.
    """
    start_time = models.DateTimeField()
    duration_in_minutes = models.PositiveIntegerField(default=50)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='appointments')
    clinician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')

    def __str__(self):
        return f"{self.client.full_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
