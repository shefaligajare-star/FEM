from django.db import models
from django.conf import settings

class EntrepreneurProfile(models.Model):
    STAGE_CHOICES = [
        ('IDEA', 'Idea & Validation'),
        ('EARLY', 'Early Stage / Initial Sales'),
        ('GROWTH', 'Growth & Expansion'),
        ('SCALING', 'Scaling Operations'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='entrepreneur_profile')
    business_name = models.CharField(max_length=200, default='New Venture')
    industry = models.CharField(max_length=100, default='Agri-Food & Rural Products')
    business_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='EARLY')
    location = models.CharField(max_length=150, blank=True, default='')
    is_rural_business = models.BooleanField(default=True)
    description = models.TextField(blank=True, default='Passionate entrepreneur solving regional market needs.')
    skills = models.TextField(blank=True, default='Operations, Local Sourcing, Product Formulation')
    collaboration_interests = models.TextField(blank=True, default='Distribution channels, sustainable packaging, supply-chain partners')
    employee_count = models.CharField(max_length=50, blank=True, default='1-10 employees')
    annual_revenue_range = models.CharField(max_length=50, blank=True, default='Under $50k')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} ({self.user.get_full_name() or self.user.username})"
