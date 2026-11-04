from django.db import models
from django.conf import settings

class OfflineSyncRecord(models.Model):
    STATUS_CHOICES = [
        ('SYNCED', 'Successfully Synchronized'),
        ('CONFLICT', 'Conflict Handled (Preserved Server Version)'),
        ('FAILED', 'Failed to Synchronize'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sync_records')
    operation_id = models.CharField(max_length=100, unique=True)
    entity_type = models.CharField(max_length=50)
    action = models.CharField(max_length=20, default='CREATE')
    client_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SYNCED')
    details = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-server_timestamp']

    def __str__(self):
        return f"Sync {self.operation_id} ({self.entity_type} {self.action}) by {self.user.username}"
