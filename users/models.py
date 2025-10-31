from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from django.utils import timezone

from django.core.files.storage import default_storage


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The email field must be set'))
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'Admin')
        
        # Ensure first_name and last_name are provided for superuser
        if not extra_fields.get('first_name'):
            extra_fields['first_name'] = 'Admin'
        if not extra_fields.get('last_name'):
            extra_fields['last_name'] = 'User'

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password=password, **extra_fields)

class MyUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Set email as the username field
    USERNAME_FIELD = 'email'
    # Required fields for createsuperuser (excluding USERNAME_FIELD)
    REQUIRED_FIELDS = []
    
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('House Manager', 'House Manager'),
    ]
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='House Manager',
        help_text=_('User role in the system')
    )
    
    # Fix related_name clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='myuser_set',
        related_query_name='myuser'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='myuser_set',
        related_query_name='myuser'
    )
    USERNAME_FIELD = 'email'

    objects = MyUserManager()

    def __str__(self):
        return self.email

class Subscription(models.Model):
    """
    Model representing a user's subscription.
    """
    user = models.OneToOneField(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        """A subscription is active if it has an expiry in the future."""
        return bool(self.expiry and timezone.now() < self.expiry)

    @property
    def status(self):
        """Returns 'active' if subscription is active, 'expired' otherwise"""
        return 'active' if self.is_active else 'expired'

    def __str__(self):
        return f"{self.user.email}'s subscription ({self.status})"

class PersonalProfile(models.Model):
    user = models.OneToOneField(
        MyUser, 
        on_delete=models.CASCADE, 
        related_name='profile',
        error_messages={
            'unique': 'A profile already exists for this user.',
            'invalid': 'Invalid user ID.',
        }
    )
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        default='O'
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"

    def save(self, *args, **kwargs):
        # Verify user exists
        if not self.user_id or not MyUser.objects.filter(id=self.user_id).exists():
            raise ValueError("Invalid user ID. The user must exist in the database.")
            
        # If first_name and last_name are not set, copy from user
        if not self.first_name and self.user.first_name:
            self.first_name = self.user.first_name
        if not self.last_name and self.user.last_name:
            self.last_name = self.user.last_name
            
        # Check if profile already exists for this user
        if not self.pk and PersonalProfile.objects.filter(user=self.user).exists():
            raise ValueError("A profile already exists for this user.")
            
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None



  


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ("info", "Info"),
        ("alert", "Alert"),
        ("reminder", "Reminder"),
        ("message", "Message"),
    ]
    recipient_user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default="info"
    )
    link = models.URLField(blank=True, null=True)
    expiry = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        target = self.recipient_user or self.recipient_learner
        return f"To {target}: {self.title}"

class Client(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    surname = models.CharField(max_length=100, null=True, blank=True)
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def get_full_name(self):
        """Return the full name of the client."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or str(self.id_number)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id_number})"

class NameAlias(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='name_aliases')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name}  {self.client.id_number}"

class ClientContact(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('address', 'Address'),
        ('emergency', 'Emergency Contact'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    contact = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'contact')
        ordering = ['contact_type', 'contact']
        verbose_name = 'Client Contact'
        verbose_name_plural = 'Client Contacts'
    
    def __str__(self):
        return f"{self.client} - {self.get_contact_type_display()}: {self.contact}"

class ClientImage(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('profile', 'Profile Picture'),
        ('id_front', 'ID Front'),
        ('id_back', 'ID Back'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='images')
    file = models.FileField(upload_to='client_files/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='image')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='other')
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Client File'
        verbose_name_plural = 'Client Files'
    
    def __str__(self):
        return f"{self.client} - {self.get_file_type_display()} ({self.get_content_type_display()})"