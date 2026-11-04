import uuid
from django.db import models
from django.conf import settings

class Story(models.Model):
    STORY_TYPES = [
        ('SUCCESS', 'Success Story — Proven Breakthroughs & Milestones'),
        ('FAILURE', 'Failure & Pivot — Crucial Lessons from the Field'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    story_type = models.CharField(max_length=20, choices=STORY_TYPES, default='FAILURE')
    title = models.CharField(max_length=200)
    business_context = models.CharField(max_length=150, help_text="e.g. Rural Dairy Cooperative, Seed Stage")
    summary = models.TextField(help_text="A brief 1-2 sentence executive summary of the journey")
    what_happened = models.TextField(help_text="The detailed facts of what unfolded")
    what_i_learned = models.TextField(help_text="The core operational or strategic insight gained")
    what_i_would_do_differently = models.TextField(help_text="Concrete actions you would take with today's perspective")
    key_takeaway = models.CharField(max_length=255, help_text="One memorable rule of thumb for fellow entrepreneurs")
    likes_count = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=True)
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Stories"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_story_type_display().split(' ')[0]}] {self.title}"

class StoryLike(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='story_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['story', 'user']
