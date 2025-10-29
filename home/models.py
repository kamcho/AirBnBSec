from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from users.models import Client
import os

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
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    
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


def evidence_upload_path(instance, filename):
    """
    Returns the upload path for evidence files.
    Format: evidence/incident_<id>/<filename>
    """
    # Ensure the directory exists
    import os
    path = f'evidence/incident_{instance.incident.id}'
    os.makedirs(os.path.join(settings.MEDIA_ROOT, path), exist_ok=True)
    return os.path.join(path, filename)


class IncidentEvidence(models.Model):
    """
    Model to store evidence files (images/videos) for security incidents
    """
    EVIDENCE_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]
    
    incident = models.ForeignKey(SecurityIncident, on_delete=models.CASCADE, related_name='evidence')
    file = models.FileField(upload_to=evidence_upload_path, help_text='Upload image or video evidence')
    file_type = models.CharField(max_length=10, choices=EVIDENCE_TYPES, help_text='Type of evidence file')
    description = models.TextField(blank=True, null=True, help_text='Brief description of the evidence')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, help_text='User who uploaded the evidence')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    file_size = models.PositiveIntegerField(help_text='File size in bytes', default=0)
    mime_type = models.CharField(max_length=100, blank=True, help_text='MIME type of the file')
    
    class Meta:
        verbose_name = 'Incident Evidence'
        verbose_name_plural = 'Incident Evidence'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Evidence for {self.incident.incident_id} - {self.get_file_type_display()}"
    
    def save(self, *args, **kwargs):
        """
        Override save to set file_type and file_size before saving
        """
        is_new = not self.pk  # Check if this is a new instance
        
        if is_new:
            # Set file size
            self.file_size = self.file.size
            
            # Get file extension and set file type
            file_name = self.file.name.lower()
            
            # Image extensions
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']
            # Video extensions
            video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm']
            # Document extensions
            document_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.csv']
            
            # Determine file type based on extension
            for ext in image_extensions:
                if file_name.endswith(ext):
                    self.file_type = 'image'
                    break
            else:
                for ext in video_extensions:
                    if file_name.endswith(ext):
                        self.file_type = 'video'
                        break
                else:
                    for ext in document_extensions:
                        if file_name.endswith(ext):
                            self.file_type = 'document'
                            break
                    else:
                        self.file_type = 'other'
        
        super().save(*args, **kwargs)
        
        # If this is a new file and it's an image, create thumbnails
        if is_new and self.file_type == 'image':
            self.create_thumbnails()
    
    def create_thumbnails(self):
        """
        Create thumbnails for image evidence
        """
        from PIL import Image
        from io import BytesIO
        from django.core.files.base import ContentFile
        import os
        
        try:
            # Open the original image
            img = Image.open(self.file.path)
            
            # Create a thumbnail (200x200)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Save the thumbnail
            thumb_name, thumb_extension = os.path.splitext(self.file.name)
            thumb_extension = thumb_extension.lower()
            thumb_filename = f"{thumb_name}_thumb{thumb_extension}"
            
            # Handle different image formats
            if thumb_extension in ['.jpg', '.jpeg']:
                FTYPE = 'JPEG'
            elif thumb_extension == '.png':
                FTYPE = 'PNG'
            elif thumb_extension == '.gif':
                FTYPE = 'GIF'
            else:
                FTYPE = 'JPEG'  # Default to JPEG
            
            # Save the thumbnail to a BytesIO object
            temp_thumb = BytesIO()
            img.save(temp_thumb, FTYPE, quality=85)
            temp_thumb.seek(0)
            
            # Save to the thumbnail field if it exists
            if hasattr(self, 'thumbnail'):
                self.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
                temp_thumb.close()
            
        except Exception as e:
            # If there's an error, just log it and continue
            print(f"Error creating thumbnail: {str(e)}")
    
    def get_file_icon(self):
        """
        Returns the appropriate Bootstrap icon class based on file type
        """
        icons = {
            'image': 'bi-image',
            'video': 'bi-film',
            'document': 'bi-file-earmark-text',
            'pdf': 'bi-file-pdf',
            'spreadsheet': 'bi-file-spreadsheet',
            'word': 'bi-file-word',
        }
        
        if self.file_type == 'document':
            if self.file.name.lower().endswith('.pdf'):
                return icons['pdf']
            elif any(ext in self.file.name.lower() for ext in ['.xls', '.xlsx', '.csv']):
                return icons['spreadsheet']
            elif any(ext in self.file.name.lower() for ext in ['.doc', '.docx', '.rtf', '.odt']):
                return icons['word']
        
        return icons.get(self.file_type, 'bi-file-earmark')
    
    def delete(self, *args, **kwargs):
        """
        Delete the file from storage when the model instance is deleted
        """
        # Delete the file from storage
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        
        # Delete the thumbnail if it exists
        if hasattr(self, 'thumbnail') and self.thumbnail:
            if os.path.isfile(self.thumbnail.path):
                os.remove(self.thumbnail.path)
        
        # Delete the parent directory if it's empty
        file_dir = os.path.dirname(self.file.path)
        if os.path.exists(file_dir) and not os.listdir(file_dir):
            os.rmdir(file_dir)
        
        super().delete(*args, **kwargs)


class Comment(models.Model):
    """
    Model to store comments on security incidents
    """
    incident = models.ForeignKey(SecurityIncident, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incident_comments')
    content = models.TextField(help_text='Comment text')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Incident Comment'
        verbose_name_plural = 'Incident Comments'
    
    def __str__(self):
        return f'Comment by {self.user.username} on {self.incident.incident_id}'
    
    def user_full_name(self):
        """Return the user's full name if available, otherwise username"""
        return self.user.get_full_name() or self.user.username
    
    def user_initials(self):
        """Return the user's initials based on their full name or username"""
        full_name = self.user.get_full_name().strip()
        if full_name:
            # Get first letters of first and last name
            parts = full_name.split()
            if len(parts) > 1:
                return (parts[0][0] + parts[-1][0]).upper()
            return full_name[:2].upper()
        # Fallback to first two characters of username
        return self.user.username[:2].upper() if self.user.username else '??'
    
    def user_avatar_url(self):
        """Return the URL of the default avatar"""
        return '/static/images/default-avatar.png'


def video_upload_path(instance, filename):
    """
    Returns the upload path for explainer videos.
    Format: videos/incident_<id>/<filename>
    """
    return f'videos/incident_{instance.incident.id}/{filename}'


class ExplainerVideo(models.Model):
    """
    Model to store video explanations for incidents
    """
    incident = models.OneToOneField(
        SecurityIncident,
        on_delete=models.CASCADE,
        related_name='explainer_video',
        help_text='The incident this video explains'
    )
    video = models.FileField(
        upload_to=video_upload_path,
        help_text='Upload a video explanation of the incident',
        validators=[
            FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'mov', 'avi'])
        ]
    )
    title = models.CharField(
        max_length=200,
        help_text='Title for the explainer video',
        default='Incident Explanation'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Optional description of the video content'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_videos',
        help_text='User who uploaded the video'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Explainer Video'
        verbose_name_plural = 'Explainer Videos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Video for {self.incident.incident_id} by {self.uploaded_by}'

    def get_absolute_url(self):
        return self.video.url
