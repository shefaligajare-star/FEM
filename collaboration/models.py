import uuid
from django.db import models
from django.conf import settings

class CollaborationRequest(models.Model):
    COLLAB_TYPES = [
        ('SUPPLY_CHAIN', 'Supply Chain & Sourcing'),
        ('PACKAGING', 'Packaging & Processing'),
        ('DISTRIBUTION', 'Distribution & Shared Retail'),
        ('SHARED_RESOURCES', 'Shared Equipment & Facilities'),
        ('CO_MARKETING', 'Co-Marketing & Joint Campaigns'),
        ('TECH_PARTNER', 'Technology & Digital Enablement'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open for Collaboration'),
        ('IN_DISCUSSION', 'In Active Discussion'),
        ('FULFILLED', 'Partner Found / Completed'),
    ]

    entrepreneur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaboration_requests')
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Describe the collaboration opportunity, what you bring to the table, and what partner you need.")
    industry = models.CharField(max_length=100, default='Food & Agriculture')
    collaboration_type = models.CharField(max_length=30, choices=COLLAB_TYPES, default='SUPPLY_CHAIN')
    location = models.CharField(max_length=150, blank=True, default='Regional')
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags e.g. Food, Packaging, Rural Business")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.entrepreneur.get_full_name() or self.entrepreneur.username})"

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

class CollaborationInterest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Discussion'),
        ('ACCEPTED', 'Connected / Accepted'),
        ('DECLINED', 'Declined'),
    ]

    collaboration = models.ForeignKey(CollaborationRequest, on_delete=models.CASCADE, related_name='interests')
    entrepreneur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaboration_proposals')
    pitch_message = models.TextField(help_text="Introduce your business and how you can collaborate successfully.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['collaboration', 'entrepreneur']

    def __str__(self):
        return f"Interest from {self.entrepreneur.get_full_name()} on #{self.collaboration.id}"
