from django.db import models
from django.conf import settings

class Expertise(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Expertises"
        ordering = ['name']

    def __str__(self):
        return self.name

class MentorProfile(models.Model):
    VERIFICATION_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified Mentor'),
        ('REJECTED', 'Not Verified'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    professional_title = models.CharField(max_length=200, default='Senior Business Mentor & Strategic Advisor')
    biography = models.TextField(default='Dedicated mentor with hands-on experience helping entrepreneurs overcome operational, financial, and market challenges.')
    years_of_experience = models.PositiveIntegerField(default=12)
    rural_business_experience = models.BooleanField(default=True)
    rural_businesses_count = models.PositiveIntegerField(default=12)
    primary_industry = models.CharField(max_length=120, default='Finance & Strategy')
    expertises = models.ManyToManyField(Expertise, related_name='mentors', blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='VERIFIED')
    is_accepting_mentees = models.BooleanField(default=True)
    preferred_stages = models.CharField(max_length=200, default='Early Stage, Growth, Scaling')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_verified(self):
        return self.verification_status == 'VERIFIED'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.professional_title}"

class MentorExperience(models.Model):
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='experiences')
    industry = models.CharField(max_length=100)
    problem_type = models.CharField(max_length=150, help_text="e.g. Cash Flow Management, Pricing Strategy, Rural Distribution")
    description = models.TextField()
    outcome = models.TextField(help_text="Measurable outcome achieved")
    years_of_experience = models.PositiveIntegerField(default=5)
    is_rural_focused = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mentor.user.get_full_name()} - {self.problem_type}"

class MentorCredit(models.Model):
    mentor = models.OneToOneField(MentorProfile, on_delete=models.CASCADE, related_name='credits')
    entrepreneurs_mentored = models.PositiveIntegerField(default=47)
    mentoring_hours = models.PositiveIntegerField(default=32)
    rural_businesses_supported = models.PositiveIntegerField(default=12)
    successful_outcomes = models.PositiveIntegerField(default=18)
    community_contributions = models.PositiveIntegerField(default=24)
    helpful_answers = models.PositiveIntegerField(default=38)
    positive_feedback_rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)

    @property
    def credit_score(self):
        # Weighted composite score representing tangible real-world impact
        score = (
            (self.entrepreneurs_mentored * 15) +
            (self.mentoring_hours * 8) +
            (self.rural_businesses_supported * 25) +
            (self.successful_outcomes * 35) +
            (self.community_contributions * 5) +
            (self.helpful_answers * 4)
        )
        return score

    def __str__(self):
        return f"Credits for {self.mentor.user.get_full_name()}: {self.credit_score} pts"

class AvailabilitySlot(models.Model):
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]

    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_type = models.CharField(max_length=100, default='1-on-1 Problem Diagnostic (45 min)')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')} ({self.mentor.user.get_full_name()})"
