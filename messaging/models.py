import uuid
from django.db import models
from django.conf import settings
from django.db.models import Q

class Conversation(models.Model):
    participant_1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_p1')
    participant_2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_p2')
    subject = models.CharField(max_length=200, blank=True, default='Mentorship Discussion')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def get_other_participant(self, current_user):
        if self.participant_1 == current_user:
            return self.participant_2
        return self.participant_1

    @classmethod
    def get_or_create_conversation(cls, user_a, user_b, subject='Mentorship Discussion'):
        if user_a.id > user_b.id:
            user_a, user_b = user_b, user_a
        conv, created = cls.objects.get_or_create(
            participant_1=user_a,
            participant_2=user_b,
            defaults={'subject': subject}
        )
        return conv, created

    @property
    def latest_message(self):
        return self.messages.order_by('-created_at').first()

    def __str__(self):
        return f"Conversation: {self.participant_1.get_full_name()} & {self.participant_2.get_full_name()}"

class Message(models.Model):
    SYNC_CHOICES = [
        ('SYNCED', 'Synced to Server'),
        ('PENDING', 'Pending Offline Sync'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    read_status = models.BooleanField(default=False)
    sync_status = models.CharField(max_length=20, choices=SYNC_CHOICES, default='SYNCED')
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg from {self.sender.username} at {self.created_at.strftime('%H:%M')}"
