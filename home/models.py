from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# Create your models here.

class SecurityIncident(models.Model):
    """
    Model to track security incidents related to rental properties
    """
    
    INCIDENT_TYPES = [
        ('fraud', 'Fraud Attempt'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('property_damage', 'Property Damage'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('verification_failure', 'Verification Failure'),
        ('payment_fraud', 'Payment Fraud'),
        ('identity_theft', 'Identity Theft'),
        ('harassment', 'Harassment'),
        ('noise_complaint', 'Noise Complaint'),
        ('other', 'Other'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ]
    
    # Basic Information
    incident_id = models.CharField(max_length=20, unique=True, help_text="Unique incident identifier")
    title = models.CharField(max_length=200, help_text="Brief description of the incident")
    description = models.TextField(help_text="Detailed description of the incident")
    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPES, help_text="Type of security incident")
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium', help_text="Severity level of the incident")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='reported', help_text="Current status of the incident")
    
    # Property and User Information
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_incidents', help_text="User who reported the incident")
    
    # Guest/User involved
    guest_name = models.CharField(max_length=100, blank=True, null=True, help_text="Name of guest involved in incident")
    guest_email = models.EmailField(blank=True, null=True, help_text="Email of guest involved in incident")
    guest_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Phone number of guest involved")
    
    # Timestamps
    incident_date = models.DateTimeField(help_text="Date and time when the incident occurred")
    reported_date = models.DateTimeField(auto_now_add=True, help_text="Date and time when incident was reported")
    resolved_date = models.DateTimeField(null=True, blank=True, help_text="Date and time when incident was resolved")
    
    # Location and Evidence
    location_description = models.TextField(blank=True, null=True, help_text="Specific location within property where incident occurred")
    evidence_files = models.JSONField(default=list, blank=True, help_text="List of file paths to evidence (photos, videos, documents)")
    
    # Financial Impact
    estimated_damage_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Estimated cost of damages")
    
    # Resolution Details
    resolution_notes = models.TextField(blank=True, null=True, help_text="Notes about how the incident was resolved")
    
    # External References
    police_report_number = models.CharField(max_length=50, blank=True, null=True, help_text="Police report number if applicable")
    
    # Risk Assessment
   
    
    # Flags
    
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reported_date']
        verbose_name = "Security Incident"
        verbose_name_plural = "Security Incidents"
        indexes = [
            models.Index(fields=['incident_type', 'status']),
            models.Index(fields=['severity', 'reported_date']),
            models.Index(fields=['reported_by', 'incident_date']),
        ]
    
    def __str__(self):
        return f"{self.incident_id} - {self.title} ({self.get_severity_display()})"
    
    def save(self, *args, **kwargs):
        if not self.incident_id:
            # Generate unique incident ID
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            self.incident_id = f"SEC{timestamp}"
        super().save(*args, **kwargs)
    
    @property
    def is_resolved(self):
        return self.status in ['resolved', 'closed']
    
    @property
    def days_since_reported(self):
        return (timezone.now() - self.reported_date).days
    
    @property
    def resolution_time_days(self):
        if self.resolved_date and self.reported_date:
            return (self.resolved_date - self.reported_date).days
        return None


class IncidentUpdate(models.Model):
    """
    Model to track updates and comments on security incidents
    """
    incident = models.ForeignKey(SecurityIncident, on_delete=models.CASCADE, related_name='updates')
    update_type = models.CharField(max_length=20, choices=[
        ('status_change', 'Status Change'),
        ('comment', 'Comment'),
        ('evidence_added', 'Evidence Added'),
        ('assignment_change', 'Assignment Change'),
        ('resolution', 'Resolution'),
    ])
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Update for {self.incident.incident_id} - {self.get_update_type_display()}"


