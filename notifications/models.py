from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = [
        ('MENTOR_REQUEST', 'Mentoring Request Received'),
        ('REQUEST_ACCEPTED', 'Mentoring Request Accepted'),
        ('NEW_MESSAGE', 'New Message'),
        ('COLLABORATION_REQUEST', 'New Collaboration Interest'),
        ('COMMENT', 'New Community Comment'),
        ('REACTION', 'Post Reaction'),
        ('RECOMMENDATION', 'New Mentor Recommendations Ready'),
        ('SYNC_COMPLETED', 'Offline Data Synchronized'),
        ('SYNC_FAILED', 'Offline Synchronization Failed'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='RECOMMENDATION')
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.CharField(max_length=255, blank=True, default='')
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.title}"
