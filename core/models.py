from django.db import models
from django.conf import settings
from django.utils import timezone
from users.models import Client
import json

class FreeTrial(models.Model):
    """Tracks free trial usage for a user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='free_trial'
    )
    count = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Free Trial'
        verbose_name_plural = 'Free Trials'

    def __str__(self):
        return f"{getattr(self.user, 'email', self.user_id)} free trial: {self.count} left"

class VerificationRequest(models.Model):
    """
    Model to track verification requests made via WhatsApp
    """
    # Request information
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_requests',
        help_text='User who requested the verification (if authenticated)'
    )
    
    # Contact information
    requester_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='Phone number of the person who requested verification'
    )
    
    # Verification details
    id_number = models.CharField(
        max_length=20,
        help_text='ID number that was verified'
    )
    
    # Verification results
    is_successful = models.BooleanField(
        default=False,
        help_text='Whether the verification was successful'
    )
    
    response_data = models.JSONField(
        default=dict,
        help_text='Raw response data from the verification service'
    )
    
    # Client information (if matched)
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verification_requests',
        help_text='Client record that was verified (if any)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this verification was requested'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the verification was completed'
    )
    
    # Additional metadata
    source = models.CharField(
        max_length=50,
        default='whatsapp',
        help_text='Source of the verification request (e.g., whatsapp, web, api)'
    )
    
    # Related incidents (many-to-many since a verification might relate to multiple incidents)
    related_incidents = models.ManyToManyField(
        'home.SecurityIncident',
        blank=True,
        related_name='verification_requests',
        help_text='Incidents related to this verification'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Verification Request'
        verbose_name_plural = 'Verification Requests'
    
    def __str__(self):
        status = '✅' if self.is_successful else '❌'
        return f"{status} {self.id_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Set completed_at if this is an update and status changed to successful
        if self.is_successful and not self.completed_at:
            self.completed_at = timezone.now()
        
        # If we have a client ID in the response data, try to link it
        if self.response_data and not self.client:
            try:
                client_id = self.response_data.get('data', {}).get('client_id')
                if client_id:
                    self.client = Client.objects.get(pk=client_id)
            except (Client.DoesNotExist, ValueError):
                pass
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('admin:core_verificationrequest_change', args=[str(self.id)])
    
    @property
    def verification_method(self):
        """Return a human-readable verification method"""
        return 'KRA API' if 'kra' in str(self.response_data).lower() else 'Manual'
    
    @property
    def verification_summary(self):
        """Return a summary of the verification result"""
        if self.is_successful:
            return f"Successfully verified {self.id_number}"
        return f"Verification failed for {self.id_number}"
    
    def link_to_client(self, client):
        """Link this verification to a client"""
        if not self.client:
            self.client = client
            self.save(update_fields=['client'])
            return True
        return False
