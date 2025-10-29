from django import forms
from django.contrib.auth.models import User
from .models import SecurityIncident, IncidentUpdate, IncidentEvidence, Comment, ExplainerVideo
from users.models import Client
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

class SecurityIncidentForm(forms.ModelForm):
    """Form for creating and updating security incidents"""
    
    class Meta:
        model = SecurityIncident
        fields = [
            'title', 'description', 'incident_type', 'severity', 'status',
            'client', 'incident_date', 'location_description', 
            'estimated_damage_cost', 'resolution_notes', 'police_report_number'
        ]
        widgets = {
            'incident_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'step': '60'  # 1 minute steps
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
            'location_description': forms.Textarea(attrs={'rows': 3}),
            'resolution_notes': forms.Textarea(attrs={'rows': 4}),
            'client': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set the format for the datetime field
        self.fields['incident_date'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Set initial value in correct format
        if not self.instance.pk:
            self.initial['incident_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    def clean_incident_date(self):
        incident_date = self.cleaned_data.get('incident_date')
        if incident_date and incident_date > timezone.now():
            raise forms.ValidationError("Incident date cannot be in the future.")
        return incident_date
    
    def save(self, commit=True):
        incident = super().save(commit=False)
        if self.user and not incident.pk:  # Only set reported_by for new incidents
            incident.reported_by = self.user
        if commit:
            incident.save()
        return incident

class IncidentUpdateForm(forms.ModelForm):
    """Form for creating incident updates"""
    
    class Meta:
        model = IncidentUpdate
        fields = ['update_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SecurityIncidentSearchForm(forms.Form):
    """Form for searching and filtering incidents"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search incidents...'})
    )
    incident_type = forms.ChoiceField(
        choices=[('', 'All Types')] + SecurityIncident.INCIDENT_TYPES,
        required=False
    )
    severity = forms.ChoiceField(
        choices=[('', 'All Severities')] + SecurityIncident.SEVERITY_LEVELS,
        required=False
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + SecurityIncident.STATUS_CHOICES,
        required=False
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

class SecurityIncidentStatusUpdateForm(forms.ModelForm):
    """Form for updating incident status"""
    
    class Meta:
        model = SecurityIncident
        fields = ['status', 'resolution_notes', 'resolved_date']
        widgets = {
            'resolved_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'resolution_notes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show resolved_date if status is being changed to resolved/closed
        if 'status' in self.data:
            status = self.data.get('status')
            if status not in ['resolved', 'closed']:
                self.fields['resolved_date'].widget = forms.HiddenInput()
        elif self.instance.pk and self.instance.status not in ['resolved', 'closed']:
            self.fields['resolved_date'].widget = forms.HiddenInput()


# Multi-step form classes
class IncidentStep1Form(forms.Form):
    """Step 1: Incident Information and Description"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of the incident'
        }),
        help_text="Provide a clear, concise title for the incident"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Detailed description of what happened...'
        }),
        help_text="Describe the incident in detail including what occurred, who was involved, and any relevant context"
    )
    incident_type = forms.ChoiceField(
        choices=SecurityIncident.INCIDENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the most appropriate category for this incident"
    )
    severity = forms.ChoiceField(
        choices=SecurityIncident.SEVERITY_LEVELS,
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Assess the severity level of this incident"
    )


class IncidentStep2Form(forms.Form):
    """Step 2: Date and Time Information"""
    incident_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
            'step': '60'
        }),
        help_text="When did this incident occur?"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value to current time
        if not self.data:
            self.initial['incident_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    def clean_incident_date(self):
        incident_date = self.cleaned_data.get('incident_date')
        if incident_date and incident_date > timezone.now():
            raise forms.ValidationError("Incident date cannot be in the future.")
        return incident_date


class IncidentStep3Form(forms.Form):
    """Step 3: Additional Details"""
    location_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Specific location within property where incident occurred...'
        }),
        help_text="Describe the exact location where the incident took place"
    )
    estimated_damage_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        help_text="Estimated cost of damages (optional)"
    )
    police_report_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Police report number if applicable'
        }),
        help_text="Police report number if law enforcement was involved"
    )
    resolution_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Notes about resolution or current status...'
        }),
        help_text="Any additional notes about the incident or its resolution"
    )


