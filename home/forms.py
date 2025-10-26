from django import forms
from django.contrib.auth.models import User
from .models import SecurityIncident, IncidentUpdate
from django.utils import timezone

class SecurityIncidentForm(forms.ModelForm):
    """Form for creating and updating security incidents"""
    
    class Meta:
        model = SecurityIncident
        fields = [
            'title', 'description', 'incident_type', 'severity', 'status',
            'guest_name', 'guest_email', 'guest_phone', 'incident_date',
            'location_description', 'estimated_damage_cost', 'resolution_notes',
            'police_report_number'
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
