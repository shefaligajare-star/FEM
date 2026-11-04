import uuid
from django.db import models
from django.conf import settings
from mentors.models import MentorProfile

class ProblemCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Problem Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class Problem(models.Model):
    URGENCY_CHOICES = [
        ('LOW', 'Low — Exploring future growth'),
        ('MEDIUM', 'Medium — Need solution within 1 month'),
        ('HIGH', 'High — Impeding daily operations'),
        ('CRITICAL', 'Critical — Immediate cash/operational crisis'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Looking for Mentor'),
        ('MATCHED', 'Matches Found'),
        ('IN_PROGRESS', 'Active Mentorship'),
        ('RESOLVED', 'Problem Resolved'),
    ]

    entrepreneur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='problems')
    title = models.CharField(max_length=200, help_text="Brief summary of the issue")
    description = models.TextField(help_text="Describe the problem in your own words")
    category = models.ForeignKey(ProblemCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='problems')
    industry = models.CharField(max_length=100, default='Agri-Food & Rural Production')
    business_stage = models.CharField(max_length=50, default='Early Stage')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='HIGH')
    desired_support = models.CharField(max_length=100, default='1-on-1 Strategy & Troubleshooting')
    is_rural_business = models.BooleanField(default=True)
    location = models.CharField(max_length=150, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="Offline sync idempotency ID")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.entrepreneur.get_full_name() or self.entrepreneur.username})"

class MentorMatch(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='matches')
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='matches')
    match_score = models.PositiveIntegerField(help_text="Overall composite match score 0-100")
    expertise_score = models.PositiveIntegerField(default=90)
    problem_similarity_score = models.PositiveIntegerField(default=90)
    industry_score = models.PositiveIntegerField(default=85)
    business_stage_score = models.PositiveIntegerField(default=88)
    rural_experience_score = models.PositiveIntegerField(default=92)
    outcomes_score = models.PositiveIntegerField(default=85)
    explanation = models.TextField(help_text="Detailed natural language breakdown of why this mentor was matched")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score', '-created_at']
        unique_together = ['problem', 'mentor']

    def __str__(self):
        return f"{self.mentor.user.get_full_name()} -> {self.problem.title} ({self.match_score}%)"

class MentoringRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Mentor Review'),
        ('ACCEPTED', 'Accepted — Ready for Session'),
        ('DECLINED', 'Declined'),
        ('COMPLETED', 'Mentorship Completed'),
    ]

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='requests')
    entrepreneur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentoring_requests_sent')
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='mentoring_requests_received')
    message = models.TextField(help_text="Personal note explaining why you'd value this mentor's guidance")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request from {self.entrepreneur.get_full_name()} to {self.mentor.user.get_full_name()} [{self.status}]"

class MentoringSession(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    request = models.OneToOneField(MentoringRequest, on_delete=models.CASCADE, related_name='session')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=45)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    meeting_link = models.CharField(max_length=255, default='https://fem.network/rooms/session-diagnostic')
    mentor_notes = models.TextField(blank=True, default='')
    entrepreneur_feedback = models.TextField(blank=True, default='')
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for Request #{self.request.id} ({self.status})"