class IncidentStep4Form(forms.Form):
    """Step 4: Client Information"""
    USER_TYPE_CHOICES = [
        ('citizen', 'Kenyan Citizen (ID)'),
        ('alien', 'Alien (Alien ID)'),
        ('kra', 'KRA PIN Holder')
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        initial='citizen',
        widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
        help_text="Select the type of identification"
    )
    
    client_id_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ID/Passport/KRA PIN',
            'hx-post': '/verify-client/',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#id_verification_result'
        }),
        help_text="Enter the identification number"
    )
    
    client_first_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Client first name'
        }),
        help_text="First name of the client involved"
    )
    client_last_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Client last name'
        }),
        help_text="Last name of the client involved (optional)"
    )
    client_surname = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Client surname'
        }),
        help_text="Surname of the client involved (optional)"
    )
    client_id_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Client ID number'
        }),
        help_text="ID number of the client involved (optional)"
    )
    client_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'client@example.com'
        }),
        help_text="Email address of the client involved (optional)"
    )
    client_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890'
        }),
        help_text="Phone number of the client involved (optional)"
    )


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    
    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
    
    def value_omitted_from_data(self, data, files, name):
        return False


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,video/*,.pdf,.doc,.docx',
        }))
        super().__init__(*args, **kwargs)
    
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class IncidentEvidenceForm(forms.ModelForm):
    """Form for uploading evidence files for an incident"""
    
    file = MultipleFileField(
        required=True,
        help_text='You can select multiple files (max 10, 10MB each)'
    )
    
    class Meta:
        model = IncidentEvidence
        fields = ['file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter a description of this evidence...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.incident = kwargs.pop('incident', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_file(self):
        files = self.cleaned_data.get('file', [])
        if not files:
            raise forms.ValidationError('Please select at least one file.')
            
        if len(files) > 10:
            raise forms.ValidationError('You can upload a maximum of 10 files at once.')
            
        # Validate each file
        max_size = 10 * 1024 * 1024  # 10MB
        valid_mime_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv',
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        for f in files:
            if not f:
                continue
                
            # Validate file size (10MB max)
            if f.size > max_size:
                file_name = getattr(f, 'name', 'a file')
                raise forms.ValidationError(
                    f'File "{file_name}" is too large. Maximum size is 10MB. ' \
                    f'Your file is {f.size/1024/1024:.1f}MB.'
                )
            
            # Validate file type
            if hasattr(f, 'content_type') and f.content_type not in valid_mime_types:
                file_name = getattr(f, 'name', 'a file')
                raise forms.ValidationError(
                    f'Unsupported file type for "{file_name}". ' \
                    'Please upload an image, video, or document.'
                )
        
        return files
    
    def save(self, commit=True):
        files = self.cleaned_data.get('file', [])
        description = self.cleaned_data.get('description')
        evidence_list = []
        
        for file in files:
            if not file:
                continue
                
            evidence = IncidentEvidence(
                file=file,
                description=description,
                incident=self.incident,
                uploaded_by=self.user
            )
            if commit:
                evidence.save()
            evidence_list.append(evidence)
            
        return evidence_list[0] if evidence_list else None


class CommentForm(forms.ModelForm):
    """Form for adding and editing comments on incidents"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your comment here...',
                'required': True
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.incident = kwargs.pop('incident', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        comment = super().save(commit=False)
        if self.user:
            comment.user = self.user
        if self.incident:
            comment.incident = self.incident
        if commit:
            comment.save()
        return comment


class ExplainerVideoForm(forms.ModelForm):
    """Form for uploading explainer videos for incidents"""
    class Meta:
        model = ExplainerVideo
        fields = ['title', 'description', 'video']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a title for this video'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of the video content'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.incident = kwargs.pop('incident', None)
        super().__init__(*args, **kwargs)

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video:
            # Limit video size to 100MB
            max_size = 100 * 1024 * 1024  # 100MB
            if video.size > max_size:
                raise forms.ValidationError('Video file too large. Maximum size is 100MB.')
        return video

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.uploaded_by = self.user
        if self.incident:
            instance.incident = self.incident
        if commit:
            instance.save()
        return instance
