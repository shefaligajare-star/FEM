import uuid
from django.db import models
from django.conf import settings

class CommunityPost(models.Model):
    POST_TYPES = [
        ('QUESTION', 'Question — Seeking guidance from peers & mentors'),
        ('DISCUSSION', 'Discussion — Industry trends & strategic insights'),
        ('ADVICE', 'Advice — Lessons learned from the field'),
        ('OPPORTUNITY', 'Opportunity — Market access, grants, or events'),
        ('COLLABORATION', 'Collaboration — Seeking business partners'),
        ('RESOURCE', 'Resource — Practical templates, tools, or guides'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='QUESTION')
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags e.g. CashFlow, RuralLogistics, Pricing")
    likes_count = models.PositiveIntegerField(default=0)
    is_reported = models.BooleanField(default=False)
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_post_type_display().split(' ')[0]}] {self.title}"

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

class Comment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_comments')
    content = models.TextField()
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.get_full_name() or self.author.username} on #{self.post.id}"

class Reaction(models.Model):
    REACTION_TYPES = [
        ('LIKE', 'Agree / Like'),
        ('INSIGHTFUL', 'Insightful'),
        ('HELPFUL', 'Very Helpful'),
    ]

    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES, default='LIKE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']

class SavedPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
