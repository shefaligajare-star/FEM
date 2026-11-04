from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ENTREPRENEUR = 'ENTREPRENEUR', 'Entrepreneur'
        MENTOR = 'MENTOR', 'Mentor'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ENTREPRENEUR,
        help_text="User's primary role on the platform"
    )
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    bio = models.TextField(blank=True, default='')

    @property
    def is_entrepreneur(self):
        return self.role == self.Role.ENTREPRENEUR

    @property
    def is_mentor(self):
        return self.role == self.Role.MENTOR

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def display_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username
