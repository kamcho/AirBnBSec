from django.contrib import admin
from .models import SecurityIncident, IncidentUpdate, IncidentEvidence

@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ['incident_id', 'title', 'incident_type', 'severity', 'status', 'reported_by', 'incident_date', 'reported_date']
    list_filter = ['incident_type', 'severity', 'status', 'reported_date']
    search_fields = ['incident_id', 'title', 'description', 'client__first_name', 'client__last_name', 'client__email']
    readonly_fields = ['incident_id', 'reported_date', 'created_at', 'updated_at']
    ordering = ['-reported_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('incident_id', 'title', 'description', 'incident_type', 'severity', 'status')
        }),
        ('People Involved', {
            'fields': ('reported_by', 'client')
        }),
        ('Timeline', {
            'fields': ('incident_date', 'reported_date', 'resolved_date')
        }),
        ('Details', {
            'fields': ('location_description', 'evidence_files', 'estimated_damage_cost')
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'police_report_number')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
admin.site.register(IncidentEvidence)
@admin.register(IncidentUpdate)
class IncidentUpdateAdmin(admin.ModelAdmin):
    list_display = ['incident', 'update_type', 'description', 'created_at']
    list_filter = ['update_type', 'created_at']
    search_fields = ['incident__incident_id', 'description']
    ordering = ['-created_at']
